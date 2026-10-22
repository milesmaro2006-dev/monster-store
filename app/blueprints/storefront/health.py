# /health endpoint
from flask import jsonify
from app.blueprints.storefront import storefront_bp
from app.extensions import db


@storefront_bp.route("/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify(status="ok", db="up"), 200
    except Exception:
        return jsonify(status="degraded", db="down"), 500