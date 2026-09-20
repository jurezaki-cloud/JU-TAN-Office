from __future__ import annotations

import os
from pathlib import Path

from app.core.deploy_paths import data_folder_name, resolve_dir

APP_NAME = "JU-TAN Office Enterprise"
APP_VERSION = "1.0.0"
APP_CHANNEL = "GOLD"
APP_BUILD = "RELEASE"
APP_AUTHOR = "JU-TAN Studio"
SCHEMA_VERSION = 2

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = resolve_dir("JU_TAN_DATA_DIR", data_folder_name())
EXPORT_DIR = resolve_dir("JU_TAN_EXPORT_DIR", "Reports")
REPORT_DIR = resolve_dir("JU_TAN_REPORT_DIR", "Reports")
BACKUP_DIR = resolve_dir("JU_TAN_BACKUP_DIR", "Backup")
TEMP_DIR = resolve_dir("JU_TAN_TEMP_DIR", "Temp")
RESOURCE_DIR = BASE_DIR / "resources"

DATABASE_NAME = "ju_tan.db"
DATABASE_PATH = Path(os.environ.get("JU_TAN_DATABASE", str(DATA_DIR / DATABASE_NAME)))

LOG_DIR = resolve_dir("JU_TAN_LOG_DIR", "Logs")
LOG_FILE = LOG_DIR / "app.log"

for folder in (DATA_DIR, EXPORT_DIR, REPORT_DIR, BACKUP_DIR, TEMP_DIR, LOG_DIR):
    folder.mkdir(parents=True, exist_ok=True)
