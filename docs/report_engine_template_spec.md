# Report Engine Template 规范（Phase 1）

## 1. 目的

本文档定义 Phase 1 中 Word 模板应满足的最基本约束。

目标是：

- 让模板与 payload 一一对应
- 让 `check-template` 能在渲染前发现问题
- 让模板作者、大模型调用者、渲染器使用统一约定

---

## 2. 模板职责

在本项目中，模板负责：

- 页面版式
- 标题体系
- 既定段落样式
- 表格样式
- 固定章节框架
- Jinja 占位符与条件块

程序负责：

- 结构化内容拼装
- subdoc 渲染
- 动态章节启停
- 附件拼接

也就是说：

> 模板决定“长什么样”，payload 决定“放什么内容”。

---

## 3. 基础概念

### 3.1 标量占位符

用于简单变量替换，例如：

```text
{{PROJECT_NAME}}
{{APPLICANT_ORG}}
{{PROJECT_LEADER}}
{{PROJECT_PERIOD}}
```

### 3.2 subdoc 占位符

用于插入富内容块，例如：

```text
{{p RESEARCH_CONTENT_SUBDOC }}
```

### 3.3 条件开关

用于控制章节或附件显示与隐藏，例如：

```text
{%p if ENABLE_RESEARCH_CONTENT %}
...
{%p endif %}
```

---

## 4. 基础模板 vs Advanced 模板

### 基础模板

只适配单章节场景，通常只包含：

- `RESEARCH_CONTENT_SUBDOC`
- 少量普通标量占位符

这种模板适合搭配：

- `data/grant_payload_demo.json`
- `data/examples/grant_demo.json`

### Advanced 模板

适配多章节、附件、总附件区、章节开关等场景。

这种模板适合搭配：

- `data/grant_payload_advanced_demo.json`
- `data/examples/grant_advanced_demo.json`

不要把基础模板直接拿去检查 advanced payload。

---

## 5. Advanced 模板最低要求

如果模板要配合 `grant_advanced_demo.json` 使用，建议至少包含以下内容。

### 5.1 标量占位符

```text
{{PROJECT_NAME}}
{{APPLICANT_ORG}}
{{PROJECT_LEADER}}
{{PROJECT_PERIOD}}
```

### 5.2 正文章节 subdoc 插槽

```text
{{p RESEARCH_CONTENT_SUBDOC }}
{{p RESEARCH_BASIS_SUBDOC }}
{{p IMPLEMENTATION_PLAN_SUBDOC }}
```

### 5.3 条件开关

```text
{%p if ENABLE_RESEARCH_CONTENT %}
{%p if ENABLE_RESEARCH_BASIS %}
{%p if ENABLE_IMPLEMENTATION_PLAN %}
```

### 5.4 附件总区

```text
{%p if ENABLE_APPENDICES %}
附件
{{p APPENDICES_SUBDOC }}
{%p endif %}
```

---

## 6. 推荐模板写法

推荐把标题和内容一起放进条件块，避免章节关闭后标题残留。

### 推荐写法

```text
{%p if ENABLE_RESEARCH_CONTENT %}
二、研究内容与技术路线
{{p RESEARCH_CONTENT_SUBDOC }}
{%p endif %}

{%p if ENABLE_RESEARCH_BASIS %}
三、研究基础
{{p RESEARCH_BASIS_SUBDOC }}
{%p endif %}

{%p if ENABLE_IMPLEMENTATION_PLAN %}
四、实施计划
{{p IMPLEMENTATION_PLAN_SUBDOC }}
{%p endif %}

{%p if ENABLE_APPENDICES %}
附件
{{p APPENDICES_SUBDOC }}
{%p endif %}
```

### 不推荐写法

```text
三、研究基础
{{p RESEARCH_BASIS_SUBDOC }}
```

原因：当 `enabled=false` 时，标题仍会保留。

---

## 7. 附件模板策略

### 策略 A：每个附件单独占位

模板中预留：

```text
{{p APPENDIX_1_SUBDOC }}
{{p APPENDIX_2_SUBDOC }}
```

这种方式适合模板强依赖固定附件位置的场景。

### 策略 B：使用总附件区

模板中只预留：

