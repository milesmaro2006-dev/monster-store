# Checkout routes
import secrets
from flask import abort, flash, redirect, render_template, request, session, url_for

from app.blueprints.cart import service as cart_service
from app.blueprints.checkout import checkout_bp
from app.blueprints.checkout.forms import CheckoutForm
from app.blueprints.checkout.service import CheckoutError, create_order
from app.extensions import limiter
from app.models.order import Order
from app.models.settings import StoreSettings
from app.utils.helpers import public_whatsapp, whatsapp_link


def _new_checkout_token() -> str:
    token = secrets.token_urlsafe(24)
    session["checkout_token"] = token
    session.modified = True
    return token


@checkout_bp.route("/", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def checkout():
    form = CheckoutForm()
    if request.method == "POST" and form.delivery_method.data in (
        "metro_pickup",
        "home_delivery",
    ):
        session["delivery_method"] = form.delivery_method.data
    details = cart_service.get_cart_details()
    english = session.get("lang") == "en"
    metro_fee = f"{details['metro_delivery_fee']:.2f}".rstrip("0").rstrip(".")
    home_fee = f"{details['home_delivery_fee']:.2f}".rstrip("0").rstrip(".")
    form.delivery_method.choices = [
        (
            "metro_pickup",
            f"Metro station pickup — EGP {metro_fee}"
            if english else f"استلام من محطة مترو ({metro_fee} جنيه)",
        ),
        (
            "home_delivery",
            f"Home delivery — EGP {home_fee}"
            if english else f"توصيل لباب المنزل ({home_fee} جنيه)",
        ),
    ]
    if not details["items"]:
        flash("Your cart is empty." if session.get("lang") == "en" else "السلة فارغة.", "warning")
        return redirect(url_for("storefront.catalog"))

    if form.validate_on_submit():
        submitted = (form.checkout_token.data or "").strip()
        expected = session.get("checkout_token")
        if not submitted or not expected or submitted != expected:
            last_id = session.get("last_order_id")
            if last_id:
                already_received = (
                    "This order was already received."
                    if session.get("lang") == "en"
                    else "تم استلام هذا الطلب مسبقاً."
                )
                flash(already_received, "info")
                return redirect(url_for("checkout.confirmation"))
            expired_message = (
                "The form expired. Please try again."
                if session.get("lang") == "en"
                else "انتهت صلاحية نموذج الطلب. أعد المحاولة."
            )
            flash(expired_message, "warning")
            form.checkout_token.data = _new_checkout_token()
            return render_template("checkout/checkout.html", form=form, **details)

        try:
            order = create_order(form.data)
            session.pop("checkout_token", None)
            session["last_order_id"] = order.id
            session.modified = True
            whatsapp_url = _order_whatsapp_url(order)
            if whatsapp_url:
                return redirect(whatsapp_url)
            return redirect(url_for("checkout.confirmation"))
        except CheckoutError as error:
            flash(str(error), "danger")
            form.checkout_token.data = _new_checkout_token()
    elif not form.is_submitted():
        form.checkout_token.data = _new_checkout_token()
        form.payment_method.data = "cod"
        form.delivery_method.data = session.get("delivery_method", "home_delivery")

    return render_template("checkout/checkout.html", form=form, **details)


@checkout_bp.route("/confirmation")
def confirmation():
    order_id = session.get("last_order_id")
    if not order_id:
        abort(404)
    order = Order.query.filter_by(id=order_id).first()
    if not order:
        abort(404)
    return render_template(
        "checkout/confirmation.html",
        order=order,
        whatsapp_url=_order_whatsapp_url(order),
        instapay_whatsapp_url=_instapay_confirmation_url(order),
    )


def _instapay_confirmation_url(order):
    settings = StoreSettings.get()
    phone = public_whatsapp(settings)
    if not phone:
        return ""
    message = f"مرحبا، قمت بالطلب رقم {order.id} وأرغب في تأكيد الدفع"
    return whatsapp_link(phone, message) or ""


def _order_whatsapp_url(order):
    store_whatsapp = public_whatsapp(StoreSettings.get())
    if not store_whatsapp:
        return ""
    item_lines = []
    for item in order.items:
        if item.components:
            item_lines.append(f"- {item.product_name}:")
            for component in item.components:
                component_name = component.get("name_en") if session.get("lang") == "en" else component.get("name")
                item_lines.append(f"  • {component_name or component.get('name')} × {component.get('quantity', 1)}")
            continue
        name = (
            item.name_en_snapshot
            if session.get("lang") == "en" and item.name_en_snapshot
            else item.product_name
        )
        brand = f" ({item.brand_snapshot})" if item.brand_snapshot else ""
        item_lines.append(f"- {name}{brand} × {item.quantity}")
    items = "\n".join(item_lines)
    metro = order.delivery_method == "metro_pickup"
    if session.get("lang") == "en":
        delivery = "Metro station pickup" if metro else "Home delivery"
        payment = {
            "cod": "Cash on delivery",
            "instapay": "InstaPay / Smart Wallet",
            "visa_link": "Bank card (secure payment link via WhatsApp)",
            "vodafone_cash": "Vodafone Cash",
            "vodafone_cash": "Vodafone Cash",
        }.get(order.payment_method, order.payment_method)
        location = order.area if metro else (
            f"{order.governorate}, {order.area}, {order.address}"
        )
        message = (
            f"Order number: #{order.reference}\n"
            f"- Customer: {order.customer_name}\n"
            f"- Phone: {order.phone}\n- Items:\n{items}\n"
            f"- Delivery: {delivery} ({order.delivery_fee:.2f} EGP)\n"
            f"- Address/station: {location}\n- Payment: {payment}\n"
            f"- Total: {order.total:.2f} EGP"
        )
    else:
        delivery = "استلام من محطة مترو" if metro else "توصيل للمنزل"
        payment = {
            "cod": "الدفع عند الاستلام",
            "instapay": "تحويل إنستاباي / محفظة ذكية",
            "visa_link": "بطاقة بنكية (رابط دفع سريع عبر واتساب)",
            "vodafone_cash": "فودافون كاش",
            "vodafone_cash": "فودافون كاش",
        }.get(order.payment_method, order.payment_method)
        location = order.area if metro else (
            f"{order.governorate}، {order.area}، {order.address}"
        )
        message = (
            f"رقم الطلب: #{order.reference}\n"
            f"- العميل: {order.customer_name}\n- الهاتف: {order.phone}\n"
            f"- الطلبات:\n{items}\n"
            f"- نوع الشحن: {delivery} ({order.delivery_fee:.2f} EGP)\n"
            f"- العنوان/المحطة: {location}\n- طريقة الدفع: {payment}\n"
            f"- الإجمالي: {order.total:.2f} EGP"
        )
    return whatsapp_link(store_whatsapp, message) or ""
