from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import BACKUP_DIR
from app.core.permissions import can, set_identity
from app.core.session import session
from app.core.ui.brand_icons import brand_icon
from app.core.ui.notify import toast
from app.core.ui.sizes import FOOTER_HEIGHT, OUTER_MARGIN
from app.modules.settings.settings_controller import SettingsController
from app.theme.tokens import SPACE_3, SPACE_4
from app.widgets.common.page_chrome import PageHeader
from app.widgets.settings.about_card import AboutCard
from app.widgets.settings.appearance_card import AppearanceCard
from app.widgets.settings.backup_card import BackupCard
from app.widgets.settings.fresh_zone_card import FreshZoneCard
from app.widgets.settings.license_card import LicenseCard
from app.widgets.settings.numbering_card import NumberingCard
from app.widgets.settings.pdf_card import PdfCard
from app.widgets.settings.privacy_card import PrivacyCard
from app.widgets.settings.security_card import SecurityCard
from app.widgets.settings.settings_health_card import SettingsHealthCard
from app.widgets.settings.settings_nav import SettingsNav
from app.widgets.settings.settings_section import SettingsSectionHeader
from app.widgets.settings.travel_settings_card import TravelSettingsCard
from app.widgets.settings.update_card import UpdateCard
from app.widgets.settings.users_card import UsersCard


