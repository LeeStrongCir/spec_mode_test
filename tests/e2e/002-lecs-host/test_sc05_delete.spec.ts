import { test, expect } from "@playwright/test";

test.describe("SC-05: Safe Host Deletion", () => {
  const TEST_HOST_IDS = {
    normal: "host-normal-001",
    stopped: "host-stopped-002",
    failed: "host-failed-003",
  };

  test.beforeEach(async ({ page }) => {
    await page.goto("/console/lecs-hosts/list");
    await page.waitForSelector("[data-testid='host-table']", { state: "visible" });
  });

  test.describe("TC-040: Running host deletion blocked", () => {
    test("normal host delete button is disabled", async ({ page }) => {
      const deleteBtn = page.locator(`[data-testid='btn-delete-${TEST_HOST_IDS.normal}']`);
      await expect(deleteBtn).toBeVisible();
      await expect(deleteBtn).toBeDisabled();
    });

    test("normal host shows correct action button states", async ({ page }) => {
      const stopBtn = page.locator(`[data-testid='btn-stop-${TEST_HOST_IDS.normal}']`);
      const startBtn = page.locator(`[data-testid='btn-start-${TEST_HOST_IDS.normal}']`);
      const deleteBtn = page.locator(`[data-testid='btn-delete-${TEST_HOST_IDS.normal}']`);

      await expect(stopBtn).toBeEnabled();
      await expect(startBtn).toBeDisabled();
      await expect(deleteBtn).toBeDisabled();
    });
  });

  test.describe("TC-041: Stopped host async soft-delete", () => {
    test("stopped host delete button is enabled", async ({ page }) => {
      const deleteBtn = page.locator(`[data-testid='btn-delete-${TEST_HOST_IDS.stopped}']`);
      await expect(deleteBtn).toBeVisible();
      await expect(deleteBtn).toBeEnabled();
    });

    test("full delete flow: confirm dialog, deleting state, row disappears", async ({ page }) => {
      const deleteBtn = page.locator(`[data-testid='btn-delete-${TEST_HOST_IDS.stopped}']`);
      const hostRow = page.locator(`[data-testid='host-row-${TEST_HOST_IDS.stopped}']`);

      await expect(hostRow).toBeVisible();
      await deleteBtn.click();

      const confirmDialog = page.locator("[data-testid='confirm-dialog']");
      await expect(confirmDialog).toBeVisible();

      const confirmBtn = page.locator("[data-testid='confirm-btn-yes']");
      await expect(confirmBtn).toBeVisible();
      await confirmBtn.click();

      await expect(confirmDialog).not.toBeVisible();

      const statusBadge = hostRow.locator("[data-testid='status-badge']");
      await expect(statusBadge).toHaveText(/删除中/);

      const allBtns = hostRow.locator("[data-testid^='btn-']");
      const count = await allBtns.count();
      for (let i = 0; i < count; i++) {
        await expect(allBtns.nth(i)).toBeDisabled();
      }

      const responsePromise = page.waitForResponse(
        (resp) =>
          resp.url().includes(`/api/v1/lecs-hosts/${TEST_HOST_IDS.stopped}`) &&
          resp.request().method() === "DELETE" &&
          resp.status() === 202
      );
      await responsePromise;

      await expect(hostRow).not.toBeVisible({ timeout: 15000 });

      await expect(page).toHaveURL(/\/console\/lecs-hosts\/list/);
    });
  });

  test.describe("TC-042: Failed host delete flow", () => {
    test("failed host delete is enabled, other buttons disabled", async ({ page }) => {
      const deleteBtn = page.locator(`[data-testid='btn-delete-${TEST_HOST_IDS.failed}']`);
      const stopBtn = page.locator(`[data-testid='btn-stop-${TEST_HOST_IDS.failed}']`);
      const startBtn = page.locator(`[data-testid='btn-start-${TEST_HOST_IDS.failed}']`);

      await expect(deleteBtn).toBeEnabled();
      await expect(stopBtn).toBeDisabled();
      await expect(startBtn).toBeDisabled();
    });

    test("cancel delete does not change state", async ({ page }) => {
      const deleteBtn = page.locator(`[data-testid='btn-delete-${TEST_HOST_IDS.failed}']`);
      const hostRow = page.locator(`[data-testid='host-row-${TEST_HOST_IDS.failed}']`);

      await deleteBtn.click();
      const confirmDialog = page.locator("[data-testid='confirm-dialog']");
      await expect(confirmDialog).toBeVisible();

      const cancelBtn = page.locator("[data-testid='confirm-btn-cancel']");
      await cancelBtn.click();
      await expect(confirmDialog).not.toBeVisible();
      await expect(hostRow).toBeVisible();
    });
  });
});
