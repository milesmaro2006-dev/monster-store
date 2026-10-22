import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """الإعدادات الأساسية المشتركة."""

    # Static assets are revalidated after one hour, including non-fingerprinted GLBs.
    SEND_FILE_MAX_AGE_DEFAULT = 3600

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # Database
    _db_url = os.getenv("DATABASE_URL", "").strip()
    if not _db_url:
        _db_path = Path(
            os.getenv("SQLITE_DATABASE_PATH", str(BASE_DIR / "instance" / "monster.db"))
        ).expanduser()
        if not _db_path.is_absolute():
            _db_path = BASE_DIR / _db_path
        _db_url = f"sqlite:///{_db_path.resolve().as_posix()}"
    elif _db_url.startswith("sqlite:///") and not _db_url.startswith("sqlite:////"):
        _rel = _db_url.replace("sqlite:///", "", 1)
        if not os.path.isabs(_rel):
            _db_url = f"sqlite:///{(BASE_DIR / _rel).resolve()}"

    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    _is_sqlite = "sqlite" in SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }
    if _is_sqlite:
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {"check_same_thread": False}

    # Session Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7

    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # Uploads
    UPLOAD_FOLDER = BASE_DIR / "app" / "static" / "uploads"
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    # i18n
    LANGUAGES = ["ar", "en"]
    BABEL_DEFAULT_LOCALE = "ar"
    BABEL_DEFAULT_TIMEZONE = "Africa/Cairo"
    STORE_TIMEZONE = os.getenv("STORE_TIMEZONE", "Africa/Cairo")

    # Rate Limiting
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://").strip()
    ADMIN_URL_PREFIX = os.getenv("ADMIN_URL_PREFIX", "/portal-spidey").strip()
    RATELIMIT_DEFAULT = "300 per day;100 per hour"

    PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip()
    MAX_CART_QTY = int(os.getenv("MAX_CART_QTY", "20"))
    COD_ENABLED = os.getenv("COD_ENABLED", "false").strip().lower() == "true"
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False
    COD_ENABLED = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name=None):
    name = name or os.getenv("FLASK_ENV", "development")
    cfg = config_map.get(name, DevelopmentConfig)
    if cfg is ProductionConfig:
        limiter_uri = os.getenv("RATELIMIT_STORAGE_URI", "").strip()
        if not limiter_uri or limiter_uri.startswith("memory://"):
            raise RuntimeError(
                "Production requires shared RATELIMIT_STORAGE_URI (for example Redis)."
            )
        secret = os.getenv("SECRET_KEY", "").strip()
        if not secret or secret == "dev-secret-change-me":
            raise RuntimeError(
                "Production requires a strong SECRET_KEY in the environment. "
                "Do not use the development default."
            )
    return cfg
