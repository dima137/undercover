import { useState } from "react";
import { postJson, type ClaimDetail, type Handler } from "../api";
import { formatDollars } from "../format";

interface Props {
  readonly detail: ClaimDetail;
  readonly handlers: readonly Handler[];
  readonly onAction: (request: () => Promise<unknown>, done: string) => void;
}

export function ClaimActions({ detail, handlers, onAction }: Props) {
  const path = `/api/claims/${detail.claim_id}`;
  const eligible = handlers.filter((handler) => handler.can_approve_over_limit);
  const [chosen, setChosen] = useState("");
  const handlerId = chosen || eligible[0]?.handler_id || "";

  const canRun = detail.state === "waiting";
  const canSignOff = detail.state === "waiting_for_sign_off";
  const canPay =
    detail.state === "decided" &&
    detail.decision === "approve" &&
    detail.payments.length === 0;

  function run() {
    onAction(
      () => postJson(`${path}/run`),
      "The agent has started on this claim.",
    );
  }

  function pay() {
    onAction(
      () => postJson(`${path}/payments`, { amount: detail.payout }),
      "The claim is paid.",
    );
  }

  return (
    <section className="panel stack">
      <h2>Actions</h2>
      <div className="button-row">
        <button type="button" disabled={!canRun} onClick={run}>
          Run the agent
        </button>
      </div>
      <form
        className="button-row"
        onSubmit={(event) => {
          event.preventDefault();
          onAction(
            () => postJson(`${path}/sign-off`, { handler_id: handlerId }),
            "The payout is signed off.",
          );
        }}
      >
        <label>
          Handler{" "}
          <select
            value={handlerId}
            disabled={!canSignOff}
            onChange={(event) => {
              setChosen(event.target.value);
            }}
          >
            {eligible.map((handler) => (
              <option key={handler.handler_id} value={handler.handler_id}>
                {handler.name}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={!canSignOff}>
          Sign off
        </button>
      </form>
      <div className="button-row">
        <button type="button" disabled={!canPay} onClick={pay}>
          Pay {detail.payout !== null ? formatDollars(detail.payout) : ""}
        </button>
      </div>
    </section>
  );
}
