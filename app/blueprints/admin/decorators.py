from functools import wraps
from flask import abort, redirect, request, url_for
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(404)
        if not getattr(current_user, "is_active", False) or not getattr(
            current_user, "is_admin", False
        ):
            abort(404)
        if (
            getattr(current_user, "must_change_password", False)
            and request.endpoint not in {
                "admin.change_password", "admin.logout",
                "admin.portal_change_password", "admin.portal_logout",
            }
        ):
            return redirect(url_for("admin.portal_change_password"))
        return f(*args, **kwargs)
    return wrapper
