"""Čarovnik prvega zagona — podatki podjetja, brez spremembe CRUD API."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QPushButton,
)

from app.core.constants import DATA_DIR
from app.core.setup_state import mark_setup_complete
from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.database.company_repository import company_repository
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
        self.admin.setText("Administrator")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Min. 10 znakov (priporočeno)")
        self.password2 = QLineEdit()
        self.password2.setEchoMode(QLineEdit.Password)
        self.vat = QDoubleSpinBox()
        self.vat.setRange(0, 100)
        self.vat.setDecimals(2)
        self.vat.setValue(22)
        self.currency = QComboBox()
        self.currency.addItems(["EUR", "USD", "CHF", "GBP"])
        self.logo_path = QLineEdit()
        self.logo_path.setReadOnly(True)
        browse = QPushButton("Izberi logotip")
        browse.setObjectName("SecondaryButton")
        browse.clicked.connect(self._pick_logo)
        grid.add("Podjetje", self.company, "Administrator", self.admin)
        grid.add("Naslov", self.address, "Davčna št.", self.tax)
        grid.add("DDV %", self.vat, "Valuta", self.currency)
        grid.add("Geslo", self.password, "Ponovi geslo", self.password2)
        grid.add_full("Logotip", self.logo_path)
        card.body.addLayout(grid.layout)
        card.body.addWidget(browse, 0, Qt.AlignLeft)
        hint = QLabel("Obvezno je ime podjetja. Podatke lahko kasneje spremenite v Nastavitvah.")
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
        target = ensure_inside(DATA_DIR / f"logo{suffix}", DATA_DIR)
        target.write_bytes(source.read_bytes())
        self._logo = str(target)
        self.logo_path.setText(str(target))

    def _finish(self) -> None:
        name = self.company.text().strip()
        if not name:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Prvi zagon", "Vnesite ime podjetja.")
            return
        tax = self.tax.text().strip()
        if tax:
            from app.core.security import require_vat
            try:
                tax = require_vat(tax)
            except ValueError as exc:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Prvi zagon", str(exc))
                return
        pwd = self.password.text()
        if pwd or self.password2.text():
            if pwd != self.password2.text():
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Prvi zagon", "Gesli se ne ujemata.")
                return
            from app.core.passwords import hash_password
            try:
                hashed = hash_password(pwd)
            except ValueError as exc:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Prvi zagon", str(exc))
                return
            from app.modules.settings.settings_controller import SettingsController
            extras = SettingsController().load_extras()
            extras["password_hash"] = hashed
            extras["administrator"] = self.admin.text().strip() or "Administrator"
            SettingsController().save_extras(extras)
        vat = float(self.vat.value())
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
        )
        mark_setup_complete(
            administrator=self.admin.text().strip() or "Administrator",
            currency=self.currency.currentText(),
        )
        self.accept()

    def reject(self) -> None:
        from PySide6.QtWidgets import QDialog
        QDialog.reject(self)
