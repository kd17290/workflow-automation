import uuid
from datetime import datetime

from fastapi import APIRouter
from fastapi import HTTPException
from starlette.background import BackgroundTasks

from app.engine import WorkflowEngine
from app.models import TriggerRequest
from app.models import WorkflowDefinition
from app.models import WorkflowRun
from app.models import WorkflowStatus
from app.storage import WorkflowStorage

router = APIRouter()

# Initialize storage and engine
storage = WorkflowStorage()
engine = WorkflowEngine(storage)


@router.post("/api/trigger")
async def trigger_workflow(request: TriggerRequest, background_tasks: BackgroundTasks):
    """Trigger a workflow execution"""
    # Check if workflow exists
    workflow = storage.load_workflow(request.workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=404, detail=f"Workflow {request.workflow_id} not found"
        )

    # Create workflow run
    run_id = str(uuid.uuid4())
    run = WorkflowRun(
        id=run_id,
        workflow_id=request.workflow_id,
        status=WorkflowStatus.PENDING,
        payload=request.payload,
        started_at=datetime.now().isoformat(),
    )

    # Save run
    storage.save_run(run)

    # Execute workflow in background
    background_tasks.add_task(engine.execute_workflow, run_id)

    return {"run_id": run_id, "status": "triggered"}


@router.post("/api/workflows")
async def create_workflow(workflow: WorkflowDefinition):
    """Create a new workflow definition"""
    storage.save_workflow(workflow)
    return {"message": "Workflow created successfully", "workflow_id": workflow.id}


@router.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get workflow definition"""
    workflow = storage.load_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    """Get workflow run details"""
    run = storage.load_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return run


@router.get("/api/runs")
async def list_runs():
    """List all workflow runs"""
    run_ids = storage.list_runs()
    runs = []
    for run_id in run_ids:
        run = storage.load_run(run_id)
        if run:
            runs.append(run)
    return runs


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
