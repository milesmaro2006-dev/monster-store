# Admin tests
def test_admin_login_required(client):
    r = client.get("/portal-spidey/", follow_redirects=False)
    assert r.status_code == 404


def test_admin_login_success(admin_client):
    r = admin_client.get("/portal-spidey/")
    assert r.status_code == 200


def test_dashboard_content_empty_state_and_static_assets(admin_client):
    import re

    response = admin_client.get("/portal-spidey/")
    assert response.status_code == 200
    assert b"IMPORT DISTRICT" in response.data
    assert "منتجات نشطة".encode() in response.data
    assert "أحدث الطلبات".encode() in response.data
    assert "لا توجد طلبات خلال الأيام السبعة الماضية".encode() in response.data
    assert "لا توجد طلبات حتى الآن".encode() in response.data
    assert b"admin.css?v=20261021-category-management" in response.data
    assert b"variables.css?v=20261021-category-management" in response.data
    assert b"admin.js?v=20261022-flavor-tags" in response.data

    assets = re.findall(rb'(?:href|src)="(/static/[^\"]+)"', response.data)
    assert assets
    for asset in assets:
        assert admin_client.get(asset.decode()).status_code == 200

    stylesheet = admin_client.get("/static/css/admin.css").get_data(as_text=True)
    assert "box-shadow:0 0 0 100vmax" not in stylesheet
    assert admin_client.get("/static/fonts/Cairo-Regular.woff2").status_code == 200


def test_arabic_status_labels_and_typography_are_clean(admin_client):
    response = admin_client.get("/portal-spidey/products")
    assert response.status_code == 200
    assert "تعديل".encode() in response.data
    assert "حذف".encode() in response.data
    assert "نـ.شط".encode() not in response.data
    assert "عـ.ادي".encode() not in response.data
    stylesheet = admin_client.get("/static/css/admin.css").get_data(as_text=True)
    assert '[dir="rtl"] body *' in stylesheet
    assert 'letter-spacing:normal!important' in stylesheet


def test_dashboard_renders_with_no_products_or_orders():
    from app import create_app
    from app.extensions import db
    from app.models.admin_user import AdminUser

    empty_app = create_app("testing")
    with empty_app.app_context():
        db.create_all()
        user = AdminUser(username="empty-dashboard-admin")
        user.set_password("test-only-password")
        db.session.add(user)
        db.session.commit()
    try:
        client = empty_app.test_client()
        login = client.post("/portal-spidey/login", data={
            "username": "empty-dashboard-admin", "password": "test-only-password",
        })
        assert login.status_code == 302
        response = client.get("/portal-spidey/")
        assert response.status_code == 200
        assert "لا توجد تنبيهات مخزون حالياً".encode() in response.data
        assert "لا توجد طلبات حتى الآن".encode() in response.data
        assert "لا توجد طلبات خلال الأيام السبعة الماضية".encode() in response.data
    finally:
        with empty_app.app_context():
            db.session.remove()
            db.drop_all()


def test_admin_products_list(admin_client):
    r = admin_client.get("/portal-spidey/products")
    assert r.status_code == 200


def test_admin_can_create_product_with_dynamic_brand(admin_client, app):
    from app.models.product import Product

    form = admin_client.get("/portal-spidey/products/new")
    assert form.status_code == 200
    assert 'name="brand"'.encode() in form.data
    response = admin_client.post("/portal-spidey/products/new", data={
        "name": "مشروب قهوة مستورد",
        "name_en": "Imported Coffee Drink",
        "brand": "Sample International Brand",
        "volume": "500 ml",
        "origin_country": "اليابان",
        "calories": "0 سعرة",
        "serving_advice": "يُقدّم بارداً",
        "price": "125.50",
        "stock": "12",
        "low_stock_threshold": "3",
        "category_id": "0",
        "is_active": "y",
    })
    assert response.status_code == 302
    with app.app_context():
        created = Product.query.filter_by(slug="imported-coffee-drink").one()
        assert created.brand == "Sample International Brand"
        assert created.stock == 12
        assert created.volume == "500 ml"
        assert created.origin_country == "اليابان"
        assert created.calories == "0 سعرة"
        assert created.serving_advice == "يُقدّم بارداً"


