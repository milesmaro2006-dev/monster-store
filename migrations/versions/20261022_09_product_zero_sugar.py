"""Add the product zero sugar attribute."""

from alembic import op
import sqlalchemy as sa


revision = "20261022_09"
down_revision = "20261021_08"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_zero_sugar",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )


def downgrade():
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_column("is_zero_sugar")
