from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.session import Base


class WorkflowDefinitionModel(Base):
    """
    Database model for WorkflowDefinition.
    """

    __tablename__ = "workflow_definitions"

    uuid: Mapped[str] = mapped_column(primary_key=True, index=True)
    id: Mapped[str | None]
    name: Mapped[str]
    description: Mapped[str | None]
    steps: Mapped[list[dict]] = mapped_column(JSONB)
