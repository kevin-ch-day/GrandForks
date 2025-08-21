# utils/about_app.py

from config import app_config
import utils.logging_utils.logging_engine as log


def about_app():
    log.info("Viewed About App")

    print("\nAbout App")
    print("-------------------")
    print(f"Name   : {app_config.APP_NAME}")
    print(f"Version: {app_config.APP_VERSION}")
    print(f"GitHub : {app_config.APP_GITHUB_REPO}\n")
