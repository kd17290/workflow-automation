from fastapi import APIRouter
from fastapi import Depends

from app.api.deps import get_workflow_service
from app.cache.redis_cache import cache_get, cache_set, cache_delete
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

    # Cache the newly created workflow (60s TTL)
    cache_set(f"workflow:{workflow.uuid}", workflow.model_dump(), ttl=60)

    return {
        "message": "Workflow created successfully",
        "workflow_id": workflow.uuid,
    }


@router.get("/{workflow_uuid}")
async def get_workflow(
    workflow_uuid: str, service: WorkflowService = Depends(get_workflow_service)
):
    """Get workflow definition"""
    # Check cache first
    cache_key = f"workflow:{workflow_uuid}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    result = service.load_workflow(workflow_uuid)
    if result:
        cache_set(cache_key, result.model_dump(), ttl=60)
    return result
