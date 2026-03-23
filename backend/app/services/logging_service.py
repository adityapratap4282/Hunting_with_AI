from sqlalchemy.orm import Session

from app.models import ActivityLog


def log_event(db: Session, *, event_type: str, entity_type: str, entity_id: str, message: str) -> None:
    db.add(
        ActivityLog(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
        )
    )
    db.commit()
