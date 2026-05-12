# 测试计划: LECS主机管理功能

> **版本**: `002-lecs-host`
> **创建日期**: 2026-05-12
> **输入**: 功能测试规格文件 `specs/002-lecs-host/spec.md`

> **说明**：本模板由 `/speckit-test.plan` 命令填充。测试计划是连接"测试规格说明"与"测试任务分解"的桥梁，定义测试策略、环境、范围和风险。

## 摘要

本测试计划覆盖 LECS 主机（云服务器）全生命周期管理功能的测试设计，包括：控制台搜索导航、主机列表与状态矩阵、创建表单与费用估算、生命周期控制（关机/启动）、安全删除（软删除）、以及 RESTful API 管理接口。测试策略分为两层——**集成测试**（API 契约 + 业务逻辑 + 数据库状态）和**端到端测试**（P1 用户故事完整流程），遵循 Lee 云平台测试宪章的 ISO 29119 技术要求与双向可追溯性要求。

## 技术上下文

**测试框架**: pytest（集成测试，支持并行执行 via pytest-xdist）+ Playwright（端到端测试）
**测试数据库**: SQLite 内存库（集成测试，保证隔离性与速度）
**浏览器自动化**: Playwright（Chromium，端到端测试）
**Mock 策略**: unittest.mock / pytest-mock mock 外部服务（计费系统、异步任务队列、认证系统），不 mock 框架层和业务核心逻辑

## 宪章门禁

*门禁：必须在测试实现前通过。测试设计后需重新检查。*

| 门禁项 | 宪章要求 | 本文档合规状态 |
|--------|----------|----------------|
| 规格优先 | 每个规格制品必须有对应测试制品 | ✅ 已通过 — 本计划为 spec.md 中全部 6 个用户故事、5 个边缘场景、5 个 API 接口设计了对应的集成测试和端到端测试 |
| 测试层级命名 | 标识符遵循 `[LEVEL]P-[SEQ]-[ITERATION]`（如 `ITP-001-A`） | ✅ 将通过 — tasks.md 中将严格使用此命名模式 |
| 双向可追溯性 | 架构设计→集成测试、用户故事→端到端测试，正负向成对 | ✅ 将通过 — 每个正向场景至少设计一个负向对照 |
| ISO 29119 接口视图 | 接口契约测试 | ✅ 将通过 — 所有 API 接口（GET/POST/DELETE）均有对应契约测试 |
| ISO 29119 数据设计视图 | 边界值分析 + 等价类划分 | ✅ 将通过 — 主机名（4-10字符）、用户名（4-16）、密码（8-32）、掩码（8-24）、IP 格式等均覆盖边界值 |
| ISO 29119 依赖视图 | 故障注入 + 负向测试 | ✅ 将通过 — 外部服务 mock 故障注入、配额超限、状态机违规操作等负向场景全覆盖 |
| 并行执行支持 | 测试框架必须支持并行 | ✅ 将通过 — pytest-xdist 用于集成测试并行 |
| 外部依赖 mock | 集成测试中所有外部依赖必须使用 mock/stub | ✅ 将通过 — 异步任务队列、计费计算、认证系统均采用 mock |
| 测试数据隔离 | 测试之间无共享可变状态 | ✅ 将通过 — 每个测试使用独立 SQLite 内存库实例 + fixture 作用域 function |

## 测试策略总览

### 测试层次

本功能包含以下测试层次：

| 层级 | 职责 | 覆盖指引 | 失败定位 |
|------|------|----------|----------|
| **集成测试** | API 契约 + 状态机逻辑 + 数据库状态流转 | 覆盖全部 6 个用户故事 + 5 个边缘场景 + 5 个 API 接口，约 30-40 条用例 | 定位到组件交互边界（Route → Service → DB） |
| **端到端测试** | 完整用户流程 + 前端交互 + 异步状态轮询 | 仅覆盖 P1 核心路径（搜索跳转、列表状态矩阵、创建表单、生命周期控制），约 5-8 条用例 | 定位到用户操作级别 |

### 分层边界规则

- **集成测试**：使用真实 SQLite 内存数据库，**不** mock 框架层（FastAPI/SQLAlchemy），但 **mock** 异步任务队列（Celery/RQ）、外部计费接口和认证系统的 JWT 签发逻辑。
- **端到端测试**：真实 Playwright 浏览器 + 完整应用栈（前端 + 后端 + 内存 DB），仅 mock 不可控的外部依赖（如第三方计费服务）。**不复测**集成测试已覆盖的 API 契约和字段级校验。

## 各层测试详细计划

### 集成测试

**目标**：LECS 主机 API 契约验证、状态机流转逻辑、数据库状态一致性、配额与权限控制

