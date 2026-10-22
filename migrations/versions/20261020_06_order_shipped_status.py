"""Normalize order progress statuses to the admin status vocabulary."""

from alembic import op
import sqlalchemy as sa


revision = "20261020_06"
down_revision = "20261020_05"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    for old_status, new_status in (("preparing", "confirmed"), ("out_for_delivery", "shipped")):
        connection.execute(
            sa.text("UPDATE orders SET status = :new WHERE status = :old"),
            {"old": old_status, "new": new_status},
        )
        connection.execute(
            sa.text("UPDATE order_status_history SET old_status = :new WHERE old_status = :old"),
            {"old": old_status, "new": new_status},
        )
        connection.execute(
            sa.text("UPDATE order_status_history SET new_status = :new WHERE new_status = :old"),
            {"old": old_status, "new": new_status},
        )


def downgrade():
    connection = op.get_bind()
    connection.execute(sa.text("UPDATE orders SET status = 'out_for_delivery' WHERE status = 'shipped'"))
    connection.execute(sa.text("UPDATE order_status_history SET old_status = 'out_for_delivery' WHERE old_status = 'shipped'"))
    connection.execute(sa.text("UPDATE order_status_history SET new_status = 'out_for_delivery' WHERE new_status = 'shipped'"))
    # "confirmed" can be a legacy confirmed state or a migrated "preparing" state,
    # so it cannot be safely reversed without recording extra migration metadata.
