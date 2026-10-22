# Cart logic (session-based)
from decimal import Decimal
from flask import current_app, session
from app.extensions import db
from app.models.product import Product
from app.utils.helpers import get_delivery_fee

CART_KEY = "cart"
CUSTOM_BOX_KEY = "custom_box"
CUSTOM_BOX_SIZE = 3
CUSTOM_BOX_DISCOUNT = Decimal("40.00")


def max_qty() -> int:
    return int(current_app.config.get("MAX_CART_QTY", 20))


def parse_qty(raw) -> int | None:
    try:
        qty = int(raw)
    except (TypeError, ValueError):
        return None
    return qty


def get_cart() -> dict:
    cart = session.get(CART_KEY, {})
    if not isinstance(cart, dict):
        return {}
    return cart


def save_cart(cart: dict) -> None:
    session[CART_KEY] = cart
    session.modified = True


def add_to_cart(product_id: int, qty: int = 1) -> tuple[bool, str]:
    product = db.session.get(Product, product_id)
    if not product or not product.is_active:
        return False, "المنتج غير متوفر."

    qty = parse_qty(qty)
    if qty is None or qty < 1 or qty > max_qty():
        return False, "كمية غير صالحة."

    if product.stock <= 0:
        return False, "المنتج غير متوفر حالياً."

    cart = get_cart()
    key = str(product_id)
    current = parse_qty(cart.get(key, 0)) or 0
    new_qty = current + qty

    if new_qty > product.stock:
        return False, f"الكمية المتاحة فقط {product.stock}."
    if new_qty > max_qty():
        return False, f"الحد الأقصى للطلب من هذا المنتج {max_qty()}."

    cart[key] = new_qty
    save_cart(cart)
    return True, "تمت الإضافة للسلة."


def add_custom_box(product_ids) -> tuple[bool, str]:
    try:
        parsed_ids = [int(product_id) for product_id in product_ids]
    except (TypeError, ValueError):
        return False, "اختيارات البوكس غير صالحة."
    if len(parsed_ids) != CUSTOM_BOX_SIZE:
        return False, "اختر 3 منتجات بالضبط لتكوين البوكس."
    products = {product.id: product for product in Product.query.filter(
        Product.id.in_(set(parsed_ids)), Product.is_active.is_(True)
    ).all()}
    if len(products) != len(set(parsed_ids)):
        return False, "أحد المنتجات لم يعد متاحاً."
    selected_counts = {}
    for product_id in parsed_ids:
        selected_counts[product_id] = selected_counts.get(product_id, 0) + 1
    for product_id, qty in selected_counts.items():
        product = products[product_id]
        if product.stock < qty:
            return False, f"المخزون المتاح من {product.name} لا يكفي للبوكس."
    cart = get_cart()
    cart[CUSTOM_BOX_KEY] = parsed_ids
    save_cart(cart)
    return True, "تم تكوين البوكس وإضافته للسلة."


def update_qty(product_id: int, qty: int) -> tuple[bool, str]:
    product = db.session.get(Product, product_id)
    if not product or not product.is_active:
        return False, "المنتج غير متوفر."

    qty = parse_qty(qty)
    if qty is None:
        return False, "كمية غير صالحة."

    cart = get_cart()
    key = str(product_id)

    if qty < 0:
        return False, "كمية غير صالحة."
    if qty == 0:
        cart.pop(key, None)
        save_cart(cart)
        return True, "تم الحذف."

    if qty > max_qty():
        return False, f"الحد الأقصى للطلب من هذا المنتج {max_qty()}."
    if qty > product.stock:
        return False, f"الكمية المتاحة فقط {product.stock}."

    cart[key] = qty
    save_cart(cart)
    return True, "تم التحديث."


def remove_from_cart(product_id: int) -> None:
    cart = get_cart()
    cart.pop(str(product_id), None)
    save_cart(cart)


def clear_cart() -> None:
    session.pop(CART_KEY, None)
    session.modified = True


def get_cart_details() -> dict:
    cart = get_cart()
    items = []
    subtotal = Decimal("0.00")

    for key, qty in list(cart.items()):
        if key == CUSTOM_BOX_KEY:
            try:
                product_ids = [int(product_id) for product_id in qty]
            except (TypeError, ValueError):
                cart.pop(key, None)
                continue
            if len(product_ids) != CUSTOM_BOX_SIZE:
                cart.pop(key, None)
                continue
            products_by_id = {p.id: p for p in Product.query.filter(
                Product.id.in_(set(product_ids)), Product.is_active.is_(True)
            ).all()}
            needed = {}
            for product_id in product_ids:
                needed[product_id] = needed.get(product_id, 0) + 1
            if len(products_by_id) != len(needed) or any(
                products_by_id[product_id].stock < quantity
                for product_id, quantity in needed.items()
            ):
                cart.pop(key, None)
                continue
            components = [
                {"product": products_by_id[product_id], "qty": 1}
                for product_id in product_ids
            ]
            component_total = sum(
                (Decimal(component["product"].price) for component in components),
                Decimal("0.00"),
            )
            line_total = max(component_total - CUSTOM_BOX_DISCOUNT, Decimal("0.00"))
            names_ar = [component["product"].name for component in components]
            names_en = [component["product"].name_en or component["product"].name for component in components]
            items.append({
                "kind": "custom_box",
                "product": None,
                "components": components,
                "name_ar": f"بوكس مخصص ({' + '.join(names_ar)})",
                "name_en": f"Custom box ({' + '.join(names_en)})",
                "discount": min(CUSTOM_BOX_DISCOUNT, component_total),
                "qty": 1,
                "unit_price": line_total,
                "line_total": line_total,
            })
            subtotal += line_total
            continue
        try:
            product_id = int(key)
        except (TypeError, ValueError):
            cart.pop(key, None)
            continue
        product = db.session.get(Product, product_id)
        if not product or not product.is_active:
            cart.pop(key, None)
            continue
        qty = parse_qty(qty) or 0
        qty = min(qty, product.stock, max_qty())
        if qty <= 0:
            cart.pop(key, None)
            continue

        line_total = Decimal(product.price) * qty
        subtotal += line_total
        items.append(
            {
                "product": product,
                "kind": "product",
                "qty": qty,
                "unit_price": Decimal(product.price),
                "line_total": line_total,
            }
        )

    save_cart(cart)
    delivery_method = session.get("delivery_method", "home_delivery")
    if delivery_method not in ("metro_pickup", "home_delivery"):
        delivery_method = "home_delivery"
    delivery_fee = get_delivery_fee(subtotal, delivery_method)
    metro_delivery_fee = get_delivery_fee(subtotal, "metro_pickup")
    home_delivery_fee = get_delivery_fee(subtotal, "home_delivery")
    total = subtotal + delivery_fee
    return {
        "items": items,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "metro_delivery_fee": metro_delivery_fee,
        "home_delivery_fee": home_delivery_fee,
        "delivery_method": delivery_method,
        "total": total,
        "count": sum(i["qty"] for i in items),
    }
