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
from app.modules.settings.settings_controller import PLACEHOLDER, SettingsController
from app.widgets.settings.about_card import AboutCard
from app.widgets.settings.appearance_card import AppearanceCard
from app.widgets.settings.backup_card import BackupCard
from app.widgets.settings.company_card import CompanyCard
from app.widgets.settings.numbering_card import NumberingCard
from app.widgets.settings.security_card import SecurityCard
from app.widgets.settings.pdf_card import PdfCard


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
        self._grid.setContentsMargins(20, 20, 20, 20)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(12)

        self.company_card = CompanyCard()
        self.numbering_card = NumberingCard()
        self.appearance_card = AppearanceCard()
        self.pdf_card = PdfCard()
        self.backup_card = BackupCard()
        self.security_card = SecurityCard()
        self.about_card = AboutCard()

        scroll.setWidget(self._canvas)
        outer.addWidget(scroll)

        self.company_card.save_clicked.connect(self._save)
        self.company_card.reset_clicked.connect(self._reset)
        self.company_card.logo_changed.connect(self.logo_changed.emit)
        self.appearance_card.theme_changed.connect(self._on_theme)
        self.appearance_card.changed.connect(self._apply_appearance)
        self.backup_card.backup_requested.connect(self._backup)
        self.backup_card.restore_requested.connect(self._restore)
        self.backup_card.export_requested.connect(self._export_settings)
        self.backup_card.import_requested.connect(self._import_settings)
        self.backup_card.folder_requested.connect(self._open_backup_folder)
        self.security_card.password_clicked.connect(self._change_password)
        self.security_card.logout_clicked.connect(self._logout)

        self._breakpoint = None
        self._place_widgets(1400)
        self.refresh()
        from app.core.ui.window_state import remember_layout
        remember_layout(self, "page.settings")
        app = QApplication.instance()
        if app is not None:
            self.controller.apply_appearance(app)

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
            self._grid.addWidget(self.company_card, 0, 0, 1, 2)
            self._grid.addWidget(self.numbering_card, 1, 0)
            self._grid.addWidget(self.appearance_card, 1, 1)
            self._grid.addWidget(self.pdf_card, 2, 0)
            self._grid.addWidget(self.backup_card, 2, 1)
            self._grid.addWidget(self.security_card, 3, 0, 1, 2)
            self._grid.addWidget(self.about_card, 4, 0, 1, 2)
            self._grid.setColumnStretch(0, 1)
            self._grid.setColumnStretch(1, 1)
        else:
            self._grid.addWidget(self.company_card, 0, 0)
            self._grid.addWidget(self.numbering_card, 1, 0)
            self._grid.addWidget(self.appearance_card, 2, 0)
            self._grid.addWidget(self.pdf_card, 3, 0)
            self._grid.addWidget(self.backup_card, 4, 0)
            self._grid.addWidget(self.security_card, 5, 0)
            self._grid.addWidget(self.about_card, 6, 0)
            self._grid.setColumnStretch(0, 1)
            self._grid.setColumnStretch(1, 0)

    def refresh(self):
        bundle = self.controller.load_bundle()
        extras = bundle["extras"]
        self.company_card.set_values(bundle["company"], extras.get("swift", ""))
        self.numbering_card.set_values(extras.get("numbering", {}))
        self.appearance_card.set_values(extras.get("appearance", {}))
        self.pdf_card.set_values(extras.get("pdf", {}))
        self.pdf_card.set_excel(extras.get("excel", {}))
        self.security_card.set_values(extras)
        self.about_card.set_values(self.controller.about())

    def extras(self) -> dict:
        return {
            "swift": self.company_card.values().get("swift", ""),
            "numbering": self.numbering_card.values(),
            "appearance": self.appearance_card.values(),
            "pdf": self.pdf_card.values(),
            "excel": self.pdf_card.excel_values(),
            **self.security_card.values(),
        }

    def _save(self):
        self.controller.save_bundle(self.company_card.values(), self.extras())
        set_identity(role=self.security_card.role.currentText())
        session.timeout_sec = int(self.security_card.timeout.value()) * 60
        self._apply_appearance()
        self.save_settings.emit()
        toast(self, "Nastavitve so shranjene.")

    def _reset(self):
        self.refresh()
        self.reset_settings.emit()

    def _on_theme(self, theme: str):
        self.theme_changed.emit(theme)
        self._apply_appearance()

    def _apply_appearance(self):
        extras = self.controller.load_extras()
        extras["appearance"] = self.appearance_card.values()
        self.controller.save_extras(extras)
        app = QApplication.instance()
        if app is not None:
            self.controller.apply_appearance(app)

    def _backup(self):
        self.backup_requested.emit()
        try:
            target = self.controller.backup_database()
            toast(self, "Varnostna kopija uspešna")
        except Exception:
            QMessageBox.information(self, "Backup", PLACEHOLDER)

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
        except Exception:
            QMessageBox.information(self, "Restore", PLACEHOLDER)

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
        except Exception:
            QMessageBox.information(self, "Settings", PLACEHOLDER)

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
            self.company_card.set_values(bundle["company"], extras.get("swift", ""))
            self.numbering_card.set_values(extras.get("numbering", {}))
            self.appearance_card.set_values(extras.get("appearance", {}))
            self.pdf_card.set_values(extras.get("pdf", {}))
            self._apply_appearance()
            toast(self, "Nastavitve so uvožene.")
        except Exception:
            QMessageBox.information(self, "Settings", PLACEHOLDER)

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
        session.logout()
        toast(self, "Odjavljeni ste. Ob naslednjem zagonu bo potrebna prijava.")

    def _open_backup_folder(self):
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(BACKUP_DIR)))
