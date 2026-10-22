from app.seed import PRODUCTS, run_seed
from app.models.product import Product


def test_development_seed_is_repeatable(app):
    with app.app_context():
        run_seed()
        first_count = Product.query.count()
        run_seed()

        assert Product.query.count() == first_count
        assert all("category_slug" in product for product in PRODUCTS)
