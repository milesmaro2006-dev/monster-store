# Models tests
from app.models.product import Product


def test_in_stock_property(app):
    p = Product(name="X", slug="x", price=45, stock=5, is_active=True)
    assert p.in_stock is True


def test_out_of_stock_property(app):
    p = Product(name="X", slug="x2", price=45, stock=0, is_active=True)
    assert p.in_stock is False


def test_low_stock_property(app):
    p = Product(name="X", slug="x3", price=45, stock=3, low_stock_threshold=5)
    assert p.is_low_stock is True