# SC-04: Host Lifecycle (Stop/Start) - 手动测试用例

**优先级:** P2
**场景描述:** 验证 LECS Host 的异步状态流转：normal→shutting_down→stopped→starting→normal，以及过渡态按钮禁用逻辑
**状态机依据:** `data-model.md` 状态转换规则

**状态转换规则:**

| 当前状态 | 操作 | 中间态 | 过渡时长 | 目标状态 |
|----------|------|--------|----------|----------|
| normal | stop | shutting_down | ~10s (±5s) | stopped |
| stopped | start | starting | ~10s (±5s) | normal |
| failed | start | starting | ~10s (±5s) | normal |

**按钮禁用规则:** shutting_down/starting/creating/deleting 期间，stop/start/delete 全部禁用

---

## TC-030: 完整状态流转 normal→关机中→已关机

**优先级:** P2
**前置条件:**
- 已登录 LECS 管理平台
- 存在至少一台状态为 **normal** (正常) 的 Host

### 步骤

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 在 Host 列表页，确认目标 Host 状态列显示 **"正常"** (normal) | Host 状态 = `normal`，操作列 stop 按钮可点击 |
| 2 | 点击该 Host 的 **"停止"** (stop) 按钮 | - 弹出确认弹窗<br>- 点击确认<br>- 按钮立即变为禁用态 (disabled)<br>- stop/start/delete 全部不可点击 |
| 3 | 刷新页面或观察状态变化 | - 状态列更新为 **"关机中"** (shutting_down)<br>- stop/start/delete 按钮仍全部禁用<br>- 记录异步任务提交记录：后端应生成一条关机任务记录，状态为 pending/in_progress |
| 4 | 等待 **10 秒** (允许 **±5 秒** 容差，即 5~15 秒范围内) | - 状态列从 "关机中" 更新为 **"已关机"** (stopped)<br>- stop 按钮继续禁用<br>- **start** 按钮变为可点击 |
| 5 | 刷新页面 | 状态保持 "已关机" (stopped)，start 按钮可用 |
| 6 | 检查异步任务提交记录 | 存在一条关机任务的提交记录，包含：任务ID、提交时间、操作类型 (stop)、最终状态 (success) |

**预期最终状态:** Host 状态 = `stopped` (已关机)，start 按钮可用

---

## TC-031: 完整状态流转 已关机→启动中→正常

**优先级:** P2
**前置条件:**
- 已登录 LECS 管理平台
- 存在至少一台状态为 **stopped** (已关机) 的 Host（可通过 TC-030 得到）

### 步骤

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 在 Host 列表页，确认目标 Host 状态列显示 **"已关机"** (stopped) | Host 状态 = `stopped`，操作列 start 按钮可点击，stop 按钮禁用 |
| 2 | 点击该 Host 的 **"启动"** (start) 按钮 | - 弹出确认弹窗<br>- 点击确认<br>- 按钮立即变为禁用态 (disabled)<br>- stop/start/delete 全部不可点击 |
| 3 | 刷新页面或观察状态变化 | - 状态列更新为 **"启动中"** (starting)<br>- stop/start/delete 按钮仍全部禁用<br>- 记录异步任务提交记录：后端应生成一条开机任务记录，状态为 pending/in_progress |
| 4 | 等待 **10 秒** (允许 **±5 秒** 容差，即 5~15 秒范围内) | - 状态列从 "启动中" 更新为 **"正常"** (normal)<br>- **stop** 按钮变为可点击<br>- start 按钮变为禁用 |
| 5 | 刷新页面 | 状态保持 "正常" (normal)，stop 按钮可用 |
| 6 | 检查异步任务提交记录 | 存在一条开机任务的提交记录，包含：任务ID、提交时间、操作类型 (start)、最终状态 (success) |

**预期最终状态:** Host 状态 = `normal` (正常)，stop 按钮可用

---

## TC-032: 过渡态按钮全禁用 (shutting_down)

**优先级:** P2
**前置条件:**
- 已登录 LECS 管理平台
- 存在一台状态为 **normal** 的 Host
- 可通过触发 stop 操作使 Host 进入 shutting_down 过渡态

