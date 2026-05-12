---
description: "测试任务清单 - 注册登录"
---

# 测试任务: 注册登录

**输入**：来自 `/specs/001-register-login/` 的设计文档  
**前置条件**：`plan.md`（必需）、`spec.md`（必需，用于测试场景）

**组织**：任务按"测试用例编写 → 测试自动化代码编写 → 测试环境准备 → 测试执行"四阶段分组。前三阶段**串行**，第四阶段内每个自动化用例**可并行 `[P]`**。

## 格式: `[ID] [P?] [LABEL] Description`

- **[P]**: 可并行执行（不同文件、无依赖关系）
- **[LABEL]**: 阶段标签前缀
  - `[CASE-SC-01]`, `[CASE-SC-02]` — 阶段 1 测试用例编写（按场景）
  - `[AUTO-SC-01]`, `[AUTO-SC-02]` — 阶段 2 测试自动化代码编写（按场景）
  - `[ENV]` — 阶段 3 测试环境准备
  - `[EVT-SC-01]`, `[EVT-SC-02]` — 阶段 4 测试执行（按场景）
- 描述中必须包含准确的文件路径

## 路径约定

- **测试代码与资产**：`tests/`在仓库根目录下, `fixtures/` 在`tests/`目录下
- 路径依据 `plan.md` 中的项目结构定义

---

## 阶段 1: 测试用例编写（串行，按场景顺序）

### 阶段 1.1: SC-01 注册新账户 用例编写

**目标**：为注册场景（TC-001~TC-009）编写完整手工测试步骤，覆盖表单校验、唯一性、密码强度、邮箱格式、注册成功自动登录及XSS防护

- [X] T001 [CASE-SC-01] 在 `tests/cases/001-register-login/sc-register-new-account.md` 中编写 TC-001~TC-006 手工测试步骤（注册页面元素、空表单校验、用户名唯一性、密码一致性、密码强度、邮箱格式）
- [X] T002 [CASE-SC-01] 在 `tests/cases/001-register-login/sc-register-new-account.md` 中编写 TC-007~TC-009 手工测试步骤（注册成功账户创建+自动登录+重定向、返回登录链接跳转、XSS输入防护）

**检查点**：SC-01 用例编写完成

### 阶段 1.2: SC-02 输入凭据完成登录 用例编写

**目标**：为登录场景（TC-010~TC-015）编写完整手工测试步骤，覆盖页面元素、已认证重定向、空表单校验、成功登录、记住我持久化、短期Cookie验证

- [X] T003 [CASE-SC-02] 在 `tests/cases/001-register-login/sc-login-authenticate.md` 中编写 TC-010~TC-013 手工测试步骤（登录页面元素、已认证用户重定向、空表单校验、成功登录Cookie签发与重定向）
- [X] T004 [CASE-SC-02] 在 `tests/cases/001-register-login/sc-login-authenticate.md` 中编写 TC-014~TC-015 手工测试步骤（记住我30天持久化、未勾选24小时短期Cookie）

**检查点**：SC-02 用例编写完成

### 阶段 1.3: SC-03 处理登录失败 用例编写

**目标**：为登录失败场景（TC-016~TC-019）编写完整手工测试步骤，覆盖不存在用户名、密码错误、连续5次失败锁定、通用错误提示防枚举

- [X] T005 [CASE-SC-03] 在 `tests/cases/001-register-login/sc-login-failure-lockout.md` 中编写 TC-016~TC-019 手工测试步骤（不存在用户名登录、存在用户名密码错误、连续5次失败账号锁定、错误提示一致性防枚举）

**检查点**：SC-03 用例编写完成

### 阶段 1.4: SC-04 退出登录 用例编写

**目标**：为退出登录场景（TC-020~TC-022）编写完整手工测试步骤，覆盖Cookie清除、重定向、后退防护、过期Cookie访问受保护页面

- [X] T006 [CASE-SC-04] 在 `tests/cases/001-register-login/sc-logout-session-clear.md` 中编写 TC-020~TC-022 手工测试步骤（正常退出Cookie清除与重定向、退出后浏览器后退防护、Cookie过期后访问受保护页面重定向）
- [X] T007 [CASE-SC-05] 在 `tests/cases/001-register-login/sc-edge-cases.md` 中编写 EC-001~EC-003 手工测试步骤（CSRF Token校验失败403、IP限速429、未认证用户访问受保护路由拦截）
- [X] T008 [CASE-SC-05] 在 `tests/cases/001-register-login/sc-edge-cases.md` 中编写 EC-004~EC-005 手工测试步骤（已认证用户访问注册页重定向、审计日志记录完整性验证）

**检查点**：所有测试用例编写完成——阶段 2 测试自动化代码编写可以开始

---

## 阶段 2: 测试自动化代码编写（串行，按场景顺序）

### 阶段 2.1: SC-01 注册新账户 自动化代码

