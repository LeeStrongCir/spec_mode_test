# SC-04: 用户退出登录 (Logout) - 测试用例

**来源规范**: LeeCloud Platform Spec v1.0  
**关联功能需求**: FR-007 (退出登录), FR-013 (安全控制)  
**优先级**: P2  
**创建日期**: 2026-05-13  
**测试环境要求**: Chrome/Firefox 浏览器, 已部署的 LeeCloud 平台, 有效测试账号

---

## 数据准备

| 准备项 | 说明 |
|--------|------|
| 测试账号 | 已注册且状态正常的用户账号（如 `test_logout@example.com` / `Test123456`） |
| 登录状态 | 用户已完成登录，持有有效的 JWT Cookie（Cookie 名称通常为 `access_token` 或 `Authorization`） |
| Cookie 验证方法 | 浏览器 DevTools → Application → Cookies → 查看 `access_token` 字段存在且值非空；或使用 `document.cookie` 控制台命令验证 |
| 目标页面 | 用户当前位于 `/console/dashboard` 或其他受保护的路由页面 |

---

## TC-030: 正常退出登录流程

**优先级**: P2  
**功能点**: FR-007  
**测试类型**: 功能测试

### 前置条件

| 序号 | 条件 |
|------|------|
| 1 | 用户已成功登录系统，JWT Cookie 有效 |
| 2 | 用户当前位于 `/console/*` 下的任意受保护页面（如 `/console/dashboard`） |
| 3 | 页面右上角可见用户头像及下拉菜单 |

### 操作步骤

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 将鼠标悬停或点击右上角用户头像 | 头像下方展开下拉菜单，菜单中包含 "退出登录" 选项 |
| 2 | 点击下拉菜单中的 "退出登录" 按钮 | 系统弹出确认对话框（如设计有），或直接执行退出流程 |
| 3 | （如有确认弹窗）点击 "确认" 按钮 | JWT Cookie 被后端失效化处理，前端 Cookie 中的 `access_token` 被清除或标记为过期 |
| 4 | 观察页面跳转及提示信息 | - 页面自动重定向至 `/auth/login`<br>- 页面顶部或弹窗显示成功提示：**"您已成功退出登录"**<br>- URL 栏显示为 `/auth/login` |
| 5 | 打开浏览器 DevTools → Application → Cookies → 检查当前域下的 Cookie 列表 | - `access_token`（或相关 JWT Cookie）已不存在，或值为空<br>- 无其他认证相关的 Cookie 残留 |
| 6 | 尝试直接访问 `/console/dashboard`（手动输入 URL 并回车） | 页面被重定向至 `/auth/login`，并显示 "请先登录" 或类似提示信息 |

### 备注

- 验证 JWT Cookie 清除时，需确认 `HttpOnly`、`Secure`、`SameSite` 属性在清除前后的一致性
- 如有多个 Cookie（如 `access_token`、`refresh_token`），需全部清除

---

## TC-031: 退出登录后浏览器后退按钮保护

**优先级**: P2  
**功能点**: FR-007, FR-013  
**测试类型**: 安全测试

### 前置条件

| 序号 | 条件 |
|------|------|
| 1 | 用户已成功完成 TC-030 的全部步骤 |
| 2 | 用户当前位于 `/auth/login` 页面（由 TC-030 步骤 4 重定向而来） |
| 3 | 浏览器地址栏显示为 `/auth/login` |

### 操作步骤

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 点击浏览器左上角的 "后退" 按钮（或快捷键 `Alt + ←` / `Cmd + [`） | 页面仍停留在 `/auth/login`，URL 不发生变化 |
| 2 | 观察后退操作后的页面内容 | - 页面内容仍为登录表单，不显示之前 `/console/*` 下的任何页面内容<br>- 不出现历史页面缓存 |
| 3 | 连续点击 "后退" 按钮 3 次 | 页面始终停留在 `/auth/login` 或更早的非受保护页面（如首次访问的登录页），无法通过浏览器缓存访问 `/console/*` |
| 4 | 检查页面响应头（DevTools → Network → 查看 `/auth/login` 请求的 Response Headers） | 响应头包含防止缓存的指令：<br>- `Cache-Control: no-store, no-cache, must-revalidate`<br>- `Pragma: no-cache` |
| 5 | 在控制台执行 `history.back()` 或使用 `window.history.length` 查看历史记录 | 无法通过 JavaScript 方式回退到受保护的 `/console/*` 页面；或回退后触发路由守卫重新跳转至 `/auth/login` |
| 6 | （可选）尝试使用浏览器 "前进" 按钮向前导航 | 无法回到退出前的 `/console/*` 页面，因为会话已失效且缓存已禁止 |

### 备注

- 此测试验证前端路由守卫 + HTTP 缓存控制头的双重防护机制
- 某些浏览器（如 Chrome）有 BFCache 特性，可能需要额外验证 `pageshow` 事件中的会话检查逻辑
- 若前端使用 SPA（Single Page Application），还需验证 `window.onpopstate` 事件是否正确处理

---

## 测试执行记录

| 用例编号 | 执行状态 | 执行人 | 执行日期 | 缺陷编号 | 备注 |
|----------|----------|--------|----------|----------|------|
| TC-030 | ☐ 未执行 / ☐ 通过 / ☐ 失败 | | | | |
| TC-031 | ☐ 未执行 / ☐ 通过 / ☐ 失败 | | | | |
