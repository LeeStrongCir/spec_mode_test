# 测试计划: 注册登录

> **版本**: `001-register-login`
> **创建日期**: 2026-05-13
> **输入**: 功能测试规格文件 `specs/001-register-login/spec.md`

> **说明**：本模板由 `/speckit-test.plan` 命令填充。测试计划是连接"测试规格说明"与"测试任务分解"的桥梁，定义测试策略、环境、范围和风险。

## 摘要

本测试计划覆盖 Lee 云平台 v1 注册登录功能的完整测试方案，基于 `specs/001-register-login/spec.md` 中定义的 5 个用户故事、25 个测试用例和 6 个边缘场景。测试分为两个层次：**后端集成测试**（FastAPI + pytest + httpx，验证 API 路由 → Service → DB 全链）、**前端集成测试**（React + Vitest + Testing Library + MSW，验证组件交互与状态流转）以及 **端到端测试**（Playwright，验证完整用户旅程）。包含 12 条功能需求（FR-001 至 FR-030）、安全机制（CSRF、XSS 防护、IP 速率限制、登录失败锁定）及 API 认证接口（登录/续签/登出）的验证。

## 技术上下文

**测试框架**:
- 后端集成：pytest 8+ + pytest-asyncio 0.24+ + httpx 0.27+
- 前端集成：Vitest 2+ + @testing-library/react 16+ + @testing-library/user-event 14+ + MSW 2+
- 端到端：Playwright 1.45+

**测试数据库**: SQLite 内存模式 `sqlite:///file::memory:?cache=shared`，每次测试通过 pytest fixture 重建 schema

**浏览器自动化**: Playwright chromium（webServer 配置自动启动 Vite + Uvicorn）

**Mock 策略**:
- 后端外部调用：pytest-mock（mocker.patch）
- 前端 API 请求：MSW handlers 拦截网络层
- 密码哈希：真实 BCrypt 算法（确定性，无外部依赖）
- 时间控制：freezegun 冻结时间（用于 Cookie 过期、锁定窗口等场景）

## 宪章门禁

*门禁：必须在测试实现前通过。测试设计后需重新检查。*

- [x] **规格优先**：`specs/001-register-login/spec.md` 已存在并通过质量检查清单验证（spec.md 25 个 TC + 6 个 EC，所有验收场景可执行）
- [x] **可追溯性**：每个 FR（FR-001 至 FR-030）已映射到对应测试用例（见 spec.md），每个正向场景有负向对照（spec.md TC-012 ↔ TC-020/021，TC-006 ↔ TC-002/003/004/005）
- [x] **技术栈约束**：严格使用宪章定义的工具（pytest + httpx 后端集成，Vitest + MSW 前端集成，Playwright E2E），未引入替代方案
- [x] **目录规范**：所有测试产物将置于 `leecloud_platform_tests/` 统一根目录下，遵循宪章第四章结构
- [x] **前端定位规范**：前端测试优先使用 `getByTestId`，遵循 `[功能模块]-[元素类型]` kebab-case 格式

## 测试策略总览

### 测试层次

本功能包含以下测试层次：

| 层级 | 职责 | 覆盖指引 | 失败定位 |
|------|------|----------|----------|
| **后端集成测试** | API 契约验证（Route → Service → Model → DB） | 覆盖全部 30 条功能需求，边界值分析 + 等价类划分 | 定位到组件交互边界（路由/Service/Model） |
| **前端组件集成测试** | 组件交互 + 表单提交状态流转 | 覆盖 5 个用户故事的 UI 交互流程 | 定位到组件级（LoginPanel/RegisterPanel/AuthHook） |
| **前端 API Service 集成测试** | Axios 请求构造 + 响应处理 | 覆盖 API 端点请求/响应契约 | 定位到 Service 层（请求函数/错误转换） |
| **端到端测试** | 完整用户旅程（注册→登录→退出） | 仅覆盖 P1 核心路径，6-10 条用例 | 定位到用户操作级别 |

### 分层边界规则

- **后端集成测试**：使用真实 FastAPI app + 真实 SQLAlchemy model + 真实 SQLite 内存库，**不** mock 框架层，但**可** mock 外部服务（邮件发送、Redis 速率限制）
- **前端组件集成测试**：使用真实 React 组件渲染 + MSW 拦截 API 请求，**不** mock 组件内部逻辑
- **端到端测试**：真实浏览器 + 完整应用栈（Vite + FastAPI），仅 mock 不可控外部依赖。**不复测**集成测试已覆盖的 API 契约

