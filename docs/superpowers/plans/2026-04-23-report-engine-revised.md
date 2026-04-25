# 通用报告模板引擎 Implementation Plan（修订版）

状态：**Phase 1 唯一实施基准**  
配套设计文档：`docs/superpowers/specs/2026-04-23-report-engine-design.md`  
当前行为基线说明：`docs/grant_render_advanced_readme.md`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## 0. 修订结论

**状态：** 方案通过，但必须按“平滑迁移优先”的方式执行。  
**核心调整：** 先保住现有可运行能力，再做模块化重构；Agent Skill 不纳入第一阶段交付。

本修订版保留原计划的总体目标，但针对评审中发现的主要风险做了收敛：

1. 不把当前仓库当成全新工程处理；
2. 先冻结现有行为，再重构；
3. 将“模板引擎工程化”和“Agent Skill 包装”拆成两个阶段；
4. 增加模板契约检查，而不只检查样式；
5. 样式检查增加**样式类型校验**，避免同名异类样式误判；
6. 明确保留对现有 payload 与脚本入口的兼容。

---

## 1. 目标与边界

### 1.1 第一阶段目标

将现有基于 `docxtpl + python-docx` 的项目申报书原型，重构为一个**本地可维护、模板驱动、可验证**的通用报告模板引擎，具备以下能力：

- 模块化渲染架构；
- payload 结构校验；
- 模板样式检查；
- 模板占位/开关契约检查；
- CLI 本地调试与渲染；
- 对现有脚本和示例数据的兼容迁移。

### 1.2 第一阶段不做的事

以下内容**不属于本阶段交付**：

- Agent Skill 封装；
- 大模型提示词编排工作流；
- 多模板生态管理界面；
- 超出当前已验证范围的大量新 block 类型；
- 对现有示例 payload 的破坏性改造。

### 1.3 阶段拆分

- **Phase 1：** 引擎工程化（schema / validator / template checks / renderer / cli / compat）
- **Phase 2：** Agent Skill 封装（确认流程、结构化生成、交互包装）

---

## 2. 当前基线与实施原则

### 2.1 当前已存在的可运行基线

仓库当前已经有一套工作原型，核心包括：

- `scripts/render_grant_advanced.py`
- `data/grant_payload_advanced_demo.json`
- `docs/grant_render_advanced_readme.md`

当前已支持：

- 多个章节 subdoc；
- 多个附件；
- 附件汇总区 `APPENDICES_SUBDOC`；
- 章节/附件开关；
- 以下 block 类型：
  - `heading`
  - `paragraph`
  - `bullet_list`
  - `numbered_list`
  - `table`
  - `image`
  - `page_break`

### 2.2 实施铁律

1. **先继承当前行为，再做抽象。**
2. **不要从零重写一个“更优雅但不兼容”的新系统。**
3. **主模板负责样式与固定框架，程序负责内容插入。**
4. **复杂章节继续用 subdoc，不退回到在主模板中堆复杂 Jinja。**
5. **渲染前必须先做校验。**

---

## 3. 目标目录结构

| File | Responsibility |
|---|---|
| `pyproject.toml` | 项目元数据、依赖、CLI 入口 |
| `src/report_engine/__init__.py` | 包初始化、版本号 |
| `src/report_engine/schema.py` | Pydantic payload 模型 |
| `src/report_engine/blocks.py` | BlockRegistry + 已支持 block 渲染器 |
| `src/report_engine/subdoc.py` | subdoc 构建器 |
| `src/report_engine/validator.py` | payload 校验与素材检查 |
| `src/report_engine/style_checker.py` | 模板样式存在性 + 样式类型检查 |
| `src/report_engine/template_checker.py` | 占位符 / flag / 附件插槽契约检查 |
| `src/report_engine/renderer.py` | 主渲染编排 |
| `src/report_engine/compat.py` | 旧字段 / 旧脚本兼容层 |
| `src/report_engine/cli.py` | `validate` / `check-template` / `render` |
| `scripts/render_grant_advanced.py` | 薄封装兼容入口 |
| `templates/grant/` | 模板文件 |
| `data/examples/` | 示例 payload |
| `tests/` | 单元与集成测试 |

### 目录约束

- **不要执行 `git init`**。当前仓库已存在版本历史，应在原仓库上增量演进。
- `schema.yaml` 可选，不作为第一阶段前置依赖。
- `requirements.txt` 可保留，但 `pyproject.toml` 作为依赖事实源。

---

## 4. 迁移契约（P0）

这一节是整个计划最重要的部分。

### 4.1 必须保证的兼容性

