"""Odklepanje seje z geslom — premium login entrance."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QMessageBox, QVBoxLayout, QWidget

from app.core.passwords import verify_password
from app.core.session import session
from app.core.ui.app_identity import apply_window_icon
from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.modules.settings.settings_controller import SettingsController
from app.widgets.navigation.sidebar_header import resolve_brand_logo


class UnlockDialog(EnterpriseDialog):
    """Startup login and idle unlock share one authentication path."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            parent,
            title="JU-TAN Office",
            heading="Prijava",
            size="SMALL",
            save_text="Prijava",
            cancel_text="Izhod",
        )
        apply_window_icon(self)
        self.setObjectName("UnlockDialog")
        extras = SettingsController().load_extras()
        self._hash = extras.get("password_hash") or ""
        self._user = extras.get("administrator") or "Administrator"
        self._authenticating = False

        brand = QWidget()
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 8)
        brand_layout.setSpacing(8)
        brand_layout.setAlignment(Qt.AlignCenter)

        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setObjectName("LoginLogo")
        # Transparent PNG — no opaque fill behind the brand mark.
        self.logo.setAttribute(Qt.WA_TranslucentBackground, True)
        self._load_brand_logo()
        brand_layout.addWidget(self.logo)

        subtitle = QLabel("Vnesite geslo za dostop do aplikacije.")
        subtitle.setObjectName("DashboardMuted")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        brand_layout.addWidget(subtitle)

        self.user = QLineEdit()
        self.user.setPlaceholderText("Uporabnik")
        self.user.setText(self._user if extras.get("remember_user", True) else "")
        self.user.setMinimumHeight(40)
        self.password = QLineEdit()
        self.password.setPlaceholderText("Geslo")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(40)

        self.body.addWidget(brand)
        self.body.addWidget(self.user)
        self.body.addWidget(self.password)

        # One path: mouse Prijava, ENTER (default button), returnPressed, accept().
        self.bind_save(self._authenticate)
        self.password.returnPressed.connect(self._authenticate)
        self.user.returnPressed.connect(self._authenticate)
        self.btn_cancel.setAutoDefault(False)
        self.btn_cancel.setDefault(False)
        self.btn_save.setAutoDefault(True)
        self.btn_save.setDefault(True)
        self.btn_save.setText("Prijava")

    def _load_brand_logo(self) -> None:
        """Theme-aware login logo via central resolver; keep aspect ratio."""
        path = resolve_brand_logo()
        if path is not None:
            pix = QPixmap(str(path))
            if not pix.isNull():
                ratio = max(1.0, float(self.devicePixelRatioF() or 1.0))
                target_w = int(220 * ratio)
                scaled = pix.scaledToWidth(target_w, Qt.SmoothTransformation)
                scaled.setDevicePixelRatio(ratio)
                self.logo.setPixmap(scaled)
                self.logo.setText("")
                self.logo.setObjectName("LoginLogo")
                return
        self.logo.setPixmap(QPixmap())
        self.logo.setText("JU-TAN Office")
        self.logo.setObjectName("LoginBrand")

    def accept(self) -> None:
        """Never close as Accepted without going through password validation."""
        self._authenticate()

    def _authenticate(self) -> None:
        if self._authenticating:
            return
        self._authenticating = True
        try:
            if not verify_password(self.password.text(), self._hash):
                QMessageBox.warning(self, "Prijava", "Geslo ni pravilno.")
                self.password.setFocus()
                self.password.selectAll()
                return
            role = SettingsController().load_extras().get("role") or "Administrator"
            session.login(self.user.text().strip() or self._user, role)
            session.touch()
            QDialog.done(self, QDialog.DialogCode.Accepted)
        finally:
            # Coalesce returnPressed + default-button click from the same ENTER.
            QTimer.singleShot(0, self._release_authenticate)

    def _release_authenticate(self) -> None:
        self._authenticating = False

    def reject(self) -> None:
        QDialog.reject(self)
