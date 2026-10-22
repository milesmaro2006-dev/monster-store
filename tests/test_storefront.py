# Storefront tests
import gzip
import html
import json
import re


def test_homepage(client):
    r = client.get("/")
    assert r.status_code == 200


def test_homepage_uses_only_classic_black_can_and_single_products_section(client, app):
    response = client.get("/")
    from app.models.product import Product
    with app.app_context():
        expected_products = Product.query.filter_by(is_active=True).limit(12).count()
    assert b"/static/models/can-1.glb" in response.data
    assert b"/static/models/can-2.glb" not in response.data
    assert b"/static/models/can-3.glb" not in response.data
    model_data = re.search(rb"data-models='([^']+)'", response.data)
    models = json.loads(html.unescape(model_data.group(1).decode()))
    assert [model["label_en"] for model in models] == ["Monster Original Energy"]
    assert [model["label_ar"] for model in models] == ["مونستر الأسود الكلاسيكي"]
    assert b"monster-black-can.svg" in response.data
    assert b"data-viewer-controls" not in response.data
    assert b"data-rotate-direction" not in response.data
    assert b"/static/js/libs/GLTFLoader.js" in response.data
    assert response.data.count(b'id="products"') == 1
    assert response.data.count(b'class="product-card"') == expected_products
    assert b"<details" not in response.data
    assert b'id="contact"' in response.data


def test_catalog(client):
    r = client.get("/products")
    assert r.status_code == 200


def test_catalog_zero_sugar_filter_is_independent_and_combines_with_category(client, app):
    from app.extensions import db
    from app.models.category import Category
    from app.models.product import Product

    with app.app_context():
        category = Category.query.filter_by(slug="test-cat").one()
        db.session.add(Product(
            name="Zero Sugar Starbucks", name_en="Zero Sugar Starbucks",
            slug="zero-sugar-starbucks", price=120, stock=8,
            category_id=category.id, is_active=True, is_zero_sugar=True,
        ))
        db.session.commit()

    response = client.get("/products?zero_sugar=1&category=test-cat")
    assert response.status_code == 200
    assert b"Zero Sugar Starbucks" in response.data
    assert b"Test Product" not in response.data
    assert b"href=\"/products?zero_sugar=1\"" in response.data
    assert b"q=zero" not in response.data


def test_catalog_flavor_tags_support_any_and_all_with_category_and_search(client, app):
    from app.extensions import db
    from app.models.category import Category
    from app.models.product import Product
    from app.models.tag import FlavorTag

    with app.app_context():
        category = Category.query.filter_by(slug="test-cat").one()
        citrus = FlavorTag(name_ar="حمضيات فلتر", name_en="Spec Citrus", slug="spec-citrus")
        lemon = FlavorTag(name_ar="ليمون فلتر", name_en="Spec Lemon", slug="spec-lemon")
        peach = FlavorTag(name_ar="خوخ فلتر", name_en="Spec Peach", slug="spec-peach")
        product_all = Product(
            name="Lemon Citrus Drink", name_en="Lemon Citrus Drink",
            slug="lemon-citrus-drink", price=90, stock=5, category_id=category.id,
            is_active=True, flavor="حمضيات، ليمون", tags=[citrus, lemon],
        )
        product_any = Product(
            name="Peach Drink", name_en="Peach Drink",
            slug="peach-drink", price=90, stock=5, category_id=category.id,
            is_active=True, flavor="خوخ", is_zero_sugar=True, tags=[peach],
        )
        db.session.add_all([product_all, product_any])
        db.session.commit()

    any_response = client.get("/products?q=Drink&category=test-cat&tags=spec-citrus,spec-peach")
    assert any_response.status_code == 200
    assert b"Lemon Citrus Drink" in any_response.data
    assert b"Peach Drink" in any_response.data
    zero_sugar_response = client.get("/products?q=Drink&category=test-cat&tags=spec-citrus,spec-peach&zero_sugar=1")
    assert b"Peach Drink" in zero_sugar_response.data
    assert b"Lemon Citrus Drink" not in zero_sugar_response.data
    all_response = client.get("/products?q=Drink&category=test-cat&tags=spec-citrus,spec-lemon&tag_mode=all")
    assert all_response.status_code == 200
    assert b"Lemon Citrus Drink" in all_response.data
    assert b"Peach Drink" not in all_response.data
    detail = client.get("/product/lemon-citrus-drink")
    assert b"flavor_tag=spec-citrus" in detail.data
    assert b"flavor_tag=spec-lemon" in detail.data


