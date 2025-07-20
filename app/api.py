from datetime import datetime

from fastapi import APIRouter
from fastapi import HTTPException
from starlette.background import BackgroundTasks

from app.models import TriggerRequest
from app.models import WorkflowDefinition
from app.models import WorkflowRun
from app.models import WorkflowStatus
from app.storage.enum import StorageType
from app.workflow_service import WorkflowService

router = APIRouter()

STORAGE = (
    StorageType.FILE_SYSTEM
)  # Example storage type, which can be changed as needed

service = WorkflowService(STORAGE)


@router.post("/workflows")
async def create_workflow(workflow: WorkflowDefinition):
    """Create a new workflow definition"""
    service.create_workflow(workflow)
    return {
        "message": "Workflow created successfully",
        "workflow_id": workflow.uuid,
    }


@router.get("/workflows/{workflow_uuid}")
async def get_workflow(workflow_uuid: str):
    """Get workflow definition"""
    return service.load_workflow(workflow_uuid)


@router.post("/trigger")
async def trigger_workflow(request: TriggerRequest, background_tasks: BackgroundTasks):
    """Trigger a workflow execution"""
    # Check if workflow exists
    workflow = service.load_workflow(request.workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=404, detail=f"Workflow {request.workflow_id} not found"
        )

    # Create workflow run
    run = WorkflowRun(
        workflow_id=request.workflow_id,
        status=WorkflowStatus.PENDING,
        payload=request.payload,
        started_at=datetime.now().isoformat(),
    )

    # Save run
    service.create_workflow_run(run)
    background_tasks.add_task(service.execute_workflow, run.uuid)
    return {"run_id": run.uuid, "status": "triggered"}


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get workflow run details"""
    run = service.load_workflow_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return run


@router.get("/runs")
async def list_runs():
    """List all workflow runs"""
    return service.list_runs()
