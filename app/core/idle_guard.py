"""Single authoritative idle / auto-lock monitor for the desktop session."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtWidgets import QApplication, QDialog

from app.core.session import session

# Genuine user interaction — not focus/activation noise, not background timers.
_ACTIVITY_EVENTS = frozenset(
    {
        QEvent.Type.MouseButtonPress,
        QEvent.Type.MouseButtonDblClick,
        QEvent.Type.KeyPress,
        QEvent.Type.Wheel,
        QEvent.Type.TouchBegin,
        QEvent.Type.TabletPress,
        QEvent.Type.ShortcutOverride,
    }
)


class IdleGuard(QObject):
    """One event filter + one timer. Focus loss never locks by itself."""

    def __init__(self, app: QApplication, window, *, password_required: bool) -> None:
        super().__init__(app)
        self._app = app
        self._window = window
        self._password_required = bool(password_required)
        self._dialog_open = False
        self._armed = False
        self._installed = False
        self._timer = QTimer(self)
        self._timer.setInterval(15_000)
        self._timer.timeout.connect(self._tick)

    @property
    def installed(self) -> bool:
        return self._installed

    def arm(self, timeout_sec: int) -> None:
        """Start monitoring after successful authentication."""
        session.timeout_sec = max(0, int(timeout_sec))
        session.touch()
        self._armed = True
        if not self._installed:
            self._app.installEventFilter(self)
            self._installed = True
        if not self._timer.isActive():
            self._timer.start()

    def disarm(self) -> None:
        self._armed = False
        self._timer.stop()

    def set_timeout_sec(self, timeout_sec: int) -> None:
        session.timeout_sec = max(0, int(timeout_sec))
        session.touch()

    def lock_now(self) -> None:
        """Manual lock — immediate when a password is configured."""
        if not self._password_required:
            return
        if not session.locked:
            session.lock()
        self._show_unlock()

    def eventFilter(self, _obj, event) -> bool:  # noqa: N802 — Qt API
        if not self._armed or session.locked or self._dialog_open:
            return False
        etype = event.type()
        if etype in _ACTIVITY_EVENTS:
            session.touch()
        return False

    def _tick(self) -> None:
        if not self._armed or not self._password_required:
            return
        if session.locked or self._dialog_open:
            return
        if not session.idle_too_long():
            return
        session.lock()
        self._show_unlock()

    def _show_unlock(self) -> None:
        if self._dialog_open:
            return
        self._dialog_open = True
        try:
            from app.windows.unlock_dialog import UnlockDialog
            import sys

            dlg = UnlockDialog(self._window)
            result = dlg.exec()
            if result != QDialog.DialogCode.Accepted:
                sys.exit(0)
            # UnlockDialog already authenticated + touched; reinforce idle baseline.
            session.touch()
        finally:
            self._dialog_open = False


_guard: IdleGuard | None = None


def get_idle_guard() -> IdleGuard | None:
    return _guard


def install_idle_guard(app: QApplication, window, *, password_required: bool, timeout_sec: int) -> IdleGuard:
    """Install at most one idle guard for the process lifetime."""
    global _guard
    if _guard is not None and _guard.installed:
        _guard._password_required = bool(password_required)
        _guard._window = window
        _guard.arm(timeout_sec)
        return _guard
    _guard = IdleGuard(app, window, password_required=password_required)
    _guard.arm(timeout_sec)
    return _guard
