# storefront_bp = Blueprint('storefront', __name__)
from flask import Blueprint

storefront_bp = Blueprint(
    "storefront",
    __name__,
    template_folder="../../templates/storefront",
)

from app.blueprints.storefront import routes, health  # noqa