# Online Editor 设计文档

日期：2026-04-25

## 概述

基于 BlockNote + Next.js 16 + FastAPI 的在线报告编辑器。用户上传 .docx 模板，系统解析章节结构，用户通过分段编辑器填充内容，导出为 .docx。

## 需求确认

| 项目 | 决策 |
|------|------|
| 目标用户 | 混合用户（技术人管模板，业务人填内容） |
| 编辑流程 | 从模板开始，不支持空白文档 |
| 模板来源 | 用户自行上传 .docx |
| 数据持久化 | 后端存储草稿 + 账号密码认证 |
| 导出方式 | 直接下载 .docx，无需实时预览 |
| 技术栈 | Next.js 16 + FastAPI + BlockNote + Zustand + shadcn/ui + Tailwind CSS |
| 部署 | 前端 :3070，后端 :8070，生产 Nginx 反代 |

## 系统架构

```
┌─────────────────────────────────────────────────┐
│                   Frontend (Next.js 16)          │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Auth     │ │ Template │ │ Editor           │ │
│  │ (login/  │ │ Manager  │ │ (BlockNote × N   │ │
│  │  register)│ │ (upload/ │ │  sections)       │ │
│  │          │ │  select) │ │                  │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│         │            │              │            │
│         └────────────┼──────────────┘            │
│                      │ HTTP/REST                 │
├──────────────────────┼──────────────────────────┤
│                   Backend (FastAPI)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Auth API │ │ Template │ │ Draft API        │ │
│  │ (JWT)    │ │ API      │ │ (CRUD + export)  │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Template │ │ BlockNote│ │ report-engine    │ │
│  │ Parser   │ │ ↔ Payload│ │ (渲染 .docx)     │ │
│  │          │ │ Converter│ │                  │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│                      │                           │
│              ┌───────┴───────┐                   │
│              │   SQLite/PG   │                   │
│              │   (users,     │                   │
│              │    templates, │                   │
│              │    drafts)    │                   │
│              └───────────────┘                   │
└─────────────────────────────────────────────────┘
```

## 数据模型

### 数据库表

```sql
users {
  id: UUID (PK)
  username: VARCHAR(50) UNIQUE
  password_hash: VARCHAR(255)
  created_at: TIMESTAMP
}

templates {
  id: UUID (PK)
  user_id: UUID (FK → users)
  name: VARCHAR(100)
  original_filename: VARCHAR(255)
  file_path: VARCHAR(500)
  parsed_structure: JSONB
  style_map: JSONB
  created_at: TIMESTAMP
}

drafts {
  id: UUID (PK)
  user_id: UUID (FK → users)
  template_id: UUID (FK → templates)
  title: VARCHAR(200)
  context: JSONB
  sections: JSONB
  attachments: JSONB
  status: ENUM('draft', 'exported')
  created_at: TIMESTAMP
  updated_at: TIMESTAMP
}
```

### parsed_structure 格式

```json
{
  "context_vars": ["PROJECT_NAME", "APPLICANT_ORG"],
  "sections": [
    {
      "id": "research_content",
      "placeholder": "RESEARCH_CONTENT_SUBDOC",
      "flag_name": "ENABLE_RESEARCH_CONTENT",
      "title": "一、研究内容与技术路线",
      "required_styles": ["Heading 2", "Body Text"]
    }
  ],
  "attachments_bundle": {
    "placeholder": "APPENDICES_SUBDOC",
    "flag_name": "ENABLE_APPENDICES"
  },
  "required_styles": ["Heading 2", "Body Text", "ResearchTable"]
}
```

## 模板解析流程

```
用户上传 .docx → 保存到磁盘 → 解析 XML 提取占位符/flag/样式
→ 识别章节边界 → 验证合法性 → 存入 templates 表
```

复用 `template_checker.py` 的解析能力，新增 `parse_section_boundaries()` 和 `extract_context_vars()`。

### 错误处理

| 场景 | 处理 |
|------|------|
| 文件不是 .docx | 400 |
| 无任何可识别章节 | 422，拒绝上传 |
| 缺少必需样式 | 200 + warnings |
| flag 不成对 | 422，拒绝上传 |

## BlockNote ↔ report-engine 转换

### BlockNote → report-engine（导出时）

