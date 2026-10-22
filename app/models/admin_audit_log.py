from datetime import datetime
from app.extensions import db


class AdminAuditLog(db.Model):
    __tablename__ = "admin_audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey("admin_users.id"), nullable=True)
    event = db.Column(db.String(80), nullable=False, index=True)
    detail = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    admin_user = db.relationship("AdminUser")
