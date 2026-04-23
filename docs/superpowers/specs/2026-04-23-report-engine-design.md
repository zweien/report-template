# 通用报告模板引擎 — 设计文档

日期：2026-04-23

## 概述

将现有"项目申报书自动生成系统"原型重构为通用报告模板引擎，采用扁平模块 + 单一 Agent Skill 架构。

核心工作流：自然语言描述 → Agent 生成结构化 JSON → 用户确认 → 渲染输出 Word 文档。

## 目录结构

```
report-template/
├── src/
│   └── report_engine/
│       ├── __init__.py
│       ├── cli.py              # 命令行入口
│       ├── renderer.py         # 主渲染流程（TemplateRenderer）
│       ├── blocks.py           # Block 渲染函数注册表
│       ├── subdoc.py           # Subdoc 构建器
│       ├── validator.py        # JSON payload 校验
│       ├── style_checker.py    # 模板样式缺失检查
│       └── schema.py           # Pydantic model 定义
├── templates/
│   └── grant/
│       ├── template.docx
│       └── schema.yaml
├── data/
│   └── examples/
│       ├── grant_demo.json
│       └── grant_advanced_demo.json
├── output/
├── assets/
├── scripts/                    # 旧脚本保留供参考
├── docs/
├── skills/
│   └── report-generator/
│       ├── skill.md
│       ├── schemas/
│       └── prompts/
├── requirements.txt
└── README.md
```

## 核心模块职责

| 模块 | 职责 |
|---|---|
| `cli.py` | 参数解析、日志配置、调用渲染流程 |
| `renderer.py` | `TemplateRenderer` 类，编排整个渲染流程 |
| `blocks.py` | `BlockRegistry` 类 + 各 block 渲染函数，支持 `registry.register("new_type", fn)` |
| `subdoc.py` | 遍历 blocks 列表，调用 `BlockRegistry` 分发渲染 |
| `schema.py` | Pydantic model 定义 payload 结构，含校验规则 |
| `validator.py` | 调用 schema 校验 + 额外检查（图片路径、占位符覆盖） |
| `style_checker.py` | 读取模板样式列表，与 `style_map` 比对，报告缺失 |

调用关系：

```
cli.py → renderer.py (TemplateRenderer)
              ├── validator.py → schema.py
              ├── style_checker.py
              └── subdoc.py → blocks.py (BlockRegistry)
```

## Block 类型系统

### 注册表接口

```python
class BlockRegistry:
    def register(self, block_type: str, renderer_fn)
    def render(self, doc, block: dict, style_map: dict)
```

### 已实现 block 类型

| block_type | 必填字段 | 可选字段 |
|---|---|---|
| `heading` | `text` | `level` (默认2) |
| `paragraph` | `text` | — |
| `bullet_list` | `items` | — |
| `numbered_list` | `items` | — |
| `table` | `headers`, `rows` | `title`, `style`, `force_borders` |
| `image` | `path` | `width_cm`, `caption`, `legend` |
| `page_break` | — | — |

### 后续可扩展（本次不实现）

`quote`、`note`、`two_images_row`、`appendix_table`、`toc_placeholder`

## Pydantic Schema

```python
class Block(BaseModel):
    type: str
    # 各 block 类型特有字段（text/items/headers/rows/path 等）
    # 使用 model_config = ConfigDict(extra="allow") 允许动态字段
    # validator.py 中按 type 值做二次校验，确保必填字段存在
    model_config = ConfigDict(extra="allow")

class Section(BaseModel):
    id: str
    placeholder: str
    flag_name: Optional[str]
    enabled: bool = True
    blocks: List[Block]

class Attachment(BaseModel):
    id: str
    placeholder: str
    flag_name: Optional[str]
    enabled: bool = True
    title: Optional[str]
    blocks: List[Block]

class AttachmentsBundle(BaseModel):
    enabled: bool = True
    placeholder: str = "APPENDICES_SUBDOC"
    flag_name: str = "ENABLE_APPENDICES"
    page_break_between_attachments: bool = True
    include_attachment_title: bool = True

class Payload(BaseModel):
    context: Dict[str, str]
    sections: List[Section] = []
    attachments: List[Attachment] = []
    attachments_bundle: Optional[AttachmentsBundle]
    style_map: Optional[Dict[str, str]]
```