## 各层测试详细计划

### 后端集成测试

**目标**：验证认证相关 API 路由（登录/注册/续签/登出）的请求处理、Service 层逻辑、DB 状态变更及响应格式

| 集成点 | 测试文件 | 验证范围 |
|--------|----------|----------|
| [Auth Route → Auth Service → User Model → DB] | `leecloud_platform_tests/integration/backend/test_api/test_auth.py` | FR-001 至 FR-013, FR-022 至 FR-030（登录/登出/API 端点） |
| [Register Route → User Service → User Model → DB] | `leecloud_platform_tests/integration/backend/test_api/test_register.py` | FR-014 至 FR-021（注册流程） |
| [中间件 → JWT Auth → Route] | `leecloud_platform_tests/integration/backend/test_api/test_auth_middleware.py` | FR-009, FR-029（受保护路由的 JWT 校验） |
| [速率限制中间件 → Auth Route] | `leecloud_platform_tests/integration/backend/test_api/test_rate_limit.py` | FR-011, FR-025（IP 速率限制） |
| [CSRF 中间件 → Auth Route] | `leecloud_platform_tests/integration/backend/test_api/test_csrf.py` | FR-010, FR-020（CSRF Token 校验） |
| [Schema 校验] | `leecloud_platform_tests/integration/backend/test_schemas/test_auth_schemas.py` | 请求/响应体边界值（密码长度、邮箱格式、Token 字段完整性） |

#### Mock 策略

| 依赖类型 | 处理方式 | 理由 |
|----------|----------|------|
| 外部 API/服务 | `pytest-mock` (`mocker.patch`) | 避免网络不确定性，仅测本功能逻辑 |
| 密码哈希 | 直接调用真实 BCrypt | 确定性算法，无外部依赖，不应 mock |
| JWT 签发 | mock 或固定 secret | 签发逻辑不在被测范围内时使用，但 Cookie 属性验证需真实签发 |
| Redis/速率限制 | `fakeredis` + `pytest-mock` | 避免真实 Redis 依赖，使用内存 Redis mock |
| 时间 | `freezegun` 冻结时间 | Cookie 过期、锁定窗口等时间相关逻辑需要确定性 |
| 审计日志 | `mocker.patch` 异步写入 | 验证日志调用参数，不验证实际写入 |

#### 测试数据隔离

- **Fixture 作用域**: 每个测试使用独立的内存 SQLite 数据库，通过 `pytest.fixture(scope="function")` 保证
- **数据工厂**: 使用自定义 builder 模式（`create_user(username=..., password=..., email=...)`）创建测试数据
- **事务回滚**: 每个测试在独立事务中执行，测试完成后自动回滚清理数据

### 前端组件集成测试

**目标**：验证注册/登录页面组件的 UI 渲染、表单验证、用户交互状态流转及 API 调用触发

| 组件 | 测试文件 | 验证范围 |
|------|----------|----------|
| LoginPanel | `leecloud_platform_tests/integration/frontend/components/LoginPanel.test.tsx` | TC-010, TC-011, TC-012, TC-020, TC-021, TC-022（登录表单交互） |
| RegisterPanel | `leecloud_platform_tests/integration/frontend/components/RegisterPanel.test.tsx` | TC-001, TC-002, TC-003, TC-004, TC-005, TC-006, TC-007, TC-008（注册表单交互） |
| Auth Hook | `leecloud_platform_tests/integration/frontend/hooks/useAuth.test.ts` | 登录/注册/登出状态流转，Token 存储与清除 |
| API Service | `leecloud_platform_tests/integration/frontend/services/api.test.ts` | FR-022, FR-026, FR-028（API 请求构造与响应解析） |

#### MSW Mock 策略

| Handler 文件 | 覆盖端点 |
|-------------|----------|
| `leecloud_platform_tests/integration/frontend/mocks/handlers/auth.ts` | `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout` |
| `leecloud_platform_tests/integration/frontend/mocks/handlers/register.ts` | Web 注册表单提交 |

### 端到端测试

**目标**：验证从用户操作到最终页面状态的完整用户旅程，覆盖 P1 核心路径

