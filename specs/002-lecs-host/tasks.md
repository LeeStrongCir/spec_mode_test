# 测试任务: LECS主机管理功能

**输入**：来自 `specs/002-lecs-host/` 的设计文档
**前置条件**：`plan.md`（必需）、`spec.md`（必需，用于测试场景）、`research.md`（可选）

**测试**：本特性分为 6 个测试场景（SC-01 至 SC-06），覆盖控制台搜索导航、列表状态矩阵、主机创建、生命周期控制、安全删除，以及 API 管理。

**组织**：测试分为四个阶段：阶段1：测试用例编写 → 阶段2：测试自动化代码编写 → 阶段3：测试环境准备 → 阶段4：测试执行。阶段间**严格串行**，但阶段1、2、4**内部任务可并行** `[P]`。

## 格式: `[ID] [P?] [LABEL] Description`

- **[P]**: 可并行执行（不同文件、无依赖关系，阶段内部可同时执行）
- **[LABEL]**: 阶段标签前缀
  - `[CASE-SC-01]`, `[CASE-SC-02]` — 阶段 1 测试用例编写（按场景）
  - `[AUTO-SC-01]`, `[AUTO-SC-02]` — 阶段 2 测试自动化代码编写（按场景）
  - `[ENV]` — 阶段 3 测试环境准备
  - `[EVT-SC-01]`, `[EVT-SC-02]` — 阶段 4 测试执行（按场景）
- 描述中必须包含准确的文件路径

## 路径约定

- **测试代码与资产**：`tests/`在仓库根目录下, `fixtures/` 在`tests/`目录下
- **测试用例文档**：`tests/cases/002-lecs-host/`
- **集成测试脚本**：`tests/integration/002-lecs-host/`
- **E2E 测试脚本**：`tests/e2e/002-lecs-host/`
- **测试数据与 Mock**：`tests/fixtures/data/`, `tests/fixtures/mocks/`

---

## 阶段 1: 测试用例编写（内部可并行 `[P]`）

**说明**：不同场景的测试用例编写可并行执行，但需等待本阶段全部完成后，阶段2才能开始

### 阶段 1.1: SC-01 搜索导航用例编写 (P1)

**目标**：验证用户通过控制台全局搜索栏搜索"LECS主机"关键词后，能够正确跳转至 LECS 主机列表页（`/console/lecs-hosts/list`）

- [X] T001 [P] [CASE-SC-01] 编写 SC-01 手工测试步骤在 `tests/cases/002-lecs-host/sc-01-search.md`，覆盖 TC-001（关键词匹配与高亮）、TC-002（模糊搜索"云服"匹配）、TC-003（点击跳转验证 URL 和页面加载）
- [X] T002 [P] [CASE-SC-01] 定义 SC-01 预期输出和验证点在 `tests/cases/002-lecs-host/sc-01-search.md`，包括搜索下拉出现时间 < 1 秒、关键词高亮正确性、跳转后 URL 精确匹配 `/console/lecs-hosts/list`

### 阶段 1.2: SC-02 列表与操作矩阵用例编写 (P1)

**目标**：验证 LECS 主机列表页数据列展示完整性，以及不同状态（normal/stopped/failed/deleting）下操作按钮（关机/启动/删除）的启用/置灰逻辑与状态机矩阵 100% 匹配

- [X] T003 [P] [CASE-SC-02] 编写 SC-02 手工测试步骤在 `tests/cases/002-lecs-host/sc-02-list.md`，覆盖 TC-010（列表数据列完整性）、TC-011（运行态 normal 按钮状态）、TC-012（已关机 stopped 按钮状态）、TC-013（创建失败 failed 按钮状态）、TC-014（删除中 deleting 按钮状态）、TC-015（软删除主机不可见）
- [X] T004 [P] [CASE-SC-02] 定义 SC-02 预期输出和验证点在 `tests/cases/002-lecs-host/sc-02-list.md`，包含每种状态下三个按钮的可点击/置灰判定标准、状态标签颜色验证、软删除查询 SQL 验证（`deleted_at IS NULL`）