def test_language_switch_updates_direction_and_preserves_page(client):
    response = client.get("/products?category=monster&lang=en")
    assert response.status_code == 200
    assert b'<html lang="en" dir="ltr">' in response.data
    assert b'href="/products?category=monster&amp;lang=ar"' in response.data


def test_product_detail(client):
    r = client.get("/product/test-product")
    assert r.status_code == 200


def test_product_detail_shows_product_specification_microcards(client, app):
    from app.extensions import db
    from app.models.product import Product

    with app.app_context():
        product = Product.query.filter_by(slug="test-product").one()
        product.volume = "500 ml"
        product.origin_country = "اليابان"
        product.calories = "0 سعرة"
        product.serving_advice = "يُقدّم مثلجاً"
        db.session.commit()
    response = client.get("/product/test-product")
    assert response.status_code == 200
    for spec in ("500 ml", "اليابان", "0 سعرة", "يُقدّم مثلجاً"):
        assert spec.encode() in response.data
    assert b"product-specs" in response.data


def test_catalog_filters_dynamic_brand_and_price_range(client, app):
    from app.extensions import db
    from app.models.product import Product

    with app.app_context():
        product = Product.query.filter_by(slug="test-product").one()
        product.brand = "Sample Brand"
        db.session.commit()
    response = client.get("/products?brand=Sample%20Brand&min_price=200&max_price=300")
    assert response.status_code == 200
    assert b"Sample Brand" in response.data
    response = client.get("/products?brand=Sample%20Brand&min_price=300")
    assert b"Test Product" not in response.data


def test_product_detail_404(client):
    r = client.get("/product/does-not-exist")
    assert r.status_code == 404


def test_search(client):
    r = client.get("/search?q=Test")
    assert r.status_code == 200
    assert b"Test Product" in r.data


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_missing_product_image_uses_local_placeholder(app):
    from app.models.product import Product
    from app.utils.helpers import product_image_filename

    with app.app_context():
        product = Product.query.first()
        product.image_url = "uploads/not-present.webp"
        assert product_image_filename(product) == "img/placeholder.svg"


def test_all_hero_images_are_available(client):
    for index in range(1, 7):
        response = client.get(f"/static/img/hero/can-{index}.png")
        assert response.status_code == 200
        assert response.mimetype == "image/png"


def test_hero_model_is_cached_and_gzip_compressed_when_supported(client):
    response = client.get(
        "/static/models/can-2.glb", headers={"Accept-Encoding": "gzip"}
    )
    assert response.status_code == 200
    assert response.mimetype == "model/gltf-binary"
    assert response.headers["Cache-Control"] == "public, max-age=3600"
    assert response.headers["Content-Encoding"] == "gzip"
    assert "Accept-Encoding" in response.headers["Vary"]
    assert gzip.decompress(response.data).startswith(b"glTF")


def test_webp_variants_are_served(client):
    for path in (
        "/static/img/hero/can-1.webp",
        "/static/img/123/can-1.webp",
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert response.mimetype == "image/webp"
        assert len(response.data) > 0


def test_login_alias_uses_admin_login_view(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"password" in response.data


def test_portal_admin_login_alias(client):
    response = client.get("/portal-admin/login")
    assert response.status_code == 200
    assert b"password" in response.data
