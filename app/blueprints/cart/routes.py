# Cart routes
from flask import render_template, request, redirect, url_for, flash, jsonify
from app.blueprints.cart import cart_bp
from app.blueprints.cart import service
from app.utils.helpers import is_same_host_redirect


def _wants_json() -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _back():
    ref = request.referrer
    if is_same_host_redirect(ref, request.host):
        return ref
    return url_for("storefront.catalog")


@cart_bp.route("/")
def view_cart():
    details = service.get_cart_details()
    return render_template("cart/cart.html", **details)


@cart_bp.route("/shipping-method", methods=["POST"])
def set_shipping_method():
    method = request.form.get("delivery_method", "")
    if method not in ("metro_pickup", "home_delivery"):
        return jsonify(ok=False), 400
    from flask import session
    from app.utils.helpers import get_delivery_fee

    session["delivery_method"] = method
    session.modified = True
    details = service.get_cart_details()
    fee = get_delivery_fee(details["subtotal"], method)
    return jsonify(
        ok=True,
        delivery_fee=f"{fee:.2f}",
        total=f"{details['subtotal'] + fee:.2f}",
    )


@cart_bp.route("/add/<int:product_id>", methods=["POST"])
def add(product_id: int):
    qty = request.form.get("qty", 1)
    ok, msg = service.add_to_cart(product_id, qty)
    if _wants_json():
        return jsonify(ok=ok, message=msg, count=service.get_cart_details()["count"])
    flash(msg, "success" if ok else "danger")
    return redirect(_back())


@cart_bp.route("/update/<int:product_id>", methods=["POST"])
def update(product_id: int):
    qty = request.form.get("qty", 1)
    ok, msg = service.update_qty(product_id, qty)
    if _wants_json():
        return jsonify(ok=ok, message=msg, count=service.get_cart_details()["count"])
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/remove/<int:product_id>", methods=["POST"])
def remove(product_id: int):
    service.remove_from_cart(product_id)
    flash("تم الحذف من السلة.", "info")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/remove-box", methods=["POST"])
def remove_box():
    from app.blueprints.cart.service import CUSTOM_BOX_KEY, get_cart, save_cart
    cart = get_cart()
    cart.pop(CUSTOM_BOX_KEY, None)
    save_cart(cart)
    flash("تم حذف البوكس المخصص من السلة.", "info")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/clear", methods=["POST"])
def clear():
    service.clear_cart()
    flash("تم تفريغ السلة.", "info")
    return redirect(url_for("cart.view_cart"))
