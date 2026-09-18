from functools import wraps

from PySide6.QtWidgets import QMessageBox

from app.core.errors import friendly_error_message
from app.core.logger import logger


def show_error(parent, error, title="Napaka"):
    logger.exception("UI operation failed", exc_info=error)
    QMessageBox.critical(parent, title, friendly_error_message(error))


def ui_error_boundary(title="Napaka"):
    """Catch UI action errors and present a safe message to the user."""
    def decorator(function):
        @wraps(function)
        def wrapped(self, *args, **kwargs):
            try:
                return function(self, *args, **kwargs)
            except Exception as error:
                show_error(self, error, title)
                return None
        return wrapped
    return decorator