```text
{%p if ENABLE_APPENDICES %}
附件
{{p APPENDICES_SUBDOC }}
{%p endif %}
```

这是当前 advanced 示例更推荐的做法，因为模板改动更少。

Phase 1 当前的 checker 已兼容这种策略：

> 如果 bundle 已启用且总附件区存在，则不强制每个附件都有单独 placeholder。

---

## 8. 推荐样式

模板建议至少预置以下样式，并最好在模板里真实使用过一次。

### 段落样式（10 种）

| 样式名 | 用途 | 使用的 block 类型 |
|--------|------|-------------------|
| `Heading 2` | 二级标题 | `heading`（level ≤ 2） |
| `Heading 3` | 三级标题 | `heading`（level > 2） |
| `Body Text` | 正文 | `paragraph`、`rich_paragraph` 及各类 fallback |
| `Caption` | 图表标题 | `table`、`image`、`formula` 的 title/caption |
| `Legend` | 图例说明 | `image` 的 legend |
| `Figure Paragraph` | 图片段落 | `image`、`two_images_row` |
| `List Bullet` | 无序列表 | `bullet_list` |
| `List Number` | 有序列表 | `numbered_list` |
| `Note` | 注释 | `note` |
| `Quote` | 引用 | `quote` |

### 表格样式（2 种）

| 样式名 | 用途 | 使用的 block 类型 |
|--------|------|-------------------|
| `ResearchTable` | 研究表格（默认） | `table` |
| `AppendixTable` | 附录表格（可选） | `appendix_table`（fallback 到 ResearchTable） |

### 其他样式（2 种，可选）

| 样式名 | 用途 | 使用的 block 类型 |
|--------|------|-------------------|
| `Checklist` | 清单 | `checklist`（fallback 到 List Bullet） |
| `CodeBlock` | 代码块 | `code_block` |

### 样式 fallback 链

如果模板中缺少某个样式，renderer 会按以下顺序降级：

```
指定样式 → DEFAULT_STYLE_MAP 中的默认值 → "Normal"
```

因此即使模板只预置了基础样式（Heading 2/3、Body Text、Caption），渲染也不会失败，只是视觉效果会降级。

---

## 9. checker 会检查什么

### style checker

检查：

- 样式是否存在
- 样式类型是否正确

例如：

- `ResearchTable` 必须是 table style
- `Caption` 必须是 paragraph style

### template checker

检查：

- section placeholder 是否存在
- attachment bundle placeholder 是否存在
- flag 是否存在
- 是否存在明显的结构不匹配

---

## 10. 常见失败原因

### 缺少样式

例如：

- `Legend`
- `Figure Paragraph`
- `ResearchTable`

### 缺少 advanced 占位符

例如：

- `RESEARCH_BASIS_SUBDOC`
- `IMPLEMENTATION_PLAN_SUBDOC`
- `APPENDICES_SUBDOC`

### 缺少条件开关

例如：

- `ENABLE_RESEARCH_BASIS`
- `ENABLE_IMPLEMENTATION_PLAN`
- `ENABLE_APPENDICES`

### 使用了错误层级的模板

即：拿基础模板去检查 advanced payload。

---

## 11. 推荐验证流程

```bash
# 日常验证
report-engine validate --payload data/examples/grant_advanced_demo.json
report-engine check-template --template templates/grant/template.docx --payload data/examples/grant_advanced_demo.json
report-engine render --template templates/grant/template.docx --payload data/examples/grant_advanced_demo.json --output output/demo.docx

# 全量 block 类型测试（18 种）
report-engine validate --payload data/examples/test_all_blocks.json
report-engine render --template templates/test_all_blocks.docx --payload data/examples/test_all_blocks.json --output output/test_all_blocks.docx
```

---

## 12. 推荐目录约定

建议将已经验证通过的模板放到：

```text
templates/grant/template.docx
```

如果需要保留历史版本，可额外保留：

- `grant_template_demo_clean_v3.docx`
- `grant_template_demo_clean_v3_advanced.docx`

但建议让 `template.docx` 成为当前稳定默认模板。

---

## 13. 参考文档

- `docs/report_engine_payload_spec.md`
- `docs/grant_template_upgrade_guide.md`
- `docs/template_check_troubleshooting.md`
- `templates/grant/README.md`
