# Order, OrderItem, OrderStatusHistory models
from datetime import datetime
import json
from app.extensions import db


ORDER_STATUSES = [
    "pending",
    "confirmed",
    "shipped",
    "delivered",
    "cancelled",
]

ORDER_STATUS_LABELS_AR = {
    "pending": "قيد الانتظار",
    "confirmed": "تم التأكيد",
    "shipped": "تم الشحن",
    # Retained for readable history and records created before the status update.
    "preparing": "قيد التجهيز",
    "out_for_delivery": "تم الشحن",
    "delivered": "تم التوصيل",
    "cancelled": "ملغي",
}


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(20), unique=True, nullable=False, index=True)
    tracking_token = db.Column(db.String(64), unique=True, nullable=False, index=True)

    customer_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False, index=True)
    governorate = db.Column(db.String(60), nullable=False)
    area = db.Column(db.String(120), nullable=False)
    address = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    delivery_method = db.Column(
        db.String(20), nullable=False, default="home_delivery", server_default="home_delivery"
    )
    payment_method = db.Column(db.String(20), nullable=False, default="cod")

    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    delivery_fee = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)

    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    stock_restored = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    items = db.relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    history = db.relationship(
        "OrderStatusHistory",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.created_at.desc()",
    )

    @property
    def status_label_ar(self) -> str:
        return ORDER_STATUS_LABELS_AR.get(self.status, self.status)

    def __repr__(self) -> str:
        return f"<Order {self.reference} {self.status}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=True, index=True
    )

    product_name = db.Column(db.String(150), nullable=False)
    name_en_snapshot = db.Column(db.String(150), nullable=True)
    brand_snapshot = db.Column(db.String(100), nullable=True)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    line_total = db.Column(db.Numeric(10, 2), nullable=False)
    components_snapshot = db.Column(db.Text, nullable=True)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")

    @property
    def components(self):
        try:
            value = json.loads(self.components_snapshot or "[]")
            return value if isinstance(value, list) else []
        except (TypeError, ValueError):
            return []

    def __repr__(self) -> str:
        return f"<OrderItem {self.product_name} x{self.quantity}>"


class OrderStatusHistory(db.Model):
    __tablename__ = "order_status_history"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey("admin_users.id"), nullable=True)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    order = db.relationship("Order", back_populates="history")

    def __repr__(self) -> str:
        return f"<StatusHistory {self.old_status}→{self.new_status}>"
