from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.modules.settings.settings_controller import SettingsController
from app.widgets.cards.enterprise_card import EnterpriseCard

DOCUMENTS = (
    ("invoice", "Računi"),
    ("offer", "Ponudbe"),
    ("order", "Naročila"),
    ("delivery", "Dobavnice"),
)


class NumberingCard(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        card = EnterpriseCard("DashboardCard")
        title = QLabel("Številčenje dokumentov")
        title.setObjectName("DashboardSectionTitle")
        card.body.addWidget(title)

        self.rows = {}
        for key, label in DOCUMENTS:
            self.rows[key] = self._add_document(card, key, label)

        hint = QLabel("Predogled")
        hint.setObjectName("DashboardMuted")
        self.preview = QLabel("RAC-2026-000001")
        self.preview.setObjectName("SettingsPreview")
        card.body.addWidget(hint)
        card.body.addWidget(self.preview)

        layout.addWidget(card)
        self._refresh_preview()

    def _add_document(self, card: EnterpriseCard, key: str, title: str):
        heading = QLabel(title)
        heading.setObjectName("SectionTitle")
        card.body.addWidget(heading)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(8)

        prefix = QLineEdit()
        prefix.setMaxLength(8)
        start = QSpinBox()
        start.setRange(1, 999999)
        start.setValue(1)
        length = QSpinBox()
        length.setRange(3, 8)
        length.setValue(6)
        yearly = QCheckBox("Letni reset")

        form.addRow("Prefix", prefix)
        form.addRow("Začetna številka", start)
        form.addRow("Dolžina številke", length)
        form.addRow("", yearly)
        card.body.addLayout(form)

        for widget in (prefix, start, length, yearly):
            if hasattr(widget, "textChanged"):
                widget.textChanged.connect(self._on_changed)
            elif hasattr(widget, "valueChanged"):
                widget.valueChanged.connect(self._on_changed)
            else:
                widget.toggled.connect(self._on_changed)

        return {
            "prefix": prefix,
            "start": start,
            "length": length,
            "yearly_reset": yearly,
        }

    def values(self) -> dict:
        data = {}
        for key, row in self.rows.items():
            data[key] = {
                "prefix": row["prefix"].text().strip() or key[:3].upper(),
                "start": int(row["start"].value()),
                "length": int(row["length"].value()),
                "yearly_reset": row["yearly_reset"].isChecked(),
            }
        return data

    def set_values(self, numbering: dict) -> None:
        for key, row in self.rows.items():
            values = numbering.get(key, {})
            widgets = (row["prefix"], row["start"], row["length"], row["yearly_reset"])
            for widget in widgets:
                widget.blockSignals(True)
            try:
                row["prefix"].setText(str(values.get("prefix", "")))
                row["start"].setValue(int(values.get("start", 1)))
                row["length"].setValue(int(values.get("length", 6)))
                row["yearly_reset"].setChecked(bool(values.get("yearly_reset", True)))
            finally:
                for widget in widgets:
                    widget.blockSignals(False)
        self._refresh_preview()

    def _on_changed(self, *_args):
        self._refresh_preview()
        self.changed.emit()

    def _refresh_preview(self):
        invoice = self.values()["invoice"]
        self.preview.setText(
            SettingsController().preview_number(
                invoice["prefix"],
                invoice["start"],
                invoice["length"],
            )
        )
