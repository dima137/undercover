import { useResource } from "../hooks";

export function InstructionsPage() {
  const instructions = useResource<{ text: string }>("/api/instructions", 0);

  if (instructions.error) {
    return <p className="notice alert">{instructions.error}</p>;
  }
  return (
    <section className="stack">
      <h1>Agent instructions</h1>
      <p className="muted">
        Read only. The agent follows these on every claim.
      </p>
      <pre className="panel">{instructions.data?.text ?? "Loading…"}</pre>
    </section>
  );
}
