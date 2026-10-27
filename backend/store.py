"""Reads and writes for the claims queue."""

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from backend.db import connection

WAITING = "waiting"
IN_PROGRESS = "in_progress"
WAITING_FOR_SIGN_OFF = "waiting_for_sign_off"
DECIDED = "decided"


class NotFound(Exception):
    """A claim, handler or other record does not exist."""


class Conflict(Exception):
    """The claim is not in a state that allows the change."""


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
        row = _claim_row(conn, claim_id)
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


def list_handlers() -> list[dict[str, Any]]:
    """Return the claims handlers who can sign off payouts."""
    with connection() as conn:
        return [
            {
                "handler_id": handler["handler_id"],
                "name": handler["name"],
                "role": handler["role"],
                "can_approve_over_limit": handler["can_approve_over_limit"],
            }
            for handler in (
                json.loads(row["record"])
                for row in conn.execute("SELECT record FROM handlers ORDER BY id")
            )
        ]


def record_decision(
    claim_id: str, decision: str, payout: float, reason: str, policy_section: str
) -> dict[str, Any]:
    """Record the agent's decision. A payout over the limit waits for sign-off."""
    payout = round(payout, 2)
    if decision == "approve" and payout <= 0:
        raise Conflict("An approval needs a payout above zero")
    if decision != "approve" and payout != 0:
        raise Conflict("Only an approval can carry a payout")
    with connection() as conn:
        row = _claim_row(conn, claim_id)
        if row["state"] not in (WAITING, IN_PROGRESS):
            raise Conflict(f"Claim {claim_id} is {row['state']}")
        needs_sign_off = decision == "approve" and payout > _approval_limit(conn)
        state = WAITING_FOR_SIGN_OFF if needs_sign_off else DECIDED
        conn.execute(
            """
            UPDATE claims
            SET state = ?, decision = ?, payout = ?, reason = ?, policy_section = ?
            WHERE id = ?
            """,
            (state, decision, payout, reason, policy_section, claim_id),
        )
    return get_claim(claim_id)


def sign_off(claim_id: str, handler_id: str) -> dict[str, Any]:
    """Record a handler's sign-off on a payout over the limit."""
    with connection() as conn:
        row = _claim_row(conn, claim_id)
        if row["state"] != WAITING_FOR_SIGN_OFF:
            raise Conflict(
                f"Claim {claim_id} is {row['state']}, not waiting for sign-off"
            )
        handler = _record(conn, "SELECT record FROM handlers WHERE id = ?", handler_id)
        if not handler["can_approve_over_limit"]:
            raise Conflict(f"{handler['name']} cannot sign off payouts over the limit")
        conn.execute(
            "UPDATE claims SET state = ?, signed_off_by = ? WHERE id = ?",
            (DECIDED, handler_id, claim_id),
        )
    return get_claim(claim_id)


def pay_claim(claim_id: str, amount: float) -> dict[str, Any]:
    """Record a payment. A payout over the limit is blocked until it is signed off."""
    amount = round(amount, 2)
    with connection() as conn:
        row = _claim_row(conn, claim_id)
        if row["decision"] != "approve":
            raise Conflict(f"Claim {claim_id} is not approved, so it cannot be paid")
        if row["state"] == WAITING_FOR_SIGN_OFF:
            raise Conflict("A payout over the limit needs a handler's sign-off first")
        if row["state"] != DECIDED:
            raise Conflict(f"Claim {claim_id} is {row['state']}, not decided")
        if amount != row["payout"]:
            raise Conflict(f"The approved payout is ${row['payout']:,.2f}")
        paid = conn.execute(
            "SELECT COUNT(*) FROM payments WHERE claim_id = ?", (claim_id,)
        ).fetchone()[0]
        if paid:
            raise Conflict(f"Claim {claim_id} has already been paid")
        conn.execute(
            "INSERT INTO payments (claim_id, amount, paid_at) VALUES (?, ?, ?)",
            (claim_id, amount, _now()),
        )
    return get_claim(claim_id)


def waiting_claim_ids() -> list[str]:
    """Return the ids of the claims waiting to be worked, in order."""
    with connection() as conn:
        rows = conn.execute(
            "SELECT id FROM claims WHERE state = ? ORDER BY id", (WAITING,)
        ).fetchall()
    return [row["id"] for row in rows]


def start_claim(claim_id: str) -> dict[str, Any]:
    """Mark a waiting claim as in progress, so the agent can work on it."""
    with connection() as conn:
        row = _claim_row(conn, claim_id)
        if row["state"] != WAITING:
            raise Conflict(f"Claim {claim_id} is {row['state']}, not waiting")
        conn.execute(
            "UPDATE claims SET state = ? WHERE id = ?", (IN_PROGRESS, claim_id)
        )
    return get_claim(claim_id)


def release(claim_id: str) -> None:
    """Return a claim the agent left in progress to waiting, and log why."""
    with connection() as conn:
        row = _claim_row(conn, claim_id)
        if row["state"] != IN_PROGRESS:
            return
        conn.execute("UPDATE claims SET state = ? WHERE id = ?", (WAITING, claim_id))
    record_step(
        claim_id,
        "run_ended",
        "",
        "The run ended without a decision, so the claim is waiting again",
    )


def record_step(claim_id: str, tool: str, step_input: str, output: str) -> None:
    """Add one step to a claim's log of what the agent did."""
    with connection() as conn:
        _claim_row(conn, claim_id)
        conn.execute(
            "INSERT INTO steps (claim_id, tool, input, output, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (claim_id, tool, step_input, output, _now()),
        )


def _claim_row(conn: sqlite3.Connection, claim_id: str) -> sqlite3.Row:
    """Return a claim's row, or raise NotFound."""
    row = conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
    if row is None:
        raise NotFound(f"No claim {claim_id}")
    return row


def _approval_limit(conn: sqlite3.Connection) -> float:
    """Return the payout above which a handler must sign off."""
    company = conn.execute(
        "SELECT value FROM settings WHERE key = 'company'"
    ).fetchone()
    return json.loads(company["value"])["payout_approval_limit"]


def _now() -> str:
    """Return the current time, to the second, in UTC."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def _record(conn: sqlite3.Connection, sql: str, key: str) -> dict[str, Any]:
    """Return the record a one-column query finds for a key, or raise NotFound."""
    row = conn.execute(sql, (key,)).fetchone()
    if row is None:
        raise NotFound(f"No record {key}")
    return json.loads(row["record"])


def _rows(conn: sqlite3.Connection, sql: str, claim_id: str) -> list[dict[str, Any]]:
    """Return every row a query finds for a claim, as dictionaries."""
    return [dict(row) for row in conn.execute(sql, (claim_id,)).fetchall()]
