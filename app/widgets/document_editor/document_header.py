"""Premium document editor header — number, status, customer, actions."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.ui.icons import apply_button_icon


def _repolish(widget: QWidget) -> None:
    style = widget.style()
    if style is None:
        return
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


class DocumentEditorHeader(QFrame):
    """Top chrome for document editors (Save / Export PDF / More)."""

    save_clicked = Signal()
    export_pdf_clicked = Signal()
    more_action = Signal(str)

    def __init__(
        self,
        *,
        doc_kind: str = "Račun",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("DocumentEditorHeader")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        identity = QVBoxLayout()
        identity.setContentsMargins(0, 0, 0, 0)
        identity.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)

        self.lbl_kind = QLabel(doc_kind.upper())
        self.lbl_kind.setObjectName("DocumentEditorEyebrow")

        self.lbl_status = QLabel("Osnutek")
        self.lbl_status.setObjectName("DocumentStatusBadge")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setProperty("kind", "draft")
        self.lbl_status.setMinimumHeight(26)

        top_row.addWidget(self.lbl_kind, 0, Qt.AlignVCenter)
        top_row.addWidget(self.lbl_status, 0, Qt.AlignVCenter)
        top_row.addStretch(1)

        self.lbl_number = QLabel("—")
        self.lbl_number.setObjectName("DocumentEditorNumber")
        self.lbl_number.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.lbl_customer = QLabel("Stranka ni izbrana")
        self.lbl_customer.setObjectName("DocumentEditorCustomer")
        self.lbl_customer.setWordWrap(True)

        identity.addLayout(top_row)
        identity.addWidget(self.lbl_number)
        identity.addWidget(self.lbl_customer)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(8)

        self.btn_more = QPushButton("Več")
        self.btn_more.setObjectName("GhostButton")
        self.btn_export_pdf = QPushButton("Izvozi PDF")
        self.btn_export_pdf.setObjectName("SecondaryButton")
        self.btn_save = QPushButton("Shrani")
        self.btn_save.setObjectName("PrimaryButton")

        for button in (self.btn_more, self.btn_export_pdf, self.btn_save):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            actions.addWidget(button)

        apply_button_icon(self.btn_save, "save")
        apply_button_icon(self.btn_export_pdf, "pdf")
        apply_button_icon(self.btn_more, "more")

        self._more_menu = QMenu(self)
        self._more_menu.setObjectName("ToolbarOverflowMenu")
        self._more_menu.addAction("Osveži vsote", lambda: self.more_action.emit("refresh_totals"))
        self._more_menu.addAction("Fokus na postavke", lambda: self.more_action.emit("focus_items"))
        self._more_menu.addSeparator()
        self._more_menu.addAction("Zapri", lambda: self.more_action.emit("close"))
        self.btn_more.setMenu(self._more_menu)

        self.btn_save.clicked.connect(self.save_clicked.emit)
        self.btn_export_pdf.clicked.connect(self.export_pdf_clicked.emit)

        root.addLayout(identity, 1)
        root.addLayout(actions, 0)

    def set_document_number(self, number: str) -> None:
        text = (number or "").strip() or "—"
        self.lbl_number.setText(text)

    def set_customer_name(self, name: str | None) -> None:
        text = (name or "").strip()
        self.lbl_customer.setText(text if text else "Stranka ni izbrana")

    def set_status(self, status: str | None, *, kind: str | None = None) -> None:
        label = (status or "").strip() or "Osnutek"
        self.lbl_status.setText(label)
        badge_kind = kind or _status_kind(label)
        self.lbl_status.setProperty("kind", badge_kind)
        _repolish(self.lbl_status)

    def set_actions_enabled(self, *, save: bool = True, export_pdf: bool = True, more: bool = True) -> None:
        self.btn_save.setEnabled(save)
        self.btn_export_pdf.setEnabled(export_pdf)
        self.btn_more.setEnabled(more)


def _status_kind(status: str) -> str:
    key = status.strip().lower()
    mapping = {
        "osnutek": "draft",
        "izdan": "issued",
        "neplačano": "warning",
        "delno plačano": "warning",
        "delno plačan": "warning",
        "plačano": "success",
        "plačan": "success",
        "zapadlo": "danger",
        "storniran": "muted",
        "stornirano": "muted",
        "poslana": "info",
        "sprejeta": "success",
        "zavrnjena": "danger",
        "potrjeno": "info",
        "v obdelavi": "warning",
        "dobavljeno": "success",
        "preklicano": "danger",
    }
    return mapping.get(key, "draft")
