"""Add product specifications and seed the initial storefront categories."""

from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "20261020_07"
down_revision = "20261020_06"
branch_labels = None
depends_on = None


INITIAL_CATEGORIES = (
    ("مشروبات طاقة ومستوردة", "Imported Energy Drinks", "imported-energy"),
    ("قهوة وبوبا مثلجة", "Iced Coffee & Boba", "iced-coffee-boba"),
    ("سناكس ومقرمشات", "Snacks & Crisps", "snacks-crisps"),
    ("شوكولاتة وحلويات", "Chocolate & Sweets", "chocolate-sweets"),
    ("زيرو سكر", "Zero Sugar", "zero-sugar"),
)


def upgrade():
    op.alter_column(
        "categories", "name", new_column_name="name_ar",
        existing_type=sa.String(length=80), existing_nullable=False,
    )
    op.add_column("products", sa.Column("volume", sa.String(length=50), nullable=True))
    op.add_column("products", sa.Column("origin_country", sa.String(length=100), nullable=True))
    op.add_column("products", sa.Column("calories", sa.String(length=50), nullable=True))
    op.add_column(
        "products",
        sa.Column(
            "serving_advice", sa.String(length=100), nullable=True,
            server_default="يُقدّم مثلجاً",
        ),
    )

    connection = op.get_bind()
    for name_ar, name_en, slug in INITIAL_CATEGORIES:
        exists = connection.execute(
            sa.text("SELECT id FROM categories WHERE slug = :slug OR name_ar = :name"),
            {"slug": slug, "name": name_ar},
        ).first()
        if not exists:
            connection.execute(
                sa.text(
                    "INSERT INTO categories (name_ar, name_en, slug, is_active, created_at) "
                    "VALUES (:name, :name_en, :slug, :is_active, :created_at)"
                ),
                {
                    "name": name_ar,
                    "name_en": name_en,
                    "slug": slug,
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                },
            )


def downgrade():
    op.drop_column("products", "serving_advice")
    op.drop_column("products", "calories")
    op.drop_column("products", "origin_country")
    op.drop_column("products", "volume")
    op.alter_column(
        "categories", "name_ar", new_column_name="name",
        existing_type=sa.String(length=80), existing_nullable=False,
    )

