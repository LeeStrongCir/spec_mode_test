---
description: "测试任务清单 - 注册登录"
---

# 测试任务: 注册登录

**输入**：来自 `/specs/001-register-login/` 的设计文档
**前置条件**：`plan.md`（必需）、`spec.md`（必需，用于测试场景）

**组织**：测试分为四个阶段：阶段1：测试用例编写 → 阶段2：测试自动化代码编写 → 阶段3：测试环境准备 → 阶段4：测试执行。阶段间**严格串行**，但阶段1、2、4**内部任务可并行 `[P]`**。

## 格式: `[ID] [P?] [LABEL] Description`

- **[P]**: 可并行执行（不同文件、无依赖关系，阶段内部可同时执行）
- **[LABEL]**: 阶段标签前缀
  - `[CASE-SC-01]`, `[CASE-SC-02]` — 阶段 1 测试用例编写（按场景）
  - `[AUTO-SC-01]`, `[AUTO-SC-02]` — 阶段 2 测试自动化代码编写（按场景）
  - `[ENV]` — 阶段 3 测试环境准备
  - `[EVT-SC-01]`, `[EVT-SC-02]` — 阶段 4 测试执行（按场景）
- 描述中必须包含准确的文件路径

---

## 阶段 1: 测试用例编写（内部可并行 `[P]`）

**说明**：不同场景的测试用例编写可并行执行，但需等待本阶段全部完成后，阶段2才能开始。共 5 个场景 + 6 个边缘场景。场景编号对应 `specs/001-register-login/spec.md` 中的用户故事：

| 场景编号 | 用户故事 | 优先级 | 覆盖 TC |
|----------|----------|--------|---------|
| SC-01 | 注册新账户 | P1 | TC-001 至 TC-008 |
| SC-02 | 输入凭据完成登录 | P1 | TC-010 至 TC-014 |
| SC-03 | 处理登录失败 | P1 | TC-020 至 TC-022 |
| SC-04 | 退出登录 | P2 | TC-030 至 TC-031 |
| SC-05 | API 登录与登出 | P2 | TC-040 至 TC-047 |

边缘场景映射：
- EC-001（Cookie过期）→ 归属 SC-02
- EC-002（CSRF无效）→ 归属 SC-02
- EC-003（XSS/SQL注入）→ 归属 SC-01
- EC-004（网络断连）→ 归属 SC-01
- EC-005（API统一响应）→ 归属 SC-05
- EC-006（审计日志）→ 归属 SC-05

### 阶段 1.1: SC-01 用例编写 —— 注册新账户（P1）

**目标**：编写注册功能的完整手工测试步骤，覆盖 8 个 TC 和 2 个边缘场景

- [X] T001 [P] [CASE-SC-01] 编写 SC-01 手工测试步骤：注册页面 UI 元素、字段校验、重复用户名拦截、密码一致性/强度校验、合法注册+自动登录+重定向、跳转至登录页、已认证用户重定向保护，输出文件 `leecloud_platform_tests/test-cases/001-register-login/TC-001-to-TC-008-register.md`
- [X] T002 [P] [CASE-SC-01] 定义 SC-01 边缘场景预期输出：XSS/SQL 注入输入清洗（EC-003）、网络断连注册行为（EC-004），追加至 `leecloud_platform_tests/test-cases/001-register-login/EC-003-xss-injection.md` 和 `leecloud_platform_tests/test-cases/001-register-login/EC-004-network-disconnect.md`
- [X] T003 [P] [CASE-SC-01] 定义 SC-01 前置条件与数据准备步骤：未注册用户名、合法密码组合（8-32位含字母+数字+特殊字符）、有效邮箱格式，追加至 `leecloud_platform_tests/test-cases/001-register-login/TC-001-to-TC-008-register.md`

### 阶段 1.2: SC-02 用例编写 —— 输入凭据完成登录（P1）

**目标**：编写登录功能的完整手工测试步骤，覆盖 5 个 TC 和 2 个边缘场景

