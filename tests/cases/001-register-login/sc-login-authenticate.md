# 测试用例: SC-02 输入凭据完成登录

**场景优先级**: P1 (MVP)
**对应 FR**: FR-001, FR-002, FR-003, FR-004, FR-005, FR-008, FR-012, FR-013
**宪章质量维度**: 功能正确性、Cookie安全性、路由守卫

---

## TC-010: 登录页面布局与元素验证

- **优先级**: P1
- **前置条件**: 用户未持有有效 JWT Cookie

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 用户访问 `/auth/login` | 页面正常加载，HTTP 状态码为 200 |
| 2 | 查看页面表单元素 | 展示用户名输入框、密码输入框，每个字段均有对应标签 |
| 3 | 查看页面操作区域 | 展示"记住我"复选框（未勾选状态）及"登录"按钮（处于可点击状态） |

**验证方式**: 手工 + E2E Playwright
**自动化文件**: `tests/e2e/001-register-login/test_register_login_flow.spec.ts`

---

## TC-011: 已认证用户访问登录页自动重定向

- **优先级**: P1
- **前置条件**: 用户已持有有效 JWT Cookie

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 已持有有效 JWT Cookie 的用户访问 `/auth/login` | 页面自动重定向至 `/console`（HTTP 302 后跟 200），不展示登录表单 |

**验证方式**: 集成 + E2E
**自动化文件**: `tests/integration/001-register-login/test_auth_middleware.py`

---

## TC-012: 登录表单项为空校验

- **优先级**: P1
- **前置条件**: 用户已访问 `/auth/login`

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 用户名和密码均为空，点击"登录"按钮 | 用户名字段下方显示"请输入用户名"，密码字段显示"请输入密码" → 表单不被提交 |

**验证方式**: 集成 + E2E
**自动化文件**: `tests/integration/001-register-login/test_login.py`

---

## TC-013: 正确凭据登录成功——Cookie 签发与重定向

- **优先级**: P1
- **前置条件**:
  - 系统中存在已注册的用户账户（用户名: `testuser`, 密码: `Test@1234`）
  - 用户未持有有效 JWT Cookie

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 用户输入正确的用户名 `testuser` 和密码 `Test@1234`，点击"登录"按钮 | "登录"按钮进入加载/禁用状态（防止重复提交） |
| 2 | 登录响应完成后观察页面变化 | 页面在 2 秒内重定向至 `/console`（HTTP 302 → 200） |
| 3 | 查看浏览器存储的 Cookie | 存在有效的 JWT Cookie，`Set-Cookie` 头中包含 `HttpOnly` 属性，`SameSite` 值为 `Lax` 或 `Strict` |
| 4 | 访问 `/console` | 页面正常加载，用户已认证，用户名或头像等个人标识可见 |

**验证方式**: 集成 + E2E
**自动化文件**: `tests/integration/001-register-login/test_login.py`, `tests/e2e/001-register-login/test_register_login_flow.spec.ts`

---

## TC-014: "记住我"——Cookie 持久化验证

- **优先级**: P2
- **前置条件**: 系统中存在已注册的用户账户

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 勾选"记住我"复选框，输入正确凭据 `testuser` / `Test@1234` 登录成功 | 签发的 JWT Cookie 的 `Max-Age` 或 `Expires` 属性为 30 天（2592000 秒） |
| 2 | 关闭浏览器所有窗口和进程 | 浏览器进程完全终止 |
| 3 | 重新打开浏览器并访问平台首页 `/` | JWT Cookie 仍存在且有效，自动认证通过，用户进入 `/console` |

**验证方式**: E2E（需要 freezegun 辅助验证时间属性）
**自动化文件**: `tests/e2e/001-register-login/test_register_login_flow.spec.ts`

---

## TC-015: 未勾选"记住我"——短期 Cookie 验证

- **优先级**: P2
- **前置条件**: 系统中存在已注册的用户账户

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 不勾选"记住我"复选框，输入正确凭据 `testuser` / `Test@1234` 登录成功 | 签发的 JWT Cookie 的 `Max-Age` 或 `Expires` 属性为 24 小时（86400 秒） |

**验证方式**: 集成（使用 freezegun 冻结服务端时间验证过期行为）
**自动化文件**: `tests/integration/001-register-login/test_login.py`
