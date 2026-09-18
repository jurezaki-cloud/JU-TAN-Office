import os
import sys
from pathlib import Path

# ----------------------------
# Informacije o aplikaciji
# ----------------------------

APP_NAME = "JU-TAN Office Enterprise"
APP_VERSION = "0.2.0"
APP_AUTHOR = "JU-TAN Studio"

# ----------------------------
# Mape projekta
# ----------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent

if getattr(sys, "frozen", False):
    default_app_data = Path(
        os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
    ) / "JU-TAN Office"
else:
    default_app_data = BASE_DIR

APP_DATA_DIR = Path(os.environ.get("JU_TAN_DATA_DIR", default_app_data))
DATA_DIR = APP_DATA_DIR / "data"
EXPORT_DIR = APP_DATA_DIR / "exports"
REPORT_DIR = APP_DATA_DIR / "reports"
BACKUP_DIR = APP_DATA_DIR / "backups"
RESOURCE_DIR = BASE_DIR / "resources"
BRAND_ASSET_DIR = APP_DATA_DIR / "brand"

# ----------------------------
# Baza
# ----------------------------

DATABASE_NAME = "ju_tan.db"
DATABASE_PATH = DATA_DIR / DATABASE_NAME

# ----------------------------
# Logiranje
# ----------------------------

LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"

# ----------------------------
# Ustvari potrebne mape
# ----------------------------

for folder in (
    DATA_DIR,
    EXPORT_DIR,
    REPORT_DIR,
    BACKUP_DIR,
    BRAND_ASSET_DIR,
    LOG_DIR,
):
    folder.mkdir(parents=True, exist_ok=True)