- [X] T009 [P] [AUTO-SC-01] 在 `tests/integration/001-register-login/test_register.py` 中编写注册集成测试（表单校验、用户名唯一性、密码强度、邮箱格式、注册成功账户创建+JWT签发+重定向，使用httpx ASGI客户端+fakeredis+freezegun）
- [X] T010 [P] [AUTO-SC-01] 在 `tests/e2e/001-register-login/test_register_login_flow.spec.ts` 中编写注册E2E测试（完整注册流程：填写表单→提交→验证账户创建→Cookie签发→重定向至/console，使用Playwright+data-testid）

### 阶段 2.2: SC-02 输入凭据完成登录 自动化代码

- [X] T011 [P] [AUTO-SC-02] 在 `tests/integration/001-register-login/test_login.py` 中编写登录集成测试（凭据验证、JWT签发、已认证重定向、空表单校验、记住我Cookie持久化、审计日志记录，使用httpx+freezegun验证过期时间）
- [X] T012 [P] [AUTO-SC-02] 在 `tests/e2e/001-register-login/test_register_login_flow.spec.ts` 中编写登录E2E测试（正常登录流程：输入凭据→验证Cookie签发→重定向至/console，使用Playwright自动等待）

### 阶段 2.3: SC-03 处理登录失败 自动化代码

- [X] T013 [P] [AUTO-SC-03] 在 `tests/integration/001-register-login/test_login.py` 中编写登录失败集成测试（不存在用户名、密码错误、通用错误提示一致性、连续5次失败锁定机制，使用fakeredis隔离锁定状态）
- [X] T014 [P] [AUTO-SC-03] 在 `tests/integration/001-register-login/test_rate_limiter.py` 中编写IP限速集成测试（同一IP每分钟10次上限，使用X-Forwarded-For头模拟不同IP）
- [X] T015 [P] [AUTO-SC-03] 在 `tests/e2e/001-register-login/test_login_failure.spec.ts` 中编写登录失败E2E测试（错误凭据登录→验证通用错误提示→密码框清空→连续失败锁定提示，使用Playwright）

### 阶段 2.4: SC-04 退出登录 自动化代码

- [X] T016 [P] [AUTO-SC-04] 在 `tests/integration/001-register-login/test_logout.py` 中编写退出登录集成测试（退出请求→Cookie清除→重定向验证）
- [X] T017 [P] [AUTO-SC-04] 在 `tests/e2e/001-register-login/test_logout_flow.spec.ts` 中编写退出登录E2E测试（点击退出→验证Cookie清除→重定向至/auth/login→后退防护验证，使用Playwright）

### 阶段 2.5: SC-05 边缘情况与异常 自动化代码

- [X] T018 [P] [AUTO-SC-05] 在 `tests/integration/001-register-login/test_csrf_middleware.py` 中编写CSRF集成测试（缺少CSRF Token返回403、伪造CSRF Token返回403、正常CSRF Token验证通过）
- [X] T019 [P] [AUTO-SC-05] 在 `tests/integration/001-register-login/test_auth_middleware.py` 中编写认证中间件集成测试（未认证用户访问受保护路由拦截、已认证用户访问登录/注册页重定向、JWT有效性校验）

**检查点**：所有自动化代码编写完成——阶段 3 测试环境准备可以开始

---

## 阶段 3: 测试环境准备（串行，阻塞后续所有阶段）

**目的**：测试基础设施初始化与环境搭建，为所有场景的后续阶段提供基础

**⚠️ 关键**：在此阶段完成之前，任何测试执行任务不得开始

- [X] T020 [ENV] 初始化 pytest 测试框架并在 `pyproject.toml` 中配置pytest依赖（pytest, httpx, fakeredis, freezegun, pytest-mock, pytest-xdist）
- [X] T021 [ENV] 在 `tests/conftest.py` 中编写全局 fixture（独立内存SQLite数据库、fakeredis实例、认证无关HTTP客户端、已认证HTTP客户端、测试用户builder）
- [X] T022 [ENV] 在 `tests/integration/001-register-login/conftest.py` 中编写特性级 fixture（带CSRF Token的认证客户端、锁定状态用户fixture）
- [X] T023 [ENV] 初始化 Playwright E2E环境并安装浏览器（`npx playwright install chromium`），在 `playwright.config.ts` 中配置E2E测试参数
- [X] T024 [ENV] 在 `tests/fixtures/base-fixture.ts` 中编写 Playwright 基础 fixture（data-testid选择器配置、认证状态管理、登录辅助函数）
- [X] T025 [ENV] 在 `tests/fixtures/data/auth-test-accounts.json` 中创建测试账号池数据文件（标准测试用户、锁定状态用户、管理员用户）
- [X] T026 [ENV] 在 `tests/fixtures/mocks/external-services.json` 中配置外部服务Mock数据（邮件发送Mock、第三方OAuth Mock）
- [X] T027 [ENV] 在 `pytest.ini` 中配置pytest标记（集成测试/e2e测试分类、并行执行设置）和 `.env.test` 测试环境变量文件

**检查点**：基础设施就绪——阶段 4 测试执行可以开始

---

## 阶段 4: 测试执行（并行，所有自动化用例同时执行）

**目的**：执行全部自动化测试用例，收集结果，验证功能是否符合规格

