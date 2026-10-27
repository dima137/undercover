import { expect, test } from "@playwright/test";

test("the queue lists the 25 claims", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Claims queue" }),
  ).toBeVisible();
  await expect(page.locator(".rows > li")).toHaveCount(25);
});
