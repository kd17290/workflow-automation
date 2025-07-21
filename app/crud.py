from sqlalchemy.orm import Session

from app.models import HealthStatus


def save_health_status(db: Session, status: str):
    print(f"Saving health status: {status}")
    health = HealthStatus(status=status)
    db.add(health)
    db.commit()
