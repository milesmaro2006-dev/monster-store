"""Store custom box components with the order item snapshot."""

from alembic import op
import sqlalchemy as sa

revision = "20261021_08"
down_revision = "20261020_07"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("order_items", sa.Column("components_snapshot", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("order_items", "components_snapshot")
