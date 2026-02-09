import datetime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.session import Base


class HealthStatus(Base):
    """
    Database model for system health checks.

    Attributes:
        id (int): Primary key.
        status (str): Health status string.
        timestamp (datetime): Creation time.
    """

    __tablename__ = "health_status"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    status: Mapped[str] = mapped_column(default="ok")
    timestamp: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now(datetime.UTC)
    )
