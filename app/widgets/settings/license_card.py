"""Premium Enterprise License card for Settings — UI only; uses existing licensing APIs."""

from __future__ import annotations

import platform

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core import license as offline_license
from app.core.ui.notify import toast
from app.services.license_gate import _grace_valid
from app.services.licensing_service import LicenseError, LicenseState, deactivate, validate
from app.widgets.cards.enterprise_card import EnterpriseCard


def _display(value: str | None, fallback: str = "—") -> str:
    text = (value or "").strip()
    return text if text else fallback


def _repolish(widget: QWidget) -> None:
    style = widget.style()
    if style is None:
        return
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def _plan_label() -> str:
    """Read plan/edition from the existing offline license payload when present."""
    payload = offline_license.load()
    if payload and offline_license.verify(payload):
        edition = str(payload.get("edition") or "").strip()
        if edition:
            return edition.capitalize()
    return ""


def _expiry_label() -> str:
    """Read expiry from the existing offline license payload when present."""
    payload = offline_license.load()
    if not payload:
        return ""
    expires = str(payload.get("expires") or "").strip()
    return expires


class _MetaTile(QFrame):
    """Small labeled value tile used in the license info grid."""

    def __init__(self, caption: str, parent=None):
        super().__init__(parent)
        self.setObjectName("LicenseMetaTile")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self.caption = QLabel(caption)
        self.caption.setObjectName("LicenseMetaCaption")
        self.value = QLabel("—")
        self.value.setObjectName("LicenseMetaValue")
        self.value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.value.setWordWrap(True)

        layout.addWidget(self.caption)
        layout.addWidget(self.value)


class LicenseCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = EnterpriseCard("DashboardCard")
        card.body.setContentsMargins(22, 22, 22, 22)
        card.body.setSpacing(16)

        # —— Header: title block + status badge ——
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(4)

        eyebrow = QLabel("LICENSE CENTER")
        eyebrow.setObjectName("LicenseEyebrow")

        title = QLabel("Licenca")
        title.setObjectName("LicenseCardTitle")

        caption = QLabel("Paket, podjetje, veljavnost in preverjanje licence na tej napravi")
        caption.setObjectName("DashboardMuted")
        caption.setWordWrap(True)

        title_col.addWidget(eyebrow)
        title_col.addWidget(title)
        title_col.addWidget(caption)

        self.lbl_status = QLabel("—")
        self.lbl_status.setObjectName("LicenseStatusBadge")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setProperty("kind", "none")
        self.lbl_status.setMinimumHeight(28)
        self.lbl_status.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        header.addLayout(title_col, 1)
        header.addWidget(self.lbl_status, 0, Qt.AlignTop | Qt.AlignRight)
        card.body.addLayout(header)

        # —— Hero: company hierarchy ——
        hero = QFrame()
        hero.setObjectName("LicenseHero")
        hero.setAttribute(Qt.WA_StyledBackground, True)
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(16, 14, 16, 14)
        hero_layout.setSpacing(2)

        hero_label = QLabel("Podjetje")
        hero_label.setObjectName("LicenseMetaCaption")

        self.lbl_company = QLabel("—")
        self.lbl_company.setObjectName("LicenseCompanyName")
        self.lbl_company.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_company.setWordWrap(True)

        hero_hint = QLabel("Licencirana organizacija")
        hero_hint.setObjectName("DashboardMuted")

        hero_layout.addWidget(hero_label)
        hero_layout.addWidget(self.lbl_company)
        hero_layout.addWidget(hero_hint)
        card.body.addWidget(hero)

        # —— Meta grid (responsive) ——
        meta_wrap = QWidget()
        self._meta_grid = QGridLayout(meta_wrap)
        self._meta_grid.setContentsMargins(0, 0, 0, 0)
        self._meta_grid.setHorizontalSpacing(10)
        self._meta_grid.setVerticalSpacing(10)

        self._tile_plan = _MetaTile("Paket / plan")
        self._tile_license = _MetaTile("Licenčni ID")
        self._tile_expiry = _MetaTile("Veljavnost do")
        self._tile_seats = _MetaTile("Naprave / sedeži")
        self._tile_device = _MetaTile("Naprava")
        self._tile_check = _MetaTile("Zadnji stik s strežnikom")
        self._tile_grace = _MetaTile("Offline milostni rok")
        self._tile_verify = _MetaTile("Preverjanje")

        # Compatibility aliases used by tests / callers
        self.lbl_plan = self._tile_plan.value
        self.lbl_license_id = self._tile_license.value
        self.lbl_expiry = self._tile_expiry.value
        self.lbl_seats = self._tile_seats.value
        self.lbl_device = self._tile_device.value
        self.lbl_last_check = self._tile_check.value
        self.lbl_grace = self._tile_grace.value
        self.lbl_verify = self._tile_verify.value

        self._meta_tiles = (
            self._tile_plan,
            self._tile_license,
            self._tile_expiry,
            self._tile_seats,
            self._tile_device,
            self._tile_check,
            self._tile_grace,
            self._tile_verify,
        )
        for index, tile in enumerate(self._meta_tiles):
            self._meta_grid.addWidget(tile, index // 2, index % 2)
        self._meta_grid.setColumnStretch(0, 1)
        self._meta_grid.setColumnStretch(1, 1)
        card.body.addWidget(meta_wrap)

        # —— Actions ——
        actions = QHBoxLayout()
        actions.setContentsMargins(0, 4, 0, 0)
        actions.setSpacing(10)

        self.btn_check = QPushButton("Preveri licenco")
        self.btn_check.setObjectName("PrimaryButton")
        self.btn_check.setCursor(Qt.PointingHandCursor)
        self.btn_check.setMinimumHeight(38)
        self.btn_check.setMinimumWidth(160)
        self.btn_check.clicked.connect(self.verify_with_server)

        self.btn_deactivate = QPushButton("Deaktiviraj napravo")
        self.btn_deactivate.setObjectName("SecondaryButton")
        self.btn_deactivate.setCursor(Qt.PointingHandCursor)
        self.btn_deactivate.setMinimumHeight(38)
        self.btn_deactivate.setMinimumWidth(160)
        self.btn_deactivate.clicked.connect(self.deactivate_device)

        actions.addWidget(self.btn_check, 0, Qt.AlignLeft)
        actions.addWidget(self.btn_deactivate, 0, Qt.AlignLeft)
        actions.addStretch(1)
        card.body.addLayout(actions)

        root.addWidget(card)
        self._breakpoint = None
        self.refresh()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_meta(self.width())

    def _layout_meta(self, width: int) -> None:
        """Stack meta tiles on narrow cards; two columns when space allows."""
        mode = "wide" if width >= 520 else "narrow"
        if mode == self._breakpoint:
            return
        self._breakpoint = mode

        while self._meta_grid.count():
            item = self._meta_grid.takeAt(0)
            if item.widget():
                item.widget().setParent(self._meta_grid.parentWidget())

        if mode == "wide":
            for index, tile in enumerate(self._meta_tiles):
                self._meta_grid.addWidget(tile, index // 2, index % 2)
            self._meta_grid.setColumnStretch(0, 1)
            self._meta_grid.setColumnStretch(1, 1)
        else:
            for index, tile in enumerate(self._meta_tiles):
                self._meta_grid.addWidget(tile, index, 0)
            self._meta_grid.setColumnStretch(0, 1)
            self._meta_grid.setColumnStretch(1, 0)

    def _set_status(self, text: str, kind: str) -> None:
        self.lbl_status.setText(text)
        self.lbl_status.setProperty("kind", kind)
        _repolish(self.lbl_status)

    def refresh(self) -> None:
        state = LicenseState.load()
        plan = _plan_label()
        expiry = _expiry_label()

        if state is None:
            self._set_status("Ni aktivirana", "none")
            self.lbl_company.setText("—")
            self.lbl_plan.setText(_display(plan))
            self.lbl_license_id.setText("—")
            self.lbl_expiry.setText(_display(expiry))
            self.lbl_seats.setText("—")
            self.lbl_device.setText(_display(platform.node()))
            self.lbl_last_check.setText("—")
            self.lbl_grace.setText("—")
            self.lbl_verify.setText("Ni preverjeno")
            self.btn_deactivate.setEnabled(False)
            return

        status = (state.status or "").strip().lower()
        if status == "active":
            self._set_status("Aktivna", "active")
            verify_text = "Preverjeno — aktivna"
        elif status:
            self._set_status(status.capitalize(), "inactive")
            verify_text = f"Status: {status}"
        elif _grace_valid(state.grace_until):
            self._set_status("Offline (milostni rok)", "grace")
            verify_text = "Offline — milostni rok velja"
        else:
            self._set_status("Aktivirana (lokalno)", "local")
            verify_text = "Lokalno aktivirana"

        if not plan:
            plan = "Enterprise"

        self.lbl_company.setText(_display(state.company_name))
        self.lbl_plan.setText(plan)
        self.lbl_license_id.setText(_display(state.license_id))
        self.lbl_expiry.setText(_display(expiry or state.grace_until))
        device = _display(state.device_name or platform.node())
        self.lbl_seats.setText(f"1 naprava · {device}" if device != "—" else "1 naprava")
        self.lbl_device.setText(device)
        self.lbl_last_check.setText(_display(state.last_seen_at))
        self.lbl_verify.setText(verify_text)
        if state.grace_until:
            grace = state.grace_until
            if _grace_valid(state.grace_until):
                grace = f"{grace} (veljavno)"
            else:
                grace = f"{grace} (potečeno)"
            self.lbl_grace.setText(grace)
        else:
            self.lbl_grace.setText("—")
        self.btn_deactivate.setEnabled(True)

    def verify_with_server(self) -> None:
        state = LicenseState.load()
        if state is None:
            self.refresh()
            toast(self, "Licenca ni aktivirana.")
            return

        self.btn_check.setEnabled(False)
        try:
            result = validate(state)
            state.apply_server_result(result)
            if not state.status:
                state.status = str(result.get("status") or "")
            state.save()
            self.refresh()
            if result.get("status") == "active":
                toast(self, "Licenca je aktivna.")
            else:
                toast(self, "Licenca ni aktivna.")
        except LicenseError as exc:
            self.refresh()
            if _grace_valid(state.grace_until):
                toast(self, f"Strežnik ni dosegljiv — milostni rok velja. ({exc})")
            else:
                toast(self, str(exc))
        finally:
            self.btn_check.setEnabled(True)

    def deactivate_device(self) -> None:
        """UI entry for the existing licensing_service.deactivate()."""
        state = LicenseState.load()
        if state is None:
            self.refresh()
            toast(self, "Licenca ni aktivirana.")
            return

        reply = QMessageBox.question(
            self,
            "Deaktivacija naprave",
            "Ali želite deaktivirati licenco na tej napravi?\n\n"
            "Po deaktivaciji bo potrebna ponovna aktivacija.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.btn_deactivate.setEnabled(False)
        self.btn_check.setEnabled(False)
        try:
            deactivate(state)
            self.refresh()
            toast(self, "Naprava je deaktivirana.")
        except LicenseError as exc:
            self.refresh()
            toast(self, str(exc))
        finally:
            self.btn_check.setEnabled(True)
            # refresh() already sets deactivate enabled based on state
