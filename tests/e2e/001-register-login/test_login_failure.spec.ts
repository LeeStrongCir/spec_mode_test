import { test, expect } from "@playwright/test";

test.describe("SC-03: Login Failure and Lockout", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/auth/login");
    await page.waitForSelector("[data-testid='login-form']", { state: "visible" });
    await page.waitForTimeout(500);
  });

  test("TC-016: login with non-existent user shows generic error", async ({ page }) => {
    await page.locator("[data-testid='login-username-input']").fill("nonexistent_user");
    await page.locator("[data-testid='login-password-input']").fill("AnyPassword1!");
    await page.locator("[data-testid='login-button']").click();
    await expect(page.locator("[data-testid='login-error-alert']")).toBeVisible();
    const errorText = await page.locator("[data-testid='login-error-alert']").textContent();
    expect(errorText).toContain("Username or password is incorrect");
  });

  test("TC-017: login with wrong password shows generic error", async ({ page }) => {
    await page.locator("[data-testid='login-username-input']").fill("testuser");
    await page.locator("[data-testid='login-password-input']").fill("WrongPassword1!");
    await page.locator("[data-testid='login-button']").click();
    await expect(page.locator("[data-testid='login-error-alert']")).toBeVisible();
    const errorText = await page.locator("[data-testid='login-error-alert']").textContent();
    expect(errorText).toContain("Username or password is incorrect");
  });

  test("TC-019: error messages are identical for wrong user vs wrong password", async ({ page }) => {
    await page.locator("[data-testid='login-username-input']").fill("nonexistent_user");
    await page.locator("[data-testid='login-password-input']").fill("Any!");
    await page.locator("[data-testid='login-button']").click();
    const error1 = await page.locator("[data-testid='login-error-alert']").textContent();

    await page.goto("/auth/login");
    await page.waitForSelector("[data-testid='login-form']", { state: "visible" });
    await page.waitForTimeout(500);
    await page.locator("[data-testid='login-username-input']").fill("testuser");
    await page.locator("[data-testid='login-password-input']").fill("Wrong!");
    await page.locator("[data-testid='login-button']").click();
    const error2 = await page.locator("[data-testid='login-error-alert']").textContent();

    expect(error1).toBe(error2);
  });

  test("TC-018: 5 failed logins locks account", async ({ page }) => {
    const username = `locktest_${Date.now()}`;
    await page.goto("/auth/register");
    await page.locator("[data-testid='register-username-input']").fill(username);
    await page.locator("[data-testid='register-password-input']").fill("Test@1234");
    await page.locator("[data-testid='register-confirm-password-input']").fill("Test@1234");
    await page.locator("[data-testid='register-email-input']").fill(`${username}@example.com`);
    await page.locator("[data-testid='register-button']").click();
    await page.waitForURL(/\/console/, { timeout: 10000 });
    await page.locator("[data-testid='logout-button']").click();
    await page.waitForURL(/\/auth\/login/, { timeout: 5000 });
    await page.waitForSelector("[data-testid='login-form']", { state: "visible" });
    await page.waitForTimeout(500);

    for (let i = 0; i < 5; i++) {
      await page.locator("[data-testid='login-username-input']").fill(username);
      await page.locator("[data-testid='login-password-input']").fill(`Wrong${i}!`);
      await page.locator("[data-testid='login-button']").click();
      await expect(page.locator("[data-testid='login-error-alert']")).toBeVisible();
    }

    await page.locator("[data-testid='login-password-input']").fill("Test@1234");
    await page.locator("[data-testid='login-button']").click();
    await expect(page.locator("[data-testid='login-error-alert']")).toBeVisible();
    const lockText = await page.locator("[data-testid='login-error-alert']").textContent();
    const normalizedText = lockText?.toLowerCase() || "";
    expect(normalizedText.includes("lock") || normalizedText.includes("15") || normalizedText.includes("暂") || normalizedText.includes("locked")).toBe(true);
  });
});
