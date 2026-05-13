# 研究记录: 注册登录

> **日期**: 2026-05-13
> **来源**: 宪章约束 + 规格定义 + 行业最佳实践

---

## 决策: 后端集成测试框架 — pytest + httpx AsyncClient

**决策**: 使用 pytest + pytest-asyncio + httpx AsyncClient 进行后端 API 集成测试。

**理由**: 宪章第 3.1 节明确规定此技术栈。httpx AsyncClient 可直接向 FastAPI 子应用发送真实 HTTP 请求，验证路由 → Service → Model 全链路，无需启动真实 HTTP 服务器。

**考虑的替代方案**:
- Flask test_client：不适用于 FastAPI
- requests + 启动 uvicorn 子进程：启动成本高、响应慢
- SQLAlchemy session 直接调用：跳过路由层，无法验证 HTTP 契约

---

## 决策: 前端集成测试 — Vitest + Testing Library + MSW

**决策**: 使用 Vitest 运行前端组件集成测试，MSW 拦截 API 请求，Testing Library 模拟用户交互。

**理由**: 宪章第 3.1 节规定。MSW 可在网络层拦截请求，与 Axios 拦截器共存，handler 可复用至开发环境。

**考虑的替代方案**:
- Jest + nock：nock 仅拦截 Node.js HTTP 模块，不适用于浏览器 fetch/Axios
- Cypress 组件测试：重量级，E2E 工具用于组件集成测试过度

---

## 决策: 端到端测试 — Playwright + storageState + webServer

**决策**: Playwright chromium 浏览器，通过 webServer 配置自动启动 Vite + Uvicorn，使用 storageState 复用登录态。

**理由**: 宪章第 3.2 节规定。E2E 测试数量控制在 10-20 条，仅覆盖核心用户旅程。

**考虑的替代方案**:
- Selenium Grid：配置复杂、执行慢
- Cypress：不支持多标签页和 iframe 场景

---

## 决策: 测试数据库 — SQLite 内存模式

**决策**: 后端集成测试使用 `sqlite:///file::memory:?cache=shared` 内存数据库。

**理由**: 宪章明确规定。每次测试通过 pytest fixture 重建 schema，确保数据隔离。

**考虑的替代方案**:
- PostgreSQL test containers：重量级、启动成本高，不适合快速开发迭代
- 共享测试数据库：并发执行时状态污染

---

## 决策: 速率限制 Mock — fakeredis

**决策**: 使用 fakeredis 模拟 Redis 行为，进行速率限制和锁定逻辑测试。

**理由**: 避免集成测试依赖真实 Redis 服务。fakeredis 提供了 Redis 命令的纯内存实现，行为与真实 Redis 一致。

**考虑的替代方案**:
- 真实 Redis Docker 容器：增加 CI/CD 复杂度
- 完全 mock Redis 调用：无法验证速率限制算法正确性

---

## 决策: E2E 测试目录结构 — 按特性文件命名

**决策**: E2E 测试文件 `auth.spec.ts` 对应 `specs/001-register-login/` 特性。

**理由**: 宪章第 4 章规定 E2E 采用扁平结构，文件级按特性命名。本特性文件名为 `auth.spec.ts` 以匹配认证领域。

**考虑的替代方案**:
- E2E 按特性分目录：宪章明确扁平结构