def test_admin_product_form_quick_adds_category(admin_client, app):
    from app.extensions import db
    from app.models.category import Category

    page = admin_client.get("/portal-admin/products/new")
    assert page.status_code == 200
    assert b"data-open-category-modal" in page.data
    assert b'href="/portal-admin/categories"' in page.data
    response = admin_client.post("/portal-admin/categories/quick-add", json={
        "name_ar": "قهوة وبوبا مثلجة",
        "name_en": "Iced Coffee & Boba",
    })
    assert response.status_code == 201
    assert response.json["success"] is True
    assert response.json["name_ar"] == "قهوة وبوبا مثلجة"
    with app.app_context():
        category = db.session.get(Category, response.json["id"])
        assert category.name_ar == "قهوة وبوبا مثلجة"
        assert category.name_en == "Iced Coffee & Boba"


def test_admin_product_form_quick_adds_and_saves_multiple_flavor_tags(admin_client, app):
    from app.extensions import db
    from app.models.product import Product
    from app.models.tag import FlavorTag

    created_tags = []
    for name_ar, name_en in [("نكهة ليمون", "Test Lemon"), ("نكهة خوخ", "Test Peach")]:
        response = admin_client.post("/portal-admin/flavor-tags/quick-add", json={
            "name_ar": name_ar, "name_en": name_en,
        })
        assert response.status_code == 201
        created_tags.append(response.json["id"])

    response = admin_client.post("/portal-admin/products/new", data={
        "name": "منتج بوسوم متعددة",
        "name_en": "Multi Tag Product",
        "brand": "Test Brand",
        "price": "99.00",
        "stock": "5",
        "low_stock_threshold": "2",
        "category_id": "0",
        "is_active": "y",
        "tag_ids": [str(tag_id) for tag_id in created_tags],
    })
    assert response.status_code == 302
    with app.app_context():
        product = Product.query.filter_by(slug="multi-tag-product").one()
        assert {tag.id for tag in product.tags} == set(created_tags)
        assert set(product.flavor.split("، ")) == {tag.name_ar for tag in product.tags}
        assert FlavorTag.query.count() >= len(created_tags)


def test_category_dashboard_edit_and_delete_guards(admin_client, app):
    from app.extensions import db
    from app.models.category import Category
    from app.models.product import Product

    with app.app_context():
        product = Product.query.filter_by(slug="test-product").one()
        linked = Category(name_ar="فئة مرتبطة", name_en="Linked", slug="linked")
        empty = Category(name_ar="فئة فارغة", name_en="Empty", slug="empty")
        db.session.add_all([linked, empty])
        db.session.flush()
        product.category_id = linked.id
        linked_id, empty_id = linked.id, empty.id
        db.session.commit()

    dashboard = admin_client.get("/portal-admin/categories")
    assert dashboard.status_code == 200
    assert "الفئات".encode() in dashboard.data
    assert "المنتجات المرتبطة".encode() in dashboard.data
    assert b'name="csrf_token"' in dashboard.data
    assert b"1</span>" in dashboard.data

    edit = admin_client.post(f"/portal-admin/categories/{empty_id}/edit", data={
        "name": "فئة معدلة", "name_en": "Updated Category", "is_active": "y",
    })
    assert edit.status_code == 302
    with app.app_context():
        updated = db.session.get(Category, empty_id)
        assert updated.name_ar == "فئة معدلة"
        assert updated.name_en == "Updated Category"
        assert updated.slug == "updated-category"

    blocked = admin_client.post(f"/portal-admin/categories/{linked_id}/delete")
    assert blocked.status_code == 302
    with app.app_context():
        assert db.session.get(Category, linked_id) is not None
        assert Product.query.filter_by(category_id=linked_id).count() == 1

    removed = admin_client.post(f"/portal-admin/categories/{empty_id}/delete")
    assert removed.status_code == 302
    with app.app_context():
        assert db.session.get(Category, empty_id) is None


