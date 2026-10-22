"""Set store pricing and save selected delivery method on orders."""

from alembic import op
import sqlalchemy as sa


revision = "20261018_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "orders",
        sa.Column(
            "delivery_method",
            sa.String(length=20),
            server_default="home_delivery",
            nullable=False,
        ),
    )
    op.execute("UPDATE products SET price = 250.00")


def downgrade():
    op.execute(
        "UPDATE products SET price = CASE slug "
        "WHEN 'monster-ultra-peachy-keen' THEN 45.00 "
        "WHEN 'monster-ultra-rosa' THEN 45.00 "
        "WHEN 'monster-ultra-paradise' THEN 45.00 "
        "WHEN 'monster-vr46-the-doctor' THEN 55.00 "
        "WHEN 'monster-pipeline-punch' THEN 50.00 "
        "WHEN 'monster-lando-norris' THEN 55.00 ELSE price END"
    )
    op.drop_column("orders", "delivery_method")
