"""
Kafka worker service for async workflow execution.

This module runs as a standalone service that:
1. Consumes workflow trigger events from Kafka
2. Executes workflows asynchronously
3. Publishes completion events back to Kafka
"""
import asyncio
import logging
import signal
import sys

from app.core.config import settings
from app.messaging.kafka import KafkaProducer, KafkaConsumer
from app.messaging.events import WorkflowTriggerEvent, WorkflowCompletedEvent
from app.services.workflow import WorkflowService
from app.storage.enum import StorageType
from app.schemas.common import WorkflowStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class WorkflowWorker:
    """
    Worker that consumes workflow events and executes workflows.
    """

    def __init__(self):
        """Initialize the worker with Kafka consumer/producer and workflow service."""
        self._consumer = KafkaConsumer(
            topic=settings.KAFKA_TOPIC_WORKFLOW_TRIGGER,
            group_id=settings.KAFKA_CONSUMER_GROUP,
        )
        self._producer = KafkaProducer()
        self._workflow_service = WorkflowService(StorageType.POSTGRES)
        self._shutdown = False

    async def start(self) -> None:
        """Start the worker and begin consuming messages."""
        logger.info("Starting workflow worker...")

        await self._producer.start()
        await self._consumer.start()

        logger.info("Workflow worker started. Waiting for messages...")

        try:
            await self._consumer.consume(self._handle_message)
        except asyncio.CancelledError:
            logger.info("Worker received cancellation")
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the worker and clean up resources."""
        logger.info("Stopping workflow worker...")
        self._shutdown = True
        await self._consumer.stop()
        await self._producer.stop()
        logger.info("Workflow worker stopped")

    async def _handle_message(self, message: dict) -> None:
        """
        Handle a workflow trigger event.

        Args:
            message: The raw message payload from Kafka.
        """
        try:
            event = WorkflowTriggerEvent(**message)
            logger.info(f"Processing workflow trigger: run_id={event.run_id}")

            # Execute the workflow
            await self._workflow_service.execute_workflow(event.run_id)

            # Get the final status
            run = self._workflow_service.load_workflow_run(event.run_id)
            status = run.status if run else WorkflowStatus.FAILED
            error = run.error if run else "Run not found"

            # Publish completion event
            completed_event = WorkflowCompletedEvent(
                run_id=event.run_id,
                workflow_id=event.workflow_id,
                status=status,
                error=error if status == WorkflowStatus.FAILED else None,
            )

            await self._producer.send(
                topic=settings.KAFKA_TOPIC_WORKFLOW_COMPLETED,
                value=completed_event.model_dump(),
                key=event.run_id,
            )

            logger.info(f"Workflow completed: run_id={event.run_id}, status={status}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # In production, you might want to send to a dead-letter queue
            raise


async def main() -> None:
    """Main entry point for the worker service."""
    worker = WorkflowWorker()

    # Handle graceful shutdown
    loop = asyncio.get_event_loop()
    shutdown_event = asyncio.Event()

    def signal_handler():
        logger.info("Shutdown signal received")
        shutdown_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        # Start worker in background
        worker_task = asyncio.create_task(worker.start())

        # Wait for shutdown signal
        await shutdown_event.wait()

        # Cancel worker
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass

    except Exception as e:
        logger.error(f"Worker error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
