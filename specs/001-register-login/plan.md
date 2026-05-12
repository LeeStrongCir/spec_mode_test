# 测试计划: 注册登录

> **版本**: `001-register-login`
> **创建日期**: 2026-05-12 
> **输入**: 功能测试规格文件 `/specs/001-register-login/spec.md`

> **说明**：本模板由 `/speckit-test.plan` 命令填充。测试计划是连接"测试规格说明"与"测试任务分解"的桥梁，定义测试策略、环境、范围和风险。

## 摘要

本功能覆盖用户认证生命周期的四个核心流程：注册新账户、凭证登录、登录失败处理、退出登录。测试范围包含表单校验、JWT Cookie签发与验证、路由守卫、安全机制（CSRF防护、速率限速、连续失败锁定、防用户名枚举）。测试不包含MFA、社交登录、邮箱验证激活及网络异常场景。

基于宪章要求，测试策略为双向可追溯：每个FR对应集成测试+端到端测试，每个P1用户故事必须有对应的端到端验证路径。负向测试成对覆盖每个正向场景。

## 技术上下文

**测试类型**: 功能测试

**测试框架**: pytest（后端集成测试）+ Playwright（端到端浏览器测试）  
**测试数据库**: SQLite 内存库（集成测试）+ 真实 PostgreSQL 测试实例（E2E测试）  
**浏览器自动化**: Playwright（Chromium）  
**Mock 策略**: 
- 外部服务（邮件发送、第三方OAuth）：`unittest.mock` / `pytest-mock`
- JWT签发：复用真实JWT库但使用固定secret进行确定性验证
- Redis状态（限速/锁定）：`fakeredis` 模拟Redis，避免外部依赖
- 时间相关逻辑：`freezegun` 冻结时间以保证锁定/过期测试的确定性
- 密码哈希：使用真实passlib/bcrypt，确定性算法不应mock

## 宪章门禁

*门禁：必须在测试实现前通过。测试设计后需重新检查。*

| 门禁项 | 宪章来源 | 状态 |
|--------|----------|------|
| 集成测试覆盖所有接口契约 | 第I条：100%接口契约覆盖 | ✅ 已覆盖 |
| 端到端测试覆盖所有P1用户故事 | 第I条：100%核心业务场景覆盖 | ✅ 已覆盖 |
| 每个正向测试对应至少一个负向测试 | 第II条：正负测试成对追溯 | ✅ 已覆盖 |
| 至少应用一种ISO 29119设计技术 | 第III条：边界值+等价类+故障注入 | ✅ 已覆盖 |
| 测试数据隔离，无共享可变状态 | 第I条：测试间无共享状态 | ✅ 已规划 |
| 测试标识符遵循 `[LEVEL]P-[SEQ]-[ITERATION]` | 第I条：命名规范 | ✅ 已遵循 |
| 所有测试可追溯至规格来源 | 第II条：正向追溯 | ✅ 已映射 |

## Phase 0: 研究与决策

### research.md

#### Decision 1: CSRF Token 在测试中的处理方式
- **Rationale**: 规格要求CSRF Token校验（FR-010、FR-020）。集成测试中需要从服务端获取有效CSRF Token后提交表单，而非mock CSRF校验逻辑本身，以验证完整的防护链路。
- **Alternatives considered**: (a) mock CSRF校验中间件——无法验证完整链路；(b) 关闭CSRF仅用于测试——遗漏安全机制验证。

#### Decision 2: JWT Cookie 在集成测试中的验证方式
- **Rationale**: 集成测试需验证HttpOnly属性、过期时间(24h/30d)、SameSite值。使用`httpx`的`ASGI/WSGI`测试客户端获取Set-Cookie响应头，解析Cookie属性。不使用`requests`库（不支持HttpOnly Cookie的完整属性验证）。
- **Alternatives considered**: (a) 使用普通HTTP客户端忽略Cookie属性测试——无法验证HttpOnly/SameSite；(b) 在浏览器环境中测试——属于E2E范围，不适用集成测试。

#### Decision 3: 连续失败锁定状态的隔离
- **Rationale**: 锁定状态存储在Redis中。集成测试使用`fakeredis`完全隔离，每个测试从干净的Redis状态开始，避免测试间污染。E2E测试使用真实Redis TestContainer（或开发环境Redis中的独立key前缀）。
- **Alternatives considered**: (a) 使用内存字典替代Redis——与生产架构不一致；(b) 每个测试重启Redis——过重。

