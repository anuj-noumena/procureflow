import { test, expect, type Page } from "@playwright/test";
async function login(page: Page, handle: string) {
  await page.goto("/login");
  await page.getByLabel("Workspace slug").fill("northline");
  await page
    .getByLabel("Email", { exact: true })
    .fill(handle + "@northline.example");
  await page.getByLabel("Password").fill(process.env.PF_E2E_PASSWORD!);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(
    page.getByRole("heading", { name: "Procurement overview" }),
  ).toBeVisible();
}
test.beforeEach(async ({ context }) => {
  await context.route("**/*", (route) => {
    const host = new URL(route.request().url()).hostname;
    return host === "127.0.0.1" || host === "localhost"
      ? route.continue()
      : route.abort();
  });
});
test("requester drafts and submits, assigned reviewer approves, history persists after reload", async ({
  page,
}) => {
  await login(page, "requester");
  await expect(page.getByRole("link", { name: "User management" })).toHaveCount(
    0,
  );
  await page.getByRole("link", { name: "New requisition" }).click();
  await page
    .getByLabel("Description", { exact: true })
    .fill("Browser verification purchase");
  await page.getByLabel("Required date").fill("2027-04-01");
  await page.getByLabel("Line description").fill("Safety binders");
  await page.getByLabel("Quantity").fill("3");
  await page.getByLabel("Unit price").fill("14.50");
  await page.getByRole("button", { name: "Save draft" }).click();
  await expect(page.getByText("USD 43.50")).toBeVisible();
  await page.getByRole("button", { name: "Submit for approval" }).click();
  await page
    .getByLabel("Assigned approver")
    .selectOption({ label: "Casey Morgan" });
  await page.getByRole("button", { name: "Confirm submission" }).click();
  await expect(page.locator(".status")).toHaveText("Pending approval");
  await page.getByRole("button", { name: "Sign out" }).click();
  await login(page, "reviewer");
  await page.getByRole("link", { name: "Approvals", exact: true }).click();
  await page
    .getByRole("link", { name: "Browser verification purchase" })
    .click();
  await page.getByLabel("Review comment").fill("Within budget.");
  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await page.getByRole("button", { name: "Confirm decision" }).click();
  await expect(page.locator(".status")).toHaveText("Approved");
  await page.reload();
  await expect(page.getByText("Within budget.")).toBeVisible();
});
test("buyer registers, finds and deactivates a supplier", async ({ page }) => {
  await login(page, "buyer");
  await page.getByRole("link", { name: "Suppliers", exact: true }).click();
  await page.getByRole("button", { name: "Add supplier" }).click();
  await page.getByLabel("Name", { exact: true }).fill("Browser Supply Co");
  await page.getByLabel("Category", { exact: true }).fill("Stationery");
  await page.getByLabel("Status", { exact: true }).selectOption("active");
  await page.getByRole("button", { name: "Save supplier" }).click();
  await page.getByLabel("Search directory").fill("Browser Supply");
  await page.getByRole("button", { name: "Open Browser Supply Co" }).click();
  await page.getByLabel("Status", { exact: true }).selectOption("inactive");
  await page.getByRole("button", { name: "Save supplier" }).click();
  await expect(page.locator("tbody .status")).toHaveText("Inactive");
});
test("mobile navigation and catalog creation", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page, "admin");
  await page.getByRole("button", { name: "Toggle navigation" }).click();
  await page.getByRole("link", { name: "Catalog", exact: true }).click();
  await page.getByRole("button", { name: "Add item" }).click();
  await page.getByLabel("Name", { exact: true }).fill("Printer service");
  await page.getByLabel("Category").fill("Maintenance");
  await page.getByLabel("Item code").fill("BR-001");
  await page.getByLabel("Type", { exact: true }).selectOption("service");
  await page.getByLabel("Reference price").fill("60.25");
  await page.getByRole("button", { name: "Save item" }).click();
  await expect(
    page.getByText("Printer service", { exact: true }),
  ).toBeVisible();
});
