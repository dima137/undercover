import { expect, test, type APIRequestContext } from "@playwright/test";

// The backend runs in its own process, so the agent cannot be stubbed here.
// These tests record the agent's decisions through the API instead.
async function decide(
  request: APIRequestContext,
  claimId: string,
  payout: number,
) {
  const response = await request.post(`/api/claims/${claimId}/decision`, {
    data: {
      decision: "approve",
      payout,
      reason: "Covered by the plan.",
      policy_section: "2",
    },
  });
  expect(response.ok()).toBe(true);
}

test("a payout over $1,000 waits for a handler's sign-off", async ({
  page,
  request,
}) => {
  await decide(request, "CLM-1003", 1250);
  await page.goto("/#/claims/CLM-1003");
  await expect(page.getByText("Waiting for sign-off").first()).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Pay $1,250.00" }),
  ).toBeDisabled();
});

test("a signed-off payout can be paid", async ({ page, request }) => {
  await decide(request, "CLM-1011", 1500);
  await page.goto("/#/claims/CLM-1011");
  await page.getByRole("button", { name: "Sign off" }).click();
  await expect(page.getByText("The payout is signed off.")).toBeVisible();

  const pay = page.getByRole("button", { name: "Pay $1,500.00" });
  await expect(pay).toBeEnabled();
  await pay.click();
  await expect(page.getByText("The claim is paid.")).toBeVisible();
  await expect(pay).toBeDisabled();
});

test("an approved claim shows its decision and the agent's steps", async ({
  page,
  request,
}) => {
  await decide(request, "CLM-1001", 420);
  await request.post("/api/claims/CLM-1001/steps", {
    data: { tool: "record_decision", input: "{}", output: "ok" },
  });
  await page.goto("/#/claims/CLM-1001");
  await expect(page.getByText("Approved").first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Pay $420.00" })).toBeEnabled();
  await expect(page.getByText("record_decision")).toBeVisible();
});

test("the agent's instructions are read only", async ({ page }) => {
  await page.goto("/#/instructions");
  await expect(
    page.getByRole("heading", { name: "Agent instructions" }),
  ).toBeVisible();
  await expect(
    page.locator("main input, main textarea, main select"),
  ).toHaveCount(0);
});
