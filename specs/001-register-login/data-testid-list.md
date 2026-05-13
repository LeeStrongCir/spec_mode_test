# data-testid Inventory: Register & Login Authentication

> All interactive UI elements must have `data-testid` with 100% coverage.
> Naming convention: `[功能模块]-[元素类型]`, kebab-case.

## LoginPage (`pages/auth/LoginPage.tsx`)

| data-testid | Element Type | Description | Validation State |
|---|---|---|---|
| `username-input` | Input (text) | Username input field | Valid: `username-valid`, Error: `username-error` |
| `password-input` | Input (password) | Password input field | Error: `password-error` |
| `remember-me-checkbox` | Checkbox | "Remember me" toggle | — |
| `login-button` | Button | Login submit button | Loading state during submission |

### Validation/Error Elements

| data-testid | Element Type | Description |
|---|---|---|
| `login-error-message` | Text/Alert | General login error message at page top |
| `username-input-error` | Text | Username field validation error |
| `password-input-error` | Text | Password field validation error |

---

## RegisterPage (`pages/auth/RegisterPage.tsx`)

| data-testid | Element Type | Description | Validation State |
|---|---|---|---|
| `username-input` | Input (text) | Username input field | Valid: `username-valid`, Error: `username-error` |
| `password-input` | Input (password) | Password input field | Error: `password-error` |
| `confirm-password-input` | Input (password) | Confirm password field | Error: `confirm-password-error` |
| `email-input` | Input (email) | Email address field | Valid: `email-valid`, Error: `email-error` |
| `register-button` | Button | Register submit button | Loading state during submission |

### Validation/Error Elements

| data-testid | Element Type | Description |
|---|---|---|
| `register-error-message` | Text/Alert | General register error message |
| `username-input-error` | Text | Username field error (duplicate, empty) |
| `password-input-error` | Text | Password field error (strength, empty) |
| `confirm-password-input-error` | Text | Confirm password field error (mismatch) |
| `email-input-error` | Text | Email field error (format, duplicate) |

### Navigation Elements

| data-testid | Element Type | Description |
|---|---|---|
| `back-to-login-link` | Link/Button | "已有账户？返回登录" → navigates to /auth/login |

---

## Layout / Header (`components/Layout.tsx`)

| data-testid | Element Type | Description |
|---|---|---|
| `user-avatar-button` | Button | User avatar dropdown trigger in top navigation |
| `user-dropdown-menu` | Dropdown | Container for user menu items |
| `logout-button` | Button | "退出登录" in user avatar dropdown menu |

---

## Dashboard (`pages/console/Dashboard.tsx`)

| data-testid | Element Type | Description |
|---|---|---|
| `dashboard-welcome` | Text | Welcome message showing username (non-interactive, for test verification) |

---

## Global / Shared Elements

| data-testid | Element Type | Description | Appears On |
|---|---|---|---|
| `session-expired-alert` | Alert/Text | "会话已过期，请重新登录" | LoginPage (after expired Cookie) |
| `logout-success-alert` | Alert/Text | "您已成功退出登录" | LoginPage (after logout redirect) |
| `network-error-alert` | Alert/Text | "网络连接失败" | LoginPage, RegisterPage |
| `csrf-token-hidden` | Hidden Input | CSRF token in web forms | LoginPage, RegisterPage forms |

---

## Summary

**Total interactive elements**: 20+ `data-testid` identifiers
**Pages covered**: Login, Register, Dashboard, Layout/Header
**Validation states**: All fields have error/valid state identifiers
**Coverage**: 100% of all interactive elements per constitutional mandate

| Feature Module | Elements |
|---|---|
| Login page | 9 |
| Register page | 10 |
| Layout/Header | 3 |
| Global/Shared | 4 |
