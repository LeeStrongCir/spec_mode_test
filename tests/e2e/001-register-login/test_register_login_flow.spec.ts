import { test, expect } from "@playwright/test";

test.describe("SC-01 + SC-02: Registration and Login Flow", () => {
  test("TC-001: register page loads with all form elements", async ({ page }) => {
    await page.goto("/auth/register");
    await expect(page.locator("[data-testid='register-username-input']")).toBeVisible();
    await expect(page.locator("[data-testid='register-password-input']")).toBeVisible();
    await expect(page.locator("[data-testid='register-confirm-password-input']")).toBeVisible();
    await expect(page.locator("[data-testid='register-email-input']")).toBeVisible();
    await expect(page.locator("[data-testid='register-button']")).toBeVisible();
    await expect(page.locator("[data-testid='register-login-link']")).toBeVisible();
  });

  test("TC-002: empty form submission shows validation errors", async ({ page }) => {
    await page.goto("/auth/register");
    await page.waitForSelector("[data-testid='register-button']", { state: "visible" });
    await page.locator("[data-testid='register-button']").click();
    await expect(page.locator("[data-testid='register-username-input']")).toBeVisible();
    await expect(page.locator("[data-testid='register-password-input']")).toBeVisible();
  });

  test("TC-007: successful registration creates account and redirects to console", async ({ page }) => {
    await page.goto("/auth/register");
    await page.waitForSelector("[data-testid='register-button']", { state: "visible" });
    const username = `newuser${Date.now()}`;
    await page.locator("[data-testid='register-username-input']").fill(username);
    await page.locator("[data-testid='register-password-input']").fill("Test@1234");
    await page.locator("[data-testid='register-confirm-password-input']").fill("Test@1234");
    await page.locator("[data-testid='register-email-input']").fill(`${username}@example.com`);
    await page.locator("[data-testid='register-button']").click();
    await page.waitForURL(/\/console/, { timeout: 10000 });
  });

  test("TC-008: back to login link redirects to login page", async ({ page }) => {
    await page.goto("/auth/register");
    await page.locator("[data-testid='register-login-link']").click();
    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test("TC-010: login page loads with all form elements", async ({ page }) => {
    await page.goto("/auth/login");
    await expect(page.locator("[data-testid='login-username-input']")).toBeVisible();
    await expect(page.locator("[data-testid='login-password-input']")).toBeVisible();
    await expect(page.locator("[data-testid='login-remember']")).toBeVisible();
    await expect(page.locator("[data-testid='login-button']")).toBeVisible();
  });

  test("TC-013: successful login redirects to console", async ({ page }) => {
    await page.goto("/auth/register");
    const username = `logintest_${Date.now()}`;
    await page.locator("[data-testid='register-username-input']").fill(username);
    await page.locator("[data-testid='register-password-input']").fill("Test@1234");
    await page.locator("[data-testid='register-confirm-password-input']").fill("Test@1234");
    await page.locator("[data-testid='register-email-input']").fill(`${username}@example.com`);
    await page.locator("[data-testid='register-button']").click();
    await page.waitForURL(/\/console/, { timeout: 10000 });
    await page.locator("[data-testid='logout-button']").click();
    await page.waitForURL(/\/auth\/login/, { timeout: 5000 });

    await page.locator("[data-testid='login-username-input']").fill(username);
    await page.locator("[data-testid='login-password-input']").fill("Test@1234");
    await page.locator("[data-testid='login-button']").click();
    await page.waitForURL(/\/console/, { timeout: 10000 });
    await expect(page.locator("[data-testid='console-greeting']")).toBeVisible();
  });
});
