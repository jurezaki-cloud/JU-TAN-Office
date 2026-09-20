"""First-run JU-TAN Office license activation dialog."""
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QMessageBox, QVBoxLayout

from app.services.licensing_service import LicenseError, activate


class LicenseActivationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aktivacija JU-TAN Office")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        title = QLabel("<b>Aktivacija licence</b>")
        info = QLabel("Vnesite licenčni ključ JU-TAN Office. Za prvo aktivacijo je potrebna internetna povezava.")
        info.setWordWrap(True)
        self.key = QLineEdit()
        self.key.setPlaceholderText("JU-TAN-XXXX-XXXX")
        self.key.returnPressed.connect(self._activate)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Aktiviraj")
        buttons.accepted.connect(self._activate)
        buttons.rejected.connect(self.reject)

        layout.addWidget(title)
        layout.addWidget(info)
        layout.addWidget(self.key)
        layout.addWidget(buttons)

    def _activate(self):
        key = self.key.text().strip()
        if not key:
            QMessageBox.warning(self, "Licenca", "Vnesite licenčni ključ.")
            return
        try:
            activate(key)
        except LicenseError as exc:
            QMessageBox.critical(self, "Aktivacija ni uspela", str(exc))
            return
        QMessageBox.information(self, "Licenca", "JU-TAN Office je uspešno aktiviran.")
        self.accept()
