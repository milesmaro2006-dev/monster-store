# Input validators
import re

EGYPT_PHONE_RE = re.compile(r"^1[0125]\d{8}$")

PLACEHOLDER_VALUES = {
    "",
    "+201000000000",
    "201000000000",
    "01000000000",
    "info@monster-eg.local",
    "القاهرة، مصر",
}


def _digits_local_egypt(phone: str) -> str:
    cleaned = re.sub(r"[\s\-()]", "", phone or "")
    if cleaned.startswith("0020"):
        cleaned = cleaned[4:]
    elif cleaned.startswith("+20"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("20") and len(cleaned) >= 12:
        cleaned = cleaned[2:]
    if cleaned.startswith("0"):
        cleaned = cleaned[1:]
    return cleaned


def is_valid_egypt_phone(phone: str) -> bool:
    if not phone:
        return False
    return bool(EGYPT_PHONE_RE.fullmatch(_digits_local_egypt(phone)))


def normalize_phone(phone: str) -> str:
    local = _digits_local_egypt(phone)
    if EGYPT_PHONE_RE.fullmatch(local):
        return "+20" + local
    cleaned = re.sub(r"[\s\-()]", "", phone or "")
    return cleaned


def is_placeholder_value(value: str | None) -> bool:
    return (value or "").strip() in PLACEHOLDER_VALUES