### 阶段 1.3: SC-03 创建主机用例编写 (P1)

**目标**：验证创建表单的完整填写流程，包括主机名格式校验（4-10字符、不能下划线开头）、凭据复杂度校验、实例规格选择、费用实时估算公式（包年/包月 = 月费×月数，按需 = 月费÷30）、确认对话框内容完整性、以及配额上限 100 台拦截

- [X] T005 [P] [CASE-SC-03] 编写 SC-03 手工测试步骤在 `tests/cases/002-lecs-host/sc-03-create.md`，覆盖 TC-020（创建入口）、TC-021（主机名校验）、TC-022（凭据校验）、TC-023（费用估算）、TC-024（IP 配置校验）、TC-025（确认对话框与提交流程）、TC-026（配额上限拦截）
- [X] T006 [P] [CASE-SC-03] 定义 SC-03 预期输出和验证点在 `tests/cases/002-lecs-host/sc-03-create.md`，包括各校验规则的具体错误提示文案、费用计算公式精确结果（如 100×3=300元、100÷30≈3.33元）、配额满载时阻断提示"主机数量达到上限"

### 阶段 1.4: SC-04 生命周期控制用例编写 (P2)

**目标**：验证关机（normal→shutting_down→stopped）和启动（stopped/failed→starting→normal）的完整异步状态流转，过渡态下所有按钮置灰防冲突

- [X] T007 [P] [CASE-SC-04] 编写 SC-04 手工测试步骤在 `tests/cases/002-lecs-host/sc-04-lifecycle.md`，覆盖 TC-030（关机完整流转）、TC-031（启动完整流转）、TC-032（过渡态按钮全禁用）、TC-033（创建失败态可启动）
- [X] T008 [P] [CASE-SC-04] 定义 SC-04 预期输出和验证点在 `tests/cases/002-lecs-host/sc-04-lifecycle.md`，包括过渡态持续时间约 10 秒允许偏差 ±5 秒、终态按钮恢复可用性判定、异步任务提交记录验证

### 阶段 1.5: SC-05 安全删除用例编写 (P2)

**目标**：验证运行态主机删除被拦截、已关机/创建失败态主机的异步软删除流程、配额计数减少、数据库中 `deleted_at` 字段设置

- [X] T009 [P] [CASE-SC-05] 编写 SC-05 手工测试步骤在 `tests/cases/002-lecs-host/sc-05-delete.md`，覆盖 TC-040（运行态删除拦截）、TC-041（已关机态异步删除）、TC-042（创建失败态删除）
- [X] T010 [P] [CASE-SC-05] 定义 SC-05 预期输出和验证点在 `tests/cases/002-lecs-host/sc-05-delete.md`，包括拦截响应 403 + 提示"请先将主机关机，再执行删除操作"、软删除后 `deleted_at IS NOT NULL`、列表查询 `WHERE deleted_at IS NULL` 不再返回该行

### 阶段 1.6: SC-06 API 认证与授权用例编写 (P2)

**目标**：验证 API 接口的认证拦截（401）、越权访问拦截（403）、统一 JSON 响应格式（success/data/error_code/error_message）、以及 RBAC（管理员查看全部 vs 普通用户仅查看自身）

- [X] T011 [P] [CASE-SC-06] 编写 SC-06 手工测试步骤在 `tests/cases/002-lecs-host/sc-06-api-auth.md`，覆盖 TC-050（认证拦截）、TC-051（RBAC 权限隔离）、TC-052（统一响应格式），以及 EC-001（配额上限）、EC-002（创建超时）、EC-003（并发防冲突）
- [X] T012 [P] [CASE-SC-06] 定义 SC-06 预期输出和验证点在 `tests/cases/002-lecs-host/sc-06-api-auth.md`，包括 401/403/400 响应体结构、管理员与普通用户返回列表差异验证、并发请求返回 409/403 冲突状态

