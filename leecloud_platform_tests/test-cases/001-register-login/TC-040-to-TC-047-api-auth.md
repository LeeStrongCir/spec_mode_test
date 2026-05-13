# 测试用例：TC-040 ~ TC-047 — API 认证 (SC-05)

> **源规格**: `specs/001-register-login/spec.md`
> **相关功能需求**: FR-022 ~ FR-030
> **优先级**: P2
> **测试类型**: API 功能测试
> **创建日期**: 2026-05-13
> **可追溯性**: 用户故事 #5 — API 外部服务认证

---

## 数据准备

| 数据项 | 值 | 备注 |
|--------|------|------|
| API 端点基地址 | `/api/v1/auth/*` | 认证相关 API 统一前缀 |
| 登录端点 | `POST /api/v1/auth/login` | API 登录接口 |
| 刷新端点 | `POST /api/v1/auth/refresh` | Token 刷新接口 |
| 登出端点 | `POST /api/v1/auth/logout` | API 登出接口 |
| 已存在用户名 | `apiuser` | 系统中已注册的有效账户 |
| 已存在密码 | `ApiTest@1234` | 符合强度要求（8-32位，含字母+数字+特殊字符） |
| 有效 JWT Token 结构 | `{ "sub": "user_id", "username": "apiuser", "role": "user", "iat": 1715000000, "exp": 1715086400, "jti": "uuid" }` | 包含用户ID、用户名、角色、签发时间、过期时间、唯一标识 |
| refresh_token 格式 | UUID v4 字符串 | 单次使用标志（single-use），使用后立即失效 |
| 统一响应格式 | `{ "success": boolean, "data": object|null, "error": { "code": string, "message": string }|null }` | 所有 API 响应遵循 FR-030 统一格式 |

---

## TC-040: API 登录 — 有效凭据

- **优先级**: P2
- **源**: spec.md → 用户故事 #5 → TC-040
- **相关FR**: FR-022（API登录）、FR-023（JWT签发）、FR-030（统一响应格式）

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 发送 POST 请求至 `/api/v1/auth/login`，Headers: `Content-Type: application/json` | 请求正常发送 |
| 2 | 请求体: `{"username": "apiuser", "password": "ApiTest@1234"}` | 无错误提示 |
| 3 | 检查 HTTP 状态码 | 返回 `200 OK` |
| 4 | 检查响应体 `success` 字段 | `success: true` |
| 5 | 检查响应体 `data.access_token` 字段 | 存在且为有效的 JWT 字符串，包含 claims: user ID、username、role、issued_at、expires_at、jti |
| 6 | 检查响应体 `data.refresh_token` 字段 | 存在且为 UUID 格式字符串，具有 single-use 标志 |
| 7 | 检查响应体 `data.expires_in` 字段 | 值为 `86400`（秒） |
| 8 | 检查响应体 `data.user` 字段 | 包含 `id`（uuid）、`username`（"apiuser"）、`role`（"user"） |
| 9 | 检查响应体 `error` 字段 | `error: null` |
| 10 | 检查响应是否设置 HttpOnly Cookie | **不设置**任何 HttpOnly Cookie（API 模式，非 Web Cookie 模式） |

---

## TC-041: API 登录 — 无效凭据

- **优先级**: P2
- **源**: spec.md → 用户故事 #5 → TC-041
- **相关FR**: FR-024（认证失败处理）、FR-030（统一响应格式）

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 发送 POST 请求至 `/api/v1/auth/login`，Headers: `Content-Type: application/json` | 请求正常发送 |
| 2 | 请求体: `{"username": "apiuser", "password": "WrongPassword123!"}` | 密码错误或用户名不存在 |
| 3 | 检查 HTTP 状态码 | 返回 `401 Unauthorized` |
| 4 | 检查响应体 `success` 字段 | `success: false` |
| 5 | 检查响应体 `data` 字段 | `data: null` |
| 6 | 检查响应体 `error.code` 字段 | `"INVALID_CREDENTIALS"` |
| 7 | 检查响应体 `error.message` 字段 | `"用户名或密码错误"`（通用错误信息，不区分用户名不存在还是密码错误） |
| 8 | 检查响应体是否泄露具体失败原因 | **不应**返回"用户不存在"或"密码错误"等具体信息（防枚举攻击） |