- [X] T004 [P] [CASE-SC-02] 编写 SC-02 手工测试步骤：登录页面 UI 元素、空值校验、正确凭据登录、记住我持久化登录、已认证用户重定向保护，输出文件 `leecloud_platform_tests/test-cases/001-register-login/TC-010-to-TC-014-login.md`
- [X] T005 [P] [CASE-SC-02] 定义 SC-02 边缘场景预期输出：JWT Cookie 过期后自动重定向（EC-001）、CSRF Token 缺失/无效返回 403（EC-002），追加至 `leecloud_platform_tests/test-cases/001-register-login/EC-001-cookie-expired.md` 和 `leecloud_platform_tests/test-cases/001-register-login/EC-002-csrf-invalid.md`
- [X] T006 [P] [CASE-SC-02] 定义 SC-02 前置条件与数据准备步骤：已注册用户账户（用户名+密码）、Cookie 属性（HttpOnly/Secure/SameSite=Strict）验证点，追加至 `leecloud_platform_tests/test-cases/001-register-login/TC-010-to-TC-014-login.md`

### 阶段 1.3: SC-03 用例编写 —— 处理登录失败（P1）

**目标**：编写登录失败场景的手工测试步骤，覆盖 3 个 TC

- [X] T007 [P] [CASE-SC-03] 编写 SC-03 手工测试步骤：不存在用户名错误凭据、存在用户名错误密码、连续 5 次失败后账号锁定，输出文件 `leecloud_platform_tests/test-cases/001-register-login/TC-020-to-TC-022-login-failure.md`
- [X] T008 [P] [CASE-SC-03] 定义 SC-03 前置条件与数据准备步骤：已存在用户账户用于错误凭据测试、锁定计数器状态验证方法，追加至 `leecloud_platform_tests/test-cases/001-register-login/TC-020-to-TC-022-login-failure.md`

### 阶段 1.4: SC-04 用例编写 —— 退出登录（P2）

**目标**：编写退出登录场景的手工测试步骤，覆盖 2 个 TC

- [X] T009 [P] [CASE-SC-04] 编写 SC-04 手工测试步骤：正常退出登录清除 Cookie 并重定向、退出后防止浏览器后退绕过，输出文件 `leecloud_platform_tests/test-cases/001-register-login/TC-030-to-TC-031-logout.md`
- [X] T010 [P] [CASE-SC-04] 定义 SC-04 前置条件与数据准备步骤：已登录状态（持有有效 JWT Cookie）、Cookie 清除后状态验证方法，追加至 `leecloud_platform_tests/test-cases/001-register-login/TC-030-to-TC-031-logout.md`

### 阶段 1.5: SC-05 用例编写 —— API 登录与登出（P2）

**目标**：编写 API 认证场景的手工测试步骤，覆盖 8 个 TC 和 2 个边缘场景

- [X] T011 [P] [CASE-SC-05] 编写 SC-05 手工测试步骤：API 登录正确/错误凭据、账号锁定、Token 续签有效/过期 refresh_token、登出 Token 黑名单化、无认证凭据访问、API IP 速率限制，输出文件 `leecloud_platform_tests/test-cases/001-register-login/TC-040-to-TC-047-api-auth.md`
- [X] T012 [P] [CASE-SC-05] 定义 SC-05 边缘场景预期输出：统一 API 响应格式（EC-005）、审计日志记录（EC-006），追加至 `leecloud_platform_tests/test-cases/001-register-login/EC-005-api-response-format.md` 和 `leecloud_platform_tests/test-cases/001-register-login/EC-006-audit-log.md`
- [X] T013 [P] [CASE-SC-05] 定义 SC-05 前置条件与数据准备步骤：API 端点基地址 `/api/v1/auth/*`、JWT Token 结构字段（用户ID/用户名/角色/签发/过期时间）、refresh_token 单次使用标志，追加至 `leecloud_platform_tests/test-cases/001-register-login/TC-040-to-TC-047-api-auth.md`

**检查点**：阶段 1 所有测试用例编写完成——阶段 2 测试自动化代码编写可以开始

---

## 阶段 2: 测试自动化代码编写（内部可并行 `[P]`）

**说明**：不同场景的自动化代码编写可并行执行，但需等待阶段1全部完成后才能开始。

### 阶段 2.1: SC-01 自动化代码 —— 注册功能

