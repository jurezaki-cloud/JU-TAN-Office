"""Dangerous zone — Fresh install reset UI."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.fresh_reset import FRESH_CONFIRM_TEXT, FreshResetError, fresh_reset_service
from app.core.permissions import can
from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.widgets.cards.enterprise_card import EnterpriseCard


class FreshZoneCard(QWidget):
    """Administrator-only destructive Fresh reset entry point."""

    fresh_completed = Signal(object)  # backup Path

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = EnterpriseCard("DashboardCard")
        card.setObjectName("DangerZoneCard")

        title = QLabel("NEVARNO OBMOČJE")
        title.setObjectName("DangerZoneTitle")
        card.body.addWidget(title)

        warn = QLabel(
            "Ponastavitev na novo namestitev bo odstranila vse poslovne podatke, "
            "uporabnike in nastavitve podjetja.\n\n"
            "Pred izbrisom bo samodejno ustvarjena varnostna kopija."
        )
        warn.setObjectName("DangerZoneText")
        warn.setWordWrap(True)
        card.body.addWidget(warn)

        self.btn_fresh = QPushButton("PONASTAVITEV NA NOVO NAMESTITEV (FRESH)")
        self.btn_fresh.setObjectName("DangerButton")
        self.btn_fresh.clicked.connect(self._open_wizard)
        card.body.addWidget(self.btn_fresh)
        layout.addWidget(card)
        # Visual shell only — RBAC refresh runs via SettingsPage.refresh().
        allowed = can("fresh")
        self.setVisible(allowed)
        self.btn_fresh.setEnabled(allowed)

    def refresh(self) -> None:
        allowed = can("fresh")
        self.setVisible(allowed)
        self.btn_fresh.setEnabled(allowed)

    def _open_wizard(self) -> None:
        if not can("fresh"):
            QMessageBox.warning(self, "FRESH", "Dejanje ni dovoljeno.")
            return
        dlg = FreshResetDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.backup_path is not None:
            self.fresh_completed.emit(dlg.backup_path)


class FreshResetDialog(EnterpriseDialog):
    """Multi-stage confirmation: warning → admin password → FRESH text."""

    def __init__(self, parent=None):
        super().__init__(
            parent,
            title="Ponastavitev FRESH",
            heading="Potrditev uničenja podatkov",
            size="MEDIUM",
            save_text="IZBRIŠI PODATKE IN ZAČNI ZNOVA",
            cancel_text="Prekliči",
        )
        self.backup_path = None
        self.setObjectName("FreshResetDialog")

        warn = QLabel(
            "To dejanje je nepovratno za delujočo namestitev.\n"
            "Samodejna varnostna kopija bo ustvarjena PRED izbrisom.\n"
            "Če varnostna kopija spodleti, se podatki NE izbrišejo."
        )
        warn.setObjectName("DangerZoneText")
        warn.setWordWrap(True)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Trenutno skrbniško geslo")
        self.password.setMinimumHeight(36)

        self.confirm = QLineEdit()
        self.confirm.setPlaceholderText("Vnesite FRESH")
        self.confirm.setMinimumHeight(36)

        form = QFormLayout()
        form.addRow("Geslo administratorja", self.password)
        form.addRow("Potrditev", self.confirm)

        self.body.addWidget(warn)
        self.body.addLayout(form)
        self.btn_save.setObjectName("DangerButton")
        self.btn_save.setEnabled(False)
        self.confirm.textChanged.connect(self._update_enabled)
        self.password.textChanged.connect(self._update_enabled)
        self.bind_save(self._execute)

    def _update_enabled(self) -> None:
        ok = (
            bool(self.password.text())
            and self.confirm.text().strip() == FRESH_CONFIRM_TEXT
        )
        self.btn_save.setEnabled(ok)

    def _execute(self) -> None:
        reply = QMessageBox.warning(
            self,
            "Zadnja potrditev",
            "Ali ste prepričani? Vsi poslovni podatki bodo izbrisani.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            fresh_reset_service.assert_authorized()
            path = fresh_reset_service.execute(
                password=self.password.text(),
                confirm_text=self.confirm.text(),
            )
        except FreshResetError as exc:
            QMessageBox.critical(self, "FRESH", str(exc))
            return
        except PermissionError as exc:
            QMessageBox.warning(self, "FRESH", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(
                self,
                "FRESH",
                f"Nepričakovana napaka. Podatki morda niso bili izbrisani.\n{exc}",
            )
            return
        self.backup_path = path
        QMessageBox.information(
            self,
            "FRESH",
            "Ponastavitev je končana.\n"
            f"Varnostna kopija: {path}\n\n"
            "Aplikacija se bo zaprla. Ob naslednjem zagonu sledi prvi zagon.",
        )
        self.accept()