**检查点**：所有测试用例编写完成（T001~T012 全部完成）——阶段 2 测试自动化代码编写可以开始

---

## 阶段 2: 测试自动化代码编写（内部可并行 `[P]`）

**说明**：不同场景的自动化代码编写可并行执行，但需等待阶段1全部完成后才能开始，且本阶段全部完成后阶段3才能开始

### 阶段 2.1: SC-01 搜索导航自动化代码

- [X] T013 [P] [AUTO-SC-01] 编写搜索导航集成测试在 `tests/integration/002-lecs-host/test_sc01_search.py`，使用 pytest + httpx AsyncClient 验证搜索关键词匹配路由逻辑和跳转响应
- [X] T014 [P] [AUTO-SC-01] 编写搜索导航 E2E 测试在 `tests/e2e/002-lecs-host/test_sc01_search.spec.ts`，使用 Playwright 验证登录→输入搜索词→点击结果→URL 跳转的完整用户流程

### 阶段 2.2: SC-02 列表与操作矩阵自动化代码

- [X] T015 [P] [AUTO-SC-02] 编写列表查询集成测试在 `tests/integration/002-lecs-host/test_sc02_list.py`，验证 GET /api/v1/lecs-hosts 分页参数、状态过滤、角色权限过滤、软删除主机排除（`WHERE deleted_at IS NULL`）
- [X] T016 [P] [AUTO-SC-02] 编写列表状态矩阵 E2E 测试在 `tests/e2e/002-lecs-host/test_sc02_list_matrix.spec.ts`，使用 Playwright 创建多状态主机数据并逐行验证按钮启用/置灰逻辑

### 阶段 2.3: SC-03 创建主机自动化代码

- [X] T017 [P] [AUTO-SC-03] 编写主机创建集成测试在 `tests/integration/002-lecs-host/test_sc03_create.py`，验证 POST /api/v1/lecs-hosts 参数校验（主机名格式、凭据复杂度、IP 格式）、费用估算公式、配额上限拦截、mock_async_queue 模拟异步任务提交
- [X] T018 [P] [AUTO-SC-03] 编写主机创建 E2E 测试在 `tests/e2e/002-lecs-host/test_sc03_create.spec.ts`，使用 Playwright 完整走通表单填写→确认弹窗→提交创建→列表页观察"创建中"→等待状态转为"正常"
- [X] T019 [P] [AUTO-SC-03] 创建实例规格基准数据在 `tests/fixtures/data/lecs-specs.json`，包含经济型和高性能型全部 8 种规格的 vCPU/内存/系统盘/月费数据

### 阶段 2.4: SC-04 生命周期控制自动化代码

- [X] T020 [P] [AUTO-SC-04] 编写关机/启动集成测试在 `tests/integration/002-lecs-host/test_sc04_lifecycle.py`，验证 POST /stop 和 /start 状态机合法性、过渡态并发拦截（mock_async_queue 记录任务提交）、使用 freezegun 控制时间确定性
- [X] T021 [P] [AUTO-SC-04] 编写生命周期 E2E 测试在 `tests/e2e/002-lecs-host/test_sc04_lifecycle.spec.ts`，使用 Playwright 验证关机→等待过渡态→已关机→启动→正常的完整流转，按钮状态实时变化

### 阶段 2.5: SC-05 安全删除自动化代码

- [X] T022 [P] [AUTO-SC-05] 编写删除集成测试在 `tests/integration/002-lecs-host/test_sc05_delete.py`，验证 DELETE /{id} 对运行态返回 403、对已关机态执行软删除（设置 `deleted_at`）、配额计数减少 1
- [X] T023 [P] [AUTO-SC-05] 编写删除 E2E 测试在 `tests/e2e/002-lecs-host/test_sc05_delete.spec.ts`，使用 Playwright 验证"已关机"主机删除确认弹窗→异步删除→行消失流程

