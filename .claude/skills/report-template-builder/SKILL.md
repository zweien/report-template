---
name: report-template-builder
description: >
  为 report-engine 项目创建或改造 .docx 模板。当用户说"制作模板"、"创建模板"、"新建模板"、
  "改造模板"、"修改模板"、"模板不对"、"模板报错"、"check-template 失败"、"样式缺失"、
  "placeholder 缺失"、"make template"、"create template"、"fix template"、
  "build a docx template for report engine" 时使用此 skill。
  也适用于用户提到"报告模板"、"申报书模板"、"Word 模板"、"docx 模板"等场景。
  即使用户只是说"帮我做个模板"而没有更多信息，也应触发此 skill。
---

# Report Template Builder

为 report-engine 创建或改造 `.docx` 模板的专用 skill。

## 核心概念

report-engine 的模板是 `.docx` 文件，包含三类占位元素：

| 类型 | 语法 | 用途 |
|------|------|------|
| 标量占位符 | `{{PROJECT_NAME}}` | 简单变量替换 |
| subdoc 插槽 | `{{p SECTION_SUBDOC }}` | 插入富内容块 |
| 条件开关 | `{%p if ENABLE_XXX %}...{%p endif %}` | 控制章节显示/隐藏 |

**关键原则**：模板决定"长什么样"，payload 决定"放什么内容"。

## 工作流程

### Step 1: 确定模板类型

询问用户需要哪种模板：

- **基础版**：单章节（只有 `RESEARCH_CONTENT_SUBDOC`），适合简单场景
- **进阶版**：多章节 + 附件 + 条件开关，适合项目申报书等复杂文档

### Step 2: 确定章节结构

进阶版默认包含以下章节（可按需增减）：

| 章节 | subdoc 占位符 | 条件开关 |
|------|--------------|----------|
| 目录（可选） | `TOC_SUBDOC` | `ENABLE_TOC` |
| 研究内容 | `RESEARCH_CONTENT_SUBDOC` | `ENABLE_RESEARCH_CONTENT` |
| 研究基础 | `RESEARCH_BASIS_SUBDOC` | `ENABLE_RESEARCH_BASIS` |
| 实施计划 | `IMPLEMENTATION_PLAN_SUBDOC` | `ENABLE_IMPLEMENTATION_PLAN` |
| 附件总区 | `APPENDICES_SUBDOC` | `ENABLE_APPENDICES` |

### Step 3: 生成模板

使用模板生成脚本：

```bash
python <skill-path>/scripts/generate_template.py \
  --mode advanced \
  --output templates/my_template.docx \
  --sections "研究内容与技术路线,研究基础与条件保障,实施计划与进度安排" \
  --appendices \
  --toc
```

或在代码中直接调用：

```python
from scripts.generate_template import build_template
build_template("templates/my_template.docx", mode="advanced",
               sections=["研究内容与技术路线", "研究基础与条件保障"],
               include_toc=True, include_appendices=True)
```

### Step 4: 验证模板

```bash
# 校验 payload
report-engine validate --payload data/examples/grant_advanced_demo.json

# 检查模板与 payload 的契约
report-engine check-template --template templates/my_template.docx --payload data/examples/grant_advanced_demo.json

# 渲染测试
report-engine render --template templates/my_template.docx --payload data/examples/grant_advanced_demo.json --output output/test.docx
```

## 样式要求

模板必须包含以下样式。生成脚本会自动创建，手动制作时需自行添加。

### 段落样式（12 种，9 种必检）

| 样式名 | 用途 | 是否必检 |
|--------|------|----------|
| `Heading 2` | 二级标题 | ✅ |
| `Heading 3` | 三级标题 | ✅ |
| `Body Text` | 正文 | ✅ |
| `Caption` | 图表标题 | ✅ |
| `Legend` | 图例 | ✅ |
| `Figure Paragraph` | 图片段落 | ✅ |
| `List Bullet` | 无序列表 | ✅ |
| `List Number` | 有序列表 | ✅ |
| `Note` | 注释 | ❌ fallback 到 Body Text |
| `Quote` | 引用 | ❌ fallback 到 Body Text |
| `Checklist` | 清单 | ❌ fallback 到 List Bullet |
| `CodeBlock` | 代码块 | ❌ fallback 到 Body Text |

### 表格样式（2 种，1 种必检）

| 样式名 | 用途 | 是否必检 |
|--------|------|----------|
| `ResearchTable` | 研究表格 | ✅ |
| `AppendixTable` | 附录表格 | ❌ fallback 到 ResearchTable |

## 常见问题排查

### check-template 报 missing placeholders

模板中缺少 payload 要求的 subdoc 占位符。用生成脚本重新生成，或手动在模板中添加对应的 `{{p XXX_SUBDOC }}` 段落。

### check-template 报 missing flags

模板中缺少条件开关。确保每个 section 的 `flag_name` 都有对应的 `{%p if FLAG_NAME %}...{%p endif %}` 块。

### 渲染后样式不对

检查模板中的样式名是否与 `DEFAULT_STYLE_MAP` 一致。样式名区分大小写。

### 条件开关不生效

确保使用 `{%p if ... %}` 而不是 `{% if ... %}`。`p` 前缀是 docxtpl 的段落级 Jinja 语法。

## 参考文档

- `docs/report_engine_template_spec.md` — 完整模板规范
- `docs/report_engine_payload_spec.md` — payload 规范（了解 block 类型和字段）
- `scripts/build_test_template.py` — 项目中的模板生成脚本示例
- `data/examples/test_all_blocks.json` — 全量 block 类型的 payload 示例
