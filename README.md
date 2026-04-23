# report-template

一个基于 `docxtpl + python-docx` 的 Word 文档生成项目，当前正从“项目申报书自动生成原型”演进为一个**通用报告模板引擎**。

项目的核心思路是：

- **主模板负责样式、版式和固定框架**
- **程序负责结构化内容组织与插入**
- **复杂正文使用 subdoc 生成，不把复杂富文本逻辑堆到主模板里**
- **大模型只负责生成结构化 payload，不直接控制 Word 格式**

---

## 1. 项目定位

本项目面向这样的场景：

- 不同单位或不同项目有各自的 `.docx` 母版模板
- 正文中包含多段文字、标题、列表、表格、图片、图题、图例、分页符等复杂内容
- 某些章节或附件需要按开关启用/禁用
- 需要兼顾**模板复用、内容结构化、渲染可验证、后续可接入大模型**

当前的 Phase 1 目标是：

> 在**保持现有 advanced 原型行为兼容**的前提下，把它工程化为一个可维护、可验证、可测试、可扩展的本地模板引擎。

---

## 2. 当前状态

目前仓库已经具备以下能力：

- 多章节 subdoc
- 多附件
- 附件汇总区 `APPENDICES_SUBDOC`
- 章节 / 附件开关
- payload 校验
- 模板样式检查
- 模板占位符 / flag 契约检查
- CLI 本地校验与渲染入口
- 兼容旧脚本入口的 wrapper
- examples 示例 payload
- 第一批测试骨架

当前支持的 block 类型（共 18 种）：

| 类型 | 说明 |
|------|------|
| `heading` | 标题（支持 level 2/3） |
| `paragraph` | 普通段落 |
| `rich_paragraph` | 富文本段落（支持 bold/italic/sub/sup） |
| `bullet_list` | 无序列表 |
| `numbered_list` | 有序列表 |
| `table` | 表格（支持标题、样式、边框） |
| `image` | 图片（支持宽度、图题、图例） |
| `page_break` | 分页符 |
| `note` | 注释块（带"注："前缀） |
| `quote` | 引用块（支持来源说明） |
| `two_images_row` | 双图并排 |
| `appendix_table` | 附录表格 |
| `checklist` | 清单（☐/☑ 勾选） |
| `horizontal_rule` | 水平分隔线 |
| `toc_placeholder` | 目录域占位 |
| `code_block` | 代码块（等宽字体 + 灰底） |
| `formula` | 公式（LaTeX 输入，三级降级） |
| `columns` | 多列布局（嵌套 block） |

---

## 3. 核心原则

- 先冻结当前行为，再重构
- 不从零重写，不做断裂式替换
- 主模板负责样式与固定框架，程序负责内容插入
- 复杂章节继续使用 subdoc
- 渲染前先做 validation + template checks
- 旧脚本最终收敛为 wrapper，而不是长期维护两套实现

---

## 4. 当前目录结构

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
├── scripts/
│   ├── __init__.py
│   ├── render_grant_demo.py
│   └── render_grant_advanced.py
├── data/
│   ├── grant_payload_demo.json
│   ├── grant_payload_advanced_demo.json
│   └── examples/
│       ├── README.md
│       ├── grant_demo.json
│       └── grant_advanced_demo.json
├── docs/
│   ├── grant_render_readme.md
│   ├── grant_render_advanced_readme.md
│   ├── grant_template_upgrade_guide.md
│   ├── report_engine_payload_spec.md
│   ├── report_engine_template_spec.md
│   ├── template_check_troubleshooting.md
│   ├── phase1_status.md
│   └── superpowers/
│       ├── plans/
│       └── specs/
├── tests/
├── templates/
│   └── grant/
├── output/
├── assets/
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 5. 模块职责

### `src/report_engine/`

- `schema.py`：Pydantic payload 模型
- `compat.py`：旧字段与旧结构兼容归一化
- `validator.py`：payload 校验、block 字段检查、图片检查、重复项检查
- `style_checker.py`：模板样式存在性与样式类型检查
- `template_checker.py`：模板 placeholder / flag / appendix 契约检查
- `blocks.py`：block 注册表与 block 渲染器
- `subdoc.py`：按顺序将 blocks 渲染为 subdoc
- `renderer.py`：主渲染编排
- `cli.py`：本地命令行入口

### `scripts/`

- `render_grant_advanced.py`：旧 advanced 渲染脚本的兼容 wrapper
- `render_grant_demo.py`：早期基础版原型脚本，保留作参考

---

## 6. 安装

建议使用 Python 3.10 及以上。

### 使用 `pyproject.toml` 安装

```bash
pip install -e ".[dev]"
```

### 或使用 `requirements.txt`

```bash
pip install -r requirements.txt
```

安装后可以使用 CLI：

```bash
report-engine --help
```

---

## 7. 快速开始

### 7.1 校验示例 payload

```bash
report-engine validate --payload data/examples/grant_advanced_demo.json
```

### 7.2 检查模板

```bash
report-engine check-template \
  --template path/to/your_template.docx \
  --payload data/examples/grant_advanced_demo.json
```

### 7.3 渲染输出

```bash
report-engine render \
  --template path/to/your_template.docx \
  --payload data/examples/grant_advanced_demo.json \
  --output output/demo.docx
```

### 7.4 运行测试

```bash
pytest
```

---

## 8. 关于模板

当前项目默认假设你已经准备好一个 `.docx` 模板，并在其中预留：

- 标量占位符，例如 `{{PROJECT_NAME}}`
- subdoc 插槽，例如 `{{p RESEARCH_CONTENT_SUBDOC }}`
- 条件开关，例如 `{%p if ENABLE_RESEARCH_CONTENT %}`
- 附件汇总区，例如 `{{p APPENDICES_SUBDOC }}`

