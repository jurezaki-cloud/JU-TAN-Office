from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.widgets.cards.enterprise_card import EnterpriseCard


class PdfCard(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = EnterpriseCard("DashboardCard")
        title = QLabel("PDF nastavitve")
        title.setObjectName("DashboardSectionTitle")
        card.body.addWidget(title)

        self.chk_logo = QCheckBox("Logo")
        self.chk_signature = QCheckBox("Podpis")
        self.chk_stamp = QCheckBox("Žig")
        self.chk_vat = QCheckBox("DDV")
        self.chk_discounts = QCheckBox("Popusti")
        self.chk_notes = QCheckBox("Opombe")

        for box in (
            self.chk_logo,
            self.chk_signature,
            self.chk_stamp,
            self.chk_vat,
            self.chk_discounts,
            self.chk_notes,
        ):
            box.setChecked(True)
            box.toggled.connect(self.changed.emit)
            card.body.addWidget(box)

        footer_caption = QLabel("Noga dokumenta")
        footer_caption.setObjectName("DashboardMuted")
        self.footer = QLineEdit()
        self.footer.setPlaceholderText("Noga dokumenta")
        self.footer.textChanged.connect(lambda *_: self.changed.emit())
        card.body.addWidget(footer_caption)
        card.body.addWidget(self.footer)

        self.signature_path = QLineEdit()
        self.signature_path.setReadOnly(True)
        self.stamp_path = QLineEdit()
        self.stamp_path.setReadOnly(True)
        card.body.addLayout(self._file_row("Podpis direktorja", self.signature_path, self._pick_signature))
        card.body.addLayout(self._file_row("Žig", self.stamp_path, self._pick_stamp))

        folder_caption = QLabel("Privzeta mapa")
        folder_caption.setObjectName("DashboardMuted")
        card.body.addWidget(folder_caption)

        folder_row = QHBoxLayout()
        folder_row.setSpacing(8)
        self.folder = QLineEdit()
        self.folder.setReadOnly(True)
        self.btn_folder = QPushButton("Izberi mapo")
        self.btn_folder.setObjectName("SecondaryButton")
        self.btn_folder.setCursor(Qt.PointingHandCursor)
        self.btn_folder.setMinimumHeight(36)
        folder_row.addWidget(self.folder, 1)
        folder_row.addWidget(self.btn_folder)
        card.body.addLayout(folder_row)

        self.excel_export = QLineEdit()
        self.excel_export.setReadOnly(True)
        self.excel_import = QLineEdit()
        self.excel_import.setReadOnly(True)
        card.body.addLayout(self._file_row("Excel izvozna mapa", self.excel_export, self._pick_excel_export))
        card.body.addLayout(self._file_row("Excel uvozna mapa", self.excel_import, self._pick_excel_import))

        layout.addWidget(card)
        self.btn_folder.clicked.connect(self._pick_folder)

    def _file_row(self, caption: str, field: QLineEdit, handler):
        wrap = QVBoxLayout()
        wrap.setSpacing(4)
        label = QLabel(caption)
        label.setObjectName("DashboardMuted")
        wrap.addWidget(label)
        inner = QHBoxLayout()
        inner.setSpacing(8)
        button = QPushButton("Izberi")
        button.setObjectName("SecondaryButton")
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(36)
        button.clicked.connect(handler)
        inner.addWidget(field, 1)
        inner.addWidget(button)
        wrap.addLayout(inner)
        return wrap

    def values(self) -> dict:
        return {
            "logo": self.chk_logo.isChecked(),
            "signature": self.chk_signature.isChecked(),
            "stamp": self.chk_stamp.isChecked(),
            "vat": self.chk_vat.isChecked(),
            "discounts": self.chk_discounts.isChecked(),
            "notes": self.chk_notes.isChecked(),
            "folder": self.folder.text().strip(),
            "footer": self.footer.text().strip(),
            "signature_path": self.signature_path.text().strip(),
            "stamp_path": self.stamp_path.text().strip(),
        }

    def set_values(self, pdf: dict) -> None:
        self.chk_logo.setChecked(bool(pdf.get("logo", True)))
        self.chk_signature.setChecked(bool(pdf.get("signature", True)))
        self.chk_stamp.setChecked(bool(pdf.get("stamp", True)))
        self.chk_vat.setChecked(bool(pdf.get("vat", True)))
        self.chk_discounts.setChecked(bool(pdf.get("discounts", True)))
        self.chk_notes.setChecked(bool(pdf.get("notes", True)))
        self.folder.setText(str(pdf.get("folder", "")))
        self.footer.setText(str(pdf.get("footer", "")))
        self.signature_path.setText(str(pdf.get("signature_path", "")))
        self.stamp_path.setText(str(pdf.get("stamp_path", "")))

    def excel_values(self) -> dict:
        return {
            "export_folder": self.excel_export.text().strip(),
            "import_folder": self.excel_import.text().strip(),
        }

    def set_excel(self, excel: dict) -> None:
        self.excel_export.setText(str(excel.get("export_folder", "")))
        self.excel_import.setText(str(excel.get("import_folder", "")))

    def _pick_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Privzeta mapa za PDF")
        if path:
            self.folder.setText(path)
            self.changed.emit()

    def _pick_excel_export(self):
        path = QFileDialog.getExistingDirectory(self, "Excel izvozna mapa")
        if path:
            self.excel_export.setText(path)
            self.changed.emit()

    def _pick_excel_import(self):
        path = QFileDialog.getExistingDirectory(self, "Excel uvozna mapa")
        if path:
            self.excel_import.setText(path)
            self.changed.emit()

    def _pick_signature(self):
        self._pick_image(self.signature_path, "Podpis direktorja")

    def _pick_stamp(self):
        self._pick_image(self.stamp_path, "Žig")

    def _pick_image(self, field: QLineEdit, title: str):
        path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            "Slike (*.png *.jpg *.jpeg *.webp)",
        )
        if path:
            field.setText(path)
            self.changed.emit()
