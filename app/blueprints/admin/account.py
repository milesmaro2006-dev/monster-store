from flask import flash, redirect, render_template, url_for
from flask_login import current_user
from app.blueprints.admin import admin_bp
from app.blueprints.admin.audit import record_admin_event
from app.blueprints.admin.decorators import admin_required
from app.blueprints.admin.forms import ChangePasswordForm
from app.extensions import db


@admin_bp.route("/change-password", methods=["GET", "POST"])
@admin_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            form.current_password.errors.append("كلمة المرور الحالية غير صحيحة.")
        elif form.new_password.data != form.confirm_password.data:
            form.confirm_password.errors.append("كلمتا المرور غير متطابقتين.")
        elif form.new_password.data == form.current_password.data:
            form.new_password.errors.append("اختر كلمة مرور مختلفة عن الحالية.")
        else:
            current_user.set_password(form.new_password.data)
            current_user.must_change_password = False
            db.session.commit()
            record_admin_event("password_changed", current_user.id)
            flash("تم تغيير كلمة المرور بنجاح.", "success")
            return redirect(url_for("admin.portal_products_list"))
    return render_template("admin/change_password.html", form=form)


@admin_bp.route("/account", methods=["GET", "POST"])
@admin_required
def account_settings():
    return redirect(url_for("admin.store_settings"))
