import type { ClaimDetail } from "../api";
import { formatDay, formatDollars, humanize } from "../format";

export function ClaimDetails({ detail }: Readonly<{ detail: ClaimDetail }>) {
  const { claim, policy, plan, customer } = detail;
  return (
    <>
      <section className="panel stack">
        <h2>Claim</h2>
        <p>{claim.summary}</p>
        <p>{claim.story}</p>
        <p className="muted">
          Incident on {formatDay(claim.incident_date)} in{" "}
          {claim.incident_location}
        </p>
        <h3>Items</h3>
        <ul className="plain">
          {claim.items.map((item) => (
            <li key={item.description} className="split">
              <span>
                {item.description}{" "}
                <span className="muted">{humanize(item.category)}</span>
              </span>
              <span className="mono">{formatDollars(item.amount)}</span>
            </li>
          ))}
        </ul>
        <h3>Documents</h3>
        <ul className="plain">
          {claim.documents.map((document) => (
            <li key={document.name}>
              <strong>{document.name}</strong>{" "}
              <span className="muted">{humanize(document.type)}</span>
              <p>{document.content}</p>
            </li>
          ))}
        </ul>
      </section>
      <section className="panel stack">
        <h2>Policy and customer</h2>
        <dl className="facts">
          <div>
            <dt>Plan</dt>
            <dd>{plan.name}</dd>
          </div>
          <div>
            <dt>Policy</dt>
            <dd className="mono">{policy.policy_id}</dd>
          </div>
          <div>
            <dt>Trip</dt>
            <dd>
              {policy.trip.destination}, {formatDay(policy.trip.departs_on)} to{" "}
              {formatDay(policy.trip.returns_on)}
            </dd>
          </div>
          <div>
            <dt>Travelers</dt>
            <dd>{policy.travelers.join(", ")}</dd>
          </div>
          <div>
            <dt>Add-ons</dt>
            <dd>
              {policy.add_ons.length > 0 ? policy.add_ons.join(", ") : "None"}
            </dd>
          </div>
        </dl>
        <h3>Claim history</h3>
        {customer.previous_claims.length === 0 ? (
          <p className="muted">No earlier claims.</p>
        ) : (
          <ul className="plain">
            {customer.previous_claims.map((previous) => (
              <li key={previous.claim_id}>
                <span className="mono">{previous.claim_id}</span>{" "}
                {formatDay(previous.filed_on)}, {previous.summary} (
                {humanize(previous.outcome)},{" "}
                {formatDollars(previous.amount_paid)})
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
