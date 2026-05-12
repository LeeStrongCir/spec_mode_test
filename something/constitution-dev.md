# Lee云平台 软件开发宪章

## 核心原则

### 一、技术栈约束

本宪章定义的技术栈为项目唯一标准，未经评审不得擅自偏离。

**后端**：
- 框架 FastAPI + Uvicorn，异步原生，路由使用 `async def`
- Python 3.12+，数据模型 SQLModel（Pydantic v2 + SQLAlchemy 2.0）
- 数据库 SQLite（单文件，v1 不引入外部数据库）
- 异步任务 FastAPI `BackgroundTasks`，不引入 Celery
- 缓存/限速 Python 内存 dict（单机部署，不引入 Redis）
- 包管理 pip + requirements.txt

**前端**：
- React 18 + TypeScript 5+，严格模式，禁用 `as any`、`@ts-ignore`
- 构建 Vite 5+，UI 组件库 Ant Design 5+
- 路由 React Router v6，状态管理 React Context（不引入额外状态库）
- HTTP Axios（统一拦截器处理 JWT 注入与错误响应）
- CSS Ant Design Design Token + CSS Modules（主题通过 ConfigProvider 定制；组件级 `.module.css` 文件与组件同目录放置，`styles/` 仅存全局 Token 配置）

**开发与部署**：
- 开发：`uvicorn --reload` + Vite DevServer，Vite proxy `/api/*` 到后端
- 生产：Nginx 反向代理（静态文件 + API 反代 + SSL）+ systemd 管理 FastAPI
- 代码质量：ESLint + Prettier（前端）、Ruff（后端）

---

### 二、项目结构规范

本项目采用 **Monorepo** 组织，根目录名为 `leecloud_platform/`，前后端同仓库，部署一体化。

```
leecloud_platform/
│
├── requirements.txt                   # 后端依赖
├── ruff.toml
│
├── backend/
│   ├── __init__.py
│   ├── main.py                        # FastAPI 入口，创建 app 实例 & 注册路由
│   ├── config.py                      # 配置常量（DB 路径、JWT 密钥等）
│   ├── database.py                    # SQLModel engine init，SQLite 连接
│   ├── security.py                    # JWT 签发/校验，密码哈希
│   ├── dependencies.py                # FastAPI 依赖注入（如 get_current_user）
│   ├── models/                        # SQLModel 表定义
│   ├── schemas/                       # Pydantic 请求/响应 DTO
│   ├── services/                      # 业务逻辑层，无框架依赖
│   └── api/                           # 路由层（APIRouter）
│       └── router.py                  # 聚合所有子路由到 /api/v1/*
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts                 # 包含 /api/* 反代到后端
│   ├── tsconfig.json
│   ├── eslint.config.js
│   └── src/
│       ├── main.tsx                   # React 挂载入口
│       ├── App.tsx                    # 布局壳 + ConfigProvider 主题 + 路由守卫
│       ├── components/                # 可复用 UI 组件（Layout、ErrorBoundary 等）
│       ├── pages/                     # 页面级组件
│       ├── hooks/                     # 自定义 Hooks
│       ├── services/                  # Axios 实例封装 + API 请求函数
│       ├── context/                   # React Context
│       ├── types/                     # 全局 TS 类型声明
│       ├── styles/                    # 仅存 Ant Design Token 全局配置 & 主题定制，不含组件级样式
│       └── utils/                     # 纯函数工具
│
├── deploy/
│   ├── nginx.conf                     # 生产反代配置
│   └── leecloud-platform.service       # systemd 托管
│
└── reqs/                              # 需求文档（只读）
```

