# vendor_normalizer.py
import re
from typing import Dict

# Centralized vendor patterns
VENDOR_PATTERNS = {
    r"^(moto|motorola)": "Motorola",
    r"^(sm-|samsung)": "Samsung",
    r"(pixel)": "Google",
    r"(nexus)": "Google",
    r"(oneplus)": "OnePlus",
    r"(oppo)": "Oppo",
    r"(vivo)": "Vivo",
    r"(huawei|honor)": "Huawei",
    r"(xiaomi|redmi|mi)": "Xiaomi",
    r"(realme)": "Realme",
    r"(nokia)": "Nokia",
    r"(sony)": "Sony",
    r"(lg)": "LG",
    r"(asus|zenfone|rog)": "Asus",
    r"(emulator|sdk_gphone)": "Android Emulator",
}


def normalize_vendor(details: Dict[str, str]) -> str:
    """
    Try to normalize vendor name based on adb extras or model patterns.
    - Checks 'vendor' field if available.
    - Falls back to model regex matching.
    """
    vendor = details.get("vendor", "").strip()
    model = details.get("model", "").lower()

    # ✅ If adb already reports vendor → trust that
    if vendor:
        return vendor.capitalize()

    # ✅ Try regex pattern matching on model
    for pattern, name in VENDOR_PATTERNS.items():
        if re.search(pattern, model, re.IGNORECASE):
            return name

    # ✅ Fallback
    return "Unknown"