| 集成点 | 测试文件 | 验证范围 |
|--------|----------|----------|
| 搜索导航 → 路由跳转 | `tests/integration/002-lecs-host/test_sc01_search.py` | 搜索关键词匹配、跳转路由正确性 |
| 列表查询 → 分页 + 状态过滤 | `tests/integration/002-lecs-host/test_sc02_list.py` | GET /api/v1/lecs-hosts 分页、状态过滤、角色权限过滤 |
| 主机创建 → 业务逻辑 + 配额校验 | `tests/integration/002-lecs-host/test_sc03_create.py` | POST /api/v1/lecs-hosts 参数校验、费用计算、配额拦截 |
| 状态机流转（关机/启动） | `tests/integration/002-lecs-host/test_sc04_lifecycle.py` | POST /stop, /start 状态转换合法性、过渡态并发拦截 |
| 软删除 → 权限 + 配额释放 | `tests/integration/002-lecs-host/test_sc05_delete.py` | DELETE /{id} 状态前置校验、软删除标记、配额减 1 |
| API 认证 + 授权 | `tests/integration/002-lecs-host/test_sc06_auth.py` | JWT Cookie / Service Token 认证、越权拦截、401/403 响应 |
| 统一响应格式 + 错误处理 | `tests/integration/002-lecs-host/test_sc07_response.py` | success/error_code/error_message 格式一致性 |

#### Mock 策略

| 依赖类型 | 处理方式 | 理由 |
|----------|----------|------|
| 异步任务队列（Celery/RQ） | `unittest.mock.patch` mock `delay()` / `apply_async()` | 异步执行不在集成测试范围内，仅验证任务提交逻辑 |
| 外部计费服务 | mock 返回固定费率表 | 计费计算逻辑由后端服务提供，集成测试验证估算公式正确性 |
| JWT 签发与验证 | 使用固定 secret 的真实签发逻辑 | 认证逻辑需真实验证，但 secret 固定以消除外部依赖 |
| 时间敏感逻辑（超、轮询） | `freezegun` 冻结/快进时间 | 创建超时（60秒）、状态轮询逻辑需要确定性时间控制 |
| 密码哈希 | 直接调用真实哈希算法 | 确定性算法，无外部依赖，不应 mock |

#### 测试数据隔离

- **Fixture 作用域**: 每个测试使用独立的 SQLite 内存数据库实例，通过 `pytest.fixture(scope="function")` 保证
- **数据工厂**: 使用 Factory Boy 创建 LECS 主机、用户等测试数据
- **事务回滚**: 每个测试在独立事务中执行，测试结束后自动回滚，确保无共享状态

### 端到端测试

**目标**：P1 用户故事的完整控制台用户旅程验证

| 场景 | 测试文件 | 路径 | 预期结果 |
|------|----------|------|----------|
| 搜索跳转至列表页 | `tests/e2e/002-lecs-host/test_sc01_search.spec.ts` | 登录 → 输入搜索词 → 点击结果 → 验证 URL | 跳转至 `/console/lecs-hosts/list`，页面正常加载 |
| 列表状态矩阵与操作按钮 | `tests/e2e/002-lecs-host/test_sc02_list_matrix.spec.ts` | 查看多状态主机 → 验证按钮启用/置灰逻辑 | 各状态按钮可用性与状态机矩阵 100% 匹配 |
| 创建主机完整流程 | `tests/e2e/002-lecs-host/test_sc03_create.spec.ts` | 填写表单 → 确认弹窗 → 提交 → 重定向 → 状态轮询 | 创建成功，30秒内状态从"创建中"转为"正常" |
| 关机→启动生命周期 | `tests/e2e/002-lecs-host/test_sc04_lifecycle.spec.ts` | 关机 → 等待过渡态 → 验证已关机 → 启动 → 验证正常 | 完整状态流转正确，过渡态按钮全禁用 |
| 安全删除流程 | `tests/e2e/002-lecs-host/test_sc05_delete.spec.ts` | 关机 → 删除确认 → 异步删除 → 行消失 | 行消失，配额计数减少 |

#### Playwright 策略

- **页面交互**: 优先使用 `data-testid` 定位元素
- **状态验证**: 验证 URL、页面内容、DOM 属性变化、网络请求响应
- **等待策略**: 使用 Playwright 自动等待 + `waitForSelector`，对异步状态转换使用轮询式断言（最多等待 30 秒，每 3 秒重试）
- **视觉回归**: 不执行截图对比，仅验证功能行为

#### 端到端测试范围约束

