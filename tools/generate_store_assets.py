"""Generate original local storefront images (not manufacturer packaging)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "app" / "static" / "img"
HERO = IMG / "hero"

CANS = [
    {"name": "can-1.png", "body": (18, 18, 18), "accent": (180, 255, 0), "label": (32, 40, 18)},
    {"name": "can-2.png", "body": (250, 214, 180), "accent": (255, 140, 70), "label": (90, 40, 20)},
    {"name": "can-3.png", "body": (255, 190, 210), "accent": (210, 50, 120), "label": (90, 20, 50)},
    {"name": "can-4.png", "body": (40, 180, 170), "accent": (180, 255, 230), "label": (10, 70, 70)},
    {"name": "can-5.png", "body": (255, 120, 50), "accent": (255, 220, 80), "label": (120, 40, 10)},
    {"name": "can-6.png", "body": (180, 30, 55), "accent": (255, 180, 200), "label": (80, 10, 25)},
]


def _ellipse(draw, xy, fill, outline=None, width=1):
    draw.ellipse(xy, fill=fill, outline=outline, width=width)


def draw_can(spec: dict, size=(720, 1200)) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    cx = w // 2
    can_w = 340
    top = 90
    bottom = h - 80
    left = cx - can_w // 2
    right = cx + can_w // 2
    body = spec["body"]
    accent = spec["accent"]
    label = spec["label"]

    # Shadow
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((left + 18, top + 40, right + 28, bottom + 30), radius=160, fill=(0, 0, 0, 90))
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    img = Image.alpha_composite(img, shadow)

    # Body
    d.rounded_rectangle((left, top + 70, right, bottom), radius=150, fill=body + (255,))

    # Side highlight
    d.rectangle((left + 18, top + 120, left + 46, bottom - 40), fill=(255, 255, 255, 38))
    d.rectangle((right - 40, top + 140, right - 18, bottom - 50), fill=(0, 0, 0, 40))

    # Top rim
    _ellipse(d, (left + 20, top + 40, right - 20, top + 130), fill=(70, 70, 70, 255))
    _ellipse(d, (left + 48, top + 52, right - 48, top + 112), fill=(28, 28, 28, 255))
    _ellipse(d, (left + 88, top + 62, right - 88, top + 98), fill=(12, 12, 12, 255))

    # Accent ring
    d.rectangle((left + 8, top + 210, right - 8, top + 250), fill=accent + (255,))

    # Label panel
    d.rounded_rectangle(
        (left + 40, top + 300, right - 40, bottom - 160),
        radius=28,
        fill=label + (230,),
    )
    d.rounded_rectangle(
        (left + 58, top + 330, right - 58, top + 470),
        radius=18,
        fill=accent + (255,),
    )

    try:
        font_big = ImageFont.truetype("arial.ttf", 54)
        font_small = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font_big = ImageFont.load_default()
        font_small = font_big

    text = "ME"
    bbox = d.textbbox((0, 0), text, font=font_big)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((w - tw) / 2, top + 365), text, fill=(10, 10, 10, 255), font=font_big)

    sub = "ENERGY"
    bbox = d.textbbox((0, 0), sub, font=font_small)
    tw = bbox[2] - bbox[0]
    d.text(((w - tw) / 2, bottom - 250), sub, fill=(245, 245, 245, 240), font=font_small)

    # Bottom rim
    d.rectangle((left + 12, bottom - 36, right - 12, bottom - 8), fill=(30, 30, 30, 255))

    img = Image.alpha_composite(img, layer)
    return img


def draw_placeholder() -> Image.Image:
    img = Image.new("RGBA", (800, 800), (12, 12, 12, 255))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((80, 80, 720, 720), radius=36, outline=(180, 255, 0, 180), width=4)
    d.rounded_rectangle((280, 180, 520, 620), radius=120, outline=(180, 255, 0, 220), width=6)
    d.ellipse((310, 150, 490, 230), outline=(180, 255, 0, 220), width=6)
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except OSError:
        font = ImageFont.load_default()
    text = "صورة المنتج"
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    d.text(((800 - tw) / 2, 650), text, fill=(180, 255, 0, 255), font=font)
    return img


def draw_og() -> Image.Image:
    img = Image.new("RGB", (1200, 630), (10, 10, 10))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 1200, 12), fill=(180, 255, 0))
    try:
        font = ImageFont.truetype("arial.ttf", 64)
        small = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
        small = font
    d.text((80, 220), "Monster EG", fill=(180, 255, 0), font=font)
    d.text((80, 320), "Independent energy drink storefront", fill=(200, 200, 200), font=small)
    return img


def write_placeholder_svg(path: Path) -> None:
    path.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800" role="img" aria-label="Placeholder">
  <rect width="800" height="800" fill="#0c0c0c"/>
  <rect x="80" y="80" width="640" height="640" rx="36" fill="none" stroke="#b4ff00" stroke-width="4"/>
  <rect x="280" y="180" width="240" height="440" rx="120" fill="none" stroke="#b4ff00" stroke-width="6"/>
  <ellipse cx="400" cy="190" rx="90" ry="40" fill="none" stroke="#b4ff00" stroke-width="6"/>
  <text x="400" y="680" text-anchor="middle" fill="#b4ff00" font-size="36" font-family="Arial, sans-serif">صورة المنتج</text>
</svg>
""",
        encoding="utf-8",
    )


def draw_favicon() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (10, 10, 10, 255))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((4, 4, 60, 60), radius=12, fill=(180, 255, 0, 255))
    try:
        font = ImageFont.truetype("arialbd.ttf", 36)
    except OSError:
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except OSError:
            font = ImageFont.load_default()
    d.text((16, 10), "M", fill=(10, 10, 10, 255), font=font)
    return img


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    HERO.mkdir(parents=True, exist_ok=True)
    (ROOT / "app" / "static" / "uploads").mkdir(parents=True, exist_ok=True)
    gitkeep = ROOT / "app" / "static" / "uploads" / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")

    for spec in CANS:
        draw_can(spec).save(HERO / spec["name"], "PNG", optimize=True)
        print(f"wrote {HERO / spec['name']}")

    draw_placeholder().save(IMG / "placeholder.png", "PNG", optimize=True)
    write_placeholder_svg(IMG / "placeholder.svg")
    draw_og().save(IMG / "og-image.jpg", "JPEG", quality=88)
    fav = draw_favicon()
    fav.save(IMG / "favicon.png", "PNG")
    fav.save(IMG / "favicon.ico", format="ICO", sizes=[(32, 32), (64, 64)])
    print("assets ready")


if __name__ == "__main__":
    main()