以下行为在第一阶段必须保留：

- 现有 `scripts/render_grant_advanced.py` 仍可调用；
- 现有示例 payload 可以继续渲染成功；
- 旧版顶层兼容字段仍可接受，例如：
  - `project_name`
  - `applicant_org`
  - `project_leader`
- 现有结构仍合法：
  - `context`
  - `sections`
  - `attachments`
  - `attachments_bundle`
  - `style_map`

### 4.2 迁移策略

1. 先把 `scripts/render_grant_advanced.py` 中现有能力抽取到 `src/report_engine/`；
2. 原脚本保留，但改成**薄封装 wrapper**；
3. 先写兼容测试，锁定当前行为；
4. 在兼容测试通过后，才逐步增加更严格的 validator / checker / CLI 默认行为。

### 4.3 第一阶段不做的破坏性变更

- 不重命名 `attachments`；
- 不强制要求模板必须有 `schema.yaml`；
- 不强制用户切到 Agent Skill 工作流。

---

## 5. 打包与脚手架

### Task 1: 安全脚手架与打包

**Files:**
- Create: `pyproject.toml`
- Create: `src/report_engine/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `output/.gitkeep`
- Create: `assets/.gitkeep`
- Modify: `requirements.txt`
- Modify: `.gitignore`

- [ ] **Step 1: 创建目录，不重置 git 仓库**

```bash
mkdir -p src/report_engine tests data/examples templates/grant output assets
```

- [ ] **Step 2: 创建 `pyproject.toml`**

```toml
[project]
name = "report-engine"
version = "0.1.0"
description = "Template-driven docx report engine"
requires-python = ">=3.10"
dependencies = [
  "docxtpl[subdoc]",
  "python-docx",
  "pydantic>=2.0",
  "pyyaml",
]

[project.optional-dependencies]
dev = ["pytest"]

[project.scripts]
report-engine = "report_engine.cli:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 3: 更新 `requirements.txt`（仅作便捷镜像）**

```txt
docxtpl[subdoc]
python-docx
pydantic>=2.0
pyyaml
pytest
```

- [ ] **Step 4: 创建 `src/report_engine/__init__.py`**

```python
"""Template-driven report engine."""

__version__ = "0.1.0"
```

- [ ] **Step 5: 更新 `.gitignore`**

```gitignore
__pycache__/
*.pyc
*.egg-info/
dist/
build/
output/*.docx
!output/.gitkeep
.venv/
.pytest_cache/
```

- [ ] **Step 6: 安装并验证**

```bash
pip install -e ".[dev]"
python -c "from report_engine import __version__; print(__version__)"
```

Expected: `0.1.0`

- [ ] **Step 7: 提交**

```bash
git add -A
git commit -m "chore: add package scaffolding for report engine"
```

---

## 6. 先冻结现有行为

### Task 2: 兼容基线测试

**Files:**
- Create: `tests/test_compat_render_advanced.py`
- Reuse: `scripts/render_grant_advanced.py`
- Reuse: 现有示例 payload

- [ ] **Step 1: 添加兼容测试，锁定当前脚本行为**
- [ ] **Step 2: 验证 advanced demo payload 可成功渲染**
- [ ] **Step 3: 验证被关闭的 section 不会输出内容**
- [ ] **Step 4: 验证 bundled appendices 仍可生成**
- [ ] **Step 5: 提交**

**说明：** 这是后续重构的安全网，没有这一步，不允许直接拆脚本。

---

## 7. Schema 模型

### Task 3: Pydantic payload 模型

**Files:**
- Create: `src/report_engine/schema.py`
- Create: `tests/test_schema.py`

### 模型设计要求

- 使用 `Field(default_factory=list)` / `Field(default_factory=dict)`，不要直接使用可变字面量默认值；
- `context` 使用 `Dict[str, Any]`，不要限制为全字符串；
- `Block` 允许额外字段，便于 block 扩展；
- 保持 `attachments` / `attachments_bundle` 与现有数据结构兼容。

### 推荐模型轮廓

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

- [ ] **Step 1: 先写测试**
- [ ] **Step 2: 实现模型**
- [ ] **Step 3: 确保旧 payload 仍可被接受**
- [ ] **Step 4: 提交**

---

## 8. Block 渲染器

### Task 4: 抽取 block registry 与现有 block 行为

**Files:**
- Create: `src/report_engine/blocks.py`
- Create: `tests/test_blocks.py`

### 第一阶段支持的 block 类型

- `heading`
- `paragraph`
- `bullet_list`
- `numbered_list`
- `table`
- `image`
- `page_break`

