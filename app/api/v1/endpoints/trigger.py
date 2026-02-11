"""
Workflow trigger endpoint.
"""
import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_workflow_service, get_kafka_producer
from app.core.config import settings
from app.messaging.kafka import KafkaProducer
from app.messaging.events import WorkflowTriggerEvent
from app.schemas.common import WorkflowStatus
from app.schemas.run import WorkflowRun
from app.schemas.workflow import TriggerRequest
from app.services.workflow import WorkflowService

router = APIRouter()


@router.post("/")
async def trigger_workflow(
    request: TriggerRequest,
    service: WorkflowService = Depends(get_workflow_service),
    producer: KafkaProducer = Depends(get_kafka_producer),
):
    """
    Trigger a workflow execution asynchronously via Kafka.

    This endpoint:
    1. Validates the workflow exists
    2. Creates a workflow run with PENDING status
    3. Publishes a trigger event to Kafka
    4. Returns immediately with the run ID

    The actual execution happens in the worker service.
    """
    # Check if workflow exists
    workflow = service.load_workflow(request.workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=404, detail=f"Workflow {request.workflow_id} not found"
        )

    # Create workflow run with PENDING status
    run = WorkflowRun(
        workflow_id=request.workflow_id,
        status=WorkflowStatus.PENDING,
        payload=request.payload,
        started_at=datetime.now().isoformat(),
    )

    # Save run to database
    service.create_workflow_run(run)

    # Publish trigger event to Kafka
    try:
        event = WorkflowTriggerEvent(
            run_id=run.uuid,
            workflow_id=request.workflow_id,
            payload=request.payload,
        )
        await producer.send(
            topic=settings.KAFKA_TOPIC_WORKFLOW_TRIGGER,
            value=event.model_dump(),
            key=run.uuid,
        )
    except Exception as e:
        # If Kafka fails, update run status to FAILED
        run.status = WorkflowStatus.FAILED
        run.error = f"Failed to queue workflow: {str(e)}"
        service.workflow_run_repository.update_workflow_run(run)
        raise HTTPException(status_code=500, detail=f"Failed to queue workflow: {e}")

    return {"run_id": run.uuid, "status": "triggered"}
