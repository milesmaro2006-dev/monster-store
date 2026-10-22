# Orders management
from datetime import datetime, timedelta
import re
from urllib.parse import quote
from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from sqlalchemy import or_, update
from sqlalchemy.orm import selectinload
from app.blueprints.admin import admin_bp
from app.blueprints.admin.decorators import admin_required
from app.blueprints.admin.forms import OrderStatusForm
from app.models.order import (
    Order, OrderItem, OrderStatusHistory, ORDER_STATUSES, ORDER_STATUS_LABELS_AR,
)
from app.extensions import db
from flask_login import current_user
from app.blueprints.admin.audit import record_admin_event
from app.utils.validators import is_valid_egypt_phone, normalize_phone

@admin_bp.route("/orders")
@admin_required
def orders_list():
    q = (request.args.get("q") or "").strip()
    status = request.args.get("status") or ""
    date_from = request.args.get("from") or ""
    date_to = request.args.get("to") or ""

    query = Order.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Order.reference.ilike(like),
                Order.phone.ilike(like),
                Order.customer_name.ilike(like),
            )
        )
    if status:
        query = query.filter(Order.status == status)
    if date_from:
        try:
            query = query.filter(Order.created_at >= datetime.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(
                Order.created_at
                <= datetime.fromisoformat(date_to) + timedelta(days=1)
            )
        except ValueError:
            pass

    pagination = (
        query.options(selectinload(Order.items))
        .order_by(Order.created_at.desc(), Order.id.desc())
        .paginate(page=max(request.args.get("page", 1, type=int), 1), per_page=25, error_out=False)
    )
    orders = pagination.items
    whatsapp_links = {
        order.id: _customer_whatsapp_link(order) for order in orders
    }
    return render_template(
        "admin/orders.html",
        orders=orders,
        pagination=pagination,
        whatsapp_links=whatsapp_links,
        q=q,
        status=status,
        date_from=date_from,
        date_to=date_to,
        order_statuses=ORDER_STATUSES,
        delivered_count=Order.query.filter_by(status="delivered").count(),
    )


def _customer_whatsapp_link(order):
    if not is_valid_egypt_phone(order.phone):
        return None
    phone = re.sub(r"\D", "", normalize_phone(order.phone))
    message = (
        f"أهلاً بك! بخصوص طلبك رقم #{order.reference} من IMPORT DISTRICT، "
        "بنأكد معاك تفاصيل الشحن."
    )
    return f"https://wa.me/{phone}?text={quote(message, safe='')}"


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def order_status_update(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json(silent=True) or request.form
    new_status = data.get("status")
    new_status = new_status.strip() if isinstance(new_status, str) else ""
    if new_status not in ORDER_STATUSES:
        return jsonify(success=False, error="حالة غير صالحة."), 400
    # Status updates are intentionally unrestricted; the allow-list below keeps
    # stored values consistent while permitting admin corrections at any time.
    if new_status != order.status:
        old_status = order.status
        if new_status == "cancelled":
            claim_restore = db.session.execute(
                update(Order)
                .where(Order.id == order.id, Order.stock_restored.is_(False))
                .values(stock_restored=True)
            )
            if claim_restore.rowcount == 1:
                for item in order.items:
                    if item.product:
                        item.product.stock += item.quantity
            order.stock_restored = True
        order.status = new_status
        db.session.add(OrderStatusHistory(
            order_id=order.id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.id,
            note=None,
        ))
        db.session.commit()
        record_admin_event(
            "order_status_changed",
            detail=f"order_id={order.id}; {old_status}->{new_status}",
        )
    return jsonify(
        success=True,
        status=order.status,
        message="تم تحديث الحالة بنجاح",
        label={
            "shipped": "تم الشحن",
            "delivered": "تم التسليم",
        }.get(order.status, ORDER_STATUS_LABELS_AR.get(order.status, order.status)),
        delivered=Order.query.filter_by(status="delivered").count(),
    )


@admin_bp.route("/orders/<int:order_id>", methods=["GET", "POST"])
@admin_required
def order_detail(order_id: int):
    order = (
        Order.query.options(selectinload(Order.items), selectinload(Order.history))
        .populate_existing().filter_by(id=order_id).first()
    )
    if not order:
        abort(404)
    items = OrderItem.query.filter_by(order_id=order.id).order_by(OrderItem.id.asc()).all()
    # Other request handlers may have loaded these collections earlier in the
    # same application context; force the persisted order-item snapshots.
    db.session.expire(order, ["items", "history"])

    form = OrderStatusForm()
    if form.validate_on_submit():
        new_status = form.status.data
        if new_status not in ORDER_STATUSES:
            flash("حالة غير صالحة.", "danger")
            return redirect(url_for("admin.order_detail", order_id=order.id))
        if new_status != order.status:
            old_status = order.status

            # التعامل مع المخزون عند الإلغاء
            if new_status == "cancelled":
                claim_restore = db.session.execute(
                    update(Order)
                    .where(Order.id == order.id, Order.stock_restored.is_(False))
                    .values(stock_restored=True)
                )
                if claim_restore.rowcount == 1:
                    for item in order.items:
                        if item.product:
                            item.product.stock += item.quantity
                order.stock_restored = True

            order.status = new_status
            db.session.add(
                OrderStatusHistory(
                    order_id=order.id,
                    old_status=old_status,
                    new_status=new_status,
                    changed_by=current_user.id,
                    note=form.note.data or None,
                )
            )
            db.session.commit()
            record_admin_event("order_status_changed", detail=(
                f"order_id={order.id}; {old_status}->{new_status}"
            ))
        flash("تم تحديث حالة الطلب بنجاح", "success")
        return redirect(url_for("admin.order_detail", order_id=order.id))

    return render_template(
        "admin/order_detail.html", order=order, form=form,
        whatsapp_url=_customer_whatsapp_link(order), items=items,
    )
