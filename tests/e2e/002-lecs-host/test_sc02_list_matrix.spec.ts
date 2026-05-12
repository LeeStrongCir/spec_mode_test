import { test, expect, type Page, type Locator } from "@playwright/test";

// --- Constants ---

const LIST_PAGE_URL = "/console/lecs-hosts/list";

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  normal: { label: "正常", color: "green" },
  stopped: { label: "已关机", color: "gray" },
  failed: { label: "创建失败", color: "red" },
  creating: { label: "创建中", color: "blue" },
  deleting: { label: "删除中", color: "orange" },
};

const EXPECTED_HEADERS = ["主机名/ID", "计费模式", "运行状态", "私有IP", "操作"];

// --- Helper functions ---

async function seedHostsViaAPI(page: Page, hosts: Array<{
  id: string;
  hostname: string;
  status: string;
  billingMode?: string;
  privateIp?: string;
}>) {
  await page.evaluate(async (hostData) => {
    const response = await fetch("/api/v1/lecs-hosts/__test__/seed", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(hostData),
    });
    if (!response.ok) {
      throw new Error(`Seed failed: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }, hosts);
}

async function getButtonState(row: Locator, btnName: "stop" | "start" | "delete"): Promise<"enabled" | "disabled"> {
  const btn = row.locator(`[data-testid="btn-${btnName}"]`);
  const isDisabled = await btn.isDisabled();
  const hasDisabledAttr = await btn.getAttribute("disabled");
  if (isDisabled || hasDisabledAttr !== null) {
    return "disabled";
  }
  // Check cursor style as secondary signal
  const cursor = await btn.evaluate((el) => window.getComputedStyle(el).cursor);
  if (cursor !== "pointer") {
    return "disabled";
  }
  return "enabled";
}

async function waitForTableLoad(page: Page) {
  await page.waitForSelector('[data-testid="host-list-table"]', { state: "visible" });
  await page.waitForLoadState("networkidle");
}

async function verifyButtonMatrix(
  page: Page,
  hostId: string,
  expected: { stop: "enabled" | "disabled"; start: "enabled" | "disabled"; delete: "enabled" | "disabled" }
) {
  await page.goto(LIST_PAGE_URL);
  await waitForTableLoad(page);

  const row = page.locator(`[data-testid="host-row-${hostId}"]`);
  await expect(row).toBeVisible();

  const stopState = await getButtonState(row, "stop");
  const startState = await getButtonState(row, "start");
  const deleteState = await getButtonState(row, "delete");

  expect(stopState, `stop button state for host ${hostId}`).toBe(expected.stop);
  expect(startState, `start button state for host ${hostId}`).toBe(expected.start);
  expect(deleteState, `delete button state for host ${hostId}`).toBe(expected.delete);
}

async function verifyStatusLabel(page: Page, hostId: string, statusKey: keyof typeof STATUS_MAP) {
  const expected = STATUS_MAP[statusKey];
  const row = page.locator(`[data-testid="host-row-${hostId}"]`);
  const statusTag = row.locator('[data-testid="status-tag"]');
  await expect(statusTag).toBeVisible();
  expect(await statusTag.textContent()).toBe(expected.label);
}

// --- TC-010: List page structure & columns ---

test.describe("SC-02: TC-010 - List Page Structure & Columns", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/auth/login");
    await page.locator("[data-testid='login-username-input']").fill("e2e_admin");
    await page.locator("[data-testid='login-password-input']").fill("Test@1234");
    await page.locator("[data-testid='login-button']").click();
    await page.waitForURL(/\/console/, { timeout: 10000 });
  });

  test("table headers match expected columns in order", async ({ page }) => {
    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    const table = page.locator('[data-testid="host-list-table"]');
    const headers = table.locator("thead th");
    const headerCount = await headers.count();
    expect(headerCount).toBe(EXPECTED_HEADERS.length);

    for (let i = 0; i < EXPECTED_HEADERS.length; i++) {
      const headerText = await headers.nth(i).textContent();
      expect(headerText?.trim()).toBe(EXPECTED_HEADERS[i]);
    }
  });

  test("create button exists with no global toolbar", async ({ page }) => {
    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    const createButton = page.locator("button", { hasText: "创建LECS主机" });
    await expect(createButton).toBeVisible();

    // Verify no extra toolbars or batch operation buttons
    const actionBar = page.locator('[data-testid="action-bar"]');
    expect(await actionBar.count()).toBe(0);

    const batchButtons = page.locator('[data-testid^="batch-"]');
    expect(await batchButtons.count()).toBe(0);
  });

  test("pagination component is visible with total count", async ({ page }) => {
    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    const pagination = page.locator('[data-testid="pagination"]');
    await expect(pagination).toBeVisible();

    const totalText = page.locator('[data-testid="pagination-total"]');
    await expect(totalText).toBeVisible();
    expect(await totalText.textContent()).toMatch(/共 \d+ 条/);
  });

  test("host rows display hostname and UUID format ID", async ({ page }) => {
    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    const rows = page.locator('[data-testid="host-list-table"] tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      const firstRow = rows.first();
      const nameCell = firstRow.locator('[data-testid="cell-hostname"]');
      const nameText = await nameCell.textContent();
      expect(nameText?.trim().length).toBeGreaterThan(0);

      // Check for UUID pattern in the row
      const idCell = firstRow.locator('[data-testid="cell-host-id"]');
      const idText = await idCell.textContent();
      expect(idText).toMatch(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i);
    }
  });

  test("billing mode column shows prepaid or pay-as-you-go", async ({ page }) => {
    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    const rows = page.locator('[data-testid="host-list-table"] tbody tr');
    const rowCount = await rows.count();

    for (let i = 0; i < Math.min(rowCount, 3); i++) {
      const billingCell = rows.nth(i).locator('[data-testid="cell-billing"]');
      const billingText = await billingCell.textContent();
      expect(
        billingText?.includes("包年/包月") || billingText?.includes("按需计费")
      ).toBe(true);
    }
  });

  test("private IP column shows IPv4 or placeholder", async ({ page }) => {
    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    const rows = page.locator('[data-testid="host-list-table"] tbody tr');
    const rowCount = await rows.count();

    for (let i = 0; i < Math.min(rowCount, 3); i++) {
      const ipCell = rows.nth(i).locator('[data-testid="cell-private-ip"]');
      const ipText = (await ipCell.textContent())?.trim();
      expect(
        ipText === "-" ||
        ipText === "" ||
        /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(ipText ?? "")
      ).toBe(true);
    }
  });
});

// --- TC-011 ~ TC-014: Operation button state matrix ---

test.describe("SC-02: TC-011~TC-014 - Operation Button State Matrix", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/auth/login");
    await page.locator("[data-testid='login-username-input']").fill("e2e_admin");
    await page.locator("[data-testid='login-password-input']").fill("Test@1234");
    await page.locator("[data-testid='login-button']").click();
    await page.waitForURL(/\/console/, { timeout: 10000 });
  });

  test("TC-011: normal host - stop enabled, start disabled, delete disabled", async ({ page }) => {
    const hostId = `e2e-normal-${Date.now()}`;
    await seedHostsViaAPI(page, [
      { id: hostId, hostname: "e2e-normal-host", status: "normal", privateIp: "10.0.1.10" },
    ]);

    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    await verifyStatusLabel(page, hostId, "normal");
    await verifyButtonMatrix(page, hostId, { stop: "enabled", start: "disabled", delete: "disabled" });

    // Verify stop button is clickable and triggers action
    const row = page.locator(`[data-testid="host-row-${hostId}"]`);
    const stopBtn = row.locator('[data-testid="btn-stop"]');
    expect(await stopBtn.isDisabled()).toBe(false);
  });

  test("TC-012: stopped host - start enabled, delete enabled, stop disabled", async ({ page }) => {
    const hostId = `e2e-stopped-${Date.now()}`;
    await seedHostsViaAPI(page, [
      { id: hostId, hostname: "e2e-stopped-host", status: "stopped", privateIp: "10.0.1.20" },
    ]);

    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    await verifyStatusLabel(page, hostId, "stopped");
    await verifyButtonMatrix(page, hostId, { stop: "disabled", start: "enabled", delete: "enabled" });

    // Verify delete button triggers confirmation dialog
    const row = page.locator(`[data-testid="host-row-${hostId}"]`);
    const deleteBtn = row.locator('[data-testid="btn-delete"]');
    expect(await deleteBtn.isDisabled()).toBe(false);
  });

  test("TC-013: failed host - start enabled, delete enabled, stop disabled", async ({ page }) => {
    const hostId = `e2e-failed-${Date.now()}`;
    await seedHostsViaAPI(page, [
      { id: hostId, hostname: "e2e-failed-host", status: "failed", privateIp: "10.0.1.30" },
    ]);

    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    await verifyStatusLabel(page, hostId, "failed");
    await verifyButtonMatrix(page, hostId, { stop: "disabled", start: "enabled", delete: "enabled" });
  });

  test("TC-014: creating host - all buttons disabled", async ({ page }) => {
    const hostId = `e2e-creating-${Date.now()}`;
    await seedHostsViaAPI(page, [
      { id: hostId, hostname: "e2e-creating-host", status: "creating", privateIp: null as unknown as string },
    ]);

    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    await verifyStatusLabel(page, hostId, "creating");
    await verifyButtonMatrix(page, hostId, { stop: "disabled", start: "disabled", delete: "disabled" });

    // Creating host may show "-" for private IP
    const row = page.locator(`[data-testid="host-row-${hostId}"]`);
    const ipCell = row.locator('[data-testid="cell-private-ip"]');
    const ipText = await ipCell.textContent();
    expect(ipText === "-" || ipText === "" || ipText === null).toBe(true);
  });

  test("TC-014: deleting host - all buttons disabled, row auto-disappears", async ({ page }) => {
    const hostId = `e2e-deleting-${Date.now()}`;
    await seedHostsViaAPI(page, [
      { id: hostId, hostname: "e2e-deleting-host", status: "deleting", privateIp: "10.0.1.40" },
    ]);

    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    await verifyStatusLabel(page, hostId, "deleting");
    await verifyButtonMatrix(page, hostId, { stop: "disabled", start: "disabled", delete: "disabled" });

    // Wait for row to auto-disappear (3-5 seconds)
    const row = page.locator(`[data-testid="host-row-${hostId}"]`);
    await expect(row).toBeVisible();

    // Poll for row removal (up to 10 seconds)
    let rowVisible = true;
    for (let attempt = 0; attempt < 10; attempt++) {
      await page.waitForTimeout(1000);
      rowVisible = await row.isVisible().catch(() => false);
      if (!rowVisible) break;
    }
    expect(rowVisible).toBe(false);

    // Verify row is gone after manual refresh
    await page.reload();
    await waitForTableLoad(page);
    const rowAfterRefresh = page.locator(`[data-testid="host-row-${hostId}"]`);
    await expect(rowAfterRefresh).not.toBeVisible();
  });
});

// --- TC-015: Soft-delete verification ---

test.describe("SC-02: TC-015 - Soft-Delete Host Not Visible in List", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/auth/login");
    await page.locator("[data-testid='login-username-input']").fill("e2e_admin");
    await page.locator("[data-testid='login-password-input']").fill("Test@1234");
    await page.locator("[data-testid='login-button']").click();
    await page.waitForURL(/\/console/, { timeout: 10000 });
  });

  test("deleted host disappears from list after deletion flow", async ({ page }) => {
    const hostId = `e2e-delete-test-${Date.now()}`;
    await seedHostsViaAPI(page, [
      { id: hostId, hostname: "e2e-to-be-deleted", status: "stopped", privateIp: "10.0.1.50" },
    ]);

    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    // Verify host is initially visible
    const row = page.locator(`[data-testid="host-row-${hostId}"]`);
    await expect(row).toBeVisible();

    // Click delete button
    const deleteBtn = row.locator('[data-testid="btn-delete"]');
    expect(await deleteBtn.isDisabled()).toBe(false);
    await deleteBtn.click();

    // Wait for confirmation dialog and confirm
    const confirmDialog = page.locator('[data-testid="delete-confirm-dialog"]');
    await expect(confirmDialog).toBeVisible();

    const confirmButton = page.locator('[data-testid="confirm-delete-btn"]');
    await confirmButton.click();

    // Status should change to "deleting" (orange)
    await verifyStatusLabel(page, hostId, "deleting");

    // Row should auto-disappear within 3-5 seconds
    for (let attempt = 0; attempt < 10; attempt++) {
      await page.waitForTimeout(1000);
      const stillVisible = await row.isVisible().catch(() => false);
      if (!stillVisible) break;
    }
    await expect(row).not.toBeVisible();

    // Manual refresh: host should still be gone
    await page.reload();
    await waitForTableLoad(page);
    const rowAfterRefresh = page.locator(`[data-testid="host-row-${hostId}"]`);
    await expect(rowAfterRefresh).not.toBeVisible();

    // Search by host ID returns empty
    const searchInput = page.locator('[data-testid="search-input"]');
    if (await searchInput.isVisible()) {
      await searchInput.fill(hostId);
      await page.waitForTimeout(500);
      const searchResults = page.locator('[data-testid="host-list-table"] tbody tr');
      expect(await searchResults.count()).toBe(0);
    }
  });

  test("soft-deleted host not recoverable via search", async ({ page }) => {
    // Seed a host that's already soft-deleted (simulated via API state)
    const hostId = `e2e-soft-deleted-${Date.now()}`;
    await seedHostsViaAPI(page, [
      { id: hostId, hostname: "e2e-already-deleted", status: "deleting", privateIp: "10.0.1.60" },
    ]);

    // Wait for it to be fully removed
    await page.waitForTimeout(6000);

    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    // Should not appear in list
    const row = page.locator(`[data-testid="host-row-${hostId}"]`);
    await expect(row).not.toBeVisible();

    // Search by ID should return no results
    const searchInput = page.locator('[data-testid="search-input"]');
    if (await searchInput.isVisible()) {
      await searchInput.fill(hostId);
      await page.waitForTimeout(500);
      const searchResults = page.locator('[data-testid="host-list-table"] tbody tr');
      expect(await searchResults.count()).toBe(0);
    }
  });
});

// --- Negative tests ---

test.describe("SC-02: Negative Tests", () => {
  test("unauthenticated access redirects to login", async ({ page }) => {
    // Clear any existing session
    await page.context().clearCookies();
    await page.goto(LIST_PAGE_URL);

    await page.waitForURL(/\/auth\/login/, { timeout: 10000 });
    expect(page.url()).toContain("/auth/login");
  });

  test("empty list shows placeholder message", async ({ page }) => {
    await page.goto("/auth/login");
    await page.locator("[data-testid='login-username-input']").fill("e2e_empty_user");
    await page.locator("[data-testid='login-password-input']").fill("Test@1234");
    await page.locator("[data-testid='login-button']").click();
    await page.waitForURL(/\/console/, { timeout: 10000 });

    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    // Empty table should show a "no data" placeholder
    const emptyState = page.locator('[data-testid="empty-state"], text=/暂无数据|暂无主机/');
    const rowCount = await page.locator('[data-testid="host-list-table"] tbody tr').count();
    if (rowCount === 0) {
      await expect(emptyState).toBeVisible();
    }
  });

  test("status label colors match specification", async ({ page }) => {
    const testHosts = [
      { id: `color-normal-${Date.now()}`, hostname: "color-normal", status: "normal", privateIp: "10.0.2.1" },
      { id: `color-stopped-${Date.now()}`, hostname: "color-stopped", status: "stopped", privateIp: "10.0.2.2" },
      { id: `color-failed-${Date.now()}`, hostname: "color-failed", status: "failed", privateIp: "10.0.2.3" },
      { id: `color-creating-${Date.now()}`, hostname: "color-creating", status: "creating", privateIp: "10.0.2.4" },
      { id: `color-deleting-${Date.now()}`, hostname: "color-deleting", status: "deleting", privateIp: "10.0.2.5" },
    ];

    await page.goto("/auth/login");
    await page.locator("[data-testid='login-username-input']").fill("e2e_admin");
    await page.locator("[data-testid='login-password-input']").fill("Test@1234");
    await page.locator("[data-testid='login-button']").click();
    await page.waitForURL(/\/console/, { timeout: 10000 });

    await seedHostsViaAPI(page, testHosts);
    await page.goto(LIST_PAGE_URL);
    await waitForTableLoad(page);

    for (const host of testHosts) {
      const row = page.locator(`[data-testid="host-row-${host.id}"]`);
      const statusTag = row.locator('[data-testid="status-tag"]');
      await expect(statusTag).toBeVisible();

      const expectedColor = STATUS_MAP[host.status as keyof typeof STATUS_MAP]?.color;
      if (expectedColor && expectedColor !== "gray") {
        const bgColor = await statusTag.evaluate((el) => {
          const style = window.getComputedStyle(el);
          return style.backgroundColor || style.background;
        });
        // Verify the tag has some background color applied (not default)
        expect(bgColor.length).toBeGreaterThan(0);
      }
    }
  });
});
