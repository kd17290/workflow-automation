from fastapi import APIRouter
from fastapi import Depends

from app.api.deps import get_workflow_service
from app.schemas.workflow import WorkflowDefinition
from app.services.workflow import WorkflowService

router = APIRouter()


@router.post("/")
async def create_workflow(
    workflow: WorkflowDefinition,
    service: WorkflowService = Depends(get_workflow_service),
):
    """Create a new workflow definition"""
    service.create_workflow(workflow)
    return {
        "message": "Workflow created successfully",
        "workflow_id": workflow.uuid,
    }


@router.get("/{workflow_uuid}")
async def get_workflow(
    workflow_uuid: str, service: WorkflowService = Depends(get_workflow_service)
):
    """Get workflow definition"""
    return service.load_workflow(workflow_uuid)