---

## TC-042: API 登录 — 账号连续失败 5 次后锁定

- **优先级**: P2
- **源**: spec.md → 用户故事 #5 → TC-042
- **相关FR**: FR-025（账号锁定机制）、FR-030（统一响应格式）

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 发送 POST 请求至 `/api/v1/auth/login`，使用有效用户名 `apiuser` 和错误密码，连续发送 **5 次** | 前 5 次均返回 `401 Unauthorized` + `INVALID_CREDENTIALS` 错误 |
| 2 | 第 6 次发送相同请求（同一用户名，错误密码） | 第 6 次请求开始返回 `423 Locked` |
| 3 | 检查 423 响应体 `success` 字段 | `success: false` |
| 4 | 检查 423 响应体 `error.code` 字段 | `"ACCOUNT_LOCKED"` |
| 5 | 检查 423 响应体 `error.message` 字段 | `"账号已被临时锁定，请 15 分钟后再试"` |
| 6 | 等待 15 分钟后，用**正确凭据**尝试登录 | 登录成功，返回 `200 OK` + 有效 tokens |
| 7 | 用**正确凭据**在锁定期间（< 15 分钟）尝试登录 | 仍返回 `423 Locked`，锁定不因正确登录而提前解除 |

---

## TC-043: Token 刷新 — 有效 refresh_token

- **优先级**: P2
- **源**: spec.md → 用户故事 #5 → TC-043
- **相关FR**: FR-026（Token刷新）、FR-027（refresh_token单次使用）、FR-030（统一响应格式）

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 先完成 TC-040 获取有效的 `access_token` 和 `refresh_token` | 获得有效凭据 |
| 2 | 发送 POST 请求至 `/api/v1/auth/refresh`，Headers: `Content-Type: application/json` | 请求正常发送 |
| 3 | 请求体: `{"refresh_token": "<上一步获得的refresh_token>"}` | refresh_token 为 UUID 格式 |
| 4 | 检查 HTTP 状态码 | 返回 `200 OK` |
| 5 | 检查响应体 `success` 字段 | `success: true` |
| 6 | 检查响应体 `data.access_token` 字段 | 存在且为**新的** JWT 字符串（与旧 token 不同，jti 不同） |
| 7 | 检查响应体 `data.refresh_token` 字段 | 存在且为**新的** UUID 字符串（与旧 refresh_token 不同） |
| 8 | 检查旧 refresh_token 是否已失效 | 再次使用旧 refresh_token 请求时返回 `401 INVALID_TOKEN` |
| 9 | 检查新 access_token 的 JWT claims | 包含正确的 user ID、username、role、issued_at（更新为当前时间）、expires_at（+86400秒）、新的 jti |

---

## TC-044: Token 刷新 — 过期/无效 refresh_token

- **优先级**: P2
- **源**: spec.md → 用户故事 #5 → TC-044
- **相关FR**: FR-027（refresh_token单次使用）、FR-030（统一响应格式）

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 先完成 TC-043 一次 token 刷新，保留旧 refresh_token | 旧 refresh_token 已被标记为已使用 |
| 2 | 发送 POST 请求至 `/api/v1/auth/refresh`，使用**已被使用过的旧 refresh_token** | 请求正常发送 |
| 3 | 检查 HTTP 状态码 | 返回 `401 Unauthorized` |
| 4 | 检查响应体 `error.code` 字段 | `"INVALID_TOKEN"` |
| 5 | 检查响应体 `error.message` 字段 | `"刷新令牌已过期"` |
| 6 | 使用**伪造的 UUID**（非系统中存在过的 refresh_token）请求 | 同样返回 `401 INVALID_TOKEN` |
| 7 | 使用**空字符串**作为 refresh_token 请求 | 返回 `422 VALIDATION_ERROR`（请求体验证失败） |

---

