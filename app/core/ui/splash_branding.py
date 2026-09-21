"""Professional startup splash pixmap for JU-TAN Office."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap

from app.core.constants import APP_CHANNEL, APP_NAME, APP_VERSION, RESOURCE_DIR


def _logo_candidates(dark: bool) -> tuple[Path, ...]:
    primary = "logo.png" if dark else "logo_light.png"
    fallback = "logo_light.png" if dark else "logo.png"
    return (
        RESOURCE_DIR / primary,
        RESOURCE_DIR / fallback,
        RESOURCE_DIR / "app.png",
        RESOURCE_DIR / "app.ico",
    )


def _load_logo(dark: bool, max_height: int = 72) -> QPixmap | None:
    for path in _logo_candidates(dark):
        if not path.exists():
            continue
        pix = QPixmap(str(path))
        if pix.isNull():
            continue
        if pix.height() > max_height:
            pix = pix.scaledToHeight(max_height, Qt.SmoothTransformation)
        return pix
    return None


def build_splash_pixmap(mode_name: str = "light") -> tuple[QPixmap, QColor]:
    """Return branded splash artwork and preferred message foreground color."""
    dark = str(mode_name).lower() == "dark"
    bg = QColor("#0B1220" if dark else "#F4F6F8")
    fg = QColor("#F8FAFC" if dark else "#0F172A")
    muted = QColor("#94A3B8" if dark else "#64748B")
    accent = QColor("#38BDF8" if dark else "#0369A1")

    width, height = 520, 280
    canvas = QPixmap(width, height)
    canvas.fill(bg)

    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    # Soft top accent bar
    painter.fillRect(0, 0, width, 4, accent)

    logo = _load_logo(dark)
    y = 48
    if logo is not None:
        x = (width - logo.width()) // 2
        painter.drawPixmap(x, y, logo)
        y += logo.height() + 22
    else:
        y = 72

    title_font = QFont()
    title_font.setFamilies(["Segoe UI", "Arial"])
    title_font.setPointSize(18)
    title_font.setBold(True)
    painter.setFont(title_font)
    painter.setPen(fg)
    painter.drawText(
        24,
        y,
        width - 48,
        36,
        Qt.AlignHCenter | Qt.AlignVCenter,
        "JU-TAN Office",
    )
    y += 40

    edition_font = QFont()
    edition_font.setFamilies(["Segoe UI", "Arial"])
    edition_font.setPointSize(10)
    painter.setFont(edition_font)
    painter.setPen(muted)
    painter.drawText(
        24,
        y,
        width - 48,
        22,
        Qt.AlignHCenter | Qt.AlignVCenter,
        f"{APP_NAME}",
    )
    y += 28

    version_font = QFont(edition_font)
    version_font.setPointSize(9)
    painter.setFont(version_font)
    painter.setPen(accent)
    painter.drawText(
        24,
        y,
        width - 48,
        20,
        Qt.AlignHCenter | Qt.AlignVCenter,
        f"v{APP_VERSION}  ·  {APP_CHANNEL}",
    )

    painter.end()
    return canvas, fg
