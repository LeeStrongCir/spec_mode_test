# data-testid 映射表 — 001-register-login

**Feature**: Register and Login
**Spec**: specs/001-register-login/spec.md
**命名规范**: `[module]-[element]` 命名约定

---

## UI 基础组件 (components/ui/)

| data-testid | 组件 | 文件 |
|---|---|---|
| `{dataTestId}` | `Input` (动态) | `components/ui/input.tsx` |
| `{dataTestId}` | `Button` (动态) | `components/ui/button.tsx` |
| `{dataTestId}` | `Alert` (动态) | `components/ui/alert.tsx` |

---

## 注册页面

| data-testid | 组件 | 文件 | 说明 |
|---|---|---|---|
| `register-form` | `<form>` | `components/auth/register-form.tsx` | 注册表单容器 |
| `register-form-error` | `<Alert variant="error">` | `components/auth/register-form.tsx` | 服务端注册错误提示 |
| `register-username-input` | `<Input>` | `components/auth/register-form.tsx` | 用户名输入框 |
| `register-email-input` | `<Input>` | `components/auth/register-form.tsx` | 邮箱输入框 |
| `register-password-input` | `<Input>` | `components/auth/register-form.tsx` | 密码输入框 |
| `register-confirm-password-input` | `<Input>` | `components/auth/register-form.tsx` | 确认密码输入框 |
| `register-button` | `<Button variant="primary">` | `components/auth/register-form.tsx` | "Create Account" 提交按钮 |
| `register-login-link` | `<Link>` | `components/auth/register-form.tsx` | "Already have an account? Sign in" 链接 |

---

## 登录页面

| data-testid | 组件 | 文件 | 说明 |
|---|---|---|---|
| `login-form` | `<form>` | `components/auth/login-form.tsx` | 登录表单容器 |
| `login-error-alert` | `<Alert variant="error">` | `components/auth/login-form.tsx` | 服务端登录错误提示（含锁定/凭证错误） |
| `login-username-input` | `<Input>` | `components/auth/login-form.tsx` | 用户名输入框 |
| `login-password-input` | `<Input>` | `components/auth/login-form.tsx` | 密码输入框 |
| `login-remember` | `<input type="checkbox">` | `components/auth/login-form.tsx` | "Remember me" 复选框 |
| `login-button` | `<Button variant="primary">` | `components/auth/login-form.tsx` | "Sign In" 提交按钮 |
| `logout-success-alert` | `<Alert variant="success">` | `app/(auth)/auth/login/page.tsx` | 登出成功提示 "You have been successfully logged out" |

---

## 登出

| data-testid | 组件 | 文件 | 说明 |
|---|---|---|---|
| `logout-button` | `<Button variant="ghost">` | `components/auth/logout-button.tsx` | "Sign Out" 登出按钮 |

---

## 控制台页面

| data-testid | 组件 | 文件 | 说明 |
|---|---|---|---|
| `console-greeting` | `<p>` | `app/(console)/console/page.tsx` | "Welcome back, {username}" 问候语 |

---

## 统计

| 类别 | 数量 |
|---|---|
| **data-testid 总数** | 16 |
| **表单 (form)** | 2 |
| **输入框 (input)** | 7 |
| **按钮 (button)** | 3 |
| **提示 (alert)** | 3 |
| **链接 (link)** | 1 |

---

## 命名约定

所有 data-testid 遵循 `[module]-[element]` 格式：
- 注册模块：`register-*`
- 登录模块：`login-*`
- 登出模块：`logout-*`
- 控制台模块：`console-*`
