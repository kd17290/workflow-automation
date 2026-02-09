"""
Kafka event schemas for workflow automation.
"""
from typing import Any
from pydantic import BaseModel


class WorkflowTriggerEvent(BaseModel):
    """
    Event published when a workflow is triggered.
    Consumed by workers to execute the workflow.
    """

    run_id: str
    workflow_id: str
    payload: dict[str, Any]


class WorkflowCompletedEvent(BaseModel):
    """
    Event published when a workflow execution completes.
    Can be used for notifications, callbacks, or chaining.
    """

    run_id: str
    workflow_id: str
    status: str  # SUCCESS, FAILED
    error: str | None = None
