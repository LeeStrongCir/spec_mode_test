// Spec: specs/001-register-login/spec.md → E2E User Stories 1-4

import { type Page, type Locator } from '@playwright/test';

export class RegisterPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly confirmPasswordInput: Locator;
  readonly emailInput: Locator;
  readonly registerButton: Locator;
  readonly loginLink: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.getByTestId('auth-username-input');
    this.passwordInput = page.getByTestId('auth-password-input');
    this.confirmPasswordInput = page.getByTestId('auth-confirm-password-input');
    this.emailInput = page.getByTestId('auth-email-input');
    this.registerButton = page.getByTestId('auth-register-button');
    this.loginLink = page.getByTestId('auth-login-link');
    this.errorMessage = page.getByTestId('auth-register-error-message');
  }

  async goto() {
    await this.page.goto('/auth/register');
  }

  async register(username: string, password: string, confirmPassword: string, email: string) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.confirmPasswordInput.fill(confirmPassword);
    await this.emailInput.fill(email);
    await this.registerButton.click();
  }

  async clickLoginLink() {
    await this.loginLink.click();
  }

  async getErrorMessage(): Promise<string> {
    return await this.errorMessage.textContent();
  }
}
