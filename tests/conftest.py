# Isolated temp dirs MUST be set before any app import.
import os
import tempfile
from pathlib import Path

_ROOT = Path(tempfile.mkdtemp(prefix="jutan-test-"))
os.environ["JU_TAN_DATA_DIR"] = str(_ROOT / "data")
os.environ["JU_TAN_EXPORT_DIR"] = str(_ROOT / "exports")
os.environ["JU_TAN_REPORT_DIR"] = str(_ROOT / "reports")
os.environ["JU_TAN_BACKUP_DIR"] = str(_ROOT / "backups")
os.environ["JU_TAN_LOG_DIR"] = str(_ROOT / "logs")
os.environ["JU_TAN_DATABASE"] = str(_ROOT / "data" / "test.db")
# Default to Qt's headless backend locally, but respect an explicit backend
# supplied by CI (Xvfb uses xcb). Overwriting xcb here caused QApplication
# to abort on Linux before GUI tests could start.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from app.database.database import db


@pytest.fixture(scope="session", autouse=True)
def _init_db():
    db.initialize()
    yield


@pytest.fixture
def qt_app():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
