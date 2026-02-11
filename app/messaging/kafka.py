"""
Kafka producer and consumer implementations.
"""
import asyncio
import json
import logging
from typing import Any, Callable, Awaitable

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KafkaProducer:
    """
    Async Kafka producer for publishing events.

    Uses asyncio.Lock to prevent race conditions during lazy initialization
    when multiple concurrent requests try to start the producer simultaneously.
    """

    def __init__(self, bootstrap_servers: str | None = None):
        """
        Initialize the Kafka producer.

        Args:
            bootstrap_servers: Kafka broker addresses. Defaults to settings.
        """
        self._bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self._producer: AIOKafkaProducer | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the Kafka producer connection (thread-safe with asyncio.Lock)."""
        async with self._lock:
            if self._producer is None:
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=self._bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    max_batch_size=32768,
                    linger_ms=10,
                    acks="all",
                )
                await self._producer.start()
                logger.info(f"Kafka producer started: {self._bootstrap_servers}")

    async def stop(self) -> None:
        """Stop the Kafka producer connection."""
        async with self._lock:
            if self._producer is not None:
                await self._producer.stop()
                self._producer = None
                logger.info("Kafka producer stopped")

    async def send(self, topic: str, value: dict[str, Any], key: str | None = None) -> None:
        """
        Send a message to a Kafka topic.

        Args:
            topic: The Kafka topic name.
            value: The message payload (will be JSON serialized).
            key: Optional message key for partitioning.
        """
        if self._producer is None:
            await self.start()

        try:
            key_bytes = key.encode("utf-8") if key else None
            await self._producer.send_and_wait(topic, value=value, key=key_bytes)
            logger.info(f"Message sent to {topic}: {value}")
        except KafkaError as e:
            logger.error(f"Failed to send message to {topic}: {e}")
            raise

    async def __aenter__(self) -> "KafkaProducer":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()


class KafkaConsumer:
    """
    Async Kafka consumer for processing events.
    """

    def __init__(
        self,
        topic: str,
        group_id: str | None = None,
        bootstrap_servers: str | None = None,
    ):
        """
        Initialize the Kafka consumer.

        Args:
            topic: The Kafka topic to subscribe to.
            group_id: Consumer group ID. Defaults to settings.
            bootstrap_servers: Kafka broker addresses. Defaults to settings.
        """
        self._topic = topic
        self._group_id = group_id or settings.KAFKA_CONSUMER_GROUP
        self._bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self._consumer: AIOKafkaConsumer | None = None
        self._running = False

    async def start(self) -> None:
        """Start the Kafka consumer connection."""
        if self._consumer is None:
            self._consumer = AIOKafkaConsumer(
                self._topic,
                bootstrap_servers=self._bootstrap_servers,
                group_id=self._group_id,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="earliest",
            )
            await self._consumer.start()
            self._running = True
            logger.info(
                f"Kafka consumer started: topic={self._topic}, group={self._group_id}"
            )

    async def stop(self) -> None:
        """Stop the Kafka consumer connection."""
        self._running = False
        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None
            logger.info("Kafka consumer stopped")

    async def consume(
        self, handler: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Start consuming messages and pass them to the handler.

        Args:
            handler: Async function to process each message.
        """
        if self._consumer is None:
            await self.start()

        logger.info(f"Starting to consume from {self._topic}...")
        try:
            async for message in self._consumer:
                if not self._running:
                    break
                try:
                    logger.info(f"Received message from {self._topic}: {message.value}")
                    await handler(message.value)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Continue processing other messages
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            raise

    async def __aenter__(self) -> "KafkaConsumer":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()
