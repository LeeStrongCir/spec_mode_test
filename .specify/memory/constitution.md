# Lee云平台 测试宪章

<!-- 面向 spec-kit 项目的测试优先章程。
     每条规格均可执行。每条需求均可验证测试。 -->

## 核心原则

### 一、规格优先，测试贯穿

每个规格制品（规格、契约、需求）必须具有对应的测试制品。没有可执行的规格证明功能正常，任何特性不得发布。没有测试的规格是不完整的；没有规格对应的测试是孤立的。

**测试层级与命名**：测试按层级划分职责，确保规格到测试的精确映射：

| 层级 | 制品格式 | 覆盖目标 |
|---|---|---|
| **集成测试** | 模块/服务之间的契约测试，前端组件→API 交互链 | 100% 接口契约覆盖 |
| **端到端测试** | 完整用户旅程与业务场景测试 | 100% 核心业务场景覆盖 |

所有测试标识符遵循模式 `[LEVEL]P-[SEQ]-[ITERATION]`（如 `ITP-001-A`），其中 `LEVEL` = I/E 分别代表集成/端到端测试，`SEQ` = 3 位序号，`ITERATION` = 字母后缀用于派生用例。

**通用约束**：
- 测试框架必须支持并行执行
- 集成测试中所有外部依赖必须使用 mock/stub
- 测试数据必须隔离（测试之间无共享可变状态）
- 每个 PR 合并前必须运行完整集成测试套件；禁止手动绕过测试门禁

### 二、可追溯性（不可协商）

所有测试制品必须在以下层级保持双向可追溯性：

- **架构设计 → 集成测试**：验证模块间契约与数据流转
- **用户故事 → 端到端测试**：验证端到端业务场景与核心链路

未经验证的设计元素不得发布。任何测试必须有可追溯的来源。正向测试与负向测试必须成对追溯——每个正向场景至少追溯到一个负向对照。

### 三、测试技术栈约束

本项目为**后端 FastAPI 服务器 + 前端 React Web 应用**的 Monorepo 架构。测试技术栈按**测试领域**划分，每个领域选择与项目技术栈深度适配的工具，不得引入冗余或偏离技术栈的方案。

#### 3.1 集成测试

集成测试验证模块间契约与数据流转，使用真实框架并 mock 外部依赖。

| 适用层 | 工具 | 版本 | 说明 |
|---|---|---|---|
| **后端 API 集成** | **pytest** + **pytest-asyncio** + **httpx** | pytest 8+, asyncio 0.24+, httpx 0.27+ | pytest 为执行框架，httpx AsyncClient 发送真实 HTTP 请求到 FastAPI 子应用，验证路由→service→model 全链 |
| **后端 Mock** | **pytest-mock** | 最新 | `mocker.patch` 隔离外部调用 |
| **前端组件集成** | **Vitest** + **@testing-library/react** + **@testing-library/user-event** | Vitest 2+, RTL 16+, user-event 14+ | 模拟真实用户交互，验证组件渲染、交互逻辑与状态流转 |
| **前端 API Mock** | **MSW (Mock Service Worker)** | 2+ | 网络层拦截，与 Axios 拦截器共存，handler 可复用至开发环境 |

**集成测试约束**：
- 后端 SQLite 使用内存模式：`sqlite:///file::memory:?cache=shared` 或 `sqlite:///:memory:`，每次测试通过 pytest fixture 重建 schema
- 后端外部调用须使用 `pytest-mock` 隔离，禁止修改被测源码
- 前端 MSW handler 定义于 `tests/integration/frontend/mocks/handlers.ts`，按模块分组（auth/user/instance 等）
- 前端集成测试覆盖组件交互流程与状态流转，使用 MSW 拦截 API 请求
- 集成测试中所有外部依赖必须使用 mock/stub，测试数据必须隔离（测试之间无共享可变状态）

**接口设计技术**（ISO 29119-4）：

| 设计视图 | 必用技术 |
|---|---|
| 接口视图 | 接口契约测试 |
| 数据设计视图 | 边界值分析 + 等价类划分 |
| 依赖视图 | 故障注入 + 负向测试 |

#### 3.2 端到端测试 (E2E)

E2E 测试验证完整的用户旅程与跨前后端的业务场景。

