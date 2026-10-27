import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { claimDetail, handlers, mockFetch, queue } from "./test/fixtures";

beforeEach(() => {
  window.location.hash = "#/claims";
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("lists the queue with its counts", async () => {
  vi.stubGlobal("fetch", mockFetch({ "GET /api/claims": { body: queue } }));
  render(<App />);
  expect(await screen.findByText("CLM-1001")).toBeDefined();
  expect(screen.getByText("Sam Lee")).toBeDefined();
  expect(screen.getAllByText("Waiting").length).toBeGreaterThan(0);
});

it("starts the queue and says how many claims it started", async () => {
  const fetchMock = mockFetch({
    "GET /api/claims": { body: queue },
    "POST /api/claims/run-queue": { body: { queued: 1 } },
  });
  vi.stubGlobal("fetch", fetchMock);
  render(<App />);
  fireEvent.click(await screen.findByText("Run the queue"));
  expect(
    await screen.findByText("The agent started on 1 waiting claims."),
  ).toBeDefined();
});

it("shows a failed queue start", async () => {
  vi.stubGlobal(
    "fetch",
    mockFetch({
      "GET /api/claims": { body: queue },
      "POST /api/claims/run-queue": { status: 409, body: { detail: "Busy" } },
    }),
  );
  render(<App />);
  fireEvent.click(await screen.findByText("Run the queue"));
  expect(await screen.findByText("Busy")).toBeDefined();
});

it("shows an error when the queue cannot load", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.reject(new Error("offline"))),
  );
  render(<App />);
  expect(await screen.findByText("offline")).toBeDefined();
});

it("opens a claim in full and disables the actions that do not apply", async () => {
  vi.stubGlobal(
    "fetch",
    mockFetch({
      "GET /api/claims/CLM-1001": { body: claimDetail() },
      "GET /api/handlers": { body: handlers },
    }),
  );
  window.location.hash = "#/claims/CLM-1001";
  render(<App />);
  expect(await screen.findByText("Flight home canceled")).toBeDefined();
  expect(screen.getByText("No decision yet.")).toBeDefined();
  expect(
    screen.getByText("The agent has not worked on this claim yet."),
  ).toBeDefined();
  expect(
    screen
      .getByRole("button", { name: "Run the agent" })
      .hasAttribute("disabled"),
  ).toBe(false);
  expect(
    screen.getByRole("button", { name: "Sign off" }).hasAttribute("disabled"),
  ).toBe(true);
  expect(
    screen.getByRole("button", { name: "Pay" }).hasAttribute("disabled"),
  ).toBe(true);
});

it("shows an unknown claim as an error", async () => {
  vi.stubGlobal(
    "fetch",
    mockFetch({
      "GET /api/claims/CLM-0000": {
        status: 404,
        body: { detail: "No claim CLM-0000" },
      },
      "GET /api/handlers": { body: handlers },
    }),
  );
  window.location.hash = "#/claims/CLM-0000";
  render(<App />);
  expect(await screen.findByText("No claim CLM-0000")).toBeDefined();
});

it("runs the agent on a waiting claim", async () => {
  const fetchMock = mockFetch({
    "GET /api/claims/CLM-1001": { body: claimDetail() },
    "GET /api/handlers": { body: handlers },
    "POST /api/claims/CLM-1001/run": {
      body: claimDetail({ state: "in_progress" }),
    },
  });
  vi.stubGlobal("fetch", fetchMock);
  window.location.hash = "#/claims/CLM-1001";
  render(<App />);
  fireEvent.click(await screen.findByText("Run the agent"));
  expect(
    await screen.findByText("The agent has started on this claim."),
  ).toBeDefined();
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/claims/CLM-1001/run",
    expect.objectContaining({ method: "POST" }),
  );
});

