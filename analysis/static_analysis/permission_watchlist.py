"""List of permissions considered sensitive or high risk."""

SENSITIVE_PERMISSIONS = {
    "android.permission.RECORD_AUDIO",
    "android.permission.READ_SMS",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.SYSTEM_ALERT_WINDOW",
}


def is_sensitive(permission: str) -> bool:
    """Return True if ``permission`` is considered sensitive."""
    return permission in SENSITIVE_PERMISSIONS
