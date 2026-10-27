import type { Step } from "../api";
import { formatTime } from "../format";

export function ActivityLog({ steps }: Readonly<{ steps: Step[] }>) {
  return (
    <section className="panel stack">
      <h2>Agent activity</h2>
      {steps.length === 0 ? (
        <p className="muted">The agent has not worked on this claim yet.</p>
      ) : (
        <ol className="plain steps">
          {steps.map((step, index) => (
            <li key={index}>
              <div className="split">
                <span className="mono">{step.tool}</span>
                <span className="muted">{formatTime(step.created_at)}</span>
              </div>
              {step.input && <pre>{step.input}</pre>}
              <pre>{step.output}</pre>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
