import logging
from enum import Enum
from typing import Annotated
from typing import Any
from typing import Union

from pydantic import BaseModel
from pydantic import Field

from app.connector.delay import DelayOutput
from app.connector.delay import DelayWorkflowStep
from app.connector.webhook import WebhookResponse
from app.connector.webhook import WebhookWorkflowStep

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class TriggerRequest(BaseModel):
    workflow_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


WorkflowStep = Annotated[
    Union[WebhookWorkflowStep, DelayWorkflowStep], Field(discriminator="type")
]


WorkflowStepResponse = Annotated[
    Union[DelayOutput, WebhookResponse], Field(discriminator="type")
]


class WorkflowDefinition(BaseModel):
    uuid: str | None = None
    id: str | None = None
    name: str
    description: str | None = None
    steps: list[WorkflowStep]


class StepResult(BaseModel):
    step_name: str
    status: StepStatus
    started_at: str
    completed_at: str | None = None
    output: WorkflowStepResponse | None = None
    error: str | None = None


class WorkflowRun(BaseModel):
    uuid: str | None = None
    id: str | None = None
    workflow_id: str
    status: WorkflowStatus
    payload: dict[str, Any]
    started_at: str
    completed_at: str | None = None
    error: str | None = None
    step_results: dict[str, StepResult] = Field(default_factory=dict)
