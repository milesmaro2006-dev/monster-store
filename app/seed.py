"""
Seed script: يضيف فئات ومنتجات تجريبية للتطوير المحلي فقط.
الأسعار والكميات عيّنة ويجب استبدالها بالقيم الحقيقية من لوحة التحكم.
يستخدمه:
    flask seed
"""
from decimal import Decimal
from app.extensions import db
from app.models.category import Category
from app.models.product import Product
from app.models.settings import StoreSettings


CATEGORIES = [
    {"name": "مشروبات طاقة ومستوردة", "name_en": "Imported Energy Drinks", "slug": "imported-energy"},
    {"name": "قهوة وبوبا مثلجة", "name_en": "Iced Coffee & Boba", "slug": "iced-coffee-boba"},
    {"name": "سناكس ومقرمشات", "name_en": "Snacks & Crisps", "slug": "snacks-crisps"},
    {"name": "شوكولاتة وحلويات", "name_en": "Chocolate & Sweets", "slug": "chocolate-sweets"},
    {"name": "زيرو سكر", "name_en": "Zero Sugar", "slug": "zero-sugar"},
    {"name": "نكهات فواكه", "name_en": "Fruit Flavors", "slug": "fruit"},
    {"name": "إصدارات خاصة", "name_en": "Special Editions", "slug": "special"},
]


PRODUCTS = [
    {
        "name": "مونستر ألترا بيتشي كين",
        "name_en": "Monster Ultra Peachy Keen",
        "slug": "monster-ultra-peachy-keen",
        "flavor": "خوخ",
        "flavor_en": "Peach",
        "description": "مشروب طاقة بنكهة الخوخ، بدون سكر. منعش وخفيف.",
        "description_en": "Zero sugar energy drink with a refreshing peach flavor.",
        "price": Decimal("250.00"),
        "stock": 50,
        "is_featured": True,
        "category_slug": "zero-sugar",
        "image_url": "img/hero/can-2.png",
    },
    {
        "name": "مونستر ألترا روزا",
        "name_en": "Monster Ultra Rosa",
        "slug": "monster-ultra-rosa",
        "flavor": "ورد",
        "flavor_en": "Rosa",
        "description": "نكهة الورد الجديدة من مونستر، بدون سكر.",
        "description_en": "A unique rosé flavor, zero sugar.",
        "price": Decimal("250.00"),
        "stock": 40,
        "is_featured": True,
        "category_slug": "zero-sugar",
        "image_url": "img/hero/can-3.png",
    },
    {
        "name": "مونستر ألترا بارادايس",
        "name_en": "Monster Ultra Paradise",
        "slug": "monster-ultra-paradise",
        "flavor": "كيوي وليمون",
        "flavor_en": "Kiwi & Lime",
        "description": "نكهة استوائية من الكيوي والليمون، بدون سكر.",
        "description_en": "Tropical kiwi-lime flavor, zero sugar.",
        "price": Decimal("250.00"),
        "stock": 60,
        "is_featured": True,
        "category_slug": "zero-sugar",
        "image_url": "img/hero/can-4.png",
    },
    {
        "name": "مونستر VR46 ذا دكتور",
        "name_en": "Monster VR46 The Doctor",
        "slug": "monster-vr46-the-doctor",
        "flavor": "فواكه استوائية",
        "flavor_en": "Tropical",
        "description": "إصدار خاص بتوقيع Valentino Rossi. نكهة فواكه استوائية.",
        "description_en": "Special Valentino Rossi edition. Tropical fruit flavor.",
        "price": Decimal("250.00"),
        "stock": 30,
        "is_featured": False,
        "category_slug": "special",
        "image_url": "img/hero/can-1.png",
    },
    {
        "name": "مونستر بايبلاين بانش",
        "name_en": "Monster Pipeline Punch",
        "slug": "monster-pipeline-punch",
        "flavor": "فواكه استوائية وبابايا",
        "flavor_en": "Tropical & Papaya",
        "description": "خلطة فواكه استوائية مع البابايا. نكهة قوية ومنعشة.",
        "description_en": "Tropical fruit punch with papaya.",
        "price": Decimal("250.00"),
        "stock": 35,
        "is_featured": True,
        "category_slug": "fruit",
        "image_url": "img/hero/can-5.png",
    },
    {
        "name": "مونستر لاندو نوريس",
        "name_en": "Monster Lando Norris",
        "slug": "monster-lando-norris",
        "flavor": "فراولة وكريم",
        "flavor_en": "Strawberry & Cream",
        "description": "إصدار خاص من Lando Norris. نكهة الفراولة والكريم.",
        "description_en": "Special Lando Norris edition. Strawberry & cream flavor.",
        "price": Decimal("250.00"),
        "stock": 25,
        "is_featured": True,
        "category_slug": "special",
        "image_url": "img/hero/can-6.png",
    },
]


def run_seed() -> None:
    """يشغّل الـ seed بشكل idempotent — مش بيكرر لو موجود."""
    # 1) الإعدادات الافتراضية
    settings = StoreSettings.get()
    if settings.default_delivery_fee is None:
        settings.default_delivery_fee = Decimal("95.00")

    # 2) الفئات
    cat_map = {}
    for c in CATEGORIES:
        existing = Category.query.filter_by(slug=c["slug"]).first()
        if not existing:
            existing = Category.query.filter_by(name=c["name"]).first()
        if not existing:
            existing = Category(**c)
            db.session.add(existing)
            db.session.flush()
        cat_map[c["slug"]] = existing

    # 3) المنتجات
    for product_data in PRODUCTS:
        existing = Product.query.filter_by(slug=product_data["slug"]).first()
        if existing:
            continue
        category = cat_map.get(product_data["category_slug"])
        fields = {
            key: value
            for key, value in product_data.items()
            if key != "category_slug"
        }
        product = Product(**fields, category_id=category.id if category else None)
        db.session.add(product)

    db.session.commit()
    print("✅ Seed completed.")