- [X] T014 [P] [AUTO-SC-01] 编写注册页面表单组件集成测试（TC-001 至 TC-008），使用 Vitest + Testing Library + MSW，输出文件 `leecloud_platform_tests/integration/frontend/components/RegisterPanel.test.tsx`，MSW handler 追加至 `leecloud_platform_tests/integration/frontend/mocks/handlers/register.ts`
- [X] T015 [P] [AUTO-SC-01] 编写后端注册 API 集成测试（FR-014 至 FR-021），使用 pytest + httpx + 内存 SQLite，输出文件 `leecloud_platform_tests/integration/backend/test_api/test_register.py`，包含用户名唯一性校验、密码强度校验、邮箱格式校验、注册成功自动登录 + Cookie 签发
- [X] T016 [P] [AUTO-SC-01] 编写 XSS/SQL 注入防护测试（EC-003），在后端 `leecloud_platform_tests/integration/backend/test_api/test_register.py` 中追加测试函数覆盖特殊输入清洗逻辑
- [X] T017 [P] [AUTO-SC-01] 编写注册页已认证用户重定向保护测试（TC-008），在前端组件和后端路由中均覆盖

### 阶段 2.2: SC-02 自动化代码 —— 登录功能

- [X] T018 [P] [AUTO-SC-02] 编写登录页面表单组件集成测试（TC-010 至 TC-014），使用 Vitest + Testing Library + MSW，输出文件 `leecloud_platform_tests/integration/frontend/components/LoginPanel.test.tsx`
- [X] T019 [P] [AUTO-SC-02] 编写认证状态流转 Hook 测试（登录/退出状态变化），输出文件 `leecloud_platform_tests/integration/frontend/hooks/useAuth.test.ts`
- [X] T020 [P] [AUTO-SC-02] 编写后端登录 API 集成测试（FR-001 至 FR-013），使用 pytest + httpx，输出文件 `leecloud_platform_tests/integration/backend/test_api/test_auth.py`，覆盖凭据验证、Cookie 签发（HttpOnly/Secure/SameSite）、重定向逻辑、记住我持久化、受保护路由 JWT 校验
- [X] T021 [P] [AUTO-SC-02] 编写 JWT 中间件集成测试（FR-009），输出文件 `leecloud_platform_tests/integration/backend/test_api/test_auth_middleware.py`，覆盖未持有有效 Cookie 时重定向至登录页
- [X] T022 [P] [AUTO-SC-02] 编写 CSRF 防护集成测试（FR-010, FR-020, EC-002），输出文件 `leecloud_platform_tests/integration/backend/test_api/test_csrf.py`，覆盖缺失/无效 CSRF Token 返回 403
- [X] T023 [P] [AUTO-SC-02] 编写 IP 速率限制集成测试（FR-011, EC-003），输出文件 `leecloud_platform_tests/integration/backend/test_api/test_rate_limit.py`，使用 fakeredis 模拟 Redis，覆盖 1 分钟内超过 10 次请求返回 429
- [X] T024 [P] [AUTO-SC-02] 编写请求/响应 Schema 边界值测试（密码长度、邮箱格式、Token 字段完整性），输出文件 `leecloud_platform_tests/integration/backend/test_schemas/test_auth_schemas.py`

### 阶段 2.3: SC-03 自动化代码 —— 登录失败

- [X] T025 [P] [AUTO-SC-03] 编写登录失败后端集成测试（TC-020 至 TC-022），追加至 `leecloud_platform_tests/integration/backend/test_api/test_auth.py`，覆盖不存在用户名返回通用错误提示、存在用户名错误密码返回通用错误提示、连续 5 次失败锁定 15 分钟
- [X] T026 [P] [AUTO-SC-03] 编写登录失败前端组件测试（错误提示展示、用户名框保留、密码框清空），追加至 `leecloud_platform_tests/integration/frontend/components/LoginPanel.test.tsx`

### 阶段 2.4: SC-04 自动化代码 —— 退出登录

- [X] T027 [P] [AUTO-SC-04] 编写退出登录 Hook 状态测试（Token 清除、状态重置），追加至 `leecloud_platform_tests/integration/frontend/hooks/useAuth.test.ts`
- [X] T028 [P] [AUTO-SC-04] 编写退出登录后端集成测试（Cookie 清除 + 重定向 + 审计日志 FR-007, FR-013），追加至 `leecloud_platform_tests/integration/backend/test_api/test_auth.py`

