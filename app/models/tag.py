"""Relational flavor tags for products."""
from app.extensions import db


product_flavor_tags = db.Table(
    "product_flavor_tags",
    db.Column("product_id", db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("flavor_tags.id", ondelete="CASCADE"), primary_key=True),
)


class FlavorTag(db.Model):
    __tablename__ = "flavor_tags"

    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(50), nullable=False, unique=True)
    name_en = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(60), nullable=False, unique=True, index=True)

    def __repr__(self):
        return f"<FlavorTag {self.slug}>"
