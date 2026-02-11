/// Application configuration loaded from environment variables.
///
/// Mirrors the Python Settings class from app/core/config.py.
/// All values are sourced from environment variables with sensible defaults.
#[derive(Debug, Clone)]
pub struct Settings {
    pub project_name: String,
    pub version: String,
    pub api_v1_str: String,

    // PostgreSQL (via PgBouncer)
    pub postgres_host: String,
    pub postgres_port: String,
    pub postgres_db: String,
    pub postgres_user: String,
    pub postgres_password: String,

    // Kafka
    pub kafka_bootstrap_servers: String,
    pub kafka_consumer_group: String,
    pub kafka_topic_workflow_trigger: String,
    pub kafka_topic_workflow_completed: String,

    // Redis
    pub redis_url: String,
}

impl Settings {
    /// Load settings from environment variables.
    ///
    /// Required env vars: POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD.
    /// All other settings have defaults.
    pub fn from_env() -> Self {
        Self {
            project_name: std::env::var("PROJECT_NAME")
                .unwrap_or_else(|_| "Workflow Automation".to_string()),
            version: std::env::var("VERSION").unwrap_or_else(|_| "1.0.0".to_string()),
            api_v1_str: std::env::var("API_V1_STR").unwrap_or_else(|_| "/api/v1".to_string()),

            postgres_host: std::env::var("POSTGRES_HOST")
                .expect("POSTGRES_HOST must be set"),
            postgres_port: std::env::var("POSTGRES_PORT")
                .unwrap_or_else(|_| "5432".to_string()),
            postgres_db: std::env::var("POSTGRES_DB")
                .expect("POSTGRES_DB must be set"),
            postgres_user: std::env::var("POSTGRES_USER")
                .expect("POSTGRES_USER must be set"),
            postgres_password: std::env::var("POSTGRES_PASSWORD")
                .expect("POSTGRES_PASSWORD must be set"),

            kafka_bootstrap_servers: std::env::var("KAFKA_BOOTSTRAP_SERVERS")
                .unwrap_or_else(|_| "kafka:9092".to_string()),
            kafka_consumer_group: std::env::var("KAFKA_CONSUMER_GROUP")
                .unwrap_or_else(|_| "workflow-workers-rust".to_string()),
            kafka_topic_workflow_trigger: std::env::var("KAFKA_TOPIC_WORKFLOW_TRIGGER")
                .unwrap_or_else(|_| "workflow.trigger.rust".to_string()),
            kafka_topic_workflow_completed: std::env::var("KAFKA_TOPIC_WORKFLOW_COMPLETED")
                .unwrap_or_else(|_| "workflow.completed.rust".to_string()),

            redis_url: std::env::var("REDIS_URL")
                .unwrap_or_else(|_| "redis://redis:6379".to_string()),
        }
    }

    /// Build the PostgreSQL connection URL.
    pub fn database_url(&self) -> String {
        format!(
            "postgresql://{}:{}@{}:{}/{}",
            self.postgres_user, self.postgres_password, self.postgres_host, self.postgres_port, self.postgres_db
        )
    }
}
