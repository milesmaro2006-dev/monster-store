"""Add relational multi-select flavor tags and backfill legacy flavor values."""

from alembic import op
import sqlalchemy as sa


revision = "20261022_10"
down_revision = "20261022_09"
branch_labels = None
depends_on = None


INITIAL_TAGS = (
    ("حمضيات", "Citrus", "citrus"),
    ("ليمون", "Lemon", "lemon"),
    ("برتقال", "Orange", "orange"),
    ("لايم", "Lime", "lime"),
    ("توت", "Berry", "berry"),
    ("خوخ", "Peach", "peach"),
    ("فراولة", "Strawberry", "strawberry"),
    ("مانجو", "Mango", "mango"),
    ("شوكولاتة", "Chocolate", "chocolate"),
    ("إسبريسو", "Espresso", "espresso"),
    ("فانيليا", "Vanilla", "vanilla"),
    ("كراميل", "Caramel", "caramel"),
)


def upgrade():
    op.create_table(
        "flavor_tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name_ar", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name_en", sa.String(length=50), nullable=False),
        sa.Column("slug", sa.String(length=60), nullable=False, unique=True),
    )
    op.create_index("ix_flavor_tags_slug", "flavor_tags", ["slug"], unique=False)
    op.create_table(
        "product_flavor_tags",
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["flavor_tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("product_id", "tag_id"),
    )

    connection = op.get_bind()
    tag_table = sa.table(
        "flavor_tags",
        sa.column("id", sa.Integer),
        sa.column("name_ar", sa.String),
        sa.column("name_en", sa.String),
        sa.column("slug", sa.String),
    )
    for name_ar, name_en, slug in INITIAL_TAGS:
        connection.execute(tag_table.insert().values(name_ar=name_ar, name_en=name_en, slug=slug))

    tag_ids = {
        slug: tag_id
        for tag_id, slug in connection.execute(sa.text("SELECT id, slug FROM flavor_tags"))
    }
    products = connection.execute(
        sa.text("SELECT id, flavor, flavor_en FROM products")
    ).mappings()
    for product in products:
        legacy_text = " ".join((product["flavor"] or "", product["flavor_en"] or "")).casefold()
        for name_ar, name_en, slug in INITIAL_TAGS:
            if name_ar.casefold() in legacy_text or name_en.casefold() in legacy_text:
                connection.execute(
                    sa.text(
                        "INSERT INTO product_flavor_tags (product_id, tag_id) "
                        "VALUES (:product_id, :tag_id)"
                    ),
                    {"product_id": product["id"], "tag_id": tag_ids[slug]},
                )


def downgrade():
    op.drop_table("product_flavor_tags")
    op.drop_index("ix_flavor_tags_slug", table_name="flavor_tags")
    op.drop_table("flavor_tags")
