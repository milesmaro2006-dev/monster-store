# Admin dashboard routes
from datetime import datetime, time, timedelta
from flask import current_app, render_template
from sqlalchemy import func
import pytz
from app.blueprints.admin import admin_bp
from app.blueprints.admin.decorators import admin_required
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.extensions import db


@admin_bp.route("/")
@admin_required
def dashboard():
    timezone = pytz.timezone(current_app.config.get("STORE_TIMEZONE", "Africa/Cairo"))
    today = datetime.now(timezone).date()
    start = (
        timezone.localize(datetime.combine(today, time.min))
        .astimezone(pytz.UTC).replace(tzinfo=None)
    )
    end = (
        timezone.localize(datetime.combine(today + timedelta(days=1), time.min))
        .astimezone(pytz.UTC).replace(tzinfo=None)
    )
    pending = Order.query.filter_by(status="pending").count()
    delivered = Order.query.filter_by(status="delivered").count()

    low_stock = (
        Product.query.filter(Product.is_active.is_(True))
        .filter(Product.stock <= Product.low_stock_threshold)
        .order_by(Product.stock.asc())
        .limit(10)
        .all()
    )

    today_orders = Order.query.filter(Order.created_at >= start, Order.created_at < end)
    today_count = today_orders.count()
    today_value = (
        today_orders.filter(Order.status != "cancelled")
        .with_entities(func.coalesce(func.sum(Order.total), 0)).scalar()
    )
    active_products = Product.query.filter_by(is_active=True).count()
    low_stock_count = Product.query.filter(
        Product.is_active.is_(True), Product.stock <= Product.low_stock_threshold
    ).count()
    recent_orders = Order.query.order_by(
        (Order.status == "pending").desc(), Order.created_at.desc(), Order.id.desc()
    ).limit(10).all()
    week_start = today - timedelta(days=6)
    labels, daily_values = [], []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        day_start = (
            timezone.localize(datetime.combine(day, time.min))
            .astimezone(pytz.UTC).replace(tzinfo=None)
        )
        day_end = (
            timezone.localize(datetime.combine(day + timedelta(days=1), time.min))
            .astimezone(pytz.UTC).replace(tzinfo=None)
        )
        daily = Order.query.filter(
            Order.created_at >= day_start,
            Order.created_at < day_end,
            Order.status != "cancelled",
        )
        labels.append(day.strftime("%a %d"))
        day_value = daily.with_entities(func.coalesce(func.sum(Order.total), 0)).scalar()
        daily_values.append(float(day_value or 0))

    return render_template(
        "admin/dashboard.html",
        pending=pending,
        delivered=delivered,
        today_count=today_count,
        today_value=today_value,
        active_products=active_products,
        low_stock_count=low_stock_count,
        chart_labels=labels,
        chart_values=daily_values,
        low_stock=low_stock,
        recent_orders=recent_orders,
    )


@admin_bp.route("/analytics")
@admin_required
def analytics():
    timezone = pytz.timezone(current_app.config.get("STORE_TIMEZONE", "Africa/Cairo"))
    today = datetime.now(timezone).date()
    start = (
        timezone.localize(datetime.combine(today - timedelta(days=13), time.min))
        .astimezone(pytz.UTC).replace(tzinfo=None)
    )
    end = (
        timezone.localize(datetime.combine(today + timedelta(days=1), time.min))
        .astimezone(pytz.UTC).replace(tzinfo=None)
    )
    top_products = (
        db.session.query(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label("units_sold"),
            func.sum(OrderItem.line_total).label("revenue"),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.created_at >= start, Order.created_at < end)
        .filter(Order.status != "cancelled")
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc(), func.sum(OrderItem.line_total).desc())
        .limit(10).all()
    )
    delivery_counts = dict(
        db.session.query(Order.delivery_method, func.count(Order.id))
        .filter(Order.created_at >= start, Order.created_at < end)
        .filter(Order.status != "cancelled")
        .group_by(Order.delivery_method).all()
    )
    delivery_total = sum(delivery_counts.values())
    status_counts = dict(
        db.session.query(Order.status, func.count(Order.id))
        .group_by(Order.status).all()
    )
    return render_template(
        "admin/analytics.html",
        top_products=top_products,
        delivery_counts=delivery_counts,
        delivery_total=delivery_total,
        period_total=Order.query.filter(
            Order.created_at >= start, Order.created_at < end,
            Order.status != "cancelled",
        ).count(),
        status_counts=status_counts,
        delivered=Order.query.filter_by(status="delivered").count(),
        pending=Order.query.filter_by(status="pending").count(),
    )


@admin_bp.route("/inventory")
@admin_required
def inventory():
    from sqlalchemy import case
    products = Product.query.filter(Product.is_active.is_(True)).order_by(
        case((Product.stock == 0, 0), (Product.stock <= Product.low_stock_threshold, 1), else_=2),
        Product.stock.asc(), Product.name.asc(),
    ).all()
    return render_template("admin/inventory.html", products=products)


@admin_bp.route("/inventory/<int:product_id>", methods=["POST"])
@admin_required
def inventory_update(product_id):
    from flask import flash, redirect, request, url_for
    from app.blueprints.admin.audit import record_admin_event

    product = Product.query.filter_by(id=product_id, is_active=True).first_or_404()
    try:
        stock = int(request.form.get("stock", ""))
        threshold = int(request.form.get("low_stock_threshold", ""))
        if stock < 0 or threshold < 0:
            raise ValueError
    except (TypeError, ValueError):
        flash("أدخل أرقاماً صحيحة غير سالبة للمخزون وحد التنبيه.", "danger")
        return redirect(url_for("admin.inventory"))
    old_stock, old_threshold = product.stock, product.low_stock_threshold
    product.stock = stock
    product.low_stock_threshold = threshold
    db.session.commit()
    if old_stock != stock or old_threshold != threshold:
        record_admin_event("inventory_quick_updated", detail=(
            f"product_id={product.id}; stock={old_stock}->{stock}; "
            f"threshold={old_threshold}->{threshold}"
        ))
    flash("تم تحديث بيانات المخزون.", "success")
    return redirect(url_for("admin.inventory"))
