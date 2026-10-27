import type { ClaimState } from "./api";

const dollars = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

const stateLabels: Record<ClaimState, string> = {
  waiting: "Waiting",
  in_progress: "In progress",
  waiting_for_sign_off: "Waiting for sign-off",
  approved: "Approved",
  declined: "Declined",
  docs_missing: "Docs missing",
};

export function formatDollars(amount: number): string {
  return dollars.format(amount);
}

export function stateLabel(state: ClaimState): string {
  return stateLabels[state];
}

export function formatDay(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    dateStyle: "medium",
    timeZone: "UTC",
  });
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  });
}

export function humanize(text: string): string {
  const spaced = text.replace(/_/g, " ");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

export function messageOf(problem: unknown): string {
  return problem instanceof Error ? problem.message : "Something went wrong";
}
