# 测试用例: SC-04 退出登录

**场景优先级**: P2
**对应 FR**: FR-007, FR-009
**宪章质量维度**: 功能正确性、会话安全、Cookie 管理

---

## TC-020: 正常退出登录——Cookie 清除与重定向

- **优先级**: P2
- **前置条件**:
  - 用户已成功登录并持有有效 JWT Cookie
  - 用户处于 `/console` 下任一页面

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 用户点击右上角用户头像菜单中的"退出登录"选项 | 退出请求（POST/GET /api/auth/logout）已发送，按钮进入加载状态 |
| 2 | 查看浏览器存储的 Cookie | JWT Cookie 已被清除或 `Set-Cookie` 响应头中设置了过期时间为过去时间（`Expires=Thu, 01 Jan 1970 00:00:00 GMT`）|
| 3 | 查看当前页面 URL | 页面已重定向至 `/auth/login` |
| 4 | 查看登录页顶部区域 | 显示"您已成功退出登录"成功提示信息 |

**验证方式**: 集成 + E2E
**自动化文件**: `tests/integration/001-register-login/test_logout.py`, `tests/e2e/001-register-login/test_logout_flow.spec.ts`

---

## TC-021: 退出后浏览器后退防护

- **优先级**: P2
- **前置条件**:
  - 用户已成功登录
  - 用户已执行退出登录操作，页面已处于 `/auth/login`

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 退出登录完成后，页面已处于 `/auth/login` | 当前页面 URL 为 `/auth/login`，页面为登录表单 |
| 2 | 点击浏览器"后退"按钮 | 页面仍停留在 `/auth/login`（或 `/auth/logout`），**无法**返回到之前的 `/console/*` 页面 |
| 3 | 尝试后退后查看 `/console/*` 页面状态 | 如后退到达控制台页面，页面立即重定向至 `/auth/login`（路由守卫拦截） |

**验证方式**: E2E Playwright（使用 `page.goBack()` 验证后退行为）
**自动化文件**: `tests/e2e/001-register-login/test_logout_flow.spec.ts`

---

## TC-022: Cookie 过期后访问受保护页面

- **优先级**: P2
- **前置条件**:
  - 用户已持有**已过期**的 JWT Cookie（通过 freezegun 或手动设置过期 Cookie 模拟）

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 模拟 JWT Cookie 已过期（服务端时间已超过 JWT 的 `exp` 声明值） | Cookie 在浏览器中仍存在但服务端判定为无效 |
| 2 | 用户访问 `/console/dashboard`（或任意 `/console/*` 路径） | 页面重定向至 `/auth/login`（HTTP 302），不展示控制台页面内容 |
| 3 | 查看登录页顶部区域 | 显示"会话已过期，请重新登录"提示信息 |

**验证方式**: 集成（使用 freezegun 冻结时间 + httpx 客户端） + E2E（设置短过期时间后等待过期）
**自动化文件**: `tests/integration/001-register-login/test_auth_middleware.py`
