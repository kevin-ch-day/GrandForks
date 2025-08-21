# utils/logging_utils/logging_core.py

import logging
from pathlib import Path


class LoggingCore:
    def __init__(self, log_name="android_tool", log_dir="logs", level=logging.INFO):
        # ensure logs directory exists
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # file path for logs
        log_file = self.log_dir / f"{log_name}.log"

        # create logger
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(level)

        # formatter for logs
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )

        # console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # file handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        # return the logger instance
        return self.logger