| 场景 | 测试文件 | 路径 | 预期结果 |
|------|----------|------|----------|
| 新账户注册到控制台访问 | `leecloud_platform_tests/e2e/auth.spec.ts` | 访问 `/auth/register` → 填写表单 → 注册 → 重定向至 `/console` | 用户成功创建并自动登录 |
| 正常登录流程 | `leecloud_platform_tests/e2e/auth.spec.ts` | 访问 `/auth/login` → 输入凭据 → 登录 → 重定向至 `/console` | Cookie 签发成功，控制台可访问 |
| 登录失败 + 错误提示 | `leecloud_platform_tests/e2e/auth.spec.ts` | 输入错误凭据 → 登录 → 查看错误提示 → 密码框清空 | 通用错误提示，不泄露用户存在信息 |
| 退出登录流程 | `leecloud_platform_tests/e2e/auth.spec.ts` | 控制台 → 点击退出 → 重定向至 `/auth/login` | Cookie 清除，显示退出成功提示 |
| 已认证用户访问登录页重定向 | `leecloud_platform_tests/e2e/auth.spec.ts` | 持有 Cookie 访问 `/auth/login` → 自动重定向至 `/console` | 不被允许停留在登录页 |
| Cookie 过期保护 | `leecloud_platform_tests/e2e/auth.spec.ts` | 过期 Cookie 访问 `/console/*` → 重定向至 `/auth/login` | 显示会话过期提示 |

#### Playwright 策略

- **页面交互**: 优先使用 `getByTestId()` 定位元素，data-testid 遵循 `[功能模块]-[元素类型]` kebab-case 格式
- **状态验证**: 验证 URL 变化、页面内容、Cookie 属性、网络请求
- **等待策略**: 使用 Playwright 自动等待，避免硬编码 sleep
- **storageState**: 使用 `storageState` 复用已登录态，避免在 E2E 中重复执行登录流程

#### 端到端测试范围约束

- 端到端测试 **不复测** 集成测试已验证的接口契约和边界条件
- 端到端测试 仅覆盖「用户操作 → 系统响应」的完整路径
- 每条 E2E 测试用例对应 spec.md 中的一个 P1 级别用户故事或关键验收场景

## 测试基础设施

### Fixture 设计

```python
# leecloud_platform_tests/integration/backend/conftest.py 中的关键 fixture

import pytest
from httpx import AsyncClient, ASGITransport
from freezegun import freeze_time

@pytest.fixture
async def db_session():
    """每个测试独立的内存 SQLite 会话"""
    async_engine = create_async_engine("sqlite:///file::memory:?cache=shared")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(async_engine)
    async with async_session() as session:
        yield session
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def test_user(db_session):
    """使用 factory 创建标准用户"""
    user = UserFactory(username="testuser", email="test@example.com", password="Test@1234")
    db_session.add(user)
    await db_session.flush()
    return user

@pytest.fixture
async def app():
    """FastAPI 应用实例"""
    return create_app()

@pytest.fixture
async def client(app, db_session):
    """HTTPX 异步测试客户端"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def frozen_time():
    """freezegun 冻结时间，用于测试 Cookie 过期/锁定窗口"""
    with freeze_time("2026-05-13T10:00:00") as frozen:
        yield frozen
```

### 并行执行策略

- 后端集成测试使用 pytest-xdist 并行执行（每个 worker 独立的内存 DB）
- 前端集成测试（Vitest）并行执行，MSW server 共享
- E2E 测试（Playwright）串行执行或有限并行（避免浏览器实例冲突）

## 项目结构

### 文档结构（本特性）

```text
specs/001-register-login/
├── plan.md              # 本文件（由 /speckit-test.plan 命令输出）
├── research.md          # 阶段 0 输出（技术调研）
├── spec.md              # 测试规格说明
└── tasks.md             # 测试执行任务分解（由 /speckit-test.tasks 命令生成）
```

### 测试工件结构（仓库根目录）