### 阶段 2.6: SC-06 API 认证与统一响应自动化代码

- [X] T024 [P] [AUTO-SC-06] 编写认证与授权集成测试在 `tests/integration/002-lecs-host/test_sc06_auth.py`，验证 JWT Cookie / Service Token 认证、无凭证返回 401、越权访问返回 403、普通用户仅查自身主机、管理员查全部
- [X] T025 [P] [AUTO-SC-06] 编写统一响应格式集成测试在 `tests/integration/002-lecs-host/test_sc07_response.py`，验证所有 API 接口的 success/error_code/error_message 字段一致性，以及 400 参数错误返回字段级错误信息
- [X] T026 [P] [AUTO-SC-06] 编写边缘场景集成测试在 `tests/integration/002-lecs-host/test_sc08_edge_cases.py`，覆盖 EC-001（配额上限 100 台创建拦截）、EC-002（创建超时 60 秒降级为 failed，使用 freezegun）、EC-003（并发操作防冲突返回 409/403）

**检查点**：所有自动化代码编写完成（T013~T026 全部完成）——阶段 3 测试环境准备可以开始

---

## 阶段 3: 测试环境准备（阶段间串行，内部任务也串行）

**目的**：测试基础设施初始化与环境搭建，为测试执行阶段提供基础

**⚠️ 关键**：此阶段内部各项环境准备工作必须严格按顺序完成，且在此阶段整体完成之前，任何测试执行任务不得开始

- [X] T027 [ENV] 选取并确认测试环境：设置环境变量 `DATABASE_URL=sqlite:///:memory:`、`JWT_SECRET=test-secret-key-for-testing-only`、`ASYNC_TASK_MOCK=true`、`BILLING_SERVICE_MOCK=true`，在 `pytest.ini` 或 `pyproject.toml` 中配置 pytest 测试标记和覆盖率
- [X] T028 [ENV] 安装执行机必需的工具和依赖：Python 3.11+、Node.js 18+，执行 `pip install pytest pytest-xdist httpx freezegun factory-boy` 安装集成测试依赖，执行 `npx playwright install chromium` 安装 Playwright 浏览器
- [X] T029 [ENV] 创建全局 conftest.py 在 `tests/conftest.py`，实现 db_session（独立 SQLite 内存库）、test_user/admin_user 工厂、authenticated_client（JWT Cookie）、lecs_host_factory、mock_async_queue 核心 fixture
- [X] T030 [ENV] 创建 Playwright 基础配置在 `playwright.config.ts`，配置 Chromium 浏览器、超时时间（30 秒）、重试策略，并在 `tests/fixtures/base-fixture.ts` 中实现基础 fixture（浏览器上下文、页面对象、data-testid 定位器策略）
- [X] T031 [ENV] 准备并注入测试数据集：在 `tests/fixtures/data/lecs-specs.json` 写入 8 种实例规格基准数据，在 `tests/fixtures/mocks/` 中创建计费服务 Mock 定义（固定费率表），确保所有 fixture 数据就绪且可被测试引用

**检查点**：基础设施就绪（T027~T031 全部完成）——阶段 4 测试执行可以开始

---

## 阶段 4: 测试执行（内部可并行 `[P]`）

**目的**：执行全部自动化测试用例，收集结果，验证功能是否符合规格

**说明**：本阶段所有任务均可并行执行，但需等待阶段1、2、3全部完成后才能开始

**⚠️ 所有任务均标记 `[P]`，可同时执行**

