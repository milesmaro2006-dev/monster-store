# Test data factories
from decimal import Decimal
from app.extensions import db
from app.models.product import Product
from app.models.category import Category
from app.models.order import Order
from app.utils.helpers import slugify, generate_order_reference, generate_tracking_token


def make_product(name="Product", price=250, stock=10, **kwargs):
    cat = Category.query.first()
    p = Product(
        name=name,
        name_en=kwargs.pop("name_en", name),
        slug=slugify(name + "-" + str(stock)),
        price=Decimal(str(price)),
        stock=stock,
        category_id=cat.id if cat else None,
        is_active=kwargs.pop("is_active", True),
        **kwargs,
    )
    db.session.add(p)
    db.session.commit()
    return p


def make_order(**kwargs):
    o = Order(
        reference=generate_order_reference(),
        tracking_token=generate_tracking_token(),
        customer_name=kwargs.pop("customer_name", "Test User"),
        phone=kwargs.pop("phone", "01012345678"),
        governorate=kwargs.pop("governorate", "القاهرة"),
        area=kwargs.pop("area", "مدينة نصر"),
        address=kwargs.pop("address", "شارع 1"),
        subtotal=kwargs.pop("subtotal", Decimal("250")),
        delivery_fee=kwargs.pop("delivery_fee", Decimal("95")),
        total=kwargs.pop("total", Decimal("345")),
        status=kwargs.pop("status", "pending"),
        **kwargs,
    )
    db.session.add(o)
    db.session.commit()
    return o