```text
leecloud_platform_tests/
├── test-cases/
│   └── 001-register-login/
│       ├── TC-001-register-page-ui.md
│       ├── TC-012-login-valid.md
│       ├── TC-020-login-invalid-username.md
│       ├── TC-API-040-api-login.md
│       ├── EC-001-cookie-expired.md
│       └── EC-002-csrf-invalid.md
│
├── integration/
│   ├── backend/
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   │   ├── __init__.py
│   │   │   ├── test_auth.py           # 登录/登出 API 集成
│   │   │   ├── test_register.py        # 注册 API 集成
│   │   │   ├── test_auth_middleware.py # JWT 中间件校验
│   │   │   ├── test_rate_limit.py      # 速率限制
│   │   │   └── test_csrf.py            # CSRF 保护
│   │   └── test_schemas/
│   │       ├── __init__.py
│   │       └── test_auth_schemas.py    # 请求/响应体边界值校验
│   └── frontend/
│       ├── setup.ts
│       ├── test-utils.tsx
│       ├── mocks/
│       │   ├── handlers.ts
│       │   ├── handlers/
│       │   │   ├── auth.ts
│       │   │   └── register.ts
│       │   └── server.ts
│       ├── components/
│       │   ├── LoginPanel.test.tsx
│       │   └── RegisterPanel.test.tsx
│       ├── hooks/
│       │   └── useAuth.test.ts
│       └── services/
│           └── api.test.ts
│
├── e2e/
│   ├── auth.spec.ts
│   └── pages/
│       ├── login.page.ts
│       ├── register.page.ts
│       └── console.page.ts
│
├── pytest.ini
├── vitest.config.ts
└── playwright.config.ts
```

## 测试环境

### 环境要求

| 组件 | 要求 | 备注 |
|------|------|------|
| 执行机（后端） | Python 3.11+, pytest, httpx, fakeredis, freezegun, pytest-mock, pytest-asyncio | 本地开发环境 |
| 执行机（前端） | Node.js 18+, npm/pnpm, Vitest, Testing Library, MSW | 本地开发环境 |
| 执行机（E2E） | Playwright chromium 浏览器 | E2E 需要真实浏览器实例 |

### 环境变量配置

```bash
# 测试环境
DATABASE_URL=sqlite:///file::memory:?cache=shared
JWT_SECRET=test-secret-key
JWT_EXPIRATION_HOURS=24
CSRF_SECRET=test-csrf-secret
RATE_LIMIT_ENABLED=true
```

### 测试配置文件

| 文件 | 用途 |
|------|------|
| `leecloud_platform_tests/pytest.ini` | pytest 配置（标记、并行、覆盖率） |
| `leecloud_platform_tests/vitest.config.ts` | Vitest 配置（MSW 集成、globals） |
| `leecloud_platform_tests/playwright.config.ts` | Playwright E2E 配置（webServer、baseURL） |

### 测试数据准备

| 数据类型 | 来源 | 刷新频率 | 清理策略 |
|----------|------|----------|----------|
| 基准测试数据 | UserFactory / 自定义 builder | 每次测试运行前 | 事务回滚自动清理 |
| 用户测试账号池 | 测试内动态创建 | 按需自动创建 | 测试结束后自动删除 |
| E2E 登录态 | Playwright storageState 复用 | E2E 测试套件执行前预置 | 测试套件结束后清除 |
| MSW Mock 响应数据 | handlers.ts / handlers/auth.ts / handlers/register.ts | 按需自动创建 | 测试结束后自动删除 |

## 测试可追溯性

### FR → Test 映射