### 步骤

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 在 Host 列表页，找到状态为 **"正常"** 的 Host | stop 按钮可点击，start 按钮禁用 (或根据业务逻辑判断)，delete 按钮可点击 |
| 2 | 点击 **"停止"** 按钮并确认 | - 按钮变为禁用<br>- 状态变为 **"关机中"** (shutting_down) |
| 3 | 在 Host 处于 **"关机中"** (shutting_down) 状态下，检查操作列中所有按钮 | - **stop** 按钮: **禁用** ✅<br>- **start** 按钮: **禁用** ✅<br>- **delete** 按钮: **禁用** ✅<br>- 所有三个按钮均不可点击 |
| 4 | 尝试通过右键菜单 / 批量操作 / API 直接触发 停止/启动/删除 操作 | 后端应返回错误：Host 处于过渡态，不允许重复操作 (错误码/提示信息需与产品约定一致) |
| 5 | 等待状态流转到 **"已关机"** (stopped) | 过渡态结束后，按钮状态恢复：start 可用，stop/delete 按业务规则恢复 |

**预期验证点:** shutting_down 过渡态期间，stop/start/delete 三种按钮全部禁用，无法触发任何生命周期操作

---

## TC-033: 创建失败态可启动 failed→启动中→正常

**优先级:** P2
**前置条件:**
- 已登录 LECS 管理平台
- 存在至少一台状态为 **failed** (创建失败) 的 Host

### 步骤

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 在 Host 列表页，确认目标 Host 状态列显示 **"创建失败"** (failed) | Host 状态 = `failed`，操作列中 start 按钮可点击 |
| 2 | 点击该 Host 的 **"启动"** (start) 按钮 | - 弹出确认弹窗<br>- 点击确认<br>- 按钮立即变为禁用态 (disabled)<br>- stop/start/delete 全部不可点击 |
| 3 | 刷新页面或观察状态变化 | - 状态列更新为 **"启动中"** (starting)<br>- stop/start/delete 按钮仍全部禁用<br>- 记录异步任务提交记录：后端应生成一条开机 (重试) 任务记录，状态为 pending/in_progress |
| 4 | 等待 **10 秒** (允许 **±5 秒** 容差，即 5~15 秒范围内) | - 状态列从 "启动中" 更新为 **"正常"** (normal)<br>- **stop** 按钮变为可点击 |
| 5 | 刷新页面 | 状态保持 "正常" (normal)，stop 按钮可用 |
| 6 | 检查异步任务提交记录 | 存在一条开机任务的提交记录，包含：任务ID、提交时间、操作类型 (start/retry)、最终状态 (success) |
| 7 | 验证失败态恢复逻辑 | 确认 failed → starting → normal 的完整路径与 data-model.md 状态机定义一致，状态流转无跳跃 |

**预期最终状态:** Host 状态 = `normal` (正常)，stop 按钮可用

---

## 附录: 状态流转路径总览

```
normal ──[stop]──▶ shutting_down ──(~10s±5s)──▶ stopped
  ▲                                                     │
  │                                            [start]  │
  │                                                     ▼
  │                                            starting ──(~10s±5s)──▶ normal
  │         ▲                                                    ˄
  │         │                                           [start]  │
  failed ──┘                                                    │
        ─────────────────────────────────────────────────────────┘

  过渡态 (shutting_down/starting/creating/deleting):
    → stop 按钮: 禁用
    → start 按钮: 禁用
    → delete 按钮: 禁用
```

## 测试环境要求

- LECS 管理平台后端服务运行正常
- 至少准备以下状态的 Host:
  - 1 台 normal (正常)
  - 1 台 stopped (已关机)
  - 1 台 failed (创建失败) — 如环境中无 failed 状态 Host，需先构造或联系后端提供测试数据
- 可访问异步任务提交记录查询页面或 API
- 计时工具 (秒表或页面内计时)，用于验证过渡时长 ±5s 容差

## 验证通过标准

- TC-030 ~ TC-033 全部通过
- 所有状态机转换路径与实际表现一致
- 过渡态期间所有按钮禁用无遗漏
- 异步任务提交记录完整可查
- 过渡时长在 `5s ~ 15s` 容差范围内
