"""Čarovnik prvega zagona — premium večstopenjski onboarding (UI).

Business finish path is unchanged: company + first administrator via existing
services only. License step is guidance — it does not activate licenses.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import DATA_DIR
from app.core.passwords import hash_password
from app.core.setup_state import mark_setup_complete
from app.core.ui.app_identity import apply_window_icon
from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.database.company_repository import company_repository
from app.modules.settings.settings_controller import SettingsController
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.navigation.sidebar_header import resolve_brand_logo

# Step indices — keep stable for navigation helpers / tests.
STEP_WELCOME = 0
STEP_COMPANY = 1
STEP_USER = 2
STEP_SECURITY = 3
STEP_LICENSE = 4
STEP_COMPLETE = 5

_STEP_META = (
    ("Dobrodošli", "Predstavitev"),
    ("Podjetje", "Podatki podjetja"),
    ("Skrbnik", "Glavni uporabnik"),
    ("Varnost", "Kontrolni seznam"),
    ("Licenca", "Aktivacija"),
    ("Konec", "Pripravljeni"),
)


class FirstRunWizard(EnterpriseDialog):
    """Premium first-launch wizard — UI shell over the existing setup finish path."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            parent,
            title="JU-TAN Office — Prvi zagon",
            heading="Dobrodošli v JU-TAN Office",
            size="MEDIUM",
            save_text="Dokončaj",
            cancel_text="Prekliči",
        )
        apply_window_icon(self)
        self.setObjectName("FirstRunWizard")
        self._logo = ""
        self._step = STEP_WELCOME

        # Default EnterpriseDialog save/cancel — replace with wizard chrome.
        self.btn_save.hide()
        self.btn_cancel.hide()

        self._progress = self._build_progress()
        self.body.addWidget(self._progress)

        self.stack = QStackedWidget()
        self.stack.setObjectName("FirstRunStack")
        self.stack.addWidget(self._step_welcome())
        self.stack.addWidget(self._step_company())
        self.stack.addWidget(self._step_user())
        self.stack.addWidget(self._step_security())
        self.stack.addWidget(self._step_license())
        self.stack.addWidget(self._step_complete())
        self.body.addWidget(self.stack)

        self.btn_back = QPushButton("Nazaj")
        self.btn_back.setObjectName("SecondaryButton")
        self.btn_next = QPushButton("Naprej")
        self.btn_next.setObjectName("PrimaryButton")
        self.btn_exit = QPushButton("Prekliči")
        self.btn_exit.setObjectName("SecondaryButton")
        for button in (self.btn_back, self.btn_next, self.btn_exit):
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
            button.setAutoDefault(False)
            button.setDefault(False)

        self.footer_layout.insertWidget(0, self.btn_exit)
        self.footer_layout.insertWidget(1, self.btn_back)
        self.footer_layout.addWidget(self.btn_next)

        self.btn_exit.clicked.connect(self.reject)
        self.btn_back.clicked.connect(self._back)
        self.btn_next.clicked.connect(self._next)

        self.btn_next.setAutoDefault(True)
        self.btn_next.setDefault(True)
        self.bind_save(self._next)
        self._show_step(STEP_WELCOME)

    # ------------------------------------------------------------------ UI steps

    def _build_progress(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("FirstRunProgress")
        frame.setAttribute(Qt.WA_StyledBackground, True)
        row = QHBoxLayout(frame)
        row.setContentsMargins(4, 4, 4, 12)
        row.setSpacing(6)
        self._progress_labels: list[QLabel] = []
        for index, (title, _subtitle) in enumerate(_STEP_META):
            if index:
                sep = QLabel("·")
                sep.setObjectName("FirstRunProgressSep")
                sep.setAlignment(Qt.AlignCenter)
                row.addWidget(sep)
            label = QLabel(f"{index + 1}. {title}")
            label.setObjectName("FirstRunProgressStep")
            label.setAlignment(Qt.AlignCenter)
            label.setProperty("active", "false")
            label.setProperty("done", "false")
            row.addWidget(label, 1)
            self._progress_labels.append(label)
        return frame

    def _step_welcome(self) -> QWidget:
        card = EnterpriseCard("DashboardCard")
        card.setObjectName("FirstRunCard")

        brand = QWidget()
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(8, 8, 8, 8)
        brand_layout.setSpacing(10)
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

        eyebrow = QLabel("Enterprise onboarding")
        eyebrow.setObjectName("FirstRunEyebrow")
        eyebrow.setAlignment(Qt.AlignCenter)
        brand_layout.addWidget(eyebrow)

        lead = QLabel(
            "Dobrodošli. Ta čarovnik vas vodi skozi prvo nastavitev podjetja, "
            "skrbnika, varnostnih priporočil in licence — varno in v nekaj minutah."
        )
        lead.setObjectName("FirstRunLead")
        lead.setWordWrap(True)
        lead.setAlignment(Qt.AlignCenter)
        brand_layout.addWidget(lead)

        points = QLabel(
            "• Podatki podjetja za dokumente in poročila\n"
            "• Glavni skrbniški račun z močnim geslom\n"
            "• Kratek varnostni kontrolni seznam\n"
            "• Navodila za aktivacijo licence"
        )
        points.setObjectName("DashboardMuted")
        points.setWordWrap(True)
        points.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        brand_layout.addWidget(points)

        note = QLabel(
            "Obstoječe namestitve s konfiguriranim podjetjem ta čarovnik "
            "preskočijo — prijava poteka kot doslej."
        )
        note.setObjectName("DashboardMuted")
        note.setWordWrap(True)
        note.setAlignment(Qt.AlignCenter)
        brand_layout.addWidget(note)

        card.body.addWidget(brand)
        return card

    def _step_company(self) -> QWidget:
        card = EnterpriseCard("DashboardCard")
        card.setObjectName("FirstRunCard")
        intro = QLabel("Vnesite osnovne podatke podjetja. Kasneje jih lahko spremenite v Nastavitvah.")
        intro.setObjectName("DashboardMuted")
        intro.setWordWrap(True)
        card.body.addWidget(intro)

        grid = FormGrid()
        self.company = QLineEdit()
        self.company.setPlaceholderText("Npr. Primer d.o.o.")
        self.company.setMinimumHeight(36)
        self.address = QLineEdit()
        self.address.setPlaceholderText("Ulica, pošta, kraj")
        self.address.setMinimumHeight(36)
        self.tax = QLineEdit()
        self.tax.setPlaceholderText("Davčna številka (neobvezno)")
        self.tax.setMinimumHeight(36)
        self.vat = QDoubleSpinBox()
        self.vat.setRange(0, 100)
        self.vat.setDecimals(2)
        self.vat.setValue(22)
        self.vat.setMinimumHeight(36)
        self.vat_liable = QComboBox()
        self.vat_liable.addItems(["DA", "NE"])
        self.vat_liable.setCurrentText("DA")
        self.vat_liable.setMinimumHeight(36)
        self.currency = QComboBox()
        self.currency.addItems(["EUR", "USD", "CHF", "GBP"])
        self.currency.setMinimumHeight(36)
        self.logo_path = QLineEdit()
        self.logo_path.setReadOnly(True)
        self.logo_path.setPlaceholderText("Ni izbran")
        self.logo_path.setMinimumHeight(36)
        browse = QPushButton("Izberi logotip")
        browse.setObjectName("SecondaryButton")
        browse.setCursor(Qt.PointingHandCursor)
        browse.setMinimumHeight(36)
        browse.clicked.connect(self._pick_logo)

        grid.add("Podjetje", self.company, "Davčna št.", self.tax)
        grid.add("Naslov", self.address)
        grid.add("DDV %", self.vat, "Zavezanec za DDV", self.vat_liable)
        grid.add("Valuta", self.currency)
        grid.add_full("Logotip podjetja", self.logo_path)
        card.body.addLayout(grid.layout)
        card.body.addWidget(browse, 0, Qt.AlignLeft)
        return card

    def _step_user(self) -> QWidget:
        card = EnterpriseCard("DashboardCard")
        card.setObjectName("FirstRunCard")
        intro = QLabel(
            "Ustvarite glavnega skrbnika. To je prvi račun z polnim dostopom do "
            "JU-TAN Office. Uporabniško ime ne sme biti prazno."
        )
        intro.setObjectName("DashboardMuted")
        intro.setWordWrap(True)
        card.body.addWidget(intro)

        grid = FormGrid()
        self.admin = QLineEdit()
        self.admin.setText("")
        self.admin.setPlaceholderText("Uporabniško ime")
        self.admin.setMinimumHeight(36)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("Min. 10 znakov (obvezno)")
        self.password.setMinimumHeight(36)
        self.password2 = QLineEdit()
        self.password2.setEchoMode(QLineEdit.Password)
        self.password2.setPlaceholderText("Potrditev gesla")
        self.password2.setMinimumHeight(36)

        self.show_password = QCheckBox("Prikaži geslo")
        self.show_password.toggled.connect(self._toggle_password_visibility)

        grid.add("Uporabniško ime", self.admin)
        grid.add("Geslo", self.password, "Potrditev gesla", self.password2)
        card.body.addLayout(grid.layout)
        card.body.addWidget(self.show_password)

        hint = QLabel(
            "Geslo se shrani le kot varna zgoščena vrednost. Po zaključku "
            "čarovnika se prijavite s temi podatki."
        )
        hint.setObjectName("DashboardMuted")
        hint.setWordWrap(True)
        card.body.addWidget(hint)
        return card

    def _step_security(self) -> QWidget:
        card = EnterpriseCard("DashboardCard")
        card.setObjectName("FirstRunCard")
        intro = QLabel(
            "Pred nadaljevanjem potrdite priporočila. Ta korak ne spreminja "
            "varnostnih pravil — gre za zavestno potrditev."
        )
        intro.setObjectName("DashboardMuted")
        intro.setWordWrap(True)
        card.body.addWidget(intro)

        self.sec_password = QCheckBox(
            "Geslo skrbnika bom hranil(-a) na varnem mestu (ni deljeno v e-pošti)."
        )
        self.sec_access = QCheckBox(
            "Dostop do delovne postaje z JU-TAN Office je omejen na pooblaščene osebe."
        )
        self.sec_backup = QCheckBox(
            "Razumem, da so varnostne kopije in posodobitve na voljo v Nastavitvah."
        )
        self.sec_updates = QCheckBox(
            "Po prvem zagonu bom preveril(-a) nastavitve podjetja in uporabnikov."
        )
        self._security_checks = (
            self.sec_password,
            self.sec_access,
            self.sec_backup,
            self.sec_updates,
        )
        for box in self._security_checks:
            box.setObjectName("FirstRunCheck")
            card.body.addWidget(box)
        return card

    def _step_license(self) -> QWidget:
        card = EnterpriseCard("DashboardCard")
        card.setObjectName("FirstRunCard")
        title = QLabel("Aktivacija licence")
        title.setObjectName("FirstRunSectionTitle")
        card.body.addWidget(title)

        lead = QLabel(
            "JU-TAN Office uporablja obstoječi licenčni sistem. Ta korak je "
            "le vodič — licenca se tukaj ne aktivira."
        )
        lead.setObjectName("DashboardMuted")
        lead.setWordWrap(True)
        card.body.addWidget(lead)

        guide = QLabel(
            "1. Po prijavi odprite Nastavitve → Licenca.\n"
            "2. Vnesite licenčni ključ v obliki JU-TAN-XXXX-XXXX.\n"
            "3. Za prvo aktivacijo je potrebna internetna povezava.\n"
            "4. Stanje licence, podjetje in obdobje offline grace "
            "preverite na kartici Licenca."
        )
        guide.setObjectName("FirstRunGuide")
        guide.setWordWrap(True)
        card.body.addWidget(guide)

        tip = QLabel(
            "Če ste licenco že aktivirali med namestitvijo, lahko ta korak "
            "preskočite — status se prikaže v nastavitvah."
        )
        tip.setObjectName("DashboardMuted")
        tip.setWordWrap(True)
        card.body.addWidget(tip)
        return card

    def _step_complete(self) -> QWidget:
        card = EnterpriseCard("DashboardCard")
        card.setObjectName("FirstRunCard")

        self.complete_title = QLabel("Pripravljeni na zagon")
        self.complete_title.setObjectName("FirstRunSectionTitle")
        self.complete_title.setAlignment(Qt.AlignCenter)
        card.body.addWidget(self.complete_title)

        self.complete_summary = QLabel()
        self.complete_summary.setObjectName("FirstRunLead")
        self.complete_summary.setWordWrap(True)
        self.complete_summary.setAlignment(Qt.AlignCenter)
        card.body.addWidget(self.complete_summary)

        closing = QLabel(
            "S klikom na »Dokončaj« shranimo podjetje in ustvarimo skrbnika. "
            "Nato sledi prijava — enak tok kot pri obstoječih uporabnikih."
        )
        closing.setObjectName("DashboardMuted")
        closing.setWordWrap(True)
        closing.setAlignment(Qt.AlignCenter)
        card.body.addWidget(closing)
        return card

    # -------------------------------------------------------------- navigation

    def _show_step(self, index: int) -> None:
        self._step = max(STEP_WELCOME, min(STEP_COMPLETE, index))
        self.stack.setCurrentIndex(self._step)
        title, subtitle = _STEP_META[self._step]
        self.set_heading(f"{title} — {subtitle}")
        for i, label in enumerate(self._progress_labels):
            label.setProperty("active", "true" if i == self._step else "false")
            label.setProperty("done", "true" if i < self._step else "false")
            label.style().unpolish(label)
            label.style().polish(label)

        self.btn_back.setEnabled(self._step > STEP_WELCOME)
        if self._step == STEP_COMPLETE:
            self._refresh_completion_summary()
            self.btn_next.setText("Dokončaj")
        elif self._step == STEP_WELCOME:
            self.btn_next.setText("Začni")
        else:
            self.btn_next.setText("Naprej")

        self.btn_next.setDefault(True)
        self.btn_next.setAutoDefault(True)

    def _refresh_completion_summary(self) -> None:
        company = self.company.text().strip() or "—"
        admin = self.admin.text().strip() or "—"
        currency = self.currency.currentText()
        self.complete_summary.setText(
            f"Podjetje: {company}\n"
            f"Skrbnik: {admin}\n"
            f"Valuta: {currency}\n"
            f"Licenca: aktivacija v Nastavitvah (po prijavi)"
        )

    def _back(self) -> None:
        if self._step > STEP_WELCOME:
            self._show_step(self._step - 1)

    def _next(self) -> None:
        if self._step == STEP_COMPLETE:
            self._finish()
            return
        if not self._validate_current_step():
            return
        self._show_step(self._step + 1)

    def _validate_current_step(self) -> bool:
        if self._step == STEP_COMPANY:
            if not self.company.text().strip():
                QMessageBox.warning(self, "Prvi zagon", "Vnesite ime podjetja.")
                self.company.setFocus()
                return False
            tax = self.tax.text().strip()
            if tax:
                from app.core.security import require_vat

                try:
                    self.tax.setText(require_vat(tax))
                except ValueError as exc:
                    QMessageBox.warning(self, "Prvi zagon", str(exc))
                    self.tax.setFocus()
                    return False
            return True

        if self._step == STEP_USER:
            return self._validate_user_fields()

        if self._step == STEP_SECURITY:
            if not all(box.isChecked() for box in self._security_checks):
                QMessageBox.warning(
                    self,
                    "Prvi zagon",
                    "Potrdite vse točke varnostnega kontrolnega seznama.",
                )
                return False
            return True

        return True

    def _validate_user_fields(self) -> bool:
        username = self.admin.text().strip()
        if not username:
            QMessageBox.warning(self, "Prvi zagon", "Vnesite uporabniško ime.")
            self.admin.setFocus()
            return False
        pwd = self.password.text()
        if not pwd:
            QMessageBox.warning(self, "Prvi zagon", "Vnesite geslo.")
            self.password.setFocus()
            return False
        if pwd != self.password2.text():
            QMessageBox.warning(self, "Prvi zagon", "Gesli se ne ujemata.")
            self.password2.setFocus()
            return False
        try:
            hash_password(pwd)
        except ValueError as exc:
            QMessageBox.warning(self, "Prvi zagon", str(exc))
            self.password.setFocus()
            return False
        return True

    def _toggle_password_visibility(self, checked: bool) -> None:
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.password.setEchoMode(mode)
        self.password2.setEchoMode(mode)

    def _load_brand_logo(self) -> None:
        path = resolve_brand_logo()
        if path is not None:
            pix = QPixmap(str(path))
            if not pix.isNull():
                ratio = max(1.0, float(self.devicePixelRatioF() or 1.0))
                target_w = int(200 * ratio)
                scaled = pix.scaledToWidth(target_w, Qt.SmoothTransformation)
                scaled.setDevicePixelRatio(ratio)
                self.logo.setPixmap(scaled)
                self.logo.setText("")
                return
        self.logo.setPixmap(QPixmap())
        self.logo.setText("JU-TAN Office")
        self.logo.setObjectName("LoginBrand")

    def _pick_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Logotip", "", "Slike (*.png *.jpg *.jpeg *.bmp)")
        if not path:
            return
        source = Path(path)
        suffix = source.suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".bmp"}:
            return
        from app.core.security import ensure_inside

        # Never overwrite application brand assets (logo.png / logo_light.png).
        target = ensure_inside(DATA_DIR / f"company_logo{suffix}", DATA_DIR)
        target.write_bytes(source.read_bytes())
        self._logo = str(target)
        self.logo_path.setText(str(target))

    def _finish(self) -> None:
        name = self.company.text().strip()
        if not name:
            QMessageBox.warning(self, "Prvi zagon", "Vnesite ime podjetja.")
            self._show_step(STEP_COMPANY)
            return
        username = self.admin.text().strip()
        if not username:
            QMessageBox.warning(self, "Prvi zagon", "Vnesite uporabniško ime.")
            self._show_step(STEP_USER)
            self.admin.setFocus()
            return
        pwd = self.password.text()
        if not pwd:
            QMessageBox.warning(self, "Prvi zagon", "Vnesite geslo.")
            self._show_step(STEP_USER)
            self.password.setFocus()
            return
        if pwd != self.password2.text():
            QMessageBox.warning(self, "Prvi zagon", "Gesli se ne ujemata.")
            self._show_step(STEP_USER)
            self.password2.setFocus()
            return
        try:
            hash_password(pwd)  # validate policy early
        except ValueError as exc:
            QMessageBox.warning(self, "Prvi zagon", str(exc))
            self._show_step(STEP_USER)
            self.password.setFocus()
            return

        tax = self.tax.text().strip()
        if tax:
            from app.core.security import require_vat

            try:
                tax = require_vat(tax)
            except ValueError as exc:
                QMessageBox.warning(self, "Prvi zagon", str(exc))
                self._show_step(STEP_COMPANY)
                return

        from app.core.user_service import create_first_administrator, users_exist

        try:
            if users_exist():
                QMessageBox.warning(self, "Prvi zagon", "Prvi uporabnik že obstaja.")
                return
            create_first_administrator(username, pwd)
        except (ValueError, PermissionError) as exc:
            QMessageBox.warning(self, "Prvi zagon", str(exc))
            return

        extras = SettingsController().load_extras()
        # SQLite users are the auth source of truth — do not keep competing hash.
        extras["password_hash"] = ""
        extras["administrator"] = username
        extras["role"] = "Administrator"
        extras["account_enabled"] = True
        extras["legacy_auth_migrated"] = True
        SettingsController().save_extras(extras)

        vat = float(self.vat.value())
        from app.utils.vat import vat_liable_int

        company_repository.save(
            name,
            name,
            self.address.text().strip(),
            "",
            "",
            "Slovenija",
            tax,
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            self._logo,
            "RAC",
            "PON",
            1,
            1,
            vat,
            "",
            vat_liable_int(self.vat_liable.currentText()),
        )
        mark_setup_complete(
            administrator=username,
            currency=self.currency.currentText(),
        )
        self.accept()

    def reject(self) -> None:
        from PySide6.QtWidgets import QDialog

        QDialog.reject(self)