## 校验逻辑

`validator.py` 在 Pydantic 校验之后额外检查：
1. **Block 字段完整性**：按 `type` 值校验必填字段（如 `heading` 需 `text`，`table` 需 `headers`+`rows`）
2. **图片路径存在性**：所有 `image` block 的 `path` 文件是否存在（不存在则 warning，不阻断）
3. **模板占位符覆盖**：payload 中声明的 `placeholder` 是否在模板中能找到对应插槽
4. **样式完整性**：`style_map` 中引用的样式是否在模板中存在

## Agent Skill 工作流

```
用户描述项目信息（自然语言）
        │
        ▼
  Agent Skill 识别
        │  解析意图 → 匹配模板类型
        │  收集必要字段
        ▼
  生成结构化 JSON（按 schema.py 模型）
        │
        ▼
  展示 JSON 给用户确认
        │  用户可编辑修改
        ▼
  用户确认 → 调用 TemplateRenderer
        │
        ▼
  输出 .docx 到 output/
```

关键约束：
- Agent 只输出结构化 JSON，不控制 Word 格式
- 模板、样式、版式全部由 `.docx` 模板文件决定
- 用户必须确认 JSON 后才触发渲染

## 模板适配机制

### 模板目录约定

```
templates/<template_name>/
    ├── template.docx          # 必须
    ├── schema.yaml            # 可选
    └── README.md              # 可选
```

### schema.yaml 示例

```yaml
name: grant_proposal
description: 科研项目申报书模板
placeholders:
  - PROJECT_NAME
  - APPLICANT_ORG
  - PROJECT_LEADER
  - PROJECT_PERIOD
required_styles:
  - Heading 2
  - Heading 3
  - Body Text
  - Caption
  - ResearchTable
  - List Bullet
  - List Number
subdoc_slots:
  - RESEARCH_CONTENT_SUBDOC
  - RESEARCH_BASIS_SUBDOC
  - IMPLEMENTATION_PLAN_SUBDOC
  - APPENDICES_SUBDOC
```

模板发现：扫描 `templates/` 子目录，含 `template.docx` 即为可用模板。无 `schema.yaml` 时仍可渲染，跳过占位符和样式检查。

## CLI 接口

```bash
report-engine list-templates
report-engine validate --template grant --payload data/examples/grant_demo.json
report-engine check-styles --template grant
report-engine render --template grant --payload data/examples/grant_demo.json --output output/result.docx
```

## 错误处理

| 场景 | 处理方式 |
|---|---|
| JSON 格式错误 | 退出 + Pydantic 字段报错 |
| 图片文件不存在 | 警告 + 占位符文字，不阻断 |
| 模板样式缺失 | 退出 + 列出缺失样式 |
| 模板文件不存在 | 退出 + 路径提示 |
| block 类型不支持 | 退出 + 支持类型列表 |
| 占位符与模板不匹配 | 警告，继续渲染 |

## 实施优先级

| 阶段 | 内容 | 优先级 |
|---|---|---|
| 1 | 目录结构 + 模块骨架 | P0 |
| 2 | schema.py + validator.py | P0 |
| 3 | blocks.py：Block 注册表 + 7 种基础 block | P0 |
| 4 | subdoc.py + renderer.py | P0 |
| 5 | style_checker.py | P0 |
| 6 | cli.py | P1 |
| 7 | 最小可运行示例 | P1 |
| 8 | Agent Skill | P1 |
| 9 | 模板 schema.yaml + 规范文档 | P2 |
| 10 | 日志、图片告警、渲染摘要 | P2 |

## 不在本次范围

- 扩展 block 类型（quote/note/two_images_row 等）
- Web UI / API 服务
- 渲染结果快照对比
- 删除旧 scripts/ 目录
