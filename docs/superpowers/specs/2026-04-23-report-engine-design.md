# 通用报告模板引擎 — 设计文档

日期：2026-04-23
状态：Phase 1 设计基线（与 `docs/superpowers/plans/2026-04-23-report-engine-revised.md` 对齐）

## 1. 设计定位

本文档用于定义**第一阶段（Phase 1）** 的技术设计。

第一阶段目标不是重新发明一套全新的系统，而是将仓库中现有、已可运行的项目申报书渲染原型，工程化为一个**本地可维护、模板驱动、可验证、可兼容迁移**的通用报告模板引擎。

当前仓库已有运行基线，核心输入包括：

- `scripts/render_grant_advanced.py`
- `data/grant_payload_advanced_demo.json`
- `docs/grant_render_advanced_readme.md`

第一阶段的设计必须以这套现有能力为基线，遵循“**先冻结当前行为，再做模块化抽取**”的原则。

## 2. Phase 1 边界

### 2.1 本阶段要做的事

第一阶段交付以下能力：

- 模块化渲染架构；
- payload 结构校验；
- block 级字段校验；
- 图片路径检查；
- 模板样式检查；
- 模板占位符 / flag / appendix contract 检查；
- CLI 本地校验与渲染入口；
- 对现有脚本与现有 payload 的兼容迁移。

### 2.2 本阶段不做的事

以下内容**不属于第一阶段交付范围**：

- Agent Skill 封装；
- 自然语言到 JSON 的大模型交互流程；
- 多模板管理 UI；
- Web API 服务；
- 大量新增 block 类型；
- 对现有 payload 的破坏性结构改造。

> 说明：Agent Skill 将在 Phase 2 单独规划，不纳入本设计的实现范围。

## 3. 实施原则

1. **先继承当前行为，再做抽象。**
2. **不从零重写，不做断裂式替换。**
3. **主模板负责版式与样式，程序负责内容组织与插入。**
4. **复杂章节继续采用 subdoc，不退回主模板堆复杂 Jinja。**
5. **渲染前必须先校验 payload 与模板契约。**
6. **兼容旧脚本入口，旧示例需持续可运行。**

## 4. 目标目录结构

```text
report-template/
├── src/
│   └── report_engine/
│       ├── __init__.py
│       ├── blocks.py
│       ├── cli.py
│       ├── compat.py
│       ├── renderer.py
│       ├── schema.py
│       ├── style_checker.py
│       ├── subdoc.py
│       ├── template_checker.py
│       └── validator.py
├── templates/
│   └── grant/
│       └── template.docx
├── data/
│   └── examples/
├── scripts/
│   └── render_grant_advanced.py
├── tests/
├── docs/
├── README.md
├── pyproject.toml
└── requirements.txt
```

### 目录约束

- 在现有仓库中增量演进，**不要 `git init`**；
- `pyproject.toml` 作为依赖事实源；
- `requirements.txt` 可保留为便捷镜像；
- `schema.yaml` 不是 Phase 1 前置依赖，可选。

## 5. 当前基线能力

当前 advanced 原型已经支持：

- 多个章节 subdoc；
- 多个附件；
- `APPENDICES_SUBDOC` 附件汇总区；
- 章节/附件的 `enabled` 开关；
- 以下 block 类型：
  - `heading`
  - `paragraph`
  - `bullet_list`
  - `numbered_list`
  - `table`
  - `image`
  - `page_break`

Phase 1 的模块化重构必须保持上述行为不退化。

## 6. 核心模块职责

| 模块 | 职责 |
|---|---|
| `schema.py` | 定义 payload 的 Pydantic 模型 |
| `compat.py` | 旧字段归一化、旧入口兼容 |
| `validator.py` | payload 解析、block 级校验、重复项检查、素材检查 |
| `style_checker.py` | 模板样式存在性与样式类型检查 |
| `template_checker.py` | 模板 placeholder / flag / appendix contract 检查 |
| `blocks.py` | BlockRegistry 与 block 渲染器 |
| `subdoc.py` | 将 blocks 顺序渲染为 subdoc |
| `renderer.py` | 主渲染编排：归一化、检查、构建 context、渲染输出 |
| `cli.py` | 本地调试入口：`validate` / `check-template` / `render` |
| `scripts/render_grant_advanced.py` | 旧入口的薄封装 wrapper |

### 调用关系

```text
cli.py
  └── renderer.py
      ├── compat.py
      ├── validator.py
      │   └── schema.py
      ├── style_checker.py
      ├── template_checker.py
      └── subdoc.py
          └── blocks.py
```

## 7. 兼容迁移设计

### 7.1 兼容目标

第一阶段必须保证以下兼容性：