class SettingsPage(QWidget):
    """Settings Center — shell paints first; data loads after first show."""

    save_settings = Signal()
    reset_settings = Signal()
    theme_changed = Signal(str)
    backup_requested = Signal()
    restore_requested = Signal()
    logo_changed = Signal(str)

    # LazyPage.refresh skips until first deferred load completes.
    defers_initial_refresh = True

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("SettingsPage")
        self.controller = SettingsController()
        self._data_loaded = False
        self._dirty = False
        self._baseline: dict | None = None
        self._applied_appearance: dict = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        chrome = QWidget()
        chrome.setObjectName("SettingsChrome")
        chrome_layout = QVBoxLayout(chrome)
        chrome_layout.setContentsMargins(SPACE_4, SPACE_4, SPACE_4, SPACE_3)
        chrome_layout.setSpacing(SPACE_3)

        self.header = PageHeader(
            "Nastavitve",
            "Upravljajte dokumente, dostop, varnostne kopije in sistem.",
        )
        chrome_layout.addWidget(self.header)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(SPACE_3)

        self.nav = SettingsNav()
        self.nav.category_selected.connect(self._on_category)
        body.addWidget(self.nav, 0)

        scroll = QScrollArea()
        scroll.setObjectName("SettingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll = scroll
        self._scroll_anim: QPropertyAnimation | None = None
        self._nav_programmatic = False

        self._canvas = QWidget()
        self._canvas.setObjectName("SettingsCanvas")
        self._grid = QGridLayout(self._canvas)
        self._grid.setContentsMargins(SPACE_3, SPACE_3, SPACE_4, SPACE_4)
        self._grid.setHorizontalSpacing(SPACE_3)
        self._grid.setVerticalSpacing(SPACE_3)

        self.health_card = SettingsHealthCard()
        self.section_overview = SettingsSectionHeader(
            "Pregled sistema",
            "Hitri status licence, baze, varnostnih kopij in seje.",
        )
        self.section_documents = SettingsSectionHeader(
            "Dokumenti",
            "PDF izvoz, Excel in številčenje dokumentov.",
        )
        self.section_appearance = SettingsSectionHeader(
            "Videz",
            "Tema, poudarek, tipografija in zaokrožitve.",
        )
        self.section_modules = SettingsSectionHeader(
            "Moduli",
            "Nastavitve potnih nalogov in modulov.",
        )
        self.section_security = SettingsSectionHeader(
            "Varnost in seje",
            "Vloga, časovna omejitev in geslo.",
        )
        self.section_users = SettingsSectionHeader(
            "Uporabniki in pravice",
            "Upravljanje računov in dovoljenj.",
        )
        self.section_backup = SettingsSectionHeader(
            "Varnostne kopije",
            "Backup baze in uvoz/izvoz nastavitev.",
        )
        self.section_license = SettingsSectionHeader(
            "Licenca",
            "Paket, podjetje, veljavnost in preverjanje licence.",
        )
        self.section_updates = SettingsSectionHeader(
            "Posodobitve",
            "Trenutna verzija in kanal posodobitev.",
        )
        self.section_privacy = SettingsSectionHeader(
            "Zasebnost",
            "GDPR informacije, politika zasebnosti in upravljanje podatkov.",
        )
        self.section_about = SettingsSectionHeader(
            "O aplikaciji",
            "JU-TAN blagovna znamka, verzija, podjetje in podpora.",
        )
        self.section_danger = SettingsSectionHeader(
            "Nevarno območje",
            "Destruktivna dejanja — samo za administratorja.",
        )

        self.numbering_card = NumberingCard()
        self.appearance_card = AppearanceCard()
        self.pdf_card = PdfCard()
        self.backup_card = BackupCard()
        self.security_card = SecurityCard()
        self.users_card = UsersCard()
        self.fresh_zone_card = FreshZoneCard()
        self.license_card = LicenseCard()
        self.update_card = UpdateCard()
        self.privacy_card = PrivacyCard()
        self.about_card = AboutCard()
        self.travel_card = TravelSettingsCard()

        # Stable section anchors — one nav key per content section.
        self._anchors: dict[str, QWidget] = {
            "overview": self.section_overview,
            "documents": self.section_documents,
            "appearance": self.section_appearance,
            "modules": self.section_modules,
            "security": self.section_security,
            "users": self.section_users,
            "backup": self.section_backup,
            "license": self.section_license,
            "updates": self.section_updates,
            "privacy": self.section_privacy,
            "about": self.section_about,
            "danger": self.section_danger,
        }
        for key, widget in self._anchors.items():
            widget.setProperty("settingsAnchor", key)

        scroll.setWidget(self._canvas)
        scroll.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)
        body.addWidget(scroll, 1)
        chrome_layout.addLayout(body, 1)
        outer.addWidget(chrome, 1)

        footer = QWidget()
        footer.setObjectName("DialogFooter")
        footer.setFixedHeight(FOOTER_HEIGHT)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(OUTER_MARGIN, 0, OUTER_MARGIN, 0)
        footer_layout.setSpacing(SPACE_3)
        footer_layout.addStretch(1)
        self.btn_cancel = QPushButton("Prekliči")
        self.btn_cancel.setObjectName("SecondaryButton")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setMinimumHeight(36)
        self.btn_save = QPushButton("Shrani")
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setMinimumHeight(36)
        self.btn_save.setIcon(brand_icon("save", color="#FFFFFF", size=14))
        footer_layout.addWidget(self.btn_cancel)
        footer_layout.addWidget(self.btn_save)
        outer.addWidget(footer)

        self.appearance_card.theme_changed.connect(self._on_theme)
        self.appearance_card.changed.connect(self._apply_appearance)
        self.backup_card.backup_requested.connect(self._backup)
        self.backup_card.restore_requested.connect(self._restore)
        self.backup_card.export_requested.connect(self._export_settings)
        self.backup_card.import_requested.connect(self._import_settings)
        self.backup_card.folder_requested.connect(self._open_backup_folder)
        self.security_card.password_clicked.connect(self._change_password)
        self.security_card.logout_clicked.connect(self._logout)
        self.fresh_zone_card.fresh_completed.connect(self._on_fresh_completed)
        self.numbering_card.changed.connect(self._mark_dirty)
        self.security_card.changed.connect(self._mark_dirty)
        self.travel_card.changed.connect(self._mark_dirty)
        self.pdf_card.changed.connect(self._mark_dirty)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._reset)

        self._breakpoint = None
        self._place_widgets(1400)
        self._sync_nav_visibility()
        self._set_dirty(False)
        from app.core.ui.window_state import remember_layout

        remember_layout(self, "page.settings")
        # Theme is applied at process startup (before MainWindow). Do NOT re-apply
        # here — that made opening Nastavitve the first moment DARK appeared.
        # Heavy card data loads after first paint via showEvent → defer(refresh).

    def showEvent(self, event):
        super().showEvent(event)
        if not self._data_loaded:
            from app.core.async_load import defer

            defer(self.refresh)

    def hideEvent(self, event):
        if self._scroll_anim is not None:
            self._scroll_anim.stop()
            self._scroll_anim = None
            self._nav_programmatic = False
        super().hideEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place_widgets(self.width())
        self._sync_bottom_spacer()

    def _sync_bottom_spacer(self) -> None:
        """Keep enough trailing space so every section can pin to the viewport top."""
        if not hasattr(self, "_bottom_spacer"):
            return
        spacer_h = max(240, self._scroll.viewport().height() - 120)
        if self._bottom_spacer.height() != spacer_h:
            self._bottom_spacer.setMinimumHeight(spacer_h)
            self._bottom_spacer.setFixedHeight(spacer_h)

    def _place_widgets(self, width: int) -> None:
        # Account for nav rail (~220) + chrome margins when choosing density.
        content_width = max(320, width - 260)
        mode = "wide" if content_width >= 980 else "narrow"
        if mode == self._breakpoint:
            return
        self._breakpoint = mode

        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().setParent(self._canvas)

        self.nav.setVisible(width >= 720)
        self.section_modules.show()

        r = 0
        self._grid.addWidget(self.section_overview, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.health_card, r, 0, 1, 2)
        r += 1

        self._grid.addWidget(self.section_documents, r, 0, 1, 2)
        r += 1
        if mode == "wide":
            self._grid.addWidget(self.pdf_card, r, 0)
            self._grid.addWidget(self.numbering_card, r, 1)
            r += 1
            self._grid.addWidget(self.section_appearance, r, 0, 1, 2)
            r += 1
            self._grid.addWidget(self.appearance_card, r, 0)
            self._grid.addWidget(self.travel_card, r, 1)
            r += 1
            # Keep modules header as a nav anchor without taking vertical space.
            self.section_modules.hide()
        else:
            self._grid.addWidget(self.pdf_card, r, 0, 1, 2)
            r += 1
            self._grid.addWidget(self.numbering_card, r, 0, 1, 2)
            r += 1
            self._grid.addWidget(self.section_appearance, r, 0, 1, 2)
            r += 1
            self._grid.addWidget(self.appearance_card, r, 0, 1, 2)
            r += 1
            self._grid.addWidget(self.section_modules, r, 0, 1, 2)
            r += 1
            self._grid.addWidget(self.travel_card, r, 0, 1, 2)
            r += 1

        self._grid.addWidget(self.section_security, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.security_card, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.section_users, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.users_card, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.section_backup, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.backup_card, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.section_license, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.license_card, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.section_updates, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.update_card, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.section_privacy, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.privacy_card, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.section_about, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.about_card, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.section_danger, r, 0, 1, 2)
        r += 1
        self._grid.addWidget(self.fresh_zone_card, r, 0, 1, 2)
        r += 1

        # Spacer so the last sections can scroll flush to the top of the viewport.
        if not hasattr(self, "_bottom_spacer"):
            self._bottom_spacer = QWidget()
            self._bottom_spacer.setObjectName("SettingsBottomSpacer")
        self._grid.addWidget(self._bottom_spacer, r, 0, 1, 2)
        self._sync_bottom_spacer()

        self._grid.setColumnStretch(0, 1)
        self._grid.setColumnStretch(1, 1 if mode == "wide" else 0)

    def _anchor_for(self, key: str) -> QWidget | None:
        """Resolve the content widget for a SettingsNav key."""
        # In wide layout the modules header is hidden; land on the travel card.
        if key == "modules" and not self.section_modules.isVisible():
            return self.travel_card
        return self._anchors.get(key)

    def _on_category(self, key: str) -> None:
        target = self._anchor_for(key)
        if target is None:
            return
        self._scroll_to_section(target, smooth=True)

    def _section_scroll_value(self, target: QWidget) -> int:
        """Scrollbar value that pins ``target`` near the top of the viewport."""
        margin = 12
        y = target.mapTo(self._canvas, target.rect().topLeft()).y()
        bar = self._scroll.verticalScrollBar()
        return max(0, min(y - margin, bar.maximum()))

    def _scroll_to_section(self, target: QWidget, *, smooth: bool = True) -> None:
        """Scroll so the section header sits at the top (not merely on-screen)."""
        self._sync_bottom_spacer()
        bar = self._scroll.verticalScrollBar()
        end_value = self._section_scroll_value(target)
        if abs(bar.value() - end_value) <= 1:
            return

        if self._scroll_anim is not None:
            self._scroll_anim.stop()
            self._scroll_anim = None

        if not smooth:
            self._nav_programmatic = True
            try:
                bar.setValue(end_value)
            finally:
                self._nav_programmatic = False
            return

        self._nav_programmatic = True
        anim = QPropertyAnimation(bar, b"value", self)
        anim.setDuration(280)
        anim.setStartValue(bar.value())
        anim.setEndValue(end_value)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def _finish() -> None:
            self._nav_programmatic = False
            self._scroll_anim = None

        anim.finished.connect(_finish)
        self._scroll_anim = anim
        anim.start()

    def _on_scroll_changed(self, _value: int = 0) -> None:
        if self._nav_programmatic:
            return
        self._sync_nav_from_scroll()

    def _sync_nav_from_scroll(self) -> None:
        """Keep the nav highlight aligned with the section currently in view."""
        top = self._scroll.verticalScrollBar().value()
        band = 96
        best_key = "overview"
        best_y = -10_000
        for key in self._anchors:
            widget = self._anchor_for(key)
            if widget is None or not widget.isVisible():
                continue
            y = widget.mapTo(self._canvas, widget.rect().topLeft()).y()
            if y <= top + band and y >= best_y:
                best_y = y
                best_key = key
        if self.nav._active != best_key:
            self.nav.select(best_key)

    def refresh(self):
        bundle = self.controller.load_bundle()
        extras = bundle["extras"]
        self.numbering_card.set_values(extras.get("numbering", {}))
        self.appearance_card.set_values(extras.get("appearance", {}))
        self.pdf_card.set_values(extras.get("pdf", {}))
        self.pdf_card.set_excel(extras.get("excel", {}))
        self.travel_card.set_values(extras.get("travel_orders", {}))
        self.security_card.set_values(extras)
        # Re-evaluate RBAC-gated cards from current effective permissions (no restart).
        self.users_card.refresh()
        self.fresh_zone_card.refresh()
        self.license_card.refresh()
        self.update_card.refresh()
        about = self.controller.about()
        self.about_card.set_values(about)
        self.health_card.refresh(
            about=about,
            appearance=extras.get("appearance", {}),
        )
        self._sync_nav_visibility()
        self._applied_appearance = dict(self.appearance_card.values())
        self._baseline = self._confirmable_extras()
        self._data_loaded = True
        self._set_dirty(False)

    def _sync_nav_visibility(self) -> None:
        users_ok = can("users")
        fresh_ok = can("fresh")
        self.nav.set_category_visible("users", users_ok)
        self.nav.set_category_visible("danger", fresh_ok)
        self.section_users.setVisible(users_ok)
        self.section_danger.setVisible(fresh_ok)

    def extras(self) -> dict:
        return {
            "numbering": self.numbering_card.values(),
            "appearance": self.appearance_card.values(),
            "pdf": self.pdf_card.values(),
            "excel": self.pdf_card.excel_values(),
            "travel_orders": self.travel_card.values(),
            **self.security_card.values(),
        }

    def _confirmable_extras(self) -> dict:
        """Settings that require explicit Save (appearance auto-saves separately)."""
        data = self.extras()
        data.pop("appearance", None)
        return data

    def _mark_dirty(self, *_args) -> None:
        if not self._data_loaded:
            return
        dirty = self._confirmable_extras() != (self._baseline or {})
        self._set_dirty(dirty)

    def _set_dirty(self, dirty: bool) -> None:
        self._dirty = bool(dirty)
        self.btn_save.setEnabled(self._dirty)
        self.btn_cancel.setEnabled(self._dirty)

    def is_dirty(self) -> bool:
        return bool(self._dirty)

    def confirm_leave(self) -> bool:
        """Return False to abort navigation when unsaved confirmable changes exist."""
        if not self._dirty:
            return True
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Neshranjene nastavitve")
        box.setText("Imate neshranjene spremembe nastavitev.")
        box.setInformativeText("Želite shraniti spremembe pred odhodom?")
        save_btn = box.addButton("Shrani", QMessageBox.AcceptRole)
        discard_btn = box.addButton("Zavrzi", QMessageBox.DestructiveRole)
        cancel_btn = box.addButton("Prekliči", QMessageBox.RejectRole)
        box.setDefaultButton(save_btn)
        box.exec()
        clicked = box.clickedButton()
        if clicked is save_btn:
            self._save()
            return not self._dirty
        if clicked is discard_btn:
            self._reset()
            return True
        if clicked is cancel_btn:
            return False
        return False

    def _save(self):
        from app.core.permissions import can, current_role

        extras = self.extras()
        requested_role = self.security_card.role.currentText()
        if requested_role != current_role() and not can("users"):
            QMessageBox.warning(
                self,
                "Vloga",
                "Sprememba vloge zahteva dovoljenje Administratorja.",
            )
            extras["role"] = current_role()
            self.security_card.role.setCurrentText(current_role())
        appearance_before = dict(getattr(self, "_applied_appearance", {}) or {})
        self.controller.save_extras(extras)
        try:
            self.pdf_card.save_branding()
        except Exception as exc:
            from app.core.logger import logger

            logger.error("Document branding save failed: %s", exc)
        if can("users"):
            set_identity(role=requested_role)
        timeout_sec = max(5, int(self.security_card.timeout.value())) * 60
        session.timeout_sec = timeout_sec
        try:
            from app.core.idle_guard import get_idle_guard

            guard = get_idle_guard()
            if guard is not None:
                guard.set_timeout_sec(timeout_sec)
        except Exception:
            pass
        sidebar = getattr(self.window(), "sidebar", None)
        if sidebar is not None and hasattr(sidebar, "apply_role"):
            sidebar.apply_role()
        # Re-apply theme only when appearance actually changed — full
        # setStyleSheet on every company save was a freeze amplifier.
        if self.appearance_card.values() != appearance_before:
            self._apply_appearance()
        self._baseline = self._confirmable_extras()
        self._set_dirty(False)
        self.save_settings.emit()
        toast(self, "Nastavitve so shranjene.")

    def _reset(self):
        self.refresh()
        self.reset_settings.emit()

    def _on_theme(self, theme: str):
        # AppearanceCard._emit_theme also emits changed → _apply_appearance.
        # Do not apply twice (double setStyleSheet freezes complex dialogs).
        self.theme_changed.emit(theme)

    def _apply_appearance(self):
        extras = self.controller.load_extras()
        appearance = self.appearance_card.values()
        extras["appearance"] = appearance
        self.controller.save_extras(extras)
        if appearance == getattr(self, "_applied_appearance", None):
            return
        app = QApplication.instance()
        if app is not None:
            self.controller.apply_appearance(app)
            self._applied_appearance = dict(appearance)
            # Refresh nav icons for new theme colors.
            if hasattr(self.nav, "_refresh_icons"):
                self.nav._refresh_icons()

    def _backup(self):
        self.backup_requested.emit()
        try:
            self.controller.backup_database()
            toast(self, "Varnostna kopija uspešna")
            self.health_card.refresh(
                about=self.controller.about(),
                appearance=self.appearance_card.values(),
            )
        except Exception as exc:
            from app.core.errors import handle_error

            handle_error(exc, context="backup", parent=self)

    def _restore(self):
        self.restore_requested.emit()
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Restore Database",
            str(BACKUP_DIR),
            "SQLite (*.db)",
        )
        if not path:
            return
        try:
            self.controller.restore_database(Path(path))
            QMessageBox.information(
                self,
                "Restore",
                "Baza je obnovljena. Ponovno zaženite aplikacijo.",
            )
        except Exception as exc:
            from app.core.errors import handle_error

            handle_error(exc, context="restore", parent=self)

    def _export_settings(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Settings",
            str(BACKUP_DIR / "settings.json"),
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            self.controller.export_settings(Path(path))
            toast(self, "Nastavitve so izvožene.")
        except Exception as exc:
            from app.core.errors import handle_error

            handle_error(exc, context="settings_export", parent=self)

    def _import_settings(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Settings",
            str(BACKUP_DIR),
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            extras = self.controller.import_settings(Path(path))
            self.numbering_card.set_values(extras.get("numbering", {}))
            self.appearance_card.set_values(extras.get("appearance", {}))
            self.pdf_card.set_values(extras.get("pdf", {}))
            self.travel_card.set_values(extras.get("travel_orders", {}))
            self.security_card.set_values(extras)
            self._apply_appearance()
            self._baseline = self._confirmable_extras()
            self._set_dirty(False)
            toast(self, "Nastavitve so uvožene.")
        except Exception as exc:
            from app.core.errors import handle_error

            handle_error(exc, context="settings_import", parent=self)

    def _change_password(self):
        try:
            self.controller.change_password(
                self.security_card.old.text(),
                self.security_card.new.text(),
            )
            self.security_card.old.clear()
            self.security_card.new.clear()
            toast(self, "Geslo je spremenjeno.")
        except Exception as exc:
            QMessageBox.warning(self, "Geslo", str(exc))

    def _logout(self):
        """Terminate the authenticated session and return to the login screen.

        Clears session, disables MainWindow, and requires username + password
        again. Cancel/close on the login dialog exits the application safely.
        """
        from app.core.auth_gate import logout_requires_reauth
        from app.windows.unlock_dialog import UnlockDialog
        from PySide6.QtWidgets import QDialog

        session.logout()
        extras = self.controller.load_extras()
        main = self.window()
        if main is not None:
            main.setEnabled(False)
        try:
            if not logout_requires_reauth(extras):
                # Credentials missing (should not happen after mandatory auth) —
                # exit rather than leaving an authenticated MainWindow open.
                QApplication.quit()
                return
            dlg = UnlockDialog(main)
            if dlg.exec() != QDialog.Accepted:
                QApplication.quit()
                return
        finally:
            if main is not None:
                main.setEnabled(True)
        sidebar = getattr(main, "sidebar", None)
        if sidebar is not None and hasattr(sidebar, "apply_role"):
            sidebar.apply_role()
        toolbar = getattr(main, "toolbar", None)
        stack = getattr(main, "stack", None)
        if toolbar is not None and stack is not None and hasattr(toolbar, "set_context"):
            toolbar.set_context(stack.currentIndex())
        bar = main.statusBar() if main is not None and hasattr(main, "statusBar") else None
        if bar is not None and hasattr(bar, "refresh"):
            bar.refresh()
        # New session may have different users/fresh rights — update without restart.
        if hasattr(self, "refresh"):
            self.refresh()

    def _on_fresh_completed(self, _backup_path) -> None:
        """Fresh reset finished; UI promised process exit after confirmation."""
        QApplication.quit()

    def _open_backup_folder(self):
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(BACKUP_DIR)))
