from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.core.logger import logger
from app.theme.colors import PALETTES, ThemeMode
from app.theme.fonts import apply_fonts

THEME_QSS_PATH = Path(__file__).resolve().parent / "theme.qss"


class ThemeManager:
    """Nalaga globalni theme.qss in omogoča preklop Light / Dark."""

    def __init__(self, mode: ThemeMode = ThemeMode.LIGHT) -> None:
        self._mode = mode
        self._template: str | None = None
        self._last_stylesheet: str | None = None
        self._defer_scheduled = False
        self._deferred_kwargs: dict | None = None

    @property
    def mode(self) -> ThemeMode:
        return self._mode

    def load_qss_template(self) -> str:
        # Always re-read so theme polish iterates without process restart tricks.
        if not THEME_QSS_PATH.exists():
            raise FileNotFoundError(f"Manjka theme.qss: {THEME_QSS_PATH}")
        self._template = THEME_QSS_PATH.read_text(encoding="utf-8")
        return self._template

    def build_stylesheet(
        self,
        mode: ThemeMode | None = None,
        accent_primary: str | None = None,
        accent_hover: str | None = None,
        card_radius: str = "12px",
        control_radius: str = "8px",
    ) -> str:
        palette = dict(PALETTES[mode or self._mode])
        if accent_primary:
            palette["PRIMARY"] = accent_primary
        if accent_hover:
            palette["PRIMARY_HOVER"] = accent_hover
        palette["CARD_RADIUS"] = card_radius
        palette["CONTROL_RADIUS"] = control_radius
        stylesheet = self.load_qss_template()
        for token, value in palette.items():
            stylesheet = stylesheet.replace("{{" + token + "}}", value)
        return stylesheet

    def apply(
        self,
        app: QApplication,
        mode: ThemeMode | None = None,
        accent_primary: str | None = None,
        accent_hover: str | None = None,
        card_radius: str = "12px",
        control_radius: str = "8px",
        *,
        force: bool = False,
    ) -> bool:
        """Apply theme. Returns True if stylesheet was set (or already current).

        Skips identical stylesheets; defers while a modal dialog is up.
        Repeated app.setStyleSheet() while InvoiceDialog (drop-shadow cards + tables)
        is open was measured to escalate from ~200ms to 15s+ and freeze the GUI
        thread (Windows Not Responding) with no Python traceback.
        """
        if mode is not None:
            self._mode = mode

        kwargs = {
            "accent_primary": accent_primary,
            "accent_hover": accent_hover,
            "card_radius": card_radius,
            "control_radius": control_radius,
        }

        # Never re-polish the entire widget tree under an active modal dialog.
        modal = app.activeModalWidget() if app is not None else None
        if not force and modal is not None and modal.isVisible():
            self._deferred_kwargs = dict(kwargs)
            self._deferred_kwargs["mode"] = self._mode
            if not self._defer_scheduled:
                self._defer_scheduled = True
                from PySide6.QtCore import QTimer

                QTimer.singleShot(250, lambda: self._flush_deferred(app))
                logger.info(
                    "Theme.qss deferred — modal %s open.",
                    modal.objectName() or modal.windowTitle() or type(modal).__name__,
                )
            return False

        apply_fonts(app)
        stylesheet = self.build_stylesheet(self._mode, **kwargs)
        if (
            not force
            and stylesheet == self._last_stylesheet
            and app.styleSheet() == stylesheet
        ):
            logger.debug("Theme.qss unchanged (%s) — skip setStyleSheet.", self._mode.value)
            return True

        app.setStyleSheet(stylesheet)
        self._last_stylesheet = stylesheet
        logger.info("Theme.qss naložen (%s).", self._mode.value)
        return True

    def _flush_deferred(self, app: QApplication | None) -> None:
        self._defer_scheduled = False
        if app is None:
            app = QApplication.instance()
        if app is None:
            return
        modal = app.activeModalWidget()
        if modal is not None and modal.isVisible():
            # Still blocked — try again shortly (single chain, not a storm).
            self._defer_scheduled = True
            from PySide6.QtCore import QTimer

            QTimer.singleShot(250, lambda: self._flush_deferred(app))
            return
        self._deferred_kwargs = None
        # Full appearance path (fonts + titlebar + icons), not stylesheet alone.
        from app.modules.settings.settings_controller import SettingsController

        SettingsController().apply_appearance(app)

    def set_mode(self, app: QApplication, mode: ThemeMode) -> None:
        """Pripravljeno za prihodnji preklop Light / Dark Theme."""
        self.apply(app, mode)


theme_manager = ThemeManager(ThemeMode.LIGHT)
