"""Mappings of known application package names to categories."""

# These mappings are placeholders and can be replaced with a database-driven
# approach in the future.
KNOWN_APPS = {
    # Social media platforms
    "com.facebook.katana": "Social Media",
    "com.facebook.lite": "Social Media",
    "com.instagram.android": "Social Media",
    "com.snapchat.android": "Social Media",
    "com.twitter.android": "Social Media",
    "com.tiktok.android": "Social Media",
    "com.zhiliaoapp.musically": "Social Media",
    "com.ss.android.ugc.trill": "Social Media",
    "com.ss.android.ugc.aweme": "Social Media",
    "com.ss.android.ugc.aweme.lite": "Social Media",
    "com.zhiliaoapp.musically.go": "Social Media",
    "com.reddit.frontpage": "Social Media",
    "com.vkontakte.android": "Social Media",
    "com.pinterest": "Social Media",
    "com.linkedin.android": "Social Media",

    # Messaging platforms
    "com.whatsapp": "Messaging",
    "com.whatsapp.w4b": "Messaging",
    "com.facebook.orca": "Messaging",
    "org.telegram.messenger": "Messaging",
    "com.discord": "Messaging",
    "com.tencent.mm": "Messaging",
    "org.thoughtcrime.securesms": "Messaging",
    "jp.naver.line.android": "Messaging",

    # Financial apps (examples)
    "com.bankofamerica.mobilebanking": "Financial",
    "com.chase.sig.android": "Financial",
}

DEFAULT_CATEGORY = "Other"

# Human-friendly labels for select social and messaging packages.  The mapping
# itself now lives in :mod:`config.social_detection` so that both static
# analysis and CSV detection utilities reference a single source of truth.  The
# name is preserved here for backward compatibility with existing imports.
from config.social_detection import SOCIAL_APP_PACKAGES as SOCIAL_APP_LABELS


def get_category(package: str) -> str:
    """Return the high-level category for ``package``."""
    return KNOWN_APPS.get(package, DEFAULT_CATEGORY)
