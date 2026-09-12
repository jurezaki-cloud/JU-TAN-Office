"""Namizna konfiguracija (Flask/SQLAlchemy nista v rabi).

Skrivnosti ne shranjujte v tem dokumentu. Poti prepišite z okoljskimi spremenljivkami:
JU_TAN_DATA_DIR, JU_TAN_DATABASE, JU_TAN_LOG_DIR.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("JU_TAN_DATA_DIR", str(BASE_DIR / "data")))
