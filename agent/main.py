"""The UnderCover Agent."""

import json
import os
from typing import Any, Literal
from uuid import UUID

import httpx
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import ToolException, tool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

load_dotenv(override=True)

BACKEND_URL = "http://localhost:8000"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-6-luna"


def backend() -> httpx.Client:
    """Return a client for the UnderCover backend."""
    return httpx.Client(base_url=BACKEND_URL, timeout=10)


def api(method: str, path: str, **kwargs: Any) -> Any:
    """Call the backend and return its JSON reply, or its error message."""
    response = backend().request(method, path, **kwargs)
    if response.is_error:
        raise ToolException(response.json()["detail"])
    return response.json()


@tool
def get_claim(claim_id: str) -> str:
    """Get one claim in full: the claim, its policy, plan, customer and history."""
    return json.dumps(api("GET", f"/api/claims/{claim_id}"))


@tool
def get_policy_wording() -> str:
    """Get the policy wording. Decide the claim from this alone."""
    return api("GET", "/api/policy-wording")["text"]


@tool
def record_decision(
    claim_id: str,
    decision: Literal["approve", "decline", "refer"],
    payout: float,
    reason: str,
    policy_section: str,
) -> str:
    """Record your decision on a claim. Payout is in US dollars, or zero."""
    claim = api(
        "POST",
        f"/api/claims/{claim_id}/decision",
        json={
            "decision": decision,
            "payout": payout,
            "reason": reason,
            "policy_section": policy_section,
        },
    )
    return f"Decision recorded. The claim is now {claim['state']}."


TOOLS = [get_claim, get_policy_wording, record_decision]
for agent_tool in TOOLS:
    agent_tool.handle_tool_error = True


class StepRecorder(BaseCallbackHandler):
    """Logs each tool call on a claim to the backend as it happens."""

    def __init__(self, claim_id: str) -> None:
        self.claim_id = claim_id
        self.calls: dict[UUID, tuple[str, str]] = {}

    def on_tool_start(
        self, serialized: dict[str, Any], input_str: str, *, run_id: UUID, **kwargs: Any
    ) -> None:
        self.calls[run_id] = (serialized["name"], input_str)

    def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        tool_name, step_input = self.calls.pop(run_id)
        api(
            "POST",
            f"/api/claims/{self.claim_id}/steps",
            json={"tool": tool_name, "input": step_input, "output": output.content},
        )


def model() -> ChatOpenAI:
    """Return the model named in MODEL_NAME, or GPT-6 Luna by default."""
    name = os.getenv("MODEL_NAME")
    return ChatOpenAI(
        model=name or DEFAULT_MODEL,
        base_url=OPENROUTER_BASE_URL,
        api_key=SecretStr(os.environ["OPENROUTER_API_KEY"]),
        reasoning_effort=None if name else "low",
    )


def run(claim_id: str, thread_id: str, llm: BaseChatModel | None = None) -> str:
    """Decide one claim and return the agent's final reply."""
    agent = create_agent(
        llm or model(),
        tools=TOOLS,
        system_prompt=api("GET", "/api/instructions")["text"],
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": f"Decide claim {claim_id}."}]},
        config={
            "configurable": {"thread_id": thread_id},
            "callbacks": [StepRecorder(claim_id)],
        },
    )
    return result["messages"][-1].text
