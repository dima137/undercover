# Status

Building the claims pilot from `docs/PLAN.md`, one phase at a time.

## Built

- Phase 1: the backend loads the pilot data into SQLite on startup, and serves the queue, each claim in full, the policy wording and the agent's instructions.

## Not built yet

- Phase 2: recording decisions, sign-off and the payment gate.
- Phases 3 to 6: the agent, running the queue, the dashboard, and the end-to-end tests.

## Running it

- `npm run dev` starts the backend and the dashboard.
- The backend rebuilds its database from `data/` each time it starts. The database is `backend/undercover.db`.
