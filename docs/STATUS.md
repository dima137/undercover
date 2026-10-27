# Status

Building the claims pilot from `docs/PLAN.md`, one phase at a time.

## Built

- Phase 1: the backend loads the pilot data into SQLite on startup, and serves the queue, each claim in full, the policy wording and the agent's instructions.
- Phase 2: the backend records decisions, sign-offs and payments, with the payment gate, and logs the agent's steps. It also lists the handlers. Money is in dollars throughout.
- Phase 3: the UnderCover Agent, on `create_agent` and OpenRouter. It has three tools, each a backend call: get a claim, get the policy wording, and record a decision. Its instructions come from `backend/instructions.md`. Each tool call is logged to the claim as it happens. The agent has no payment tool.

- Phase 4: the agent runs in the background. `POST /api/claims/{id}/run` starts one claim, and `POST /api/claims/run-queue` works every waiting claim in turn. A run that fails, or ends without a decision, returns its claim to waiting and logs why.

- Phase 5: the dashboard. The queue shows each state with its count and can run the queue. A claim page shows the claim in full, the decision, the payment, the agent's activity, and three actions: run the agent, sign off and pay. Instructions are read only. The screens follow `docs/BRAND.md`, with light and dark colour tokens.

- Phase 6: five end-to-end tests in `e2e/`, covering the queue, the sign-off gate, a signed-off payment, a decided claim, and the read-only instructions.

## Not built yet

- The live run of the agent against OpenRouter (Phase 3's last criterion). It costs API money, so it is left to the student.

## Claim states

- `waiting`, `in_progress`, `waiting_for_sign_off`, then the result: `approved`, `declined` or `docs_missing`. A refer decision is `docs_missing`. This follows the correction in `docs/SPEC.md`, which replaces "decided".

## Running it

- `npm run check` runs every check.

- `npm run dev` starts the backend and the dashboard, at http://localhost:5173.
- The backend rebuilds its database from `data/` each time it starts. The database is `backend/undercover.db`.
- A live run of the agent calls OpenRouter and costs API money. To try one routine claim, with the backend running: `uv run python -c "from agent.main import run; print(run('CLM-1001', 'live'))"`.
