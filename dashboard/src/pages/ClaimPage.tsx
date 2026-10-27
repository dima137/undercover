import { useState } from "react";
import type { ClaimDetail, Handler } from "../api";
import { ClaimActions } from "../components/ClaimActions";
import { ClaimDetails } from "../components/ClaimDetails";
import { ActivityLog } from "../components/ActivityLog";
import { DecisionPanel } from "../components/DecisionPanel";
import { StateChip } from "../components/StateChip";
import { formatDollars, humanize, messageOf } from "../format";
import { useResource } from "../hooks";

export function ClaimPage({ claimId }: Readonly<{ claimId: string }>) {
  const claim = useResource<ClaimDetail>(`/api/claims/${claimId}`);
  const handlers = useResource<Handler[]>("/api/handlers", 0);
  const [notice, setNotice] = useState<string>();

  if (claim.error) {
    return <p className="notice alert">{claim.error}</p>;
  }
  if (!claim.data) {
    return <p>Loading the claim…</p>;
  }
  const detail = claim.data;

  async function act(request: () => Promise<unknown>, done: string) {
    try {
      await request();
      setNotice(done);
    } catch (problem: unknown) {
      setNotice(messageOf(problem));
    }
    claim.reload();
  }

  return (
    <section className="stack">
      <a href="#/claims">Back to the queue</a>
      <header className="page-head">
        <div>
          <p className="mono muted">{detail.claim_id}</p>
          <h1>{humanize(detail.claim.claim_type)}</h1>
          <p>
            {detail.customer.name} ·{" "}
            <span className="mono">
              {formatDollars(detail.claim.amount_claimed)}
            </span>{" "}
            claimed
          </p>
        </div>
        <StateChip state={detail.state} />
      </header>
      {notice && <p className="notice">{notice}</p>}
      <ClaimActions
        detail={detail}
        handlers={handlers.data ?? []}
        onAction={(request, done) => void act(request, done)}
      />
      <DecisionPanel detail={detail} />
      <ClaimDetails detail={detail} />
      <ActivityLog steps={detail.steps} />
    </section>
  );
}
