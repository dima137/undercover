# Status

Building the claims pilot from `docs/PLAN.md`, one phase at a time.

## Built

- Phase 1: the backend loads the pilot data into SQLite on startup, and serves the queue, each claim in full, the policy wording and the agent's instructions.
- Phase 2: the backend records decisions, sign-offs and payments, with the payment gate, and logs the agent's steps. It also lists the handlers. Money is in dollars throughout.
- Phase 3: the UnderCover Agent, on `create_agent` and OpenRouter. It has three tools, each a backend call: get a claim, get the policy wording, and record a decision. Its instructions come from `backend/instructions.md`. Each tool call is logged to the claim as it happens. The agent has no payment tool.

## Not built yet

- Phase 4: running the queue in the background.
- Phases 5 and 6: the dashboard, and the end-to-end tests.

## Running it

- `npm run dev` starts the backend and the dashboard.
- The backend rebuilds its database from `data/` each time it starts. The database is `backend/undercover.db`.
- A live run of the agent calls OpenRouter and costs API money. To try one routine claim, with the backend running: `uv run python -c "from agent.main import run; print(run('CLM-1001', 'live'))"`.
