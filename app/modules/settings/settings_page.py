from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QMessageBox,
    QScrollArea,
    QWidget,
)

from app.core.constants import BACKUP_DIR
from app.core.permissions import set_identity
from app.core.session import session
from app.core.ui.notify import toast
from app.modules.settings.settings_controller import SettingsController
from app.widgets.settings.about_card import AboutCard
from app.widgets.settings.appearance_card import AppearanceCard
from app.widgets.settings.backup_card import BackupCard
from app.widgets.settings.fresh_zone_card import FreshZoneCard
from app.widgets.settings.numbering_card import NumberingCard
from app.widgets.settings.pdf_card import PdfCard
from app.widgets.settings.security_card import SecurityCard
from app.widgets.settings.travel_settings_card import TravelSettingsCard
from app.widgets.settings.users_card import UsersCard


class SettingsPage(QWidget):
    save_settings = Signal()
    reset_settings = Signal()
    theme_changed = Signal(str)
    backup_requested = Signal()
    restore_requested = Signal()
    logo_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("SettingsPage")
        self.controller = SettingsController()

        outer = QGridLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("SettingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._canvas = QWidget()
        self._canvas.setObjectName("SettingsCanvas")
        self._grid = QGridLayout(self._canvas)
        self._grid.setContentsMargins(12, 12, 12, 12)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(12)

        self.numbering_card = NumberingCard()
        self.appearance_card = AppearanceCard()
        self.pdf_card = PdfCard()
        self.backup_card = BackupCard()
        self.security_card = SecurityCard()
        self.users_card = UsersCard()
        self.fresh_zone_card = FreshZoneCard()
        self.about_card = AboutCard()
        self.travel_card = TravelSettingsCard()

        scroll.setWidget(self._canvas)
        outer.addWidget(scroll)

        self.appearance_card.theme_changed.connect(self._on_theme)
        self.appearance_card.changed.connect(self._apply_appearance)
        self.backup_card.backup_requested.connect(self._backup)
        self.backup_card.restore_requested.connect(self._restore)
        self.backup_card.export_requested.connect(self._export_settings)
        self.backup_card.import_requested.connect(self._import_settings)
        self.backup_card.folder_requested.connect(self._open_backup_folder)
        self.security_card.password_clicked.connect(self._change_password)
        self.security_card.logout_clicked.connect(self._logout)
        self.fresh_zone_card.fresh_completed.connect(self._on_fresh_completed)

        self._breakpoint = None
        self._place_widgets(1400)
        self.refresh()
        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.settings")
        # Theme is applied at process startup (before MainWindow). Do NOT re-apply
        # here — that made opening Nastavitve the first moment DARK appeared.

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place_widgets(self.width())

    def _place_widgets(self, width: int) -> None:
        mode = "wide" if width >= 980 else "narrow"
        if mode == self._breakpoint:
            return
        self._breakpoint = mode

        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().setParent(self._canvas)

        if mode == "wide":
            # Company identity has its own dedicated module. Settings contains
            # application behaviour only, avoiding two editable sources.
            self._grid.addWidget(self.pdf_card, 0, 0)
            self._grid.addWidget(self.numbering_card, 0, 1)
            self._grid.addWidget(self.appearance_card, 1, 0)
            self._grid.addWidget(self.travel_card, 1, 1)
            self._grid.addWidget(self.security_card, 2, 0, 1, 2)
            self._grid.addWidget(self.users_card, 3, 0, 1, 2)
            self._grid.addWidget(self.backup_card, 4, 0, 1, 2)
            self._grid.addWidget(self.about_card, 5, 0, 1, 2)
            self._grid.addWidget(self.fresh_zone_card, 6, 0, 1, 2)
            self._grid.setColumnStretch(0, 1)
            self._grid.setColumnStretch(1, 1)
        else:
            self._grid.addWidget(self.pdf_card, 0, 0)
            self._grid.addWidget(self.numbering_card, 1, 0)
            self._grid.addWidget(self.appearance_card, 2, 0)
            self._grid.addWidget(self.travel_card, 3, 0)
            self._grid.addWidget(self.security_card, 4, 0)
            self._grid.addWidget(self.users_card, 5, 0)
            self._grid.addWidget(self.backup_card, 6, 0)
            self._grid.addWidget(self.about_card, 7, 0)
            self._grid.addWidget(self.fresh_zone_card, 8, 0)
            self._grid.setColumnStretch(0, 1)
            self._grid.setColumnStretch(1, 0)

    def refresh(self):
        bundle = self.controller.load_bundle()
        extras = bundle["extras"]
        self.numbering_card.set_values(extras.get("numbering", {}))
        self.appearance_card.set_values(extras.get("appearance", {}))
        self.pdf_card.set_values(extras.get("pdf", {}))
        self.pdf_card.set_excel(extras.get("excel", {}))
        self.travel_card.set_values(extras.get("travel_orders", {}))
        self.security_card.set_values(extras)
        # Re-evaluate RBAC-gated cards from current effective permissions (no restart).
        self.users_card.refresh()
        self.fresh_zone_card.refresh()
        self.about_card.set_values(self.controller.about())

    def extras(self) -> dict:
        return {
            "numbering": self.numbering_card.values(),
            "appearance": self.appearance_card.values(),
            "pdf": self.pdf_card.values(),
            "excel": self.pdf_card.excel_values(),
            "travel_orders": self.travel_card.values(),
            **self.security_card.values(),
        }

    def _save(self):
        from app.core.permissions import can, current_role

        extras = self.extras()
        requested_role = self.security_card.role.currentText()
        if requested_role != current_role() and not can("users"):
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self,
                "Vloga",
                "Sprememba vloge zahteva dovoljenje Administratorja.",
            )
            extras["role"] = current_role()
            self.security_card.role.setCurrentText(current_role())
        appearance_before = dict(getattr(self, "_applied_appearance", {}) or {})
        self.controller.save_extras(extras)
        if can("users"):
            set_identity(role=requested_role)
        timeout_sec = max(5, int(self.security_card.timeout.value())) * 60
        session.timeout_sec = timeout_sec
        try:
            from app.core.idle_guard import get_idle_guard

            guard = get_idle_guard()
            if guard is not None:
                guard.set_timeout_sec(timeout_sec)
        except Exception:
            pass
        sidebar = getattr(self.window(), "sidebar", None)
        if sidebar is not None and hasattr(sidebar, "apply_role"):
            sidebar.apply_role()
        # Re-apply theme only when appearance actually changed — full
        # setStyleSheet on every company save was a freeze amplifier.
        if self.appearance_card.values() != appearance_before:
            self._apply_appearance()
        self.save_settings.emit()
        toast(self, "Nastavitve so shranjene.")

    def _reset(self):
        self.refresh()
        self.reset_settings.emit()

    def _on_theme(self, theme: str):
        # AppearanceCard._emit_theme also emits changed → _apply_appearance.
        # Do not apply twice (double setStyleSheet freezes complex dialogs).
        self.theme_changed.emit(theme)

    def _apply_appearance(self):
        extras = self.controller.load_extras()
        appearance = self.appearance_card.values()
        extras["appearance"] = appearance
        self.controller.save_extras(extras)
        if appearance == getattr(self, "_applied_appearance", None):
            return
        app = QApplication.instance()
        if app is not None:
            self.controller.apply_appearance(app)
            self._applied_appearance = dict(appearance)

    def _backup(self):
        self.backup_requested.emit()
        try:
            self.controller.backup_database()
            toast(self, "Varnostna kopija uspešna")
        except Exception as exc:
            from app.core.errors import handle_error

            handle_error(exc, context="backup", parent=self)

    def _restore(self):
        self.restore_requested.emit()
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Restore Database",
            str(BACKUP_DIR),
            "SQLite (*.db)",
        )
        if not path:
            return
        try:
            self.controller.restore_database(Path(path))
            QMessageBox.information(
                self,
                "Restore",
                "Baza je obnovljena. Ponovno zaženite aplikacijo.",
            )
        except Exception as exc:
            from app.core.errors import handle_error

            handle_error(exc, context="restore", parent=self)

    def _export_settings(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Settings",
            str(BACKUP_DIR / "settings.json"),
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            self.controller.export_settings(Path(path))
            toast(self, "Nastavitve so izvožene.")
        except Exception as exc:
            from app.core.errors import handle_error

            handle_error(exc, context="settings_export", parent=self)

    def _import_settings(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Settings",
            str(BACKUP_DIR),
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            extras = self.controller.import_settings(Path(path))
            bundle = self.controller.load_bundle()
            self.numbering_card.set_values(extras.get("numbering", {}))
            self.appearance_card.set_values(extras.get("appearance", {}))
            self.pdf_card.set_values(extras.get("pdf", {}))
            self.travel_card.set_values(extras.get("travel_orders", {}))
            self._apply_appearance()
            toast(self, "Nastavitve so uvožene.")
        except Exception as exc:
            from app.core.errors import handle_error

            handle_error(exc, context="settings_import", parent=self)

    def _change_password(self):
        try:
            self.controller.change_password(
                self.security_card.old.text(),
                self.security_card.new.text(),
            )
            self.security_card.old.clear()
            self.security_card.new.clear()
            toast(self, "Geslo je spremenjeno.")
        except Exception as exc:
            QMessageBox.warning(self, "Geslo", str(exc))

    def _logout(self):
        """Terminate the authenticated session and return to the login screen.

        Clears session, disables MainWindow, and requires username + password
        again. Cancel/close on the login dialog exits the application safely.
        """
        from app.core.auth_gate import logout_requires_reauth
        from app.windows.unlock_dialog import UnlockDialog
        from PySide6.QtWidgets import QDialog

        session.logout()
        extras = self.controller.load_extras()
        main = self.window()
        if main is not None:
            main.setEnabled(False)
        try:
            if not logout_requires_reauth(extras):
                # Credentials missing (should not happen after mandatory auth) —
                # exit rather than leaving an authenticated MainWindow open.
                QApplication.quit()
                return
            dlg = UnlockDialog(main)
            if dlg.exec() != QDialog.Accepted:
                QApplication.quit()
                return
        finally:
            if main is not None:
                main.setEnabled(True)
        sidebar = getattr(main, "sidebar", None)
        if sidebar is not None and hasattr(sidebar, "apply_role"):
            sidebar.apply_role()
        toolbar = getattr(main, "toolbar", None)
        stack = getattr(main, "stack", None)
        if toolbar is not None and stack is not None and hasattr(toolbar, "set_context"):
            toolbar.set_context(stack.currentIndex())
        bar = main.statusBar() if main is not None and hasattr(main, "statusBar") else None
        if bar is not None and hasattr(bar, "refresh"):
            bar.refresh()
        # New session may have different users/fresh rights — update without restart.
        if hasattr(self, "refresh"):
            self.refresh()

    def _on_fresh_completed(self, _backup_path) -> None:
        """Fresh reset finished; UI promised process exit after confirmation."""
        QApplication.quit()

    def _open_backup_folder(self):
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(BACKUP_DIR)))
