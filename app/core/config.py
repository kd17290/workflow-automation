from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Workflow Automation"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL (via PgBouncer)
    POSTGRES_HOST: str
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_CONSUMER_GROUP: str = "workflow-workers"
    KAFKA_TOPIC_WORKFLOW_TRIGGER: str = "workflow.trigger"
    KAFKA_TOPIC_WORKFLOW_COMPLETED: str = "workflow.completed"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: str = "6379"

    # Pagination
    DEFAULT_PAGE_LIMIT: int = 50

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
