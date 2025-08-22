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

# Human-friendly labels for select social and messaging packages.  This map is
# referenced by :mod:`social_app_finder` to keep the list of curated social apps
# in a single location.
SOCIAL_APP_LABELS = {
    # TikTok and variants
    "com.zhiliaoapp.musically": "TikTok",
    "com.ss.android.ugc.trill": "TikTok",
    "com.ss.android.ugc.aweme": "TikTok",
    "com.ss.android.ugc.aweme.lite": "TikTok Lite",
    "com.zhiliaoapp.musically.go": "TikTok Lite",
    "com.tiktok.android": "TikTok",

    # Meta/Facebook ecosystem
    "com.instagram.android": "Instagram",
    "com.facebook.katana": "Facebook",
    "com.facebook.lite": "Facebook Lite",
    "com.facebook.orca": "Messenger",

    # Messaging platforms
    "com.whatsapp": "WhatsApp",
    "com.whatsapp.w4b": "WhatsApp Business",
    "org.telegram.messenger": "Telegram",
    "com.discord": "Discord",
    "com.tencent.mm": "WeChat",
    "org.thoughtcrime.securesms": "Signal",
    "jp.naver.line.android": "LINE",

    # Other social platforms
    "com.snapchat.android": "Snapchat",
    "com.twitter.android": "Twitter",
    "com.reddit.frontpage": "Reddit",
    "com.vkontakte.android": "VK",
    "com.pinterest": "Pinterest",
    "com.linkedin.android": "LinkedIn",
}


def get_category(package: str) -> str:
    """Return the high-level category for ``package``."""
    return KNOWN_APPS.get(package, DEFAULT_CATEGORY)
