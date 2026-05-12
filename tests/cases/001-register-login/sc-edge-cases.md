# 测试用例: SC-05 边缘情况与异常

**场景优先级**: N/A（边缘/安全用例）
**对应 FR**: FR-010, FR-011, FR-009, FR-020, FR-021, FR-013
**宪章质量维度**: 安全防护（CSRF、限速、路由守卫）、审计合规

---

## EC-001: CSRF Token 校验失败

- **严重程度**: 高
- **对应 FR**: FR-010, FR-020

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 不携带 CSRF Token 提交登录请求（如通过 curl 或 httpx 直接 POST `/api/auth/login`，请求头中不含 `X-CSRF-Token` 或表单中不含 `_csrf_token`） | 服务端返回 `403 Forbidden` 状态码，响应内容不含敏感信息 |
| 2 | 携带伪造/不匹配的 CSRF Token 提交登录或注册请求 | 服务端返回 `403 Forbidden` 状态码，表单未被处理 |
| 3 | 先 GET 登录页获取有效 CSRF Token，在 POST 登录请求中携带该 Token | 请求正常处理，CSRF 校验通过（正向验证） |

**验证方式**: 集成
**自动化文件**: `tests/integration/001-register-login/test_csrf_middleware.py`

---

## EC-002: IP 登录请求限速（同一 IP 每分钟 10 次上限）

- **严重程度**: 高
- **对应 FR**: FR-011

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 从同一 IP（通过 `X-Forwarded-For` 头模拟）连续发起 10 次登录请求（无论凭据是否正确） | 前 10 次请求正常处理（返回 200、302、401、403 等正常业务状态码） |
| 2 | 在第 11 次发起登录请求（同一 IP，1 分钟时间窗口内） | 服务端返回 `429 Too Many Requests` 状态码 |
| 3 | 查看第 11 次响应内容 | 响应体或响应头中包含"请求过于频繁，请稍后重试"或等价的限速提示 |

**验证方式**: 集成（使用 `X-Forwarded-For` 头模拟不同 IP，fakeredis 隔离限速状态）
**自动化文件**: `tests/integration/001-register-login/test_rate_limiter.py`

---

## EC-003: 未认证用户访问受保护路由

- **严重程度**: 高
- **对应 FR**: FR-009

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 无有效 JWT Cookie 的用户访问 `/console/dashboard` | 页面重定向至 `/auth/login`（HTTP 302），不展示控制台内容 |
| 2 | 无有效 JWT Cookie 的用户访问 `/console/settings` | 页面重定向至 `/auth/login` |
| 3 | 覆盖任意 `/console/*` 路径（如 `/console/billing`, `/console/notifications` 等） | 所有路径均被认证中间件拦截并重定向至 `/auth/login` |

**验证方式**: 集成 + E2E
**自动化文件**: `tests/integration/001-register-login/test_auth_middleware.py`

---

## EC-004: 已认证用户访问注册页自动重定向

- **严重程度**: 中
- **对应 FR**: FR-021

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 已登录（持有有效 JWT Cookie）用户访问 `/auth/register` | 页面自动重定向至 `/console`（HTTP 302 → 200），不展示注册表单 |
| 2 | 查看重定向后的页面内容 | 页面加载控制台首页内容，用户个人信息可见 |

**验证方式**: 集成
**自动化文件**: `tests/integration/001-register-login/test_auth_middleware.py`

---

## EC-005: 审计日志记录完整性

- **严重程度**: 中
- **对应 FR**: FR-013

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 执行一次成功登录（正确用户名 + 正确密码） | 审计日志包含：用户名、时间戳、IP 地址、操作结果（`success`） |
| 2 | 执行一次失败登录（正确用户名 + 错误密码） | 审计日志包含：用户名、时间戳、IP 地址、操作结果（`failure`） |
| 3 | 执行一次连续锁定登录（第 6 次失败达到锁定阈值） | 审计日志包含：用户名、时间戳、IP 地址、操作结果（`locked`） |
| 4 | 执行一次退出登录 | 审计日志包含：用户名、时间戳、IP 地址、操作结果（`logout`） |

**验证方式**: 集成（查询审计日志表或 Mock 服务记录）
**自动化文件**: `tests/integration/001-register-login/test_login.py`
