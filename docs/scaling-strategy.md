# Scaling Strategy

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Current Architecture](#2-current-architecture)
- [3. Scaling Dimensions](#3-scaling-dimensions)
- [4. Horizontal Scaling Strategy](#4-horizontal-scaling-strategy)
- [5. Vertical Scaling Strategy](#5-vertical-scaling-strategy)
- [6. Database Scaling](#6-database-scaling)
- [7. Kafka Scaling](#7-kafka-scaling)
- [8. Caching Strategy](#8-caching-strategy)
- [9. Load Balancing](#9-load-balancing)
- [10. Auto-Scaling Policies](#10-auto-scaling-policies)
- [11. Scaling Roadmap](#11-scaling-roadmap)

---

## 1. Executive Summary

This document defines the scaling strategy for the Workflow Automation Platform, covering both the **Python (FastAPI)** and **Rust (Actix-Web)** implementations. The platform is designed as a distributed, event-driven system with clear separation of concerns, enabling independent scaling of each component.

**Current state (Phase 2 — Implemented):**
- 3× API replicas per language behind **Nginx load balancer** (least_conn)
- 3× Workers per language in **Kafka consumer groups** (3 partitions/topic)
- **PgBouncer** connection pooler (600 max connections, transaction pooling)
- **Redis** centralized cache (256MB, LRU eviction, 60s/10s TTL)
- **0% error rate** under 1000 concurrent users (both Python and Rust)
- Python: **1,084 req/s** | Rust: **4,017 req/s** (measured)

**Key scaling levers:**
- API servers scale horizontally behind Nginx load balancer
- Workers scale horizontally via Kafka consumer groups
- PgBouncer manages DB connection multiplexing
- Redis caching reduces DB read pressure
- PostgreSQL scales vertically + read replicas
- Kafka scales via partitions and broker count

---

## 2. Current Architecture (Phase 2 — Implemented)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          CURRENT DEPLOYMENT — PHASE 2                             │
│                                                                                  │
│  ┌──────────┐    ┌──────────────────────────────────────────────────────────┐    │
│  │  Client   │───▶│                 Nginx Load Balancer                      │    │
│  │          │    │            :8001 (Python)  :8002 (Rust)                  │    │
│  └──────────┘    └──────┬──────────────┬──────────────┬─────────────────────┘    │
│                         │              │              │                           │
│              ┌──────────▼──┐ ┌────────▼────┐ ┌──────▼────────┐                  │
│              │ Python API 1│ │ Python API 2│ │ Python API 3  │                  │
│              │ FastAPI     │ │ FastAPI     │ │ FastAPI       │                  │
│              └──────┬──────┘ └──────┬──────┘ └──────┬────────┘                  │
│                     │              │              │                              │
│              ┌──────▼──┐ ┌────────▼────┐ ┌──────▼────────┐                     │
│              │ Rust API1│ │ Rust API 2  │ │ Rust API 3    │                     │
│              │ Actix-Web│ │ Actix-Web   │ │ Actix-Web     │                     │
│              └──────┬───┘ └──────┬──────┘ └──────┬────────┘                     │
│                     │            │              │                                │
│                     └────────────┼──────────────┘                                │
│                                  │                                               │
│              ┌───────────┐  ┌────▼─────┐  ┌──────────┐  ┌──────────────────┐   │
│              │   Redis   │  │ PgBouncer│  │  Kafka   │  │  PostgreSQL 16.1 │   │
│              │   Cache   │  │  (600    │  │  (3 part │  │  (via PgBouncer) │   │
│              │   :6379   │  │   conn)  │  │  /topic) │  │  :5432           │   │
│              └───────────┘  └────┬─────┘  └────┬─────┘  └──────────────────┘   │
│                                  │             │                                 │
│              ┌───────────────────┼─────────────┼───────────────────────┐         │
│              │  Py Worker 1  Py Worker 2  Py Worker 3  (consumer grp) │         │
│              │  Rs Worker 1  Rs Worker 2  Rs Worker 3  (consumer grp) │         │
│              └────────────────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Current Capacity (Measured — Phase 2)

| Component | Python (FastAPI) | Rust (Actix-Web) |
|-----------|-----------------|------------------|
| API Instances | 3 (behind Nginx LB) | 3 (behind Nginx LB) |
| Worker Instances | 3 (Kafka consumer group) | 3 (Kafka consumer group) |
| DB Connections | 50/instance via PgBouncer | 100/instance via PgBouncer |
| Cache | Redis (60s TTL workflows, 10s TTL runs) | Redis (60s TTL workflows, 10s TTL runs) |
| Kafka Partitions | 3 per topic | 3 per topic |
| Throughput | **1,084 req/s** | **4,017 req/s** |
| Error Rate @ 1000 users | **0.00%** ✅ | **0.00%** ✅ |
| Mean Latency | 523ms | 161ms |
| P99 Latency | 1,076ms | 364ms |

### Phase 1 → Phase 2 Improvement

| Metric | Phase 1 Python | Phase 2 Python | Improvement |
|--------|---------------|----------------|-------------|
| Throughput | 42 req/s | 1,084 req/s | **25× higher** |
| Error Rate | 20.36% | 0.00% | **Eliminated** |
| Wall Time | 151s | 6.46s | **23× faster** |

| Metric | Phase 1 Rust | Phase 2 Rust | Improvement |
|--------|-------------|--------------|-------------|
| Throughput | 221 req/s | 4,017 req/s | **18× higher** |
| Error Rate | 0.06% | 0.00% | **Eliminated** |
| Wall Time | 31.7s | 1.74s | **18× faster** |

---

## 3. Scaling Dimensions

```
                    ┌─────────────────────────────────────┐
                    │        SCALING DIMENSIONS            │
                    └─────────────────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
    │   HORIZONTAL    │   │    VERTICAL     │   │   DATA LAYER    │
    │                 │   │                 │   │                 │
    │ • API replicas  │   │ • CPU/RAM per   │   │ • DB read       │
    │ • Worker        │   │   container     │   │   replicas      │
    │   replicas      │   │ • DB instance   │   │ • Connection    │
    │ • Kafka         │   │   size          │   │   pooling       │
    │   partitions    │   │ • Kafka broker  │   │ • Caching       │
    │ • Load          │   │   resources     │   │ • Partitioning  │
    │   balancers     │   │                 │   │                 │
    └─────────────────┘   └─────────────────┘   └─────────────────┘
```

---

## 4. Horizontal Scaling Strategy

### 4.1 API Layer Scaling

```
                         ┌──────────────┐
                         │ Load Balancer │
                         │ (Nginx/HAProxy│
                         │  /K8s Ingress)│
                         └──────┬───────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
     ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
     │  API Server 1  │ │  API Server 2  │ │  API Server N  │
     │  (Stateless)   │ │  (Stateless)   │ │  (Stateless)   │
     └────────┬───────┘ └────────┬───────┘ └────────┬───────┘
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                         ┌──────▼───────┐
                         │  PostgreSQL   │
                         │  + Kafka      │
                         └──────────────┘
```

**Strategy:**
- API servers are **stateless** — no session affinity required
- Scale by adding replicas: `docker compose up --scale workflow=3 --scale workflow_rust=3`
- In Kubernetes: `HorizontalPodAutoscaler` based on CPU/request latency

**Docker Compose scaling:**
```yaml
# Scale to 3 API replicas
workflow:
  deploy:
    replicas: 3
workflow_rust:
  deploy:
    replicas: 3
```

### 4.2 Worker Layer Scaling

```
                         ┌──────────────┐
                         │    Kafka      │
                         │  Topic:       │
                         │  workflow.    │
                         │  trigger      │
                         │              │
                         │  Partitions:  │
                         │  [0][1][2]..  │
                         └──────┬───────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
     ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
     │   Worker 1     │ │   Worker 2     │ │   Worker N     │
     │ Partition [0]  │ │ Partition [1]  │ │ Partition [2]  │
     │                │ │                │ │                │
     │ Consumer Group:│ │ Consumer Group:│ │ Consumer Group:│
     │ workflow-      │ │ workflow-      │ │ workflow-      │
     │ workers        │ │ workers        │ │ workers        │
     └────────────────┘ └────────────────┘ └────────────────┘
```

**Strategy:**
- Workers share a **Kafka consumer group** — Kafka auto-distributes partitions
- Scale workers up to the number of topic partitions
- Each worker processes workflows independently

**Scaling formula:**
```
Max parallel workflows = min(num_workers, num_partitions)
```

**Recommended partition count per scaling tier:**

| Tier | Users | Workers | Partitions | Throughput Target |
|------|-------|---------|------------|-------------------|
| Dev | 1-100 | 1 | 3 | 50 req/s |
| Staging | 100-1K | 3 | 6 | 500 req/s |
| Production | 1K-10K | 10 | 12 | 2,000 req/s |
| High Scale | 10K+ | 30 | 30 | 10,000+ req/s |

---

## 5. Vertical Scaling Strategy

### Resource Allocation per Component

```
┌─────────────────────────────────────────────────────────────┐
│              RESOURCE ALLOCATION MATRIX                       │
├──────────────┬──────────┬──────────┬──────────┬─────────────┤
│  Component   │   Dev    │ Staging  │   Prod   │  High Scale │
├──────────────┼──────────┼──────────┼──────────┼─────────────┤
│ Python API   │ 256MB    │ 512MB    │ 1GB      │ 2GB         │
│              │ 0.25 CPU │ 0.5 CPU  │ 1 CPU    │ 2 CPU       │
├──────────────┼──────────┼──────────┼──────────┼─────────────┤
│ Rust API     │ 64MB     │ 128MB    │ 256MB    │ 512MB       │
│              │ 0.25 CPU │ 0.5 CPU  │ 1 CPU    │ 2 CPU       │
├──────────────┼──────────┼──────────┼──────────┼─────────────┤
│ Worker (Py)  │ 256MB    │ 512MB    │ 1GB      │ 2GB         │
│              │ 0.25 CPU │ 0.5 CPU  │ 1 CPU    │ 2 CPU       │
├──────────────┼──────────┼──────────┼──────────┼─────────────┤
│ Worker (Rs)  │ 64MB     │ 128MB    │ 256MB    │ 512MB       │
│              │ 0.25 CPU │ 0.5 CPU  │ 1 CPU    │ 2 CPU       │
├──────────────┼──────────┼──────────┼──────────┼─────────────┤
│ PostgreSQL   │ 256MB    │ 1GB      │ 4GB      │ 16GB        │
│              │ 0.5 CPU  │ 1 CPU    │ 4 CPU    │ 8 CPU       │
├──────────────┼──────────┼──────────┼──────────┼─────────────┤
│ Kafka Broker │ 512MB    │ 1GB      │ 4GB      │ 8GB         │
│              │ 0.5 CPU  │ 1 CPU    │ 2 CPU    │ 4 CPU       │
└──────────────┴──────────┴──────────┴──────────┴─────────────┘
```

> **Note:** Rust services require ~4x less memory than Python equivalents for the same workload.

---

## 6. Database Scaling

### 6.1 Connection Pooling (Implemented — PgBouncer)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Py API ×3   │     │  Rs API ×3   │     │  Workers ×6  │
│  Pool: 50    │     │  Pool: 100   │     │  Pool: ~10   │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                     ┌──────▼───────┐
                     │   PgBouncer  │  ✅ IMPLEMENTED
                     │  max_client: │
                     │  600 conn    │
                     │  txn pooling │
                     │  pool: 40    │
                     └──────┬───────┘
                            │
                     ┌──────▼───────┐
                     │  PostgreSQL  │
                     │  max_conn:   │
                     │  100         │
                     └──────────────┘
```

**Connection budget (Phase 2 — Current):**
```
Total client connections to PgBouncer:
  = (3 × 50) + (3 × 100) + (6 × 10) + overhead
  = 150 + 300 + 60 + 10
  = 520 client connections (within 600 max)

PgBouncer → PostgreSQL server connections:
  = default_pool_size (40) + reserve (10)
  = ~50 actual DB connections (well within 100 max)

✅ PgBouncer multiplexes 520 client → ~50 server connections
```

### 6.2 Read Replica Strategy

```
                     ┌──────────────┐
                     │   Primary    │◀──── Writes (CREATE, UPDATE)
                     │  PostgreSQL  │
                     └──────┬───────┘
                            │ Streaming
                            │ Replication
                     ┌──────▼───────┐
                     │   Replica    │◀──── Reads (GET, LIST)
                     │  PostgreSQL  │
                     └──────────────┘
```

**Read/Write split:**
- **Writes** → Primary: `POST /workflows`, `POST /trigger`, worker updates
- **Reads** → Replica: `GET /workflows/{id}`, `GET /runs`, `GET /runs/{id}`

### 6.3 Table Partitioning (Future)

```sql
-- Partition workflow_runs by month for large-scale deployments
CREATE TABLE workflow_runs (
    uuid VARCHAR PRIMARY KEY,
    ...
    started_at TIMESTAMPTZ NOT NULL
) PARTITION BY RANGE (started_at);

CREATE TABLE workflow_runs_2026_01 PARTITION OF workflow_runs
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

---

## 7. Kafka Scaling

### 7.1 Topic Partition Strategy

```
Topic: workflow.trigger
┌───────────┬───────────┬───────────┬───────────┐
│Partition 0│Partition 1│Partition 2│Partition 3│
│           │           │           │           │
│ msg msg   │ msg msg   │ msg msg   │ msg msg   │
│ msg msg   │ msg       │ msg msg   │ msg       │
└─────┬─────┴─────┬─────┴─────┬─────┴─────┬─────┘
      │           │           │           │
      ▼           ▼           ▼           ▼
  Worker 0    Worker 1    Worker 2    Worker 3
```

**Partition key:** `workflow_run_id` — ensures all messages for a run go to the same partition (ordering guarantee).

### 7.2 Multi-Broker Setup

```
┌──────────────────────────────────────────────────┐
│                 Kafka Cluster                     │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Broker 1 │  │ Broker 2 │  │ Broker 3 │      │
│  │ Leader   │  │ Follower │  │ Follower │      │
│  │ P0, P1   │  │ P0, P2   │  │ P1, P2   │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│                                                  │
│  Replication Factor: 3                           │
│  Min In-Sync Replicas: 2                         │
└──────────────────────────────────────────────────┘
```

**Production Kafka config:**
```yaml
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3
KAFKA_DEFAULT_REPLICATION_FACTOR: 3
KAFKA_MIN_INSYNC_REPLICAS: 2
KAFKA_NUM_PARTITIONS: 12
```

---

## 8. Caching Strategy

```
┌──────────┐     ┌──────────┐     ┌──────────────┐
│  Client  │────▶│ API      │────▶│    Redis     │
│          │     │ Server   │     │   (Cache)    │
└──────────┘     └────┬─────┘     └──────┬───────┘
                      │                  │
                      │  Cache Miss      │ Cache Hit
                      ▼                  │ (fast path)
                ┌──────────────┐         │
                │  PostgreSQL  │─────────┘
                │  (Source of  │  Populate cache
                │   Truth)     │
                └──────────────┘
```

**Cacheable endpoints:**
| Endpoint | TTL | Invalidation |
|----------|-----|-------------|
| `GET /workflows/{id}` | 60s | On workflow update |
| `GET /runs/{id}` | 5s | On run status change |
| `GET /runs` | 2s | Time-based expiry |
| `GET /health` | No cache | — |

---

## 9. Load Balancing

### Production Architecture with Load Balancer

```
                         ┌──────────────────┐
                         │   DNS / CDN      │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │  Load Balancer   │
                         │  (Nginx/Traefik) │
                         │                  │
                         │  /api/v1/* ──────┼──▶ API Pool
                         │  /health  ──────┼──▶ Health Pool
                         └────────┬─────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
              ┌─────▼─────┐ ┌────▼──────┐ ┌────▼──────┐
              │ API Pod 1 │ │ API Pod 2 │ │ API Pod 3 │
              │ Python    │ │ Python    │ │ Python    │
              │ :8001     │ │ :8001     │ │ :8001     │
              └───────────┘ └───────────┘ └───────────┘

              ┌─────▼─────┐ ┌────▼──────┐ ┌────▼──────┐
              │ API Pod 1 │ │ API Pod 2 │ │ API Pod 3 │
              │ Rust      │ │ Rust      │ │ Rust      │
              │ :8002     │ │ :8002     │ │ :8002     │
              └───────────┘ └───────────┘ └───────────┘
```

**Load balancing algorithm:** Round-robin (stateless APIs) or least-connections.

---

## 10. Auto-Scaling Policies

### Kubernetes HPA Configuration

```yaml
# API auto-scaling
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: workflow-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: workflow-api
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
```

### Scaling Triggers

```
┌─────────────────────────────────────────────────────────────┐
│                  AUTO-SCALING TRIGGERS                        │
├─────────────────┬───────────────┬───────────────────────────┤
│  Metric         │  Threshold    │  Action                   │
├─────────────────┼───────────────┼───────────────────────────┤
│  CPU Usage      │  > 70%        │  Scale up API replicas    │
│  CPU Usage      │  < 30%        │  Scale down API replicas  │
│  Kafka Lag      │  > 1000 msgs  │  Scale up workers         │
│  Kafka Lag      │  < 100 msgs   │  Scale down workers       │
│  P99 Latency    │  > 2000ms     │  Scale up API replicas    │
│  Error Rate     │  > 5%         │  Alert + investigate      │
│  DB Connections  │  > 80% pool   │  Scale up pool / add PgB  │
│  Memory Usage   │  > 85%        │  Scale up vertically      │
└─────────────────┴───────────────┴───────────────────────────┘
```

---

## 11. Scaling Roadmap

```
Phase 1 (Completed)        Phase 2 (Current ✅)       Phase 3 (Production)       Phase 4 (High Scale)
─────────────────          ───────────────────        ────────────────────       ──────────────────

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ • Single API    │       │ • 3 API replicas│       │ • 10+ API pods  │       │ • 20+ API pods  │
│ • Single Worker │  ──▶  │ • 3 Workers     │  ──▶  │ • 10+ Workers   │  ──▶  │ • 30+ Workers   │
│ • Single DB     │       │ • PgBouncer ✅  │       │ • DB + Replica  │       │ • DB Sharding   │
│ • 1 Kafka broker│       │ • Redis Cache ✅│       │ • 3 Kafka broker│       │ • 5+ Kafka brk  │
│ • ~42-221 req/s │       │ • Nginx LB ✅   │       │ • ~12,000 req/s │       │ • ~50,000 req/s │
│ • 20% errors    │       │ • 3 Kafka parts │       │ • Prometheus    │       │ • Multi-region  │
│                 │       │ • 1K-4K req/s ✅│       │ • Circuit break │       │ • CQRS pattern  │
│                 │       │ • 0% errors ✅  │       │                 │       │                 │
│                 │       │ • 10K: saturated│       │                 │       │                 │
└─────────────────┘       └─────────────────┘       └─────────────────┘       └─────────────────┘
```

### 10K Stress Test — Scaling Validation

The Phase 2 infrastructure was stress-tested at **10,000 concurrent users** to identify the scaling ceiling:

```
┌──────────────────────────────────────────────────────────────────┐
│              10K STRESS TEST — PHASE 2 CEILING                    │
│                                                                   │
│  Metric           │ 1K Python │ 10K Python │ 1K Rust │ 10K Rust │
│  ─────────────────│───────────│────────────│─────────│──────────│
│  Error Rate       │  0.00% ✅ │  21.08% ❌ │  0.00% ✅│  8.89% ⚠️│
│  Throughput       │  1,084/s  │  462/s     │  4,017/s│  1,677/s │
│  Mean Latency     │  523ms    │  8,188ms   │  161ms  │  3,073ms │
│  P99 Latency      │  1,076ms  │  25,002ms  │  364ms  │  9,681ms │
│  Wall Time        │  6.46s    │  106.33s   │  1.74s  │  32.97s  │
│                                                                   │
│  Bottleneck: Nginx connection limits + PgBouncer max_client_conn  │
│  All errors are "Server disconnected" — infrastructure, not code  │
└──────────────────────────────────────────────────────────────────┘
```

**Key findings:**
- Phase 2 (3 replicas) handles **1K users perfectly** but **saturates at 10K**
- Rust degrades more gracefully (8.9% errors vs Python's 21.1%)
- Throughput actually drops because connections queue and time out
- The bottleneck is **infrastructure** (Nginx, PgBouncer limits), not application code

**To handle 10K users, Phase 3 requires:**
- 10+ API replicas per language
- Nginx `worker_connections` tuning (beyond 1024)
- PgBouncer `max_client_conn` > 600
- 12+ Kafka partitions for worker parallelism
- Kubernetes with HPA auto-scaling

### Phase 1 → Phase 2 Checklist (✅ ALL COMPLETED)
- [x] Add PgBouncer for connection pooling (600 max conn, txn pooling)
- [x] Increase Kafka partitions to 3 per topic
- [x] Deploy 3 API replicas + Nginx load balancer (least_conn)
- [x] Deploy 3 worker replicas per language
- [x] Add Redis caching for workflow reads (60s TTL) and runs (10s TTL)
- [x] Add cursor-based pagination on GET /runs
- [x] Add DB indexes (status, started_at, uuid, composite)
- [x] Fix Python Kafka producer race condition (asyncio.Lock + startup init)
- [x] Increase Python DB pool (pool_size=50, max_overflow=20)

### Phase 2 → Phase 3 Checklist (Required for 10K Users)
- [ ] Scale to 10+ API replicas per language
- [ ] Tune Nginx `worker_connections` and `proxy_connect_timeout`
- [ ] Increase PgBouncer `max_client_conn` beyond 600
- [ ] Increase Kafka partitions to 12+ per topic
- [ ] Migrate to Kubernetes with HPA auto-scaling
- [ ] Add PostgreSQL read replica
- [ ] Deploy 3-broker Kafka cluster
- [ ] Add distributed tracing (Jaeger/Zipkin)
- [ ] Implement circuit breakers
- [ ] Add rate limiting
- [ ] Set up Prometheus + Grafana monitoring

### Phase 3 → Phase 4 Checklist
- [ ] Database table partitioning
- [ ] Multi-region deployment
- [ ] Kafka MirrorMaker for cross-region replication
- [ ] CDN for static assets
- [ ] Implement CQRS pattern for read/write separation
