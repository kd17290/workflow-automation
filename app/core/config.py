from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Workflow Automation"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL
    POSTGRES_HOST: str
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_CONSUMER_GROUP: str = "workflow-workers"
    KAFKA_TOPIC_WORKFLOW_TRIGGER: str = "workflow.trigger"
    KAFKA_TOPIC_WORKFLOW_COMPLETED: str = "workflow.completed"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
