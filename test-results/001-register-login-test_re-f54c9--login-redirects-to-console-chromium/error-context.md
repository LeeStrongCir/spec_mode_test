# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 001-register-login/test_register_login_flow.spec.ts >> SC-01 + SC-02: Registration and Login Flow >> TC-013: successful login redirects to console
- Location: tests/e2e/001-register-login/test_register_login_flow.spec.ts:48:7

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
      - textbox "username" [ref=e12]: logintest_1778554686147
    - generic [ref=e13]:
      - generic [ref=e14]: Email
      - textbox "you@example.com" [ref=e16]: logintest_1778554686147@example.com
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
  3  | test.describe("SC-01 + SC-02: Registration and Login Flow", () => {
  4  |   test("TC-001: register page loads with all form elements", async ({ page }) => {
  5  |     await page.goto("/auth/register");
  6  |     await expect(page.locator("[data-testid='register-username-input']")).toBeVisible();
  7  |     await expect(page.locator("[data-testid='register-password-input']")).toBeVisible();
  8  |     await expect(page.locator("[data-testid='register-confirm-password-input']")).toBeVisible();
  9  |     await expect(page.locator("[data-testid='register-email-input']")).toBeVisible();
  10 |     await expect(page.locator("[data-testid='register-button']")).toBeVisible();
  11 |     await expect(page.locator("[data-testid='register-login-link']")).toBeVisible();
  12 |   });
  13 | 
  14 |   test("TC-002: empty form submission shows validation errors", async ({ page }) => {
  15 |     await page.goto("/auth/register");
  16 |     await page.waitForSelector("[data-testid='register-button']", { state: "visible" });
  17 |     await page.locator("[data-testid='register-button']").click();
  18 |     await expect(page.locator("[data-testid='register-username-input']")).toBeVisible();
  19 |     await expect(page.locator("[data-testid='register-password-input']")).toBeVisible();
  20 |   });
  21 | 
  22 |   test("TC-007: successful registration creates account and redirects to console", async ({ page }) => {
  23 |     await page.goto("/auth/register");
  24 |     await page.waitForSelector("[data-testid='register-button']", { state: "visible" });
  25 |     const username = `newuser${Date.now()}`;
  26 |     await page.locator("[data-testid='register-username-input']").fill(username);
  27 |     await page.locator("[data-testid='register-password-input']").fill("Test@1234");
  28 |     await page.locator("[data-testid='register-confirm-password-input']").fill("Test@1234");
  29 |     await page.locator("[data-testid='register-email-input']").fill(`${username}@example.com`);
  30 |     await page.locator("[data-testid='register-button']").click();
  31 |     await page.waitForURL(/\/console/, { timeout: 10000 });
  32 |   });
  33 | 
  34 |   test("TC-008: back to login link redirects to login page", async ({ page }) => {
  35 |     await page.goto("/auth/register");
  36 |     await page.locator("[data-testid='register-login-link']").click();
  37 |     await expect(page).toHaveURL(/\/auth\/login/);
  38 |   });
  39 | 
  40 |   test("TC-010: login page loads with all form elements", async ({ page }) => {
  41 |     await page.goto("/auth/login");
  42 |     await expect(page.locator("[data-testid='login-username-input']")).toBeVisible();
  43 |     await expect(page.locator("[data-testid='login-password-input']")).toBeVisible();
  44 |     await expect(page.locator("[data-testid='login-remember']")).toBeVisible();
  45 |     await expect(page.locator("[data-testid='login-button']")).toBeVisible();
  46 |   });
  47 | 
  48 |   test("TC-013: successful login redirects to console", async ({ page }) => {
  49 |     await page.goto("/auth/register");
  50 |     const username = `logintest_${Date.now()}`;
  51 |     await page.locator("[data-testid='register-username-input']").fill(username);
  52 |     await page.locator("[data-testid='register-password-input']").fill("Test@1234");
  53 |     await page.locator("[data-testid='register-confirm-password-input']").fill("Test@1234");
  54 |     await page.locator("[data-testid='register-email-input']").fill(`${username}@example.com`);
  55 |     await page.locator("[data-testid='register-button']").click();
> 56 |     await page.waitForURL(/\/console/, { timeout: 10000 });
     |                ^ TimeoutError: page.waitForURL: Timeout 10000ms exceeded.
  57 |     await page.locator("[data-testid='logout-button']").click();
  58 |     await page.waitForURL(/\/auth\/login/, { timeout: 5000 });
  59 | 
  60 |     await page.locator("[data-testid='login-username-input']").fill(username);
  61 |     await page.locator("[data-testid='login-password-input']").fill("Test@1234");
  62 |     await page.locator("[data-testid='login-button']").click();
  63 |     await page.waitForURL(/\/console/, { timeout: 10000 });
  64 |     await expect(page.locator("[data-testid='console-greeting']")).toBeVisible();
  65 |   });
  66 | });
  67 | 
```