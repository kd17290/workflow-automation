from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from app.api.deps import get_workflow_service
from app.cache.redis_cache import cache_get, cache_set
from app.core.config import settings
from app.services.workflow import WorkflowService

router = APIRouter()


@router.get("/{run_id}")
async def get_run(
    run_id: str, service: WorkflowService = Depends(get_workflow_service)
):
    """Get workflow run details"""
    # Check cache first
    cache_key = f"run:{run_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    run = service.load_workflow_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")

    # Cache for 10s (runs change status so short TTL)
    run_data = run.model_dump()
    cache_set(cache_key, run_data, ttl=10)
    return run_data


@router.get("/")
async def list_runs(
    limit: int = Query(default=50, ge=1, le=200, description="Max items per page"),
    cursor: str | None = Query(default=None, description="Cursor for pagination (uuid)"),
    service: WorkflowService = Depends(get_workflow_service),
):
    """List workflow runs with cursor-based pagination"""
    runs, next_cursor = service.list_runs_paginated(limit=limit, cursor=cursor)
    return {
        "items": runs,
        "next_cursor": next_cursor,
        "limit": limit,
    }
