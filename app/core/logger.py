import logging

from app.core.constants import LOG_FILE

logger = logging.getLogger("JU-TAN Office")
logger.setLevel(logging.INFO)
logger.addHandler(logging.NullHandler())


def configure_logging():
    """Configure file and console logging once, at application startup."""
    if any(getattr(handler, "_ju_tan_handler", False) for handler in logger.handlers):
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )
    file_handler._ju_tan_handler = True
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler._ju_tan_handler = True
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
