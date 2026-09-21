from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, qVersion
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from app.core.config_guard import migrate, stamp, valid
from app.core.constants import APP_AUTHOR, APP_BUILD, APP_CHANNEL, APP_NAME, APP_VERSION, BACKUP_DIR, DATABASE_PATH, DATA_DIR, EXPORT_DIR
from app.core.errors import handle_error
from app.core.logger import logger
from app.core.permissions import audit, require
from app.core.security import parse_json_object, write_json_atomic
from app.database.company_repository import company_repository
from app.theme import theme_manager
from app.theme.colors import ThemeMode
from app.theme.fonts import apply_fonts

SETTINGS_PATH = DATA_DIR / "settings.json"

ACCENTS = {
    "blue": ("#2563EB", "#1D4ED8"),
    "green": ("#059669", "#047857"),
    "orange": ("#D97706", "#B45309"),
}

FONT_POINTS = {"small": 9, "normal": 10, "large": 12}

RADII = {
    "small": ("8px", "6px"),
    "medium": ("12px", "8px"),
    "large": ("16px", "10px"),
}

DOC_DEFAULTS = {
    "invoice": {"prefix": "RAC", "start": 1, "length": 6, "yearly_reset": True},
    "offer": {"prefix": "PON", "start": 1, "length": 6, "yearly_reset": True},
    "order": {"prefix": "NAR", "start": 1, "length": 6, "yearly_reset": True},
    "delivery": {"prefix": "DOB", "start": 1, "length": 6, "yearly_reset": True},
}


def default_settings() -> dict:
    return {
        "swift": "",
        "travel_orders": {"mileage_rate": 0.0, "domestic_per_diem": 0.0},
        "numbering": {key: dict(value) for key, value in DOC_DEFAULTS.items()},
        "appearance": {
            "theme": "light",
            "accent": "green",
            "font_size": "normal",
            "radius": "medium",
        },
        "pdf": {
            "logo": True,
            "signature": True,
            "stamp": True,
            "vat": True,
            "discounts": True,
            "notes": True,
            "folder": str(DATA_DIR),
            "footer": (
                "Hvala za vaše zaupanje. "
                "Trudimo se, da za vas vedno poiščemo najboljše rešitve."
            ),
            "signature_path": "",
            "stamp_path": "",
            "payment_method": "Nakazilo",
        },
        "excel": {
            "export_folder": str(EXPORT_DIR),
            "import_folder": str(DATA_DIR),
        },
        "setup_complete": False,
        "administrator": "Administrator",
        "currency": "EUR",
        "database_version": 1,
        "role": "Administrator",
        "session_timeout_min": 30,
        "remember_user": True,
        "password_hash": "",
        "account_enabled": True,
        "secrets_blob": "",
        "config_version": 1,
    }


