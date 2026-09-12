"""Odklepanje seje z geslom."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QLineEdit, QMessageBox

from app.core.passwords import verify_password
from app.core.session import session
from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.modules.settings.settings_controller import SettingsController
from app.widgets.cards.enterprise_card import EnterpriseCard


class UnlockDialog(EnterpriseDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(
            parent,
            title="Prijava",
            heading="Odkleni JU-TAN Office",
            size="SMALL",
            save_text="Prijava",
            cancel_text="Izhod",
        )
        extras = SettingsController().load_extras()
        self._hash = extras.get("password_hash") or ""
        self._user = extras.get("administrator") or "Administrator"
        card = EnterpriseCard("DashboardCard")
        grid = FormGrid()
        self.user = QLineEdit()
        self.user.setText(self._user if extras.get("remember_user", True) else "")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        grid.add_full("Uporabnik", self.user)
        grid.add_full("Geslo", self.password)
        card.body.addLayout(grid.layout)
        hint = QLabel("Seja je zaklenjena. Vnesite geslo administratorja.")
        hint.setObjectName("DashboardMuted")
        hint.setWordWrap(True)
        self.body.addWidget(card)
        self.body.addWidget(hint)
        self.bind_save(self._unlock)

    def _unlock(self) -> None:
        if not verify_password(self.password.text(), self._hash):
            QMessageBox.warning(self, "Prijava", "Geslo ni pravilno.")
            return
        from app.modules.settings.settings_controller import SettingsController
        role = SettingsController().load_extras().get("role") or "Administrator"
        session.login(self.user.text().strip() or self._user, role)
        self.accept()

    def reject(self) -> None:
        from PySide6.QtWidgets import QDialog
        QDialog.reject(self)
