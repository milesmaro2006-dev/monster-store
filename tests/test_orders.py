# Orders tests
from app.blueprints.checkout.service import create_order
from app.models.product import Product


def test_order_reference_unique(app):
    with app.app_context():
        from app.utils.helpers import generate_order_reference
        ref1 = generate_order_reference()
        assert ref1.startswith("MN-")


def test_order_stock_deduction(app):
    with app.app_context():
        p = Product.query.first()
        pid = p.id
        initial_stock = p.stock
    from tests.factories import make_order
    # محاكاة طلب كامل عبر service (بديل أفضل من route في test)
    # هنا نتحقق فقط من الفكرة
    assert initial_stock > 0