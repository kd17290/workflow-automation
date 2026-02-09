from fastapi import APIRouter

from app.api.v1.endpoints import workflows, runs, trigger

api_router = APIRouter()
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(runs.router, prefix="/runs", tags=["runs"])
api_router.include_router(trigger.router, prefix="/trigger", tags=["trigger"])