推荐样式至少包括：

### 段落样式

- `Heading 2`
- `Heading 3`
- `Body Text`
- `Caption`
- `Legend`
- `Figure Paragraph`
- `List Bullet`
- `List Number`
- `Note`（注释块）
- `Quote`（引用块）
- `CodeBlock`（代码块）
- `Checklist`（清单）

### 表格样式

- `ResearchTable`
- `AppendixTable`（附录表格，可选，fallback 到 ResearchTable）

### 制作模板的文档指引

如果你要从零制作一个新模板，按以下顺序阅读：

1. **`docs/report_engine_template_spec.md`** — 模板规范（必读），包含占位符、条件开关、样式要求、fallback 链
2. **`docs/report_engine_payload_spec.md`** — payload 规范，了解每种 block 需要什么字段，模板需要配套什么样式
3. **`scripts/build_test_template.py`** — 模板生成脚本，可作为参考实现
4. **`templates/grant/README.md`** — 现有模板的约定说明

如果要从现有模板改造：

- **`docs/grant_template_upgrade_guide.md`** — 从基础版升级到 advanced 版的指南
- **`docs/template_check_troubleshooting.md`** — check-template 报错时的排查手册

### 重要说明

不要把**基础版模板**直接拿去校验 **advanced payload**。

如果你的模板只支持：

- 单个 `RESEARCH_CONTENT_SUBDOC`
- 没有 `RESEARCH_BASIS_SUBDOC`
- 没有 `IMPLEMENTATION_PLAN_SUBDOC`
- 没有 `APPENDICES_SUBDOC`
- 没有对应 `ENABLE_XXX` 条件开关

那么对它运行：

```bash
report-engine check-template --payload data/examples/grant_advanced_demo.json
```

出现 missing placeholders / missing flags / missing styles，通常是**预期结果**，表示模板还没有升级到 advanced 结构。

---

## 9. 关于 payload

项目当前主要围绕两类 payload：

### 基础版

用于单章节 `research_content` 的早期原型：

- `data/grant_payload_demo.json`
- `data/examples/grant_demo.json`

适合搭配只含单个 `RESEARCH_CONTENT_SUBDOC` 的基础模板。

### 进阶版

用于多章节、多个附件、附件总区、章节开关等场景：

- `data/grant_payload_advanced_demo.json`
- `data/examples/grant_advanced_demo.json`

适合搭配已经升级为 advanced 结构的模板。

推荐优先使用 `data/examples/grant_advanced_demo.json` 进行开发与验证，但前提是模板本身也已经完成 advanced 适配。

payload 写法参考：

- `docs/report_engine_payload_spec.md`

---

## 10. 兼容入口说明

`scripts/render_grant_advanced.py` 已经被收敛为**兼容 wrapper**。

它的作用是：

- 保留已有调用方式
- 将旧入口转发到 `src/report_engine/renderer.py`
- 避免继续维护第二套独立实现

后续建议优先使用 CLI 或 `src/report_engine` 的包接口，而不是继续扩展旧脚本。

---

## 11. 文档地图

### Phase 1 实施基准

- `docs/superpowers/plans/2026-04-23-report-engine-revised.md`

### Phase 1 设计文档

- `docs/superpowers/specs/2026-04-23-report-engine-design.md`

### Block 扩展

- `docs/superpowers/specs/2026-04-23-block-extensions-design.md`（11 种新 block 设计）
- `docs/superpowers/plans/2026-04-23-block-extensions-plan.md`（实施计划）

### 当前行为基线

- `docs/grant_render_advanced_readme.md`
- `scripts/render_grant_advanced.py`
- `data/grant_payload_advanced_demo.json`

### 正式规范文档

- `docs/report_engine_payload_spec.md`
- `docs/report_engine_template_spec.md`

### 模板改造参考

- `docs/grant_template_upgrade_guide.md`
- `docs/template_check_troubleshooting.md`
- `templates/grant/README.md`

### 阶段状态

- `docs/phase1_status.md`

### 基础版示例（参考）

- `docs/grant_render_readme.md`
- `scripts/render_grant_demo.py`
- `data/grant_payload_demo.json`

---

## 12. 当前测试覆盖

当前测试主要覆盖以下链路：

- schema 模型
- payload validator
- block registry 与基础 block 渲染
- subdoc 构建
- style checker
- template checker
- renderer 集成
- CLI smoke test
- 旧 advanced wrapper 兼容测试

这些测试的目标，是先把当前重构阶段的关键行为锁住，为后续继续开发提供回归保护。

---

## 13. 当前限制

当前项目已从 Phase 1 进入扩展阶段，下面这些内容仍在逐步完善：

- 更严格的运行级回归验证
- 更多模板适配样例
- formula 的 OMML 原生公式支持（当前降级为图片/纯文本）
- columns 内嵌套 table 的支持
- 更完整的错误提示和日志输出
- Phase 2 的 Agent Skill 封装

---

## 14. 后续开发建议

如果你要继续推进这个项目，建议按下面顺序：

1. 先跑通 `pytest`
2. 用真实模板跑一次 `check-template`
3. 用真实模板和 example payload 跑一次 `render`
4. 根据真实模板差异补充 style / placeholder / flag 约束
5. 根据需要添加更多模板适配样例
6. 推进 Phase 2 的 Agent Skill 封装

---

## 15. 说明

仓库中旧的“总提示词式交接文档”已经移除，不再作为实施依据。

后续如需让 coding agent 或开发者继续推进，请直接以以下两份文档为准：

- `docs/superpowers/plans/2026-04-23-report-engine-revised.md`
- `docs/superpowers/specs/2026-04-23-report-engine-design.md`
