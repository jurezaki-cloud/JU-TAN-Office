"""Update Center card for Settings — UI only; uses existing app.core.update."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import APP_CHANNEL, APP_VERSION
from app.core.ui.notify import toast
from app.widgets.cards.enterprise_card import EnterpriseCard


def _repolish(widget: QWidget) -> None:
    style = widget.style()
    if style is None:
        return
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


class UpdateCard(QWidget):
    """Commercial Update Center — check channel and show status (no installer logic)."""

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = EnterpriseCard("DashboardCard")
        card.body.setContentsMargins(22, 22, 22, 22)
        card.body.setSpacing(16)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(4)

        eyebrow = QLabel("UPDATE CENTER")
        eyebrow.setObjectName("LicenseEyebrow")

        title = QLabel("Posodobitve")
        title.setObjectName("LicenseCardTitle")

        caption = QLabel("Trenutna verzija in status kanala posodobitev")
        caption.setObjectName("DashboardMuted")
        caption.setWordWrap(True)

        title_col.addWidget(eyebrow)
        title_col.addWidget(title)
        title_col.addWidget(caption)

        self.lbl_status = QLabel("—")
        self.lbl_status.setObjectName("LicenseStatusBadge")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setProperty("kind", "local")
        self.lbl_status.setMinimumHeight(28)
        self.lbl_status.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        header.addLayout(title_col, 1)
        header.addWidget(self.lbl_status, 0, Qt.AlignTop | Qt.AlignRight)
        card.body.addLayout(header)

        version_row = QFrame()
        version_row.setObjectName("LicenseHero")
        version_row.setAttribute(Qt.WA_StyledBackground, True)
        version_layout = QVBoxLayout(version_row)
        version_layout.setContentsMargins(16, 14, 16, 14)
        version_layout.setSpacing(2)

        version_caption = QLabel("Trenutna verzija")
        version_caption.setObjectName("LicenseMetaCaption")
        self.lbl_version = QLabel(f"{APP_VERSION} {APP_CHANNEL}")
        self.lbl_version.setObjectName("LicenseCompanyName")
        self.lbl_channel = QLabel(f"Kanal: {APP_CHANNEL}")
        self.lbl_channel.setObjectName("DashboardMuted")

        version_layout.addWidget(version_caption)
        version_layout.addWidget(self.lbl_version)
        version_layout.addWidget(self.lbl_channel)
        card.body.addWidget(version_row)

        self.empty_state = QLabel(
            "Kanal posodobitev trenutno ni na voljo.\n"
            "Ko bo namestitveni kanal konfiguriran, se tukaj prikažejo nove različice."
        )
        self.empty_state.setObjectName("SettingsEmptyState")
        self.empty_state.setAlignment(Qt.AlignCenter)
        self.empty_state.setWordWrap(True)
        card.body.addWidget(self.empty_state)

        self.lbl_detail = QLabel("")
        self.lbl_detail.setObjectName("DashboardMuted")
        self.lbl_detail.setWordWrap(True)
        self.lbl_detail.hide()
        card.body.addWidget(self.lbl_detail)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 4, 0, 0)
        actions.setSpacing(10)

        self.btn_check = QPushButton("Preveri posodobitve")
        self.btn_check.setObjectName("PrimaryButton")
        self.btn_check.setCursor(Qt.PointingHandCursor)
        self.btn_check.setMinimumHeight(38)
        self.btn_check.setMinimumWidth(180)
        self.btn_check.clicked.connect(self.check_updates)

        actions.addWidget(self.btn_check, 0, Qt.AlignLeft)
        actions.addStretch(1)
        card.body.addLayout(actions)

        root.addWidget(card)
        self.refresh()

    def _set_status(self, text: str, kind: str) -> None:
        self.lbl_status.setText(text)
        self.lbl_status.setProperty("kind", kind)
        _repolish(self.lbl_status)

    def refresh(self) -> None:
        self.lbl_version.setText(f"{APP_VERSION} {APP_CHANNEL}")
        self.lbl_channel.setText(f"Kanal: {APP_CHANNEL}")
        self._set_status("Ni preverjeno", "local")
        self.empty_state.hide()
        self.lbl_detail.hide()
        self.lbl_detail.clear()

    def check_updates(self) -> None:
        self.btn_check.setEnabled(False)
        try:
            # Lazy import avoids circular load via app.core.update → SettingsController.
            from app.core.update import UpdateError, check_for_update

            try:
                payload = check_for_update()
            except UpdateError as exc:
                self._set_status("Kanal zavrnjen", "none")
                self.empty_state.show()
                self.lbl_detail.hide()
                toast(self, str(exc))
                return

            if payload is None:
                # Channel missing, unreadable, or already up to date — professional empty state.
                self._set_status("Ni posodobitev", "local")
                self.empty_state.show()
                self.lbl_detail.hide()
                toast(self, "Ni na voljo novejše različice.")
                return

            remote = str(payload.get("version") or "").strip() or "—"
            notes = str(payload.get("notes") or "").strip()
            self._set_status("Na voljo", "active")
            self.empty_state.hide()
            detail = f"Nova različica: {remote}"
            if notes:
                detail = f"{detail}\n{notes}"
            self.lbl_detail.setText(detail)
            self.lbl_detail.show()
            toast(self, f"Na voljo je različica {remote}.")
        except Exception as exc:
            self._set_status("Kanal ni dosegljiv", "none")
            self.empty_state.show()
            self.lbl_detail.hide()
            toast(self, f"Preverjanje ni uspelo: {exc}")
        finally:
            self.btn_check.setEnabled(True)