#### Decision 4: IP限速测试的地址模拟
- **Rationale**: 限速基于客户端IP地址。集成测试中在测试请求中携带伪造的`X-Forwarded-For`或`X-Real-IP`头来模拟不同IP，测试限速隔离。E2E测试中由于浏览器同源限制，所有请求来自同一IP，使用独立测试实例或独立key前缀隔离。
- **Alternatives considered**: (a) 修改服务逻辑以支持测试注入IP——侵入性过大；(b) 使用代理层修改IP——过重。

#### Decision 5: Cookie过期测试的时间模拟
- **Rationale**: Cookie过期涉及时间逻辑。集成测试使用`freezegun`冻结服务端时间来测试过期行为。E2E测试中无法冻结浏览器时间，采用"设置极短过期时间(如5秒)后等待过期"的策略。
- **Alternatives considered**: (a) 修改系统时钟——影响其他进程；(b) 等待真实时间过期——测试执行时间过长。

## 测试策略总览

### 测试层次

本功能包含以下测试层次：

| 层级 | 职责 | 覆盖指引 | 失败定位 |
|------|------|----------|----------|
| **集成测试** | Auth路由→Service→DB的组件协作+API契约验证 | 覆盖全部FR（FR-001至FR-021），含正向+负向场景 | 定位到组件交互边界 |
| **端到端测试** | 完整用户流程端到端验证（浏览器交互） | 仅覆盖核心P1路径（注册成功、登录成功、登录失败锁定、退出登录） | 定位到用户操作级别 |

### 分层边界规则

- **集成测试**：使用真实数据库（SQLite内存库），**不**mock路由层逻辑，但**可**mock外部服务（邮件、第三方API）。JWT Cookie验证使用真实JWT库。Redis状态用fakeredis模拟。
- **端到端测试**：真实浏览器+完整应用栈，仅mock不可控的外部依赖。**不复测**集成测试已覆盖的API契约和边界条件。

## 各层测试详细计划

### 集成测试

**目标**：Auth路由→Service→DB的组件协作与API契约验证，覆盖全部21项功能需求（FR-001至FR-021）。

| 集成点 | 测试文件 | 验证范围 |
|--------|----------|----------|
| Auth路由→用户服务→数据库（注册） | `tests/integration/001-register-login/test_register.py` | 表单提交→账户创建→JWT签发→重定向 |
| Auth路由→认证服务→数据库（登录） | `tests/integration/001-register-login/test_login.py` | 凭据提交→认证校验→JWT签发→重定向 |
| Auth路由→会话服务（退出登录） | `tests/integration/001-register-login/test_logout.py` | 退出请求→Cookie清除→重定向 |
| Auth中间件→路由守卫 | `tests/integration/001-register-login/test_auth_middleware.py` | JWT有效性校验、未认证拦截、已认证重定向 |
| 速率限制器→Auth路由 | `tests/integration/001-register-login/test_rate_limiter.py` | IP限速、账号锁定 |
| CSRF中间件→Auth路由 | `tests/integration/001-register-login/test_csrf_middleware.py` | CSRF Token校验机制 |

#### Mock 策略

| 依赖类型 | 处理方式 | 理由 |
|----------|----------|------|
| 外部API/服务 | `unittest.mock` / `pytest-mock` | 避免网络不确定性，仅测本功能逻辑 |
| 密码哈希 | 直接调用真实bcrypt/argon2 | 确定性算法，无外部依赖，不应mock |
| JWT签发 | 真实JWT库+固定secret | 签发逻辑需验证完整链路，但需确定性 |
| Redis状态 | `fakeredis` | 避免外部依赖，保持测试隔离 |
| 时间/定时器 | `freezegun` | 时间相关逻辑需要确定性 |

#### 测试数据隔离

- **Fixture 作用域**: 每个测试使用独立的内存SQLite数据库+独立的fakeredis实例，通过`pytest.fixture(scope="function")`保证
- **数据工厂**: 使用自定义builder模式创建测试用户、账户状态等
- **事务回滚**: 每个测试在事务中执行，测试完成后自动回滚清理状态

### 端到端测试

**目标**：完整用户浏览器流程的端到端验证。

