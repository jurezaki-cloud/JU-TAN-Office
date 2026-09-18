import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QMessageBox, QPushButton, QSpinBox, QTextEdit,
    QVBoxLayout, QWidget,
)

from app.database.settings_repository import settings_repository
from app.core.constants import BRAND_ASSET_DIR
from app.services.backup_service import backup_service
from app.widgets.messages import show_error


class Settings(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Nastavitve podjetja")
        title.setStyleSheet("font-size:24px;font-weight:bold;padding:8px;")
        layout.addWidget(title)

        company_box = QGroupBox("Podatki izdajatelja dokumentov")
        form = QFormLayout(company_box)
        self.fields = {}
        for key, label in (
            ("company_name", "Naziv podjetja"), ("address", "Naslov"),
            ("postal_code", "Poštna številka"), ("city", "Kraj"),
            ("country", "Država"), ("tax_number", "Davčna številka"),
            ("registration_number", "Matična številka"), ("iban", "IBAN"),
            ("bank_name", "Banka"), ("email", "E-pošta"),
            ("phone", "Telefon"), ("website", "Spletna stran"),
        ):
            widget = QLineEdit(); self.fields[key] = widget; form.addRow(label + ":", widget)
        self.footer = QTextEdit(); self.footer.setMaximumHeight(70)
        form.addRow("Noga dokumenta:", self.footer)
        self.payment_days = QSpinBox(); self.payment_days.setRange(1, 365)
        form.addRow("Privzeti rok plačila:", self.payment_days)

        self.asset_fields = {}
        for key, label in (
            ("logo_path", "Logotip JU-TAN"),
            ("signature_path", "Podpis"),
            ("stamp_path", "Žig"),
        ):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            value = QLineEdit()
            value.setReadOnly(True)
            value.setPlaceholderText("Ni izbrano")
            choose = QPushButton("Izberi sliko")
            clear = QPushButton("Odstrani")
            choose.clicked.connect(lambda checked=False, k=key: self.choose_asset(k))
            clear.clicked.connect(lambda checked=False, k=key: self.asset_fields[k].clear())
            row_layout.addWidget(value, 1)
            row_layout.addWidget(choose)
            row_layout.addWidget(clear)
            self.asset_fields[key] = value
            form.addRow(label + ":", row)
        self.btn_save = QPushButton("💾 Shrani nastavitve")
        form.addRow("", self.btn_save)
        layout.addWidget(company_box)

        backup_box = QGroupBox("Varnostne kopije")
        backup_layout = QVBoxLayout(backup_box)
        backup_options = QFormLayout()
        self.auto_backup = QCheckBox("Samodejna dnevna varnostna kopija")
        self.retention_days = QSpinBox(); self.retention_days.setRange(1, 3650)
        backup_options.addRow("", self.auto_backup)
        backup_options.addRow("Hramba kopij (dni):", self.retention_days)
        backup_layout.addLayout(backup_options)
        buttons = QHBoxLayout()
        self.btn_backup = QPushButton("➕ Ustvari kopijo")
        self.btn_restore = QPushButton("♻️ Obnovi iz kopije")
        self.btn_refresh = QPushButton("🔄 Osveži seznam")
        for button in (self.btn_backup, self.btn_restore, self.btn_refresh):
            buttons.addWidget(button)
        buttons.addStretch(); backup_layout.addLayout(buttons)
        self.backups = QListWidget(); backup_layout.addWidget(self.backups)
        layout.addWidget(backup_box)

        self.btn_save.clicked.connect(self.save)
        self.btn_backup.clicked.connect(self.create_backup)
        self.btn_restore.clicked.connect(self.restore_backup)
        self.btn_refresh.clicked.connect(self.refresh_backups)
        self.load()

    def load(self):
        try:
            values = settings_repository.get()
            for key, widget in self.fields.items():
                widget.setText(str(values.get(key) or ""))
            self.footer.setPlainText(values.get("invoice_footer") or "")
            for key, widget in self.asset_fields.items():
                widget.setText(values.get(key) or "")
            self.payment_days.setValue(values["payment_terms_days"])
            self.auto_backup.setChecked(bool(values["auto_backup"]))
            self.retention_days.setValue(values["backup_retention_days"])
            self.refresh_backups()
        except Exception as error: show_error(self, error, "Nastavitev ni mogoče naložiti")

    def save(self):
        try:
            values = {key: widget.text() for key, widget in self.fields.items()}
            values.update({
                "invoice_footer": self.footer.toPlainText(),
                "payment_terms_days": self.payment_days.value(),
                "auto_backup": self.auto_backup.isChecked(),
                "backup_retention_days": self.retention_days.value(),
            })
            values.update({key: widget.text() for key, widget in self.asset_fields.items()})
            settings_repository.update(values)
            QMessageBox.information(self, "Nastavitve", "Nastavitve so shranjene.")
        except Exception as error: show_error(self, error, "Nastavitev ni mogoče shraniti")

    def choose_asset(self, key):
        path, _ = QFileDialog.getOpenFileName(
            self, "Izberi grafični element", "",
            "Slike (*.png *.jpg *.jpeg);;Vse datoteke (*)",
        )
        if not path:
            return
        source = Path(path)
        destination = BRAND_ASSET_DIR / f"{key}{source.suffix.lower()}"
        try:
            BRAND_ASSET_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            self.asset_fields[key].setText(str(destination))
        except OSError as error:
            show_error(self, error, "Slike ni mogoče shraniti")

    def refresh_backups(self):
        self.backups.clear()
        for path in backup_service.list_backups():
            self.backups.addItem(str(path))

    def create_backup(self):
        try:
            path = backup_service.create()
            self.refresh_backups()
            QMessageBox.information(self, "Varnostna kopija", f"Kopija je ustvarjena:\n{path}")
        except Exception as error: show_error(self, error, "Kopije ni mogoče ustvariti")

    def restore_backup(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Izberi varnostno kopijo", str(backup_service.backup_dir),
            "SQLite kopije (*.db)",
        )
        if not path: return
        reply = QMessageBox.warning(
            self, "Obnovitev podatkov",
            "Trenutni podatki bodo zamenjani z izbrano kopijo. Nadaljujem?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes: return
        try:
            safety = backup_service.restore(path)
            self.load()
            QMessageBox.information(
                self, "Obnovitev končana",
                f"Podatki so obnovljeni. Pred obnovitvijo je bila ustvarjena kopija:\n{safety}",
            )
        except Exception as error: show_error(self, error, "Podatkov ni mogoče obnoviti")
