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

DATA_DIR = BASE_DIR / "data"
EXPORT_DIR = BASE_DIR / "exports"
REPORT_DIR = BASE_DIR / "reports"
BACKUP_DIR = BASE_DIR / "backups"
RESOURCE_DIR = BASE_DIR / "resources"

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
    LOG_DIR,
):
    folder.mkdir(parents=True, exist_ok=True)