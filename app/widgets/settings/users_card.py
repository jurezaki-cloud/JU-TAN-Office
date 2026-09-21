"""Uporabniki in pravice — Administrator user management."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.permissions import can, role_default_permission_keys
from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.icons import apply_button_icon
from app.core.user_service import (
    ACTION_PERMISSION_LABELS,
    LastAdminError,
    PAGE_PERMISSION_LABELS,
    SelfRemovalError,
    UI_ROLE_PRESETS,
    assess_user_removal,
    create_user,
    display_role_for_user,
    list_public_users,
    remove_user,
    reset_user_password,
    role_label,
    update_user,
)
from app.widgets.cards.enterprise_card import EnterpriseCard


class UsersCard(QWidget):
    """Settings card: list users and open create/edit dialogs."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = EnterpriseCard("DashboardCard")
        title = QLabel("Uporabniki in pravice")
        title.setObjectName("DashboardSectionTitle")
        card.body.addWidget(title)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Uporabnik", "Vloga", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setMinimumHeight(140)
        card.body.addWidget(self.table)

        self.empty_state = QLabel("Ni uporabnikov.\nDodajte prvega uporabnika za dostop do sistema.")
        self.empty_state.setObjectName("SettingsEmptyState")
        self.empty_state.setAlignment(Qt.AlignCenter)
        self.empty_state.setWordWrap(True)
        self.empty_state.setMinimumHeight(120)
        self.empty_state.hide()
        card.body.addWidget(self.empty_state)

        row = QHBoxLayout()
        self.btn_new = QPushButton("+ Nov uporabnik")
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_edit = QPushButton("Uredi")
        self.btn_edit.setObjectName("SecondaryButton")
        self.btn_reset = QPushButton("Ponastavi geslo")
        self.btn_reset.setObjectName("SecondaryButton")
        self.btn_remove = QPushButton("Odstrani uporabnika")
        self.btn_remove.setObjectName("DangerButton")
        apply_button_icon(self.btn_remove, "delete")
        row.addWidget(self.btn_new)
        row.addWidget(self.btn_edit)
        row.addWidget(self.btn_reset)
        row.addWidget(self.btn_remove)
        row.addStretch(1)
        card.body.addLayout(row)
        layout.addWidget(card)

        self.btn_new.clicked.connect(self._create)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_reset.clicked.connect(self._reset_password)
        self.btn_remove.clicked.connect(self._remove)
        self._users: list[dict] = []
        self.refresh()

    def refresh(self) -> None:
        allowed = can("users")
        self.setVisible(allowed)
        self.btn_new.setEnabled(allowed)
        self.btn_edit.setEnabled(allowed)
        self.btn_reset.setEnabled(allowed)
        self.btn_remove.setEnabled(allowed)
        if not allowed:
            self.table.setRowCount(0)
            self.table.hide()
            self.empty_state.hide()
            return
        try:
            self._users = list_public_users()
        except PermissionError:
            self._users = []
        self.table.setRowCount(len(self._users))
        for i, user in enumerate(self._users):
            self.table.setItem(i, 0, QTableWidgetItem(user["username"]))
            self.table.setItem(i, 1, QTableWidgetItem(display_role_for_user(user)))
            status = "Aktiven" if user["is_active"] else "Odstranjen/Neaktiven"
            self.table.setItem(i, 2, QTableWidgetItem(status))
        empty = len(self._users) == 0
        self.table.setVisible(not empty)
        self.empty_state.setVisible(empty)

    def _selected(self) -> dict | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        index = rows[0].row()
        if index < 0 or index >= len(self._users):
            return None
        return self._users[index]

    def _create(self) -> None:
        dlg = UserEditorDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()
            self.changed.emit()

    def _edit(self) -> None:
        user = self._selected()
        if user is None:
            QMessageBox.information(self, "Uporabniki", "Izberite uporabnika.")
            return
        dlg = UserEditorDialog(self, user=user)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()
            self.changed.emit()

    def _reset_password(self) -> None:
        user = self._selected()
        if user is None:
            QMessageBox.information(self, "Uporabniki", "Izberite uporabnika.")
            return
        dlg = ResetPasswordDialog(self, user_id=user["id"], username=user["username"])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Geslo", "Geslo je ponastavljeno.")

    def _remove(self) -> None:
        if not can("users"):
            QMessageBox.warning(self, "Uporabniki", "Dejanje ni dovoljeno.")
            return
        user = self._selected()
        if user is None:
            QMessageBox.information(self, "Uporabniki", "Izberite uporabnika.")
            return
        try:
            assessment = assess_user_removal(user["id"])
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "Uporabniki", str(exc))
            return

        if assessment.mode == "physical":
            detail = (
                f"Uporabnik {assessment.username} ne bo več mogel dostopati do JU-TAN Office.\n\n"
                "Uporabnik nima povezane poslovne zgodovine in bo trajno odstranjen."
            )
        else:
            detail = (
                f"Uporabnik {assessment.username} ne bo več mogel dostopati do JU-TAN Office.\n\n"
                "Uporabnik ima povezano zgodovino. Zaradi sledljivosti bo račun "
                "deaktiviran, zgodovinski zapisi pa bodo ohranjeni."
            )

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Odstrani uporabnika?")
        box.setText("Odstrani uporabnika?")
        box.setInformativeText(detail)
        btn_remove = box.addButton("ODSTRANI UPORABNIKA", QMessageBox.DestructiveRole)
        btn_cancel = box.addButton("PREKLIČI", QMessageBox.RejectRole)
        box.setDefaultButton(btn_cancel)
        box.exec()
        if box.clickedButton() is not btn_remove:
            return

        try:
            remove_user(user["id"])
        except (LastAdminError, SelfRemovalError) as exc:
            QMessageBox.warning(self, "Uporabniki", str(exc))
            return
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "Uporabniki", str(exc))
            return

        self.refresh()
        self.changed.emit()


