# Storefront routes
from flask import render_template, request, abort, url_for
from sqlalchemy import or_, false
from sqlalchemy import func
from decimal import Decimal, InvalidOperation
from app.blueprints.storefront import storefront_bp
from app.models.product import Product
from app.models.category import Category
from app.models.order import Order, OrderItem
from app.models.tag import FlavorTag, product_flavor_tags
from app.extensions import db
from app.blueprints.cart import service as cart_service


@storefront_bp.route("/")
def index():
    products = (
        Product.query.filter_by(is_active=True)
        .order_by(Product.created_at.desc())
        .limit(12)
        .all()
    )
    _mark_top_sellers(products)
    best_sellers = (
        Product.query.join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Product.is_active.is_(True),
            Order.status.in_(["confirmed", "shipped", "delivered"]),
        )
        .group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc(), Product.created_at.desc())
        .limit(4)
        .all()
    )
    _mark_top_sellers(best_sellers)
    categories = Category.query.filter_by(is_active=True).order_by(Category.name.asc()).all()
    return render_template(
        "storefront/index.html",
        products=products,
        best_sellers=best_sellers,
        categories=categories,
        hero_models=[{
            "url": url_for("static", filename="models/can-1.glb"),
            "fallback": url_for("static", filename="img/hero/monster-black-can.svg"),
            "label_ar": "مونستر الأسود الكلاسيكي",
            "label_en": "Monster Original Energy",
            "alt_ar": "عبوة مونستر السوداء الكلاسيكية",
            "alt_en": "Classic black Monster Energy can",
        }],
    )


