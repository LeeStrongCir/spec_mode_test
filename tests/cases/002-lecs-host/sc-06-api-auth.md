# SC-06: API 认证与授权 — 手动测试用例

> **功能模块**: LECS 主机管理
> **测试编号**: SC-06
> **覆盖范围**: API 认证拦截 (401)、RBAC 授权 (403)、统一 JSON 响应格式、配额/超时/并发边界场景
> **优先级**: P2
> **创建日期**: 2026-05-12
> **前置公共条件**:
> - 测试环境已部署 Lee 云平台控制台及 LECS 主机管理服务
> - 测试账号已准备：
>   - 普通用户 A（`user_a`，密码已知，无管理员权限）
>   - 普通用户 B（`user_b`，密码已知，无管理员权限）
>   - 管理员用户（`admin`，密码已知，拥有 system:admin 角色）
> - API 测试工具可用（Postman / curl / 浏览器开发者工具 Network 面板）
> - 数据库可访问（用于预置数据状态）

---

## TC-050: API 认证拦截

**优先级**: P2
**目标**: 验证未携带认证凭证或携带无效凭证时，API 返回 401 未授权

### TC-050-01: 无认证凭证访问列表接口

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 已获取 API 基础 URL（如 `https://console.example.com`） | 打开 Postman 或终端，构造请求：`GET https://console.example.com/api/v1/lecs-hosts`，**不携带任何 Cookie / Authorization Header** | 请求已准备，无任何认证信息 |
| 2 | 发送上述 GET 请求 | 点击 Send（Postman）或执行 curl 命令 | HTTP 状态码 = **401 Unauthorized** |
| 3 | 检查响应体 | 查看返回的 JSON | 响应体包含：<br>• `success`: `false`<br>• `error_code`: 字符串（如 `"UNAUTHORIZED"` 或 `"AUTH_001"`）<br>• `error_message`: 字符串（如"未认证，请先登录"或类似描述）<br>• **不包含** `data` 字段 |
| 4 | 验证 Content-Type | 检查响应头 `Content-Type` | 值为 `application/json` 或 `application/json; charset=utf-8` |

### TC-050-02: 过期/无效的 JWT Cookie 访问 API

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 用户 A 已登录，通过浏览器开发者工具获取当前有效的 JWT Cookie 值 | 复制 Cookie 中的 JWT token（如 `lecs_jwt=eyJ...`） | 获得有效的 JWT 字符串 |
| 2 | 等待 JWT 自然过期 **或** 通过数据库/token 服务使该 token 失效 | 确认 token 已过期或已被服务端吊销 | Token 失效状态已确认 |
| 3 | 构造请求：`GET /api/v1/lecs-hosts`，在 Cookie 头中携带**已过期**的 JWT | 使用 Postman / curl 发送请求，设置 `Cookie: lecs_jwt=<过期token>` | HTTP 状态码 = **401 Unauthorized** |
| 4 | 检查响应体 | 查看返回的 JSON | 响应体包含：<br>• `success`: `false`<br>• `error_code`: 字符串（如 `"TOKEN_EXPIRED"` 或 `"AUTH_002"`）<br>• `error_message`: 字符串（如"认证凭证已过期，请重新登录"） |
| 5 | 构造请求：`GET /api/v1/lecs-hosts`，Cookie 中携带**完全伪造**的 JWT（随机字符串） | 发送请求，设置 `Cookie: lecs_jwt=invalid_random_string` | HTTP 状态码 = **401 Unauthorized** |
| 6 | 检查响应体 | 查看返回的 JSON | 响应体包含：<br>• `success`: `false`<br>• `error_code`: 字符串（如 `"TOKEN_INVALID"` 或 `"AUTH_003"`）<br>• `error_message`: 字符串（如"认证凭证无效"） |

### TC-050-03: 过期 JWT 访问其他 API 端点（任意接口）

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 持有已过期的 JWT Cookie（同 TC-050-02） | 构造请求：`POST /api/v1/lecs-hosts/{任意已知主机ID}/stop`，携带过期 JWT Cookie | HTTP 状态码 = **401 Unauthorized** |
| 2 | 检查响应体 | 查看返回的 JSON | 响应体包含 `success: false`, `error_code`, `error_message`，且 **不** 包含 `data` |
| 3 | 构造请求：`DELETE /api/v1/lecs-hosts/{任意已知主机ID}`，携带过期 JWT Cookie | 发送请求 | HTTP 状态码 = **401 Unauthorized** |
| 4 | 检查响应体 | 查看返回的 JSON | 响应体格式同上，`success: false`，含错误码与错误消息 |

---