| Spec 中的 FR | 测试层级 | 测试文件 | 测试用例 |
|--------------|----------|----------|----------|
| FR-001（登录页UI） | 组件集成 + 端到端 | `LoginPanel.test.tsx`, `auth.spec.ts` | TC-010, TC-011 |
| FR-002（凭据验证+签发） | 后端集成 + 组件集成 | `test_auth.py`, `LoginPanel.test.tsx` | TC-012 |
| FR-003（重定向至控制台） | 端到端 | `auth.spec.ts` | TC-012 |
| FR-004（空值拦截） | 组件集成 | `LoginPanel.test.tsx` | TC-011 |
| FR-005（通用错误提示） | 后端集成 + 组件集成 | `test_auth.py`, `LoginPanel.test.tsx` | TC-020, TC-021 |
| FR-006（锁定策略） | 后端集成 + 端到端 | `test_auth.py`, `auth.spec.ts` | TC-022 |
| FR-007（退出重定向） | 端到端 + 组件集成 | `auth.spec.ts`, `useAuth.test.ts` | TC-030, TC-031 |
| FR-008（记住我持久化） | 后端集成 + 端到端 | `test_auth.py`, `auth.spec.ts` | TC-013 |
| FR-009（受保护路由校验） | 后端集成 + 端到端 | `test_auth_middleware.py`, `auth.spec.ts` | EC-001 |
| FR-010（CSRF校验） | 后端集成 | `test_csrf.py` | EC-002 |
| FR-011（IP速率限制） | 后端集成 + 端到端 | `test_rate_limit.py`, `auth.spec.ts` | TC-047 |
| FR-012（已认证拦截登录页） | 端到端 + 组件集成 | `auth.spec.ts`, `LoginPanel.test.tsx` | TC-014 |
| FR-013（审计日志） | 后端集成 | `test_auth.py` | EC-006 |
| FR-014（注册页UI） | 组件集成 + 端到端 | `RegisterPanel.test.tsx`, `auth.spec.ts` | TC-001 |
| FR-015（用户名唯一性） | 后端集成 + 组件集成 | `test_register.py`, `RegisterPanel.test.tsx` | TC-003 |
| FR-016（密码强度校验） | 组件集成 + 后端集成 | `RegisterPanel.test.tsx`, `test_register.py` | TC-005 |
| FR-017（密码一致性） | 组件集成 | `RegisterPanel.test.tsx` | TC-004 |
| FR-018（邮箱格式） | 组件集成 | `RegisterPanel.test.tsx` | TC-002 |
| FR-019（注册后自动登录） | 端到端 | `auth.spec.ts` | TC-006 |
| FR-020（注册CSRF校验） | 后端集成 | `test_csrf.py` | EC-002 |
| FR-021（已认证拦截注册页） | 端到端 | `auth.spec.ts` | TC-008 |
| FR-022（API登录） | 后端集成 + API Service | `test_auth.py`, `api.test.ts` | TC-040 |
| FR-023（API错误凭据） | 后端集成 | `test_auth.py` | TC-041 |
| FR-024（API锁定策略） | 后端集成 | `test_auth.py` | TC-042 |
| FR-025（API速率限制） | 后端集成 | `test_rate_limit.py` | TC-047 |
| FR-026（API续签） | 后端集成 + API Service | `test_auth.py`, `api.test.ts` | TC-043, TC-044 |
| FR-027（API续签校验） | 后端集成 | `test_auth.py` | TC-044 |
| FR-028（API登出） | 后端集成 + API Service | `test_auth.py`, `api.test.ts` | TC-045 |
| FR-029（API鉴权强制） | 后端集成 | `test_auth_middleware.py` | TC-046 |
| FR-030（API统一响应） | 后端集成 + API Service | `test_auth.py`, `api.test.ts` | EC-005 |

### 用户故事 → Test 映射

| 用户故事 | 优先级 | 对应测试 | 独立验证方式 |
|------------|--------|----------|--------------|
| 注册新账户 | P1 | `RegisterPanel.test.tsx`, `test_register.py`, `auth.spec.ts` | 新用户名+密码+邮箱提交注册，验证账户创建、Cookie签发、重定向 |
| 输入凭据完成登录 | P1 | `LoginPanel.test.tsx`, `test_auth.py`, `auth.spec.ts` | 正确凭据登录，验证 Cookie 签发、重定向 |
| 处理登录失败 | P1 | `LoginPanel.test.tsx`, `test_auth.py`, `auth.spec.ts` | 错误凭据登录，验证通用错误提示、账号锁定 |
| 退出登录 | P2 | `useAuth.test.ts`, `auth.spec.ts` | 已登录状态退出，验证 Cookie 清除、重定向 |
| API 登录与登出 | P2 | `test_auth.py`, `api.test.ts` | 直接调用 API 端点，验证 Token 返回、续签、黑名单 |

## 测试风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| JWT Cookie 时间相关逻辑不确定性 | 测试依赖真实时间导致结果不稳定 | 使用 freezegun 冻结时间，确保所有时间逻辑确定性 |
| Redis 速率限制依赖 | 集成测试需要真实 Redis 启动 | 使用 fakeredis 内存 Redis，避免外部依赖 |
| CSRF Token 跨请求传递 | 需要先获取 CSRF Token 再提交 | 集成测试中先 GET 页面获取 CSRF Token，再 POST 提交 |
| 前端 MSW handler 与真实 API 不一致 | Mock 响应可能与实际后端不同步 | MSW handler 基于真实 API 响应格式定义，定期与实际 API 对比 |
| E2E 测试依赖前后端同时启动 | 环境配置复杂可能导致启动失败 | Playwright webServer 配置自动启动，失败时提供详细日志 |
| 并发测试间数据库状态污染 | 共享内存 DB 导致测试相互影响 | pytest-xdist 使用独立 SQLite 文件/内存实例 per worker |

## 复杂度追踪

> 本次测试计划无违反宪章门禁项——所有测试层级、工具选型和目录结构均严格遵循宪章定义。
