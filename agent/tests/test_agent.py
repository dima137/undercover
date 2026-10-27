from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from agent import main


class StubModel(GenericFakeChatModel):
    """A chat model that gives scripted replies in place of a real model."""

    def bind_tools(self, tools, **kwargs):
        return self


def call(name, args, call_id):
    return AIMessage(
        content="", tool_calls=[{"name": name, "args": args, "id": call_id}]
    )


def approve(payout):
    return call(
        "record_decision",
        {
            "claim_id": "CLM-1001",
            "decision": "approve",
            "payout": payout,
            "reason": "Covered.",
            "policy_section": "2",
        },
        "decide",
    )


def test_get_claim_tool(client, monkeypatch):
    monkeypatch.setattr(main, "backend", lambda: client)
    assert "CLM-1001" in main.get_claim.invoke({"claim_id": "CLM-1001"})


def test_run_decides_the_claim_and_logs_each_step(client, monkeypatch):
    monkeypatch.setattr(main, "backend", lambda: client)
    replies = [
        call("get_policy_wording", {}, "1"),
        approve(420.0),
        AIMessage(content="Approved."),
    ]
    assert main.run("CLM-1001", "t1", StubModel(messages=iter(replies))) == "Approved."
    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["state"] == "decided"
    assert claim["payout"] == 420.0
    assert [step["tool"] for step in claim["steps"]] == [
        "get_policy_wording",
        "record_decision",
    ]


def test_payment_over_the_limit_is_not_made(client, monkeypatch):
    monkeypatch.setattr(main, "backend", lambda: client)
    pay = call("pay_claim", {"claim_id": "CLM-1001", "amount": 1250.0}, "2")
    replies = [approve(1250.0), pay, AIMessage(content="Waiting for sign-off.")]
    main.run("CLM-1001", "t2", StubModel(messages=iter(replies)))
    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["state"] == "waiting_for_sign_off"
    assert claim["payments"] == []


def test_refused_decision_is_returned_to_the_model(client, monkeypatch):
    monkeypatch.setattr(main, "backend", lambda: client)
    refused = call(
        "record_decision",
        {
            "claim_id": "CLM-1001",
            "decision": "decline",
            "payout": 10.0,
            "reason": "No.",
            "policy_section": "2",
        },
        "1",
    )
    replies = [refused, AIMessage(content="Could not record it.")]
    assert (
        main.run("CLM-1001", "t3", StubModel(messages=iter(replies)))
        == "Could not record it."
    )
    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["state"] == "waiting"
    assert claim["steps"][0]["output"] == "Only an approval can carry a payout"


def test_unknown_tool_ends_the_run_without_a_crash(client, monkeypatch):
    monkeypatch.setattr(main, "backend", lambda: client)
    replies = [call("nonexistent", {}, "1"), AIMessage(content="Done.")]
    assert main.run("CLM-1001", "t4", StubModel(messages=iter(replies))) == "Done."
    assert client.get("/api/claims/CLM-1001").json()["state"] == "waiting"


def test_model_name(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("MODEL_NAME", raising=False)
    assert main.model().model_name == "openai/gpt-6-luna"
    monkeypatch.setenv("MODEL_NAME", "openrouter/free")
    assert main.model().model_name == "openrouter/free"