**后端分层流向**：`api/ (路由) → schemas/ (DTO) → services/ (业务逻辑) → models/ (表)`
- **api/**：仅接收参数与返回响应，保持薄层
- **schemas/**：Pydantic 模型，请求校验 + 响应序列化
- **services/**：纯业务逻辑，无 FastAPI 依赖，可被异步任务复用
- **models/**：SQLModel 表定义，对应 SQLite schema

**前端数据流**：`pages/ (展示) → hooks/ (状态+副作用) → services/ (Axios) → 后端 API`

**命名约定**：
- 后端：snake_case（Python 标准），文件名与路由路径对应
- 前端：PascalCase（组件）、camelCase（工具/服务）、kebab-case（data-testid）

**CSS Modules 规范**：
- 组件级样式文件使用 `.module.css` 后缀，与对应组件同目录放置（如 `Button.tsx` + `Button.module.css`）
- 删除组件时一并清理对应样式文件，不得残留
- `styles/` 目录不承担组件级样式，仅存放全局 Token 配置、字体引入、全局重置样式

**Ant Design 默认样式覆盖**：
- Ant Design 组件自带的圆角、hover 过渡、背景色等默认样式**必须**通过 `ConfigProvider` 的 `theme.token` 及自定义 CSS 全面覆盖
- 禁止组件默认样式与自定义样式共存，避免视觉不一致
- 圆角、动画、hover 行为等须严格遵循第三章 UI/UX 规范，不得依赖 Ant Design 默认值

---

### 三、UI/UX 生成规范

所有 UI 组件基于 **Ant Design 5** 实现，通过 ConfigProvider 定制主题以遵循编辑极简主义（Editorial Minimalism）风格——暗色基调、克制用色、强烈排版层级。全局须保持统一调性，任何页面不得自行引入偏离整体风格的设计。

**字体排版**：
- 标题使用 Playfair Display / DM Serif Display
- 正文使用 JetBrains Mono / Geist / DM Sans
- ❌ 禁用：Inter、Roboto、Arial、system-ui、Space Grotesk
- 加载方式：字体文件存放于 `frontend/public/fonts/`，通过 `@font-face` 在 `styles/` 下全局 CSS 文件中声明引入，禁止使用 CDN 加载

**色彩体系**：
- 背景禁止纯黑 `#000000`，使用近黑色（如 `#0A0A0A`）
- 全局仅允许一种强调色，用于 CTA、链接、hover 高亮
- 通过 Ant Design Token 定义色彩，禁止在组件中硬编码色值
- ❌ 禁用：白底紫色渐变等 AI 俗套配色

**空间与构图**：
- Section 间距 80px~120px，保证呼吸感
- 圆角统一：全锐利（0px）或统一 8-12px，禁止混用
- 边框使用 0.5px/1px 半透明白色，营造玻璃质感

**动画与交互**：
- 仅使用 `transform` + `opacity`，保证 GPU 加速
- 入场动画：交错延迟（0.08s/元素），时长 600ms，缓动 `cubic-bezier(0.22, 0.6, 0, 1)`
- Hover：`translateY(-2px)` + 边框高亮
- ❌ 禁用：弹跳、旋转加载、卡通效果
- 优先 CSS 动画，React 场景下可使用 Framer Motion 作为补充

**质感细节**：
- 背景叠加极淡噪点纹理（SVG filter / 伪元素，opacity 0.03-0.05）
- 禁止单调纯色背景，每层须有微妙深度变化

### 四、data-testid 属性强制规范

所有 React (JSX/TSX) 组件中的可交互元素必须添加 `data-testid` 属性作为自动化测试标识。

**命名规则**：`[功能模块]-[元素类型]`（如 `username-input`、`login-button`），小写英文字母，连字符分隔。

**选择器优先级**：`data-testid` > `aria-label` > `role` + `name` > 其他（不推荐）。

**强制范围**：
- 全部可交互元素（antd 按钮、输入框、下拉框、复选框等）覆盖率须达 100%
- 登录、注册、主机管理等核心流程必须全覆盖
- 表单验证状态、异步加载/结果状态须有独立标识

**实现要求**：直接在 JSX/TSX 元素上添加 `data-testid` 属性，测试使用 Testing Library 的 `getByTestId` 查询。

**审查要求**：新增/修改 UI 组件必须同步更新标识，未验证 `data-testid` 覆盖率不得合并 PR。

---

## 治理

本宪法为项目最高级别的开发规范，所有代码提交、PR 审查、架构决策必须遵循。任何修改须经团队评审。

开发人员在实现功能时必须同时遵守以下四项要求：

**技术栈约束**：严格使用本宪章"技术栈"章节定义的技术与工具，不得擅自引入替代方案。

**项目结构**：严格遵循 Monorepo 目录结构，后端保持 api→schemas→services→models 分层，前端按类型分目录。

**UI/UX 实现**：严格基于 Ant Design 5 + ConfigProvider Token 定制暗色极简主题，保持全局风格统一。

**data-testid 覆盖**：所有可交互元素 100% 标注 `data-testid`，核心流程端到端可测。

未经上述四项验证的实现不得合并 PR。

**版本**：3.0.0 | **生效日期**：2026-05-08 | **最后修订**：2026-05-12
