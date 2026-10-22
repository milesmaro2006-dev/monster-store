# Store settings + delivery areas
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from sqlalchemy import func
from app.blueprints.admin import admin_bp
from app.blueprints.admin.decorators import admin_required
from app.blueprints.admin.forms import SettingsForm, DeliveryAreaForm, AdminAccountForm
from app.models.settings import StoreSettings, DeliveryArea
from app.extensions import db
from app.blueprints.admin.audit import record_admin_event


@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def store_settings():
    s = StoreSettings.get()
    form = SettingsForm(obj=s)
    account_form = AdminAccountForm(username=current_user.username)
    if request.form.get("form_type") == "account" and account_form.validate_on_submit():
        username = account_form.username.data.strip()
        existing = db.session.query(current_user.__class__.id).filter(
            func.lower(current_user.__class__.username) == username.lower(),
            current_user.__class__.id != current_user.id,
        ).first()
        if existing:
            account_form.username.errors.append("اسم المستخدم مستخدم بالفعل.")
        elif not current_user.check_password(account_form.current_password.data):
            account_form.current_password.errors.append("كلمة المرور الحالية غير صحيحة.")
        elif (
            account_form.new_password.data
            and account_form.new_password.data != account_form.confirm_password.data
        ):
            account_form.confirm_password.errors.append("كلمتا المرور غير متطابقتين.")
        elif account_form.new_password.data == account_form.current_password.data:
            account_form.new_password.errors.append("اختر كلمة مرور مختلفة عن الحالية.")
        else:
            current_user.username = username
            if account_form.new_password.data:
                current_user.set_password(account_form.new_password.data)
            current_user.must_change_password = False
            db.session.commit()
            record_admin_event("account_updated", current_user.id)
            flash("تم تحديث بيانات الدخول مع الحفاظ على جلستك.", "success")
            return redirect(url_for("admin.store_settings"))
    elif request.form.get("form_type") != "account" and form.validate_on_submit():
        form.populate_obj(s)
        # Keep older integrations and checkout helpers working while the storefront
        # uses the explicit contact_* settings.
        s.store_phone = s.contact_phone
        s.store_whatsapp = s.contact_whatsapp
        s.store_email = s.contact_email
        db.session.commit()
        record_admin_event("store_settings_updated")
        flash("تم حفظ الإعدادات.", "success")
        return redirect(url_for("admin.store_settings"))

    areas = DeliveryArea.query.order_by(DeliveryArea.governorate).all()
    area_form = DeliveryAreaForm()
    return render_template(
        "admin/settings.html", form=form, areas=areas, area_form=area_form,
        account_form=account_form,
    )


@admin_bp.route("/settings/areas/new", methods=["POST"])
@admin_required
def add_area():
    form = DeliveryAreaForm()
    if form.validate_on_submit():
        db.session.add(
            DeliveryArea(
                governorate=form.governorate.data.strip(),
                area=form.area.data.strip(),
                fee=form.fee.data,
                is_active=form.is_active.data,
            )
        )
        db.session.commit()
        record_admin_event("delivery_area_created")
        flash("تم إضافة المنطقة.", "success")
    else:
        flash("تأكد من البيانات.", "danger")
    return redirect(url_for("admin.store_settings"))


@admin_bp.route("/settings/areas/<int:area_id>/delete", methods=["POST"])
@admin_required
def delete_area(area_id: int):
    a = db.session.get(DeliveryArea, area_id)
    if a:
        db.session.delete(a)
        db.session.commit()
        record_admin_event("delivery_area_deleted")
        flash("تم الحذف.", "info")
    return redirect(url_for("admin.store_settings"))
