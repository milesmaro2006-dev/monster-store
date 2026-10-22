# Product model
from datetime import datetime
from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    name_en = db.Column(db.String(150), nullable=True)
    brand = db.Column(db.String(100), nullable=True, index=True)
    slug = db.Column(db.String(150), unique=True, nullable=False, index=True)
    flavor = db.Column(db.String(80), nullable=True)
    flavor_en = db.Column(db.String(80), nullable=True)
    volume = db.Column(db.String(50), nullable=True)
    origin_country = db.Column(db.String(100), nullable=True)
    calories = db.Column(db.String(50), nullable=True)
    serving_advice = db.Column(
        db.String(100), nullable=True, default="يُقدّم مثلجاً",
        server_default="يُقدّم مثلجاً",
    )
    description = db.Column(db.Text, nullable=True)
    description_en = db.Column(db.Text, nullable=True)

    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)

    stock = db.Column(db.Integer, default=0, nullable=False, index=True)
    low_stock_threshold = db.Column(db.Integer, default=5, nullable=False)

    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    is_zero_sugar = db.Column(db.Boolean, default=False, nullable=False, server_default=db.false())

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    category = db.relationship("Category", back_populates="products")
    order_items = db.relationship("OrderItem", back_populates="product")
    tags = db.relationship(
        "FlavorTag",
        secondary="product_flavor_tags",
        backref=db.backref("products", lazy="dynamic"),
    )

    @property
    def in_stock(self) -> bool:
        return self.stock > 0 and self.is_active

    @property
    def is_low_stock(self) -> bool:
        return 0 < self.stock <= self.low_stock_threshold

    def __repr__(self) -> str:
        return f"<Product {self.slug} stock={self.stock}>"
