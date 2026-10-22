from app.extensions import db
from app.models.admin_audit_log import AdminAuditLog
from flask_login import current_user


def record_admin_event(event, admin_user_id=None, detail=None):
    """Store a concise audit event without credentials or customer data."""
    if admin_user_id is None and current_user.is_authenticated:
        admin_user_id = current_user.id
    db.session.add(AdminAuditLog(
        event=event,
        admin_user_id=admin_user_id,
        detail=detail,
    ))
    db.session.commit()