class PermissionChecks(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.page_boxes: dict[int, QCheckBox] = {}
        self.action_boxes: dict[str, QCheckBox] = {}
        pages_lbl = QLabel("Dostop do modulov")
        pages_lbl.setObjectName("DashboardMuted")
        layout.addWidget(pages_lbl)
        for label, index in PAGE_PERMISSION_LABELS:
            box = QCheckBox(label)
            self.page_boxes[index] = box
            layout.addWidget(box)
        actions_lbl = QLabel("Dejanja")
        actions_lbl.setObjectName("DashboardMuted")
        layout.addWidget(actions_lbl)
        for label, key in ACTION_PERMISSION_LABELS:
            box = QCheckBox(label)
            self.action_boxes[key] = box
            layout.addWidget(box)

    def set_from_keys(self, keys: list[str]) -> None:
        keyset = set(keys)
        for index, box in self.page_boxes.items():
            box.setChecked(f"page:{index}" in keyset)
        for action, box in self.action_boxes.items():
            box.setChecked(action in keyset)

    def keys(self) -> list[str]:
        from app.core.permissions import actions_and_pages_to_permission_keys

        actions = {k for k, box in self.action_boxes.items() if box.isChecked()}
        pages = {i for i, box in self.page_boxes.items() if box.isChecked()}
        return actions_and_pages_to_permission_keys(actions, pages)

    def apply_role_preset(self, role: str) -> None:
        self.set_from_keys(role_default_permission_keys(role))


class UserEditorDialog(EnterpriseDialog):
    def __init__(self, parent=None, user: dict | None = None):
        self._user = user
        super().__init__(
            parent,
            title="Uporabnik",
            heading="Nov uporabnik" if user is None else "Uredi uporabnika",
            size="MEDIUM",
            save_text="Shrani",
            cancel_text="Prekliči",
        )
        form = QFormLayout()
        self.username = QLineEdit()
        self.username.setMinimumHeight(36)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(36)
        self.password2 = QLineEdit()
        self.password2.setEchoMode(QLineEdit.Password)
        self.password2.setMinimumHeight(36)
        self.role = QComboBox()
        for key in UI_ROLE_PRESETS:
            self.role.addItem(role_label(key), key)
        self.active = QCheckBox("Aktiven")
        self.active.setChecked(True)
        form.addRow("Uporabniško ime", self.username)
        if user is None:
            form.addRow("Geslo", self.password)
            form.addRow("Ponovi geslo", self.password2)
        form.addRow("Vloga", self.role)
        form.addRow("", self.active)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        self.perms = PermissionChecks()
        scroll.setWidget(self.perms)
        scroll.setMinimumHeight(220)

        custom_hint = QLabel("Če pravice odstopajo od vloge, bo status »Po meri«.")
        custom_hint.setObjectName("DashboardMuted")
        custom_hint.setWordWrap(True)

        self.body.addLayout(form)
        self.body.addWidget(custom_hint)
        self.body.addWidget(scroll)
        self.role.currentIndexChanged.connect(self._on_role)
        self.bind_save(self._save)

        if user is not None:
            self.username.setText(user["username"])
            idx = self.role.findData(user["role"])
            if idx >= 0:
                self.role.setCurrentIndex(idx)
            self.active.setChecked(bool(user["is_active"]))
            self.perms.set_from_keys(user.get("permissions") or role_default_permission_keys(user["role"]))
        else:
            self.perms.apply_role_preset(self.role.currentData())

    def _on_role(self) -> None:
        role = self.role.currentData()
        if role:
            self.perms.apply_role_preset(role)

    def _save(self) -> None:
        username = self.username.text().strip()
        if not username:
            QMessageBox.warning(self, "Uporabnik", "Vnesite uporabniško ime.")
            return
        role = self.role.currentData() or "Read Only"
        keys = self.perms.keys()
        try:
            if self._user is None:
                pwd = self.password.text()
                if not pwd:
                    QMessageBox.warning(self, "Uporabnik", "Vnesite geslo.")
                    return
                if pwd != self.password2.text():
                    QMessageBox.warning(self, "Uporabnik", "Gesli se ne ujemata.")
                    return
                create_user(
                    username=username,
                    password=pwd,
                    role=role,
                    is_active=self.active.isChecked(),
                    permissions=keys,
                )
            else:
                update_user(
                    self._user["id"],
                    username=username,
                    role=role,
                    is_active=self.active.isChecked(),
                    permissions=keys,
                )
        except LastAdminError as exc:
            QMessageBox.warning(self, "Uporabniki", str(exc))
            return
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "Uporabnik", str(exc))
            return
        self.accept()


