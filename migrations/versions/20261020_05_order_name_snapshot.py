"""Snapshot the English product name on each order item."""

from alembic import op
import sqlalchemy as sa


revision = "20261020_05"
down_revision = "20261020_04"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("order_items") as batch_op:
        batch_op.add_column(
            sa.Column("name_en_snapshot", sa.String(length=150), nullable=True)
        )
    op.execute(sa.text(
        "UPDATE order_items SET name_en_snapshot = "
        "(SELECT products.name_en FROM products WHERE products.id = order_items.product_id) "
        "WHERE product_id IS NOT NULL"
    ))


def downgrade():
    with op.batch_alter_table("order_items") as batch_op:
        batch_op.drop_column("name_en_snapshot")
