"""
Regression Test Suite: Python (FastAPI) vs Rust (Actix-Web) Workflow Automation APIs.

Runs identical test flows against both services with 1000 concurrent users
and presents comparative metrics (latency, throughput, error rates).

Usage (inside Docker):
    python regression_test.py

Environment variables:
    PYTHON_API_URL  - default http://workflow-ms:8001
    RUST_API_URL    - default http://workflow-rust-ms:8002
    CONCURRENCY     - default 1000
"""

import asyncio
import json
import os
import statistics
import time
from dataclasses import dataclass, field
from typing import Any

import aiohttp
from tabulate import tabulate


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PYTHON_API_URL = os.getenv("PYTHON_API_URL", "http://workflow-ms:8001")
RUST_API_URL = os.getenv("RUST_API_URL", "http://workflow-rust-ms:8002")
CONCURRENCY = int(os.getenv("CONCURRENCY", "1000"))
API_V1 = "/api/v1"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RequestMetric:
    """Single request timing."""
    endpoint: str
    method: str
    status: int
    latency_ms: float
    error: str | None = None


@dataclass
class FlowMetrics:
    """Aggregated metrics for a full test flow."""
    service_name: str
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    # Per-endpoint breakdown
    endpoint_latencies: dict[str, list[float]] = field(default_factory=dict)

    def record(self, metric: RequestMetric) -> None:
        self.total_requests += 1
        self.latencies_ms.append(metric.latency_ms)

        key = f"{metric.method} {metric.endpoint}"
        self.endpoint_latencies.setdefault(key, []).append(metric.latency_ms)

        if 200 <= metric.status < 300:
            self.successful += 1
        else:
            self.failed += 1
            if metric.error:
                self.errors.append(metric.error)

    @property
    def wall_time_s(self) -> float:
        return self.end_time - self.start_time

    @property
    def throughput_rps(self) -> float:
        if self.wall_time_s == 0:
            return 0
        return self.total_requests / self.wall_time_s

    @property
    def error_rate_pct(self) -> float:
        if self.total_requests == 0:
            return 0
        return (self.failed / self.total_requests) * 100

    def percentile(self, p: float) -> float:
        if not self.latencies_ms:
            return 0
        sorted_lat = sorted(self.latencies_ms)
        idx = int(len(sorted_lat) * p / 100)
        idx = min(idx, len(sorted_lat) - 1)
        return sorted_lat[idx]


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

async def timed_request(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    endpoint_label: str,
    json_body: dict | None = None,
) -> RequestMetric:
    """Execute an HTTP request and return timing metrics."""
    start = time.perf_counter()
    error_msg = None
    status = 0
    try:
        async with session.request(method, url, json=json_body) as resp:
            status = resp.status
            if status >= 400:
                body = await resp.text()
                error_msg = body[:200]
            else:
                await resp.read()
    except Exception as e:
        status = 0
        error_msg = str(e)[:200]
    elapsed = (time.perf_counter() - start) * 1000  # ms
    return RequestMetric(
        endpoint=endpoint_label,
        method=method,
        status=status,
        latency_ms=elapsed,
        error=error_msg,
    )


# ---------------------------------------------------------------------------
# Test flows
# ---------------------------------------------------------------------------

SAMPLE_WORKFLOW = {
    "id": "bench_workflow",
    "name": "Benchmark Workflow",
    "description": "Workflow for regression benchmarking",
    "steps": [
        {"name": "initial_delay", "type": "delay", "config": {"duration": 1}},
    ],
}


