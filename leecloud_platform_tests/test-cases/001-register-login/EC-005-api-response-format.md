# 边缘用例：EC-005 — 统一 API 响应格式

> **源规格**: `specs/001-register-login/spec.md`
> **相关功能需求**: FR-030（统一API响应格式）
> **优先级**: P2
> **测试类型**: 边缘情况/契约测试
> **创建日期**: 2026-05-13
> **可追溯性**: API 契约 `specs/001-register-login/contracts/auth_api.md` → Common Response Format

---

## 数据准备

| 数据项 | 值 | 备注 |
|--------|------|------|
| API 端点基地址 | `/api/v1/auth/*` | 认证相关 API 统一前缀 |
| 统一响应 Schema | `{ "success": boolean, "data": object\|null, "error": { "code": string, "message": string }\|null }` | 三个顶层字段，遵循互斥规则 |
| 成功响应规则 | `success=true`, `data` 存在（可为对象或null）, `error=null` | data 与 error 互斥 |
| 错误响应规则 | `success=false`, `data=null`, `error` 存在（含 code + message） | data 与 error 互斥 |
| 额外字段约束 | 响应体中**不应**出现 schema 未定义的额外顶层字段 | 防止数据泄露 |

---

## EC-005.1: 成功响应 — 标准三字段结构

- **优先级**: P2
- **相关FR**: FR-030

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 发送 `POST /api/v1/auth/login` 使用有效凭据 | 登录成功，返回 200 OK |
| 2 | 解析响应体 JSON | JSON 格式正确，Content-Type 为 `application/json` |
| 3 | 检查顶层字段 | **仅含三个字段**: `success`, `data`, `error`，无额外顶层字段 |
| 4 | 检查 `success` 字段类型与值 | 类型为 `boolean`，值为 `true` |
| 5 | 检查 `data` 字段 | 包含完整的登录成功数据（`access_token`, `refresh_token`, `expires_in`, `user`） |
| 6 | 检查 `error` 字段 | 值为 `null` |
| 7 | 验证 `success=true` 与 `error=null` 的互斥性 | 当 success=true 时，error 必须为 null，不能有任何错误信息 |

---

## EC-005.2: 错误响应 — 标准三字段结构

- **优先级**: P2
- **相关FR**: FR-030

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 发送 `POST /api/v1/auth/login` 使用无效凭据 | 认证失败，返回 401 |
| 2 | 解析响应体 JSON | JSON 格式正确 |
| 3 | 检查顶层字段 | **仅含三个字段**: `success`, `data`, `error` |
| 4 | 检查 `success` 字段 | 类型为 `boolean`，值为 `false` |
| 5 | 检查 `data` 字段 | 值为 `null` |
| 6 | 检查 `error` 字段 | 为对象，包含 `code`（字符串）和 `message`（字符串）两个必填字段 |
| 7 | 验证 `success=false` 与 `data=null` 的互斥性 | 当 success=false 时，data 必须为 null，不能包含任何有效数据 |

---

## EC-005.3: 验证错误响应 — 包含 details 扩展字段

- **优先级**: P2
- **相关FR**: FR-030

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 发送 `POST /api/v1/auth/login` 使用空请求体 `{}` | 缺少必填字段 |
| 2 | 检查 HTTP 状态码 | 返回 `422 Unprocessable Content` |
| 3 | 检查响应体 `error` 结构 | 包含 `code: "VALIDATION_ERROR"`, `message`, 以及 `details` 扩展字段 |
| 4 | 检查 `details` 字段 | 为数组类型，每个元素包含 `field`（字符串）和 `message`（字符串） |
| 5 | 验证 `details` 与核心 schema 兼容性 | `details` 是 `error` 对象的扩展属性，不影响 `success`/`data`/`error` 三字段核心结构 |

---

## EC-005.4: 边界情况 — 空值/null 处理一致性

- **优先级**: P2
- **相关FR**: FR-030

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 执行 API 登出（`POST /api/v1/auth/logout`），携带有效 Authorization Header | 登出成功 |
| 2 | 检查成功响应中 `data` 字段 | 值为 `null`（而非空对象 `{}` 或空字符串 `""`） |
| 3 | 检查成功响应中 `error` 字段 | 值为 `null` |
| 4 | 执行带无效凭据的登录请求 | 认证失败 |
| 5 | 检查错误响应中 `data` 字段 | 值为 `null`（而非空对象 `{}` 或空字符串 `""`） |
| 6 | 验证所有 null 字段在 JSON 中以字面量 `null` 序列化 | 不是字符串 `"null"`，不是空字符串 `""`，不是 `undefined`，也不是字段被省略缺失 |
| 7 | 跨所有端点验证一致性 | 登录成功、登录失败、刷新成功、刷新失败、登出成功 —— 所有响应的 null 处理方式一致 |

---

## EC-005.5: 非 JSON 请求体错误处理

- **优先级**: P2
- **相关FR**: FR-030

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 发送 `POST /api/v1/auth/login`，Headers: `Content-Type: text/plain`，Body: `not json` | 请求体无法解析为 JSON |
| 2 | 检查 HTTP 状态码 | 返回 `422` 或 `400`（取决于框架实现） |
| 3 | 检查响应体 | **仍须遵循**统一响应格式：`{"success": false, "data": null, "error": {"code": "...", "message": "..."}}` |
| 4 | 验证即使服务端内部异常，对外响应也遵循统一格式 | 不会出现裸 HTML 错误页或纯文本错误堆栈 |
