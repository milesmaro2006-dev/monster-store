# Order creation + inventory
from decimal import Decimal
import json
from flask import current_app, session
from app.extensions import db
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.blueprints.cart import service as cart_service
from app.blueprints.cart.service import CUSTOM_BOX_DISCOUNT
from app.utils.helpers import (
    generate_order_reference,
    generate_tracking_token,
    get_delivery_fee,
)
from app.utils.validators import normalize_phone


class CheckoutError(Exception):
    pass


def create_order(form_data: dict) -> Order:
    """
    إنشاء أوردر جديد داخل transaction واحد:
    - يتحقق من المخزون والأسعار من قاعدة البيانات
    - يخصم الكميات
    - يحفظ الأوردر + عناصره
    """
    details = cart_service.get_cart_details()
    if not details["items"]:
        raise CheckoutError("السلة فارغة.")

    try:
        with db.session.begin_nested():
            product_demand = {}
            for item in details["items"]:
                if item.get("kind") == "custom_box":
                    for component in item["components"]:
                        product_id = component["product"].id
                        product_demand[product_id] = product_demand.get(product_id, 0) + component["qty"]
                else:
                    product_id = item["product"].id
                    product_demand[product_id] = product_demand.get(product_id, 0) + item["qty"]
            product_ids = list(product_demand)
            query = Product.query.filter(Product.id.in_(product_ids))
            try:
                query = query.with_for_update()
            except Exception:
                pass
            products = {p.id: p for p in query.all()}

            for product_id, quantity in product_demand.items():
                p = products.get(product_id)
                if not p or not p.is_active:
                    raise CheckoutError("أحد المنتجات لم يعد متوفراً.")
                if quantity < 1:
                    raise CheckoutError("كمية غير صالحة.")
                if quantity > p.stock:
                    raise CheckoutError(
                        f"الكمية المتاحة من «{p.name}» فقط {p.stock}."
                    )

            for item in details["items"]:
                if item.get("kind") == "custom_box":
                    for component in item["components"]:
                        component["product"] = products[component["product"].id]
                    component_total = sum((
                        Decimal(component["product"].price) * component["qty"]
                        for component in item["components"]
                    ), Decimal("0.00"))
                    item["discount"] = min(CUSTOM_BOX_DISCOUNT, component_total)
                    item["line_total"] = component_total - item["discount"]
                    item["unit_price"] = item["line_total"]
                    names_ar = [c["product"].name for c in item["components"]]
                    names_en = [c["product"].name_en or c["product"].name for c in item["components"]]
                    item["name_ar"] = f"بوكس مخصص ({' + '.join(names_ar)})"
                    item["name_en"] = f"Custom box ({' + '.join(names_en)})"
                else:
                    product = products[item["product"].id]
                    item["product"] = product
                    item["unit_price"] = Decimal(product.price)
                    item["line_total"] = item["unit_price"] * item["qty"]
            subtotal = sum((item["line_total"] for item in details["items"]), Decimal("0.00"))
            delivery_method = form_data["delivery_method"]
            delivery_fee = get_delivery_fee(subtotal, delivery_method)
            total = subtotal + delivery_fee

            if delivery_method == "metro_pickup":
                station = form_data["station_name"].strip()
                governorate = "Metro station pickup"
                area = station
                address = station
            else:
                governorate = form_data["governorate"]
                area = form_data["area"].strip()
                address = "\n".join(
                    [
                        form_data["street_address"].strip(),
                        f"Building: {form_data['building'].strip()}",
                        f"Apartment: {form_data['apartment'].strip()}",
                    ]
                )

            order = Order(
                reference=generate_order_reference(),
                tracking_token=generate_tracking_token(),
                customer_name=form_data["customer_name"].strip(),
                phone=normalize_phone(form_data["phone"].strip()),
                governorate=governorate,
                area=area,
                address=address,
                notes=(form_data.get("notes") or "").strip() or None,
                delivery_method=delivery_method,
                payment_method=form_data["payment_method"],
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                total=total,
                status="pending",
            )
            db.session.add(order)
            db.session.flush()

            for item in details["items"]:
                if item.get("kind") == "custom_box":
                    product_name = (
                        item["name_en"]
                        if session.get("lang") == "en" else item["name_ar"]
                    )
                    components = [{
                        "name": component["product"].name,
                        "name_en": component["product"].name_en,
                        "brand": component["product"].brand,
                        "quantity": component["qty"],
                    } for component in item["components"]]
                    db.session.add(OrderItem(
                        order_id=order.id,
                        product_id=None,
                        product_name=product_name,
                        name_en_snapshot=item["name_en"],
                        brand_snapshot="Custom Mix Box",
                        unit_price=item["unit_price"],
                        quantity=1,
                        line_total=item["line_total"],
                        components_snapshot=json.dumps(components, ensure_ascii=False),
                    ))
                else:
                    p = item["product"]
                    db.session.add(OrderItem(
                        order_id=order.id,
                        product_id=p.id,
                        product_name=p.name,
                        name_en_snapshot=p.name_en,
                        brand_snapshot=p.brand,
                        unit_price=item["unit_price"],
                        quantity=item["qty"],
                        line_total=item["line_total"],
                    ))

            for product_id, quantity in product_demand.items():
                products[product_id].stock -= quantity

            db.session.add(
                OrderStatusHistory(
                    order_id=order.id,
                    old_status=None,
                    new_status="pending",
                    note="تم إنشاء الأوردر",
                )
            )

        db.session.commit()
    except CheckoutError:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to create order")
        raise CheckoutError("تعذر إنشاء الطلب. حاول مرة أخرى.")

    cart_service.clear_cart()
    return order
