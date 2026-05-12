# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: 001-register-login/test_logout_flow.spec.ts >> SC-04: Logout Flow >> TC-022: expired cookie redirects to login on protected page access
- Location: tests/e2e/001-register-login/test_logout_flow.spec.ts:32:7

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
      - textbox "username" [ref=e12]: testuser_e2e_1778554671512
    - generic [ref=e13]:
      - generic [ref=e14]: Email
      - textbox "you@example.com" [ref=e16]: testuser_e2e_1778554671512@example.com
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
  3  | test.describe.configure({ mode: 'parallel' });
  4  | 
  5  | test.describe("SC-04: Logout Flow", () => {
  6  |   async function registerAndLogin(page: import("@playwright/test").Page) {
  7  |     await page.goto("/auth/register");
  8  |     const username = `testuser_e2e_${Date.now()}`;
  9  |     await page.locator("[data-testid='register-username-input']").fill(username);
  10 |     await page.locator("[data-testid='register-password-input']").fill("Test@1234");
  11 |     await page.locator("[data-testid='register-confirm-password-input']").fill("Test@1234");
  12 |     await page.locator("[data-testid='register-email-input']").fill(`${username}@example.com`);
  13 |     await page.locator("[data-testid='register-button']").click();
> 14 |     await page.waitForURL(/\/console/, { timeout: 10000 });
     |                ^ TimeoutError: page.waitForURL: Timeout 10000ms exceeded.
  15 |   }
  16 | 
  17 |   test("TC-020: logout clears cookie and redirects to login", async ({ page }) => {
  18 |     await registerAndLogin(page);
  19 |     await page.locator("[data-testid='logout-button']").click();
  20 |     await expect(page).toHaveURL(/\/auth\/login/);
  21 |     await expect(page.locator("[data-testid='logout-success-alert']")).toBeVisible();
  22 |   });
  23 | 
  24 |   test("TC-021: browser back button protection after logout", async ({ page }) => {
  25 |     await registerAndLogin(page);
  26 |     await page.locator("[data-testid='logout-button']").click();
  27 |     await expect(page).toHaveURL(/\/auth\/login/);
  28 |     await page.goBack();
  29 |     await expect(page).toHaveURL(/\/auth\/login/);
  30 |   });
  31 | 
  32 |   test("TC-022: expired cookie redirects to login on protected page access", async ({ page }) => {
  33 |     await registerAndLogin(page);
  34 |     await page.locator("[data-testid='logout-button']").click();
  35 |     await expect(page).toHaveURL(/\/auth\/login/);
  36 |     await page.goto("/console/dashboard");
  37 |     await expect(page).toHaveURL(/\/auth\/login/);
  38 |   });
  39 | });
  40 | 
```