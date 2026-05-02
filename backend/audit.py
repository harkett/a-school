from sqlalchemy.orm import Session
from backend.models_db import AdminAuditLog


def log_admin_action(
    db: Session,
    admin_email: str,
    action: str,
    target_email: str | None = None,
    ip: str | None = None,
    details: str = "",
) -> None:
    db.add(AdminAuditLog(
        admin_email=admin_email,
        action=action,
        target_email=target_email,
        ip_address=ip,
        details=details,
    ))
    db.commit()