- [X] T032 [P] [EVT-SC-01] 执行搜索导航集成测试 `tests/integration/002-lecs-host/test_sc01_search.py` 并记录结果
- [X] T033 [P] [EVT-SC-01] 执行搜索导航 E2E 测试 `tests/e2e/002-lecs-host/test_sc01_search.spec.ts` 并记录结果
- [X] T034 [P] [EVT-SC-02] 执行列表查询集成测试 `tests/integration/002-lecs-host/test_sc02_list.py` 并记录结果
- [X] T035 [P] [EVT-SC-02] 执行列表状态矩阵 E2E 测试 `tests/e2e/002-lecs-host/test_sc02_list_matrix.spec.ts` 并记录结果
- [X] T036 [P] [EVT-SC-03] 执行创建主机集成测试 `tests/integration/002-lecs-host/test_sc03_create.py` 并记录结果
- [X] T037 [P] [EVT-SC-03] 执行创建主机 E2E 测试 `tests/e2e/002-lecs-host/test_sc03_create.spec.ts` 并记录结果
- [X] T038 [P] [EVT-SC-04] 执行生命周期集成测试 `tests/integration/002-lecs-host/test_sc04_lifecycle.py` 并记录结果
- [X] T039 [P] [EVT-SC-04] 执行生命周期 E2E 测试 `tests/e2e/002-lecs-host/test_sc04_lifecycle.spec.ts` 并记录结果
- [X] T040 [P] [EVT-SC-05] 执行删除集成测试 `tests/integration/002-lecs-host/test_sc05_delete.py` 并记录结果
- [X] T041 [P] [EVT-SC-05] 执行删除 E2E 测试 `tests/e2e/002-lecs-host/test_sc05_delete.spec.ts` 并记录结果
- [X] T042 [P] [EVT-SC-06] 执行认证授权集成测试 `tests/integration/002-lecs-host/test_sc06_auth.py` 并记录结果
- [X] T043 [P] [EVT-SC-06] 执行统一响应格式集成测试 `tests/integration/002-lecs-host/test_sc07_response.py` 并记录结果
- [X] T044 [P] [EVT-SC-06] 执行边缘场景集成测试 `tests/integration/002-lecs-host/test_sc08_edge_cases.py` 并记录结果
- [X] T045 [P] [EVT-ALL] 执行回归验证：运行 `pytest tests/integration/002-lecs-host/ -n auto` 全集并行执行 + `npx playwright test tests/e2e/002-lecs-host/`，输出测试总结报告在 `tests/reports/summary.md`

**检查点**：所有测试用例执行完成（T032~T045 全部完成）

---

## 依赖关系图

```
阶段 1: [P] CASE-SC-01 (T001,T002) ─┐
       [P] CASE-SC-02 (T003,T004) ──┼──→ T001~T012 全部完成
       [P] CASE-SC-03 (T005,T006) ──┤
       [P] CASE-SC-04 (T007,T008) ──┤
       [P] CASE-SC-05 (T009,T010) ──┤
       [P] CASE-SC-06 (T011,T012) ─┘
                                     ↓
阶段 2: [P] AUTO-SC-01 (T013,T014) ─┐
       [P] AUTO-SC-02 (T015,T016) ──┤
       [P] AUTO-SC-03 (T017~T019) ──┼──→ T013~T026 全部完成
       [P] AUTO-SC-04 (T020,T021) ──┤
       [P] AUTO-SC-05 (T022,T023) ──┤
       [P] AUTO-SC-06 (T024~T026) ─┘
                                     ↓
阶段 3: ENV T027 → T028 → T029 → T030 → T031（严格串行）
                                     ↓
阶段 4: [P] EVT-SC-01 (T032,T033) ─┐
       [P] EVT-SC-02 (T034,T035) ──┤
       [P] EVT-SC-03 (T036,T037) ──┼──→ T032~T045 全部完成
       [P] EVT-SC-04 (T038,T039) ──┤
       [P] EVT-SC-05 (T040,T041) ──┤
       [P] EVT-SC-06 (T042~T044) ──┤
       [P] EVT-ALL  (T045) ────────┘
```

---

## 并行示例：阶段 4 测试执行

```bash
# 同时启动所有集成测试（pytest-xdist 并行）:
pytest tests/integration/002-lecs-host/ -n auto

# 同时启动所有 E2E 测试（Playwright workers）:
npx playwright test tests/e2e/002-lecs-host/ --workers=4

# 每条用例独立执行，结果汇总至 tests/reports/summary.md
```

