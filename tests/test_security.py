# Security tests
def test_csrf_token_in_cart_form(client, app):
    r = client.get("/products")
    assert b"csrf_token" in r.data


def test_unauthorized_admin(app):
    # Use an explicitly new client so a prior test's admin cookie can never leak in.
    r = app.test_client().get("/portal-spidey/products", follow_redirects=False)
    assert r.status_code == 404


def test_non_admin_cannot_access_admin_endpoints(app):
    from app.extensions import db
    from app.models.admin_user import AdminUser
    with app.app_context():
        user = AdminUser(username="customer-account", is_admin=False)
        user.set_password("customer-password")
        db.session.add(user)
        db.session.commit()
    client = app.test_client()
    client.post("/portal-spidey/login", data={
        "username": "customer-account", "password": "customer-password",
    })
    assert client.get("/portal-spidey/").status_code == 404


def test_forced_password_change_blocks_dashboard_until_rotated(app):
    from app.extensions import db
    from app.models.admin_user import AdminUser
    with app.app_context():
        user = AdminUser.query.filter_by(username="admin").one()
        original_hash = user.password_hash
        user.must_change_password = True
        db.session.commit()
    try:
        client = app.test_client()
        login_response = client.post("/portal-spidey/login", data={
            "username": "admin", "password": "secret123",
        })
        assert login_response.status_code == 302
        assert login_response.headers["Location"].endswith(
            "/portal-admin/change-password"
        )
        form_page = client.get("/portal-admin/change-password")
        assert form_page.status_code == 200
        assert b'<main class="admin-main">' in form_page.data
        assert "تغيير كلمة المرور".encode() in form_page.data
        for field in ("current_password", "new_password", "confirm_password"):
            assert f'name="{field}"'.encode() in form_page.data
        assert "حفظ كلمة المرور".encode() in form_page.data
        response = client.get("/portal-spidey/")
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/portal-admin/change-password")
        changed = client.post("/portal-admin/change-password", data={
            "current_password": "secret123",
            "new_password": "A-new-strong-password-456",
            "confirm_password": "A-new-strong-password-456",
        })
        assert changed.status_code == 302
        assert client.get("/portal-spidey/").status_code == 200
    finally:
        with app.app_context():
            user = AdminUser.query.filter_by(username="admin").one()
            user.password_hash = original_hash
            user.must_change_password = False
            db.session.commit()


def test_price_tampering(client, app):
    """التأكد إن السعر بيتحسب من الـ DB مش من الفورم."""
    with app.app_context():
        from app.models.product import Product
        pid = Product.query.first().id
    # نضيف منتج للسلة وندفع سعر مزيّف في الفورم — الـ service بيتجاهل الفورم
    client.post(f"/cart/add/{pid}", data={"qty": 1})
    client.get("/checkout/")
    with client.session_transaction() as session:
        checkout_token = session["checkout_token"]
    r = client.post("/checkout/", data={
        "customer_name": "Test Buyer",
        "phone": "01012345678",
        "delivery_method": "home_delivery",
        "governorate": "القاهرة",
        "area": "مدينة نصر",
        "street_address": "شارع", "building": "10", "apartment": "4",
        "payment_method": "cod",
        "subtotal": "1.00",     # مزيّف
        "total": "1.00",        # مزيّف
        "checkout_token": checkout_token,
    }, follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["Location"].startswith("https://wa.me/")
    with app.app_context():
        from app.models.order import Order
        order = Order.query.order_by(Order.id.desc()).first()
        product = Product.query.get(pid)
        assert order.subtotal == product.price
        assert order.total != 1


def test_static_route_rejects_private_files_and_non_image_uploads(client):
    assert client.get("/static/example.db").status_code == 404
    assert client.get("/static/example.sqlite-wal").status_code == 404
    assert client.get("/static/.env.production").status_code == 404
    assert client.get("/static/config.py").status_code == 404
    assert client.get("/static/uploads/example.py").status_code == 404
