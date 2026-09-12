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

    @property
    def mode(self) -> ThemeMode:
        return self._mode

    def load_qss_template(self) -> str:
        if self._template is None:
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
    ) -> None:
        if mode is not None:
            self._mode = mode

        apply_fonts(app)
        stylesheet = self.build_stylesheet(
            self._mode,
            accent_primary=accent_primary,
            accent_hover=accent_hover,
            card_radius=card_radius,
            control_radius=control_radius,
        )
        app.setStyleSheet(stylesheet)
        logger.info("Theme.qss naložen (%s).", self._mode.value)

    def set_mode(self, app: QApplication, mode: ThemeMode) -> None:
        """Pripravljeno za prihodnji preklop Light / Dark Theme."""
        self.apply(app, mode)


theme_manager = ThemeManager(ThemeMode.LIGHT)
