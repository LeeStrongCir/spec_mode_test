# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 001-register-login/test_login_failure.spec.ts >> SC-03: Login Failure and Lockout >> TC-018: 5 failed logins locks account
- Location: tests/e2e/001-register-login/test_login_failure.spec.ts:45:7

# Error details

```
TimeoutError: page.waitForURL: Timeout 10000ms exceeded.
=========================== logs ===========================
waiting for navigation until "load"
============================================================
```

# Page snapshot

```yaml
- generic [ref=e1]:
  - generic [ref=e4]:
    - generic [ref=e5]:
      - heading "Create Account" [level=1] [ref=e6]
      - paragraph [ref=e7]: Secure access to Lee Cloud Platform
    - alert [ref=e8]: Security token not available. Please refresh.
    - generic [ref=e9]:
      - generic [ref=e10]: Username
      - textbox "username" [ref=e12]: locktest_1778554666730
    - generic [ref=e13]:
      - generic [ref=e14]: Email
      - textbox "you@example.com" [ref=e16]: locktest_1778554666730@example.com
    - generic [ref=e17]:
      - generic [ref=e18]: Password
      - textbox "••••••••" [ref=e20]: Test@1234
    - generic [ref=e21]:
      - generic [ref=e22]: Confirm Password
      - textbox "••••••••" [ref=e24]: Test@1234
    - button "Create Account" [active] [ref=e25]
    - link "Already have an account? Sign in" [ref=e27] [cursor=pointer]:
      - /url: /auth/login
  - button "Open Next.js Dev Tools" [ref=e33] [cursor=pointer]:
    - img [ref=e34]
  - alert [ref=e37]
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | 
  3  | test.describe("SC-03: Login Failure and Lockout", () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.goto("/auth/login");
  6  |     await page.waitForSelector("[data-testid='login-form']", { state: "visible" });
  7  |     await page.waitForTimeout(500);
  8  |   });
  9  | 
  10 |   test("TC-016: login with non-existent user shows generic error", async ({ page }) => {
  11 |     await page.locator("[data-testid='login-username-input']").fill("nonexistent_user");
  12 |     await page.locator("[data-testid='login-password-input']").fill("AnyPassword1!");
  13 |     await page.locator("[data-testid='login-button']").click();
  14 |     await expect(page.locator("[data-testid='login-error-alert']")).toBeVisible();
  15 |     const errorText = await page.locator("[data-testid='login-error-alert']").textContent();
  16 |     expect(errorText).toContain("Username or password is incorrect");
  17 |   });
  18 | 
  19 |   test("TC-017: login with wrong password shows generic error", async ({ page }) => {
  20 |     await page.locator("[data-testid='login-username-input']").fill("testuser");
  21 |     await page.locator("[data-testid='login-password-input']").fill("WrongPassword1!");
  22 |     await page.locator("[data-testid='login-button']").click();
  23 |     await expect(page.locator("[data-testid='login-error-alert']")).toBeVisible();
  24 |     const errorText = await page.locator("[data-testid='login-error-alert']").textContent();
  25 |     expect(errorText).toContain("Username or password is incorrect");
  26 |   });
  27 | 
  28 |   test("TC-019: error messages are identical for wrong user vs wrong password", async ({ page }) => {
  29 |     await page.locator("[data-testid='login-username-input']").fill("nonexistent_user");
  30 |     await page.locator("[data-testid='login-password-input']").fill("Any!");
  31 |     await page.locator("[data-testid='login-button']").click();
  32 |     const error1 = await page.locator("[data-testid='login-error-alert']").textContent();
  33 | 
  34 |     await page.goto("/auth/login");
  35 |     await page.waitForSelector("[data-testid='login-form']", { state: "visible" });
  36 |     await page.waitForTimeout(500);
  37 |     await page.locator("[data-testid='login-username-input']").fill("testuser");
  38 |     await page.locator("[data-testid='login-password-input']").fill("Wrong!");
  39 |     await page.locator("[data-testid='login-button']").click();
  40 |     const error2 = await page.locator("[data-testid='login-error-alert']").textContent();
  41 | 
  42 |     expect(error1).toBe(error2);
  43 |   });
  44 | 
  45 |   test("TC-018: 5 failed logins locks account", async ({ page }) => {
  46 |     const username = `locktest_${Date.now()}`;
  47 |     await page.goto("/auth/register");
  48 |     await page.locator("[data-testid='register-username-input']").fill(username);
  49 |     await page.locator("[data-testid='register-password-input']").fill("Test@1234");
  50 |     await page.locator("[data-testid='register-confirm-password-input']").fill("Test@1234");
  51 |     await page.locator("[data-testid='register-email-input']").fill(`${username}@example.com`);
  52 |     await page.locator("[data-testid='register-button']").click();
> 53 |     await page.waitForURL(/\/console/, { timeout: 10000 });
     |                ^ TimeoutError: page.waitForURL: Timeout 10000ms exceeded.
  54 |     await page.locator("[data-testid='logout-button']").click();
  55 |     await page.waitForURL(/\/auth\/login/, { timeout: 5000 });
  56 |     await page.waitForSelector("[data-testid='login-form']", { state: "visible" });
  57 |     await page.waitForTimeout(500);
  58 | 
  59 |     for (let i = 0; i < 5; i++) {
  60 |       await page.locator("[data-testid='login-username-input']").fill(username);
  61 |       await page.locator("[data-testid='login-password-input']").fill(`Wrong${i}!`);
  62 |       await page.locator("[data-testid='login-button']").click();
  63 |       await expect(page.locator("[data-testid='login-error-alert']")).toBeVisible();
  64 |     }
  65 | 
  66 |     await page.locator("[data-testid='login-password-input']").fill("Test@1234");
  67 |     await page.locator("[data-testid='login-button']").click();
  68 |     await expect(page.locator("[data-testid='login-error-alert']")).toBeVisible();
  69 |     const lockText = await page.locator("[data-testid='login-error-alert']").textContent();
  70 |     const normalizedText = lockText?.toLowerCase() || "";
  71 |     expect(normalizedText.includes("lock") || normalizedText.includes("15") || normalizedText.includes("暂") || normalizedText.includes("locked")).toBe(true);
  72 |   });
  73 | });
  74 | 
```