def test_category_delete_requires_and_accepts_csrf_token(admin_client, app):
    import re
    from app.extensions import db
    from app.models.category import Category

    previous_csrf = app.config["WTF_CSRF_ENABLED"]
    app.config["WTF_CSRF_ENABLED"] = True
    try:
        with app.app_context():
            category = Category(name_ar="حذف آمن", name_en="Safe Delete", slug="safe-delete")
            db.session.add(category)
            db.session.commit()
            category_id = category.id
        missing = admin_client.post(f"/portal-admin/categories/{category_id}/delete")
        assert missing.status_code == 400
        dashboard = admin_client.get("/portal-admin/categories")
        token = re.search(rb'name="csrf_token" value="([^"]+)"', dashboard.data)
        assert token
        removed = admin_client.post(
            f"/portal-admin/categories/{category_id}/delete",
            data={"csrf_token": token.group(1).decode()},
        )
        assert removed.status_code == 302
        with app.app_context():
            assert db.session.get(Category, category_id) is None
    finally:
        app.config["WTF_CSRF_ENABLED"] = previous_csrf


def test_admin_orders_list(admin_client):
    r = admin_client.get("/portal-spidey/orders")
    assert r.status_code == 200
    assert "لا توجد طلبات محفوظة حتى الآن".encode() in r.data


def test_inventory_and_analytics_pages(admin_client):
    inventory = admin_client.get("/portal-spidey/inventory")
    assert inventory.status_code == 200
    assert b'name="stock"' in inventory.data
    assert b'name="low_stock_threshold"' in inventory.data
    assert b'colspan="4"' not in inventory.data
    assert "الكمية المتاحة".encode() in inventory.data
    assert "حد التنبيه".encode() in inventory.data
    analytics = admin_client.get("/portal-spidey/analytics")
    assert analytics.status_code == 200
    assert "تحليلات المتجر".encode() in analytics.data
    assert "الأكثر مبيعاً حسب النكهة".encode() in analytics.data
    assert "توزيع طرق التوصيل".encode() in analytics.data
    assert b"DAILY VALUE" not in analytics.data


def test_inventory_inline_quick_update(admin_client, app):
    from app.extensions import db
    from app.models.product import Product

    with app.app_context():
        product = Product.query.filter_by(slug="test-product").one()
        product_id = product.id
        original_stock = product.stock
        original_threshold = product.low_stock_threshold
    response = admin_client.post(
        f"/portal-spidey/inventory/{product_id}",
        data={"stock": "4", "low_stock_threshold": "6"},
    )
    assert response.status_code == 302
    with app.app_context():
        product = db.session.get(Product, product_id)
        assert product.stock == 4
        assert product.low_stock_threshold == 6
        product.stock = original_stock
        product.low_stock_threshold = original_threshold
        db.session.commit()


def test_product_quick_update_persists_and_rejects_negative_values(admin_client, app):
    from decimal import Decimal
    from app.extensions import db
    from app.models.order import OrderItem
    from app.models.product import Product
    from tests.factories import make_order

    with app.app_context():
        product = Product.query.filter_by(slug="test-product").one()
        product_id = product.id
        original_price, original_stock = product.price, product.stock
        order = make_order()
        snapshot = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            unit_price=product.price,
            quantity=1,
            line_total=product.price,
        )
        db.session.add(snapshot)
        db.session.commit()
        snapshot_id = snapshot.id
    product_page = admin_client.get("/portal-spidey/products")
    assert b'name="price"' in product_page.data
    assert b'name="stock"' in product_page.data
    response = admin_client.post(
        f"/portal-spidey/products/{product_id}/quick-update",
        data={"price": "275.50", "stock": "8"},
    )
    assert response.status_code == 302
    with app.app_context():
        product = db.session.get(Product, product_id)
        assert product.price == Decimal("275.50")
        assert product.stock == 8
        assert db.session.get(OrderItem, snapshot_id).unit_price == original_price
    rejected = admin_client.post(
        f"/portal-spidey/products/{product_id}/quick-update",
        data={"price": "-1", "stock": "-2"},
    )
    assert rejected.status_code == 302
    with app.app_context():
        product = db.session.get(Product, product_id)
        assert product.price == Decimal("275.50")
        assert product.stock == 8
        product.price, product.stock = original_price, original_stock
        db.session.commit()


