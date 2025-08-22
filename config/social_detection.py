"""Curated package IDs and keyword tokens for social app detection."""

# Mapping of known social/messaging package identifiers to human-friendly labels.
SOCIAL_APP_PACKAGES = {
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

# Keyword tokens searched within package names for loose matches.
KEYWORD_TOKENS = [
    "tiktok",
    "facebook",
    "instagram",
    "whatsapp",
    "telegram",
    "discord",
    "wechat",
    "signal",
    "line",
    "snap",
    "snapchat",
    "twitter",
    "reddit",
    "vk",
    "pinterest",
    "linkedin",
]
