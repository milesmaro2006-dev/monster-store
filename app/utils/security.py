# Security decorators
from functools import wraps
from flask import abort, redirect, url_for
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("admin.login"))
        if not getattr(current_user, "is_active", False):
            abort(403)
        return f(*args, **kwargs)
    return wrapper