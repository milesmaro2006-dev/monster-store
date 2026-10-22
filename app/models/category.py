# Category model
from datetime import datetime
from app.extensions import db
from sqlalchemy.orm import synonym


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(80), unique=True, nullable=False)
    # Backward-compatible alias for callers that still use the former attribute.
    name = synonym("name_ar")
    name_en = db.Column(db.String(80), nullable=True)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    products = db.relationship("Product", back_populates="category", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Category {self.slug}>"
