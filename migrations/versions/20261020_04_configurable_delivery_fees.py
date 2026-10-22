"""Make metro and home delivery rates editable in store settings."""

from alembic import op
import sqlalchemy as sa


revision = "20261020_04"
down_revision = "20261020_03"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("store_settings") as batch_op:
        batch_op.add_column(sa.Column(
            "metro_pickup_fee", sa.Numeric(10, 2), nullable=False, server_default="60.00"
        ))
        batch_op.add_column(sa.Column(
            "home_delivery_fee", sa.Numeric(10, 2), nullable=False, server_default="95.00"
        ))


def downgrade():
    with op.batch_alter_table("store_settings") as batch_op:
        batch_op.drop_column("home_delivery_fee")
        batch_op.drop_column("metro_pickup_fee")
