"""System health overview for Settings Center — UI only, reads existing state."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.core.constants import BACKUP_DIR, DATABASE_PATH
from app.core.session import session
from app.services.license_gate import _grace_valid
from app.services.licensing_service import LicenseState
from app.theme.tokens import SPACE_2, SPACE_3
from app.widgets.cards.enterprise_card import EnterpriseCard
from app.widgets.cards.kpi_card import KpiCard


def _display(value: str | None, fallback: str = "—") -> str:
    text = (value or "").strip()
    return text if text else fallback


class SettingsHealthCard(QWidget):
    """Premium health strip: license, database, backups, session."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsHealthCard")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(SPACE_3)

        hero = EnterpriseCard("DashboardCard")
        hero.body.setContentsMargins(20, 18, 20, 18)
        hero.body.setSpacing(10)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(SPACE_2)

        titles = QVBoxLayout()
        titles.setContentsMargins(0, 0, 0, 0)
        titles.setSpacing(2)

        eyebrow = QLabel("SYSTEM HEALTH")
        eyebrow.setObjectName("SettingsHealthEyebrow")

        title = QLabel("Pregled sistema")
        title.setObjectName("SettingsHealthTitle")

        caption = QLabel("Stanje licence, baze, varnostnih kopij in aktivne seje")
        caption.setObjectName("DashboardMuted")
        caption.setWordWrap(True)

        titles.addWidget(eyebrow)
        titles.addWidget(title)
        titles.addWidget(caption)
        header.addLayout(titles, 1)

        self.lbl_summary = QLabel("—")
        self.lbl_summary.setObjectName("SettingsHealthSummary")
        self.lbl_summary.setAlignment(Qt.AlignRight | Qt.AlignTop)
        header.addWidget(self.lbl_summary, 0, Qt.AlignTop)
        hero.body.addLayout(header)
        root.addWidget(hero)

        tiles = QWidget()
        self._tiles = QGridLayout(tiles)
        self._tiles.setContentsMargins(0, 0, 0, 0)
        self._tiles.setHorizontalSpacing(SPACE_3)
        self._tiles.setVerticalSpacing(SPACE_3)

        self.kpi_license = KpiCard("Licenca", "—", "Status")
        self.kpi_database = KpiCard("Baza podatkov", "—", "SQLite")
        self.kpi_backup = KpiCard("Varnostne kopije", "—", "Mapa Backup")
        self.kpi_session = KpiCard("Seja", "—", "Uporabnik")

        self._tiles.addWidget(self.kpi_license, 0, 0)
        self._tiles.addWidget(self.kpi_database, 0, 1)
        self._tiles.addWidget(self.kpi_backup, 0, 2)
        self._tiles.addWidget(self.kpi_session, 0, 3)
        for col in range(4):
            self._tiles.setColumnStretch(col, 1)
        root.addWidget(tiles)

        self._breakpoint = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_tiles(self.width())

    def _layout_tiles(self, width: int) -> None:
        mode = "wide" if width >= 900 else ("medium" if width >= 560 else "narrow")
        if mode == self._breakpoint:
            return
        self._breakpoint = mode

        while self._tiles.count():
            item = self._tiles.takeAt(0)
            if item.widget():
                item.widget().setParent(self._tiles.parentWidget())

        cards = (
            self.kpi_license,
            self.kpi_database,
            self.kpi_backup,
            self.kpi_session,
        )
        if mode == "wide":
            for col, card in enumerate(cards):
                self._tiles.addWidget(card, 0, col)
                self._tiles.setColumnStretch(col, 1)
        elif mode == "medium":
            self._tiles.addWidget(self.kpi_license, 0, 0)
            self._tiles.addWidget(self.kpi_database, 0, 1)
            self._tiles.addWidget(self.kpi_backup, 1, 0)
            self._tiles.addWidget(self.kpi_session, 1, 1)
            self._tiles.setColumnStretch(0, 1)
            self._tiles.setColumnStretch(1, 1)
            self._tiles.setColumnStretch(2, 0)
            self._tiles.setColumnStretch(3, 0)
        else:
            for row, card in enumerate(cards):
                self._tiles.addWidget(card, row, 0)
            self._tiles.setColumnStretch(0, 1)
            for col in range(1, 4):
                self._tiles.setColumnStretch(col, 0)

    def refresh(self, *, about: dict | None = None, appearance: dict | None = None) -> None:
        about = about or {}
        appearance = appearance or {}

        # License
        state = LicenseState.load()
        if state is None:
            self.kpi_license.set_value("Ni aktivirana", "Zahteva aktivacijo")
            license_ok = False
        else:
            status = (state.status or "").strip().lower()
            if status == "active":
                self.kpi_license.set_value("Aktivna", _display(state.company_name, "Podjetje"))
                license_ok = True
            elif _grace_valid(state.grace_until):
                self.kpi_license.set_value("Milostni rok", _display(state.grace_until))
                license_ok = True
            else:
                self.kpi_license.set_value(
                    status.capitalize() if status else "Lokalno",
                    _display(state.company_name, "Licenca"),
                )
                license_ok = bool(status) or bool(state.license_id)

        # Database
        db_path = Path(DATABASE_PATH)
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            self.kpi_database.set_value(f"{size_mb:.1f} MB", db_path.name)
            db_ok = True
        else:
            self.kpi_database.set_value("Manjka", str(db_path.name))
            db_ok = False

        # Backups
        backup_dir = Path(BACKUP_DIR)
        backups = sorted(backup_dir.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True) if backup_dir.exists() else []
        if backups:
            latest = datetime.fromtimestamp(backups[0].stat().st_mtime)
            self.kpi_backup.set_value(str(len(backups)), f"Zadnja: {latest.strftime('%d.%m.%Y %H:%M')}")
            backup_ok = True
        else:
            self.kpi_backup.set_value("0", "Ni varnostnih kopij")
            backup_ok = False

        # Session
        user = _display(getattr(session, "user", None) or getattr(session, "username", None), "—")
        role = _display(getattr(session, "role", None), "—")
        theme = _display((appearance or {}).get("theme"), "light")
        self.kpi_session.set_value(user, f"{role} · tema {theme}")

        version = _display(about.get("version"), "—")
        if license_ok and db_ok:
            summary = "Sistem je pripravljen"
            kind = "ok"
        elif db_ok:
            summary = "Delno — preverite licenco"
            kind = "warn"
        else:
            summary = "Zahteva pozornost"
            kind = "bad"
        if not backup_ok and kind == "ok":
            summary = "Pripravljen · priporočena varnostna kopija"
            kind = "warn"

        self.lbl_summary.setText(f"{summary}\n{version}")
        self.lbl_summary.setProperty("kind", kind)
        style = self.lbl_summary.style()
        if style is not None:
            style.unpolish(self.lbl_summary)
            style.polish(self.lbl_summary)
        self.lbl_summary.update()
