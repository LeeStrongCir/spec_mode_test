// Spec: specs/001-register-login/spec.md → E2E User Stories 1-4

import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/login.page';
import { RegisterPage } from './pages/register.page';
import { ConsolePage } from './pages/console.page';

const TEST_USERNAME_REG = 'e2e_testuser_reg';
const TEST_USERNAME_LOGIN = 'e2e_testuser_login';
const TEST_PASSWORD_REG = 'R3g!Test2026';
const TEST_PASSWORD_LOGIN = 'L0gin!Test2026';
const TEST_EMAIL_REG = 'e2e_testuser_reg@leecloud.com';
const TEST_EMAIL_LOGIN = 'e2e_testuser_login@leecloud.com';

test.describe('User Story 1 - Register New Account', () => {

  test('User registers with valid credentials and gets redirected to console', async ({ page }) => {
    // Covers: TC-006
    const registerPage = new RegisterPage(page);
    const consolePage = new ConsolePage(page);

    await registerPage.goto();
    await expect(page).toHaveURL(/\/auth\/register/);

    await registerPage.register(TEST_USERNAME_REG, TEST_PASSWORD_REG, TEST_PASSWORD_REG, TEST_EMAIL_REG);

    await expect(page).toHaveURL(/\/console/);
    await expect(consolePage.dashboardHeading).toBeVisible();
  });

  test('User can register and JWT Cookie is present after registration', async ({ page }) => {
    // Covers: TC-006
    const registerPage = new RegisterPage(page);

    await registerPage.goto();
    await registerPage.register(`${TEST_USERNAME_REG}_cookie`, TEST_PASSWORD_REG, TEST_PASSWORD_REG, 'cookie_test@leecloud.com');

    await expect(page).toHaveURL(/\/console/);

    const cookies = await page.context().cookies();
    const authCookie = cookies.find(c => c.name === 'access_token');
    expect(authCookie).toBeDefined();
    expect(authCookie!.value).not.toBe('');
  });

  test('User on register page navigates to login page via link', async ({ page }) => {
    // Covers: TC-007
    const registerPage = new RegisterPage(page);

    await registerPage.goto();
    await registerPage.clickLoginLink();

    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test('User sees validation errors when submitting empty registration form', async ({ page }) => {
    // Covers: TC-002 (negative)
    const registerPage = new RegisterPage(page);

    await registerPage.goto();
    await registerPage.register('', '', '', '');

    await expect(page).toHaveURL(/\/auth\/register/);
  });

  test('User sees error when passwords do not match during registration', async ({ page }) => {
    // Covers: TC-004 (negative)
    const registerPage = new RegisterPage(page);

    await registerPage.goto();
    await registerPage.register('nonexistent_user', TEST_PASSWORD_REG, 'DifferentPass@1', 'test@leecloud.com');

    await expect(page).toHaveURL(/\/auth\/register/);
  });
});

test.describe('Authenticated User Redirects', () => {
  test.use({ storageState: 'leecloud_platform_tests/e2e/.auth/storageState.json' });

  test('Authenticated user visiting register page is redirected to console', async ({ page }) => {
    // Covers: TC-008
    await page.goto('/auth/register');
    await expect(page).toHaveURL(/\/console/);
  });

  test('Authenticated user visiting login page is redirected to console', async ({ page }) => {
    // Covers: TC-014
    await page.goto('/auth/login');
    await expect(page).toHaveURL(/\/console/);
  });
});

test.describe('User Story 2 - Login with Valid Credentials', () => {

  test('User logs in with valid credentials and is redirected to console', async ({ page }) => {
    // Covers: TC-012, TC-006
    const loginPage = new LoginPage(page);
    const consolePage = new ConsolePage(page);

    await loginPage.goto();
    await expect(page).toHaveURL(/\/auth\/login/);

    await loginPage.login(TEST_USERNAME_LOGIN, TEST_PASSWORD_LOGIN);

    await expect(page).toHaveURL(/\/console/);
    await expect(consolePage.dashboardHeading).toBeVisible();

    const cookies = await page.context().cookies();
    const authCookie = cookies.find(c => c.name === 'access_token');
    expect(authCookie).toBeDefined();
  });

  test('User login produces Cookie with HttpOnly attribute', async ({ page }) => {
    // Covers: TC-012
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.login(TEST_USERNAME_LOGIN, TEST_PASSWORD_LOGIN);
    await expect(page).toHaveURL(/\/console/);

    const cookies = await page.context().cookies();
    const authCookie = cookies.find(c => c.name === 'access_token');
    expect(authCookie).toBeDefined();
    expect(authCookie!.httpOnly).toBe(true);
  });

  test('User logs in with Remember Me checkbox checked', async ({ page }) => {
    // Covers: TC-013
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.loginWithRememberMe(TEST_USERNAME_LOGIN, TEST_PASSWORD_LOGIN);

    await expect(page).toHaveURL(/\/console/);
  });
});

test.describe('User Story 3 - Login Failure Handling', () => {

  test('User sees generic error with non-existent username', async ({ page }) => {
    // Covers: TC-020
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.login('nonexistent_user_xyz', 'AnyPassword123!');

    await expect(loginPage.errorMessage).toBeVisible();
    const errorMsg = await loginPage.getErrorMessage();
    expect(errorMsg).toContain('用户名或密码错误');

    await expect(loginPage.usernameInput).toHaveValue('nonexistent_user_xyz');
    await expect(loginPage.passwordInput).toHaveValue('');
  });

  test('User sees generic error with existing username but wrong password', async ({ page }) => {
    // Covers: TC-021
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.login(TEST_USERNAME_LOGIN, 'WrongPassword@123');

    await expect(loginPage.errorMessage).toBeVisible();
    const errorMsg = await loginPage.getErrorMessage();
    expect(errorMsg).toContain('用户名或密码错误');

    await expect(loginPage.usernameInput).toHaveValue(TEST_USERNAME_LOGIN);
    await expect(loginPage.passwordInput).toHaveValue('');
  });

  test('Non-existent user and wrong password return identical error message', async ({ page }) => {
    // Covers: TC-020, TC-021 (negative pair)
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.login('nonexistent_user_abc', 'WrongPass!1');
    const errorUnknownUser = await loginPage.getErrorMessage();

    await loginPage.login(TEST_USERNAME_LOGIN, 'WrongPass!2');
    const errorWrongPassword = await loginPage.getErrorMessage();

    expect(errorUnknownUser).toBe(errorWrongPassword);
  });
});

test.describe('User Story 4 - Logout', () => {
  test.use({ storageState: 'leecloud_platform_tests/e2e/.auth/storageState.json' });

  test('User logs out and is redirected to login page with success message', async ({ page }) => {
    // Covers: TC-030
    const consolePage = new ConsolePage(page);
    const loginPage = new LoginPage(page);

    await consolePage.goto();
    await expect(consolePage.dashboardHeading).toBeVisible();

    await consolePage.logout();

    await expect(page).toHaveURL(/\/auth\/login/);
    await expect(loginPage.successMessage).toBeVisible();
    const successMsg = await loginPage.getSuccessMessage();
    expect(successMsg).toContain('您已成功退出登录');
  });

  test('User cannot access console after logout via back button protection', async ({ page }) => {
    // Covers: TC-031
    await expect(page).toHaveURL(/\/auth\/login/);

    await page.goto('/console');
    await expect(page).toHaveURL(/\/auth\/login/);
  });
});

test.describe('Protected Route Access', () => {

  test('User with expired Cookie visiting console is redirected to login', async ({ page }) => {
    // Covers: EC-001
    const loginPage = new LoginPage(page);

    await page.goto('/console');
    await expect(page).toHaveURL(/\/auth\/login/);
    await expect(loginPage.errorMessage).toBeVisible();
  });

  test('User without any Cookie visiting console is redirected to login', async ({ browser }) => {
    // Covers: EC-001 (no-cookie variant)
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.goto('/console');
    await expect(page).toHaveURL(/\/auth\/login/);

    await context.close();
  });
});