### 阶段 2.5: SC-05 自动化代码 —— API 认证

- [X] T029 [P] [AUTO-SC-05] 编写 API Service 层集成测试（请求构造 + 响应解析），使用 Vitest + MSW，输出文件 `leecloud_platform_tests/integration/frontend/services/api.test.ts`，MSW handlers 追加至 `leecloud_platform_tests/integration/frontend/mocks/handlers/auth.ts`
- [X] T030 [P] [AUTO-SC-05] 编写后端 API 认证端点集成测试（FR-022 至 FR-030），追加至 `leecloud_platform_tests/integration/backend/test_api/test_auth.py`，覆盖：
  - `POST /api/v1/auth/login` 正确/错误凭据响应
  - `POST /api/v1/auth/refresh` 有效/过期 refresh_token 续费
  - `POST /api/v1/auth/logout` Token 黑名单化
  - 无认证凭据访问返回 401
  - API 统一 JSON 响应格式验证
  - 审计日志记录验证
- [X] T031 [P] [AUTO-SC-05] 编写 API 速率限制测试（FR-025），追加至 `leecloud_platform_tests/integration/backend/test_api/test_rate_limit.py`
- [X] T032 [P] [AUTO-SC-05] 编写 API 登录锁定策略测试（FR-024），追加至 `leecloud_platform_tests/integration/backend/test_api/test_auth.py`

### 阶段 2.6: 端到端测试脚本编写

- [X] T033 [P] [E2E] 编写 Playwright E2E 测试脚本，覆盖完整用户旅程（注册→自动登录→退出→Cookie 过期→已认证重定向），输出文件 `leecloud_platform_tests/e2e/auth.spec.ts`
- [X] T034 [P] [E2E] 编写 E2E Page Object 封装，输出文件 `leecloud_platform_tests/e2e/pages/login.page.ts`、`leecloud_platform_tests/e2e/pages/register.page.ts`、`leecloud_platform_tests/e2e/pages/console.page.ts`

**检查点**：阶段 2 所有自动化代码编写完成——阶段 3 测试环境准备可以开始

---

## 阶段 3: 测试环境准备（阶段间串行，内部任务也串行）

**目的**：克隆项目制品、部署应用、测试基础设施初始化与环境搭建，为测试执行阶段提供基础

**⚠️ 关键**：此阶段内部各项环境准备工作必须严格按顺序完成，且在此阶段整体完成之前，任何测试执行任务不得开始

- [ ] T035 [ENV] 将项目制品克隆至 WSL 原生文件系统，执行 `cd /tmp && git clone https://github.com/LeeStrongCir/spec_mode_dev.git`，确认 `leecloud_platform/` 目录存在
- [ ] T036 [ENV] 安装后端测试依赖：`cd /tmp/spec_mode_dev/leecloud_platform && pip install pytest pytest-asyncio httpx pytest-mock fakeredis freezegun`，确认 pytest 8+ / httpx 0.27+ / fakeredis 可用
- [ ] T037 [ENV] 安装前端测试依赖：`cd /tmp/spec_mode_dev/leecloud_platform && npm install --save-dev vitest @testing-library/react @testing-library/user-event msw playwright`，确认 Vitest 2+ / MSW 2+ / Playwright 1.45+ 可用
- [ ] T038 [ENV] 安装 Playwright Chromium 浏览器：`npx playwright install chromium`，确认浏览器可启动
- [ ] T039 [ENV] 配置测试环境变量：创建 `.env.test` 文件，设置 `DATABASE_URL=sqlite:///file::memory:?cache=shared`、`JWT_SECRET=test-secret-key`、`JWT_EXPIRATION_HOURS=24`、`CSRF_SECRET=test-csrf-secret`、`RATE_LIMIT_ENABLED=true`
- [ ] T040 [ENV] 启动前后端开发服务器：`playwright.config.ts` 中 `webServer` 配置自动启动 Vite（前端 http://localhost:5173）和 Uvicorn（后端 http://localhost:8000），执行 `npx playwright test --list` 验证连接
- [ ] T041 [ENV] 创建 E2E 共享登录态：执行预置脚本生成 `leecloud_platform_tests/e2e/.auth/storageState.json`（包含已登录用户的 Cookie 和 localStorage），用于 `storageState` 复用

