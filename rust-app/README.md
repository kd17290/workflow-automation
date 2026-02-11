# Workflow Automation — Rust Implementation

A 1:1 Rust port of the Python (FastAPI) workflow automation API, built with **Actix-Web**, **SQLx**, and **rdkafka**.

## Architecture

The project mirrors the Python app's layered architecture, following SOLID principles:

```
rust-app/src/
├── bin/
│   ├── api.rs              # HTTP server binary (Actix-Web, port 8002)
│   └── worker.rs           # Kafka consumer worker binary
├── api/
│   ├── deps.rs             # AppState / dependency injection
│   └── v1/
│       ├── router.rs       # Route configuration
│       └── endpoints/
│           ├── workflows.rs  # POST/GET /api/v1/workflows
│           ├── runs.rs       # GET /api/v1/runs
│           └── trigger.rs    # POST /api/v1/trigger
├── connector/
│   ├── base.rs             # Connector trait (Interface Segregation)
│   ├── delay.rs            # Delay connector
│   ├── webhook.rs          # Webhook/HTTP connector
│   └── factory.rs          # ConnectorFactory (Factory Pattern)
├── core/
│   └── config.rs           # Settings from env vars
├── db/
│   ├── session.rs          # PgPool creation + migrations
│   └── models/             # SQLx row types
├── messaging/
│   ├── events.rs           # Kafka event schemas
│   └── kafka.rs            # KafkaProducer / KafkaConsumer
├── repositories/
│   ├── health.rs           # Health status persistence
│   ├── workflow.rs         # WorkflowRepository
│   └── run.rs              # WorkflowRunRepository
├── schemas/
│   ├── common.rs           # WorkflowStatus, StepStatus enums
│   ├── workflow.rs         # WorkflowDefinition, StepResult, TriggerRequest
│   └── run.rs              # WorkflowRun
├── services/
│   └── workflow.rs         # WorkflowService (orchestration)
├── storage/
│   ├── base.rs             # Storage trait (Dependency Inversion)
│   └── db_storage.rs       # PostgreSQL storage implementations
└── lib.rs                  # Module root
```

## SOLID Principles Applied

| Principle | Implementation |
|-----------|---------------|
| **Single Responsibility** | Each module has one job: `storage/` persists, `repositories/` wraps storage, `services/` orchestrates, `api/` handles HTTP |
| **Open/Closed** | New connectors added by implementing `Connector` trait + registering in factory — no existing code modified |
| **Liskov Substitution** | All `Storage<T>` implementations are interchangeable behind the trait |
| **Interface Segregation** | `Connector` trait has a single `execute` method; `Storage<T>` trait has focused CRUD methods |
| **Dependency Inversion** | `WorkflowService` depends on `Arc<dyn Storage<T>>` traits, not concrete `DBStorage` types |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Root — returns `{"message": "Hello World"}` |
| GET | `/health` | Health check — returns `{"status": "ok"}` |
| POST | `/api/v1/workflows` | Create workflow definition |
| GET | `/api/v1/workflows/{uuid}` | Get workflow by UUID |
| POST | `/api/v1/trigger` | Trigger workflow execution via Kafka |
| GET | `/api/v1/runs/{run_id}` | Get workflow run details |
| GET | `/api/v1/runs` | List all workflow runs |

## Running

Everything runs inside Docker — **no local dependencies required**.

```bash
# Start all services (Python + Rust + DB + Kafka)
docker compose --profile workflow up --build -d

# Run benchmarks (1000 concurrent users)
docker compose --profile workflow --profile benchmark up --build benchmark
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `workflow_db` | PostgreSQL host |
| `POSTGRES_DB` | `workflow_db` | Database name |
| `POSTGRES_USER` | `postgres` | DB user |
| `POSTGRES_PASSWORD` | `postgres` | DB password |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka brokers |
| `KAFKA_CONSUMER_GROUP` | `workflow-workers-rust` | Kafka consumer group |