- 端到端测试 **不复测** 集成测试已验证的接口契约和边界条件
- 端到端测试 仅覆盖「用户操作 → 系统响应」的完整路径
- 每条端到端测试用例必须对应 spec.md 中的一个 P1 级别用户故事或关键验收场景

## 测试基础设施

### Fixture 设计

```python
# conftest.py 中的关键 fixture

@pytest.fixture(scope="function")
def db_session():
    """每个测试独立的内存 SQLite 会话"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = SessionLocal(bind=engine)
    yield session
    session.close()

@pytest.fixture
def test_user(db_session):
    """使用 Factory Boy 创建标准用户"""
    user = UserFactory(db_session, role="user")
    yield user

@pytest.fixture
def admin_user(db_session):
    """创建管理员用户"""
    user = UserFactory(db_session, role="admin")
    yield user

@pytest.fixture
def authenticated_client(client, test_user):
    """创建已登录状态的测试客户端（携带 JWT Cookie）"""
    token = create_jwt_token(test_user.id)
    client.cookies.set("jwt_token", token)
    yield client

@pytest.fixture
def lecs_host_factory(db_session, test_user):
    """LECS 主机数据工厂，支持指定状态、规格等参数"""
    def _create(state="normal", **kwargs):
        return LecsHostFactory(db_session, user=test_user, state=state, **kwargs)
    yield _create

@pytest.fixture
def mock_async_queue():
    """mock 异步任务队列，记录任务提交但不实际执行"""
    with patch("celery.Celery.send_task") as mock:
        mock.return_value = MockAsyncResult()
        yield mock
```

### 并行执行策略

- 集成测试使用 pytest-xdist 并行执行（`pytest -n auto`）
- E2E 测试串行执行（避免浏览器实例冲突）

## 项目结构

### 文档结构（本特性）

```text
specs/002-lecs-host/
├── plan.md              # 本文件（由 /speckit-test.plan 命令输出）
├── research.md          # 阶段 0 输出（技术调研）
├── spec.md              # 测试规格说明
└── tasks.md             # 测试执行任务分解（由 /speckit-test.tasks 命令生成）
```

### 测试工件结构（仓库根目录）

```text
tests/
├── cases/
│   └── 002-lecs-host/
│       ├── sc-01-search.md
│       ├── sc-02-list.md
│       ├── sc-03-create.md
│       ├── sc-04-lifecycle.md
│       └── sc-05-delete.md
│
├── integration/
│   └── 002-lecs-host/
│       ├── test_sc01_search.py
│       ├── test_sc02_list.py
│       ├── test_sc03_create.py
│       ├── test_sc04_lifecycle.py
│       ├── test_sc05_delete.py
│       ├── test_sc06_auth.py
│       └── test_sc07_response.py
│
├── e2e/
│   └── 002-lecs-host/
│       ├── test_sc01_search.spec.ts
│       ├── test_sc02_list_matrix.spec.ts
│       ├── test_sc03_create.spec.ts
│       ├── test_sc04_lifecycle.spec.ts
│       └── test_sc05_delete.spec.ts
│
├── fixtures/
│   ├── base-fixture.ts
│   ├── data/
│   │   └── lecs-specs.json
│   └── mocks/
│       └── billing-service.json
```

## 测试环境

### 环境要求

| 组件 | 要求 | 备注 |
|------|------|------|
| 执行机 | Python 3.11+，Node.js 18+ | 集成测试 + E2E 测试运行环境 |
| 依赖项 | pytest, pytest-xdist, httpx, fakeredis, freezegun, factory-boy | 集成测试依赖 |
| 浏览器 | Playwright Chromium | E2E 测试需要，通过 `npx playwright install` 安装 |

### 环境变量配置

```bash
DATABASE_URL=sqlite:///:memory:
JWT_SECRET=test-secret-key-for-testing-only
ASYNC_TASK_MOCK=true
BILLING_SERVICE_MOCK=true
```

### 测试配置文件

| 文件 | 用途 |
|------|------|
| `tests/conftest.py` | 全局 fixture（DB、用户、客户端、主机工厂） |
| `pytest.ini` / `pyproject.toml` | pytest 配置（标记、并行、覆盖率） |
| `playwright.config.ts` | Playwright 配置（浏览器、超时、重试） |

### 测试数据准备

| 数据类型 | 来源 | 刷新频率 | 清理策略 |
|----------|------|----------|----------|
| 实例规格基准数据 | `tests/fixtures/data/lecs-specs.json` | 每次测试运行前加载 | 事务回滚自动清理 |
| 用户测试数据 | Factory Boy 动态创建 | 按需自动创建 | 测试结束后自动删除 |
| 外部服务 Mock 数据 | `tests/fixtures/mocks/` | 按需自动加载 | 测试结束后自动释放 |

