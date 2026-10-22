# Products CRUD
from flask import (
    render_template, request, redirect, url_for, flash, abort, jsonify
)
import secrets
from sqlalchemy.exc import IntegrityError
from app.blueprints.admin import admin_bp
from app.blueprints.admin.decorators import admin_required
from app.blueprints.admin.forms import ProductForm, CategoryForm, ProductQuickUpdateForm
from app.models.product import Product
from app.models.category import Category
from app.models.tag import FlavorTag
from app.utils.helpers import slugify
from app.utils.image_handler import save_product_image
from app.extensions import db
from app.blueprints.admin.audit import record_admin_event
from sqlalchemy import or_, func


@admin_bp.route("/products")
@admin_required
def products_list():
    q = (request.args.get("q") or "").strip()
    category_id = request.args.get("category", type=int)
    stock = request.args.get("stock", "")
    featured = request.args.get("featured", "")
    state = request.args.get("state", "active")
    query = Product.query
    if q:
        term = f"%{q}%"
        query = query.filter(or_(
            Product.name.ilike(term), Product.name_en.ilike(term),
            Product.flavor.ilike(term), Product.flavor_en.ilike(term),
            Product.brand.ilike(term),
        ))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if state == "archived":
        query = query.filter(Product.is_active.is_(False))
    else:
        query = query.filter(Product.is_active.is_(True))
    if stock == "out":
        query = query.filter(Product.stock <= 0)
    elif stock == "low":
        query = query.filter(Product.stock > 0, Product.stock <= Product.low_stock_threshold)
    elif stock == "available":
        query = query.filter(Product.stock > Product.low_stock_threshold)
    if featured in {"yes", "no"}:
        query = query.filter(Product.is_featured.is_(featured == "yes"))
    pagination = query.order_by(Product.created_at.desc(), Product.id.desc()).paginate(
        page=max(request.args.get("page", 1, type=int), 1), per_page=20, error_out=False
    )
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template("admin/products.html", products=pagination.items, pagination=pagination,
                           categories=categories, q=q, category_id=category_id, stock=stock,
                           featured=featured, state=state)


