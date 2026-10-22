# Pytest fixtures
import os
import pytest
from app import create_app
from app.extensions import db as _db
from app.models.admin_user import AdminUser
from app.models.category import Category
from app.models.product import Product
from app.models.settings import StoreSettings


@pytest.fixture(scope="session")
def app():
    os.environ["FLASK_ENV"] = "testing"
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        # بيانات أساسية
        StoreSettings.get().store_whatsapp = "+201115751214"
        _db.session.commit()
        cat = Category(name="Test Cat", name_en="Test Cat", slug="test-cat")
        _db.session.add(cat)
        _db.session.flush()
        _db.session.add(Product(
            name="Test Product", name_en="Test Product",
            slug="test-product", price=250, stock=10,
            category_id=cat.id, is_active=True,
        ))
        admin = AdminUser(username="admin")
        admin.set_password("secret123")
        _db.session.add(admin)
        _db.session.commit()

    yield app

    with app.app_context():
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def admin_client(client):
    client.post("/login", data={"username": "admin", "password": "secret123"})
    return client
