"""
Tests for Kafka producer and consumer.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.messaging.kafka import KafkaProducer, KafkaConsumer
from app.messaging.events import WorkflowTriggerEvent, WorkflowCompletedEvent


class TestWorkflowTriggerEvent:
    """Tests for WorkflowTriggerEvent schema."""

    def test_create_event(self):
        """Test creating a trigger event."""
        event = WorkflowTriggerEvent(
            run_id="run-123",
            workflow_id="workflow-456",
            payload={"key": "value"},
        )
        assert event.run_id == "run-123"
        assert event.workflow_id == "workflow-456"
        assert event.payload == {"key": "value"}

    def test_event_serialization(self):
        """Test event can be serialized to dict."""
        event = WorkflowTriggerEvent(
            run_id="run-123",
            workflow_id="workflow-456",
            payload={"key": "value"},
        )
        data = event.model_dump()
        assert data["run_id"] == "run-123"
        assert data["workflow_id"] == "workflow-456"
        assert data["payload"] == {"key": "value"}


class TestWorkflowCompletedEvent:
    """Tests for WorkflowCompletedEvent schema."""

    def test_create_success_event(self):
        """Test creating a success completion event."""
        event = WorkflowCompletedEvent(
            run_id="run-123",
            workflow_id="workflow-456",
            status="SUCCESS",
        )
        assert event.run_id == "run-123"
        assert event.status == "SUCCESS"
        assert event.error is None

    def test_create_failure_event(self):
        """Test creating a failure completion event."""
        event = WorkflowCompletedEvent(
            run_id="run-123",
            workflow_id="workflow-456",
            status="FAILED",
            error="Something went wrong",
        )
        assert event.status == "FAILED"
        assert event.error == "Something went wrong"


class TestKafkaProducer:
    """Tests for KafkaProducer."""

    @pytest.mark.asyncio
    async def test_producer_start_stop(self):
        """Test producer can start and stop."""
        with patch("app.messaging.kafka.AIOKafkaProducer") as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer

            producer = KafkaProducer(bootstrap_servers="localhost:9092")
            await producer.start()

            mock_producer_class.assert_called_once()
            mock_producer.start.assert_called_once()

            await producer.stop()
            mock_producer.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_producer_send(self):
        """Test producer can send messages."""
        with patch("app.messaging.kafka.AIOKafkaProducer") as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer

            producer = KafkaProducer(bootstrap_servers="localhost:9092")
            await producer.start()

            await producer.send(
                topic="test-topic",
                value={"key": "value"},
                key="test-key",
            )

            mock_producer.send_and_wait.assert_called_once()
            call_args = mock_producer.send_and_wait.call_args
            assert call_args.kwargs["key"] == b"test-key"

            await producer.stop()

    @pytest.mark.asyncio
    async def test_producer_context_manager(self):
        """Test producer can be used as async context manager."""
        with patch("app.messaging.kafka.AIOKafkaProducer") as mock_producer_class:
            mock_producer = AsyncMock()
            mock_producer_class.return_value = mock_producer

            async with KafkaProducer(bootstrap_servers="localhost:9092") as producer:
                assert producer is not None
                mock_producer.start.assert_called_once()

            mock_producer.stop.assert_called_once()


class TestKafkaConsumer:
    """Tests for KafkaConsumer."""

    @pytest.mark.asyncio
    async def test_consumer_start_stop(self):
        """Test consumer can start and stop."""
        with patch("app.messaging.kafka.AIOKafkaConsumer") as mock_consumer_class:
            mock_consumer = AsyncMock()
            mock_consumer_class.return_value = mock_consumer

            consumer = KafkaConsumer(
                topic="test-topic",
                bootstrap_servers="localhost:9092",
            )
            await consumer.start()

            mock_consumer_class.assert_called_once()
            mock_consumer.start.assert_called_once()

            await consumer.stop()
            mock_consumer.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_consumer_context_manager(self):
        """Test consumer can be used as async context manager."""
        with patch("app.messaging.kafka.AIOKafkaConsumer") as mock_consumer_class:
            mock_consumer = AsyncMock()
            mock_consumer_class.return_value = mock_consumer

            async with KafkaConsumer(
                topic="test-topic",
                bootstrap_servers="localhost:9092",
            ) as consumer:
                assert consumer is not None
                mock_consumer.start.assert_called_once()

            mock_consumer.stop.assert_called_once()
