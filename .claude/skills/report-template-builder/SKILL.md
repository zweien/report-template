---
name: report-template-builder
description: >
  为 report-engine 项目创建或改造 .docx 模板，支持三种模式：从零生成、从文字描述生成、从现有 docx 改造。
  当用户说"制作模板"、"创建模板"、"新建模板"、"改造模板"、"修改模板"、"模板不对"、"模板报错"、
  "check-template 失败"、"样式缺失"、"placeholder 缺失"、"make template"、"create template"、
  "fix template"、"build a docx template for report engine" 时使用此 skill。
  也适用于用户提到"报告模板"、"申报书模板"、"Word 模板"、"docx 模板"、"根据描述生成模板"、
  "把现有模板改成引擎能用的"等场景。即使用户只是说"帮我做个模板"而没有更多信息，也应触发此 skill。
---

# Report Template Builder

为 report-engine 创建或改造 `.docx` 模板的专用 skill。支持三种输入模式。

## 核心概念

report-engine 的模板是 `.docx` 文件，包含三类占位元素：

| 类型 | 语法 | 用途 |
|------|------|------|
| 标量占位符 | `{{PROJECT_NAME}}` | 简单变量替换 |
| subdoc 插槽 | `{{p SECTION_SUBDOC }}` | 插入富内容块 |
| 条件开关 | `{%p if ENABLE_XXX %}...{%p endif %}` | 控制章节显示/隐藏 |

**关键原则**：模板决定"长什么样"，payload 决定"放什么内容"。

## 三种工作模式

### 模式 A：从零生成

用户明确告诉你要什么结构，直接用生成脚本。

### 模式 B：从文字描述生成

用户提供一段描述（如"项目申报书，包含研究内容、研究基础、实施计划，需要目录和附件"），用描述解析脚本自动生成。

### 模式 C：从现有 docx 改造

用户提供一个上级下发的或已有的 `.docx` 模板（仅有示例内容），用分析脚本提取结构并生成引擎兼容的模板和 payload。

## 工作流程

### Step 1: 确定输入模式

问用户：

1. "你有现成的 .docx 模板文件吗？" → 有：模式 C
2. "你能描述一下模板需要哪些章节吗？" → 能描述：模式 B
3. 都没有 → 模式 A，引导用户说出需求

### Step 2: 执行生成

#### 模式 A：从零生成

```bash
python <skill-path>/scripts/generate_template.py \
  --mode advanced \
  --output templates/my_template.docx \
  --sections "研究内容与技术路线,研究基础与条件保障,实施计划与进度安排" \
  --appendices \
  --toc
```

#### 模式 B：从文字描述生成

```bash
python <skill-path>/scripts/description_to_payload.py \
  --description "项目申报书，包含：一、研究内容，二、研究基础，三、实施计划，需要目录和附件" \
  --output-template templates/generated.docx \
  --output-payload data/examples/generated.json
```

也支持从文件读取描述：

```bash
python <skill-path>/scripts/description_to_payload.py \
  --file description.txt \
  --output-template templates/generated.docx \
  --output-payload data/examples/generated.json
```

#### 模式 C：从现有 docx 改造

```bash
python <skill-path>/scripts/analyze_docx.py \
  --input path/to/reference.docx \
  --output-template templates/generated.docx \
  --output-payload data/examples/generated.json
```

### Step 3: 验证模板

```bash
# 校验 payload
report-engine validate --payload data/examples/generated.json

# 检查模板与 payload 的契约
report-engine check-template --template templates/generated.docx --payload data/examples/generated.json

# 渲染测试
report-engine render --template templates/generated.docx --payload data/examples/generated.json --output output/test.docx
```

### Step 4: 手动完善

生成的模板和 payload 是骨架，用户需要：

1. 编辑 payload 填写实际内容（替换"（请填写）"占位符）
2. 在 Word 中调整模板的字体、间距、页边距等排版细节
3. 如有图片，在 payload 中添加 `image` 或 `two_images_row` block

## 描述解析规则（模式 B）

描述解析脚本支持以下格式：

| 格式 | 示例 |
|------|------|
| 中文数字序号 | 一、研究内容，二、研究基础 |
| 第X章/节 | 第一章 绪论，第二章 方法 |
| 数字序号 | 1. 研究目标，2. 技术路线 |
| 逗号/顿号分隔 | 研究内容，研究基础，实施计划 |
| 关键词检测 | "目录"→启用 TOC，"附件/附录"→启用附件区 |

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

### 从 docx 改造时章节识别不准确

analyze_docx.py 依赖标题样式（Heading 1/2）识别章节。如果原文档没有使用标准标题样式，需要手动调整生成的 payload 中的 sections。

## 参考文档

- `docs/report_engine_template_spec.md` — 完整模板规范
- `docs/report_engine_payload_spec.md` — payload 规范（了解 block 类型和字段）
- `scripts/build_test_template.py` — 项目中的模板生成脚本示例
- `data/examples/test_all_blocks.json` — 全量 block 类型的 payload 示例
