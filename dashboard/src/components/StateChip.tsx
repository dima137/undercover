import type { ClaimState } from "../api";
import { stateLabel } from "../format";

export function StateChip({ state }: Readonly<{ state: ClaimState }>) {
  return <span className={`chip chip-${state}`}>{stateLabel(state)}</span>;
}
