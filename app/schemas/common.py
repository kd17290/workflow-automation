from enum import Enum


class WorkflowStatus(str, Enum):
    """Enumeration of workflow execution statuses."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"


class StepStatus(str, Enum):
    """Enumeration of workflow step statuses."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
