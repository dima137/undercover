import type { ClaimDetail } from "../api";
import { formatDollars, formatTime, humanize } from "../format";

export function DecisionPanel({ detail }: Readonly<{ detail: ClaimDetail }>) {
  return (
    <section className="panel stack">
      <h2>Decision</h2>
      {detail.decision === null ? (
        <p className="muted">No decision yet.</p>
      ) : (
        <dl className="facts">
          <div>
            <dt>Decision</dt>
            <dd>{humanize(detail.decision)}</dd>
          </div>
          <div>
            <dt>Payout</dt>
            <dd className="mono">{formatDollars(detail.payout ?? 0)}</dd>
          </div>
          <div>
            <dt>Policy section</dt>
            <dd>{detail.policy_section}</dd>
          </div>
          <div>
            <dt>Signed off by</dt>
            <dd>{detail.signed_off_by ?? "Not signed off"}</dd>
          </div>
          <div className="wide">
            <dt>Reason</dt>
            <dd>{detail.reason}</dd>
          </div>
        </dl>
      )}
      {detail.payments.length > 0 && (
        <ul className="plain">
          {detail.payments.map((payment) => (
            <li key={payment.paid_at}>
              Paid <span className="mono">{formatDollars(payment.amount)}</span>{" "}
              on {formatTime(payment.paid_at)}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
