# admin_bp = Blueprint('admin', __name__)
from flask import Blueprint

admin_bp = Blueprint("admin", __name__)

from app.blueprints.admin import auth, routes, products, orders, settings, export, account  # noqa