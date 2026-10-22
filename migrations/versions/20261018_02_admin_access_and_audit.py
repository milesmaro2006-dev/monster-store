"""Add admin authorization, password rotation, and audit records."""

from alembic import op
import sqlalchemy as sa


revision = "20261018_02"
down_revision = "20261018_01"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("admin_users") as batch_op:
        batch_op.add_column(sa.Column(
            "is_admin", sa.Boolean(), nullable=False, server_default=sa.true()
        ))
        batch_op.add_column(sa.Column(
            "must_change_password", sa.Boolean(), nullable=False, server_default=sa.false()
        ))
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_user_id", sa.Integer(), nullable=True),
        sa.Column("event", sa.String(length=80), nullable=False),
        sa.Column("detail", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["admin_user_id"], ["admin_users.id"]),
    )
    op.create_index("ix_admin_audit_logs_event", "admin_audit_logs", ["event"])
    op.create_index("ix_admin_audit_logs_created_at", "admin_audit_logs", ["created_at"])


def downgrade():
    op.drop_index("ix_admin_audit_logs_created_at", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_event", table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")
    with op.batch_alter_table("admin_users") as batch_op:
        batch_op.drop_column("must_change_password")
        batch_op.drop_column("is_admin")
