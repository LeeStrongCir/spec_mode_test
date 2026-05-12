import { test, expect, type Page } from "@playwright/test";

// Fixture data — mirrors tests/fixtures/data/lecs-specs.json
const INSTANCE_SPECS = [
  { id: "eco-001", name: "2vCPU+2GiB", planType: "ECONOMY", vcpu: 2, memoryGiB: 2, systemDiskGB: 40, monthlyPriceCents: 10000 },
  { id: "eco-002", name: "2vCPU+4GiB", planType: "ECONOMY", vcpu: 2, memoryGiB: 4, systemDiskGB: 40, monthlyPriceCents: 14000 },
  { id: "eco-003", name: "2vCPU+8GiB", planType: "ECONOMY", vcpu: 2, memoryGiB: 8, systemDiskGB: 40, monthlyPriceCents: 18000 },
  { id: "eco-004", name: "4vCPU+8GiB", planType: "ECONOMY", vcpu: 4, memoryGiB: 8, systemDiskGB: 40, monthlyPriceCents: 24000 },
  { id: "hp-001", name: "2vCPU+4GiB", planType: "HIGH_PERFORMANCE", vcpu: 2, memoryGiB: 4, systemDiskGB: 40, monthlyPriceCents: 16000 },
  { id: "hp-002", name: "2vCPU+8GiB", planType: "HIGH_PERFORMANCE", vcpu: 2, memoryGiB: 8, systemDiskGB: 40, monthlyPriceCents: 20000 },
  { id: "hp-003", name: "4vCPU+8GiB", planType: "HIGH_PERFORMANCE", vcpu: 4, memoryGiB: 8, systemDiskGB: 40, monthlyPriceCents: 26000 },
  { id: "hp-004", name: "8vCPU+16GiB", planType: "HIGH_PERFORMANCE", vcpu: 8, memoryGiB: 16, systemDiskGB: 40, monthlyPriceCents: 50000 },
];

// Selector constants (data-testid-based)
const S = {
  createHostBtn: "[data-testid='create-host-btn']",
  hostnameInput: "[data-testid='hostname-input']",
  usernameInput: "[data-testid='username-input']",
  passwordInput: "[data-testid='password-input']",
  buyNowBtn: "[data-testid='buy-now-btn']",
  confirmDialog: "[data-testid='confirm-dialog']",
  confirmDialogCancel: "[data-testid='confirm-dialog-cancel']",
  confirmDialogConfirm: "[data-testid='confirm-dialog-confirm']",
  hostnameError: "[data-testid='hostname-error']",
  usernameError: "[data-testid='username-error']",
  passwordError: "[data-testid='password-error']",
  ipInput: "[data-testid='ip-address-input']",
  ipError: "[data-testid='ip-address-error']",
  billingModeSelect: "[data-testid='billing-mode-select']",
  instanceTypeRadio: "[data-testid='instance-type-radio']",
  specCard: "[data-testid='spec-card']",
  costDisplay: "[data-testid='cost-display']",
  costUnit: "[data-testid='cost-unit']",
  purchaseMonthsSelect: "[data-testid='purchase-months-select']",
  osSelect: "[data-testid='os-select']",
  ipAllocationRadio: "[data-testid='ip-allocation-radio']",
  submitLoading: "[data-testid='submit-loading']",
  statusBadge: "[data-testid='status-badge']",
};

const SECTION_TITLES = ["基础配置", "实例规格", "操作系统", "IP 配置", "购买时长", "配置费用"];

async function login(page: Page) {
  await page.goto("/login");
  await page.locator(S.usernameInput).fill("testuser");
  await page.locator(S.passwordInput).fill("Test@1234");
  await page.locator('[data-testid="login-button"]').click();
  await page.waitForURL(/\/console/);
}

