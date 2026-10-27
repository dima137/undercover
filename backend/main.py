"""The UnderCover backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend import db, runner, store

INSTRUCTIONS = Path(__file__).parent / "instructions.md"


class DecisionIn(BaseModel):
    decision: Literal["approve", "decline", "refer"]
    payout: float
    reason: str
    policy_section: str


class SignOffIn(BaseModel):
    handler_id: str


class PaymentIn(BaseModel):
    amount: float


class StepIn(BaseModel):
    tool: str
    input: str
    output: str


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Rebuild the database from the data folder each time the backend starts."""
    db.reset()
    yield


app = FastAPI(title="UnderCover", lifespan=lifespan)


@app.exception_handler(store.NotFound)
def not_found(_request: Any, exc: store.NotFound) -> JSONResponse:
    """Answer 404 when a record does not exist."""
    return JSONResponse({"detail": str(exc)}, status_code=404)


@app.exception_handler(store.Conflict)
def conflict(_request: Any, exc: store.Conflict) -> JSONResponse:
    """Answer 409 when the claim is not in a state that allows the change."""
    return JSONResponse({"detail": str(exc)}, status_code=409)


@app.get("/api/health", operation_id="health")
def health() -> dict[str, str]:
    """Check that the backend is running."""
    return {"status": "ok"}


@app.get("/api/claims", operation_id="list_claims")
def list_claims() -> list[dict[str, Any]]:
    """List every claim in the queue with its state."""
    return store.list_claims()


@app.get("/api/claims/{claim_id}", operation_id="get_claim")
def get_claim(claim_id: str) -> dict[str, Any]:
    """Get one claim in full, with its policy, customer and decision."""
    return store.get_claim(claim_id)


@app.post("/api/claims/{claim_id}/run", operation_id="run_claim")
def run_claim(claim_id: str) -> dict[str, Any]:
    """Start the agent on a waiting claim, in the background."""
    return runner.start_claim(claim_id)


@app.post("/api/claims/run-queue", operation_id="run_queue")
def run_queue() -> dict[str, int]:
    """Start the agent on every waiting claim, one after another, in the background."""
    return {"queued": runner.start_queue()}


@app.post("/api/claims/{claim_id}/decision", operation_id="record_decision")
def record_decision(claim_id: str, body: DecisionIn) -> dict[str, Any]:
    """Record the decision on a claim. A payout over the limit waits for sign-off."""
    return store.record_decision(
        claim_id, body.decision, body.payout, body.reason, body.policy_section
    )


@app.post("/api/claims/{claim_id}/sign-off", operation_id="sign_off")
def sign_off(claim_id: str, body: SignOffIn) -> dict[str, Any]:
    """Sign off a payout over the limit as a handler."""
    return store.sign_off(claim_id, body.handler_id)


@app.post("/api/claims/{claim_id}/payments", operation_id="pay_claim")
def pay_claim(claim_id: str, body: PaymentIn) -> dict[str, Any]:
    """Pay an approved claim, once any payout over the limit is signed off."""
    return store.pay_claim(claim_id, body.amount)


@app.post("/api/claims/{claim_id}/steps", operation_id="record_step")
def record_step(claim_id: str, body: StepIn) -> dict[str, str]:
    """Add one step to the log of what the agent did on a claim."""
    store.record_step(claim_id, body.tool, body.input, body.output)
    return {"status": "recorded"}


@app.get("/api/handlers", operation_id="list_handlers")
def list_handlers() -> list[dict[str, Any]]:
    """List the claims handlers, and who can sign off payouts over the limit."""
    return store.list_handlers()


@app.get("/api/policy-wording", operation_id="get_policy_wording")
def get_policy_wording() -> dict[str, str]:
    """Get the policy wording the agent decides claims from."""
    return {"text": store.get_policy_wording()}


@app.get("/api/instructions", operation_id="get_instructions")
def get_instructions() -> dict[str, str]:
    """Get the UnderCover Agent's instructions."""
    return {"text": INSTRUCTIONS.read_text(encoding="utf-8")}