| 场景 | 测试文件 | 路径 | 预期结果 |
|------|----------|------|----------|
| E2EP-001: 新用户注册→自动登录→进入控制台 | `tests/e2e/001-register-login/test_register_login_flow.spec.ts` | `/auth/register`→填写→提交→`/console` | 账户创建、Cookie签发、重定向成功 |
| E2EP-002: 正常登录流程 | `tests/e2e/001-register-login/test_register_login_flow.spec.ts` | `/auth/login`→填写凭据→提交→`/console` | 登录成功、Cookie签发、页面跳转 |
| E2EP-003: 登录失败与安全锁定 | `tests/e2e/001-register-login/test_login_failure.spec.ts` | `/auth/login`→错误凭据×5→第6次锁定 | 通用错误提示、密码框清空、锁定提示 |
| E2EP-004: 退出登录流程 | `tests/e2e/001-register-login/test_logout_flow.spec.ts` | `/console/*`→退出→`/auth/login` | Cookie清除、重定向、成功提示 |

#### Playwright 策略

- **页面交互**: 优先使用 `data-testid` 定位元素
- **状态验证**: 验证URL变化、页面内容、DOM属性、Cookie状态
- **等待策略**: 使用Playwright自动等待，避免硬编码sleep
- **视觉回归**: 不执行视觉回归截图对比（本功能关注功能正确性）

#### 端到端测试范围约束

- 端到端测试 **不复测** 集成测试已验证的接口契约和边界条件（如密码强度校验的各个子类、邮箱格式的各种变体）
- 端到端测试 仅覆盖「用户操作 → 系统响应」的完整路径
- 每条端到端测试 用例必须对应spec.md中的一个P1级别用户故事或关键验收场景

## 测试基础设施

### Fixture 设计

```python
# conftest.py 中的关键 fixture

@pytest.fixture
def test_db():
    """每个测试独立的内存 SQLite 数据库"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine("sqlite:///:memory:")
    # 创建所有表
    yield engine
    engine.dispose()

@pytest.fixture
def redis_client():
    """每个测试独立的 fakeredis 实例"""
    import fakeredis
    return fakeredis.FakeStrictRedis()

@pytest.fixture
def test_user(test_db):
    """使用 builder 模式创建标准用户"""
    # 构建并持久化用户
    yield user

@pytest.fixture
def locked_user(test_db, redis_client):
    """创建登录失败次数已达锁定阈值的用户"""
    # 构建用户 + 在 redis 中设置锁定状态
    yield user

@pytest.fixture
def api_client(test_db, redis_client):
    """认证无关的HTTP客户端"""
    # httpx ASGI client
    yield client

@pytest.fixture
def authenticated_client(api_client, test_user):
    """携带有效JWT Cookie的已认证HTTP客户端"""
    # 先执行登录获取Cookie，后续请求携带Cookie
    yield client_with_cookies
```

### 并行执行策略

- 集成测试可使用 pytest-xdist 并行执行（独立DB + 独立fakeredis实例）
- E2E测试串行执行（避免浏览器实例冲突）

## 项目结构

### 文档结构（本特性）

```text
specs/001-register-login/
├── plan.md              # 本文件（由 /speckit.plan 命令输出）
├── spec.md              # 测试规格说明
├── research.md          # 阶段 0 输出（技术调研）
└── tasks.md             # 测试执行任务分解（由 /speckit.tasks 命令生成）
```

### 测试工件结构（仓库根目录）

```text
tests/
├── cases/
│   └── 001-register-login/
│       ├── sc-register-new-account.md
│       ├── sc-login-authenticate.md
│       ├── sc-login-failure-lockout.md
│       └── sc-logout-session-clear.md
│
├── integration/
│   └── 001-register-login/
│       ├── test_register.py
│       ├── test_login.py
│       ├── test_logout.py
│       ├── test_auth_middleware.py
│       ├── test_rate_limiter.py
│       └── test_csrf_middleware.py
│
├── e2e/
│   └── 001-register-login/
│       ├── test_register_login_flow.spec.ts
│       ├── test_login_failure.spec.ts
│       └── test_logout_flow.spec.ts
│
├── fixtures/
│   ├── base-fixture.ts
│   ├── data/
│   │   └── auth-test-accounts.json
│   └── mocks/
│       └── external-services.json
```

## 测试可追溯性

### FR → Test 映射

