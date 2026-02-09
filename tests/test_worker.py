"""
Tests for the workflow worker service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.worker.main import WorkflowWorker
from app.messaging.events import WorkflowTriggerEvent
from app.schemas.common import WorkflowStatus


class TestWorkflowWorker:
    """Tests for WorkflowWorker."""

    @pytest.mark.asyncio
    async def test_handle_message_success(self):
        """Test worker handles successful workflow execution."""
        with patch("app.worker.main.KafkaConsumer") as mock_consumer_class, \
             patch("app.worker.main.KafkaProducer") as mock_producer_class, \
             patch("app.worker.main.WorkflowService") as mock_service_class:

            # Setup mocks
            mock_consumer = AsyncMock()
            mock_producer = AsyncMock()
            mock_service = MagicMock()
            mock_consumer_class.return_value = mock_consumer
            mock_producer_class.return_value = mock_producer
            mock_service_class.return_value = mock_service

            # Mock successful workflow run
            mock_run = MagicMock()
            mock_run.status = WorkflowStatus.SUCCESS
            mock_run.error = None
            mock_service.load_workflow_run.return_value = mock_run
            mock_service.execute_workflow = AsyncMock()

            # Create worker and call handler directly
            worker = WorkflowWorker()
            worker._workflow_service = mock_service
            worker._producer = mock_producer

            message = {
                "run_id": "run-123",
                "workflow_id": "workflow-456",
                "payload": {"key": "value"},
            }

            await worker._handle_message(message)

            # Verify workflow was executed
            mock_service.execute_workflow.assert_called_once_with("run-123")

            # Verify completion event was published
            mock_producer.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_message_failure(self):
        """Test worker handles failed workflow execution."""
        with patch("app.worker.main.KafkaConsumer") as mock_consumer_class, \
             patch("app.worker.main.KafkaProducer") as mock_producer_class, \
             patch("app.worker.main.WorkflowService") as mock_service_class:

            # Setup mocks
            mock_consumer = AsyncMock()
            mock_producer = AsyncMock()
            mock_service = MagicMock()
            mock_consumer_class.return_value = mock_consumer
            mock_producer_class.return_value = mock_producer
            mock_service_class.return_value = mock_service

            # Mock failed workflow run
            mock_run = MagicMock()
            mock_run.status = WorkflowStatus.FAILED
            mock_run.error = "Step failed"
            mock_service.load_workflow_run.return_value = mock_run
            mock_service.execute_workflow = AsyncMock()

            # Create worker and call handler directly
            worker = WorkflowWorker()
            worker._workflow_service = mock_service
            worker._producer = mock_producer

            message = {
                "run_id": "run-123",
                "workflow_id": "workflow-456",
                "payload": {"key": "value"},
            }

            await worker._handle_message(message)

            # Verify workflow was executed
            mock_service.execute_workflow.assert_called_once_with("run-123")

            # Verify completion event was published with error
            mock_producer.send.assert_called_once()
            call_args = mock_producer.send.call_args
            assert call_args.kwargs["value"]["status"] == WorkflowStatus.FAILED
            assert call_args.kwargs["value"]["error"] == "Step failed"

    @pytest.mark.asyncio
    async def test_handle_invalid_message(self):
        """Test worker handles invalid message gracefully."""
        with patch("app.worker.main.KafkaConsumer") as mock_consumer_class, \
             patch("app.worker.main.KafkaProducer") as mock_producer_class, \
             patch("app.worker.main.WorkflowService") as mock_service_class:

            mock_consumer = AsyncMock()
            mock_producer = AsyncMock()
            mock_service = MagicMock()
            mock_consumer_class.return_value = mock_consumer
            mock_producer_class.return_value = mock_producer
            mock_service_class.return_value = mock_service

            worker = WorkflowWorker()
            worker._workflow_service = mock_service
            worker._producer = mock_producer

            # Invalid message missing required fields
            message = {"run_id": "run-123"}

            with pytest.raises(Exception):
                await worker._handle_message(message)