## TC-051: 普通用户仅能查询自身主机

**优先级**: P2
**目标**: 验证 RBAC — 普通用户只能看到自己创建的主机，管理员可查看所有用户的主机

### TC-051-01: 普通用户 A 查询自身主机

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 通过数据库预置数据：<br>• 用户 A 名下有 3 台活跃主机（状态含 normal、stopped）<br>• 用户 B 名下有 2 台活跃主机<br>• 所有主机 `deleted_at IS NULL` | 确认数据库中主机归属已正确设置 | DB 查询确认：用户 A 有 3 台，用户 B 有 2 台 |
| 2 | 用户 A 登录控制台，获取有效 JWT Cookie | 使用用户 A 的凭证登录，记录返回的 Cookie | 获取到用户 A 的有效 JWT |
| 3 | 构造请求：`GET /api/v1/lecs-hosts?page=1&page_size=50`，携带用户 A 的 JWT Cookie | 发送请求 | HTTP 状态码 = **200 OK** |
| 4 | 检查响应体中的 `data` 数组 | 查看 `data` 字段内容 | • `data` 数组长度 = **3**<br>• 每条记录中的 `owner_id`（或 `user_id`）字段值 = 用户 A 的 ID<br>• **不存在** 属于用户 B 的主机记录 |
| 5 | 检查响应体中的 `success` 字段 | 查看 `success` 字段值 | `success`: `true` |
| 6 | 检查 `pagination` 字段 | 查看 `pagination` 对象 | 包含 `total`（总记录数）、`page`、`page_size` 字段 |

### TC-051-02: 管理员查询所有用户主机

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 同 TC-051-01 前置条件：用户 A 有 3 台、用户 B 有 2 台活跃主机 | 确认预置数据不变 | DB 确认 5 台活跃主机存在 |
| 2 | 管理员用户登录控制台，获取有效 JWT Cookie | 使用管理员凭证登录 | 获取到管理员的有效 JWT |
| 3 | 构造请求：`GET /api/v1/lecs-hosts?page=1&page_size=50`，携带管理员 JWT Cookie | 发送请求 | HTTP 状态码 = **200 OK** |
| 4 | 检查响应体中的 `data` 数组 | 查看 `data` 字段内容 | • `data` 数组长度 = **5**<br>• 记录中同时包含用户 A 和用户 B 的主机<br>• 每条记录的 `owner_id` 涵盖两个用户的 ID |
| 5 | 检查响应体中的 `success` 字段 | 查看 `success` 字段值 | `success`: `true` |

### TC-051-03: 普通用户尝试通过 API 直接访问他人主机（越权）

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 用户 A 和用户 B 各有活跃主机，已知用户 B 某台主机的 ID（如 `host-b-001`） | 通过数据库或管理员接口获悉该 ID | 确认主机 ID `host-b-001` 归属于用户 B |
| 2 | 用户 A 登录，获取有效 JWT Cookie | 登录用户 A | 获得用户 A 的有效 JWT |
| 3 | 构造请求：`GET /api/v1/lecs-hosts/host-b-001`（或带查询参数尝试获取用户 B 的主机详情），携带用户 A 的 JWT | 发送请求 | HTTP 状态码 = **403 Forbidden** |
| 4 | 检查响应体 | 查看返回的 JSON | 响应体包含：<br>• `success`: `false`<br>• `error_code`: 字符串（如 `"FORBIDDEN"` 或 `"RBAC_001"`）<br>• `error_message`: 字符串（如"无权访问该资源"或"权限不足"） |

---

## TC-052: 统一 JSON 响应格式

**优先级**: P2
**目标**: 验证所有 API 遵循统一的 JSON 响应结构 — 成功响应含 `success` + `data`，失败响应含 `success` + `error_code` + `error_message`

### TC-052-01: 成功响应的统一格式验证

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 管理员已登录，获取有效 JWT Cookie | 确认 JWT 有效 | 持有有效认证凭证 |
| 2 | 构造请求：`GET /api/v1/lecs-hosts?page=1&page_size=10`，携带 JWT | 发送 GET 请求 | HTTP 状态码 = **200 OK** |
| 3 | 检查响应体顶层字段 | 解析返回的 JSON | 响应体顶层**必须**包含：<br>• `success`: 值为 `true`（boolean 类型）<br>• `data`: 值为数组或对象（payload） |
| 4 | 检查 `data` 字段内部结构 | 查看 `data` 内容 | • 列表接口：`data` 为数组，每个元素包含主机字段（`id`、`host_name`、`status`、`billing_mode`、`private_ip` 等）<br>• 分页信息可能独立为 `pagination` 对象或与 `data` 同级 |
| 5 | 构造请求：`POST /api/v1/lecs-hosts`，携带完整合法创建参数和 JWT | 发送 POST 请求创建一台主机 | HTTP 状态码 = **201 Created** 或 **202 Accepted** |
| 6 | 检查创建成功响应体 | 解析返回的 JSON | 响应体包含：<br>• `success`: `true`（boolean）<br>• `data`: 包含新主机的 `id`、`host_name`、`status`（"creating" 或 "创建中"） |

