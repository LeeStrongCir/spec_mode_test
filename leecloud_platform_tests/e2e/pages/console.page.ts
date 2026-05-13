// Spec: specs/001-register-login/spec.md → E2E User Stories 1-4

import { type Page, type Locator } from '@playwright/test';

export class ConsolePage {
  readonly page: Page;
  readonly dashboardHeading: Locator;
  readonly logoutButton: Locator;
  readonly sessionExpiredAlert: Locator;

  constructor(page: Page) {
    this.page = page;
    this.dashboardHeading = page.getByTestId('console-dashboard-heading');
    this.logoutButton = page.getByTestId('auth-logout-button');
    this.sessionExpiredAlert = page.getByTestId('session-expired-alert');
  }

  async goto() {
    await this.page.goto('/console');
  }

  async isDashboardVisible(): Promise<boolean> {
    return await this.dashboardHeading.isVisible();
  }

  async logout() {
    await this.logoutButton.click();
  }

  async getSessionExpiredMessage(): Promise<string> {
    return await this.sessionExpiredAlert.textContent();
  }
}