- 现有 `scripts/render_grant_advanced.py` 仍可调用；
- 现有 advanced demo payload 仍可渲染成功；
- 旧顶层兼容字段仍可接受，例如：
  - `project_name`
  - `applicant_org`
  - `project_leader`
- 现有结构仍合法：
  - `context`
  - `sections`
  - `attachments`
  - `attachments_bundle`
  - `style_map`

### 7.2 compat.py 职责

`compat.py` 负责：

- 将旧顶层字段映射到 `context`；
- 保留旧脚本调用方式；
- 为 validator 与 renderer 提供统一、归一化后的 payload 输入。

### 7.3 wrapper 约束

`scripts/render_grant_advanced.py` 在重构后应只保留为**薄封装 wrapper**，不得继续维护第二套独立实现。

## 8. Block 类型系统

### 8.1 注册表接口

```python
class BlockRegistry:
    def register(self, block_type: str, renderer_fn) -> None: ...
    def render(self, doc, block: dict, style_map: dict) -> None: ...
```

### 8.2 Phase 1 支持的 block 类型

| block_type | 必填字段 | 可选字段 |
|---|---|---|
| `heading` | `text` | `level` |
| `paragraph` | `text` | — |
| `bullet_list` | `items` | — |
| `numbered_list` | `items` | — |
| `table` | `headers`, `rows` | `title`, `style`, `force_borders` |
| `image` | `path` | `width_cm`, `caption`, `legend` |
| `page_break` | — | — |

### 8.3 行为约束

Phase 1 中 block 渲染行为应与现有 advanced 脚本保持一致，尤其包括：

- 缺图时插入占位提示文本；
- 表格支持“可选标题 + 表格 + 尾随空段落”；
- 支持通过 `style_map` 覆盖默认样式；
- 遇到未知 block type 明确抛错。

### 8.4 暂不实现的扩展类型

以下 block 仅作为后续扩展方向，不纳入本阶段：

- `quote`
- `note`
- `two_images_row`
- `appendix_table`
- `toc_placeholder`

## 9. Pydantic Schema 设计

### 9.1 设计原则

- 使用 `Field(default_factory=list)` / `Field(default_factory=dict)`，避免可变默认值；
- `context` 使用 `Dict[str, Any]`，不限制为纯字符串；
- `Block` 允许额外字段，便于不同 block 类型扩展；
- 保持 `attachments` / `attachments_bundle` 与现有结构兼容。

### 9.2 推荐模型轮廓

```python
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class Block(BaseModel):
    type: str
    model_config = ConfigDict(extra="allow")

class Section(BaseModel):
    id: str
    placeholder: str
    flag_name: Optional[str] = None
    enabled: bool = True
    blocks: List[Block] = Field(default_factory=list)
    order: Optional[int] = None

class Attachment(BaseModel):
    id: str
    placeholder: str
    flag_name: Optional[str] = None
    enabled: bool = True
    title: Optional[str] = None
    title_level: int = 2
    blocks: List[Block] = Field(default_factory=list)
    order: Optional[int] = None

class AttachmentsBundle(BaseModel):
    enabled: bool = True
    placeholder: str = "APPENDICES_SUBDOC"
    flag_name: str = "ENABLE_APPENDICES"
    page_break_between_attachments: bool = True
    include_attachment_title: bool = True

class Payload(BaseModel):
    context: Dict[str, Any] = Field(default_factory=dict)
    sections: List[Section] = Field(default_factory=list)
    attachments: List[Attachment] = Field(default_factory=list)
    attachments_bundle: Optional[AttachmentsBundle] = None
    style_map: Dict[str, str] = Field(default_factory=dict)
```

## 10. Payload Validator 设计

### 10.1 validator.py 职责

`validator.py` 负责：

- Pydantic 解析与基础结构校验；
- 各 block 类型字段完整性校验；
- 图片路径检查；
- section / attachment id 重复检测；
- placeholder / flag 重复检测；
- 可选顺序字段合法性检查。

### 10.2 校验策略

- **结构性错误**：直接 fail fast；
- **缺失图片**：支持 warning / error 两种策略；
- **旧字段兼容**：先由 `compat.py` 归一化，再进入 validator；
- **模板相关问题**：交由 `style_checker.py` 与 `template_checker.py`，不混进 schema 层。

## 11. 样式检查器设计

### 11.1 为什么要严格检查

只检查“样式名存在”是不够的，因为当前引擎同时依赖：

- paragraph styles
- table styles

如果模板里存在**同名但类型错误**的样式，仅按名称判断会出现“检查通过、渲染异常”的情况。

### 11.2 style_checker.py 必须检查的内容

