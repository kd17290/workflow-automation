from typing import Generator
from app.db.session import SessionLocal
from app.messaging.kafka import KafkaProducer
from app.storage.enum import StorageType
from app.services.workflow import WorkflowService


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_workflow_service() -> WorkflowService:
    """
    Dependency provider for WorkflowService.

    Returns:
        WorkflowService: An instance of WorkflowService configured with POSTGRES storage.
    """
    return WorkflowService(StorageType.POSTGRES)


# Shared Kafka producer instance — initialized once at app startup via lifespan().
_kafka_producer: KafkaProducer | None = None


def set_kafka_producer(producer: KafkaProducer) -> None:
    """Set the shared Kafka producer (called from lifespan startup)."""
    global _kafka_producer
    _kafka_producer = producer


def get_kafka_producer() -> KafkaProducer:
    """
    Dependency provider for the shared KafkaProducer.

    Returns:
        KafkaProducer: The singleton Kafka producer started at app startup.
    """
    if _kafka_producer is None:
        raise RuntimeError("Kafka producer not initialized. App startup may have failed.")
    return _kafka_producer
