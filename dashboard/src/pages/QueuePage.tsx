import { useState } from "react";
import { postJson, type ClaimState, type ClaimSummary } from "../api";
import { StateChip } from "../components/StateChip";
import { formatDollars, humanize, messageOf } from "../format";
import { useResource } from "../hooks";

const STATES: ClaimState[] = [
  "waiting",
  "in_progress",
  "waiting_for_sign_off",
  "approved",
  "declined",
  "docs_missing",
];

export function QueuePage() {
  const queue = useResource<ClaimSummary[]>("/api/claims");
  const [notice, setNotice] = useState<string>();

  async function runQueue() {
    try {
      const result = await postJson<{ queued: number }>(
        "/api/claims/run-queue",
      );
      setNotice(
        `The agent started on ${String(result.queued)} waiting claims.`,
      );
    } catch (problem: unknown) {
      setNotice(messageOf(problem));
    }
    queue.reload();
  }

  if (queue.error) {
    return <p className="notice alert">{queue.error}</p>;
  }
  if (!queue.data) {
    return <p>Loading the queue…</p>;
  }
  const claims = queue.data;

  return (
    <section className="stack">
      <div className="page-head">
        <h1>Claims queue</h1>
        <button type="button" onClick={() => void runQueue()}>
          Run the queue
        </button>
      </div>
      {notice && <p className="notice">{notice}</p>}
      <ul className="counts">
        {STATES.map((state) => (
          <li key={state} className="panel count">
            <span className="count-number mono">
              {claims.filter((claim) => claim.state === state).length}
            </span>
            <StateChip state={state} />
          </li>
        ))}
      </ul>
      <ul className="rows">
        {claims.map((claim) => (
          <li key={claim.claim_id}>
            <a className="panel row" href={`#/claims/${claim.claim_id}`}>
              <span className="mono">{claim.claim_id}</span>
              <span>{claim.customer_name}</span>
              <span className="muted">{humanize(claim.claim_type)}</span>
              <span className="mono">
                {formatDollars(claim.amount_claimed)}
              </span>
              <StateChip state={claim.state} />
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}