**⚠️ 所有 `[P]` 任务并行执行**

### 集成测试执行

- [X] T028 [P] [EVT-SC-01] 在 `tests/integration/001-register-login/test_register.py` 中执行注册集成测试 — **8 passed**
- [X] T029 [P] [EVT-SC-02] 在 `tests/integration/001-register-login/test_login.py` 中执行登录集成测试 — **5 passed**
- [X] T030 [P] [EVT-SC-03] 在 `tests/integration/001-register-login/test_logout.py` 中执行退出登录集成测试 — **1 passed**
- [X] T031 [P] [EVT-SC-05] 在 `tests/integration/001-register-login/test_auth_middleware.py` 中执行认证中间件集成测试 — **3 passed**
- [X] T032 [P] [EVT-SC-05] 在 `tests/integration/001-register-login/test_rate_limiter.py` 中执行速率限制集成测试 — **1 passed**
- [X] T033 [P] [EVT-SC-05] 在 `tests/integration/001-register-login/test_csrf_middleware.py` 中执行CSRF集成测试 — **3 passed**

### E2E 测试执行

- [X] T034 [P] [EVT-SC-01] 在 `tests/e2e/001-register-login/test_register_login_flow.spec.ts` 中执行注册登录E2E流程测试并记录结果到 `tests/reports/register-login-e2e-report.md`
- [X] T035 [P] [EVT-SC-03] 在 `tests/e2e/001-register-login/test_login_failure.spec.ts` 中执行登录失败E2E测试并记录结果到 `tests/reports/login-failure-e2e-report.md`
- [X] T036 [P] [EVT-SC-04] 在 `tests/e2e/001-register-login/test_logout_flow.spec.ts` 中执行退出登录E2E测试并记录结果到 `tests/reports/logout-e2e-report.md`

### 回归验证与总结

- [X] T037 [EVT-ALL] 执行回归验证，汇总所有测试报告并输出总结到 `tests/reports/summary.md`（包含通过率、失败用例详情、Test Incident Report、宪章门禁验证状态）

**检查点**：所有测试用例执行完成

---

## 依赖图

```
阶段 1: CASE-SC-01 ── CASE-SC-02 ── CASE-SC-03 ── CASE-SC-04 ── CASE-SC-05 → 全部完成
                                  ↓
阶段 2: AUTO-SC-01 ── AUTO-SC-02 ── AUTO-SC-03 ── AUTO-SC-04 ── AUTO-SC-05 → 全部完成
                                  ↓
阶段 3: ENV ───────────────────────────────────────────────────────────→ 完成
                                  ↓
阶段 4: EVT-SC-01 [P] ─── T028, T029, T034
        EVT-SC-02 [P] ─── T029
        EVT-SC-03 [P] ─── T030, T035
        EVT-SC-04 [P] ─── T036
        EVT-SC-05 [P] ─── T031, T032, T033
        EVT-ALL       ─── T037（回归验证，依赖所有EVT任务完成）
```

## 并行示例：阶段 4 测试执行

```bash
# 并行执行所有集成测试:
pytest tests/integration/001-register-login/ -n auto --dist loadfile

# 并行执行所有E2E测试:
npx playwright test tests/e2e/001-register-login/ --workers 4

# 每个用例独立执行，结果汇总至 tests/reports/summary.md
```

---

## 执行策略

### MVP First（仅执行 P1 场景）

1. 完成 阶段 1: SC-01（注册新账户）、SC-02（输入凭据完成登录）、SC-03（处理登录失败）用例编写
2. 完成 阶段 2: SC-01、SC-02、SC-03 自动化代码编写
3. 完成 阶段 3: 测试环境准备
4. 执行 阶段 4: SC-01、SC-02、SC-03 测试执行
5. **停止并验证**：独立验证 P1 场景结果（注册成功、登录成功、失败锁定）
6. 若通过，输出阶段性 MVP 报告

### 增量覆盖

1. 阶段 3 环境准备 → 基础设施就绪
2. P1 场景执行通过 → 输出阶段性报告（MVP！）
3. 继续 SC-04（退出登录）场景的用例编写、自动化、执行
4. 继续 SC-05（边缘情况）场景的用例编写、自动化、执行
5. 每个场景增加验证范围且不破坏已验证的场景

### 并行团队策略

多人协作时：

1. 团队共同完成 阶段 1~2 按场景顺序串行编写
2. 阶段 3: 测试环境准备
3. 阶段 4 内所有自动化用例同时并行执行

---

## Notes

- `[P]` 任务 = 不同文件、无依赖关系，可并行执行
- 阶段标签（`[ENV]`, `[CASE-SC-*]`, `[AUTO-SC-*]`, `[EVT-SC-*]`）将任务映射至具体阶段和测试场景以实现可追溯性
- 阶段 1~3 为串行依赖，阶段 4 为并行执行
- 执行前确认前置条件与测试数据就绪
- 每个任务或逻辑组执行后记录结果
- 避免：模糊任务、文件冲突、破坏执行顺序的跨阶段依赖
