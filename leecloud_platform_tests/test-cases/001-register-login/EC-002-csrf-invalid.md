# 边缘用例：EC-002 — CSRF Token 缺失/无效

> **源规格**: `specs/001-register-login/spec.md`
> **相关功能需求**: FR-001 ~ FR-012
> **优先级**: P1
> **测试类型**: 安全测试 — CSRF 防护
> **创建日期**: 2026-05-13
> **可追溯性**: spec.md → 边缘情况与异常测试 → EC-002
> **严重程度**: 高

---

## 数据准备

| 数据项 | 值 | 备注 |
|--------|------|------|
| 已存在用户名 | `testuser` | 系统中已注册的有效账户 |
| 已存在密码 | `Test@1234` | 符合强度要求 |
| CSRF Token 字段名 | `csrf_token` | 登录/注册表单中的 CSRF Token 字段 |
| 登录端点 | `POST /auth/login` | 登录表单提交路径 |

---

## 前置条件

- 系统已启动并正常运行
- 用户已知晓 CSRF Token 的签发与验证机制
- 准备 HTTP 请求工具（如 curl、Postman）可用于构造自定义请求

---

## 测试场景：CSRF Token 缺失

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 访问 `/auth/login` 获取页面及初始 CSRF Token（Cookie 或表单隐藏字段） | CSRF Token 被签发 |
| 2 | 构造登录请求，提交用户名 `testuser` 和密码 `Test@1234`，但**不携带 CSRF Token** | 请求发送至服务器 |
| 3 | 检查响应状态码 | 返回 `403 Forbidden` |
| 4 | 检查响应体 | 包含拒绝访问的错误说明 |

---

## 测试场景：CSRF Token 无效/伪造

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 访问 `/auth/login` 获取合法的 CSRF Token | CSRF Token 被正确签发 |
| 2 | 构造登录请求，提交用户名 `testuser` 和密码 `Test@1234`，但携带**伪造的 CSRF Token**（如 `csrf_token=invalid_token_value`） | 请求发送至服务器 |
| 3 | 检查响应状态码 | 返回 `403 Forbidden` |
| 4 | 检查响应体 | 包含 CSRF 验证失败，拒绝登录 |
| 5 | 确认用户未被认证，未签发 JWT Cookie | 无 `access_token` Cookie 被创建 |

---

## 验收标准

- [ ] 缺失 CSRF Token 的登录请求返回 403，不执行认证
- [ ] 伪造/篡改 CSRF Token 的登录请求返回 403，不执行认证
- [ ] 403 响应不包含敏感信息泄露
- [ ] 合法 CSRF Token + 正确凭据的登录请求正常通过

---
