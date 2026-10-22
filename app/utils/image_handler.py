# Image upload + validation
import os
import secrets
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def _allowed(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_product_image(file_storage) -> str | None:
    """يحفظ صورة المنتج ويرجع المسار النسبي أو None."""
    if not file_storage or not file_storage.filename:
        return None

    if not _allowed(file_storage.filename):
        raise ValueError("صيغة الصورة غير مدعومة (المسموح: png, jpg, jpeg, webp).")

    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[1].lower()
    unique = f"{secrets.token_hex(8)}.{ext}"

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    full_path = upload_dir / unique

    file_storage.save(full_path)

    # التحقق إن الملف صورة فعلاً
    try:
        from PIL import Image, ImageOps
        with Image.open(full_path) as img:
            img.verify()
        if ext != "webp":
            webp_path = full_path.with_suffix(".webp")
            try:
                with Image.open(full_path) as img:
                    optimized = ImageOps.exif_transpose(img)
                    optimized.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                    if optimized.mode not in ("RGB", "RGBA"):
                        optimized = optimized.convert(
                            "RGBA" if "transparency" in optimized.info else "RGB"
                        )
                    optimized.save(
                        webp_path,
                        format="WEBP",
                        quality=84,
                        method=6,
                    )
            except Exception:
                if webp_path.exists():
                    webp_path.unlink()
    except Exception:
        os.remove(full_path)
        raise ValueError("الملف المرفوع ليس صورة صحيحة.")

    return f"uploads/{unique}"
