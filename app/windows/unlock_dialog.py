"""Odklepanje seje — username + password authentication."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QCheckBox, QDialog, QLabel, QLineEdit, QMessageBox, QVBoxLayout, QWidget

from app.core.auth_gate import (
    AUTH_ERROR_MESSAGE,
    authenticate_credentials,
    authenticated_role,
)
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
        self._user = (extras.get("administrator") or "Administrator").strip()
        self._remember = bool(extras.get("remember_user", True))
        self._authenticating = False

        brand = QWidget()
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 8)
        brand_layout.setSpacing(8)
        brand_layout.setAlignment(Qt.AlignCenter)

        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setObjectName("LoginLogo")
        self.logo.setAttribute(Qt.WA_TranslucentBackground, True)
        self._load_brand_logo()
        brand_layout.addWidget(self.logo)

        title = QLabel("JU-TAN OFFICE")
        title.setObjectName("LoginBrand")
        title.setAlignment(Qt.AlignCenter)
        brand_layout.addWidget(title)

        subtitle = QLabel("Prijavite se z uporabniškim imenom in geslom.")
        subtitle.setObjectName("DashboardMuted")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        brand_layout.addWidget(subtitle)

        self.user = QLineEdit()
        self.user.setPlaceholderText("Uporabniško ime")
        self.user.setText(self._user if self._remember else "")
        self.user.setMinimumHeight(40)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Geslo")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(40)
        self.password.clear()

        self.remember = QCheckBox("Zapomni uporabniško ime")
        self.remember.setChecked(self._remember)

        self.show_password = QCheckBox("Prikaži geslo")
        self.show_password.toggled.connect(
            lambda checked: self.password.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )

        self.body.addWidget(brand)
        self.body.addWidget(self.user)
        self.body.addWidget(self.password)
        self.body.addWidget(self.show_password)
        self.body.addWidget(self.remember)

        self.bind_save(self._authenticate)
        self.password.returnPressed.connect(self._authenticate)
        self.user.returnPressed.connect(self._focus_password)
        self.btn_cancel.setAutoDefault(False)
        self.btn_cancel.setDefault(False)
        self.btn_save.setAutoDefault(True)
        self.btn_save.setDefault(True)
        self.btn_save.setText("Prijava")

    def _focus_password(self) -> None:
        self.password.setFocus()
        self.password.selectAll()

    def _load_brand_logo(self) -> None:
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
        self._authenticate()

    def _authenticate(self) -> None:
        if self._authenticating:
            return
        self._authenticating = True
        extras = SettingsController().load_extras()
        username = self.user.text().strip()
        password = self.password.text()
        ok, err = authenticate_credentials(username, password, extras)
        if not ok:
            self._authenticating = False
            QMessageBox.warning(self, "Prijava", err or AUTH_ERROR_MESSAGE)
            self.password.clear()
            self.password.setFocus()
            return

        extras["remember_user"] = self.remember.isChecked()
        if self.remember.isChecked() and username:
            extras["administrator"] = username
            extras["remembered_username"] = username
        SettingsController().save_extras(extras)
        session.remember_user = self.remember.isChecked()

        from app.core.auth_gate import resolve_authenticated_user
        from app.core.user_service import apply_session_for_user

        user = resolve_authenticated_user(username, password, extras)
        if user is not None:
            apply_session_for_user(user)
        else:
            role = authenticated_role(extras, username=username)
            session.login(username or (extras.get("administrator") or "Administrator"), role)
        session.touch()
        self.password.clear()
        QDialog.done(self, QDialog.DialogCode.Accepted)

    def reject(self) -> None:
        self.password.clear()
        QDialog.reject(self)
