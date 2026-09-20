"""One-time credential onboarding for existing installs without login credentials.

Preserves all business data — creates the first SQLite administrator and clears
competing settings.json password_hash. Idempotent once users exist.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QMessageBox, QVBoxLayout, QWidget

from app.core.passwords import hash_password
from app.core.ui.app_identity import apply_window_icon
from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.user_service import create_first_administrator, users_exist
from app.modules.settings.settings_controller import SettingsController
from app.widgets.navigation.sidebar_header import resolve_brand_logo


class CredentialOnboardingDialog(EnterpriseDialog):
    """Force set administrator username + password for legacy installs."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            parent,
            title="JU-TAN Office",
            heading="Nastavitev prijave",
            size="SMALL",
            save_text="Shrani in nadaljuj",
            cancel_text="Izhod",
        )
        apply_window_icon(self)
        self.setObjectName("CredentialOnboardingDialog")

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

        subtitle = QLabel("Za nadaljevanje nastavite prijavo za skrbnika.")
        subtitle.setObjectName("DashboardMuted")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        brand_layout.addWidget(subtitle)

        self.user = QLineEdit()
        self.user.setPlaceholderText("Uporabniško ime")
        self.user.setText("")  # Never prefill — owner must choose deliberately.
        self.user.setMinimumHeight(40)
        self.user.setObjectName("LoginUsername")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Novo geslo")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(40)
        self.password.setObjectName("LoginPassword")

        self.password2 = QLineEdit()
        self.password2.setPlaceholderText("Potrditev gesla")
        self.password2.setEchoMode(QLineEdit.Password)
        self.password2.setMinimumHeight(40)

        user_lbl = QLabel("Uporabniško ime")
        user_lbl.setObjectName("DashboardMuted")
        pwd_lbl = QLabel("Novo geslo")
        pwd_lbl.setObjectName("DashboardMuted")
        pwd2_lbl = QLabel("Potrditev gesla")
        pwd2_lbl.setObjectName("DashboardMuted")

        self.body.addWidget(brand)
        self.body.addWidget(user_lbl)
        self.body.addWidget(self.user)
        self.body.addWidget(pwd_lbl)
        self.body.addWidget(self.password)
        self.body.addWidget(pwd2_lbl)
        self.body.addWidget(self.password2)

        self.bind_save(self._save)
        self.password2.returnPressed.connect(self._save)
        self.btn_cancel.setAutoDefault(False)
        self.btn_cancel.setDefault(False)
        self.btn_save.setAutoDefault(True)
        self.btn_save.setDefault(True)

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
                return
        self.logo.setPixmap(QPixmap())
        self.logo.setText("JU-TAN Office")
        self.logo.setObjectName("LoginBrand")

    def accept(self) -> None:
        self._save()

    def _save(self) -> None:
        username = self.user.text().strip()
        if not username:
            QMessageBox.warning(self, "Prijava", "Vnesite uporabniško ime.")
            self.user.setFocus()
            return
        pwd = self.password.text()
        if not pwd:
            QMessageBox.warning(self, "Prijava", "Vnesite geslo.")
            self.password.setFocus()
            return
        if pwd != self.password2.text():
            QMessageBox.warning(self, "Prijava", "Gesli se ne ujemata.")
            self.password2.setFocus()
            return
        try:
            hash_password(pwd)  # validate policy before creating account
        except ValueError as exc:
            QMessageBox.warning(self, "Prijava", str(exc))
            self.password.setFocus()
            return

        if users_exist():
            # Idempotent: credentials already present.
            QDialog.done(self, QDialog.DialogCode.Accepted)
            return

        try:
            create_first_administrator(username, pwd)
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "Prijava", str(exc))
            return

        controller = SettingsController()
        extras = controller.load_extras()
        # Preserve role/business settings; retire competing settings auth hash.
        extras["administrator"] = username
        extras["password_hash"] = ""
        extras["account_enabled"] = True
        extras["legacy_auth_migrated"] = True
        if not extras.get("role"):
            extras["role"] = "Administrator"
        controller.save_extras(extras)
        QDialog.done(self, QDialog.DialogCode.Accepted)

    def reject(self) -> None:
        QDialog.reject(self)
