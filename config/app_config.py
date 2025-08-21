# app_config.py

import os

APP_NAME: str = "Android Tool"
APP_VERSION: str = "0.0.1"
APP_GITHUB_REPO: str = "None"

# Default color theme palette. Can be overridden via the GF_THEME env var or
# the ``--theme`` runtime flag processed in ``main.py``.
THEME_PALETTE: str = os.getenv("GF_THEME", "cyber")