**检查点**：基础设施就绪——阶段 4 测试执行可以开始

---

## 阶段 4: 测试执行（内部可并行 `[P]`）

**目的**：执行全部自动化测试用例，收集结果，验证功能是否符合规格

**说明**：本阶段所有任务均可并行执行，但需等待阶段1、2、3全部完成后才能开始

### 阶段 4.1: P1 场景执行（MVP 范围）

- [ ] T042 [P] [EVT-SC-01] 执行注册功能后端集成测试 `test_register.py`，记录结果
- [ ] T043 [P] [EVT-SC-01] 执行注册功能前端组件集成测试 `RegisterPanel.test.tsx`，记录结果
- [ ] T044 [P] [EVT-SC-02] 执行登录功能后端集成测试 `test_auth.py`（FR-001 至 FR-013），记录结果
- [ ] T045 [P] [EVT-SC-02] 执行登录功能前端组件集成测试 `LoginPanel.test.tsx`，记录结果
- [ ] T046 [P] [EVT-SC-03] 执行登录失败场景后端集成测试 `test_auth.py`（TC-020 至 TC-022），记录结果
- [ ] T047 [P] [EVT-SC-02] 执行认证中间件集成测试（`test_auth_middleware.py`、`test_csrf.py`、`test_rate_limit.py`），记录结果
- [ ] T048 [P] [EVT-SC-01] 执行注册/登录 Schema 边界值测试 `test_auth_schemas.py`，记录结果

### 阶段 4.2: P2 场景执行

- [ ] T049 [P] [EVT-SC-04] 执行退出登录 Hook + 后端集成测试（`useAuth.test.ts` + `test_auth.py` 登出部分），记录结果
- [ ] T050 [P] [EVT-SC-05] 执行 API 认证后端集成测试 `test_auth.py`（FR-022 至 FR-030），记录结果
- [ ] T051 [P] [EVT-SC-05] 执行 API Service 前端集成测试 `api.test.ts`，记录结果
- [ ] T052 [P] [EVT-SC-05] 执行 API 速率限制集成测试 `test_rate_limit.py`（API 部分），记录结果

### 阶段 4.3: 端到端测试执行

- [ ] T053 [P] [EVT-E2E] 执行 Playwright 端到端完整用户旅程测试 `auth.spec.ts`（注册→登录→退出→Cookie 过期→已认证重定向），记录结果

### 阶段 4.4: 回归与报告

- [ ] T054 [P] [EVT-REGRESSION] 所有用例通过后执行回归验证，运行完整测试套件确认无破坏，输出测试总结报告 `leecloud_platform_tests/reports/001-register-login-summary.md`
- [ ] T055 [P] [EVT-REGRESSION] 对失败用例逐一分析，生成测试事件报告（Test Incident Report），输出至 `leecloud_platform_tests/reports/001-register-login-incidents.md`

**检查点**：所有测试用例执行完成

---

## 依赖关系

```
阶段 1: [P] CASE-SC-01 (T001-T003) ─┐
       [P] CASE-SC-02 (T004-T006) ──┤
       [P] CASE-SC-03 (T007-T008) ──┤
       [P] CASE-SC-04 (T009-T010) ──┤
       [P] CASE-SC-05 (T011-T013) ──┘
                   ↓ (全部完成)
阶段 2: [P] AUTO-SC-01 (T014-T017) ─┐
       [P] AUTO-SC-02 (T018-T024) ──┤
       [P] AUTO-SC-03 (T025-T026) ──┤
       [P] AUTO-SC-04 (T027-T028) ──┤
       [P] AUTO-SC-05 (T029-T032) ──┤
       [P] E2E (T033-T034) ─────────┘
                   ↓ (全部完成)
阶段 3: ENV (T035 → T036 → T037 → T038 → T039 → T040 → T041) (严格串行)
                   ↓ (全部完成)
阶段 4: [P] EVT-SC-01 (T042-T043) ─┐
       [P] EVT-SC-02 (T044-T045) ──┤
       [P] EVT-SC-03 (T046) ───────┤
       [P] EVT-SC-04 (T049) ───────┤
       [P] EVT-SC-05 (T050-T052) ──┤
       [P] EVT-E2E (T053) ─────────┤
       [P] EVT-REGRESSION (T054-T055) ┘
```

