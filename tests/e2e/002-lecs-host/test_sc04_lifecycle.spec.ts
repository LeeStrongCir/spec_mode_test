import { test, expect, Page } from "@playwright/test";

const STATUS_LABEL = "[data-testid='status-label']";
const BTN_STOP = "[data-testid='btn-stop']";
const BTN_START = "[data-testid='btn-start']";
const BTN_DELETE = "[data-testid='btn-delete']";

const POLL_INTERVAL_MS = 3000;
const POLL_MAX_MS = 30000;

async function waitForStatus(page: Page, expectedText: string) {
  const deadline = Date.now() + POLL_MAX_MS;
  while (Date.now() < deadline) {
    const label = await page.locator(STATUS_LABEL).first();
    const visible = await label.isVisible().catch(() => false);
    if (visible) {
      const text = (await label.textContent()) || "";
      if (text.includes(expectedText)) return;
    }
    await page.waitForTimeout(POLL_INTERVAL_MS);
  }
  throw new Error(
    `Timed out waiting for status "${expectedText}" after ${POLL_MAX_MS}ms`
  );
}

async function confirmDialog(page: Page) {
  const dialog = page.locator('[role="dialog"], .modal, [class*="dialog"]');
  if (await dialog.isVisible().catch(() => false)) {
    const confirmBtn = dialog.locator(
      'button:has-text("确认"), button:has-text("Confirm"), [data-testid="confirm-button"]'
    );
    await confirmBtn.click();
  }
}

function isDisabled(locator: ReturnType<Page["locator"]>) {
  return locator.isDisabled().catch(() => locator.getAttribute("disabled").then((v) => v !== null));
}

test.describe("SC-04: Host Lifecycle (Stop/Start)", () => {

  test.beforeEach(async ({ page }) => {
    await page.goto("/auth/login");
    await page.locator("[data-testid='login-username-input']").fill("test-admin");
    await page.locator("[data-testid='login-password-input']").fill("Admin@1234");
    await page.locator("[data-testid='login-button']").click();
    await page.waitForURL(/\/console/, { timeout: 10000 });
    await page.goto("/console/lecs-hosts/list");
    await page.waitForLoadState("networkidle");
  });

  test("ETP-004-A: Stop normal host -> shutting_down -> stopped -> start button appears", async ({ page }) => {
    const statusLabel = page.locator(STATUS_LABEL).filter({ hasText: "正常" }).first();
    await expect(statusLabel).toBeVisible({ timeout: 10000 });

    const row = statusLabel.locator("..");
    const stopBtn = row.locator(BTN_STOP);
    await expect(stopBtn).toBeVisible();
    await expect(stopBtn).toBeEnabled();

    await stopBtn.click();
    await confirmDialog(page);

    await expect(stopBtn).toBeDisabled();
    const startBtnInRow = row.locator(BTN_START);
    await expect(startBtnInRow).toBeDisabled();

    await waitForStatus(page, "关机中");
    await waitForStatus(page, "已关机");

    await expect(startBtnInRow).toBeEnabled();
    await expect(stopBtn).toBeDisabled();
  });

  test("ETP-004-B: Start stopped host -> starting -> normal -> stop button appears", async ({ page }) => {
    const statusLabel = page.locator(STATUS_LABEL).filter({ hasText: "已关机" }).first();
    await expect(statusLabel).toBeVisible({ timeout: 10000 });

    const row = statusLabel.locator("..");
    const startBtn = row.locator(BTN_START);
    await expect(startBtn).toBeVisible();
    await expect(startBtn).toBeEnabled();

    await startBtn.click();
    await confirmDialog(page);

    await expect(startBtn).toBeDisabled();
    const stopBtnInRow = row.locator(BTN_STOP);
    await expect(stopBtnInRow).toBeDisabled();

    await waitForStatus(page, "启动中");
    await waitForStatus(page, "正常");

    await expect(stopBtnInRow).toBeEnabled();
    await expect(startBtn).toBeDisabled();
  });

  test("ETP-004-C: All buttons disabled during transition states", async ({ page }) => {
    const statusLabel = page.locator(STATUS_LABEL).filter({ hasText: "正常" }).first();
    await expect(statusLabel).toBeVisible({ timeout: 10000 });

    const row = statusLabel.locator("..");
    const stopBtn = row.locator(BTN_STOP);
    const startBtn = row.locator(BTN_START);
    const deleteBtn = row.locator(BTN_DELETE);

    await stopBtn.click();
    await confirmDialog(page);

    await expect(stopBtn).toBeDisabled();

    while (true) {
      const currentStatus = await row.locator(STATUS_LABEL).textContent();
      if (currentStatus?.includes("关机中")) {
        await expect(startBtn).toBeDisabled();
        await expect(deleteBtn).toBeDisabled();
        break;
      }
      if (currentStatus?.includes("已关机") || currentStatus?.includes("正常")) {
        break;
      }
      await page.waitForTimeout(POLL_INTERVAL_MS);
    }
  });

});
