FROM rust:1.88-slim AS builder

RUN apt-get update && \
    apt-get -y install pkg-config libssl-dev cmake build-essential librdkafka-dev libcurl4-openssl-dev curl && \
    apt-get clean autoclean --yes && \
    apt-get autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

WORKDIR /usr/src/app

# Copy manifest files first for dependency caching
COPY Cargo.toml Cargo.lock* ./

# Create a dummy src to build dependencies first (layer caching)
RUN mkdir -p src/bin && \
    echo "fn main() {}" > src/bin/api.rs && \
    echo "fn main() {}" > src/bin/worker.rs && \
    echo "" > src/lib.rs && \
    cargo build --release 2>/dev/null || true && \
    rm -rf src target/release/api target/release/worker target/release/deps/workflow_automation* target/release/.fingerprint/workflow-automation*

# Copy actual source code
COPY src ./src

# Build the real binaries (force recompile of our crate)
RUN touch src/lib.rs && cargo build --release

# --- Runtime stage ---
FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get -y install libssl3 librdkafka1 ca-certificates curl && \
    apt-get clean autoclean --yes && \
    apt-get autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

WORKDIR /usr/src/app

# Copy built binaries from builder
COPY --from=builder /usr/src/app/target/release/api /usr/local/bin/api
COPY --from=builder /usr/src/app/target/release/worker /usr/local/bin/worker

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD curl -f http://localhost:8002/health || exit 1

EXPOSE 8002

CMD ["api"]
