from typing import Generator
from app.db.session import SessionLocal
from app.storage.enum import StorageType
from app.services.workflow import WorkflowService


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_workflow_service() -> WorkflowService:
    """
    Dependency provider for WorkflowService.

    Returns:
        WorkflowService: An instance of WorkflowService configured with POSTGRES storage.
    """
    return WorkflowService(StorageType.POSTGRES)