class SettingsController:

    def load_bundle(self) -> dict:
        extras = self.load_extras()
        company = company_repository.get_company()
        numbering = extras["numbering"]
        if company:
            if company[16]:
                numbering["invoice"]["prefix"] = company[16]
            if company[18] is not None:
                numbering["invoice"]["start"] = int(company[18] or 1)
            if company[17]:
                numbering["offer"]["prefix"] = company[17]
            if company[19] is not None:
                numbering["offer"]["start"] = int(company[19] or 1)
        return {"company": company, "extras": extras}

    def load_extras(self) -> dict:
        data = default_settings()
        if SETTINGS_PATH.exists():
            try:
                loaded = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                if not isinstance(loaded, dict):
                    raise ValueError("Poškodovane nastavitve.")
                if loaded.get("_checksum") and not valid(loaded):
                    logger.warning("Checksum nastavitev se ne ujema.")
                data = migrate(loaded, default_settings())
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                handle_error(
                    exc,
                    context="settings-load",
                    recover=lambda: write_json_atomic(SETTINGS_PATH, stamp(default_settings())),
                )
                data = default_settings()
        return data

    def save_extras(self, extras: dict) -> None:
        require("settings")
        self._write_extras(extras, audit_event=True)

    def save_extras_unrestricted(self, extras: dict) -> None:
        """Bootstrap/setup writes — no RBAC gate (first-run, schema bump)."""
        self._write_extras(extras, audit_event=False)

    def _write_extras(self, extras: dict, *, audit_event: bool) -> None:
        current = {}
        if SETTINGS_PATH.exists():
            try:
                current = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                if not isinstance(current, dict):
                    current = {}
            except (OSError, json.JSONDecodeError):
                current = {}
        merged = dict(current)
        merged.update(extras or {})
        for key in ("password_hash", "secrets_blob"):
            if not merged.get(key) and current.get(key):
                merged[key] = current[key]
        from app.core.secrets import SECRET_KEYS, seal

        secret_plain = {key: merged.pop(key) for key in SECRET_KEYS if key in merged}
        if secret_plain:
            existing = {}
            try:
                from app.core.secrets import reveal
                existing = reveal(merged.get("secrets_blob") or "")
            except Exception:
                existing = {}
            existing.update(secret_plain)
            merged["secrets_blob"] = seal(existing)
        write_json_atomic(SETTINGS_PATH, stamp(merged))
        if audit_event:
            audit("settings", "save")

    def change_password(self, old: str, new: str) -> None:
        require("users")
        from app.core.passwords import hash_password, verify_password

        extras = self.load_extras()
        stored = extras.get("password_hash") or ""
        if stored and not verify_password(old, stored):
            raise PermissionError("Trenutno geslo ni pravilno.")
        extras["password_hash"] = hash_password(new)
        self.save_extras(extras)
        audit("settings", "change-password")

    def secrets(self) -> dict:
        from app.core.secrets import reveal

        extras = self.load_extras()
        try:
            return reveal(extras.get("secrets_blob") or "")
        except Exception:
            return {}

    def save_bundle(self, company_values: dict, extras: dict) -> None:
        current = company_repository.get_company()
        logo = company_values.get("logo")
        if logo is None:
            logo = current[15] if current else ""
        notes = current[21] if current else ""
        vat = current[20] if current else 22
        legal = company_values.get("legal_name") or (
            current[2] if current else company_values.get("name", "")
        )
        bank = current[10] if current else ""
        numbering = extras.get("numbering", DOC_DEFAULTS)
        from app.utils.vat import vat_liable_int

        # Never lower live document counters — settings "start" previously overwrote
        # company.invoice_counter and caused UNIQUE failures / freeze on save.
        live_invoice = int(current[18]) if current and current[18] is not None else 1
        live_offer = int(current[19]) if current and current[19] is not None else 1
        want_invoice = int(numbering["invoice"]["start"])
        want_offer = int(numbering["offer"]["start"])
        try:
            from app.database.invoice_repository import invoice_repository

            # Heal against existing rows before persisting settings.
            invoice_repository.get_next_number()
            refreshed = company_repository.get_company()
            if refreshed and refreshed[18] is not None:
                live_invoice = max(live_invoice, int(refreshed[18]))
        except Exception:
            pass
        invoice_counter = max(want_invoice, live_invoice)
        offer_counter = max(want_offer, live_offer)
        numbering["invoice"]["start"] = invoice_counter
        numbering["offer"]["start"] = offer_counter
        extras["numbering"] = numbering

        if "vat_liable" in company_values:
            vat_liable = vat_liable_int(company_values.get("vat_liable"))
        elif current and len(current) > 22:
            vat_liable = vat_liable_int(current[22])
        else:
            vat_liable = 1
        company_repository.save(
            company_values.get("name", ""),
            legal,
            company_values.get("address", ""),
            company_values.get("postal_code", ""),
            company_values.get("city", ""),
            company_values.get("country", ""),
            company_values.get("tax_number", ""),
            company_values.get("registration_number", ""),
            company_values.get("iban", ""),
            bank,
            company_values.get("email", ""),
            company_values.get("website", ""),
            company_values.get("phone", ""),
            company_values.get("mobile", ""),
            logo or "",
            numbering["invoice"]["prefix"],
            numbering["offer"]["prefix"],
            invoice_counter,
            offer_counter,
            vat if vat is not None else 22,
            notes or "",
            vat_liable,
        )
        self.save_extras(extras)

    def apply_appearance(self, app: QApplication | None = None) -> str:
        extras = self.load_extras()
        appearance = extras["appearance"]
        app = app or QApplication.instance()
        mode = self.resolve_theme(appearance.get("theme", "light"))
        accent = appearance.get("accent", "green")
        radius = appearance.get("radius", "medium")
        font_key = appearance.get("font_size", "normal")
        primary, hover = ACCENTS.get(accent, ACCENTS["green"])
        card, control = RADII.get(radius, RADII["medium"])
        applied = theme_manager.apply(
            app,
            mode,
            accent_primary=primary,
            accent_hover=hover,
            card_radius=card,
            control_radius=control,
        )
        if not applied:
            # Modal dialog open — stylesheet deferred; skip icon/titlebar thrash too.
            return mode.value
        apply_fonts(app, FONT_POINTS.get(font_key, 10))
        try:
            from app.core.ui.app_identity import sync_titlebar_for_app
            from app.core.ui.brand_icons import clear_icon_cache
            from app.widgets.navigation.sidebar_header import refresh_brand_logos

            clear_icon_cache()
            sync_titlebar_for_app(mode)
            # Live LIGHT↔DARK brand logo swap (sidebar) without restart.
            refresh_brand_logos()
        except Exception:
            pass
        return mode.value

    def resolve_theme(self, preference: str) -> ThemeMode:
        if preference == "dark":
            return ThemeMode.DARK
        if preference == "auto":
            try:
                scheme = QGuiApplication.styleHints().colorScheme()
                if scheme == Qt.ColorScheme.Dark:
                    return ThemeMode.DARK
            except Exception:
                pass
        return ThemeMode.LIGHT

    def preview_number(self, prefix: str, start: int, length: int) -> str:
        year = datetime.now().year
        pad = max(3, min(int(length), 8))
        number = max(1, int(start))
        clean = (prefix or "DOC").strip() or "DOC"
        return f"{clean}-{year}-{number:0{pad}d}"

    def backup_database(self) -> Path:
        require("backup")
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = BACKUP_DIR / f"ju_tan-{stamp}.db"
        source = sqlite3.connect(DATABASE_PATH)
        dest = sqlite3.connect(target)
        try:
            source.backup(dest)
        finally:
            dest.close()
            source.close()
        audit("backup", str(target))
        from app.core.db_guard import verify_backup
        if not verify_backup(target):
            raise ValueError("Varnostna kopija ni prestala preverjanja.")
        return target

    def restore_database(self, source: Path) -> None:
        require("backup")
        check = sqlite3.connect(source)
        try:
            row = check.execute("PRAGMA integrity_check").fetchone()
            if not row or row[0] != "ok":
                raise ValueError("Varnostna kopija ni celovita.")
        finally:
            check.close()
        from app.database.database import db
        db.dispose()
        dest = sqlite3.connect(DATABASE_PATH)
        src = sqlite3.connect(source)
        try:
            src.backup(dest)
        finally:
            src.close()
            dest.close()
        audit("restore", str(source))

    def export_settings(self, target: Path) -> None:
        require("export")
        extras = self.load_extras()
        redacted = {
            key: value
            for key, value in extras.items()
            if key not in ("password_hash", "secrets_blob")
        }
        redacted["password_configured"] = bool(extras.get("password_hash"))
        redacted["secrets_configured"] = bool(extras.get("secrets_blob"))
        target.write_text(
            json.dumps(redacted, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        audit("export", str(target))

    def import_settings(self, source: Path) -> dict:
        loaded = parse_json_object(source.read_text(encoding="utf-8"))
        loaded.pop("password_hash", None)
        loaded.pop("secrets_blob", None)
        loaded.pop("password_configured", None)
        loaded.pop("secrets_configured", None)
        extras = self._merge(default_settings(), loaded)
        # Preserve existing credentials — import never overwrites secrets.
        current = self.load_extras()
        extras["password_hash"] = current.get("password_hash") or ""
        extras["secrets_blob"] = current.get("secrets_blob") or ""
        self.save_extras(extras)
        return extras

    def about(self) -> dict:
        return {
            "app": APP_NAME,
            "edition": f"Enterprise {APP_CHANNEL}",
            "version": f"{APP_VERSION} {APP_CHANNEL}",
            "python": sys.version.split()[0],
            "qt": qVersion(),
            "sqlite": sqlite3.sqlite_version,
            "build": f"2026-09-12 {APP_BUILD}",
            "copyright": f"© 2026 {APP_AUTHOR}",
            "name": APP_NAME,
            "company": APP_AUTHOR,
            "support": "support@ju-tan.com",
            "website": "www.ju-tan.com",
        }

    @staticmethod
    def _merge(base: dict, incoming: dict) -> dict:
        for key, value in incoming.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                base[key] = SettingsController._merge(base[key], value)
            else:
                base[key] = value
        return base
