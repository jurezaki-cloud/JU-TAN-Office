"""Premium totals summary for document editors."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
)

from app.widgets.cards.enterprise_card import EnterpriseCard


class DocumentTotalsPanel(EnterpriseCard):
    """Subtotal / discount / VAT / total + payment information."""

    def __init__(self, parent=None) -> None:
        super().__init__("DocumentEditorCard", parent)
        self.setObjectName("DocumentTotalsPanel")
        self.body.setContentsMargins(18, 14, 18, 14)
        self.body.setSpacing(12)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        eyebrow = QLabel("POVZETEK")
        eyebrow.setObjectName("DocumentEditorEyebrow")
        title = QLabel("Skupaj")
        title.setObjectName("DocumentSectionTitle")
        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(2)
        title_col.addWidget(eyebrow)
        title_col.addWidget(title)
        header.addLayout(title_col, 1)
        self.body.addLayout(header)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 0)

        self.lbl_subtotal_caption = QLabel("Osnova")
        self.lbl_subtotal_caption.setObjectName("DocumentTotalCaption")
        self.lbl_subtotal = QLabel("0.00 €")
        self.lbl_subtotal.setObjectName("DocumentTotalValue")
        self.lbl_subtotal.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.lbl_discount_caption = QLabel("Popust")
        self.lbl_discount_caption.setObjectName("DocumentTotalCaption")
        self.lbl_discount = QLabel("0.00 €")
        self.lbl_discount.setObjectName("DocumentTotalValue")
        self.lbl_discount.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.lbl_vat_caption = QLabel("DDV")
        self.lbl_vat_caption.setObjectName("DocumentTotalCaption")
        self.lbl_vat = QLabel("0.00 €")
        self.lbl_vat.setObjectName("DocumentTotalValue")
        self.lbl_vat.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        grid.addWidget(self.lbl_subtotal_caption, 0, 0)
        grid.addWidget(self.lbl_subtotal, 0, 1)
        grid.addWidget(self.lbl_discount_caption, 1, 0)
        grid.addWidget(self.lbl_discount, 1, 1)
        grid.addWidget(self.lbl_vat_caption, 2, 0)
        grid.addWidget(self.lbl_vat, 2, 1)
        self.body.addLayout(grid)

        divider = QFrame()
        divider.setObjectName("DocumentTotalsDivider")
        divider.setFixedHeight(1)
        divider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.body.addWidget(divider)

        total_row = QHBoxLayout()
        total_row.setContentsMargins(0, 0, 0, 0)
        total_row.setSpacing(12)
        total_caption = QLabel("SKUPAJ")
        total_caption.setObjectName("DocumentGrandTotalCaption")
        self.lbl_total = QLabel("0.00 €")
        self.lbl_total.setObjectName("TotalValue")
        self.lbl_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        total_row.addWidget(total_caption)
        total_row.addStretch(1)
        total_row.addWidget(self.lbl_total)
        self.body.addLayout(total_row)

        payment = QFrame()
        payment.setObjectName("DocumentPaymentInfo")
        payment.setAttribute(Qt.WA_StyledBackground, True)
        payment_layout = QVBoxLayout(payment)
        payment_layout.setContentsMargins(12, 10, 12, 10)
        payment_layout.setSpacing(4)
        pay_caption = QLabel("Plačilne informacije")
        pay_caption.setObjectName("DocumentMetaCaption")
        self.lbl_payment = QLabel("Ni zabeleženih plačil")
        self.lbl_payment.setObjectName("DocumentMetaValue")
        self.lbl_payment.setWordWrap(True)
        payment_layout.addWidget(pay_caption)
        payment_layout.addWidget(self.lbl_payment)
        self.body.addWidget(payment)

        self.lbl_vat_notice = QLabel("")
        self.lbl_vat_notice.setObjectName("DashboardMuted")
        self.lbl_vat_notice.setWordWrap(True)
        self.lbl_vat_notice.hide()
        self.body.addWidget(self.lbl_vat_notice)

    def set_payment_info(self, text: str | None) -> None:
        cleaned = (text or "").strip()
        self.lbl_payment.setText(cleaned if cleaned else "Ni zabeleženih plačil")
