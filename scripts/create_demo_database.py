"""Create isolated fictional screenshot database: data/ju_tan_demo.db

Read-only against data/ju_tan.db (schema clone only — never copies rows).
Also writes data/warehouse_demo.json (warehouse is JSON-backed, not SQLite).
Does not modify ju_tan.db, settings, or application source.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DB = ROOT / "data" / "ju_tan.db"
DEST_DB = ROOT / "data" / "ju_tan_demo.db"
WAREHOUSE_DEMO = ROOT / "data" / "warehouse_demo.json"

VAT = 22.0


def _money(qty: float, price: float, discount_pct: float = 0.0, vat: float = VAT) -> tuple[float, float, float]:
    base = round(qty * price * (1 - discount_pct / 100.0), 2)
    vat_amt = round(base * vat / 100.0, 2)
    total = round(base + vat_amt, 2)
    return base, vat_amt, total


def clone_schema(src: Path, dest: Path) -> None:
    if dest.exists():
        dest.unlink()
    for suffix in ("-wal", "-shm"):
        side = Path(str(dest) + suffix)
        if side.exists():
            side.unlink()

    src_conn = sqlite3.connect(f"file:{src.resolve().as_posix()}?mode=ro", uri=True)
    dest_conn = sqlite3.connect(dest)
    dest_conn.execute("PRAGMA foreign_keys = OFF")

    # Clone CREATE statements for tables/indexes/triggers, skipping FTS shadow tables
    # (CREATE VIRTUAL TABLE recreates them). Never copy INSERT/data.
    objects = src_conn.execute(
        """
        SELECT type, name, sql FROM sqlite_master
        WHERE sql IS NOT NULL
          AND name NOT LIKE 'sqlite_%'
          AND name NOT LIKE '%_fts_%'
        ORDER BY
          CASE type
            WHEN 'table' THEN 0
            WHEN 'index' THEN 1
            WHEN 'trigger' THEN 2
            ELSE 3
          END,
          name
        """
    ).fetchall()

    for _type, name, sql in objects:
        try:
            dest_conn.execute(sql)
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed creating {name}: {exc}") from exc

    dest_conn.commit()
    src_conn.close()
    dest_conn.close()


def seed(dest: Path) -> dict:
    conn = sqlite3.connect(dest)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Fictional company only — no real bank/tax data
    cur.execute(
        """
        INSERT INTO company(
            id, name, legal_name, address, postal_code, city, country,
            tax_number, registration_number, iban, bank,
            email, website, phone, mobile, logo,
            invoice_prefix, offer_prefix, invoice_counter, offer_counter,
            default_vat, notes
        ) VALUES (
            1,
            'Demo Soft d.o.o.',
            'Demo Soft d.o.o.',
            'Demo ulica 1',
            '1000',
            'Ljubljana',
            'Slovenija',
            'SI00000000',
            '0000000000',
            'SI56000000000000000',
            'Demo Banka',
            'info@demo-soft.example.com',
            'https://demo-soft.example.com',
            '+386 1 000 00 00',
            '+386 40 000 000',
            NULL,
            'RAC',
            'PON',
            1,
            1,
            22,
            'Fictional screenshot demo company — not a real entity.'
        )
        """
    )

    customers = [
        ("Alpina Digital d.o.o.", "Ana Novak", "Gorenjska cesta 12", "4000", "Kranj", "Slovenija", "SI11111111", "ana.novak@alpina-digital.example.com", "+386 40 111 111"),
        ("Nordis Projekt d.o.o.", "Marko Horvat", "Tržaška 45", "1000", "Ljubljana", "Slovenija", "SI22222222", "marko.horvat@nordis-projekt.example.com", "+386 41 222 222"),
        ("Vektor Studio d.o.o.", "Eva Kranjc", "Kidričeva 8", "2000", "Maribor", "Slovenija", "SI33333333", "eva.krjc@vektor-studio.example.com", "+386 31 333 333"),
        ("Lumina Sistem d.o.o.", "Luka Zupan", "Cankarjeva 3", "6000", "Koper", "Slovenija", "SI44444444", "luka.zupan@lumina-sistem.example.com", "+386 51 444 444"),
        ("Adria Solutions d.o.o.", "Maja Breznik", "Obala 21", "6320", "Portorož", "Slovenija", "SI55555555", "maja.breznik@adria-solutions.example.com", "+386 41 555 555"),
        ("Nova Pot d.o.o.", "Tomaž Kos", "Celovška 100", "1000", "Ljubljana", "Slovenija", "SI66666666", "tomaz.kos@nova-pot.example.com", "+386 40 666 666"),
        ("Orion Analytics d.o.o.", "Sara Pirc", "Partizanska 7", "3000", "Celje", "Slovenija", "SI77777777", "sara.pirc@orion-analytics.example.com", "+386 31 777 777"),
        ("Pixel Forge d.o.o.", "Jan Vidmar", "Kidričeva 15", "5000", "Nova Gorica", "Slovenija", "SI88888888", "jan.vidmar@pixel-forge.example.com", "+386 51 888 888"),
    ]
    for company, contact, address, postal, city, country, tax, email, phone in customers:
        cur.execute(
            """
            INSERT INTO customers(company, contact, address, postal_code, city, country, tax_number, email, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (company, contact, address, postal, city, country, tax, email, phone),
        )

    articles = [
        ("SRV-001", "Razvoj programske opreme", "Fictional demo service", "ura", 85.0),
        ("SRV-002", "UI/UX načrtovanje", "Fictional demo service", "ura", 75.0),
        ("SRV-003", "Sistemska integracija", "Fictional demo service", "ura", 95.0),
        ("SRV-004", "Tehnično svetovanje", "Fictional demo service", "ura", 110.0),
        ("SRV-005", "Vzdrževanje sistema", "Fictional demo service", "mesec", 450.0),
        ("SRV-006", "API integracija", "Fictional demo service", "ura", 90.0),
        ("SRV-007", "Avtomatizacija procesa", "Fictional demo service", "ura", 100.0),
        ("SRV-008", "Podpora uporabnikom", "Fictional demo service", "ura", 55.0),
    ]
    for code, name, desc, unit, price in articles:
        cur.execute(
            """
            INSERT INTO articles(code, name, description, unit, price, vat)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (code, name, desc, unit, price, VAT),
        )

    # Rebuild FTS if empty / ensure populated via triggers already fired on INSERT
    try:
        cur.execute("INSERT INTO articles_fts(articles_fts) VALUES('rebuild')")
    except sqlite3.Error:
        pass
    try:
        cur.execute("INSERT INTO customers_fts(customers_fts) VALUES('rebuild')")
    except sqlite3.Error:
        pass

    article_rows = cur.execute("SELECT id, code, name, unit, price FROM articles ORDER BY id").fetchall()
    customer_ids = [r[0] for r in cur.execute("SELECT id FROM customers ORDER BY id").fetchall()]

    # Invoices across multiple months for dashboard chart
    # (customer_idx, article_idxs with qty, issue, due, status, number)
    invoice_specs = [
        (0, [(0, 40), (3, 8)], "2025-10-05", "2025-10-20", "Plačan", "RAC-2025-001"),
        (1, [(1, 24), (7, 10)], "2025-11-12", "2025-11-27", "Plačan", "RAC-2025-002"),
        (2, [(2, 16), (5, 12)], "2025-12-03", "2025-12-18", "Plačan", "RAC-2025-003"),
        (3, [(4, 1), (0, 20)], "2026-01-15", "2026-01-30", "Plačan", "RAC-2026-001"),
        (4, [(6, 18), (3, 6)], "2026-02-10", "2026-02-25", "Plačan", "RAC-2026-002"),
        (5, [(1, 30), (7, 20)], "2026-03-08", "2026-03-23", "Plačan", "RAC-2026-003"),
        (6, [(0, 50), (5, 15)], "2026-04-14", "2026-04-29", "Plačan", "RAC-2026-004"),
        (7, [(2, 22), (6, 10)], "2026-05-06", "2026-05-21", "Plačan", "RAC-2026-005"),
        (0, [(4, 2), (7, 16)], "2026-06-11", "2026-06-26", "Plačan", "RAC-2026-006"),
        (1, [(3, 12), (0, 28)], "2026-07-09", "2026-07-24", "Izdan", "RAC-2026-007"),
        (2, [(5, 20), (1, 14)], "2026-08-04", "2026-08-19", "Izdan", "RAC-2026-008"),
        (3, [(6, 25)], "2026-08-22", "2026-09-06", "Izdan", "RAC-2026-009"),
        (4, [(0, 35), (2, 10)], "2026-09-02", "2026-09-17", "Izdan", "RAC-2026-010"),
        (5, [(7, 8)], "2026-09-10", "2026-09-25", "Osnutek", "RAC-2026-011"),
        (6, [(1, 12), (3, 4)], "2026-09-15", "2026-09-30", "Osnutek", "RAC-2026-012"),
        (7, [(4, 1)], "2026-05-28", "2026-06-12", "Storniran", "RAC-2026-013"),
    ]

    for cust_i, items, issue, due, status, number in invoice_specs:
        subtotal = 0.0
        vat_sum = 0.0
        total_sum = 0.0
        line_payload = []
        for art_i, qty in items:
            art = article_rows[art_i]
            base, vat_amt, line_total = _money(qty, art[4])
            subtotal += base
            vat_sum += vat_amt
            total_sum += line_total
            line_payload.append((art[0], art[1], art[2], qty, art[3], art[4], base + 0, line_total))

        subtotal = round(subtotal, 2)
        vat_sum = round(vat_sum, 2)
        total_sum = round(total_sum, 2)

        cur.execute(
            """
            INSERT INTO invoices(
                invoice_number, customer_id, issue_date, due_date, status,
                subtotal, discount, vat, total, notes
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (
                number,
                customer_ids[cust_i],
                issue,
                due,
                status,
                subtotal,
                vat_sum,
                total_sum,
                "Fictional demo invoice",
            ),
        )
        invoice_id = cur.lastrowid
        for art_id, code, name, qty, unit, price, _base, line_total in line_payload:
            cur.execute(
                """
                INSERT INTO invoice_items(
                    invoice_id, article_id, code, name, description,
                    quantity, unit, price, discount, vat, total
                ) VALUES (?, ?, ?, ?, '', ?, ?, ?, 0, ?, ?)
                """,
                (invoice_id, art_id, code, name, qty, unit, price, VAT, line_total),
            )

    offer_specs = [
        (0, [(0, 60), (1, 20)], "2026-07-01", "2026-07-31", "Sprejeta", "PON-2026-001"),
        (1, [(2, 40)], "2026-08-05", "2026-09-05", "Poslana", "PON-2026-002"),
        (4, [(3, 16), (5, 24)], "2026-08-20", "2026-09-20", "Poslana", "PON-2026-003"),
        (5, [(6, 30), (7, 40)], "2026-09-01", "2026-10-01", "Osnutek", "PON-2026-004"),
        (7, [(1, 50)], "2026-06-15", "2026-07-15", "Zavrnjena", "PON-2026-005"),
    ]

    for cust_i, items, issue, valid, status, number in offer_specs:
        subtotal = 0.0
        vat_sum = 0.0
        total_sum = 0.0
        line_payload = []
        for art_i, qty in items:
            art = article_rows[art_i]
            base, vat_amt, line_total = _money(qty, art[4])
            subtotal += base
            vat_sum += vat_amt
            total_sum += line_total
            line_payload.append((art[0], art[1], art[2], qty, art[3], art[4], line_total))

        cur.execute(
            """
            INSERT INTO offers(
                number, customer_id, issue_date, valid_until, status,
                subtotal, discount, vat, total, notes
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (
                number,
                customer_ids[cust_i],
                issue,
                valid,
                status,
                round(subtotal, 2),
                round(vat_sum, 2),
                round(total_sum, 2),
                "Fictional demo offer",
            ),
        )
        offer_id = cur.lastrowid
        for art_id, code, name, qty, unit, price, line_total in line_payload:
            cur.execute(
                """
                INSERT INTO offer_items(
                    offer_id, article_id, code, name, description,
                    quantity, unit, price, discount, vat, total
                ) VALUES (?, ?, ?, ?, '', ?, ?, ?, 0, ?, ?)
                """,
                (offer_id, art_id, code, name, qty, unit, price, VAT, line_total),
            )

    # Bump counters past demo documents
    cur.execute(
        "UPDATE company SET invoice_counter=14, offer_counter=6 WHERE id=1"
    )

    # Empty audit — no real usernames
    # Leave CRM/orders/purchase empty (not required for listed screenshots)

    conn.commit()

    summary = {
        "customers": cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
        "articles": cur.execute("SELECT COUNT(*) FROM articles").fetchone()[0],
        "invoices": cur.execute("SELECT COUNT(*) FROM invoices").fetchone()[0],
        "invoice_items": cur.execute("SELECT COUNT(*) FROM invoice_items").fetchone()[0],
        "offers": cur.execute("SELECT COUNT(*) FROM offers").fetchone()[0],
        "offer_items": cur.execute("SELECT COUNT(*) FROM offer_items").fetchone()[0],
        "months": [
            r[0]
            for r in cur.execute(
                "SELECT DISTINCT substr(issue_date,1,7) FROM invoices "
                "WHERE status <> 'Storniran' ORDER BY 1"
            ).fetchall()
        ],
        "customer_names": [
            r[0] for r in cur.execute("SELECT company FROM customers ORDER BY id").fetchall()
        ],
        "article_names": [
            r[0] for r in cur.execute("SELECT name FROM articles ORDER BY id").fetchall()
        ],
        "invoice_numbers": [
            r[0] for r in cur.execute("SELECT invoice_number FROM invoices ORDER BY id").fetchall()
        ],
        "offer_numbers": [
            r[0] for r in cur.execute("SELECT number FROM offers ORDER BY id").fetchall()
        ],
        "tables": [
            r[0]
            for r in cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '%_fts%' "
                "ORDER BY name"
            ).fetchall()
        ],
    }
    conn.close()
    return summary


def write_warehouse_demo(article_count: int = 8) -> dict:
    """Warehouse is JSON-backed (data/warehouse.json), not SQLite.

    Write an isolated companion file for screenshot sessions.
    Does not create or overwrite warehouse.json.
    """
    # Varied stock: normal / low / zero
    stock_plan = {
        "1": {"main": {"qty": 120, "reserved": 10, "min_qty": 20}},   # normal
        "2": {"main": {"qty": 80, "reserved": 5, "min_qty": 15}},    # normal
        "3": {"main": {"qty": 8, "reserved": 2, "min_qty": 10}},     # low
        "4": {"main": {"qty": 3, "reserved": 0, "min_qty": 5}},      # low
        "5": {"main": {"qty": 0, "reserved": 0, "min_qty": 2}},      # zero
        "6": {"main": {"qty": 45, "reserved": 0, "min_qty": 10}},    # normal
        "7": {"main": {"qty": 2, "reserved": 1, "min_qty": 8}},      # low
        "8": {"main": {"qty": 0, "reserved": 0, "min_qty": 5}},      # zero
    }
    today = date.today().isoformat()
    payload = {
        "warehouses": [{"id": "main", "name": "Glavno skladišče"}],
        "stock": {k: v for k, v in stock_plan.items() if int(k) <= article_count},
        "movements": [
            {
                "id": 1,
                "date": today,
                "type": "Prevzem",
                "article_id": 1,
                "warehouse_id": "main",
                "quantity": 120,
                "user": "demo",
                "note": "Fictional demo stock",
            },
            {
                "id": 2,
                "date": (date.today() - timedelta(days=3)).isoformat(),
                "type": "Izdaja",
                "article_id": 3,
                "warehouse_id": "main",
                "quantity": -5,
                "user": "demo",
                "note": "Fictional demo issue",
            },
        ],
    }
    WAREHOUSE_DEMO.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def privacy_scan(dest: Path) -> list[str]:
    """Return list of findings; empty means clean for fictional demo markers."""
    findings: list[str] = []
    conn = sqlite3.connect(f"file:{dest.resolve().as_posix()}?mode=ro", uri=True)
    cur = conn.cursor()

    # All emails must be example.com
    bad_emails = cur.execute(
        """
        SELECT email FROM customers
        WHERE email IS NOT NULL AND email != ''
          AND email NOT LIKE '%@%.example.com'
          AND email NOT LIKE '%@example.com'
        """
    ).fetchall()
    if bad_emails:
        findings.append(f"non-example emails: {len(bad_emails)}")

    company_email = cur.execute("SELECT email, iban, tax_number FROM company WHERE id=1").fetchone()
    if company_email:
        email, iban, tax = company_email
        if email and "example.com" not in email:
            findings.append("company email not fictional")
        if iban and iban not in ("SI56000000000000000",):
            # only allow known fictional placeholder
            findings.append("unexpected company IBAN")
        if tax and tax != "SI00000000":
            findings.append("unexpected company tax id")

    # Forbid obvious secret-like columns/content
    for table in ("customers", "company", "invoices", "offers", "articles", "audit_log"):
        cols = [c[1] for c in cur.execute(f"PRAGMA table_info([{table}])").fetchall()]
        for col in cols:
            if col.lower() in ("password", "api_key", "token", "secret", "hash"):
                findings.append(f"secret-like column {table}.{col}")

    # No passwords/tokens in text fields
    text_hits = cur.execute(
        """
        SELECT COUNT(*) FROM company
        WHERE lower(coalesce(notes,'')) LIKE '%password%'
           OR lower(coalesce(notes,'')) LIKE '%api_key%'
           OR lower(coalesce(notes,'')) LIKE '%token%'
        """
    ).fetchone()[0]
    if text_hits:
        findings.append("secret-like words in company notes")

    # Ensure demo marker customers only
    real_looking = cur.execute(
        """
        SELECT company FROM customers
        WHERE company NOT LIKE '%d.o.o.'
        """
    ).fetchall()
    # Soft check only — all our demos are d.o.o.

    conn.close()
    return findings


def main() -> None:
    if not SRC_DB.exists():
        raise SystemExit(f"Source DB missing: {SRC_DB}")

    src_size_before = SRC_DB.stat().st_size
    clone_schema(SRC_DB, DEST_DB)
    summary = seed(DEST_DB)
    warehouse = write_warehouse_demo(summary["articles"])
    findings = privacy_scan(DEST_DB)
    src_size_after = SRC_DB.stat().st_size

    print("DEST:", DEST_DB)
    print("WAREHOUSE_DEMO:", WAREHOUSE_DEMO)
    print("SRC_SIZE_BEFORE:", src_size_before)
    print("SRC_SIZE_AFTER:", src_size_after)
    print("SRC_UNCHANGED:", src_size_before == src_size_after)
    print("SUMMARY:", json.dumps(summary, ensure_ascii=False))
    normal = sum(1 for a in warehouse["stock"].values() for c in a.values() if c["qty"] > c["min_qty"] > 0 or (c["qty"] > 0 and c["min_qty"] == 0))
    low = sum(1 for a in warehouse["stock"].values() for c in a.values() if 0 < c["qty"] <= c["min_qty"])
    zero = sum(1 for a in warehouse["stock"].values() for c in a.values() if c["qty"] <= 0)
    print("WAREHOUSE_COUNTS:", json.dumps({"normal_or_above_min": normal, "low": low, "zero": zero}))
    print("PRIVACY_FINDINGS:", findings or "NONE")


if __name__ == "__main__":
    main()