- 样式是否存在；
- 样式类型是否正确；
- 缺失样式列表；
- 类型错误样式列表；
- `ok / missing / wrong_type / warnings` 等结果摘要。

### 11.3 最低样式要求

**段落样式：**

- `Heading 2`
- `Heading 3`
- `Body Text`
- `TableCaption`
- `FigureCaption`
- `Legend`
- `Figure Paragraph`
- `List Bullet`
- `List Number`

**表格样式：**

- `ResearchTable`

## 12. 模板契约检查器设计

### 12.1 需要单独引入的原因

真实模板风险通常不止是样式，还包括：

- 漏写 `{{p XXX_SUBDOC}}`；
- `ENABLE_XXX` 与 payload 中 `flag_name` 不一致；
- `APPENDICES_SUBDOC` 不存在；
- 标题写在 `{%p if %}` 外，导致关闭章节后标题仍残留。

### 12.2 template_checker.py 必须检查的内容

- payload 声明的 `{{p XXX_SUBDOC}}` 是否存在；
- 启用附件 bundle 时，`APPENDICES_SUBDOC` 是否存在；
- 与 `ENABLE_XXX` 相关的模板用法是否至少满足约定；
- 对明显风险模式给出 warning，例如“标题在条件块外”。

### 12.3 结果对象建议字段

- `ok`
- `missing_placeholders`
- `missing_flags`
- `warnings`
- `notes`

## 13. Subdoc 与 Renderer 设计

### 13.1 subdoc.py

`subdoc.py` 负责：

- 按顺序遍历 blocks；
- 调用 `BlockRegistry` 分发渲染；
- 可选在 subdoc 顶部追加标题；
- 支持 `style_map` 覆盖；
- 遇到未知 block 时明确抛错。

### 13.2 renderer.py

`renderer.py` 负责：

- 加载模板；
- 调用 `compat.py` 归一化 payload；
- 调用 validator / style checker / template checker；
- 构造 sections context；
- 构造 individual attachments context；
- 构造 bundled appendix context；
- 执行 render 并保存输出。

### 13.3 渲染前置约束

`render` 默认必须先执行：

1. payload validation；
2. style checks；
3. template contract checks；
4. 然后才允许真正渲染。

容错模式必须显式开启，不默认静默 fallback。

## 14. CLI 设计

### 14.1 Phase 1 CLI 命令

```bash
report-engine validate --payload data/examples/grant_advanced_demo.json
report-engine check-template --template templates/grant/template.docx --payload data/examples/grant_advanced_demo.json
report-engine render --template templates/grant/template.docx --payload data/examples/grant_advanced_demo.json --output output/demo.docx
```

### 14.2 CLI 行为约定

- `validate`：只做 payload 校验；
- `check-template`：做样式检查 + 模板契约检查；
- `render`：默认先执行 validation + template checks，再渲染；
- 可选增强项可以后补，但不是第一提交的硬要求。

### 14.3 可选增强（非 Phase 1 必做）

- `list-templates`
- `--strict-images`
- `--allow-style-fallback`

## 15. 测试策略

必须覆盖以下测试层级：

1. compat baseline tests；
2. schema tests；
3. block tests；
4. subdoc tests；
5. validator tests；
6. style checker tests；
7. template checker tests；
8. renderer integration tests；
9. CLI smoke tests。

### 最低验收标准

至少保证以下测试全部通过：

- compat wrapper tests
- schema tests
- renderer integration tests
- style checker tests
- template checker tests
- CLI smoke tests

## 16. 错误处理策略

| 场景 | 处理方式 |
|---|---|
| JSON / payload 结构错误 | 退出并输出 Pydantic / validator 错误 |
| 图片文件不存在 | 默认 warning；严格模式下可报错 |
| 模板样式缺失 | 退出并列出缺失项 |
| 模板样式类型错误 | 退出并列出 wrong-type 项 |
| 模板占位符缺失 | 退出并列出缺失 placeholder |
| 高风险模板写法 | 警告并给出 notes |
| block 类型不支持 | 退出并列出支持类型 |

## 17. Phase 2 预告（不在本设计实现范围）

在第一阶段稳定后，第二阶段才考虑：

- Agent Skill 封装；
- 自然语言输入到结构化 JSON 的交互层；
- 用户确认 payload 后再渲染的工作流包装；
- 更丰富的 block 类型。

## 18. 结论

Phase 1 的核心不是“设计一套更优雅的新系统”，而是把当前 advanced 原型整理成一个：

- **可验证**的 payload / template 输入面；
- **可维护**的模块化渲染内核；
- **可兼容迁移**的工程化本地工具链。

后续所有实现都应以“**连续演进，而非断裂重写**”为最高约束。