| Spec 中的 FR | 测试层级 | 测试文件 | 测试用例 |
|--------------|----------|----------|----------|
| FR-001 | 集成测试 + E2E | `tests/integration/001-register-login/test_login.py` | ITP-001: 登录页表单元素验证 |
| FR-002 | 集成测试 | `tests/integration/001-register-login/test_login.py` | ITP-002: 凭据验证+JWT签发 |
| FR-003 | 集成测试 + E2E | `tests/integration/001-register-login/test_login.py` | ITP-003: 登录成功重定向 |
| FR-004 | 集成测试 | `tests/integration/001-register-login/test_login.py` | ITP-004: 空表单校验 |
| FR-005 | 集成测试 + E2E | `tests/integration/001-register-login/test_login.py` | ITP-005: 通用错误提示 |
| FR-006 | 集成测试 + E2E | `tests/integration/001-register-login/test_rate_limiter.py` | ITP-006: 账号锁定机制 |
| FR-007 | 集成测试 + E2E | `tests/integration/001-register-login/test_logout.py` | ITP-007: 退出登录+重定向 |
| FR-008 | 集成测试 + E2E | `tests/integration/001-register-login/test_login.py` | ITP-008: 记住我Cookie过期 |
| FR-009 | 集成测试 | `tests/integration/001-register-login/test_auth_middleware.py` | ITP-009: 受保护路由JWT校验 |
| FR-010 | 集成测试 | `tests/integration/001-register-login/test_csrf_middleware.py` | ITP-010: CSRF Token校验 |
| FR-011 | 集成测试 | `tests/integration/001-register-login/test_rate_limiter.py` | ITP-011: IP限速 |
| FR-012 | 集成测试 + E2E | `tests/integration/001-register-login/test_auth_middleware.py` | ITP-012: 已认证用户访问登录页重定向 |
| FR-013 | 集成测试 | `tests/integration/001-register-login/test_login.py` | ITP-013: 审计日志记录 |
| FR-014 | 集成测试 + E2E | `tests/integration/001-register-login/test_register.py` | ITP-014: 注册页表单元素验证 |
| FR-015 | 集成测试 + E2E | `tests/integration/001-register-login/test_register.py` | ITP-015: 用户名唯一性校验 |
| FR-016 | 集成测试 | `tests/integration/001-register-login/test_register.py` | ITP-016: 密码强度校验 |
| FR-017 | 集成测试 | `tests/integration/001-register-login/test_register.py` | ITP-017: 密码一致性校验 |
| FR-018 | 集成测试 | `tests/integration/001-register-login/test_register.py` | ITP-018: 邮箱格式校验 |
| FR-019 | 集成测试 + E2E | `tests/integration/001-register-login/test_register.py` | ITP-019: 注册成功自动登录重定向 |
| FR-020 | 集成测试 | `tests/integration/001-register-login/test_csrf_middleware.py` | ITP-020: 注册CSRF校验 |
| FR-021 | 集成测试 + E2E | `tests/integration/001-register-login/test_auth_middleware.py` | ITP-021: 已认证用户访问注册页重定向 |

### 用户故事 → Test 映射

| 用户故事 | 优先级 | 对应测试 | 独立验证方式 |
|------------|--------|----------|--------------|
| 注册新账户 | P1 | 集成:`test_register.py` + E2E:`test_register_login_flow.spec.ts` | 新用户名+密码+邮箱注册，验证账户创建、Cookie签发、重定向、各种校验拦截 |
| 输入凭据完成登录 | P1 | 集成:`test_login.py` + E2E:`test_register_login_flow.spec.ts` | 正确凭据登录，验证Cookie签发、重定向、记住我持久化 |
| 处理登录失败 | P1 | 集成:`test_login.py`,`test_rate_limiter.py` + E2E:`test_login_failure.spec.ts` | 错误凭据登录+连续失败锁定，验证通用错误提示、密码框清空、账号锁定 |
| 退出登录 | P2 | 集成:`test_logout.py` + E2E:`test_logout_flow.spec.ts` | 已登录状态退出，验证Cookie清除、重定向、成功提示、后退防护 |

## 测试风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| JWT Cookie 过期在E2E中难以模拟（无法冻结浏览器时间） | Cookie过期测试依赖真实等待时间 | E2E中使用极短过期时间(5秒)策略；集成测试中用freezegun冻结时间 |
| IP限速测试在E2E中难以模拟多IP | 从同一浏览器发出的请求共享IP地址 | 集成测试中用X-Forwarded-For头模拟IP；E2E中仅验证限速存在性，不验证多IP隔离 |
| 测试执行顺序依赖（如锁定状态污染） | 后续测试可能受前面测试遗留状态影响 | fakeredis每个测试独立实例；集成测试间无状态共享 |
| CSRF Token 获取流程增加测试复杂度 | 每个请求需要先获取Token再提交 | 封装CSRF-aware测试客户端fixture，自动处理Token获取 |

## 复杂度追踪

> **仅在宪章门禁存在需要证明的违反项时填写**

无违反项。所有宪章门禁检查项均为通过状态。

## 版本历史

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
| 2026-05-12 | v1.0 | 初始版本——基于测试规格和宪章创建测试计划 | Sisyphus |
