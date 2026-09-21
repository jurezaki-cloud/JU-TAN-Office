"""Modern enterprise customer card for document editors."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.widgets.cards.enterprise_card import EnterpriseCard


class _InfoTile(QFrame):
    def __init__(self, caption: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DocumentMetaTile")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        self.caption = QLabel(caption)
        self.caption.setObjectName("DocumentMetaCaption")
        self.value = QLabel("—")
        self.value.setObjectName("DocumentMetaValue")
        self.value.setWordWrap(True)
        self.value.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(self.caption)
        layout.addWidget(self.value)

    def set_value(self, text: str | None) -> None:
        cleaned = (text or "").strip()
        self.value.setText(cleaned if cleaned else "—")


class DocumentCustomerPanel(EnterpriseCard):
    """Customer hierarchy + host slot for document meta fields."""

    def __init__(self, parent=None) -> None:
        super().__init__("DocumentEditorCard", parent)
        self.setObjectName("DocumentCustomerPanel")
        self.body.setContentsMargins(18, 16, 18, 16)
        self.body.setSpacing(14)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(2)

        eyebrow = QLabel("STRANKA")
        eyebrow.setObjectName("DocumentEditorEyebrow")
        title = QLabel("Podatki stranke")
        title.setObjectName("DocumentSectionTitle")
        title_col.addWidget(eyebrow)
        title_col.addWidget(title)

        header.addLayout(title_col, 1)
        self.body.addLayout(header)

        select_row = QVBoxLayout()
        select_row.setContentsMargins(0, 0, 0, 0)
        select_row.setSpacing(6)
        select_label = QLabel("Izberi stranko")
        select_label.setObjectName("FieldLabel")
        self.customer = QComboBox()
        self.customer.setObjectName("DocumentCustomerCombo")
        self.customer.setMinimumHeight(36)
        select_row.addWidget(select_label)
        select_row.addWidget(self.customer)
        self.body.addLayout(select_row)

        hero = QFrame()
        hero.setObjectName("DocumentCustomerHero")
        hero.setAttribute(Qt.WA_StyledBackground, True)
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(14, 12, 14, 12)
        hero_layout.setSpacing(4)

        hero_caption = QLabel("Podjetje")
        hero_caption.setObjectName("DocumentMetaCaption")
        self.lbl_company = QLabel("—")
        self.lbl_company.setObjectName("DocumentCustomerName")
        self.lbl_company.setWordWrap(True)
        self.lbl_contact = QLabel("Kontakt ni na voljo")
        self.lbl_contact.setObjectName("DashboardMuted")
        self.lbl_contact.setWordWrap(True)

        hero_layout.addWidget(hero_caption)
        hero_layout.addWidget(self.lbl_company)
        hero_layout.addWidget(self.lbl_contact)
        self.body.addWidget(hero)

        tiles = QGridLayout()
        tiles.setContentsMargins(0, 0, 0, 0)
        tiles.setHorizontalSpacing(10)
        tiles.setVerticalSpacing(10)
        self.tile_tax = _InfoTile("Davčna št.")
        self.tile_city = _InfoTile("Kraj")
        self.tile_email = _InfoTile("E-pošta")
        self.tile_phone = _InfoTile("Telefon")
        tiles.addWidget(self.tile_tax, 0, 0)
        tiles.addWidget(self.tile_city, 0, 1)
        tiles.addWidget(self.tile_email, 1, 0)
        tiles.addWidget(self.tile_phone, 1, 1)
        self.body.addLayout(tiles)

        meta_title = QLabel("Dokument")
        meta_title.setObjectName("DocumentSectionTitle")
        self.body.addWidget(meta_title)

        self.meta_host = QWidget()
        self.meta_layout = QVBoxLayout(self.meta_host)
        self.meta_layout.setContentsMargins(0, 0, 0, 0)
        self.meta_layout.setSpacing(10)
        self.body.addWidget(self.meta_host)

        notes_title = QLabel("Opombe")
        notes_title.setObjectName("FieldLabel")
        self.body.addWidget(notes_title)
        self.notes_host = QWidget()
        self.notes_layout = QVBoxLayout(self.notes_host)
        self.notes_layout.setContentsMargins(0, 0, 0, 0)
        self.notes_layout.setSpacing(0)
        self.body.addWidget(self.notes_host)

    def set_customer_record(self, row) -> None:
        """Populate hierarchy from customer_repository.get_by_id row."""
        if not row:
            self.lbl_company.setText("—")
            self.lbl_contact.setText("Kontakt ni na voljo")
            self.tile_tax.set_value(None)
            self.tile_city.set_value(None)
            self.tile_email.set_value(None)
            self.tile_phone.set_value(None)
            return

        company = row[1] if len(row) > 1 else ""
        contact = row[2] if len(row) > 2 else ""
        city_parts = []
        if len(row) > 4 and row[4]:
            city_parts.append(str(row[4]))
        if len(row) > 5 and row[5]:
            city_parts.append(str(row[5]))
        country = row[6] if len(row) > 6 else ""
        tax = row[7] if len(row) > 7 else ""
        email = row[8] if len(row) > 8 else ""
        phone = row[9] if len(row) > 9 else ""

        self.lbl_company.setText((company or "").strip() or "—")
        contact_line = (contact or "").strip()
        if country:
            contact_line = f"{contact_line} · {country}" if contact_line else str(country)
        self.lbl_contact.setText(contact_line or "Kontakt ni na voljo")
        self.tile_tax.set_value(tax)
        self.tile_city.set_value(" ".join(city_parts) if city_parts else None)
        self.tile_email.set_value(email)
        self.tile_phone.set_value(phone)
