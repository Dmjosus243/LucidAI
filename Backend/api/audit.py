import uuid
from sqlalchemy.orm import Session
from database import AuditLog

def log_action(
    db: Session,
    user_id: str,
    action: str,
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    try:
        entry = AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            details=details or {},
            ip_address=ip_address,
        )
        db.add(entry)
        db.commit()
    except Exception:
        db.rollback()
