"""Compact system health widget for the dashboard — reads existing state only."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.core.constants import BACKUP_DIR, DATABASE_PATH
from app.core.session import session
from app.theme.tokens import SPACE_1, SPACE_2
from app.widgets.cards.enterprise_card import EnterpriseCard


def _display(value: str | None, fallback: str = "—") -> str:
    text = (value or "").strip()
    return text if text else fallback


class _HealthRow(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(SPACE_2)

        self.dot = QLabel("●")
        self.dot.setObjectName("DashboardHealthDot")
        self.dot.setFixedWidth(14)

        self.key = QLabel(label)
        self.key.setObjectName("DashboardMuted")

        self.value = QLabel("—")
        self.value.setObjectName("DashboardHealthValue")
        self.value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(self.dot, 0)
        layout.addWidget(self.key, 0)
        layout.addStretch(1)
        layout.addWidget(self.value, 1)

    def set_status(self, value: str, *, kind: str = "ok") -> None:
        self.value.setText(value)
        self.dot.setProperty("kind", kind)
        self.value.setProperty("kind", kind)
        for widget in (self.dot, self.value):
            style = widget.style()
            if style is not None:
                style.unpolish(widget)
                style.polish(widget)
            widget.update()


class DashboardHealthCard(EnterpriseCard):
    """System health overview: license, database, backups, session."""

    def __init__(self, parent=None):
        super().__init__("DashboardCard", parent)
        self.body.setSpacing(SPACE_1)

        header = QVBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(2)

        eyebrow = QLabel("SISTEM")
        eyebrow.setObjectName("DashboardEyebrow")
        title = QLabel("Stanje sistema")
        title.setObjectName("DashboardSectionTitle")
        caption = QLabel("Licenca, baza, varnostne kopije in sejo")
        caption.setObjectName("DashboardMuted")
        caption.setWordWrap(True)

        header.addWidget(eyebrow)
        header.addWidget(title)
        header.addWidget(caption)
        self.body.addLayout(header)

        self.row_license = _HealthRow("Licenca")
        self.row_database = _HealthRow("Baza podatkov")
        self.row_backup = _HealthRow("Varnostne kopije")
        self.row_session = _HealthRow("Seja")

        for row in (
            self.row_license,
            self.row_database,
            self.row_backup,
            self.row_session,
        ):
            self.body.addWidget(row)

        self.summary = QLabel("—")
        self.summary.setObjectName("DashboardHealthSummary")
        self.summary.setWordWrap(True)
        self.body.addWidget(self.summary)
        self.body.addStretch(1)
        # License/DB/backup scan deferred to Dashboard.refresh() / showEvent.

    def refresh(self) -> None:
        # License — existing licensing system only (lazy import keeps shell light).
        from app.services.license_gate import _grace_valid
        from app.services.licensing_service import LicenseState

        state = LicenseState.load()
        if state is None:
            self.row_license.set_status("Ni aktivirana", kind="bad")
            license_ok = False
        else:
            status = (state.status or "").strip().lower()
            if status == "active":
                self.row_license.set_status("Aktivna", kind="ok")
                license_ok = True
            elif _grace_valid(state.grace_until):
                self.row_license.set_status("Milostni rok", kind="warn")
                license_ok = True
            else:
                label = status.capitalize() if status else "Lokalno"
                self.row_license.set_status(label, kind="warn")
                license_ok = bool(status) or bool(state.license_id)

        # Database
        db_path = Path(DATABASE_PATH)
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            self.row_database.set_status(f"OK · {size_mb:.1f} MB", kind="ok")
            db_ok = True
        else:
            self.row_database.set_status("Manjka", kind="bad")
            db_ok = False

        # Backups
        backup_dir = Path(BACKUP_DIR)
        backups = (
            sorted(backup_dir.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
            if backup_dir.exists()
            else []
        )
        if backups:
            latest = datetime.fromtimestamp(backups[0].stat().st_mtime)
            self.row_backup.set_status(
                f"{len(backups)} · {latest.strftime('%d.%m.%Y')}",
                kind="ok",
            )
            backup_ok = True
        else:
            self.row_backup.set_status("Ni kopij", kind="warn")
            backup_ok = False

        # Session
        user = _display(getattr(session, "user", None), "—")
        role = _display(getattr(session, "role", None), "—")
        self.row_session.set_status(f"{user} · {role}", kind="ok")

        if license_ok and db_ok and backup_ok:
            summary, kind = "Sistem je pripravljen", "ok"
        elif license_ok and db_ok:
            summary, kind = "Pripravljen · priporočena varnostna kopija", "warn"
        elif db_ok:
            summary, kind = "Delno — preverite licenco", "warn"
        else:
            summary, kind = "Zahteva pozornost", "bad"

        self.summary.setText(summary)
        self.summary.setProperty("kind", kind)
        style = self.summary.style()
        if style is not None:
            style.unpolish(self.summary)
            style.polish(self.summary)
        self.summary.update()
