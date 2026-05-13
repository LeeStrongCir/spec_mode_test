// Spec: specs/001-register-login/spec.md → E2E User Stories 1-4

import { type Page, type Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly rememberMeCheckbox: Locator;
  readonly loginButton: Locator;
  readonly errorMessage: Locator;
  readonly successMessage: Locator;
  readonly usernameInputError: Locator;
  readonly passwordInputError: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.getByTestId('auth-username-input');
    this.passwordInput = page.getByTestId('auth-password-input');
    this.rememberMeCheckbox = page.getByTestId('auth-remember-me-checkbox');
    this.loginButton = page.getByTestId('auth-login-button');
    this.errorMessage = page.getByTestId('auth-login-error-message');
    this.successMessage = page.getByTestId('auth-success-message');
    this.usernameInputError = page.getByTestId('auth-username-input-error');
    this.passwordInputError = page.getByTestId('auth-password-input-error');
  }

  async goto() {
    await this.page.goto('/auth/login');
  }

  async login(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }

  async loginWithRememberMe(username: string, password: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.rememberMeCheckbox.check();
    await this.loginButton.click();
  }

  async selectRememberMe() {
    await this.rememberMeCheckbox.check();
  }

  async getErrorMessage(): Promise<string> {
    return await this.errorMessage.textContent();
  }

  async getSuccessMessage(): Promise<string> {
    return await this.successMessage.textContent();
  }

  async getUsernameInputError(): Promise<string> {
    return await this.usernameInputError.textContent();
  }

  async getPasswordInputError(): Promise<string> {
    return await this.passwordInputError.textContent();
  }

  async isErrorMessageVisible(): Promise<boolean> {
    return await this.errorMessage.isVisible();
  }

  async isLoginButtonDisabled(): Promise<boolean> {
    return await this.loginButton.isDisabled();
  }
}
