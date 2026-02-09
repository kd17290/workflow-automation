from sqlalchemy.orm import Session

from app.db.models.health import HealthStatus


def save_health_status(db: Session, status: str):
    """
    Save the health status to the database.

    Args:
        db (Session): The database session.
        status (str): The status string to save (e.g., "ok").
    """
    print(f"Saving health status: {status}")
    health = HealthStatus(status=status)
    db.add(health)
    db.commit()