## TC-045: API 登出 — 有效 token 黑名单化

- **优先级**: P2
- **源**: spec.md → 用户故事 #5 → TC-045
- **相关FR**: FR-028（API登出）、FR-029（Token黑名单）、FR-030（统一响应格式）

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 先完成 TC-040 获取有效的 `access_token` | 获得有效 JWT |
| 2 | 发送 POST 请求至 `/api/v1/auth/logout`，Headers: `Authorization: Bearer <access_token>` | 请求正常发送 |
| 3 | 检查 HTTP 状态码 | 返回 `200 OK` |
| 4 | 检查响应体 `success` 字段 | `success: true` |
| 5 | 检查响应体 `data` 字段 | `data: null` |
| 6 | 检查响应体 `error` 字段 | `error: null` |
| 7 | 使用**同一个 access_token** 访问需要认证的保护端点 | 返回 `401 UNAUTHORIZED`（token 已被加入黑名单） |
| 8 | 使用**同一个 access_token** 再次调用 logout 端点 | 返回 `401 UNAUTHORIZED`（token 已失效） |

---

## TC-046: 未认证访问受保护 API

- **优先级**: P2
- **源**: spec.md → 用户故事 #5 → TC-046
- **相关FR**: FR-029（Token黑名单）、FR-030（统一响应格式）

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 选择任意一个需要认证的受保护 API 端点（如 `/api/v1/auth/logout` 或其他保护端点） | 端点需要 Bearer Token |
| 2 | 发送请求，**不携带**任何 Authentication Header 或 Token | 请求正常发送 |
| 3 | 检查 HTTP 状态码 | 返回 `401 Unauthorized` |
| 4 | 检查响应体 `error.code` 字段 | `"UNAUTHORIZED"` |
| 5 | 检查响应体 `error.message` 字段 | `"未授权"` |
| 6 | 发送请求，携带**伪造/无效的 JWT Token**: `Authorization: Bearer invalid.token.here` | 同样返回 `401 UNAUTHORIZED` |
| 7 | 发送请求，携带**过期 JWT Token**（已过期未黑名单化的历史 token） | 返回 `401 INVALID_TOKEN`（token 已过期） |

---

## TC-047: IP 速率限制 — 1 分钟内超过 10 次请求

- **优先级**: P2
- **源**: spec.md → 用户故事 #5 → TC-047
- **相关FR**: FR-030（统一响应格式）、FR-009（速率限制）

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 从同一 IP 地址向 `/api/v1/auth/login` 发送 **10 次** POST 请求（任意凭据），每次间隔适当时间 | 前 10 次请求均正常处理，返回 `200` 或 `401` |
| 2 | 从同一 IP 地址发送第 **11 次** POST 请求至 `/api/v1/auth/login` | 返回 `429 Too Many Requests` |
| 3 | 检查 429 响应体 `success` 字段 | `success: false` |
| 4 | 检查 429 响应体 `error.code` 字段 | `"RATE_LIMITED"` |
| 5 | 检查 429 响应体 `error.message` 字段 | `"请求过于频繁，请稍后重试"` |
| 6 | 检查 429 响应是否包含 `Retry-After` Header | 存在 `Retry-After` 头，指示何时可再次请求 |
| 7 | 等待 60 秒后，再次从同一 IP 发送请求 | 请求恢复正常，返回 `200` 或 `401`（速率限制已重置） |

---

## 错误代码汇总表（FR-030）

| 错误代码 | HTTP 状态码 | 说明 |
|----------|-------------|------|
| `INVALID_CREDENTIALS` | 401 | 用户名或密码错误 |
| `ACCOUNT_LOCKED` | 423 | 账号连续失败 5 次后临时锁定（15分钟） |
| `RATE_LIMITED` | 429 | IP 速率限制：每分钟超过 10 次请求 |
| `INVALID_TOKEN` | 401 | Token 过期、格式错误、被重用或已黑名单化 |
| `UNAUTHORIZED` | 401 | 未提供有效认证信息 |
| `VALIDATION_ERROR` | 422 | 请求体未通过 Pydantic 验证 |
