# Helper functions
import secrets
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode, urlparse

from flask import current_app, request, session, url_for
from app.extensions import db
from app.models.settings import StoreSettings
from app.models.category import Category
from app.utils.validators import is_valid_egypt_phone, normalize_phone, is_placeholder_value
from app.ui import translate_ui


def generate_order_reference() -> str:
    """مثال: MN-2026-000123"""
    year = datetime.utcnow().year
    last_id = db.session.execute(
        db.text("SELECT COALESCE(MAX(id), 0) FROM orders")
    ).scalar() or 0
    return f"MN-{year}-{int(last_id) + 1:06d}"


def generate_tracking_token() -> str:
    return secrets.token_urlsafe(32)


def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or secrets.token_hex(4)


def get_delivery_fee(subtotal: Decimal, delivery_method="home_delivery") -> Decimal:
    """Return the configured store fee for a selected delivery method."""
    del subtotal
    settings = StoreSettings.get()
    fees = {
        "metro_pickup": Decimal(settings.metro_pickup_fee),
        "home_delivery": Decimal(settings.home_delivery_fee),
    }
    return fees.get(delivery_method, fees["home_delivery"])


def localized_text(ar_value, en_value=None):
    lang = session.get("lang", "ar")
    if lang == "en":
        return en_value or ar_value or ""
    return ar_value or en_value or ""


def product_image_filename(product) -> str:
    filename = (getattr(product, "image_url", None) or "").strip()
    if filename:
        static_root = Path(current_app.static_folder)
        candidate = static_root / filename
        if candidate.is_file():
            return filename
    return "img/placeholder.svg"


def product_image_webp_filename(product) -> str | None:
    """Return a WebP image variant when one exists for a product image."""
    source_name = product_image_filename(product)
    source_path = Path(current_app.static_folder) / source_name
    if source_path.suffix.lower() == ".webp":
        return source_name
    webp_path = source_path.with_suffix(".webp")
    if webp_path.is_file():
        return webp_path.relative_to(current_app.static_folder).as_posix()
    return None


def available_hero_cans() -> list[dict]:
    static_root = Path(current_app.static_folder)
    cans = []
    for i in range(1, 7):
        rel = f"img/hero/can-{i}.png"
        if (static_root / rel).is_file():
            cans.append(
                {
                    "filename": rel,
                    "alt": "عبوة مشروب طاقة معروضة ضمن تشكيلة المتجر",
                }
            )
    return cans


def public_phone(settings) -> str | None:
    if not settings:
        return None
    raw = (getattr(settings, "contact_phone", None) or settings.store_phone or "").strip()
    if not raw or is_placeholder_value(raw):
        return None
    if not is_valid_egypt_phone(raw):
        return None
    return normalize_phone(raw)


def public_whatsapp(settings) -> str | None:
    if not settings:
        return None
    raw = (getattr(settings, "contact_whatsapp", None) or settings.store_whatsapp or "").strip()
    if not raw or is_placeholder_value(raw):
        return None
    if not is_valid_egypt_phone(raw):
        return None
    return normalize_phone(raw)


def whatsapp_link(phone: str, text: str | None = None) -> str | None:
    if not phone or not is_valid_egypt_phone(phone):
        return None
    digits = re.sub(r"\D", "", normalize_phone(phone))
    url = f"https://wa.me/{digits}"
    if text:
        from urllib.parse import quote

        url += f"?text={quote(text)}"
    return url


def public_email(settings) -> str | None:
    if not settings:
        return None
    raw = (getattr(settings, "contact_email", None) or settings.store_email or "").strip()
    if not raw or is_placeholder_value(raw):
        return None
    return raw


def public_address(settings) -> str | None:
    if not settings:
        return None
    raw = (settings.store_address or "").strip()
    if not raw or is_placeholder_value(raw):
        return None
    return raw


def is_same_host_redirect(target: str | None, request_host: str) -> bool:
    if not target:
        return False
    parsed = urlparse(target)
    if target.startswith("//") or "\\" in target:
        return False
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return False
    if parsed.netloc and parsed.netloc != request_host:
        return False
    return True


def is_safe_admin_redirect(target: str | None) -> bool:
    if not target:
        return False
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return False
    if "\\" in target or target.startswith("//"):
        return False
    from flask import current_app
    prefix = current_app.config.get("ADMIN_URL_PREFIX", "/portal-spidey").rstrip("/")
    return target == prefix or target.startswith(prefix + "/")


def cart_item_count() -> int:
    cart = session.get("cart") or {}
    total = 0
    for qty in cart.values():
        try:
            total += max(int(qty), 0)
        except (TypeError, ValueError):
            continue
    return total


def register_context_processors(app):
    @app.context_processor
    def inject_globals():
        try:
            settings = StoreSettings.get()
        except Exception:
            settings = None
        phone = public_phone(settings)
        wa = public_whatsapp(settings)

        def webp_image(product):
            filename = product_image_webp_filename(product)
            return url_for("static", filename=filename) if filename else None

        return {
            "product_image": lambda product: url_for(
                "static", filename=product_image_filename(product)
            ),
            "product_image_webp": webp_image,
            "store_settings": settings,
            "nav_categories": (
                Category.query.filter_by(is_active=True)
                .order_by(Category.name)
                .limit(5)
                .all()
            ),
            "current_lang": session.get("lang", "ar"),
            "lang_switch_url": _language_switch_url(),
            "language_url": _language_url,
            "t": lambda key: translate_ui(key, session.get("lang", "ar")),
            "is_rtl": session.get("lang", "ar") == "ar",
            "current_year": datetime.utcnow().year,
            "cart_count": cart_item_count(),
            "max_cart_qty": current_app.config.get("MAX_CART_QTY", 20),
            "contact_phone": phone,
            "contact_whatsapp": wa,
            "contact_whatsapp_url": whatsapp_link(wa) if wa else None,
            "contact_email": public_email(settings),
            "contact_address": public_address(settings),
            "social_facebook_url": (settings.facebook_url or "").strip() or None if settings else None,
            "social_instagram_url": (settings.instagram_url or "").strip() or None if settings else None,
            "social_tiktok_url": (settings.tiktok_url or "").strip() or None if settings else None,
            "placeholder_image": url_for("static", filename="img/placeholder.svg"),
        }

    @app.template_filter("product_name")
    def product_name_filter(product):
        return localized_text(product.name, product.name_en)

    @app.template_filter("product_flavor")
    def product_flavor_filter(product):
        return localized_text(product.flavor, product.flavor_en)

    @app.template_filter("product_desc")
    def product_desc_filter(product):
        return localized_text(product.description, product.description_en)


def _language_switch_url():
    target = "en" if session.get("lang", "ar") == "ar" else "ar"
    return _language_url(target)


def _language_url(language: str):
    args = request.args.to_dict(flat=True)
    args["lang"] = language if language in {"ar", "en"} else "ar"
    return f"{request.path}?{urlencode(args)}"