### TC-052-02: 失败响应的统一格式验证 — 参数校验错误

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 管理员已登录，获取有效 JWT Cookie | 确认 JWT 有效 | 持有有效认证凭证 |
| 2 | 构造请求：`POST /api/v1/lecs-hosts`，携带**缺少必填字段**的 JSON body（如省略 `host_name`），携带 JWT | 发送请求，Content-Type: application/json | HTTP 状态码 = **400 Bad Request** |
| 3 | 检查响应体 | 解析返回的 JSON | 响应体**必须**包含：<br>• `success`: `false`（boolean）<br>• `error_code`: 字符串（如 `"VALIDATION_ERROR"` 或 `"PARAM_INVALID"`）<br>• `error_message`: 字符串（描述性错误信息，如"主机名为必填字段"）<br>• **不包含** `data` 字段（或 `data` 为 `null`） |
| 4 | 构造请求：`POST /api/v1/lecs-hosts`，`host_name` 设置为 `_abc`（非法格式），携带 JWT | 发送请求 | HTTP 状态码 = **400 Bad Request** |
| 5 | 检查响应体 | 解析返回的 JSON | 响应体格式同上，`success: false`，含 `error_code` 和 `error_message` |

### TC-052-03: 失败响应的统一格式验证 — 资源不存在

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 管理员已登录，获取有效 JWT Cookie | 确认 JWT 有效 | 持有有效认证凭证 |
| 2 | 构造请求：`GET /api/v1/lecs-hosts/nonexistent-host-id-99999`，携带 JWT | 发送请求 | HTTP 状态码 = **404 Not Found** |
| 3 | 检查响应体 | 解析返回的 JSON | 响应体包含：<br>• `success`: `false`<br>• `error_code`: 字符串（如 `"NOT_FOUND"` 或 `"RESOURCE_404"`）<br>• `error_message`: 字符串（如"主机不存在"） |

### TC-052-04: 失败响应的统一格式验证 — 状态冲突（403/409）

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 管理员已登录，获取有效 JWT；存在一台状态为"已关机"（stopped）的主机 `host-stopped-01` | 确认主机状态为 stopped | 目标主机存在且状态为已关机 |
| 2 | 构造请求：`POST /api/v1/lecs-hosts/host-stopped-01/stop`，携带 JWT | 对已关机的主机发送关机请求 | HTTP 状态码 = **403 Forbidden**（或 409 Conflict） |
| 3 | 检查响应体 | 解析返回的 JSON | 响应体包含：<br>• `success`: `false`<br>• `error_code`: 字符串（如 `"STATE_CONFLICT"` 或 `"INVALID_OPERATION"`）<br>• `error_message`: 字符串（如"当前状态不允许关机"） |

---

## EC-001: 配额上限创建拦截

**优先级**: P2
**严重程度**: 高
**目标**: 验证用户活跃主机数达到 100 台上限后，创建新主机请求被拒绝

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 通过数据库脚本或管理接口，将用户 A 的活跃主机数设置为 **100 台**（状态含 normal、stopped、creating、failed 等，`deleted_at IS NULL`） | 执行 SQL 或管理接口批量插入 100 条主机记录 | 数据库中确认：`SELECT COUNT(*) FROM lecs_hosts WHERE owner_id = 'user_a' AND deleted_at IS NULL` 返回 100 |
| 2 | 用户 A 登录控制台，获取有效 JWT Cookie | 登录用户 A | 获得有效 JWT |
| 3 | **前端验证**：用户 A 访问 `/console/lecs-hosts/create`，填写完整创建表单，点击"立即购买"→"确定" | 提交创建请求 | 前端弹出提示：**"主机数量达到上限"**，请求未发送至后端或被前端拦截 |
| 4 | **API 验证**：构造请求 `POST /api/v1/lecs-hosts`，携带合法创建参数和用户 A 的 JWT | 直接向 API 发送 POST 请求 | HTTP 状态码 = **409 Conflict**（或 403 Forbidden） |
| 5 | 检查 API 响应体 | 解析返回的 JSON | 响应体包含：<br>• `success`: `false`<br>• `error_code`: 字符串（如 `"QUOTA_EXCEEDED"` 或 `"HOST_LIMIT_REACHED"`）<br>• `error_message`: 字符串中包含 **"主机数量达到上限"** 或语义等价描述 |
| 6 | 清理数据：删除用户 A 的 1 台主机（`deleted_at` 设为当前时间），使活跃主机数变为 99 | 执行清理操作 | 活跃计数降为 99 |
| 7 | 再次通过 API 提交创建请求 | `POST /api/v1/lecs-hosts`，携带合法参数和 JWT | HTTP 状态码 = **201** 或 **202**，创建成功，响应体 `success: true` |

