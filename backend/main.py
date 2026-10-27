"""The UnderCover backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend import db, store

INSTRUCTIONS = Path(__file__).parent / "instructions.md"


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


@app.get("/api/policy-wording", operation_id="get_policy_wording")
def get_policy_wording() -> dict[str, str]:
    """Get the policy wording the agent decides claims from."""
    return {"text": store.get_policy_wording()}


@app.get("/api/instructions", operation_id="get_instructions")
def get_instructions() -> dict[str, str]:
    """Get the UnderCover Agent's instructions."""
    return {"text": INSTRUCTIONS.read_text(encoding="utf-8")}