---

## 并行示例：阶段 4 测试执行

```bash
# 同时启动 P1 场景后端集成测试:
Task: "Execute leecloud_platform_tests/integration/backend/test_api/test_register.py"
Task: "Execute leecloud_platform_tests/integration/backend/test_api/test_auth.py (FR-001 to FR-013)"
Task: "Execute leecloud_platform_tests/integration/backend/test_api/test_auth_middleware.py"
Task: "Execute leecloud_platform_tests/integration/backend/test_api/test_csrf.py"
Task: "Execute leecloud_platform_tests/integration/backend/test_api/test_rate_limit.py"

# 同时启动 P1 场景前端集成测试:
Task: "Execute leecloud_platform_tests/integration/frontend/components/RegisterPanel.test.tsx"
Task: "Execute leecloud_platform_tests/integration/frontend/components/LoginPanel.test.tsx"

# 同时启动 P2 场景与 E2E:
Task: "Execute leecloud_platform_tests/integration/frontend/hooks/useAuth.test.ts"
Task: "Execute leecloud_platform_tests/integration/frontend/services/api.test.ts"
Task: "Execute leecloud_platform_tests/e2e/auth.spec.ts"

# 每个用例独立执行，结果汇总至 leecloud_platformTests/reports/001-register-login-summary.md
```

---

## 执行策略

### MVP First（仅执行 P1 场景）

1. 完成 阶段 1: P1 场景（SC-01 注册、SC-02 登录、SC-03 登录失败）的测试用例编写
2. 完成 阶段 2: P1 场景的自动化代码编写（后端集成 + 前端组件集成）
3. 完成 阶段 3: 测试环境准备
4. 执行 阶段 4: P1 场景的测试执行（T042-T048）
5. **停止并验证**：独立验证 P1 场景的 16 个 TC（TC-001 至 TC-022）+ 6 个 EC 中相关的 4 个
6. 若通过，输出阶段性报告 `leecloud_platform_tests/reports/001-register-login-mvp.md`

### 增量覆盖

1. 阶段 3 环境准备 → 基础设施就绪
2. P1 场景执行通过 → 输出 MVP 报告
3. 继续 P2 场景（SC-04 退出、SC-05 API）的用例自动化（T027-T032）执行（T049-T052）
4. 执行 E2E 端到端完整用户旅程（T053）
5. 回归验证（T054-T055），确保新增场景不破坏已验证的 P1 场景
6. 每个场景增加覆盖范围且不破坏已验证的场景

### 独立验证标准

| 场景 | 独立验证标准 |
|------|-------------|
| SC-01 注册 | 新用户名+密码+邮箱可成功创建账户，自动签发 JWT Cookie 并重定向至 `/console`；重复用户名/弱密码/邮箱格式错误被准确拦截 |
| SC-02 登录 | 正确凭据可在 2 秒内完成认证并重定向；"记住我"30天持久化；已认证用户访问登录页自动重定向 |
| SC-03 登录失败 | 错误凭据返回通用提示不泄露用户名存在；连续 5 次失败锁定 15 分钟 |
| SC-04 退出 | Cookie 清除 + 重定向至登录页 + 退出成功提示；后退按钮无法绕过 |
| SC-05 API | API 登录/续签/登出端点正确返回/拒绝请求；Token 黑名单立即生效；速率限制 429 触发 |

---

## 备注

- `[P]` 任务 = 不同文件、无依赖关系，阶段内部可并行执行
- 阶段标签（`[ENV]`, `[CASE-SC-*]`, `[AUTO-SC-*]`, `[EVT-SC-*]`）将任务映射至具体阶段和测试场景以实现可追溯性
- **阶段间严格串行**：阶段1：测试用例编写 → 阶段2：测试自动化代码编写 → 阶段3：测试环境准备 → 阶段4：测试执行
- **阶段内可并行**：阶段1：测试用例编写、阶段2：测试自动化代码编写、阶段4：测试执行 — 内部标记 `[P]` 的任务可同时执行
- 执行前确认前置条件与测试数据就绪
- 每个任务或逻辑组执行后记录结果
- 避免：模糊任务、文件冲突、破坏执行顺序的跨阶段依赖
