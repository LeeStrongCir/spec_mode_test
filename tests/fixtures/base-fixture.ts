{
  "description": "Playwright base fixture for auth E2E tests",
  "selectors": {
    "usernameInput": "[data-testid='username-input']",
    "passwordInput": "[data-testid='password-input']",
    "confirmPasswordInput": "[data-testid='confirm-password-input']",
    "emailInput": "[data-testid='email-input']",
    "loginButton": "[data-testid='login-button']",
    "registerButton": "[data-testid='register-button']",
    "logoutButton": "[data-testid='logout-button']",
    "rememberMeCheckbox": "[data-testid='remember-me-checkbox']",
    "backToLoginLink": "[data-testid='back-to-login-link']",
    "loginError": "[data-testid='login-error']",
    "usernameError": "[data-testid='username-error']",
    "passwordError": "[data-testid='password-error']",
    "confirmPasswordError": "[data-testid='confirm-password-error']",
    "emailError": "[data-testid='email-error']",
    "logoutSuccessMessage": "[data-testid='logout-success-message']",
    "sessionExpiredMessage": "[data-testid='session-expired-message']"
  },
  "defaultTimeout": 5000,
  "navigationTimeout": 10000,
  "baseUrl": "http://localhost:3000"
}