### 实现要求

- 与当前 `scripts/render_grant_advanced.py` 行为保持一致；
- 保留 block registry 的可扩展性；
- 保持缺图时插入占位提示的当前行为；
- 表格继续支持“可选表题 + 表格 + 尾随空段落”的现有策略。

- [ ] **Step 1: 迁移当前 block 逻辑到 `blocks.py`**
- [ ] **Step 2: 为每个 block 类型补测试**
- [ ] **Step 3: 补未知 block type 异常测试**
- [ ] **Step 4: 提交**

---

## 9. Subdoc 构建器

### Task 5: SubdocBuilder

**Files:**
- Create: `src/report_engine/subdoc.py`
- Create: `tests/test_subdoc.py`

### 要求

- 将 blocks 顺序渲染为一个新的 subdoc；
- 可选地在 subdoc 顶部加入标题；
- 支持 style_map 覆盖；
- 对不支持的 block 提供明确异常。

- [ ] **Step 1: 先写测试**
- [ ] **Step 2: 实现 `build_subdoc(...)`**
- [ ] **Step 3: 与旧脚本行为保持一致**
- [ ] **Step 4: 提交**

---

## 10. Payload Validator

### Task 6: Payload 校验与素材检查

**Files:**
- Create: `src/report_engine/validator.py`
- Create: `tests/test_validator.py`

### Validator 职责

- Pydantic 解析与基础校验；
- 各 block 类型的字段完整性校验；
- 图片路径检查；
- 占位符 / flag 重复检测；
- section / attachment id 重复检测；
- 可选的顺序字段合法性检查。

### 校验策略

- 结构性错误：直接 fail fast；
- 缺失图片：支持 warning / error 两种策略；
- 旧字段兼容：交给 `compat.py` 先归一化。

- [ ] **Step 1: 为合法 / 非法 payload 写测试**
- [ ] **Step 2: 实现解析与归一化入口**
- [ ] **Step 3: 实现 block 级字段检查**
- [ ] **Step 4: 提交**

---

## 11. 样式检查器（严格版）

### Task 7: Style Checker

**Files:**
- Create: `src/report_engine/style_checker.py`
- Create: `tests/test_style_checker.py`

### 这一版必须修正的问题

只检查“样式名存在”是不够的。因为当前引擎同时依赖：

- paragraph styles
- table styles

模板里可能存在同名但类型错误的样式。如果只按名称判断，会出现“检查通过，渲染异常”的情况。

### 必须检查的内容

- 样式是否存在；
- 样式类型是否正确；
- 缺失样式列表；
- 类型错误样式列表；
- `ok / missing / wrong_type / warnings` 等结果摘要。

### 最低样式要求

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

### 测试要求

不要再用 paragraph style 去模拟 table style 存在性。测试里必须区分样式类型。

- [ ] **Step 1: 写 all-present / missing / wrong-type 三类测试**
- [ ] **Step 2: 实现严格 style checker**
- [ ] **Step 3: 提交**

---

## 12. 模板契约检查器

### Task 8: Template Contract Checker

**Files:**
- Create: `src/report_engine/template_checker.py`
- Create: `tests/test_template_checker.py`

### 为什么必须加这一层

真实模板问题不只出在样式上，更常见的是：

- 漏了 `{{p XXX_SUBDOC}}`；
- `ENABLE_XXX` 与 payload 中 `flag_name` 不一致；
- 附件汇总区占位符不存在；
- 标题写在 `{%p if %}` 外部，导致关闭章节后标题还保留。

### 必须检查的内容

- 所有需要的 `{{p XXX_SUBDOC}}` 是否存在；
- 当 bundle 启用时，`APPENDICES_SUBDOC` 是否存在；
- 与 `ENABLE_XXX` 相关的模板用法是否至少满足约定；
- 对明显风险模式给 warning，例如“标题在条件块外”。

### 结果对象至少包含

- `ok`
- `missing_placeholders`
- `missing_flags` 或 `warnings`
- `notes`

- [ ] **Step 1: 写 section placeholder / appendix bundle 测试**
- [ ] **Step 2: 实现 checker**
- [ ] **Step 3: 提交**

---

## 13. 渲染编排与兼容层

### Task 9: Renderer + Compat

**Files:**
- Create: `src/report_engine/renderer.py`
- Create: `src/report_engine/compat.py`
- Create: `tests/test_renderer.py`
- Modify: `scripts/render_grant_advanced.py`

### Renderer 职责

- 加载模板；
- 归一化 payload；
- 构造 style_map；
- 构造 sections context；
- 构造 individual attachments context；
- 构造 bundled appendix context；
- 执行 render 并保存输出。

