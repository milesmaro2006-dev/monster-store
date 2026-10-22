# Checkout tests
from app.models.product import Product


def checkout_token(client):
    response = client.get("/checkout/")
    assert response.status_code == 200
    with client.session_transaction() as session:
        return session["checkout_token"]


def test_checkout_empty_cart(client):
    r = client.get("/checkout/", follow_redirects=True)
    assert r.status_code == 200


def test_checkout_accepts_payment_preference_and_shipping_methods(client, app):
    with app.app_context():
        product = Product.query.first()
        product_id = product.id
        from app.models.order import Order
        before = Order.query.count()
    client.post(f"/cart/add/{product_id}", data={"qty": 1})
    token = checkout_token(client)
    response = client.post("/checkout/", data={
        "customer_name": "Test User", "phone": "01012345678",
        "delivery_method": "metro_pickup", "station_name": "السادات",
        "payment_method": "instapay", "checkout_token": token,
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].startswith("https://wa.me/201115751214?text=")
    with app.app_context():
        order = Order.query.order_by(Order.id.desc()).first()
        assert Order.query.count() == before + 1
        assert order.delivery_fee == 60
        assert order.payment_method == "instapay"


def test_checkout_invalid_phone(client, app):
    with app.app_context():
        pid = Product.query.first().id
    client.post(f"/cart/add/{pid}", data={"qty": 1})
    token = checkout_token(client)
    r = client.post("/checkout/", data={
        "customer_name": "Test User",
        "phone": "invalid",
        "delivery_method": "home_delivery",
        "governorate": "القاهرة",
        "area": "مدينة نصر",
        "street_address": "شارع 1", "building": "10", "apartment": "4",
        "payment_method": "cod",
        "checkout_token": token,
    })
    assert r.status_code == 200
    assert b"\xd8\xb1\xd9\x82\xd9\x85" in r.data or b"phone" in r.data.lower()


def test_checkout_success(client, app):
    with app.app_context():
        pid = Product.query.first().id
    client.post(f"/cart/add/{pid}", data={"qty": 1})
    token = checkout_token(client)
    response = client.post("/checkout/", data={
        "customer_name": "Test User", "phone": "01012345678",
        "delivery_method": "home_delivery", "governorate": "القاهرة",
        "area": "مدينة نصر", "street_address": "شارع 1",
        "building": "10", "apartment": "4", "payment_method": "cod",
        "checkout_token": token,
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].startswith("https://wa.me/201115751214?text=")
    # The on-site confirmation remains available if the customer returns from WhatsApp.
    fallback = client.get("/checkout/confirmation")
    assert fallback.status_code == 200
    assert b"MN-" in fallback.data
    assert b"data-whatsapp-countdown" in fallback.data


def test_whatsapp_message_contains_structured_order(client, app):
    from urllib.parse import parse_qs, urlparse
    with app.app_context():
        product = Product.query.first()
        product.brand = "Sample Brand"
        product.name_en = "English Snapshot Name"
        pid = product.id
        from app.extensions import db
        db.session.commit()
    client.post(f"/cart/add/{pid}", data={"qty": 2})
    token = checkout_token(client)
    response = client.post("/checkout/", data={
        "customer_name": "Test User", "phone": "01012345678",
        "delivery_method": "home_delivery", "governorate": "القاهرة",
        "area": "مدينة نصر", "street_address": "شارع 1", "building": "10",
        "apartment": "4", "payment_method": "vodafone_cash", "checkout_token": token,
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].startswith("https://wa.me/201115751214?text=")
    message = parse_qs(urlparse(response.headers["Location"]).query)["text"][0]
    assert "رقم الطلب" in message and "Test User" in message
    assert "Sample Brand" in message and "× 2" in message
    assert "توصيل للمنزل" in message and "مدينة نصر" in message
    assert "الإجمالي" in message and "EGP" in message
    fallback = client.get("/checkout/confirmation")
    assert fallback.status_code == 200
    assert "إرسال وتأكيد الطلب عبر واتساب (اضغط هنا إذا لم يتم التحويل تلقائياً)".encode() in fallback.data
    with app.app_context():
        from app.models.order import Order
        order = Order.query.order_by(Order.id.desc()).first()
        assert order.subtotal == 500
        assert order.delivery_fee == 95
        assert order.total == 595
        assert order.items[0].brand_snapshot == "Sample Brand"
        assert order.items[0].name_en_snapshot == "English Snapshot Name"


def test_new_egyptian_prefix_and_localized_checkout_choices(client, app):
    with app.app_context():
        product_id = Product.query.first().id
    client.post(f"/cart/add/{product_id}", data={"qty": 1})
    page = client.get("/checkout/?lang=ar")
    assert "استلام من محطة مترو (60 جنيه)".encode() in page.data
    assert "توصيل لباب المنزل (95 جنيه)".encode() in page.data
    assert "الدفع عند الاستلام (كاش)".encode() in page.data
    assert "إنستاباي / محفظة إلكترونية (InstaPay / Wallet)".encode() in page.data
    with client.session_transaction() as session:
        token = session["checkout_token"]
    response = client.post("/checkout/", data={
        "customer_name": "Test Buyer", "phone": "01552371521",
        "delivery_method": "metro_pickup", "station_name": "السادات",
        "payment_method": "instapay", "checkout_token": token,
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].startswith("https://wa.me/201115751214?text=")
    with app.app_context():
        from app.models.order import Order
        order = Order.query.order_by(Order.id.desc()).first()
        assert order.phone == "+201552371521"
        assert order.delivery_fee == 60



def test_checkout_shows_conditional_shipping_sections_and_server_fees(client, app):
    with app.app_context():
        product_id = Product.query.first().id
    client.post(f"/cart/add/{product_id}", data={"qty": 1})
    response = client.get("/checkout/?lang=ar")
    assert response.status_code == 200
    assert b'data-delivery-fields="metro_pickup"' in response.data
    assert b'data-delivery-fields="home_delivery"' in response.data
    assert b'data-metro-fee="60.00"' in response.data
    assert b'data-home-fee="95.00"' in response.data
    assert b"data-total" in response.data


def test_checkout_requires_station_for_metro_pickup(client, app):
    with app.app_context():
        product_id = Product.query.first().id
    client.post(f"/cart/add/{product_id}", data={"qty": 1})
    token = checkout_token(client)
    response = client.post("/checkout/", data={
        "customer_name": "Test Buyer", "phone": "01012345678",
        "delivery_method": "metro_pickup", "station_name": "",
        "payment_method": "cod", "checkout_token": token,
    })
    assert response.status_code == 200
    assert "اسم محطة المترو مطلوب.".encode() in response.data


def test_checkout_uses_confirmation_fallback_without_store_whatsapp(client, app):
    from app.extensions import db
    from app.models.settings import StoreSettings
    with app.app_context():
        product_id = Product.query.first().id
        settings = StoreSettings.get()
        previous_phone = settings.store_whatsapp
        settings.store_whatsapp = None
        db.session.commit()
    try:
        client.post(f"/cart/add/{product_id}", data={"qty": 1})
        token = checkout_token(client)
        response = client.post("/checkout/", data={
            "customer_name": "Fallback Buyer", "phone": "01012345678",
            "delivery_method": "home_delivery", "governorate": "القاهرة",
            "area": "مدينة نصر", "street_address": "شارع 1",
            "building": "10", "apartment": "4", "payment_method": "cod",
            "checkout_token": token,
        }, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/checkout/confirmation")
        confirmation = client.get("/checkout/confirmation")
        assert confirmation.status_code == 200
        assert b"order-items" in confirmation.data
    finally:
        with app.app_context():
            settings = StoreSettings.get()
            settings.store_whatsapp = previous_phone
            db.session.commit()
