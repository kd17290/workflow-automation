from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from app.api.deps import get_workflow_service
from app.services.workflow import WorkflowService

router = APIRouter()


@router.get("/{run_id}")
async def get_run(
    run_id: str, service: WorkflowService = Depends(get_workflow_service)
):
    """Get workflow run details"""
    run = service.load_workflow_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return run


@router.get("/")
async def list_runs(service: WorkflowService = Depends(get_workflow_service)):
    """List all workflow runs"""
    return service.list_runs()