@admin_bp.route("/products/new", methods=["GET", "POST"])
@admin_required
def product_new():
    form = ProductForm()
    flavor_tags = FlavorTag.query.order_by(FlavorTag.name_ar.asc()).all()
    form.category_id.choices = [(0, "— بدون —")] + [
        (c.id, c.name) for c in Category.query.filter_by(is_active=True).all()
    ]

    if form.validate_on_submit():
        try:
            image_url = None
            file = request.files.get("image")
            if file and file.filename:
                image_url = save_product_image(file)

            selected_tags = _selected_flavor_tags(request.form.getlist("tag_ids"))
            legacy_flavor = "، ".join(tag.name_ar for tag in selected_tags) or (form.flavor.data or "").strip()
            legacy_flavor_en = ", ".join(tag.name_en for tag in selected_tags) or (form.flavor_en.data or "").strip()
            product = Product(
                name=form.name.data.strip(),
                name_en=(form.name_en.data or "").strip() or None,
                brand=(form.brand.data or "").strip() or None,
                slug=slugify(form.name_en.data or form.name.data),
                flavor=legacy_flavor or None,
                flavor_en=legacy_flavor_en or None,
                volume=(form.volume.data or "").strip() or None,
                origin_country=(form.origin_country.data or "").strip() or None,
                calories=(form.calories.data or "").strip() or None,
                serving_advice=(form.serving_advice.data or "").strip() or "يُقدّم مثلجاً",
                description=(form.description.data or "").strip() or None,
                description_en=(form.description_en.data or "").strip() or None,
                price=form.price.data,
                stock=form.stock.data,
                low_stock_threshold=form.low_stock_threshold.data or 5,
                category_id=form.category_id.data or None,
                is_active=form.is_active.data,
                is_featured=form.is_featured.data,
                is_zero_sugar=form.is_zero_sugar.data,
                image_url=image_url,
            )
            product.tags = selected_tags
            db.session.add(product)
            db.session.commit()
            record_admin_event("product_created", detail=f"product_id={product.id}")
            flash("تم إضافة المنتج.", "success")
            return redirect(url_for("admin.portal_products_list"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("admin/product_form.html", form=form, product=None,
                           flavor_tags=flavor_tags,
                           selected_tag_ids=set(_safe_ints(request.form.getlist("tag_ids"))))


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def product_edit(product_id: int):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)

    form = ProductForm(obj=product)
    flavor_tags = FlavorTag.query.order_by(FlavorTag.name_ar.asc()).all()
    form.category_id.choices = [(0, "— بدون —")] + [
        (c.id, c.name) for c in Category.query.filter_by(is_active=True).all()
    ]
    if not form.is_submitted():
        form.category_id.data = product.category_id or 0

    if form.validate_on_submit():
        try:
            old_price, old_stock = product.price, product.stock
            file = request.files.get("image")
            if file and file.filename:
                product.image_url = save_product_image(file)

            product.name = form.name.data.strip()
            product.name_en = (form.name_en.data or "").strip() or None
            product.brand = (form.brand.data or "").strip() or None
            selected_tags = _selected_flavor_tags(request.form.getlist("tag_ids"))
            product.tags = selected_tags
            product.flavor = "، ".join(tag.name_ar for tag in selected_tags) or (form.flavor.data or "").strip() or None
            product.flavor_en = ", ".join(tag.name_en for tag in selected_tags) or (form.flavor_en.data or "").strip() or None
            product.volume = (form.volume.data or "").strip() or None
            product.origin_country = (form.origin_country.data or "").strip() or None
            product.calories = (form.calories.data or "").strip() or None
            product.serving_advice = (form.serving_advice.data or "").strip() or "يُقدّم مثلجاً"
            product.description = (form.description.data or "").strip() or None
            product.description_en = (form.description_en.data or "").strip() or None
            product.price = form.price.data
            product.stock = form.stock.data
            product.low_stock_threshold = form.low_stock_threshold.data or 5
            product.category_id = form.category_id.data or None
            product.is_active = form.is_active.data
            product.is_featured = form.is_featured.data
            product.is_zero_sugar = form.is_zero_sugar.data

            db.session.commit()
            if old_price != product.price or old_stock != product.stock:
                record_admin_event("product_updated", detail=(
                    f"product_id={product.id}; price_changed={old_price != product.price}; "
                    f"stock_changed={old_stock != product.stock}"
                ))
            flash("تم تحديث المنتج.", "success")
            return redirect(url_for("admin.portal_products_list"))
        except ValueError as e:
            flash(str(e), "danger")

    selected_tag_ids = (set(_safe_ints(request.form.getlist("tag_ids"))) if form.is_submitted()
                        else {tag.id for tag in product.tags})
    return render_template("admin/product_form.html", form=form, product=product,
                           flavor_tags=flavor_tags, selected_tag_ids=selected_tag_ids)


def _safe_ints(values):
    result = []
    for value in values:
        try:
            result.append(int(value))
        except (TypeError, ValueError):
            continue
    return result


def _selected_flavor_tags(values):
    ids = set(_safe_ints(values))
    return FlavorTag.query.filter(FlavorTag.id.in_(ids)).order_by(FlavorTag.id.asc()).all() if ids else []


@admin_bp.route("/flavor-tags/quick-add", methods=["POST"])
@admin_required
def flavor_tag_quick_add():
    data = request.get_json(silent=True) or request.form
    name_ar = data.get("name_ar")
    name_en = data.get("name_en", "")
    if not isinstance(name_ar, str) or not name_ar.strip() or len(name_ar.strip()) > 50:
        return jsonify(success=False, error="أدخل اسم الوسم بالعربية (حتى 50 حرفاً)."), 400
    if not isinstance(name_en, str) or len(name_en.strip()) > 50:
        return jsonify(success=False, error="اسم الوسم بالإنجليزية يجب ألا يتجاوز 50 حرفاً."), 400
    name_ar = name_ar.strip()
    name_en = name_en.strip() or name_ar
    existing = FlavorTag.query.filter_by(name_ar=name_ar).first()
    if existing:
        return jsonify(success=True, id=existing.id, name_ar=existing.name_ar,
                       name_en=existing.name_en, slug=existing.slug)
    base_slug = slugify(name_en) or f"flavor-{secrets.token_hex(3)}"
    slug = base_slug[:60]
    if FlavorTag.query.filter_by(slug=slug).first():
        slug = f"{base_slug[:52]}-{secrets.token_hex(3)}"
    tag = FlavorTag(name_ar=name_ar, name_en=name_en, slug=slug)
    db.session.add(tag)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existing = FlavorTag.query.filter_by(name_ar=name_ar).first()
        if existing:
            return jsonify(success=True, id=existing.id, name_ar=existing.name_ar,
                           name_en=existing.name_en, slug=existing.slug)
        return jsonify(success=False, error="تعذر إضافة الوسم. حاول مرة أخرى."), 409
    record_admin_event("flavor_tag_created", detail=f"tag_id={tag.id}")
    return jsonify(success=True, id=tag.id, name_ar=tag.name_ar,
                   name_en=tag.name_en, slug=tag.slug), 201


@admin_bp.route("/products/<int:product_id>/quick-update", methods=["POST"])
@admin_required
def product_quick_update(product_id: int):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    form = ProductQuickUpdateForm()
    if not form.validate_on_submit():
        messages = [error for errors in form.errors.values() for error in errors]
        flash("تعذر حفظ السعر والمخزون. " + " ".join(messages), "danger")
        return redirect(url_for("admin.portal_products_list"))

    old_price, old_stock = product.price, product.stock
    product.price = form.price.data
    product.stock = form.stock.data
    db.session.commit()
    record_admin_event("product_quick_updated", detail=(
        f"product_id={product.id}; price_changed={old_price != product.price}; "
        f"stock_changed={old_stock != product.stock}"
    ))
    flash("تم تحديث السعر والمخزون.", "success")
    return redirect(url_for("admin.portal_products_list"))


@admin_bp.route("/products/<int:product_id>/toggle", methods=["POST"])
@admin_required
def product_toggle(product_id: int):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    product.is_active = not product.is_active
    db.session.commit()
    record_admin_event("product_archived" if not product.is_active else "product_unarchived",
                       detail=f"product_id={product.id}")
    flash("تم التحديث.", "info")
    return redirect(url_for("admin.portal_products_list"))


@admin_bp.route("/categories", methods=["GET", "POST"])
@admin_required
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        c = Category(
            name=form.name.data.strip(),
            name_en=(form.name_en.data or "").strip() or None,
            slug=slugify(form.name_en.data or form.name.data),
            is_active=form.is_active.data,
        )
        db.session.add(c)
        db.session.commit()
        record_admin_event("category_created", detail=f"category_id={c.id}")
        flash("تم إضافة الفئة.", "success")
        return redirect(url_for("admin.categories"))

    all_categories = (
        db.session.query(
            Category,
            func.count(Product.id).label("product_count"),
        )
        .outerjoin(Product, Product.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.created_at.desc(), Category.id.desc())
        .all()
    )
    category_rows = [
        {"category": category, "product_count": product_count}
        for category, product_count in all_categories
    ]
    return render_template("admin/categories.html", form=form, categories=category_rows)


@admin_bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
@admin_required
def category_edit(category_id: int):
    category = db.session.get(Category, category_id)
    if not category:
        abort(404)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        name_ar = form.name.data.strip()
        name_en = (form.name_en.data or "").strip() or None
        duplicate_filters = [Category.name_ar == name_ar]
        if name_en:
            duplicate_filters.append(Category.name_en == name_en)
        duplicate = Category.query.filter(
            Category.id != category.id, or_(*duplicate_filters)
        ).first()
        if duplicate:
            flash("يوجد قسم آخر بهذا الاسم بالفعل.", "danger")
        else:
            category.name_ar = name_ar
            category.name_en = name_en
            category.is_active = form.is_active.data
            base_slug = slugify(name_en or name_ar)
            slug = base_slug
            suffix = 2
            while Category.query.filter(
                Category.id != category.id, Category.slug == slug
            ).first():
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            category.slug = slug
            db.session.commit()
            record_admin_event("category_updated", detail=f"category_id={category.id}")
            flash("تم تحديث الفئة.", "success")
            return redirect(url_for("admin.portal_categories"))
    return render_template("admin/category_form.html", form=form, category=category)


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@admin_required
def category_delete(category_id: int):
    category = db.session.get(Category, category_id)
    if not category:
        abort(404)
    linked_count = Product.query.filter_by(category_id=category.id).count()
    if linked_count:
        flash(
            f"لا يمكن حذف الفئة لأنها مرتبطة بـ {linked_count} منتج. انقل المنتجات إلى فئة أخرى أولاً.",
            "warning",
        )
        return redirect(url_for("admin.portal_categories"))
    db.session.delete(category)
    db.session.commit()
    record_admin_event("category_deleted", detail=f"category_id={category_id}")
    flash("تم حذف الفئة.", "success")
    return redirect(url_for("admin.portal_categories"))


@admin_bp.route("/categories/quick-add", methods=["POST"])
@admin_required
def category_quick_add():
    data = request.get_json(silent=True) or request.form
    name_ar = data.get("name_ar")
    name_en = data.get("name_en", "")
    if not isinstance(name_ar, str) or not name_ar.strip() or len(name_ar.strip()) > 80:
        return jsonify(success=False, error="أدخل اسم القسم بالعربية (حتى 80 حرفاً)."), 400
    if not isinstance(name_en, str) or len(name_en.strip()) > 80:
        return jsonify(success=False, error="اسم القسم بالإنجليزية يجب ألا يتجاوز 80 حرفاً."), 400

    name_ar = name_ar.strip()
    name_en = name_en.strip() or None
    existing = Category.query.filter_by(name=name_ar).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.session.commit()
        return jsonify(
            success=True, id=existing.id, name_ar=existing.name,
            name_en=existing.name_en or "", slug=existing.slug,
        )

    base_slug = slugify(name_en or name_ar)
    slug = base_slug
    while Category.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{secrets.token_hex(3)}"
    category = Category(name=name_ar, name_en=name_en, slug=slug, is_active=True)
    db.session.add(category)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existing = Category.query.filter_by(name=name_ar).first()
        if existing:
            return jsonify(
                success=True, id=existing.id, name_ar=existing.name,
                name_en=existing.name_en or "", slug=existing.slug,
            )
        return jsonify(success=False, error="تعذر إضافة القسم. حاول مرة أخرى."), 409

    record_admin_event("category_created", detail=f"category_id={category.id}")
    return jsonify(
        success=True, id=category.id, name_ar=category.name,
        name_en=category.name_en or "", slug=category.slug,
    ), 201


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def product_delete(product_id: int):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    # Keep the immutable product name/price snapshots in past orders.
    for item in product.order_items:
        item.product_id = None
    db.session.delete(product)
    db.session.commit()
    record_admin_event("product_deleted", detail=f"product_id={product_id}")
    flash("تم حذف المنتج مع الاحتفاظ بتفاصيل الطلبات السابقة.", "success")
    return redirect(url_for("admin.portal_products_list"))