it("signs off a payout with a handler who has the authority", async () => {
  const fetchMock = mockFetch({
    "GET /api/claims/CLM-1002": {
      body: claimDetail({
        claim_id: "CLM-1002",
        state: "waiting_for_sign_off",
        decision: "approve",
        payout: 1250,
        policy_section: "3",
        reason: "Covered.",
      }),
    },
    "GET /api/handlers": { body: handlers },
    "POST /api/claims/CLM-1002/sign-off": { body: {} },
  });
  vi.stubGlobal("fetch", fetchMock);
  window.location.hash = "#/claims/CLM-1002";
  render(<App />);
  const signOff = await screen.findByRole("button", { name: "Sign off" });
  expect(signOff.hasAttribute("disabled")).toBe(false);
  expect(screen.queryByText("Marcus Oyelaran")).toBeNull();
  fireEvent.click(signOff);
  expect(await screen.findByText("The payout is signed off.")).toBeDefined();
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/claims/CLM-1002/sign-off",
    expect.objectContaining({ body: JSON.stringify({ handler_id: "HND-01" }) }),
  );
});

it("pays an approved claim and reports a refused payment", async () => {
  const approved = claimDetail({
    state: "decided",
    decision: "approve",
    payout: 420,
    policy_section: "2",
    reason: "Covered.",
  });
  vi.stubGlobal(
    "fetch",
    mockFetch({
      "GET /api/claims/CLM-1001": { body: approved },
      "GET /api/handlers": { body: handlers },
      "POST /api/claims/CLM-1001/payments": {
        status: 409,
        body: { detail: "The approved payout is $420.00" },
      },
    }),
  );
  window.location.hash = "#/claims/CLM-1001";
  render(<App />);
  const pay = await screen.findByRole("button", { name: "Pay $420.00" });
  expect(pay.hasAttribute("disabled")).toBe(false);
  fireEvent.click(pay);
  expect(
    await screen.findByText("The approved payout is $420.00"),
  ).toBeDefined();
});

it("shows the decision, the steps and the policy and customer", async () => {
  vi.stubGlobal(
    "fetch",
    mockFetch({
      "GET /api/claims/CLM-1001": {
        body: claimDetail({
          state: "decided",
          decision: "approve",
          payout: 420,
          policy_section: "2",
          reason: "Covered by the trip delay benefit.",
          payments: [{ amount: 420, paid_at: "2026-10-27T06:00:00+00:00" }],
          customer: {
            customer_id: "CUS-3001",
            name: "Maya Patel",
            previous_claims: [
              {
                claim_id: "CLM-0412",
                filed_on: "2024-08-19",
                claim_type: "baggage_delay",
                summary: "Checked bag late",
                outcome: "approved",
                amount_paid: 140,
              },
            ],
          },
          steps: [
            {
              tool: "record_decision",
              input: "{}",
              output: "ok",
              created_at: "2026-10-27T06:00:00+00:00",
            },
          ],
        }),
      },
      "GET /api/handlers": { body: handlers },
    }),
  );
  window.location.hash = "#/claims/CLM-1001";
  render(<App />);
  expect(
    await screen.findByText("Covered by the trip delay benefit."),
  ).toBeDefined();
  expect(screen.getByText("UnderCover Premium")).toBeDefined();
  expect(screen.getByText("record_decision")).toBeDefined();
  expect(screen.getByText("Checked bag late", { exact: false })).toBeDefined();
  expect(screen.getAllByText("$420.00").length).toBeGreaterThan(0);
});

it("moves between the queue, a claim and the instructions", async () => {
  vi.stubGlobal(
    "fetch",
    mockFetch({
      "GET /api/claims": { body: queue },
      "GET /api/instructions": { body: { text: "Decide from the wording." } },
    }),
  );
  render(<App />);
  await screen.findByText("CLM-1001");
  act(() => {
    window.location.hash = "#/instructions";
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  });
  expect(await screen.findByText("Decide from the wording.")).toBeDefined();
  expect(
    screen.getByText("Read only. The agent follows these on every claim."),
  ).toBeDefined();
});