---

## EC-002: 创建超时降级

**优先级**: P2
**严重程度**: 高
**目标**: 验证后台创建任务超过 60 秒未完成时，主机状态强制降级为"创建失败"，前端停止轮询

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 用户 A 已登录，获取有效 JWT；确认当前活跃主机数 < 100 | 确认配额未满 | 可以正常发起创建 |
| 2 | 用户 A 访问 `/console/lecs-hosts/create`，填写完整表单，点击"立即购买"→"确定" | 提交创建请求 | 创建请求发送成功，重定向至列表页 `/console/lecs-hosts/list` |
| 3 | 在列表页观察新主机 | 找到刚创建的主机行 | 主机状态显示为 **"创建中"**（creating），前端开始轮询该主机状态 |
| 4 | **模拟超时**：通过数据库将对应后台任务的执行时间模拟为 > 60 秒（或暂停后台 worker 进程使其无法完成） | 不干预前端，仅让后台任务超时 | 系统内部记录超时事件 |
| 5 | 等待 **超过 60 秒**（从创建请求提交时刻起计时） | 持续观察列表页中该主机的状态变化 | 主机状态从 **"创建中"** 自动变更为 **"创建失败"**（failed） |
| 6 | 检查前端行为 | 观察 Network 面板或前端日志 | 前端**停止对该主机的轮询**请求，不再持续调用状态查询接口 |
| 7 | 检查数据库记录 | 查询该主机记录 | `status` 字段值为 `"failed"`，`error_message`（如有）字段包含超时相关描述 |
| 8 | 验证后续操作可用性 | 查看该主机行的操作按钮 | "删除"按钮可点击，"关机"和"启动"按钮置灰（符合 failed 态操作矩阵） |

---

## EC-003: 并发操作防冲突

**优先级**: P2
**严重程度**: 高
**目标**: 验证主机处于过渡态（如 shutting_down / starting）时，重复的 `/stop` 或 `/start` 请求被拒绝，返回 409/403

### EC-003-01: 关机中再次调用 /stop

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 管理员已登录，获取有效 JWT；存在一台状态为"正常"（normal）的主机 `host-normal-01` | 确认主机状态为 normal | 目标主机可执行关机操作 |
| 2 | 构造请求：`POST /api/v1/lecs-hosts/host-normal-01/stop`，携带 JWT | 发送第一次关机请求 | HTTP 状态码 = **202 Accepted**，主机状态进入 **"关机中"**（shutting_down） |
| 3 | **立即**（在 1-2 秒内，主机仍处于 shutting_down 态时），再次构造请求：`POST /api/v1/lecs-hosts/host-normal-01/stop`，携带相同 JWT | 发送第二次关机请求 | HTTP 状态码 = **409 Conflict**（或 403 Forbidden） |
| 4 | 检查第二次请求的响应体 | 解析返回的 JSON | 响应体包含：<br>• `success`: `false`<br>• `error_code`: 字符串（如 `"STATE_CONFLICT"` 或 `"OPERATION_IN_PROGRESS"`）<br>• `error_message`: 字符串（如"主机正在关机中，请勿重复操作"） |
| 5 | 等待主机自然过渡到"已关机"（stopped） | 观察状态变化 | 状态变为 "已关机" |

### EC-003-02: 关机中再次调用 /start

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 管理员已登录，获取有效 JWT；存在一台状态为"正常"（normal）的主机 `host-normal-02` | 确认主机状态为 normal | 目标主机可执行关机操作 |
| 2 | 构造请求：`POST /api/v1/lecs-hosts/host-normal-02/stop`，携带 JWT | 发送关机请求 | HTTP 状态码 = **202 Accepted**，主机进入 **"关机中"** |
| 3 | **立即**（主机仍处于 shutting_down 态时），构造请求：`POST /api/v1/lecs-hosts/host-normal-02/start`，携带 JWT | 发送启动请求 | HTTP 状态码 = **409 Conflict**（或 403 Forbidden） |
| 4 | 检查响应体 | 解析返回的 JSON | 响应体包含：<br>• `success`: `false`<br>• `error_code`: 字符串（如 `"STATE_CONFLICT"` 或 `"INVALID_TRANSITION"`）<br>• `error_message`: 字符串（如"主机正在关机中，无法启动"） |