test.describe("SC-03 Create Host", () => {
  test("ETP-003-A: entry point and six form sections render", async ({ page }) => {
    await login(page);
    await page.goto("/console/lecs-hosts/list");
    await expect(page.locator(S.createHostBtn)).toBeVisible();
    await page.locator(S.createHostBtn).click();
    await expect(page).toHaveURL(/\/console\/lecs-hosts\/create/);

    for (const title of SECTION_TITLES) {
      await expect(page.getByText(title, { exact: false }).first()).toBeVisible();
    }

    await expect(page.locator(S.hostnameInput)).toBeVisible();
    await expect(page.locator(S.usernameInput)).toBeVisible();
    await expect(page.locator(S.passwordInput)).toBeVisible();
    await expect(page.locator(S.billingModeSelect)).toBeVisible();
    await expect(page.locator(S.costDisplay)).toBeVisible();
  });

  test("ETP-003-B: hostname validation feedback", async ({ page }) => {
    await login(page);
    await page.goto("/console/lecs-hosts/list");
    await page.locator(S.createHostBtn).click();
    await page.waitForURL(/\/console\/lecs-hosts\/create/);

    await page.locator(S.hostnameInput).fill("_abc");
    await page.locator(S.hostnameInput).blur();
    await expect(page.locator(S.hostnameError)).toBeVisible();

    await page.locator(S.hostnameInput).fill("valid_host1");
    await page.locator(S.hostnameInput).blur();
    await expect(page.locator(S.hostnameError)).not.toBeVisible();
  });

  test("ETP-003-C: credential validation feedback", async ({ page }) => {
    await login(page);
    await page.goto("/console/lecs-hosts/list");
    await page.locator(S.createHostBtn).click();
    await page.waitForURL(/\/console\/lecs-hosts\/create/);

    await page.locator(S.usernameInput).fill("ab");
    await page.locator(S.usernameInput).blur();
    await expect(page.locator(S.usernameError)).toBeVisible();

    await page.locator(S.usernameInput).fill("valid_user");
    await page.locator(S.usernameInput).blur();
    await expect(page.locator(S.usernameError)).not.toBeVisible();

    await page.locator(S.passwordInput).fill("123");
    await page.locator(S.passwordInput).blur();
    await expect(page.locator(S.passwordError)).toBeVisible();

    await page.locator(S.passwordInput).fill("Abcdef12!");
    await page.locator(S.passwordInput).blur();
    await expect(page.locator(S.passwordError)).not.toBeVisible();
  });

  test("ETP-003-D: spec selection updates cost in real-time", async ({ page }) => {
    await login(page);
    await page.goto("/console/lecs-hosts/list");
    await page.locator(S.createHostBtn).click();
    await page.waitForURL(/\/console\/lecs-hosts\/create/);

    await page.locator(S.hostnameInput).fill("test_host_a");
    await page.locator(S.usernameInput).fill("admin_user");
    await page.locator(S.passwordInput).fill("Abcdef12!");

    await page.locator(S.instanceTypeRadio).filter({ hasText: "经济型" }).click();
    await page.locator(S.specCard).filter({ hasText: "2vCPU+2GiB" }).click();
    await page.locator(S.purchaseMonthsSelect).selectOption({ label: "3个月" });

    const costText = await page.locator(S.costDisplay).textContent();
    expect(costText).toMatch(/300/);

    await page.locator(S.purchaseMonthsSelect).selectOption({ label: "12个月" });
    const costText12 = await page.locator(S.costDisplay).textContent();
    expect(costText12).toMatch(/1200/);

    await page.locator(S.billingModeSelect).selectOption({ label: "按需计费" });
    const costPayg = await page.locator(S.costDisplay).textContent();
    expect(costPayg).toMatch(/3\.33/);

    const unitText = await page.locator(S.costUnit).textContent();
    expect(unitText).toContain("天");
  });

  test("ETP-003-E: confirm dialog Cancel preserves form data", async ({ page }) => {
    await login(page);
    await page.goto("/console/lecs-hosts/list");
    await page.locator(S.createHostBtn).click();
    await page.waitForURL(/\/console\/lecs-hosts\/create/);

    await page.locator(S.hostnameInput).fill("test_host_a");
    await page.locator(S.usernameInput).fill("admin_user");
    await page.locator(S.passwordInput).fill("Abcdef12!");

    await page.locator(S.buyNowBtn).click();
    await expect(page.locator(S.confirmDialog)).toBeVisible();

    await page.locator(S.confirmDialogCancel).click();
    await expect(page.locator(S.confirmDialog)).not.toBeVisible();

    await expect(page.locator(S.hostnameInput)).toHaveValue("test_host_a");
    await expect(page.locator(S.usernameInput)).toHaveValue("admin_user");
  });

  test("ETP-003-F: confirm dialog Confirm submits and redirects to list", async ({ page }) => {
    await login(page);
    await page.goto("/console/lecs-hosts/list");
    await page.locator(S.createHostBtn).click();
    await page.waitForURL(/\/console\/lecs-hosts\/create/);

    await page.locator(S.hostnameInput).fill("test_host_e2e");
    await page.locator(S.usernameInput).fill("admin_user");
    await page.locator(S.passwordInput).fill("Abcdef12!");
    await page.locator(S.instanceTypeRadio).filter({ hasText: "经济型" }).click();
    await page.locator(S.specCard).filter({ hasText: "2vCPU+2GiB" }).click();
    await page.locator(S.purchaseMonthsSelect).selectOption({ label: "3个月" });

    await page.locator(S.buyNowBtn).click();
    await expect(page.locator(S.confirmDialog)).toBeVisible();

    const dialogText = await page.locator(S.confirmDialog).textContent();
    expect(dialogText).toContain("test_host_e2e");
    expect(dialogText).toContain("admin_user");

    await page.locator(S.confirmDialogConfirm).click();
    await page.waitForURL(/\/console\/lecs-hosts\/list/, { timeout: 10000 });
    await expect(page).toHaveURL(/\/console\/lecs-hosts\/list/);

    const newHostRow = page.locator("tr").filter({ hasText: "test_host_e2e" }).first();
    await expect(newHostRow).toBeVisible({ timeout: 10000 });
    await expect(newHostRow.locator(S.statusBadge)).toContainText("创建中");
  });

  test("ETP-003-G: status transitions from 创建中 to 正常 or 创建失败", async ({ page }) => {
    await login(page);
    await page.goto("/console/lecs-hosts/list");
    await page.locator(S.createHostBtn).click();
    await page.waitForURL(/\/console\/lecs-hosts\/create/);

    await page.locator(S.hostnameInput).fill("test_status_poll");
    await page.locator(S.usernameInput).fill("admin_user");
    await page.locator(S.passwordInput).fill("Abcdef12!");
    await page.locator(S.instanceTypeRadio).filter({ hasText: "经济型" }).click();
    await page.locator(S.specCard).filter({ hasText: "2vCPU+2GiB" }).click();
    await page.locator(S.purchaseMonthsSelect).selectOption({ label: "3个月" });

    await page.locator(S.buyNowBtn).click();
    await expect(page.locator(S.confirmDialog)).toBeVisible();
    await page.locator(S.confirmDialogConfirm).click();
    await page.waitForURL(/\/console\/lecs-hosts\/list/, { timeout: 10000 });

    const hostRow = page.locator("tr").filter({ hasText: "test_status_poll" }).first();
    const badge = hostRow.locator(S.statusBadge);

    let finalStatus: string | null = null;
    for (let i = 0; i < 10; i++) {
      const text = await badge.textContent();
      if (text?.includes("正常")) { finalStatus = "normal"; break; }
      if (text?.includes("创建失败")) { finalStatus = "failed"; break; }
      await page.waitForTimeout(3000);
      await page.reload();
    }

    expect(finalStatus).not.toBeNull();
    expect(finalStatus).toMatch(/normal|failed/);
  });

  test("ETP-003-H: IP configuration manual mode validation", async ({ page }) => {
    await login(page);
    await page.goto("/console/lecs-hosts/list");
    await page.locator(S.createHostBtn).click();
    await page.waitForURL(/\/console\/lecs-hosts\/create/);

    await page.locator(S.ipAllocationRadio).filter({ hasText: "手工配置" }).click();
    await expect(page.locator(S.ipInput)).toBeVisible();

    await page.locator(S.ipInput).fill("999.999.999.999");
    await page.locator(S.ipInput).blur();
    await expect(page.locator(S.ipError)).toBeVisible();

    await page.locator(S.ipInput).fill("192.168.1.100");
    await page.locator(S.ipInput).blur();
    await expect(page.locator(S.ipError)).not.toBeVisible();

    await page.locator(S.ipAllocationRadio).filter({ hasText: "DHCP" }).click();
    await expect(page.locator(S.ipInput)).not.toBeVisible();
  });
});
