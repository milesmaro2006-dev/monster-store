# Inventory tests
from app.models.product import Product
from app.extensions import db
from tests.factories import make_product


def test_stock_reduces_on_order(app):
    with app.app_context():
        p = make_product(name="Stock Test", stock=10)
        p.stock -= 3
        db.session.commit()
        assert p.stock == 7


def test_stock_restore_on_cancel(app):
    with app.app_context():
        p = make_product(name="Cancel Test", stock=5)
        p.stock += 3
        db.session.commit()
        assert p.stock == 8