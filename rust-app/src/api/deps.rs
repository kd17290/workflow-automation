use std::sync::Arc;

use sqlx::PgPool;

use crate::cache::redis_cache::RedisCache;
use crate::messaging::kafka::KafkaProducer;
use crate::services::workflow::WorkflowService;
use crate::storage::db_storage::{WorkflowDefinitionStorage, WorkflowRunStorage};

/// Application state shared across all request handlers (Dependency Injection).
///
/// Mirrors Python's dependency injection via FastAPI's Depends() from app/api/deps.py.
/// Holds the WorkflowService, KafkaProducer, and RedisCache as shared state.
pub struct AppState {
    pub workflow_service: Arc<WorkflowService>,
    pub kafka_producer: Arc<KafkaProducer>,
    pub cache: Arc<RedisCache>,
}

impl AppState {
    /// Create application state from a database pool, Kafka bootstrap servers, and Redis URL.
    pub fn new(pool: PgPool, kafka_bootstrap_servers: &str, redis_url: &str) -> Self {
        let workflow_storage = Arc::new(WorkflowDefinitionStorage::new(pool.clone()));
        let run_storage = Arc::new(WorkflowRunStorage::new(pool));

        let workflow_service = Arc::new(WorkflowService::new(workflow_storage, run_storage));

        let kafka_producer = Arc::new(
            KafkaProducer::new(kafka_bootstrap_servers)
                .expect("Failed to create Kafka producer"),
        );

        let cache = Arc::new(
            RedisCache::new(redis_url).expect("Failed to create Redis cache client"),
        );

        Self {
            workflow_service,
            kafka_producer,
            cache,
        }
    }
}
