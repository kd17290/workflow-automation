from typing import Any
from pydantic import BaseModel, Field

from app.schemas.common import WorkflowStatus
from app.schemas.workflow import StepResult


class WorkflowRun(BaseModel):
    """
    State of a workflow execution run.

    Attributes:
        uuid (str | None): Unique run ID.
        id (str | None): Optional external ID.
        workflow_id (str): ID of the workflow definition.
        status (WorkflowStatus): Overall run status.
        payload (dict[str, Any]): Initial input payload.
        started_at (str): Start timestamp.
        completed_at (str | None): Completion timestamp.
        error (str | None): Error message if failed.
        step_results (dict[str, StepResult]): Results of individual steps.
    """

    uuid: str | None = None
    id: str | None = None
    workflow_id: str
    status: WorkflowStatus
    payload: dict[str, Any]
    started_at: str
    completed_at: str | None = None
    error: str | None = None
    step_results: dict[str, StepResult] = Field(default_factory=dict)
