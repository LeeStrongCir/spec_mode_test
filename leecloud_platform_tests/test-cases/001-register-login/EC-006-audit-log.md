# 边缘用例：EC-006 — 登录/登出操作审计日志

> **源规格**: `specs/001-register-login/spec.md`
> **相关功能需求**: FR-022（API登录）、FR-028（API登出）
> **优先级**: P2
> **测试类型**: 边缘情况/安全审计测试
> **创建日期**: 2026-05-13
> **可追溯性**: 审计日志记录要求（安全合规）

---

## 数据准备

| 数据项 | 值 | 备注 |
|--------|------|------|
| API 端点基地址 | `/api/v1/auth/*` | 认证相关 API 统一前缀 |
| 登录端点 | `POST /api/v1/auth/login` | API 登录接口 |
| 登出端点 | `POST /api/v1/auth/logout` | API 登出接口 |
| 已存在用户名 | `audituser` | 系统中已注册的有效账户 |
| 已存在密码 | `Audit@1234` | 符合强度要求 |
| 审计日志存储位置 | 数据库 `audit_log` 表或等效日志系统 | 记录所有认证操作 |
| 审计日志必填字段 | `timestamp`, `action`, `username`, `source_ip`, `user_agent`, `result` | 每次操作必须记录 |

---

## EC-006.1: 登录成功 — 审计日志记录

- **优先级**: P2
- **相关FR**: FR-022

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 发送 `POST /api/v1/auth/login` 使用有效凭据（用户名: audituser, 密码正确） | 登录成功，返回 200 OK |
| 2 | 查询审计日志系统，查找最近一条 `action=login` 的记录 | 存在对应日志条目 |
| 3 | 检查日志 `timestamp` 字段 | 时间戳在合理范围内，与请求发送时间的误差不超过 1 秒 |
| 4 | 检查日志 `action` 字段 | 值为 `"login"` |
| 5 | 检查日志 `username` 字段 | 值为 `"audituser"` |
| 6 | 检查日志 `source_ip` 字段 | 值与请求来源 IP 地址一致（或 X-Forwarded-For 中的真实 IP） |
| 7 | 检查日志 `user_agent` 字段 | 记录了请求的 User-Agent 字符串 |
| 8 | 检查日志 `result` 字段 | 值为 `"success"` |

---

## EC-006.2: 登录失败 — 审计日志记录（含失败原因分类）

- **优先级**: P2
- **相关FR**: FR-024（认证失败处理）

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 发送 `POST /api/v1/auth/login` 使用有效用户名、错误密码 | 返回 401 INVALID_CREDENTIALS |
| 2 | 查询审计日志，查找最近一条 `action=login` 的记录 | 存在对应日志条目 |
| 3 | 检查日志 `result` 字段 | 值为 `"failure"` |
| 4 | 检查日志 `failure_reason` 字段（如有） | 值为 `"invalid_password"` 或等效分类（用于内部审计，不暴露给 API 响应） |
| 5 | 检查日志 `username` 字段 | 值为尝试登录的用户名（即使是**不存在的用户名**） |
| 6 | 发送 `POST /api/v1/auth/login` 使用**不存在的用户名** | 返回 401 INVALID_CREDENTIALS（通用错误） |
| 7 | 查询审计日志 | 同样记录了失败日志，`username` 为尝试使用的用户名，`result` 为 `"failure"`，`failure_reason` 为 `"user_not_found"` 或等效分类 |
| 8 | 验证**内部审计日志**与**外部 API 响应**的差异 | 外部响应返回通用错误（防枚举），内部日志记录具体失败原因（便于安全分析） |

---

## EC-006.3: 账号锁定 — 审计日志记录

- **优先级**: P2
- **相关FR**: FR-025（账号锁定机制）

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 连续 5 次使用错误密码登录同一账号 | 第 5 次失败后，账号进入锁定状态 |
| 2 | 查询审计日志，查找连续失败记录 | 存在 5 条连续的 `result="failure"` 日志，对应同一 username 和时间窗口 |
| 3 | 第 6 次尝试登录（仍错误） | 返回 423 ACCOUNT_LOCKED |
| 4 | 查询审计日志 | 存在一条 `action=login`, `result="locked"` 的日志条目 |
| 5 | 检查日志是否记录了锁定触发条件 | 包含关联信息，如连续失败次数（5次）、锁定开始时间、预期解锁时间（+15分钟） |

---

## EC-006.4: Token 刷新 — 审计日志记录

- **优先级**: P2
- **相关FR**: FR-026（Token刷新）

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 先正常登录获取 valid refresh_token | 获得凭据 |
| 2 | 发送 `POST /api/v1/auth/refresh` 使用有效的 refresh_token | 刷新成功，返回 200 OK |
| 3 | 查询审计日志，查找最近一条 `action=token_refresh` 的记录 | 存在对应日志条目 |
| 4 | 检查日志 `action` 字段 | 值为 `"token_refresh"` |
| 5 | 检查日志 `result` 字段 | 值为 `"success"` |
| 6 | 发送 `POST /api/v1/auth/refresh` 使用已失效的 refresh_token | 返回 401 INVALID_TOKEN |
| 7 | 查询审计日志 | 存在 `action=token_refresh`, `result="failure"`, `failure_reason="invalid_or_reused_token"` 的日志 |

---

## EC-006.5: API 登出 — 审计日志记录

- **优先级**: P2
- **相关FR**: FR-028（API登出）、FR-029（Token黑名单）

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 使用有效 access_token 发送 `POST /api/v1/auth/logout` | 登出成功，返回 200 OK |
| 2 | 查询审计日志，查找最近一条 `action=logout` 的记录 | 存在对应日志条目 |
| 3 | 检查日志 `action` 字段 | 值为 `"logout"` |
| 4 | 检查日志 `result` 字段 | 值为 `"success"` |
| 5 | 使用**已过期/无效**的 token 发送 logout 请求 | 返回 401 UNAUTHORIZED |
| 6 | 查询审计日志 | 存在 `action=logout`, `result="failure"`, `failure_reason="invalid_token"` 的日志 |

---

## EC-006.6: 审计日志 — 安全合规性验证

- **优先级**: P2
- **相关FR**: FR-022, FR-028

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 完成一系列认证操作（登录成功、登录失败、刷新、登出） | 操作正常完成 |
| 2 | 检查审计日志中是否记录了任何**敏感信息**（如密码明文、token 值、密码哈希） | **不应**记录密码、完整 JWT token、或其他敏感凭据信息 |
| 3 | 检查日志中 `username` 字段 | 记录了用户名用于身份追溯 |
| 4 | 验证日志不可篡改性 | 日志存储在受保护的存储中，无法通过 API 端点修改或删除 |
| 5 | 检查日志时间戳格式 | 使用 UTC 时间戳，格式一致（如 ISO 8601: `2026-05-13T10:30:00Z`） |
| 6 | 验证高并发场景下日志完整性 | 同时发送多个请求（5-10），所有请求均在日志中有对应记录，无丢失或乱序 |
