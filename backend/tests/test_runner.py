import time

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from agent import main as agent_main
from backend import runner


class StubModel(GenericFakeChatModel):
    """A chat model that gives scripted replies in place of a real model."""

    def bind_tools(self, tools, **kwargs):
        return self


def approve_reply(claim_id):
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": "record_decision",
                "args": {
                    "claim_id": claim_id,
                    "decision": "approve",
                    "payout": 420.0,
                    "reason": "Covered.",
                    "policy_section": "2",
                },
                "id": "decide",
            }
        ],
    )


def wait_until(condition, timeout=10):
    deadline = time.monotonic() + timeout
    while not condition():
        assert time.monotonic() < deadline, "timed out"
        time.sleep(0.05)


@pytest.fixture
def stub_agent(client, monkeypatch):
    """Run the real agent against the test backend, with a stub model that approves."""
    monkeypatch.setattr(agent_main, "backend", lambda: client)

    def run(claim_id, thread_id):
        replies = [approve_reply(claim_id), AIMessage(content="Approved.")]
        return agent_main.run(claim_id, thread_id, StubModel(messages=iter(replies)))

    monkeypatch.setattr(runner, "run_agent", run)
    return client


def state(client, claim_id):
    return client.get(f"/api/claims/{claim_id}").json()["state"]


def test_a_run_is_in_progress_then_decided(stub_agent):
    started = stub_agent.post("/api/claims/CLM-1001/run")
    assert started.json()["state"] == "in_progress"
    wait_until(lambda: state(stub_agent, "CLM-1001") == "decided")
    steps = stub_agent.get("/api/claims/CLM-1001").json()["steps"]
    assert [step["tool"] for step in steps] == ["record_decision"]


def test_a_claim_already_in_progress_cannot_be_started_again(stub_agent):
    stub_agent.post("/api/claims/CLM-1001/run")
    response = stub_agent.post("/api/claims/CLM-1001/run")
    assert response.status_code == 409


def test_a_failed_run_returns_the_claim_to_waiting(client, monkeypatch):
    def fail(claim_id, thread_id):
        raise RuntimeError("boom")

    monkeypatch.setattr(runner, "run_agent", fail)
    client.post("/api/claims/CLM-1001/run")
    wait_until(lambda: len(client.get("/api/claims/CLM-1001").json()["steps"]) == 2)
    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["state"] == "waiting"
    assert claim["steps"][0]["tool"] == "run_failed"
    assert claim["steps"][0]["output"] == "boom"


def test_a_run_without_a_decision_returns_the_claim_to_waiting(client, monkeypatch):
    monkeypatch.setattr(runner, "run_agent", lambda claim_id, thread_id: "Unsure.")
    client.post("/api/claims/CLM-1001/run")
    wait_until(lambda: len(client.get("/api/claims/CLM-1001").json()["steps"]) == 1)
    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["state"] == "waiting"
    assert claim["steps"][0]["tool"] == "run_ended"


def test_the_queue_runs_every_waiting_claim(stub_agent):
    response = stub_agent.post("/api/claims/run-queue")
    assert response.json() == {"queued": 25}
    wait_until(
        lambda: (
            [claim["state"] for claim in stub_agent.get("/api/claims").json()]
            == ["decided"] * 25
        )
    )
