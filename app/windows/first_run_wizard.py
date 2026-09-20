"""Čarovnik prvega zagona — podatki podjetja + obvezna skrbniška prijava."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
)

from app.core.constants import DATA_DIR
from app.core.passwords import hash_password
from app.core.setup_state import mark_setup_complete
from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.database.company_repository import company_repository
from app.modules.settings.settings_controller import SettingsController
from app.widgets.cards.enterprise_card import EnterpriseCard


class FirstRunWizard(EnterpriseDialog):

    def __init__(self, parent=None) -> None:
        super().__init__(
            parent,
            title="Prvi zagon",
            heading="Nastavitev podjetja",
            size="MEDIUM",
            save_text="Dokončaj",
            cancel_text="Prekliči",
        )
        self._logo = ""
        self.bind_save(self._finish)

        card = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.company = QLineEdit()
        self.address = QLineEdit()
        self.tax = QLineEdit()
        self.admin = QLineEdit()
        self.admin.setText("")
        self.admin.setPlaceholderText("Uporabniško ime")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Min. 10 znakov (obvezno)")
        self.password2 = QLineEdit()
        self.password2.setEchoMode(QLineEdit.Password)
        self.password2.setPlaceholderText("Potrditev gesla")
        self.vat = QDoubleSpinBox()
        self.vat.setRange(0, 100)
        self.vat.setDecimals(2)
        self.vat.setValue(22)
        self.vat_liable = QComboBox()
        self.vat_liable.addItems(["DA", "NE"])
        self.vat_liable.setCurrentText("DA")
        self.currency = QComboBox()
        self.currency.addItems(["EUR", "USD", "CHF", "GBP"])
        self.logo_path = QLineEdit()
        self.logo_path.setReadOnly(True)
        browse = QPushButton("Izberi logotip")
        browse.setObjectName("SecondaryButton")
        browse.clicked.connect(self._pick_logo)
        grid.add("Podjetje", self.company, "Uporabniško ime", self.admin)
        grid.add("Naslov", self.address, "Davčna št.", self.tax)
        grid.add("DDV %", self.vat, "Zavezanec za DDV", self.vat_liable)
        grid.add("Valuta", self.currency)
        grid.add("Geslo", self.password, "Potrditev gesla", self.password2)
        grid.add_full("Logotip podjetja", self.logo_path)
        card.body.addLayout(grid.layout)
        card.body.addWidget(browse, 0, Qt.AlignLeft)
        hint = QLabel(
            "Obvezno: ime podjetja, uporabniško ime in geslo skrbnika. "
            "Podatke podjetja lahko kasneje spremenite v Nastavitvah."
        )
        hint.setObjectName("DashboardMuted")
        hint.setWordWrap(True)
        self.body.addWidget(card)
        self.body.addWidget(hint)

    def _pick_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Logotip", "", "Slike (*.png *.jpg *.jpeg *.bmp)")
        if not path:
            return
        source = Path(path)
        suffix = source.suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".bmp"}:
            return
        from app.core.security import ensure_inside

        # Never overwrite application brand assets (logo.png / logo_light.png).
        target = ensure_inside(DATA_DIR / f"company_logo{suffix}", DATA_DIR)
        target.write_bytes(source.read_bytes())
        self._logo = str(target)
        self.logo_path.setText(str(target))

    def _finish(self) -> None:
        name = self.company.text().strip()
        if not name:
            QMessageBox.warning(self, "Prvi zagon", "Vnesite ime podjetja.")
            return
        username = self.admin.text().strip()
        if not username:
            QMessageBox.warning(self, "Prvi zagon", "Vnesite uporabniško ime.")
            self.admin.setFocus()
            return
        pwd = self.password.text()
        if not pwd:
            QMessageBox.warning(self, "Prvi zagon", "Vnesite geslo.")
            self.password.setFocus()
            return
        if pwd != self.password2.text():
            QMessageBox.warning(self, "Prvi zagon", "Gesli se ne ujemata.")
            self.password2.setFocus()
            return
        try:
            hash_password(pwd)  # validate policy early
        except ValueError as exc:
            QMessageBox.warning(self, "Prvi zagon", str(exc))
            self.password.setFocus()
            return

        tax = self.tax.text().strip()
        if tax:
            from app.core.security import require_vat

            try:
                tax = require_vat(tax)
            except ValueError as exc:
                QMessageBox.warning(self, "Prvi zagon", str(exc))
                return

        from app.core.user_service import create_first_administrator, users_exist

        try:
            if users_exist():
                QMessageBox.warning(self, "Prvi zagon", "Prvi uporabnik že obstaja.")
                return
            create_first_administrator(username, pwd)
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "Prvi zagon", str(exc))
            return

        extras = SettingsController().load_extras()
        # SQLite users are the auth source of truth — do not keep competing hash.
        extras["password_hash"] = ""
        extras["administrator"] = username
        extras["role"] = "Administrator"
        extras["account_enabled"] = True
        extras["legacy_auth_migrated"] = True
        SettingsController().save_extras(extras)

        vat = float(self.vat.value())
        from app.utils.vat import vat_liable_int

        company_repository.save(
            name,
            name,
            self.address.text().strip(),
            "",
            "",
            "Slovenija",
            tax,
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            self._logo,
            "RAC",
            "PON",
            1,
            1,
            vat,
            "",
            vat_liable_int(self.vat_liable.currentText()),
        )
        mark_setup_complete(
            administrator=username,
            currency=self.currency.currentText(),
        )
        self.accept()

    def reject(self) -> None:
        from PySide6.QtWidgets import QDialog

        QDialog.reject(self)
