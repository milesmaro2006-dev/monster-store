from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_babel import Babel

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
babel = Babel()


@login_manager.user_loader
def load_user(user_id: str):
    from app.models.admin_user import AdminUser
    return db.session.get(AdminUser, int(user_id))