| 工具 | 版本 | 说明 |
|---|---|---|
| **Playwright** | 1.45+ | `webServer` 配置自动启动 Vite + FastAPI，内建截图/录屏/trace |

**E2E 测试约束**：
- 通过 Playwright `webServer` 配置同时启动前端 Vite DevServer 和后端 Uvicorn
- 使用 `storageState` 复用已登录态，避免重复执行登录流程
- E2E 测试数量控制在 10-20 条，仅覆盖核心用户旅程（登录→操作→结果）
- 定位元素优先使用 `data-testid`，禁止依赖 Ant Design 内部 class
- Playwright 配置文件中定义 `baseURL`，前端和后端 URL 通过环境变量注入

**负向测试要求**：每个正向测试必须至少有一个对应的负向测试，覆盖：无效输入类型和边界越界、缺少必需参数、服务/依赖故障（故障注入）、权限/授权边界场景、超时和限流场景。

### 四、测试结构与目录规范

本项目采用**统一 `leecloud_platform_tests/` 根目录**组织全部测试产物，按测试类型集中管理：

1. **测试用例** —— `leecloud_platform_tests/test-cases/{NNN-feature}/` 存放从规格派生的手工文本用例
2. **集成测试** —— `leecloud_platform_tests/integration/` 下按技术层分组（不按特性分割），共享基础设施
3. **端到端测试** —— `leecloud_platform_tests/e2e/` 扁平结构验证完整系统行为，文件级按特性命名

```
./ (仓库根目录)
└── leecloud_platform_tests/
     ├── test-cases/                           # 手工/文本测试用例（从 spec.md TC-xxx 派生）
     │   ├── 001-auth/                         # 特性 001：认证，与 specs/001-auth/ 对应
     │   │   ├── TC-001-login-valid.md         # 正常凭证登录
     │   │   ├── TC-002-login-invalid.md       # 无效凭证登录（负向）
     │   │   └── TC-API-001-auth-contract.md   # 认证 API 契约验证
     │   └── 002-user-mgmt/                    # 特性 002：用户管理，与 specs/002-user-mgmt/ 对应
     │       ├── TC-001-create-user.md
     │       ├── TC-002-delete-user.md
     │       └── EC-001-concurrent-deletion.md # 边界/异常场景
     │
     ├── integration/                          # 集成测试集中目录（按技术层，不按特性）
     │   ├── backend/                          # 后端集成测试
     │   │   ├── conftest.py                   # 全局 fixture：app 实例、httpx client、内存 DB
     │   │   ├── test_api/                     # API 层集成测试，按路由模块分组
     │   │   │   ├── __init__.py
     │   │   │   └── test_auth.py              # 认证路由契约：请求→service→model→响应
     │   │   ├── test_services/                # service 层集成（含 DB 交互）
     │   │   │   ├── __init__.py
     │   │   │   └── test_user_service.py
     │   │   └── test_schemas/                 # schema 校验测试（边界值、等价类）
     │   │       ├── __init__.py
     │   │       └── test_user_schemas.py
     │   └── frontend/                         # 前端集成测试
     │       ├── setup.ts                      # Vitest 全局 setup（Testing Library 扩展）
     │       ├── test-utils.tsx                # 自定义 render（ConfigProvider 包裹）
     │       ├── mocks/
     │       │   ├── handlers.ts               # MSW request handlers（按模块分组）
     │       │   ├── server.ts                 # MSW Node setup（Vitest 用）
     │       │   └── browser.ts                # MSW browser setup（E2E 用）
     │       ├── components/                   # 组件集成测试（交互与状态流转）
     │       │   └── LoginPanel.test.tsx       # 登录面板：输入→提交→状态反馈
     │       ├── hooks/                        # hook 集成测试（状态流转）
     │       │   └── useAuth.test.ts           # 认证 hook：登录/登出状态流转
     │       └── services/                     # API service 集成测试（MSW + 请求构造与响应处理）
     │           └── api.test.ts               # Axios 请求函数：请求参数构造与响应解析
     ├── e2e/                                  # Playwright 端到端测试（扁平结构，不按特性分目录）
     │   ├── auth.spec.ts                      # 登录/注册端到端流程
     │   ├── user-management.spec.ts           # 用户管理核心场景
     │   ├── pages/                            # Page Object 模式封装
     │   │   ├── login.page.ts                 # 登录页：元素定位 + 操作封装
     │   │   └── dashboard.page.ts             # 控制台页：元素定位 + 操作封装
     │   └── test-ids/                         # data-testid 常量映射表
     │       ├── login-test-ids.ts             # 登录流程 TestId 定义
     │       └── dashboard-test-ids.ts         # 控制台 TestId 定义
     │
     ├── pytest.ini                                # pytest 配置
     ├── vitest.config.ts                          # Vitest 配置
     └── playwright.config.ts                      # Playwright E2E 配置
```