## 测试可追溯性

### FR → Test 映射

| Spec 中的 FR | 测试层级 | 测试文件 | 测试用例 |
|--------------|----------|----------|----------|
| FR-001 (搜索跳转) | 集成 + E2E | `test_sc01_search.py`, `test_sc01_search.spec.ts` | ITP-001-A, ETP-001-A |
| FR-002 (列表展示) | 集成 + E2E | `test_sc02_list.py`, `test_sc02_list_matrix.spec.ts` | ITP-002-A, ETP-002-A |
| FR-003 (状态机操作矩阵) | 集成 + E2E | `test_sc02_list.py`, `test_sc02_list_matrix.spec.ts` | ITP-003-A, ETP-002-B |
| FR-004 ~ FR-008 (创建流程) | 集成 + E2E | `test_sc03_create.py`, `test_sc03_create.spec.ts` | ITP-004-A~E, ETP-003-A |
| FR-009 (配额) | 集成 | `test_sc03_create.py` | ITP-009-A |
| FR-010 ~ FR-011 (关机/启动) | 集成 + E2E | `test_sc04_lifecycle.py`, `test_sc04_lifecycle.spec.ts` | ITP-010-A, ETP-004-A |
| FR-012 ~ FR-014 (删除) | 集成 + E2E | `test_sc05_delete.py`, `test_sc05_delete.spec.ts` | ITP-012-A, ETP-005-A |
| FR-015 ~ FR-016 (轮询/超时) | 集成 | `test_sc02_list.py`, `test_sc03_create.py` | ITP-015-A, ITP-016-A |
| FR-017 ~ FR-018 (RBAC + 审计) | 集成 | `test_sc06_auth.py` | ITP-017-A |
| FR-019 ~ FR-020 (认证 + 加密) | 集成 | `test_sc06_auth.py` | ITP-019-A |
| FR-021 ~ FR-025 (API 接口) | 集成 | `test_sc02_list.py`, `test_sc03_create.py`, `test_sc04_lifecycle.py`, `test_sc05_delete.py` | ITP-021-A ~ ITP-025-A |
| FR-026 ~ FR-028 (API 认证/校验/格式) | 集成 | `test_sc06_auth.py`, `test_sc07_response.py` | ITP-026-A ~ ITP-028-A |

### 用户故事 → Test 映射

| 用户故事 | 优先级 | 对应测试 | 独立验证方式 |
|----------|--------|----------|--------------|
| 搜索并跳转至LECS主机列表 | P1 | `test_sc01_search.py` + `.spec.ts` | 输入关键词 → 验证搜索结果 → 点击跳转 → 验证 URL |
| 查看列表与操作矩阵 | P1 | `test_sc02_list.py` + `.spec.ts` | 创建多状态主机 → 逐行验证按钮状态 |
| 创建LECS主机 | P1 | `test_sc03_create.py` + `.spec.ts` | 完整表单填写 → 确认弹窗 → 提交 → 状态转换 |
| 控制生命周期 | P2 | `test_sc04_lifecycle.py` + `.spec.ts` | 触发关机 → 等待 → 触发启动 → 验证终态 |
| 安全删除主机 | P2 | `test_sc05_delete.py` + `.spec.ts` | 尝试删除运行态（拦截）→ 删除已关机态（成功） |
| 通过 API 管理主机 | P2 | `test_sc06_auth.py` + 各接口测试文件 | 直接调用 API → 验证认证、参数、响应格式 |

## 测试风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 异步状态流转时序不确定性 | 测试结果不稳定（flaky tests） | 使用 `freezegun` 控制时间 + 轮询式断言（3 秒间隔，最多 30 秒）替代硬编码 sleep |
| 外部计费服务不可用或返回不一致 | 费用估算测试失败 | Mock 计费服务返回固定费率表，隔离测试不依赖外部 |
| SQLite 内存库与生产 DB 行为差异 | 特定 SQL 查询在集成测试中通过但生产失败 | 仅用于状态 CRUD 测试；复杂查询在更上层测试中验证 |
| Playwright 浏览器版本更新导致定位失效 | E2E 测试大面积失败 | 使用 `data-testid` 而非 CSS 选择器，定期更新锁定浏览器版本 |
| 并发操作（前端点击 + API 调用同时触发） | 状态机竞态条件测试覆盖不全 | 在集成测试中模拟并发请求，验证后端幂等性与锁机制 |

## 复杂度追踪

> **仅在宪章门禁存在需要证明的违反项时填写**

| 违反项 | 为什么需要 | 拒绝更简单方案的理由 |
|--------|-----------|---------------------|
| 无 | 本计划未违反任何宪章门禁项 | — |
