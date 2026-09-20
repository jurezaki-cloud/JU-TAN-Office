from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QVBoxLayout,
)

from app.licensing.client import LicenseServiceError


class ActivationDialog(QDialog):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.setWindowTitle("Aktivacija JU-TAN Office")
        self.setMinimumWidth(520)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        layout = QVBoxLayout(self)
        title = QLabel("Aktivacija programa")
        title.setStyleSheet("font-size:24px;font-weight:700;")
        description = QLabel(
            "Vnesite podatke licence. Program pošlje samo tehnične podatke, "
            "potrebne za preverjanje licence; poslovni dokumenti se ne pošiljajo."
        )
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        form = QFormLayout()
        self.company = QLineEdit()
        self.email = QLineEdit()
        self.key = QLineEdit()
        self.key.setPlaceholderText("JUTAN-XXXX-XXXX-XXXX")
        form.addRow("Podjetje:", self.company)
        form.addRow("E-pošta:", self.email)
        form.addRow("Licenčni ključ:", self.key)
        layout.addLayout(form)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.activate_button = QPushButton("Aktiviraj")
        self.activate_button.setDefault(True)
        buttons.addButton(self.activate_button, QDialogButtonBox.AcceptRole)
        layout.addWidget(buttons)
        self.activate_button.clicked.connect(self.activate)
        buttons.rejected.connect(self.reject)

    def activate(self):
        if not all((self.company.text().strip(), self.email.text().strip(), self.key.text().strip())):
            QMessageBox.warning(self, "Aktivacija", "Izpolnite vsa polja.")
            return
        self.activate_button.setEnabled(False)
        self.status.setText("Preverjanje licence …")
        try:
            state = self.client.activate(
                self.key.text(), self.company.text(), self.email.text()
            )
        except LicenseServiceError as error:
            self.status.setText(str(error))
            self.activate_button.setEnabled(True)
            return
        self.status.setText(state.message)
        self.accept()


def ensure_licensed(client, parent=None):
    state = client.local_status()
    if state.permits_use:
        return client.refresh()
    dialog = ActivationDialog(client, parent)
    if dialog.exec() != QDialog.Accepted:
        return state
    return client.local_status()
