export type ClaimState =
  | "waiting"
  | "in_progress"
  | "waiting_for_sign_off"
  | "approved"
  | "declined"
  | "docs_missing";

export type Decision = "approve" | "decline" | "refer";

export interface ClaimSummary {
  claim_id: string;
  claim_type: string;
  customer_name: string;
  amount_claimed: number;
  state: ClaimState;
  decision: Decision | null;
}

export interface ClaimItem {
  description: string;
  category: string;
  amount: number;
}

export interface ClaimDocument {
  name: string;
  type: string;
  content: string;
}

export interface ClaimRecord {
  claim_id: string;
  claim_type: string;
  incident_date: string;
  incident_location: string;
  summary: string;
  story: string;
  items: ClaimItem[];
  amount_claimed: number;
  documents: ClaimDocument[];
}

export interface PreviousClaim {
  claim_id: string;
  filed_on: string;
  claim_type: string;
  summary: string;
  outcome: string;
  amount_paid: number;
}

export interface Customer {
  customer_id: string;
  name: string;
  previous_claims: PreviousClaim[];
}

export interface Policy {
  policy_id: string;
  plan: string;
  add_ons: string[];
  purchased_on: string;
  trip: { destination: string; departs_on: string; returns_on: string };
  travelers: string[];
  status: string;
}

export interface Plan {
  plan: string;
  name: string;
}

export interface Payment {
  amount: number;
  paid_at: string;
}

export interface Step {
  tool: string;
  input: string;
  output: string;
  created_at: string;
}

export interface ClaimDetail {
  claim_id: string;
  state: ClaimState;
  claim: ClaimRecord;
  policy: Policy;
  plan: Plan;
  customer: Customer;
  decision: Decision | null;
  payout: number | null;
  reason: string | null;
  policy_section: string | null;
  signed_off_by: string | null;
  payments: Payment[];
  steps: Step[];
}

export interface Handler {
  handler_id: string;
  name: string;
  role: string;
  can_approve_over_limit: boolean;
}

export async function getJson<T>(path: string): Promise<T> {
  return readJson<T>(await fetch(path));
}

export async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  return readJson<T>(response);
}

async function readJson<T>(response: Response): Promise<T> {
  const body: unknown = await response.json();
  if (!response.ok) {
    throw new Error(errorDetail(body));
  }
  return body as T;
}

function errorDetail(body: unknown): string {
  if (typeof body === "object" && body !== null && "detail" in body) {
    if (typeof body.detail === "string") {
      return body.detail;
    }
  }
  return "The request failed";
}
