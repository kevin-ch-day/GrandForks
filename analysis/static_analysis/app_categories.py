"""Mappings of known application package names to categories."""

# These mappings are placeholders and can be replaced with a database-driven
# approach in the future.
KNOWN_APPS = {
    "com.facebook.katana": "Social Media",
    "com.instagram.android": "Social Media",
    "com.snapchat.android": "Social Media",
    "com.twitter.android": "Social Media",
    "com.tiktok.android": "Social Media",
    "com.whatsapp": "Messaging",
    "com.facebook.orca": "Messaging",
    "org.telegram.messenger": "Messaging",
    "com.bankofamerica.mobilebanking": "Financial",
    "com.chase.sig.android": "Financial",
}

DEFAULT_CATEGORY = "Other"


def get_category(package: str) -> str:
    """Return the high-level category for ``package``."""
    return KNOWN_APPS.get(package, DEFAULT_CATEGORY)
