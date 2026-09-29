from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTextEdit, QVBoxLayout,
)

from app.services.mail_center import mail_center


class MailCenterDialog(QDialog):
    def __init__(self, parent=None, *, recipient="", subject="", body="", attachment=""):
        super().__init__(parent)
        self.setWindowTitle("JU-TAN Mail Center")
        self.setMinimumSize(640, 520)
        self.attachment = str(attachment or "")
        layout = QVBoxLayout(self)
        title = QLabel("Pošlji dokument po e-pošti")
        title.setObjectName("DashboardSectionTitle")
        layout.addWidget(title)
        form = QFormLayout()
        self.to = QLineEdit(recipient)
        self.subject = QLineEdit(subject)
        self.body = QTextEdit(body)
        form.addRow("Prejemnik", self.to)
        form.addRow("Zadeva", self.subject)
        form.addRow("Sporočilo", self.body)
        attached = QLabel(Path(self.attachment).name if self.attachment else "Brez priponke")
        attached.setObjectName("DashboardMuted")
        attached.setToolTip(self.attachment)
        form.addRow("PDF priponka", attached)
        layout.addLayout(form)
        self.btn_test = QPushButton("Preveri SMTP povezavo")
        self.btn_test.setObjectName("SecondaryButton")
        self.btn_test.clicked.connect(self._test)
        layout.addWidget(self.btn_test, 0, Qt.AlignLeft)
        buttons = QDialogButtonBox()
        self.send_button = buttons.addButton("Pošlji", QDialogButtonBox.AcceptRole)
        buttons.addButton("Prekliči", QDialogButtonBox.RejectRole)
        self.send_button.setObjectName("PrimaryButton")
        buttons.accepted.connect(self._send)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _test(self):
        try:
            mail_center.test_connection()
            QMessageBox.information(self, "Mail Center", "SMTP povezava je uspešna.")
        except Exception as exc:
            QMessageBox.warning(self, "Mail Center", f"Povezava ni uspela:\n{exc}")

    def _send(self):
        self.send_button.setEnabled(False)
        try:
            mail_center.send(
                to=self.to.text(),
                subject=self.subject.text(),
                body=self.body.toPlainText(),
                attachments=[self.attachment] if self.attachment else [],
            )
        except Exception as exc:
            self.send_button.setEnabled(True)
            QMessageBox.warning(self, "Mail Center", f"Pošiljanje ni uspelo:\n{exc}")
            return
        QMessageBox.information(self, "Mail Center", "E-pošta je bila uspešno poslana.")
        self.accept()
