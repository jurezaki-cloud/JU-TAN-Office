"""Prostorninski generator za ročni stres (ni privzeti pytest)."""

from __future__ import annotations

import argparse
import sqlite3
import time

from app.core.constants import DATABASE_PATH


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--customers", type=int, default=2000)
    parser.add_argument("--articles", type=int, default=2000)
    args = parser.parse_args()
    conn = sqlite3.connect(DATABASE_PATH, timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    started = time.perf_counter()
    conn.executemany(
        "INSERT INTO customers(company, contact) VALUES (?,?)",
        [(f"VOL-C-{i:07d}", "QA") for i in range(args.customers)],
    )
    conn.executemany(
        "INSERT INTO articles(code, name, unit, price, vat) VALUES (?,?,?,?,?)",
        [(f"VOL-A-{i:07d}", f"Artikel {i}", "kos", 1.0, 22) for i in range(args.articles)],
    )
    conn.commit()
    conn.close()
    print(f"Inserted in {time.perf_counter() - started:.2f}s")


if __name__ == "__main__":
    main()