### EC-003-03: 启动中再次调用 /stop

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 管理员已登录，获取有效 JWT；存在一台状态为"已关机"（stopped）的主机 `host-stopped-02` | 确认主机状态为 stopped | 目标主机可执行启动操作 |
| 2 | 构造请求：`POST /api/v1/lecs-hosts/host-stopped-02/start`，携带 JWT | 发送启动请求 | HTTP 状态码 = **202 Accepted**，主机进入 **"启动中"**（starting） |
| 3 | **立即**（主机仍处于 starting 态时），构造请求：`POST /api/v1/lecs-hosts/host-stopped-02/stop`，携带 JWT | 发送关机请求 | HTTP 状态码 = **409 Conflict**（或 403 Forbidden） |
| 4 | 检查响应体 | 解析返回的 JSON | 响应体包含：<br>• `success`: `false`<br>• `error_code`: 字符串<br>• `error_message`: 字符串（如"主机正在启动中，无法关机"） |

### EC-003-04: 并发请求 — 同时发送多个 /stop（Race Condition）

| 步骤 | 前置条件 | 操作 | 预期结果 |
|------|----------|------|----------|
| 1 | 管理员已登录，获取有效 JWT；存在一台状态为"正常"（normal）的主机 `host-normal-03` | 确认主机状态为 normal | 目标主机可执行关机操作 |
| 2 | 准备 3 个并行的 API 客户端（如 3 个 Postman Tab / 3 个 curl 进程） | 同时向 `POST /api/v1/lecs-hosts/host-normal-03/stop` 发送请求（误差控制在 500ms 内） | 3 个请求几乎同时到达服务端 |
| 3 | 检查 3 个请求的响应 | 分别查看每个请求的 HTTP 状态码和响应体 | - **有且仅有 1 个**请求返回 **202 Accepted**<br>- 其余 **2 个**请求返回 **409 Conflict**（或 403 Forbidden）<br>- 所有 403/409 响应体格式统一：`success: false`，含 `error_code` 和 `error_message` |
| 4 | 检查数据库中该主机的最终状态 | 查询 `lecs_hosts` 表 | 主机最终进入 **"已关机"** 状态，且**只有一条**关机操作记录 |

---

## 附录：预期响应体结构参考

### 成功响应格式

```json
{
  "success": true,
  "data": {
    // 具体业务数据，如主机对象或主机列表数组
  },
  "pagination": {
    // 分页元数据（仅列表接口）
    "total": 10,
    "page": 1,
    "page_size": 10
  }
}
```

### 失败响应格式

```json
{
  "success": false,
  "error_code": "ERROR_CODE_STRING",
  "error_message": "人类可读的错误描述信息"
}
```

### 常见错误码映射表

| HTTP 状态码 | 错误码 (`error_code`) | 说明 |
|-------------|----------------------|------|
| 401 | `UNAUTHORIZED` / `TOKEN_EXPIRED` / `TOKEN_INVALID` | 认证相关 |
| 403 | `FORBIDDEN` / `RBAC_DENIED` / `STATE_CONFLICT` | 授权/状态冲突 |
| 400 | `VALIDATION_ERROR` / `PARAM_INVALID` | 参数校验失败 |
| 404 | `NOT_FOUND` / `RESOURCE_NOT_FOUND` | 资源不存在 |
| 409 | `QUOTA_EXCEEDED` / `OPERATION_IN_PROGRESS` / `STATE_CONFLICT` | 配额/并发冲突 |

---

## 测试执行记录模板

| 用例编号 | 执行日期 | 执行人 | 环境 | 结果 (Pass/Fail) | 备注/Bug ID |
|----------|----------|--------|------|-------------------|-------------|
| TC-050-01 | | | | | |
| TC-050-02 | | | | | |
| TC-050-03 | | | | | |
| TC-051-01 | | | | | |
| TC-051-02 | | | | | |
| TC-051-03 | | | | | |
| TC-052-01 | | | | | |
| TC-052-02 | | | | | |
| TC-052-03 | | | | | |
| TC-052-04 | | | | | |
| EC-001 | | | | | |
| EC-002 | | | | | |
| EC-003-01 | | | | | |
| EC-003-02 | | | | | |
| EC-003-03 | | | | | |
| EC-003-04 | | | | | |

---

*文档版本: v1.0 | 最后更新: 2026-05-12*