| BlockNote type | report-engine type | 转换要点 |
|----------------|-------------------|----------|
| `heading` | `heading` | `props.level` → `level` |
| `paragraph` | `paragraph` | `content[].text` 拼接 |
| `bulletListItem` | `bullet_list` | 连续聚合为 `items[]` |
| `numberedListItem` | `numbered_list` | 连续聚合为 `items[]` |
| `table` | `table` | 提取行列 |
| `image` | `image` | 上传路径 |
| `quote` | `quote` | `content[].text` |
| `codeBlock` | `code_block` | `content[].text` |
| `pageBreak` | `page_break` | 直接映射 |

### 内联样式

段落 content 中任何 segment 有 styles（bold/italic）→ 转为 `rich_paragraph`，否则 `paragraph`。

### 不支持的类型

静默忽略，不报错。

## API 接口

### 认证

```
POST /api/auth/register    注册
POST /api/auth/login       登录 → JWT
GET  /api/auth/me          当前用户
```

### 模板

```
POST   /api/templates          上传模板
GET    /api/templates           列表
GET    /api/templates/{id}      详情
DELETE /api/templates/{id}      删除
```

### 草稿

```
POST   /api/drafts              新建
GET    /api/drafts              列表
GET    /api/drafts/{id}         详情
PATCH  /api/drafts/{id}         更新
DELETE /api/drafts/{id}         删除
POST   /api/drafts/{id}/export  导出 .docx
```

### 图片上传

```
POST   /api/upload/image        上传图片
```

认证方式：`Authorization: Bearer <jwt_token>`

## 前端页面与交互

### 页面路由

```
/login                    登录页
/register                 注册页
/dashboard                首页（模板+草稿列表）
/templates/upload         上传模板
/drafts/new?template=xxx  新建草稿
/drafts/{id}              编辑器页
```

### 编辑器布局

```
┌─────────────────────────────────────────────────────┐
│  顶栏：草稿标题 | 保存状态 | 导出按钮 | 用户菜单     │
├──────────┬──────────────────────────────────────────┤
│  章节    │         BlockNote 编辑器                  │
│  侧边栏  │                                          │
│          │  ┌────────────────────────────────────┐  │
│ ○ 封面   │  │ 一、研究内容与技术路线              │  │
│ ● 研究内容│  │                                    │  │
│ ○ 研究基础│  │ 1.1 研究目标                       │  │
│ ○ 实施计划│  │ 请输入内容...                      │  │
│ ○ 附件   │  └────────────────────────────────────┘  │
│          │                                          │
│  顶层变量 │                                          │
│  ─────── │                                          │
│ 项目名称: │                                          │
│ [______] │                                          │
└──────────┴──────────────────────────────────────────┘
```

### UI 设计规范（Linear 风格）

遵循 Linear 的设计哲学，核心原则：

**1. 深色主题优先**
- 默认深色背景（`#0A0A0B` 主背景，`#141415` 卡片/侧边栏）
- 浅色文字（`#E8E8ED` 主文字，`#8B8B93` 次要文字）
- 支持亮色主题切换，但深色为默认

**2. 克制的配色**
- 主色调：`#5B6CF0`（柔和蓝紫，用于选中态、按钮、链接）
- 成功：`#4ADE80`，警告：`#FBBF24`，错误：`#F87171`
- 其余全部灰阶，不使用多余颜色

**3. 信息密度与层次**
- 4px/8px 网格系统，所有间距为 4 的倍数
- 通过微妙的背景色差（而非边框线）划分区域
- 卡片/面板使用 `border: 1px solid rgba(255,255,255,0.06)` 极细边框
- 圆角统一 `6px`（小元素）或 `8px`（大面板）

**4. 字体**
- 主字体：Inter（或系统无衬线字体）
- 代码字体：JetBrains Mono / Fira Code
- 字号层级：12px（辅助）/ 13px（正文）/ 14px（标题）/ 16px（大标题）

**5. 交互反馈**
- 悬停：背景色微亮 `rgba(255,255,255,0.04)`
- 点击/选中：主色调半透明背景 `rgba(91,108,240,0.12)`
- 过渡动画：`150ms ease`，不使用弹性/跳跃效果
- 加载状态：骨架屏（Skeleton），不使用 spinner

**6. 键盘优先**
- Cmd/Ctrl+K 命令面板（跳转章节、搜索、导出等）
- Cmd/Ctrl+S 手动保存
- Cmd/Ctrl+Shift+E 导出
- Tab 在侧边栏 ↔ 编辑器之间切换

