"""Add public contact, social, and InstaPay store settings."""

from alembic import op
import sqlalchemy as sa


revision = "20261022_11"
down_revision = "20261022_10"
branch_labels = None
depends_on = None


def upgrade():
    columns = (
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
        sa.Column("contact_whatsapp", sa.String(length=20), nullable=True),
        sa.Column("contact_email", sa.String(length=120), nullable=True),
        sa.Column("facebook_url", sa.String(length=500), nullable=True),
        sa.Column("instagram_url", sa.String(length=500), nullable=True),
        sa.Column("tiktok_url", sa.String(length=500), nullable=True),
        sa.Column("instapay_address", sa.String(length=120), nullable=True),
        sa.Column("instapay_name", sa.String(length=120), nullable=True),
        sa.Column("payment_instructions", sa.Text(), nullable=True),
    )
    with op.batch_alter_table("store_settings") as batch_op:
        for column in columns:
            batch_op.add_column(column)

    # Preserve the existing public contact details for stores upgrading in place.
    op.execute(
        "UPDATE store_settings SET "
        "contact_phone = store_phone, "
        "contact_whatsapp = store_whatsapp, "
        "contact_email = store_email "
        "WHERE id = 1"
    )


def downgrade():
    with op.batch_alter_table("store_settings") as batch_op:
        for name in (
            "payment_instructions",
            "instapay_name",
            "instapay_address",
            "tiktok_url",
            "instagram_url",
            "facebook_url",
            "contact_email",
            "contact_whatsapp",
            "contact_phone",
        ):
            batch_op.drop_column(name)