def test_product_quick_update_requires_admin(app):
    response = app.test_client().post(
        "/portal-spidey/products/1/quick-update",
        data={"price": "275.50", "stock": "8"},
    )
    assert response.status_code == 404


def test_order_status_ajax_updates_history_and_analytics(admin_client, app):
    from app.extensions import db
    from app.models.order import Order, OrderStatusHistory
    from tests.factories import make_order

    with app.app_context():
        order = make_order(status="shipped")
        db.session.commit()
        order_id = order.id
    response = admin_client.post(
        f"/portal-spidey/orders/{order_id}/status",
        data={"status": "delivered"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert response.status_code == 200
    assert response.json["status"] == "delivered"
    assert response.json["label"] == "تم التسليم"
    assert response.json["delivered"] >= 1
    with app.app_context():
        order = db.session.get(Order, order_id)
        assert order.status == "delivered"
        assert OrderStatusHistory.query.filter_by(
            order_id=order_id, new_status="delivered"
        ).count() == 1
    analytics = admin_client.get("/portal-spidey/analytics")
    assert analytics.status_code == 200
    assert "طلبات تم تسليمها".encode() in analytics.data


def test_order_status_unchanged_is_successful_noop(admin_client, app):
    from app.extensions import db
    from app.models.order import Order, OrderStatusHistory
    from tests.factories import make_order

    with app.app_context():
        order = make_order(status="pending")
        db.session.commit()
        order_id = order.id
    response = admin_client.post(
        f"/portal-spidey/orders/{order_id}/status",
        data={"status": "pending"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert response.status_code == 200
    assert response.json["status"] == "pending"
    with app.app_context():
        assert OrderStatusHistory.query.filter_by(order_id=order_id).count() == 0


def test_order_status_uses_database_transition_keys(admin_client, app):
    from app.extensions import db
    from app.models.order import Order
    from tests.factories import make_order

    with app.app_context():
        order = make_order(status="confirmed")
        db.session.commit()
        order_id = order.id
    response = admin_client.post(
        f"/portal-spidey/orders/{order_id}/status",
        data={"status": "shipped"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert response.status_code == 200
    assert response.json["status"] == "shipped"
    assert response.json["label"] == "تم الشحن"


def test_order_status_accepts_json_with_csrf_header_and_logs_rejection(admin_client, app, caplog):
    import re
    from app.extensions import db
    from tests.factories import make_order

    previous_csrf = app.config["WTF_CSRF_ENABLED"]
    app.config["WTF_CSRF_ENABLED"] = True
    try:
        with app.app_context():
            order = make_order(status="pending")
            db.session.commit()
            order_id = order.id
        page = admin_client.get("/portal-spidey/orders")
        token_match = re.search(rb'<meta name="csrf-token" content="([^"]+)"', page.data)
        assert token_match
        response = admin_client.post(
            f"/portal-spidey/orders/{order_id}/status",
            json={"status": "confirmed"},
            headers={"X-CSRFToken": token_match.group(1).decode()},
        )
        assert response.status_code == 200
        assert response.json["success"] is True
        assert response.json["status"] == "confirmed"
        assert response.json["message"] == "تم تحديث الحالة بنجاح"
        rejected = admin_client.post(
            f"/portal-spidey/orders/{order_id}/status",
            json={"status": "shipped"},
        )
        assert rejected.status_code == 400
        assert rejected.json["success"] is False
        assert "CSRF validation failed" in caplog.text
    finally:
        app.config["WTF_CSRF_ENABLED"] = previous_csrf


def test_logout_invalidates_admin_session(admin_client):
    response = admin_client.post("/portal-spidey/logout")
    assert response.status_code == 302
    assert admin_client.get("/portal-spidey/").status_code == 404


def test_orders_monitor_shows_order_details_and_customer_whatsapp_link(admin_client, app):
    import html
    import re
    from urllib.parse import parse_qs, urlparse
    from app.extensions import db
    from app.models.order import OrderItem
    from tests.factories import make_order, make_product

    with app.app_context():
        product = make_product(name="Monitor Can")
        order = make_order(
            customer_name="Monitor Customer",
            phone="+201155237152",
            delivery_method="metro_pickup",
            payment_method="instapay",
        )
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            unit_price=product.price,
            quantity=2,
            line_total=product.price * 2,
        ))
        db.session.commit()
        reference = order.reference
        order_id = order.id

    response = admin_client.get("/portal-spidey/orders")
    assert response.status_code == 200
    assert reference.encode() in response.data
    assert b"Monitor Customer" in response.data
    assert "توصيل للمنزل".encode() in response.data
    for status in (b"pending", b"confirmed", b"shipped", b"delivered", b"cancelled"):
        assert f'value="{status.decode()}"'.encode() in response.data
    assert b'name="csrf_token"' in response.data
    assert b"data-delivered-count" not in response.data
    link = re.search(rb'href="(https://wa\.me/201155237152\?text=[^"]+)"', response.data)
    assert link
    whatsapp_url = html.unescape(link.group(1).decode())
    message = parse_qs(urlparse(whatsapp_url).query)["text"][0]
    assert f"#{reference}" in message
    assert "بنأكد معاك تفاصيل الشحن" in message
    analytics = admin_client.get("/portal-spidey/analytics")
    assert "Monitor Can".encode() in analytics.data
    assert "500.00".encode() in analytics.data
    details = admin_client.get(f"/portal-spidey/orders/{order_id}")
    assert details.status_code == 200
    assert b"Monitor Can" in details.data
    assert b"250.00" in details.data


def test_admin_settings(admin_client):
    r = admin_client.get("/portal-spidey/settings")
    assert r.status_code == 200
    assert b'name="metro_pickup_fee"' in r.data
    assert b'name="home_delivery_fee"' in r.data


def test_csv_export(admin_client):
    r = admin_client.get("/portal-spidey/export/orders.csv")
    assert r.status_code == 200
    assert r.mimetype == "text/csv"


def test_cancelling_order_restores_stock_once(admin_client, app):
    from app.extensions import db
    from app.models.order import Order, OrderItem
    from app.models.product import Product
    from tests.factories import make_order, make_product

    with app.app_context():
        product = make_product(name="Admin Cancel Product", stock=3)
        order = make_order()
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            unit_price=product.price,
            quantity=2,
            line_total=product.price * 2,
        ))
        db.session.commit()
        order_id, product_id = order.id, product.id

    response = admin_client.post(
        f"/portal-spidey/orders/{order_id}",
        data={"status": "cancelled", "note": "Customer cancelled"},
    )
    assert response.status_code == 302

    admin_client.post(
        f"/portal-spidey/orders/{order_id}",
        data={"status": "cancelled", "note": "Repeated status"},
    )
    with app.app_context():
        assert db.session.get(Product, product_id).stock == 5
        assert db.session.get(Order, order_id).stock_restored is True


def test_portal_admin_three_view_routes(admin_client):
    assert admin_client.get("/portal-admin/products").status_code == 200
    assert admin_client.get("/portal-admin/orders").status_code == 200
    assert admin_client.get("/portal-admin/settings").status_code == 200
