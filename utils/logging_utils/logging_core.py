# utils/logging_utils/logging_core.py

import logging
from pathlib import Path


class LoggingCore:
    def __init__(self, log_name: str = "android_tool", log_dir: str = "logs"):
        """Configure application-wide logging.

        A root logger is created at DEBUG level. Console output defaults to
        INFO while the log file captures DEBUG and above.
        """

        # ensure logs directory exists
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # file path for logs
        log_file = self.log_dir / f"{log_name}.log"

        # configure root logger
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        # avoid duplicate handlers if re-initialized
        self.logger.handlers.clear()

        # formatter for logs
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )

        # console handler at INFO by default
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.INFO)
        self.console_handler.setFormatter(formatter)
        self.logger.addHandler(self.console_handler)

        # file handler captures DEBUG messages
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def set_console_level(self, level: int) -> None:
        """Adjust the console handler log level."""

        self.console_handler.setLevel(level)

    def get_logger(self):
        # return the logger instance
        return self.logger