@storefront_bp.route("/products")
def catalog():
    q = (request.args.get("q") or "").strip()
    category_slug = request.args.get("category") or ""
    flavor = request.args.get("flavor") or ""
    selected_tag_slugs = _requested_flavor_tags()
    brand = (request.args.get("brand") or "").strip()
    zero_sugar_only = request.args.get("zero_sugar") == "1"
    featured_only = request.args.get("featured") == "1"
    min_price = _decimal_filter(request.args.get("min_price"))
    max_price = _decimal_filter(request.args.get("max_price"))
    sort = request.args.get("sort") or "newest"
    page = request.args.get("page", 1, type=int) or 1

    query = Product.query.filter_by(is_active=True)
    catalog_total = Product.query.filter_by(is_active=True).count()

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Product.name.ilike(like),
                Product.name_en.ilike(like),
                Product.flavor.ilike(like),
                Product.flavor_en.ilike(like),
                Product.brand.ilike(like),
            )
        )

    if category_slug:
        query = query.join(Category).filter(Category.slug == category_slug)

    if flavor:
        query = query.filter(
            or_(Product.flavor == flavor, Product.flavor_en == flavor)
        )
    if selected_tag_slugs:
        requested_tags = []
        numeric_ids = []
        for value in selected_tag_slugs:
            if value.isdigit():
                numeric_ids.append(int(value))
            else:
                requested_tags.append(value)
        tag_query = FlavorTag.query.filter(
            or_(
                FlavorTag.slug.in_(requested_tags) if requested_tags else false(),
                FlavorTag.id.in_(numeric_ids) if numeric_ids else false(),
            )
        )
        resolved_ids = {tag.id for tag in tag_query.all()}
        if not resolved_ids or len(resolved_ids) != len(set(selected_tag_slugs)):
            query = query.filter(Product.id == -1)
        else:
            matching_products = db.session.query(product_flavor_tags.c.product_id).filter(
                product_flavor_tags.c.tag_id.in_(resolved_ids)
            )
            if request.args.get("tag_mode") == "all":
                matching_products = matching_products.group_by(
                    product_flavor_tags.c.product_id
                ).having(func.count(func.distinct(product_flavor_tags.c.tag_id)) == len(resolved_ids))
            query = query.filter(Product.id.in_(matching_products))
    if brand:
        query = query.filter(Product.brand == brand)
    if zero_sugar_only:
        query = query.filter(Product.is_zero_sugar.is_(True))
    if featured_only:
        query = query.filter(Product.is_featured.is_(True))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "popular":
        sales = (
            db.session.query(
                OrderItem.product_id.label("product_id"),
                func.sum(OrderItem.quantity).label("quantity_sold"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.status.in_(["confirmed", "shipped", "delivered"]))
            .group_by(OrderItem.product_id)
            .subquery()
        )
        query = query.outerjoin(sales, Product.id == sales.c.product_id).order_by(
            func.coalesce(sales.c.quantity_sold, 0).desc(), Product.created_at.desc()
        )
    else:
        query = query.order_by(Product.created_at.desc())
        sort = "newest"

    pagination = query.paginate(page=page, per_page=12, error_out=False)
    _mark_top_sellers(pagination.items)
    categories = Category.query.filter_by(is_active=True).all()
    brands = [name for (name,) in db.session.query(Product.brand).filter(
        Product.is_active.is_(True), Product.brand.isnot(None), Product.brand != ""
    ).distinct().order_by(Product.brand).all()]

    return render_template(
        "storefront/catalog.html",
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        flavors=db_flavors(),
        q=q,
        selected_category=category_slug,
        selected_flavor=flavor,
        flavor_tags=FlavorTag.query.order_by(FlavorTag.name_ar.asc()).all(),
        selected_tag_slugs=selected_tag_slugs,
        selected_brand=brand,
        zero_sugar_only=zero_sugar_only,
        featured_only=featured_only,
        brands=brands,
        min_price=request.args.get("min_price", ""),
        max_price=request.args.get("max_price", ""),
        selected_sort=sort,
        catalog_total=catalog_total,
    )


def _requested_flavor_tags():
    values = []
    for raw in request.args.getlist("tags"):
        values.extend(part.strip() for part in raw.split(",") if part.strip())
    for raw in request.args.getlist("flavor_tag"):
        values.extend(part.strip() for part in raw.split(",") if part.strip())
    # Keep query URLs deterministic and avoid applying one tag more than once.
    return list(dict.fromkeys(values))


@storefront_bp.route("/build-box", methods=["GET", "POST"])
def build_box():
    from flask import flash, redirect, session
    if request.method == "POST":
        success, message = cart_service.add_custom_box(request.form.getlist("product_ids"))
        flash(message, "success" if success else "warning")
        if success:
            return redirect(url_for("cart.view_cart"))
    products = Product.query.filter(Product.is_active.is_(True), Product.stock > 0).order_by(Product.created_at.desc()).all()
    _mark_top_sellers(products)
    return render_template("storefront/build_box.html", products=products)


def db_flavors():
    from app.extensions import db
    rows = (
        db.session.query(Product.flavor, Product.flavor_en)
        .filter(Product.is_active.is_(True))
        .distinct()
        .all()
    )
    result = []
    for ar, en in rows:
        if ar or en:
            raw_ar, raw_en = ar or en, en or ar
            result.append({
                "ar": raw_ar,
                "en": raw_en,
                "label_ar": _short_flavor(raw_ar),
                "label_en": _short_flavor(raw_en),
            })
    return result


def _short_flavor(value: str, max_length: int = 25) -> str:
    words = (value or "").split()
    concise = " ".join(words[:3])
    if len(concise) > max_length:
        return concise[: max_length - 1].rstrip() + "…"
    return concise


def _decimal_filter(value):
    if not value:
        return None
    try:
        amount = Decimal(value)
        return amount if amount.is_finite() and amount >= 0 else None
    except (InvalidOperation, TypeError, ValueError):
        return None


@storefront_bp.route("/product/<slug>")
def product_detail(slug: str):
    product = Product.query.filter_by(slug=slug, is_active=True).first()
    if not product:
        abort(404)

    related = (
        Product.query.filter(
            Product.is_active.is_(True),
            Product.id != product.id,
            Product.category_id == product.category_id,
        )
        .limit(4)
        .all()
    )
    _mark_top_sellers(related)
    return render_template(
        "storefront/product.html", product=product, related=related
    )


@storefront_bp.route("/search")
def search():
    q = (request.args.get("q") or "").strip()
    products = []
    if q:
        like = f"%{q}%"
        products = (
            Product.query.filter(Product.is_active.is_(True))
            .filter(
                or_(
                    Product.name.ilike(like),
                    Product.name_en.ilike(like),
                    Product.flavor.ilike(like),
                    Product.flavor_en.ilike(like),
                    Product.brand.ilike(like),
                )
            )
            .limit(50)
            .all()
        )
    _mark_top_sellers(products)
    return render_template("storefront/search.html", q=q, products=products)


def _mark_top_sellers(products):
    """Annotate product cards with the three highest-selling active products."""
    if not products:
        return
    top_ids = {
        product_id
        for (product_id,) in (
            db.session.query(OrderItem.product_id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.status.in_(["confirmed", "shipped", "delivered"]))
            .group_by(OrderItem.product_id)
            .order_by(func.sum(OrderItem.quantity).desc(), OrderItem.product_id.asc())
            .limit(3)
            .all()
        )
    }
    for product in products:
        product.is_top_seller = product.id in top_ids


@storefront_bp.route("/contact")
def contact():
    return render_template("storefront/contact.html")


@storefront_bp.route("/about")
def about():
    return render_template("store/about.html")


@storefront_bp.route("/faq")
def faq():
    return render_template("storefront/faq.html")


@storefront_bp.route("/policies/delivery")
def delivery_policy():
    return render_template("storefront/policy_delivery.html")


@storefront_bp.route("/policies/returns")
def returns_policy():
    return render_template("storefront/policy_returns.html")
