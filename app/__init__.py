import gzip
import os
import re
from pathlib import Path
from flask import Flask, abort, request, session, render_template
from flask_wtf.csrf import CSRFError
from sqlalchemy.engine import make_url
from app.extensions import db, migrate, csrf, login_manager, limiter, babel
from config import get_config


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(get_config(config_name))

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    database_url = make_url(app.config["SQLALCHEMY_DATABASE_URI"])
    if database_url.drivername.startswith("sqlite") and database_url.database not in (
        None,
        ":memory:",
    ):
        database_path = Path(database_url.database).expanduser()
        os.makedirs(database_path.parent, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    babel.init_app(app, locale_selector=_select_locale)

    @app.before_request
    def _persist_selected_language():
        language = request.args.get("lang")
        if language in ("ar", "en"):
            session["lang"] = language

        # Static routes must never expose a database, secret, or non-image upload,
        # even if one is accidentally copied into the public static tree.
        if request.endpoint == "static":
            filename = request.view_args.get("filename", "") if request.view_args else ""
            parts = {part.lower() for part in Path(filename).parts}
            name = Path(filename).name.lower()
            private_suffixes = (
                ".db", ".sqlite", ".sqlite3", ".db-wal", ".db-shm",
                ".sqlite-wal", ".sqlite-shm", ".pem", ".key", ".p12",
                ".pfx", ".py", ".pyc", ".crt", ".secret", ".conf",
                ".ini", ".toml", ".yaml", ".yml", ".json",
            )
            private_names = {"instance", "__pycache__", ".env", ".flaskenv"}
            if (
                any(name.endswith(suffix) for suffix in private_suffixes)
                or name.startswith((
                    ".env", ".flaskenv", "secret-", "config.", "settings.",
                ))
                or parts.intersection(private_names)
                or name in {"wsgi.py", "run.py"}
            ):
                abort(404)
            if "uploads" in parts and Path(name).suffix.lower() not in {
                ".png", ".jpg", ".jpeg", ".webp"
            }:
                abort(404)

    login_manager.login_view = "admin.login"
    login_manager.login_message = "من فضلك سجّل الدخول للوصول للوحة التحكم."
    login_manager.login_message_category = "warning"

    from app import models  # noqa

    from app.blueprints.storefront import storefront_bp
    from app.blueprints.cart import cart_bp
    from app.blueprints.checkout import checkout_bp
    from app.blueprints.admin import admin_bp

    app.register_blueprint(storefront_bp)
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(checkout_bp, url_prefix="/checkout")
    admin_prefix = app.config.get("ADMIN_URL_PREFIX", "/portal-spidey")
    reserved_prefixes = {
        "static", "login", "cart", "checkout", "products", "product",
        "robots.txt", "sitemap.xml",
    }
    if (
        not isinstance(admin_prefix, str)
        or not re.fullmatch(r"/(?!static(?:/|$))[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", admin_prefix)
        or admin_prefix.split("/", 2)[1].lower() in reserved_prefixes
    ):
        raise RuntimeError("ADMIN_URL_PREFIX must be a safe absolute URL path.")
    app.register_blueprint(admin_bp, url_prefix=admin_prefix)
    # Keep stable login entry points even when the private admin prefix changes.
    app.add_url_rule(
        "/portal-admin/login", endpoint="admin.login_alias",
        view_func=app.view_functions["admin.login"], methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/login", endpoint="admin.login_legacy_alias",
        view_func=app.view_functions["admin.login"], methods=["GET", "POST"],
    )
    # Stable, concise admin workspace URLs, independent of the private legacy prefix.
    for suffix, endpoint, methods in (
        ("products", "products_list", ["GET"]),
        ("products/new", "product_new", ["GET", "POST"]),
        ("products/<int:product_id>/edit", "product_edit", ["GET", "POST"]),
        ("products/<int:product_id>/quick-update", "product_quick_update", ["POST"]),
        ("products/<int:product_id>/delete", "product_delete", ["POST"]),
        ("categories", "categories", ["GET", "POST"]),
        ("categories/<int:category_id>/edit", "category_edit", ["GET", "POST"]),
        ("categories/<int:category_id>/delete", "category_delete", ["POST"]),
        ("categories/quick-add", "category_quick_add", ["POST"]),
        ("flavor-tags/quick-add", "flavor_tag_quick_add", ["POST"]),
        ("orders", "orders_list", ["GET"]),
        ("orders/<int:order_id>/status", "order_status_update", ["POST"]),
        ("settings", "store_settings", ["GET", "POST"]),
        ("change-password", "change_password", ["GET", "POST"]),
        ("logout", "logout", ["POST"]),
    ):
        app.add_url_rule(
            f"/portal-admin/{suffix}",
            endpoint=f"admin.portal_{endpoint}",
            view_func=app.view_functions[f"admin.{endpoint}"],
            methods=methods,
        )

    from app.utils.helpers import register_context_processors
    register_context_processors(app)

    _register_error_handlers(app)
    _register_cli(app)

    from app.utils.logging_config import configure_logging
    configure_logging(app)

    @app.after_request
    def _static_model_delivery(response):
        if request.path.endswith(".glb"):
            response.headers.setdefault("Cache-Control", "public, max-age=3600")
            response.vary.add("Accept-Encoding")
            accepts_gzip = request.accept_encodings.quality("gzip") > 0
            if (
                accepts_gzip
                and response.status_code == 200
                and response.mimetype == "model/gltf-binary"
                and not request.range
                and "Content-Encoding" not in response.headers
            ):
                response.direct_passthrough = False
                response.set_data(gzip.compress(response.get_data(), compresslevel=6))
                response.headers["Content-Encoding"] = "gzip"
        return response

    @app.after_request
    def _security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    return app


def _select_locale():
    lang = request.args.get("lang")
    if lang in ("ar", "en"):
        session["lang"] = lang
    return session.get("lang", "ar")


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(CSRFError)
    def csrf_error(error):
        app.logger.warning(
            "CSRF validation failed: path=%s method=%s remote=%s reason=%s",
            request.path,
            request.method,
            request.remote_addr or "unknown",
            error.description,
        )
        if request.path.endswith("/status") and "/orders/" in request.path:
            return {
                "success": False,
                "error": "فشل التحقق الأمني. حدّث الصفحة وحاول مرة أخرى.",
            }, 400
        return "فشل التحقق الأمني. حدّث الصفحة وحاول مرة أخرى.", 400

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500


def _register_cli(app: Flask) -> None:
    import click

    @app.cli.command("init-db")
    def init_db():
        """إنشاء كل الجداول."""
        db.create_all()
        click.echo("✅ Database initialized.")

    @app.cli.command("seed")
    def seed_cmd():
        """إضافة بيانات تجريبية."""
        if not app.testing and not app.debug:
            raise click.ClickException(
                "Sample products are for local development only; seeding is disabled in production."
            )
        from app.seed import run_seed
        run_seed()
        click.echo("✅ Seed data inserted.")

    def _prompt_admin_password(label="Password"):
        password = click.prompt(label, hide_input=True, confirmation_prompt=True)
        if len(password) < 8 or len(password) > 128:
            raise click.ClickException("Password length must be between 8 and 128 characters.")
        return password

    def _create_admin(username, initial_password=True):
        from app.models.admin_user import AdminUser
        if AdminUser.query.filter_by(username=username).first():
            click.echo("Admin account already exists; its password was not changed.")
            return False
        user = AdminUser(username=username, is_admin=True)
        user.set_password(_prompt_admin_password("Initial password"))
        user.must_change_password = initial_password
        db.session.add(user)
        try:
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            raise click.ClickException("Could not create the admin account.") from error
        from app.blueprints.admin.audit import record_admin_event
        record_admin_event("admin_created", user.id)
        click.echo(f"Admin account '{username}' created.")
        return True

    @app.cli.group("admin")
    def admin_cli():
        """Secure administration account commands."""
        pass

    @admin_cli.command("create-user")
    @click.option("--username", default="Spidey", show_default=True)
    def create_admin_user(username):
        """Create an admin account once; never overwrite an existing account."""
        _create_admin(username)

    @admin_cli.command("reset-password")
    @click.option("--username", default="Spidey", show_default=True)
    def reset_admin_password(username):
        """Set a temporary password and require a change at next login."""
        from app.models.admin_user import AdminUser
        user = AdminUser.query.filter_by(username=username).first()
        if not user:
            raise click.ClickException("Admin account not found.")
        password = click.prompt("Temporary password", hide_input=True, confirmation_prompt=True)
        if len(password) < 12 or len(password) > 128:
            raise click.ClickException("Password length must be between 12 and 128 characters.")
        user.set_password(password)
        user.must_change_password = True
        db.session.commit()
        from app.blueprints.admin.audit import record_admin_event
        record_admin_event("password_reset", user.id)
        click.echo("Temporary password updated; it must be changed at next login.")

    @app.cli.command("create-admin")
    @click.option("--username", default="Spidey", show_default=True)
    def create_admin(username):
        """Backward-compatible alias for the secure admin creation command."""
        _create_admin(username)
