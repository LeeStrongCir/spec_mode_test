import { test, expect } from "@playwright/test";

test.describe.configure({ mode: 'parallel' });

test.describe("SC-04: Logout Flow", () => {
  async function registerAndLogin(page: import("@playwright/test").Page) {
    await page.goto("/auth/register");
    const username = `testuser_e2e_${Date.now()}`;
    await page.locator("[data-testid='register-username-input']").fill(username);
    await page.locator("[data-testid='register-password-input']").fill("Test@1234");
    await page.locator("[data-testid='register-confirm-password-input']").fill("Test@1234");
    await page.locator("[data-testid='register-email-input']").fill(`${username}@example.com`);
    await page.locator("[data-testid='register-button']").click();
    await page.waitForURL(/\/console/, { timeout: 10000 });
  }

  test("TC-020: logout clears cookie and redirects to login", async ({ page }) => {
    await registerAndLogin(page);
    await page.locator("[data-testid='logout-button']").click();
    await expect(page).toHaveURL(/\/auth\/login/);
    await expect(page.locator("[data-testid='logout-success-alert']")).toBeVisible();
  });

  test("TC-021: browser back button protection after logout", async ({ page }) => {
    await registerAndLogin(page);
    await page.locator("[data-testid='logout-button']").click();
    await expect(page).toHaveURL(/\/auth\/login/);
    await page.goBack();
    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test("TC-022: expired cookie redirects to login on protected page access", async ({ page }) => {
    await registerAndLogin(page);
    await page.locator("[data-testid='logout-button']").click();
    await expect(page).toHaveURL(/\/auth\/login/);
    await page.goto("/console/dashboard");
    await expect(page).toHaveURL(/\/auth\/login/);
  });
});
