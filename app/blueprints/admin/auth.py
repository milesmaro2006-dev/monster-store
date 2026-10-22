# Admin login/logout
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user
from app.blueprints.admin import admin_bp
from app.blueprints.admin.forms import LoginForm
from app.models.admin_user import AdminUser
from app.extensions import limiter, db
from app.blueprints.admin.decorators import admin_required
from app.utils.helpers import is_safe_admin_redirect
from app.blueprints.admin.audit import record_admin_event


@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = AdminUser.query.filter_by(username=form.username.data).first()
        if (
            user and user.is_active and user.is_admin
            and user.check_password(form.password.data)
        ):
            session.clear()
            login_user(user, remember=False, fresh=True)
            session.permanent = True
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            record_admin_event("login_success", user.id)
            if user.must_change_password:
                return redirect(url_for("admin.portal_change_password"))
            flash("أهلاً بيك!", "success")
            next_url = request.args.get("next")
            if not is_safe_admin_redirect(next_url):
                next_url = url_for("admin.portal_products_list")
            return redirect(next_url)
        record_admin_event("login_failure")
        flash("بيانات الدخول غير صحيحة.", "danger")
    return render_template("admin/login.html", form=form)


@admin_bp.route("/logout", methods=["POST"])
@admin_required
def logout():
    logout_user()
    session.clear()
    flash("تم تسجيل الخروج.", "info")
    return redirect(url_for("admin.login"))