---

## 执行策略

### MVP First（仅执行 P1 场景：SC-01/SC-02/SC-03）

1. 完成 阶段 1: P1 场景（SC-01 搜索、SC-02 列表、SC-03 创建）的测试用例编写（T001~T006，可并行）
2. 完成 阶段 2: P1 场景的自动化代码编写（T013~T019，可并行）
3. 完成 阶段 3: 测试环境准备（T027~T031，严格串行）
4. 执行 阶段 4: P1 场景的测试执行（T032~T037，可并行）
5. **停止并验证**：独立验证搜索跳转、列表状态矩阵、主机创建三大核心路径
6. 若通过，输出阶段性报告并进入增量覆盖

### 增量覆盖

1. 阶段 3 环境准备 → 基础设施就绪（一次完成，后续场景复用）
2. P1 场景执行通过 → 输出阶段性报告（MVP！）
3. 继续 P2 场景（SC-04 生命周期、SC-05 删除、SC-06 API）的用例编写、自动化、执行（T007~T012, T020~T026, T038~T045）
4. 每个场景增加验证范围且不破坏已验证的场景
5. 边缘场景（EC-001~EC-005）在 SC-06 自动化中统一覆盖

### 并行团队策略

多人协作时：

1. 阶段 1~2: 不同成员可并行负责不同场景的用例编写和自动化代码编写（如成员 A 负责 SC-01/SC-02，成员 B 负责 SC-03/SC-04，成员 C 负责 SC-05/SC-06）
2. 阶段 3: 测试环境准备由一名成员按顺序完成（阻塞后续阶段）
3. 阶段 4: 所有自动化用例同时并行执行
4. **阶段间保持严格串行依赖**：阶段1完成→阶段2开始→阶段3完成→阶段4开始

---

## 场景独立验证标准

| 场景 | 优先级 | 独立验证标准 |
|------|--------|--------------|
| SC-01 搜索导航 | P1 | 输入关键词 → 出现搜索结果 → 点击跳转 → URL = `/console/lecs-hosts/list` → 页面正常渲染 |
| SC-02 列表与操作矩阵 | P1 | 创建多状态主机 → 每个状态的按钮开启/置灰与状态机矩阵 100% 匹配 → 软删除主机不在列表中 |
| SC-03 创建主机 | P1 | 完整表单填写 → 字段校验全部通过 → 费用估算公式精确 → 确认弹窗完整摘要 → 提交后重定向 → 新主机"创建中"→"正常" |
| SC-04 生命周期控制 | P2 | normal→shutting_down→stopped→starting→normal 完整流转 → 过渡态所有按钮置灰 |
| SC-05 安全删除 | P2 | 运行态删除返回 403 → 已关机态删除成功 → 行消失 → 配额计数减 1 → 数据库 `deleted_at` 已设置 |
| SC-06 API 认证与授权 | P2 | 无凭证→401 → 越权→403 → 统一 JSON 响应格式 → 管理员/普通用户返回数据差异正确 |

---

## 备注

- `[P]` 任务 = 不同文件、无依赖关系，阶段内部可并行执行
- 阶段标签（`[ENV]`, `[CASE-SC-*]`, `[AUTO-SC-*]`, `[EVT-SC-*]`）将任务映射至具体阶段和测试场景以实现可追溯性
- **阶段间严格串行**：阶段1：测试用例编写 → 阶段2：测试自动化代码编写 → 阶段3：测试环境准备 → 阶段4：测试执行
- **阶段内可并行**：阶段1：测试用例编写、阶段2：测试自动化代码编写、阶段4：测试执行 — 内部标记 `[P]` 的任务可同时执行
- 执行前确认前置条件与测试数据就绪
- 每个任务或逻辑组执行后记录结果
- 避免：模糊任务、文件冲突、破坏执行顺序的跨阶段依赖
