from PySide6.QtWidgets import QLabel, QStatusBar

from app.core.constants import APP_VERSION, DATABASE_PATH
from app.modules.automation.job_queue import job_queue


class StatusBar(QStatusBar):

    def __init__(self):
        super().__init__()
        self.setObjectName("AppStatusBar")
        self._user = QLabel("Administrator")
        self._company = QLabel("—")
        self._version = QLabel(f"v{APP_VERSION}")
        self._db = QLabel("Baza: …")
        self._jobs = QLabel("Opravila: 0")
        for label in (self._user, self._company, self._version, self._db, self._jobs):
            label.setObjectName("StatusChip")
            self.addPermanentWidget(label)
        self.showMessage("Sistem pripravljen")
        self.refresh()

    def refresh(self) -> None:
        self._user.setText("Administrator")
        self._version.setText(f"v{APP_VERSION}")
        try:
            from app.database.company_repository import company_repository
            row = company_repository.get_company()
            name = (row[1] if row else "") or "Podjetje"
            self._company.setText(str(name))
        except Exception:
            self._company.setText("Podjetje")
        try:
            ok = DATABASE_PATH.exists()
            self._db.setText("Baza: OK" if ok else "Baza: ni datoteke")
        except Exception:
            self._db.setText("Baza: ?")
        pending = len(getattr(job_queue, "_pending", []) or [])
        self._jobs.setText(f"Opravila: {pending}")
