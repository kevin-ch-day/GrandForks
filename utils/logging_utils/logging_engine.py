# utils/logging_utils/logging_engine.py

from utils.logging_utils.logging_core import LoggingCore


# initialize the core logging system once
_core = LoggingCore()
_logger = _core.get_logger()


def info(message: str):
    # log informational messages
    _logger.info(message)


def warning(message: str):
    # log warnings
    _logger.warning(message)


def error(message: str):
    # log errors
    _logger.error(message)


def debug(message: str):
    # log debug messages
    _logger.debug(message)


def critical(message: str):
    # log critical issues
    _logger.critical(message)


def set_console_level(level: int) -> None:
    """Expose ability to tweak console log level at runtime."""

    _core.set_console_level(level)
