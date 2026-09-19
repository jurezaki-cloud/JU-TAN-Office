"""Temporary demo-session path/data verification. Not application source."""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Env must already be set by launcher.
for m in list(sys.modules):
    if m.startswith("app.") or m in {"config"}:
        del sys.modules[m]

from app.core.constants import DATA_DIR, DATABASE_PATH  # noqa: E402
from app.modules.warehouse.warehouse_service import STORE_PATH, WarehouseService, stock_status  # noqa: E402

normal = (ROOT / "data").resolve()
data_dir = DATA_DIR.resolve()
db_path = DATABASE_PATH.resolve()
store = STORE_PATH.resolve()

print("DATA_DIR", data_dir)
print("DATABASE_PATH", db_path)
print("STORE_PATH", store)

if data_dir == normal or data_dir == normal or "demo-session" not in str(data_dir):
    print("STOP: DATA_DIR not isolated")
    sys.exit(2)
if db_path.parent != data_dir or db_path.name != "ju_tan.db":
    print("STOP: DATABASE_PATH not in demo-session")
    sys.exit(2)
if store != data_dir / "warehouse.json":
    print("STOP: STORE_PATH wrong")
    sys.exit(2)
if str(normal) in str(db_path) and "demo-session" not in str(db_path):
    print("STOP: database resolves to normal data/")
    sys.exit(2)

print("PATH_GUARD_PASS")

conn = sqlite3.connect(db_path)
customers = conn.execute("select count(*) from customers").fetchone()[0]
names = [r[0] for r in conn.execute("select company from customers order by id").fetchall()]
articles = conn.execute("select count(*) from articles").fetchone()[0]
invoices = conn.execute("select count(*) from invoices").fetchone()[0]
offers = conn.execute("select count(*) from offers").fetchone()[0]
company = conn.execute("select name, bank, iban, tax_number from company").fetchone()
months = conn.execute(
    "select substr(issue_date,1,7), count(*) from invoices group by 1 order by 1"
).fetchall()
zak = conn.execute(
    "select count(*) from customers where company like ?", ("%Zak%",)
).fetchone()[0]
conn.close()

print("CUSTOMERS", customers)
print("CUSTOMER_NAMES", names)
print("ARTICLES", articles)
print("INVOICES", invoices)
print("OFFERS", offers)
print("COMPANY_NAME", company[0] if company else None)
print("COMPANY_BANK", company[1] if company else None)
print("INVOICE_MONTHS", months)
print("ZAK_TRADE_COUNT", zak)

# Warehouse status mix via service (uses articles from DB)
rows = WarehouseService(path=store).stock_rows()
statuses = sorted({r.status for r in rows})
print("WAREHOUSE_ROWS", len(rows))
print("WAREHOUSE_STATUSES", statuses)
for r in rows:
    print("WH", r.code, r.qty, r.min_qty, r.status)

required = {"Alpina Digital d.o.o.", "Nordis Projekt d.o.o.", "Vektor Studio d.o.o."}
ok = (
    customers == 8
    and articles == 8
    and invoices == 16
    and offers == 5
    and required.issubset(set(names))
    and zak == 0
    and len(months) >= 2
    and len(statuses) >= 3
)
print("VERIFY_OK" if ok else "VERIFY_FAIL")
sys.exit(0 if ok else 1)
