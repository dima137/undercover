"""Reads and writes for the claims queue."""

import json
import sqlite3
from typing import Any

from backend.db import connection

WAITING = "waiting"
IN_PROGRESS = "in_progress"
WAITING_FOR_SIGN_OFF = "waiting_for_sign_off"
DECIDED = "decided"


class NotFound(Exception):
    """A claim, handler or other record does not exist."""


def list_claims() -> list[dict[str, Any]]:
    """Return a one-line summary of every claim in the queue."""
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT claims.id, claims.record, claims.state, claims.decision,
                   customers.record AS customer
            FROM claims
            JOIN customers
              ON customers.id = json_extract(claims.record, '$.customer_id')
            ORDER BY claims.id
            """
        ).fetchall()
    return [
        {
            "claim_id": row["id"],
            "claim_type": json.loads(row["record"])["claim_type"],
            "customer_name": json.loads(row["customer"])["name"],
            "amount_claimed": json.loads(row["record"])["amount_claimed"],
            "state": row["state"],
            "decision": row["decision"],
        }
        for row in rows
    ]


def get_claim(claim_id: str) -> dict[str, Any]:
    """Return one claim in full, with its policy, plan, customer and decision."""
    with connection() as conn:
        row = conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
        if row is None:
            raise NotFound(f"No claim {claim_id}")
        claim = json.loads(row["record"])
        policy = _record(
            conn, "SELECT record FROM policies WHERE id = ?", claim["policy_id"]
        )
        return {
            "claim_id": claim_id,
            "state": row["state"],
            "claim": claim,
            "policy": policy,
            "plan": _record(
                conn, "SELECT record FROM plans WHERE id = ?", policy["plan"]
            ),
            "customer": _record(
                conn, "SELECT record FROM customers WHERE id = ?", claim["customer_id"]
            ),
            "decision": row["decision"],
            "payout": row["payout"],
            "reason": row["reason"],
            "policy_section": row["policy_section"],
            "signed_off_by": row["signed_off_by"],
            "payments": _rows(
                conn,
                "SELECT amount, paid_at FROM payments WHERE claim_id = ? ORDER BY id",
                claim_id,
            ),
            "steps": _rows(
                conn,
                "SELECT tool, input, output, created_at FROM steps "
                "WHERE claim_id = ? ORDER BY id",
                claim_id,
            ),
        }


def get_policy_wording() -> str:
    """Return the policy wording the agent decides from."""
    with connection() as conn:
        row = conn.execute(
            "SELECT text FROM documents WHERE name = 'policy_wording'"
        ).fetchone()
        return row["text"]


def _record(conn: sqlite3.Connection, sql: str, key: str) -> dict[str, Any]:
    """Return the record a one-column query finds for a key, or raise NotFound."""
    row = conn.execute(sql, (key,)).fetchone()
    if row is None:
        raise NotFound(f"No record {key}")
    return json.loads(row["record"])


def _rows(conn: sqlite3.Connection, sql: str, claim_id: str) -> list[dict[str, Any]]:
    """Return every row a query finds for a claim, as dictionaries."""
    return [dict(row) for row in conn.execute(sql, (claim_id,)).fetchall()]
