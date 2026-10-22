"""Add product brand and preserve it on order items."""

from alembic import op
import sqlalchemy as sa


revision = "20261020_03"
down_revision = "20261018_02"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("products") as batch_op:
        batch_op.add_column(sa.Column("brand", sa.String(length=100), nullable=True))
        batch_op.create_index("ix_products_brand", ["brand"], unique=False)
    op.execute(sa.text(
        "UPDATE products SET brand = 'Monster Energy' "
        "WHERE brand IS NULL AND (lower(coalesce(name, '')) LIKE '%monster%' "
        "OR lower(coalesce(name_en, '')) LIKE '%monster%' OR name LIKE '%مونستر%')"
    ))
    with op.batch_alter_table("order_items") as batch_op:
        batch_op.add_column(
            sa.Column("brand_snapshot", sa.String(length=100), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("order_items") as batch_op:
        batch_op.drop_column("brand_snapshot")
    with op.batch_alter_table("products") as batch_op:
        batch_op.drop_index("ix_products_brand")
        batch_op.drop_column("brand")
