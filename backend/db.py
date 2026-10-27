"""The UnderCover database: its schema and the loader for the data folder."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent / "undercover.db"
DATA_DIR = Path(__file__).parents[1] / "data"

SCHEMA = """
CREATE TABLE policies (id TEXT PRIMARY KEY, record TEXT NOT NULL);
CREATE TABLE customers (id TEXT PRIMARY KEY, record TEXT NOT NULL);
CREATE TABLE plans (id TEXT PRIMARY KEY, record TEXT NOT NULL);
CREATE TABLE handlers (id TEXT PRIMARY KEY, record TEXT NOT NULL);
CREATE TABLE claims (
    id TEXT PRIMARY KEY,
    record TEXT NOT NULL,
    state TEXT NOT NULL,
    decision TEXT,
    payout REAL,
    reason TEXT,
    policy_section TEXT,
    signed_off_by TEXT
);
CREATE TABLE payments (
    id INTEGER PRIMARY KEY,
    claim_id TEXT NOT NULL,
    amount REAL NOT NULL,
    paid_at TEXT NOT NULL
);
CREATE TABLE steps (
    id INTEGER PRIMARY KEY,
    claim_id TEXT NOT NULL,
    tool TEXT NOT NULL,
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE documents (name TEXT PRIMARY KEY, text TEXT NOT NULL);
CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    """Open a connection that commits when the block ends without an error."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def reset() -> None:
    """Rebuild the database from the data folder."""
    DB_PATH.unlink(missing_ok=True)
    with connection() as conn:
        conn.executescript(SCHEMA)
        load(conn)


def load(conn: sqlite3.Connection) -> None:
    """Load the files the pilot needs. It never opens data/evals or data/security."""

    def read_json(name: str) -> Any:
        return json.loads((DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))

    def insert(sql: str, key: str, records: list[dict]) -> None:
        conn.executemany(sql, [(record[key], json.dumps(record)) for record in records])

    insert(
        "INSERT INTO policies (id, record) VALUES (?, ?)",
        "policy_id",
        read_json("policies"),
    )
    insert(
        "INSERT INTO customers (id, record) VALUES (?, ?)",
        "customer_id",
        read_json("customers"),
    )
    insert(
        "INSERT INTO handlers (id, record) VALUES (?, ?)",
        "handler_id",
        read_json("handlers"),
    )
    insert(
        "INSERT INTO plans (id, record) VALUES (?, ?)",
        "plan",
        read_json("plans")["plans"],
    )
    conn.executemany(
        "INSERT INTO claims (id, record, state) VALUES (?, ?, 'waiting')",
        [(claim["claim_id"], json.dumps(claim)) for claim in read_json("claims")],
    )
    conn.execute(
        "INSERT INTO settings (key, value) VALUES ('company', ?)",
        (json.dumps(read_json("company")),),
    )
    wording = (DATA_DIR / "policy_wording.md").read_text(encoding="utf-8")
    conn.execute(
        "INSERT INTO documents (name, text) VALUES ('policy_wording', ?)", (wording,)
    )