**7. 编辑器区域特化**
- BlockNote 编辑器区域背景与侧边栏有微妙色差（`#0F0F10` vs `#141415`）
- 章节标题行：左侧 2px 主色调竖线标记当前章节
- 空内容占位文字：`rgba(255,255,255,0.25)` 极淡灰色
- 侧边栏章节项：hover 时展开操作图标（删除、拖拽排序）

**8. 响应式**
- 最小支持宽度 1024px（桌面端优先）
- 侧边栏在窄屏下折叠为图标模式（仅显示章节序号）
- 移动端不作为 MVP 目标

### 状态管理（Zustand）

```typescript
interface DraftStore {
  draft: Draft | null;
  activeSection: string;
  isDirty: boolean;
  saveStatus: 'idle' | 'saving' | 'saved' | 'error';

  setActiveSection(id: string): void;
  updateSection(id: string, blocks: Block[]): void;
  updateContext(key: string, value: string): void;
  save(): Promise<void>;
  export(): Promise<void>;
}
```

### 保存策略

- 自动保存：停止编辑 3s 后 debounce
- 手动保存：Ctrl+S
- 离开提醒：未保存时弹确认

## 错误处理

| 场景 | 处理 |
|------|------|
| 自动保存失败 | 顶栏提示，保留本地数据 |
| 网络断开 | 本地继续，恢复后同步 |
| BlockNote 渲染异常 | 降级纯文本 |
| payload 校验失败 | 422 + 字段错误 |
| 模板样式缺失 | 422 + 缺失列表 |
| 渲染超时 | 504 |
| JWT 过期 | 401 + 自动刷新 |
| 访问他人资源 | 404 |

## 项目结构

### 前端（Next.js 16）

```
web/
├── app/
│   ├── layout.tsx
│   ├── login/page.tsx
│   ├── register/page.tsx
│   ├── dashboard/
│   │   ├── page.tsx
│   │   ├── templates/upload/page.tsx
│   │   └── drafts/
│   │       ├── new/page.tsx
│   │       └── [id]/page.tsx
├── components/
│   ├── editor/
│   │   ├── SectionEditor.tsx
│   │   ├── SectionSidebar.tsx
│   │   └── ContextPanel.tsx
│   ├── auth/
│   ├── template/
│   └── ui/                    # shadcn/ui
├── lib/
│   ├── api.ts
│   ├── auth.ts
│   ├── converter/
│   │   ├── blocknote-to-engine.ts
│   │   └── engine-to-blocknote.ts
│   └── stores/
│       ├── auth-store.ts
│       └── draft-store.ts
└── package.json
```

### 后端（FastAPI）

```
server/
├── main.py
├── routers/
│   ├── auth.py
│   ├── templates.py
│   ├── drafts.py
│   └── upload.py
├── services/
│   ├── auth_service.py
│   ├── template_parser.py
│   ├── draft_service.py
│   ├── converter.py
│   └── export_service.py
├── models/
│   ├── user.py
│   ├── template.py
│   └── draft.py
├── schemas/
│   ├── auth.py
│   ├── template.py
│   └── draft.py
├── database.py
├── config.py
└── requirements.txt
```

## 关键依赖

**前端**：next@16, react@19, @blocknote/react, zustand, shadcn/ui, tailwindcss, axios

**后端**：fastapi, uvicorn, sqlalchemy, python-jose, passlib, python-multipart, python-docx, report-engine

## 部署

**开发**：前端 localhost:3070，后端 localhost:8070

**生产**：Nginx (443) → 前端（Vercel）+ 后端 /api（VPS）

## 实现阶段

| Phase | 目标 | 预估 |
|-------|------|------|
| 1 | 后端 API 骨架 | 1-2 天 |
| 2 | 前端页面骨架 | 1-2 天 |
| 3 | BlockNote 编辑器 + 转换器 + 导出 | 3-5 天 |
| 4 | 打磨 MVP（自动保存、图片上传、快捷键） | 2-3 天 |
| **合计** | **可用 MVP** | **7-12 天** |

## 可选增强（后续）

- rich_paragraph 内联样式支持
- 表格编辑器增强（三线表样式切换）
- 草稿版本历史
- 模板分享
