import logging
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

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
    payload: Dict[str, Any] = Field(default_factory=dict)


class WorkflowStep(BaseModel):
    name: str
    type: str
    config: Dict[str, Any]


class WorkflowDefinition(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    steps: List[WorkflowStep]


class WorkflowRun(BaseModel):
    id: str
    workflow_id: str
    status: WorkflowStatus
    payload: Dict[str, Any]
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    step_results: Dict[str, Any] = Field(default_factory=dict)


class StepResult(BaseModel):
    step_name: str
    status: StepStatus
    started_at: str
    completed_at: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
