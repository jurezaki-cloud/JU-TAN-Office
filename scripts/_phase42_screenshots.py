"""Phase 4.2 visual capture — titles, nav states, empty states."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / ".rc-qa-tmp" / "phase42-polish"
OUT.mkdir(parents=True, exist_ok=True)


def _grab(widget, name: str) -> None:
    pix = widget.grab()
    path = OUT / f"{name}.png"
    pix.save(str(path))
    print(f"saved {path} ({pix.width()}x{pix.height()})")


def main() -> int:
    app = QApplication(sys.argv)
    from app.core import permissions
    from app.core.session import session
    from app.core.ui.app_identity import apply_application_identity
    from app.theme.colors import ThemeMode
    from app.theme.theme import theme_manager
    from app.windows.main_window import MainWindow

    apply_application_identity(app)
    session.login("Administrator", "Administrator")
    permissions.set_identity(
        user="Administrator", role="Administrator", authenticated=True
    )
    theme_manager.apply(app, ThemeMode.LIGHT)

    win = MainWindow()
    win.resize(1440, 900)
    win.show()
    app.processEvents()

    # Active nav + toolbar title (no duplicate page H1)
    win.change_page(1)
    app.processEvents()
    _grab(win, "invoices-shell")
    _grab(win.toolbar, "toolbar-invoices")
    _grab(win.sidebar, "sidebar-active-invoices")

    # Keyboard focus rail
    btn = win.sidebar.buttons[3]
    btn.setFocus(Qt.TabFocusReason)
    app.processEvents()
    _grab(win.sidebar, "sidebar-focus-offers")

    # Empty-state pages
    for idx, name in (
        (1, "invoices-empty"),
        (3, "offers-empty"),
        (9, "orders-empty"),
        (2, "customers-empty"),
    ):
        win.change_page(idx)
        app.processEvents()
        page = win.stack.widget(idx)
        inner = page.ensure() if hasattr(page, "ensure") else page
        if hasattr(inner, "empty_state"):
            inner.content_stack.setCurrentWidget(inner.empty_state)
            app.processEvents()
        _grab(win, name)

    # Collapsed sidebar selection
    win.change_page(1)
    win.sidebar.set_collapsed(True)
    app.processEvents()
    _grab(win.sidebar, "sidebar-collapsed-active")
    win.sidebar.set_collapsed(False)
    app.processEvents()

    # Settings description-only header
    win.change_page(8)
    app.processEvents()
    _grab(win, "settings-no-duplicate-title")

    win.close()
    print(f"OUT={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