### Compat 层职责

- 将旧顶层字段映射到 `context`；
- 保留旧脚本的调用方式；
- 保证旧示例可继续运行。

### 关键约束

`scripts/render_grant_advanced.py` 最终应只做**薄封装**，而不是继续维护第二套实现。

- [ ] **Step 1: 将当前 orchestration 迁移到 `renderer.py`**
- [ ] **Step 2: 增加 `compat.py` 的归一化逻辑**
- [ ] **Step 3: 将旧脚本改写为 wrapper**
- [ ] **Step 4: 为 example payload 增加集成测试**
- [ ] **Step 5: 提交**

---

## 14. CLI 本地调试入口

### Task 10: CLI

**Files:**
- Create: `src/report_engine/cli.py`
- Create: `tests/test_cli.py`

### 第一阶段 CLI 命令

- `report-engine validate --payload data/examples/grant_advanced_demo.json`
- `report-engine check-template --template templates/grant/template.docx --payload ...`
- `report-engine render --template ... --payload ... --output output/demo.docx`

### CLI 行为约定

- `validate`：只做 payload 校验；
- `check-template`：做样式检查 + 模板契约检查；
- `render`：默认先执行 validation + template checks，再渲染；
- 容错模式必须显式开启，不默认静默 fallback。

### 可选增强（不是第一提交硬要求）

- `list-templates`
- `--strict-images`
- `--allow-style-fallback`

- [ ] **Step 1: 写 CLI 测试**
- [ ] **Step 2: 实现上述 3 个核心命令**
- [ ] **Step 3: 确保 `render` 默认触发前置检查**
- [ ] **Step 4: 提交**

---

## 15. 测试策略

### 必须具备的测试层级

1. **compat baseline tests**：锁定当前行为；
2. **schema tests**：验证 payload 模型；
3. **block tests**：覆盖每种 block；
4. **subdoc tests**：验证 subdoc 组合；
5. **validator tests**：验证结构正确性；
6. **style checker tests**：验证样式存在性与类型；
7. **template checker tests**：验证 placeholder / flag 契约；
8. **renderer integration tests**：结合示例 payload 跑通主流程；
9. **cli tests**：命令级 smoke test。

### 第一阶段最低验收标准

以下测试必须全部通过：

- schema tests
- renderer integration tests
- compat wrapper tests
- style checker tests
- template checker tests
- CLI smoke tests

---

## 16. 强制执行顺序

为避免重构失控，必须按这个顺序推进：

1. 安全脚手架与打包；
2. 兼容基线测试；
3. schema 模型；
4. block 抽取；
5. subdoc builder；
6. validator；
7. style checker；
8. template contract checker；
9. renderer + compat；
10. 旧脚本 wrapper 化；
11. CLI；
12. 文档更新。

**不允许跳过第 2 步直接重写。**  
**不允许把 Agent Skill 封装提前到第一阶段。**

---

## 17. 文档同步更新

### Task 11: 更新说明文档

**Files:**
- Modify: `README.md`
- Modify: `docs/grant_render_advanced_readme.md`
- Optional: `docs/report_engine_payload_spec.md`
- Optional: `docs/report_engine_template_spec.md`

### 需要补充的内容

- 新的本地运行命令；
- payload 兼容说明；
- 模板样式要求；
- 占位符 / flag / appendix contract 说明；
- “旧脚本已变为 wrapper”的迁移说明。

- [ ] **Step 1: 更新 README quick start**
- [ ] **Step 2: 更新 advanced rendering 文档，补充 CLI 与 checks**
- [ ] **Step 3: 如有必要，新增简明 payload/template spec**
- [ ] **Step 4: 提交**

---

## 18. 第二阶段预告（本计划不实现）

在第一阶段稳定后，才单独规划 Agent Skill 封装。第二阶段可能包括：

- 让用户先确认 payload 再渲染；
- 大模型生成结构化 JSON 的交互封装；
- skill 化复用接口；
- 更丰富的 block 类型，如：
  - `quote`
  - `note`
  - `two_images_row`

这一阶段必须另立计划，不与当前引擎重构混做。

---

## 19. Done Criteria

以下条件全部满足，才算本计划完成：

- 当前 advanced demo 仍可通过旧 wrapper 成功渲染；
- 新 package API 可渲染同一场景；
- 样式问题与模板契约问题可在渲染前暴露；
- CLI 支持 `validate` / `check-template` / `render`；
- 仓库表现为对现有原型的**连续演进**，而不是断裂式重写。
