# data-testid 映射表 — 002-lecs-host

**Feature**: LECs Host Management
**Spec**: specs/002-lecs-host/spec.md
**命名规范**: `[module]-[element]` 命名约定

---

## UI 基础组件 (components/ui/) — 复用

| data-testid | 组件 | 文件 |
|---|---|---|
| `{dataTestId}` | `Input` (动态) | `components/ui/input.tsx` |
| `{dataTestId}` | `Button` (动态) | `components/ui/button.tsx` |
| `{dataTestId}` | `Alert` (动态) | `components/ui/alert.tsx` |

---

## Console 全局组件 (components/console/)

| data-testid | 组件 | 文件 | 说明 |
|---|---|---|---|
| `search-input` | `<input>` | `components/console/search-bar.tsx` | 搜索输入框 |
| `search-result-lecs` | `<button>` | `components/console/search-bar.tsx` | "LECS主机" 搜索结果 |

---

## 主机列表 (components/lecs/)

| data-testid | 组件 | 文件 | 说明 |
|---|---|---|---|
| `host-table` | `<table>` | `components/lecs/host-list.tsx` | 主机列表表格 |
| `host-row-{id}` | `<tr>` | `components/lecs/host-list.tsx` | 动态：每行主机，含 id 后缀 |
| `pagination` | `<div>` | `components/lecs/host-list.tsx` | 分页容器 |
| `btn-create-host` | `<Button variant="primary">` | `app/(console)/console/lecs-hosts/list/page.tsx` | "创建LECS主机" 创建按钮 |

---

## 操作按钮 (components/lecs/)

| data-testid | 组件 | 文件 | 说明 |
|---|---|---|---|
| `btn-{action}-{id}` | `<button>` | `components/lecs/operation-buttons.tsx` | 动态：`action` 为 `stop`/`start`/`delete`，`id` 为 ` hostId` 后缀 |

---

## 创建主机表单 (components/lecs/)

| data-testid | 组件 | 文件 | 说明 |
|---|---|---|---|
| `host-create-form` | `<form>` | `components/lecs/host-create-form.tsx` | 创建主机表单容器 |
| `form-error` | `<div role="alert">` | `components/lecs/host-create-form.tsx` | 表单级错误提示 |
| `panel-billing` | `<section>` | `components/lecs/host-create-form.tsx` | "Billing Mode" 区块 |
| `panel-hostname` | `<section>` | `components/lecs/host-create-form.tsx` | "Hostname" 区块 |
| `panel-credentials` | `<section>` | `components/lecs/host-create-form.tsx` | "Credentials" 区块 |
| `panel-instance` | `<section>` | `components/lecs/host-create-form.tsx` | "Instance Type" 区块 |
| `panel-os` | `<section>` | `components/lecs/host-create-form.tsx` | "OS Image" 区块 |
| `panel-ip` | `<section>` | `components/lecs/host-create-form.tsx` | "Network" 区块 |
| `panel-duration` | `<section>` | `components/lecs/host-create-form.tsx` | "Duration" 区块 |
| `input-hostname` | `<input>` | `components/lecs/host-create-form.tsx` | 主机名输入框 |
| `input-username` | `<input>` | `components/lecs/host-create-form.tsx` | 凭证用户名输入框 |
| `input-password` | `<input>` | `components/lecs/host-create-form.tsx` | 凭证密码输入框 |
| `select-plan` | `<select>` | `components/lecs/host-create-form.tsx` | 实例类型计划下拉框 |
| `select-os` | `<select>` | `components/lecs/host-create-form.tsx` | 操作系统镜像下拉框 |
| `input-ip` | `<input>` | `components/lecs/host-create-form.tsx` | IP地址输入框 |
| `input-mask` | `<input>` | `components/lecs/host-create-form.tsx` | 子网掩码输入框 |
| `btn-duration-{m}` | `<button>` | `components/lecs/host-create-form.tsx` | 动态：`m` 为 1/2/3/6/12/24 月时长 |
| `cost-summary` | `<div>` | `components/lecs/host-create-form.tsx` | 费用汇总区块 |
| `btn-submit-create` | `<button type="submit">` | `components/lecs/host-create-form.tsx` | "Create Host" 提交按钮 |

---

## 确认对话框 (components/lecs/)

| data-testid | 组件 | 文件 | 说明 |
|---|---|---|---|
| `confirm-dialog-overlay` | `<div>` | `components/lecs/confirm-dialog.tsx` | 购买确认弹窗遮罩层 |
| `confirm-dialog-cancel` | `<Button variant="ghost">` | `components/lecs/confirm-dialog.tsx` | "Cancel" 取消按钮 |
| `confirm-dialog-confirm` | `<Button variant="primary">` | `components/lecs/confirm-dialog.tsx` | "Confirm" 确认按钮 |

---

## 删除对话框 (components/lecs/)

| data-testid | 组件 | 文件 | 说明 |
|---|---|---|---|
| `delete-dialog-overlay` | `<div>` | `components/lecs/delete-dialog.tsx` | 删除确认弹窗遮罩层 |
| `delete-dialog-cancel` | `<Button variant="ghost">` | `components/lecs/delete-dialog.tsx` | "Cancel" 取消按钮 |
| `delete-dialog-confirm` | `<Button variant="ghost">` | `components/lecs/delete-dialog.tsx` | "Delete" 确认按钮 |

---

## 组件无 data-testid

| 组件 | 文件 | 说明 |
|---|---|---|
| `StatusBadge` | `components/lecs/status-badge.tsx` | 状态标签组件 |

---

## 统计

| 类别 | 数量 |
|---|---|
| **data-testid 总数** | 28 (含 3 组动态值) |
| **表单 (form)** | 1 |
| **输入框 (input)** | 6 |
| **下拉框 (select)** | 2 |
| **按钮 (button)** | 5 + `btn-{action}-{id}` (动态) + `btn-duration-{m}` (动态) |
| **对话框/弹窗 (dialog)** | 6 |
| **区块/面板 (panel)** | 7 |
| **表格 (table)** | 1 |
| **行 (tr)** | `host-row-{id}` (动态) |
| **其他** | 2 (cost-summary, pagination) |

---

## 命名约定

所有 data-testid 遵循 `[module]-[element]` 格式：
- **主机列表模块**：`host-*`, `btn-*`, `pagination`
- **创建主机模块**：`input-*`, `select-*`, `panel-*`, `cost-*`, `btn-*`
- **对话框模块**：`*-dialog-*`
- **全局搜索**：`search-*`

### 动态 data-testid 规则

| 模式 | 示例 | 说明 |
|---|---|---|
| `btn-{action}-{id}` | `btn-stop-abc12345` | 操作按钮：action∈{stop,start,delete}, id=hostId |
| `btn-duration-{m}` | `btn-duration-12`, `btn-duration-24` | 时长按钮：m∈{1,2,3,6,12,24} |
| `host-row-{id}` | `host-row-abc12345` | 表格行：id=hostId |