async def single_user_flow(
    session: aiohttp.ClientSession,
    base_url: str,
    metrics: FlowMetrics,
    workflow_id: str,
    user_idx: int,
) -> None:
    """
    Execute the full API flow for a single simulated user:
    1. GET  /health
    2. GET  /
    3. POST /api/v1/workflows          (create workflow)
    4. GET  /api/v1/workflows/{uuid}   (get workflow)
    5. POST /api/v1/trigger            (trigger workflow)
    6. GET  /api/v1/runs/{run_id}      (get run)
    7. GET  /api/v1/runs               (list runs)
    """
    # 1. Health check
    m = await timed_request(session, "GET", f"{base_url}/health", "/health")
    metrics.record(m)

    # 2. Root
    m = await timed_request(session, "GET", f"{base_url}/", "/")
    metrics.record(m)

    # 3. Create workflow
    workflow_payload = SAMPLE_WORKFLOW.copy()
    workflow_payload["id"] = f"bench_workflow_{user_idx}"
    workflow_payload["name"] = f"Benchmark Workflow {user_idx}"
    m = await timed_request(
        session, "POST", f"{base_url}{API_V1}/workflows",
        "/api/v1/workflows", json_body=workflow_payload,
    )
    metrics.record(m)

    # Parse workflow_id from response
    created_workflow_id = workflow_id  # fallback
    if 200 <= m.status < 300:
        # Re-fetch to get the uuid (we need to parse the response)
        # Since timed_request consumes the body, we do a separate call
        pass

    # 3b. Re-create to capture the response body
    async with session.post(
        f"{base_url}{API_V1}/workflows", json=workflow_payload
    ) as resp:
        if resp.status == 200:
            data = await resp.json()
            created_workflow_id = data.get("workflow_id", workflow_id)

    # 4. Get workflow
    m = await timed_request(
        session, "GET", f"{base_url}{API_V1}/workflows/{created_workflow_id}",
        "/api/v1/workflows/{uuid}",
    )
    metrics.record(m)

    # 5. Trigger workflow
    trigger_payload = {
        "workflow_id": created_workflow_id,
        "payload": {"user_id": f"user_{user_idx}", "event": "benchmark"},
    }
    m = await timed_request(
        session, "POST", f"{base_url}{API_V1}/trigger",
        "/api/v1/trigger", json_body=trigger_payload,
    )
    metrics.record(m)

    # Parse run_id
    run_id = "unknown"
    if 200 <= m.status < 300:
        async with session.post(
            f"{base_url}{API_V1}/trigger", json=trigger_payload
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                run_id = data.get("run_id", "unknown")

    # 6. Get run
    m = await timed_request(
        session, "GET", f"{base_url}{API_V1}/runs/{run_id}",
        "/api/v1/runs/{run_id}",
    )
    metrics.record(m)

    # 7. List runs (with pagination to avoid full table scan)
    m = await timed_request(
        session, "GET", f"{base_url}{API_V1}/runs?limit=50",
        "/api/v1/runs",
    )
    metrics.record(m)


async def run_load_test(
    base_url: str,
    service_name: str,
    concurrency: int,
) -> FlowMetrics:
    """Run the full load test against a single service."""
    metrics = FlowMetrics(service_name=service_name)

    # First, create a shared workflow for trigger tests
    connector = aiohttp.TCPConnector(limit=concurrency, force_close=False)
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Seed workflow
        async with session.post(
            f"{base_url}{API_V1}/workflows", json=SAMPLE_WORKFLOW
        ) as resp:
            seed_workflow_id = "unknown"
            if resp.status == 200:
                data = await resp.json()
                seed_workflow_id = data.get("workflow_id", "unknown")

        print(f"\n{'='*60}")
        print(f"  Running {concurrency} concurrent users against {service_name}")
        print(f"  Base URL: {base_url}")
        print(f"  Seed workflow ID: {seed_workflow_id}")
        print(f"{'='*60}\n")

        metrics.start_time = time.perf_counter()

        # Launch concurrent user flows
        tasks = [
            single_user_flow(session, base_url, metrics, seed_workflow_id, i)
            for i in range(concurrency)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        metrics.end_time = time.perf_counter()

    return metrics


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_summary(py_metrics: FlowMetrics, rs_metrics: FlowMetrics) -> None:
    """Print a comparative summary table."""
    print("\n" + "=" * 80)
    print("  REGRESSION TEST RESULTS: Python (FastAPI) vs Rust (Actix-Web)")
    print("=" * 80)

    # Overall summary
    headers = ["Metric", "Python (FastAPI)", "Rust (Actix-Web)", "Diff (%)"]
    rows = []

    def diff_pct(py_val: float, rs_val: float) -> str:
        if py_val == 0:
            return "N/A"
        pct = ((rs_val - py_val) / py_val) * 100
        sign = "+" if pct > 0 else ""
        return f"{sign}{pct:.1f}%"

    rows.append([
        "Total Requests",
        py_metrics.total_requests,
        rs_metrics.total_requests,
        "",
    ])
    rows.append([
        "Successful",
        py_metrics.successful,
        rs_metrics.successful,
        "",
    ])
    rows.append([
        "Failed",
        py_metrics.failed,
        rs_metrics.failed,
        "",
    ])
    rows.append([
        "Error Rate (%)",
        f"{py_metrics.error_rate_pct:.2f}%",
        f"{rs_metrics.error_rate_pct:.2f}%",
        "",
    ])
    rows.append([
        "Wall Time (s)",
        f"{py_metrics.wall_time_s:.2f}",
        f"{rs_metrics.wall_time_s:.2f}",
        diff_pct(py_metrics.wall_time_s, rs_metrics.wall_time_s),
    ])
    rows.append([
        "Throughput (req/s)",
        f"{py_metrics.throughput_rps:.1f}",
        f"{rs_metrics.throughput_rps:.1f}",
        diff_pct(py_metrics.throughput_rps, rs_metrics.throughput_rps),
    ])

    # Latency stats
    for label, p in [("Mean Latency (ms)", None), ("P50 (ms)", 50), ("P90 (ms)", 90), ("P95 (ms)", 95), ("P99 (ms)", 99)]:
        if p is None:
            py_val = statistics.mean(py_metrics.latencies_ms) if py_metrics.latencies_ms else 0
            rs_val = statistics.mean(rs_metrics.latencies_ms) if rs_metrics.latencies_ms else 0
        else:
            py_val = py_metrics.percentile(p)
            rs_val = rs_metrics.percentile(p)
        rows.append([label, f"{py_val:.2f}", f"{rs_val:.2f}", diff_pct(py_val, rs_val)])

    if py_metrics.latencies_ms:
        rows.append(["Min Latency (ms)", f"{min(py_metrics.latencies_ms):.2f}", f"{min(rs_metrics.latencies_ms):.2f}" if rs_metrics.latencies_ms else "N/A", ""])
        rows.append(["Max Latency (ms)", f"{max(py_metrics.latencies_ms):.2f}", f"{max(rs_metrics.latencies_ms):.2f}" if rs_metrics.latencies_ms else "N/A", ""])

    print("\n" + tabulate(rows, headers=headers, tablefmt="grid"))

    # Per-endpoint breakdown
    print("\n" + "-" * 80)
    print("  PER-ENDPOINT LATENCY BREAKDOWN (mean ms)")
    print("-" * 80)

    all_endpoints = sorted(
        set(list(py_metrics.endpoint_latencies.keys()) + list(rs_metrics.endpoint_latencies.keys()))
    )
    ep_headers = ["Endpoint", "Python Mean (ms)", "Python P99 (ms)", "Rust Mean (ms)", "Rust P99 (ms)", "Mean Diff (%)"]
    ep_rows = []
    for ep in all_endpoints:
        py_lats = py_metrics.endpoint_latencies.get(ep, [])
        rs_lats = rs_metrics.endpoint_latencies.get(ep, [])
        py_mean = statistics.mean(py_lats) if py_lats else 0
        rs_mean = statistics.mean(rs_lats) if rs_lats else 0
        py_p99 = sorted(py_lats)[int(len(py_lats) * 0.99)] if py_lats else 0
        rs_p99 = sorted(rs_lats)[int(len(rs_lats) * 0.99)] if rs_lats else 0
        ep_rows.append([
            ep,
            f"{py_mean:.2f}",
            f"{py_p99:.2f}",
            f"{rs_mean:.2f}",
            f"{rs_p99:.2f}",
            diff_pct(py_mean, rs_mean),
        ])

    print("\n" + tabulate(ep_rows, headers=ep_headers, tablefmt="grid"))

    # Errors summary
    if py_metrics.errors or rs_metrics.errors:
        print("\n" + "-" * 80)
        print("  ERRORS SUMMARY")
        print("-" * 80)
        if py_metrics.errors:
            print(f"\n  Python errors ({len(py_metrics.errors)}):")
            for e in py_metrics.errors[:10]:
                print(f"    - {e}")
        if rs_metrics.errors:
            print(f"\n  Rust errors ({len(rs_metrics.errors)}):")
            for e in rs_metrics.errors[:10]:
                print(f"    - {e}")

    print("\n" + "=" * 80)
    print("  TEST COMPLETE")
    print("=" * 80 + "\n")


# ---------------------------------------------------------------------------
# Wait for services
# ---------------------------------------------------------------------------

async def wait_for_service(url: str, name: str, timeout: int = 120) -> bool:
    """Wait for a service to become healthy."""
    print(f"Waiting for {name} at {url}/health ...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        print(f"  {name} is ready!")
                        return True
        except Exception:
            pass
        await asyncio.sleep(2)
    print(f"  TIMEOUT: {name} did not become ready within {timeout}s")
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    print("\n" + "=" * 80)
    print("  WORKFLOW AUTOMATION - REGRESSION TEST SUITE")
    print(f"  Concurrency: {CONCURRENCY} users")
    print(f"  Python API:  {PYTHON_API_URL}")
    print(f"  Rust API:    {RUST_API_URL}")
    print("=" * 80)

    # Wait for both services
    py_ready = await wait_for_service(PYTHON_API_URL, "Python (FastAPI)")
    rs_ready = await wait_for_service(RUST_API_URL, "Rust (Actix-Web)")

    if not py_ready or not rs_ready:
        print("\nERROR: Not all services are ready. Aborting.")
        return

    # Run load tests sequentially to avoid resource contention
    print("\n--- Phase 1: Testing Python (FastAPI) ---")
    py_metrics = await run_load_test(PYTHON_API_URL, "Python (FastAPI)", CONCURRENCY)

    # Small pause between tests
    print("\nPausing 5s between tests...")
    await asyncio.sleep(5)

    print("\n--- Phase 2: Testing Rust (Actix-Web) ---")
    rs_metrics = await run_load_test(RUST_API_URL, "Rust (Actix-Web)", CONCURRENCY)

    # Print comparative results
    print_summary(py_metrics, rs_metrics)


if __name__ == "__main__":
    asyncio.run(main())
