"""Runs the UnderCover Agent on claims in the background."""

import threading
import uuid
from typing import Any

from agent.main import run as run_agent
from backend import store


def start_claim(claim_id: str) -> dict[str, Any]:
    """Start the agent on a waiting claim in the background, and return the claim."""
    claim = store.start_claim(claim_id)
    threading.Thread(
        target=work, args=(claim_id,), name=f"run-{claim_id}", daemon=True
    ).start()
    return claim


def start_queue() -> int:
    """Start the agent on every waiting claim, one after another, in the background."""
    claim_ids = store.waiting_claim_ids()
    threading.Thread(
        target=_work_queue, args=(claim_ids,), name="run-queue", daemon=True
    ).start()
    return len(claim_ids)


def work(claim_id: str) -> None:
    """Run the agent on a claim that is in progress, then release it if undecided."""
    try:
        run_agent(claim_id, f"{claim_id}-{uuid.uuid4()}")
    except Exception as error:
        store.record_step(claim_id, "run_failed", "", str(error))
    store.release(claim_id)


def _work_queue(claim_ids: list[str]) -> None:
    """Work each claim in turn, skipping any that another run has started."""
    for claim_id in claim_ids:
        try:
            store.start_claim(claim_id)
        except store.Conflict:
            continue
        work(claim_id)
