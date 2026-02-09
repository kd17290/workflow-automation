from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.session import Base


class WorkflowRunModel(Base):
    """
    Database model for WorkflowRun.
    """

    __tablename__ = "workflow_runs"

    uuid: Mapped[str] = mapped_column(primary_key=True, index=True)
    id: Mapped[str | None]
    workflow_id: Mapped[str] = mapped_column(index=True)
    status: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSONB)
    started_at: Mapped[str]
    completed_at: Mapped[str | None]
    error: Mapped[str | None]
    step_results: Mapped[dict] = mapped_column(JSONB)