**目录设计原则**：

| 层级 | 放置位置 | 适用测试类型 | 设计理由 |
|---|---|---|---|
| **测试用例层** | `leecloud_platform_tests/test-cases/{NNN-feature}/` | 手工文本用例（TC-xxx / EC-xxx） | 与 `specs/{NNN-feature}/` 一一对应，特性级管理、独立评审、可追溯 |
| **集成层** | `leecloud_platform_tests/integration/backend/` | API 集成、service 集成、schema 校验 | pytest conftest 统一 fixture，按技术层分组保持内聚性 |
| | `leecloud_platform_tests/integration/frontend/` | 组件集成、hook 集成、API service 集成 | MSW mocks、Vitest setup 集中管理，测试文件按类型分组 |
| **E2E 层** | `leecloud_platform_tests/e2e/` | Playwright E2E | 独立于前后端生命周期，数量控制在 10-20 条，扁平结构足够清晰 |

**追溯规则**：
- 文本用例通过目录与 specs 镜像对应（`leecloud_platform_tests/test-cases/001-auth/TC-001-*.md` ↔ `specs/001-auth/spec.md#TC-001`），正向 ↔ 负向在文件内以 `Related:` 字段标注
- 自动化代码通过文件头部注释追溯至 TC 编号及 spec.md，如 `# Spec: specs/001-auth/spec.md → TC-001, TC-002`；pytest 可配合 `@pytest.mark.feature("auth")` 按特性筛选
- E2E 通过文件名与 TC 编号对应（`auth.spec.ts` ↔ `specs/001-auth/spec.md`）

**测试文件命名约定**：
- **文本用例文件**：`TC-{序号}-{简述}.md`（如 `TC-001-login-valid.md`）、`EC-{序号}-{简述}.md`（如 `EC-001-concurrent-deletion.md`），目录名 `{NNN-feature}` 与 `specs/` 下特性目录编号一致
- **后端 pytest 文件**：`test_<module>.py`，snake_case，如 `test_auth.py`
- **后端 pytest 测试函数**：`test_<功能描述>`，snake_case，如 `test_login_valid_credentials_returns_200`
- **前端 Vitest 文件**：`<ComponentName>.test.tsx`，PascalCase 组件名 + `.test.tsx`
- **E2E 测试文件**：`<feature>.spec.ts`，kebab-case 功能名，如 `auth-flow.spec.ts`
- **Page Object 文件**：`<page-name>.page.ts`，如 `login.page.ts`
- **TestId 映射文件**：`<page-name>-test-ids.ts`，如 `login-test-ids.ts`

### 五、前端测试与 data-testid 定位强制规范

本章节为 data-testid 规范的测试侧执行要求。所有可交互元素须按 `[功能模块]-[元素类型]` 的 kebab-case 格式添加 `data-testid` 属性。

#### 5.1 data-testid 在测试中的使用

所有前端测试（集成测试 + Playwright E2E 测试）**必须**优先使用 `data-testid` 定位元素，不得依赖 CSS class、DOM 结构或 Ant Design 内部 class 名。

**选择器优先级（强制执行）**：
1. `getByTestId()` → `data-testid` 属性，最高优先级
2. `getByRole()` → 语义化 role + name 组合
3. `getByLabelText()` → 表单 label 关联
4. `getByText()` → 仅在无语义元素且无 `data-testid` 时的最后手段

禁止使用：
- CSS 选择器定位（如 `.ant-btn-primary`、`.ant-input`）
- XPath
- Ant Design 内部 class 名（如 `.ant-modal-body`）
- DOM 层级路径（如 `div > div > button`）

