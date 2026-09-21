from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.database.company_repository import (
    DEFAULT_ACCENT,
    DEFAULT_PRIMARY,
    DEFAULT_TABLE_HEADER,
    company_repository,
)
from app.pdf.pdf_branding import archive_branding_asset, normalize_hex
from app.widgets.cards.enterprise_card import EnterpriseCard


def _da_ne(value: bool) -> str:
    return "DA" if value else "NE"


def _is_da(text: str) -> bool:
    return str(text or "").strip().upper() == "DA"


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

        branding_title = QLabel("Blagovna znamka dokumentov")
        branding_title.setObjectName("SectionTitle")
        card.body.addWidget(branding_title)

        self.logo_preview = QLabel("Logotip ni izbran")
        self.logo_preview.setObjectName("LogoPreview")
        self.logo_preview.setAlignment(Qt.AlignCenter)
        self.logo_preview.setFixedSize(96, 64)
        card.body.addWidget(self.logo_preview)

        self.logo_path = QLineEdit()
        self.logo_path.setReadOnly(True)
        card.body.addLayout(self._file_row("Logotip podjetja", self.logo_path, self._pick_logo))

        self.chk_logo = QCheckBox("Prikaži logotip na dokumentih")
        self.chk_vat = QCheckBox("DDV")
        self.chk_discounts = QCheckBox("Popusti")
        self.chk_notes = QCheckBox("Opombe")

        for box in (self.chk_logo, self.chk_vat, self.chk_discounts, self.chk_notes):
            box.setChecked(True)
            box.toggled.connect(self.changed.emit)
            card.body.addWidget(box)

        self.show_signature = QComboBox()
        self.show_signature.addItems(["DA", "NE"])
        self.show_signature.setCurrentText("DA")
        self.show_stamp = QComboBox()
        self.show_stamp.addItems(["DA", "NE"])
        self.show_stamp.setCurrentText("DA")
        card.body.addLayout(self._da_ne_row("Prikaži podpis na dokumentih", self.show_signature))
        card.body.addLayout(self._da_ne_row("Prikaži žig na dokumentih", self.show_stamp))
        self.show_signature.currentTextChanged.connect(self._persist_signature_stamp)
        self.show_stamp.currentTextChanged.connect(self._persist_signature_stamp)

        self.signature_path = QLineEdit()
        self.signature_path.setReadOnly(True)
        self.stamp_path = QLineEdit()
        self.stamp_path.setReadOnly(True)
        card.body.addLayout(self._file_row("Podpis direktorja", self.signature_path, self._pick_signature))
        card.body.addLayout(self._file_row("Žig", self.stamp_path, self._pick_stamp))

        colors_title = QLabel("Barve dokumentov")
        colors_title.setObjectName("SectionTitle")
        card.body.addWidget(colors_title)

        self.primary_color = QLineEdit(DEFAULT_PRIMARY)
        self.accent_color = QLineEdit(DEFAULT_ACCENT)
        self.table_header_color = QLineEdit(DEFAULT_TABLE_HEADER)
        card.body.addLayout(self._color_row("Primarna (besedilo)", self.primary_color))
        card.body.addLayout(self._color_row("Poudarek (črte / glava)", self.accent_color))
        card.body.addLayout(self._color_row("Ozadje tabel", self.table_header_color))

        footer_caption = QLabel("Noga dokumenta")
        footer_caption.setObjectName("DashboardMuted")
        self.footer = QLineEdit()
        self.footer.setPlaceholderText("Noga dokumenta")
        self.footer.textChanged.connect(lambda *_: self.changed.emit())
        card.body.addWidget(footer_caption)
        card.body.addWidget(self.footer)

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

    def _da_ne_row(self, caption: str, combo: QComboBox):
        wrap = QVBoxLayout()
        wrap.setSpacing(4)
        label = QLabel(caption)
        label.setObjectName("DashboardMuted")
        wrap.addWidget(label)
        wrap.addWidget(combo)
        return wrap

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

    def _color_row(self, caption: str, field: QLineEdit):
        wrap = QVBoxLayout()
        wrap.setSpacing(4)
        label = QLabel(caption)
        label.setObjectName("DashboardMuted")
        wrap.addWidget(label)
        inner = QHBoxLayout()
        inner.setSpacing(8)
        field.setPlaceholderText("#000000")
        field.setMaximumWidth(110)
        field.textChanged.connect(lambda *_: self.changed.emit())
        swatch = QPushButton()
        swatch.setObjectName("SecondaryButton")
        swatch.setFixedSize(36, 36)
        swatch.setCursor(Qt.PointingHandCursor)
        swatch.setToolTip("Izberi barvo")

        def _sync_swatch(_text: str = ""):
            color = QColor(normalize_hex(field.text(), "#000000"))
            swatch.setStyleSheet(
                f"background:{color.name()}; border:1px solid #CBD5E1; border-radius:6px;"
            )

        def _pick():
            current = QColor(normalize_hex(field.text(), DEFAULT_PRIMARY))
            chosen = QColorDialog.getColor(current, self, caption)
            if chosen.isValid():
                field.setText(chosen.name().upper())
                self.changed.emit()

        field.textChanged.connect(_sync_swatch)
        swatch.clicked.connect(_pick)
        _sync_swatch()
        inner.addWidget(field)
        inner.addWidget(swatch)
        inner.addStretch()
        wrap.addLayout(inner)
        return wrap

    def values(self) -> dict:
        return {
            "logo": self.chk_logo.isChecked(),
            "signature": _is_da(self.show_signature.currentText()),
            "stamp": _is_da(self.show_stamp.currentText()),
            "vat": self.chk_vat.isChecked(),
            "discounts": self.chk_discounts.isChecked(),
            "notes": self.chk_notes.isChecked(),
            "folder": self.folder.text().strip(),
            "footer": self.footer.text().strip(),
            "signature_path": self.signature_path.text().strip(),
            "stamp_path": self.stamp_path.text().strip(),
        }

    def branding_values(self) -> dict:
        return {
            "logo": self.logo_path.text().strip(),
            "signature_path": self.signature_path.text().strip(),
            "stamp_path": self.stamp_path.text().strip(),
            "doc_primary_color": normalize_hex(self.primary_color.text(), DEFAULT_PRIMARY),
            "doc_accent_color": normalize_hex(self.accent_color.text(), DEFAULT_ACCENT),
            "doc_table_header_color": normalize_hex(
                self.table_header_color.text(), DEFAULT_TABLE_HEADER
            ),
        }

    def set_values(self, pdf: dict) -> None:
        self.chk_logo.setChecked(bool(pdf.get("logo", True)))
        self.show_signature.blockSignals(True)
        self.show_stamp.blockSignals(True)
        self.show_signature.setCurrentText(_da_ne(bool(pdf.get("signature", True))))
        self.show_stamp.setCurrentText(_da_ne(bool(pdf.get("stamp", True))))
        self.show_signature.blockSignals(False)
        self.show_stamp.blockSignals(False)
        self.chk_vat.setChecked(bool(pdf.get("vat", True)))
        self.chk_discounts.setChecked(bool(pdf.get("discounts", True)))
        self.chk_notes.setChecked(bool(pdf.get("notes", True)))
        self.folder.setText(str(pdf.get("folder", "")))
        self.footer.setText(str(pdf.get("footer", "")))
        # Prefer DB branding; settings.json remains a fallback for older installs.
        branding = company_repository.get_branding()
        self._set_logo(branding.get("logo") or "")
        self.signature_path.setText(
            branding.get("signature_path") or str(pdf.get("signature_path", "") or "")
        )
        self.stamp_path.setText(
            branding.get("stamp_path") or str(pdf.get("stamp_path", "") or "")
        )
        self.primary_color.setText(
            normalize_hex(branding.get("doc_primary_color"), DEFAULT_PRIMARY)
        )
        self.accent_color.setText(
            normalize_hex(branding.get("doc_accent_color"), DEFAULT_ACCENT)
        )
        self.table_header_color.setText(
            normalize_hex(branding.get("doc_table_header_color"), DEFAULT_TABLE_HEADER)
        )

    def save_branding(self) -> None:
        """Persist logo / signature / stamp / colors to the company table."""
        values = self.branding_values()
        company_repository.save_branding(
            logo=values["logo"],
            signature_path=values["signature_path"],
            stamp_path=values["stamp_path"],
            doc_primary_color=values["doc_primary_color"],
            doc_accent_color=values["doc_accent_color"],
            doc_table_header_color=values["doc_table_header_color"],
        )

    def excel_values(self) -> dict:
        return {
            "export_folder": self.excel_export.text().strip(),
            "import_folder": self.excel_import.text().strip(),
        }

    def set_excel(self, excel: dict) -> None:
        self.excel_export.setText(str(excel.get("export_folder", "")))
        self.excel_import.setText(str(excel.get("import_folder", "")))

    def _persist_signature_stamp(self, _text: str = "") -> None:
        """Write signature/stamp flags immediately so PDF matches the visible UI."""
        try:
            from app.modules.settings.settings_controller import SettingsController

            ctrl = SettingsController()
            extras = ctrl.load_extras()
            pdf = dict(extras.get("pdf") or {})
            pdf["signature"] = _is_da(self.show_signature.currentText())
            pdf["stamp"] = _is_da(self.show_stamp.currentText())
            extras["pdf"] = pdf
            ctrl.save_extras(extras)
        except Exception as exc:
            from app.core.logger import logger

            logger.error("PDF signature/stamp persist failed: %s", exc)
        self.changed.emit()

    def _set_logo(self, path: str) -> None:
        self.logo_path.setText(path or "")
        if path and Path(path).exists():
            pixmap = QPixmap(path)
            self.logo_preview.setPixmap(
                pixmap.scaled(96, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self.logo_preview.setText("")
        else:
            # Preview the same bundled fallback that the PDF engine will use.
            # This avoids Settings saying "ni izbran" while the document uses a
            # brand fallback, and makes stale archived paths immediately visible.
            fallback = Path(__file__).resolve().parents[3] / "resources" / "logo.png"
            pixmap = QPixmap(str(fallback)) if fallback.exists() else QPixmap()
            if not pixmap.isNull():
                self.logo_preview.setPixmap(
                    pixmap.scaled(96, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                self.logo_preview.setText("")
            else:
                self.logo_preview.setPixmap(QPixmap())
                self.logo_preview.setText("Logotip ni izbran")

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

    def _pick_logo(self):
        path = self._pick_image_path("Logotip podjetja")
        if path is None:
            return
        archived = archive_branding_asset(path, "logo") if path else ""
        self._set_logo(archived)
        self.changed.emit()

    def _pick_signature(self):
        path = self._pick_image_path("Podpis direktorja")
        if path is None:
            return
        archived = archive_branding_asset(path, "signature") if path else ""
        self.signature_path.setText(archived)
        self.changed.emit()

    def _pick_stamp(self):
        path = self._pick_image_path("Žig")
        if path is None:
            return
        archived = archive_branding_asset(path, "stamp") if path else ""
        self.stamp_path.setText(archived)
        self.changed.emit()

    def _pick_image_path(self, title: str) -> str | None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            "Slike (*.png *.jpg *.jpeg *.webp)",
        )
        if not path:
            return None
        return path
