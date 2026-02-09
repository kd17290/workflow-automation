from typing import Annotated, Any, Union
from pydantic import BaseModel, Field

from app.connector.delay import DelayOutput, DelayWorkflowStep
from app.connector.webhook import WebhookResponse, WebhookWorkflowStep
from app.schemas.common import StepStatus


class TriggerRequest(BaseModel):
    """
    Request model for triggering a workflow.

    Attributes:
        workflow_id (str): The unique identifier of the workflow to trigger.
        payload (dict[str, Any]): Input data for the workflow execution.
    """

    workflow_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


WorkflowStep = Annotated[
    Union[WebhookWorkflowStep, DelayWorkflowStep], Field(discriminator="type")
]

WorkflowStepResponse = Annotated[
    Union[DelayOutput, WebhookResponse], Field(discriminator="type")
]


class WorkflowDefinition(BaseModel):
    """
    Definition of a workflow.

    Attributes:
        uuid (str | None): Unique internal ID.
        id (str | None): User-defined ID.
        name (str): Display name of the workflow.
        description (str | None): Optional description.
        steps (list[WorkflowStep]): List of steps to execute.
    """

    uuid: str | None = None
    id: str | None = None
    name: str
    description: str | None = None
    steps: list[WorkflowStep]


class StepResult(BaseModel):
    """
    Result of a single workflow step execution.

    Attributes:
        step_name (str): Name of the step.
        status (StepStatus): Execution status.
        started_at (str): ISO timestamp of start time.
        completed_at (str | None): ISO timestamp of completion time.
        output (WorkflowStepResponse | None): output data from the step.
        error (str | None): Error message if failed.
    """

    step_name: str
    status: StepStatus
    started_at: str
    completed_at: str | None = None
    output: WorkflowStepResponse | None = None
    error: str | None = None
