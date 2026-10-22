# Cart tests
from app.models.product import Product


def test_add_to_cart(client, app):
    with app.app_context():
        p = Product.query.first()
        pid = p.id
    r = client.post(f"/cart/add/{pid}", data={"qty": 2}, follow_redirects=True)
    assert r.status_code == 200


def test_add_more_than_stock(client, app):
    with app.app_context():
        p = Product.query.first()
        pid = p.id
        stock = p.stock
    r = client.post(f"/cart/add/{pid}", data={"qty": stock + 100}, follow_redirects=True)
    assert r.status_code == 200


def test_view_cart_empty(client):
    r = client.get("/cart/")
    assert r.status_code == 200


def test_update_qty(client, app):
    with app.app_context():
        pid = Product.query.first().id
    client.post(f"/cart/add/{pid}", data={"qty": 1})
    r = client.post(f"/cart/update/{pid}", data={"qty": 3}, follow_redirects=True)
    assert r.status_code == 200


def test_remove_item(client, app):
    with app.app_context():
        pid = Product.query.first().id
    client.post(f"/cart/add/{pid}", data={"qty": 1})
    r = client.post(f"/cart/remove/{pid}", follow_redirects=True)
    assert r.status_code == 200


def test_shipping_method_updates_fee_and_total(client, app):
    with app.app_context():
        product = Product.query.first()
        product_id = product.id
        unit_price = product.price
    client.post(f"/cart/add/{product_id}", data={"qty": 1})
    metro = client.post("/cart/shipping-method", data={"delivery_method": "metro_pickup"})
    assert metro.json["delivery_fee"] == "60.00"
    assert metro.json["total"] == f"{unit_price + 60:.2f}"
    home = client.post("/cart/shipping-method", data={"delivery_method": "home_delivery"})
    assert home.json["delivery_fee"] == "95.00"
    assert home.json["total"] == f"{unit_price + 95:.2f}"


def test_shipping_fees_follow_admin_settings(client, app):
    from app.extensions import db
    from app.models.settings import StoreSettings

    with app.app_context():
        settings = StoreSettings.get()
        old_metro, old_home = settings.metro_pickup_fee, settings.home_delivery_fee
        settings.metro_pickup_fee, settings.home_delivery_fee = 72, 118
        product_id = Product.query.first().id
        db.session.commit()
    try:
        client.post(f"/cart/add/{product_id}", data={"qty": 1})
        response = client.post(
            "/cart/shipping-method", data={"delivery_method": "home_delivery"}
        )
        assert response.json["delivery_fee"] == "118.00"
        checkout = client.get("/checkout/")
        assert "توصيل لباب المنزل (118 جنيه)".encode() in checkout.data
        assert 'data-metro-fee="72.00"'.encode() in checkout.data
    finally:
        with app.app_context():
            settings = StoreSettings.get()
            settings.metro_pickup_fee, settings.home_delivery_fee = old_metro, old_home
            db.session.commit()



def test_negative_quantity_update_is_rejected_without_removing_item(client, app):
    with app.app_context():
        product_id = Product.query.first().id
    client.post(f"/cart/add/{product_id}", data={"qty": 2})
    response = client.post(
        f"/cart/update/{product_id}", data={"qty": -1}, follow_redirects=True
    )
    assert response.status_code == 200
    with client.session_transaction() as session:
        assert session["cart"][str(product_id)] == 2


def test_cart_uses_accessible_increment_controls(client, app):
    with app.app_context():
        product_id = Product.query.first().id
    client.post(f"/cart/add/{product_id}", data={"qty": 1})
    response = client.get("/cart/")
    page = response.get_data(as_text=True)
    assert "data-quantity-form" in page
    assert 'aria-label="زيادة الكمية"' in page
    assert 'name="qty" value="0"' in page
    assert 'aria-label="حذف المنتج من السلة"' in page
    assert "cart-table" not in page
