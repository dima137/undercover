import { vi } from "vitest";
import type { ClaimDetail, ClaimSummary, Handler } from "../api";

export const queue: ClaimSummary[] = [
  {
    claim_id: "CLM-1001",
    claim_type: "trip_delay",
    customer_name: "Maya Patel",
    amount_claimed: 420,
    state: "waiting",
    decision: null,
  },
  {
    claim_id: "CLM-1002",
    claim_type: "baggage_delay",
    customer_name: "Sam Lee",
    amount_claimed: 1250,
    state: "waiting_for_sign_off",
    decision: "approve",
  },
];

export const handlers: Handler[] = [
  {
    handler_id: "HND-01",
    name: "Dana Whitfield",
    role: "Senior Claims Handler",
    can_approve_over_limit: true,
  },
  {
    handler_id: "HND-02",
    name: "Marcus Oyelaran",
    role: "Claims Handler",
    can_approve_over_limit: false,
  },
];

export function claimDetail(overrides: Partial<ClaimDetail> = {}): ClaimDetail {
  return {
    claim_id: "CLM-1001",
    state: "waiting",
    claim: {
      claim_id: "CLM-1001",
      claim_type: "trip_delay",
      incident_date: "2026-06-18",
      incident_location: "Rome, Italy",
      summary: "Flight home canceled",
      story: "My flight was canceled and I booked a hotel.",
      items: [
        {
          description: "Airport hotel",
          category: "accommodation",
          amount: 245,
        },
      ],
      amount_claimed: 420,
      documents: [
        {
          name: "Hotel receipt",
          type: "receipt",
          content: "Total paid $245.00.",
        },
      ],
    },
    policy: {
      policy_id: "POL-2001",
      plan: "premium",
      add_ons: [],
      purchased_on: "2026-04-22",
      trip: {
        destination: "Rome, Italy",
        departs_on: "2026-06-10",
        returns_on: "2026-06-18",
      },
      travelers: ["Maya Patel"],
      status: "active",
    },
    plan: { plan: "premium", name: "UnderCover Premium" },
    customer: {
      customer_id: "CUS-3001",
      name: "Maya Patel",
      previous_claims: [],
    },
    decision: null,
    payout: null,
    reason: null,
    policy_section: null,
    signed_off_by: null,
    payments: [],
    steps: [],
    ...overrides,
  };
}

export interface Reply {
  status?: number;
  body: unknown;
}

// Answers each "METHOD /path" with its reply, and fails any request it does not know.
export function mockFetch(replies: Partial<Record<string, Reply>>) {
  return vi.fn((input: string, init?: RequestInit) => {
    const key = `${init?.method ?? "GET"} ${input}`;
    const reply = replies[key];
    if (reply === undefined) {
      return Promise.resolve(
        new Response(JSON.stringify({ detail: `Not mocked: ${key}` }), {
          status: 500,
        }),
      );
    }
    return Promise.resolve(
      new Response(JSON.stringify(reply.body), { status: reply.status ?? 200 }),
    );
  });
}