#### 5.2 测试用例与 data-testid 映射

每个核心 UI 流程（登录、注册、主机管理等）须建立独立的 **测试标识映射表**，放置于 `tests/e2e/test-ids/` 目录：

```typescript
// 示例：tests/e2e/test-ids/login-test-ids.ts
export const LoginTestIds = {
  // 表单元素
  usernameInput: 'username-input',
  passwordInput: 'password-input',
  loginButton: 'login-button',
  registerLink: 'register-link',
  // 验证状态
  usernameError: 'username-error',
  passwordError: 'password-error',
  loadingSpinner: 'login-loading',
  // 结果状态
  successToast: 'login-success',
  failureToast: 'login-failure',
} as const;
```

**要求**：
- 每个 Page Object 或组件测试须导入对应的 TestId 常量对象
- TestId 常量对象的键名使用 PascalCase，值严格对应 JSX 中 `data-testid` 属性值（kebab-case）
- 新增 `data-testid` 时，须同步更新对应 TestId 常量对象
- E2E Page Object 中所有 `getByTestId()` / `locator()` 调用必须引用 TestId 常量，禁止硬编码字符串

#### 5.3 前端测试覆盖要求

| 测试类型 | 覆盖范围 | 最低要求 |
|---|---|---|
| **组件集成测试** (Vitest + Testing Library + userEvent) | 组件交互、表单提交与状态反馈 | 每个公开组件至少 1 个交互流程测试（输入→操作→结果反馈） |
| **Hook 集成测试** (Vitest + MSW) | 自定义 hooks/ 的状态流转与事件处理 | 每个 hook 至少覆盖正常路径 + 异常路径 |
| **API Service 集成测试** (Vitest + MSW) | Axios 请求构造、响应处理、错误转换 | 每个 API 函数至少 1 个成功 + 1 个失败场景 |
| **端到端测试** (Playwright) | 核心用户旅程（登录→操作→结果） | 每个用户故事至少 1 个正向 + 1 个负向 E2E 测试 |
| **表单验证** | 登录、注册等表单的验证状态反馈 | 每个必填字段至少覆盖：空值、无效格式、有效值 |
| **异步状态** | Loading、Success、Error 三态展示 | 每个异步操作必须覆盖三态转换 |

## 项目制品信息与部署要求

**制品信息(代码仓地址)**：`https://github.com/LeeStrongCir/spec_mode_dev.git`

**部署操作步骤**：

```bash
# 务必克隆到 WSL 原生文件系统（/mnt/c/ 路径构建极慢）
cd /tmp
git clone https://github.com/LeeStrongCir/spec_mode_dev.git

ls /tmp/spec_mode_dev/
# 能看到 leecloud_platform/ 目录
```

**部署约束**：
- 项目制品必须克隆至 WSL 原生 Linux 文件系统（如 `/tmp`），禁止使用 `/mnt/c/` 等 Windows 挂载路径，否则构建速度极慢

## 治理

本章程为项目最高级别的测试规范，所有测试制品提交与审查必须遵循。任何修改须经团队评审。

测试人员在交付测试制品时必须满足以下五项要求：

**规格对应**：每个功能须有对应的测试用例，无测试规格的功能不得交付。

**双向可追溯**：集成测试须可追溯至架构设计，端到端测试须可追溯至用户故事，正向与负向场景成对覆盖。

**技术栈约束**：严格使用本宪章定义的工具，按集成/E2E 领域选型，不得擅自引入替代方案。

**目录规范**：所有测试产物置于统一 `leecloud_platform_tests/` 根目录下。文本用例按特性分组存放于 `leecloud_platform_tests/test-cases/{NNN-feature}/`，与 `specs/` 结构镜像对应；集成测试按技术层分组存放于 `leecloud_platform_tests/integration/`，保持 conftest fixture 共享；E2E 测试以扁平结构存放于 `leecloud_platform_tests/e2e/`，文件级按特性命名。

**前端定位规范**：前端集成测试与 E2E 测试须优先使用 `getByTestId` 定位元素，禁止依赖 Ant Design 内部 class 或 DOM 结构。

**版本**：4.1.0 | **生效日期**：2026-05-13 | **最后修订**：2026-05-13