class ResetPasswordDialog(EnterpriseDialog):
    def __init__(self, parent=None, *, user_id: int, username: str):
        self._user_id = user_id
        super().__init__(
            parent,
            title="Ponastavitev gesla",
            heading=f"Novo geslo — {username}",
            size="SMALL",
            save_text="Ponastavi",
            cancel_text="Prekliči",
        )
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(36)
        self.password2 = QLineEdit()
        self.password2.setEchoMode(QLineEdit.Password)
        self.password2.setMinimumHeight(36)
        form = QFormLayout()
        form.addRow("Novo geslo", self.password)
        form.addRow("Ponovi geslo", self.password2)
        hint = QLabel("Staro geslo se nikoli ne prikaže.")
        hint.setObjectName("DashboardMuted")
        self.body.addLayout(form)
        self.body.addWidget(hint)
        self.bind_save(self._save)

    def _save(self) -> None:
        pwd = self.password.text()
        if not pwd:
            QMessageBox.warning(self, "Geslo", "Vnesite novo geslo.")
            return
        if pwd != self.password2.text():
            QMessageBox.warning(self, "Geslo", "Gesli se ne ujemata.")
            return
        try:
            reset_user_password(self._user_id, pwd)
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "Geslo", str(exc))
            return
        self.accept()
