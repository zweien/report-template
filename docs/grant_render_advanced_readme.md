# 配套说明：多章节 subdoc + 多附件 + 可选章节开关

> 本文档描述的是**当前 advanced 渲染原型的行为基线**。  
> 如需推进 Phase 1 工程化重构，请以以下两份文档为准：  
> - `docs/superpowers/plans/2026-04-23-report-engine-revised.md`  
> - `docs/superpowers/specs/2026-04-23-report-engine-design.md`

这套文件是对上一版示例的升级版，重点解决三个问题：

1. 一个申报书里不止一个富内容章节；
2. 有多个附件，需要集中渲染；
3. 某些章节或附件需要按开关显示/隐藏。

## 文件
- `render_grant_advanced.py`：升级版渲染脚本
- `grant_payload_advanced_demo.json`：升级版示例数据
- `grant_template_demo_clean_v3.docx`：你现有的主模板母版

## 依赖

```bash
pip install "docxtpl[subdoc]" python-docx
```

## 运行

```bash
python render_grant_advanced.py
```

默认读取：
- `grant_payload_advanced_demo.json`
- `grant_template_demo_clean_v3.docx`

输出：
- `grant_output_advanced_demo.docx`

## 这版支持什么

### 1）多个章节 subdoc
在 JSON 中使用 `sections` 数组，每个章节都可以有自己的：
- `placeholder`
- `flag_name`
- `enabled`
- `blocks`

例如：
- `RESEARCH_CONTENT_SUBDOC`
- `RESEARCH_BASIS_SUBDOC`
- `IMPLEMENTATION_PLAN_SUBDOC`

### 2）多个附件
在 JSON 中使用 `attachments` 数组，每个附件都可以：
- 单独对应一个占位符
- 也可以自动汇总进一个总附件区 `APPENDICES_SUBDOC`

这意味着你可以同时支持两种模板策略：
- 模板里每个附件单独占位
- 模板里只留一个“附件”总插槽，由脚本自动拼装多个附件

### 3）可选章节开关
每个章节和附件都可以通过 `enabled` 控制开关。脚本会同时向模板提供：
- 一个布尔变量，例如 `ENABLE_RESEARCH_BASIS`
- 一个对应的 subdoc 变量，例如 `RESEARCH_BASIS_SUBDOC`

## 模板怎么写

### 写法 A：推荐做法（章节标题也可一起隐藏）

```text
{%p if ENABLE_RESEARCH_CONTENT %}
二、研究内容与技术路线
{{p RESEARCH_CONTENT_SUBDOC }}
{%p endif %}

{%p if ENABLE_RESEARCH_BASIS %}
三、研究基础
{{p RESEARCH_BASIS_SUBDOC }}
{%p endif %}

{%p if ENABLE_APPENDICES %}
附件
{{p APPENDICES_SUBDOC }}
{%p endif %}
```

### 写法 B：标题固定，只隐藏内容

```text
三、研究基础
{{p RESEARCH_BASIS_SUBDOC }}
```

这种写法在 `enabled=false` 时，标题还会保留，所以只适合“标题必须出现”的场景。

## 推荐的 JSON 结构

```json
{
  "context": {
    "PROJECT_NAME": "...",
    "APPLICANT_ORG": "..."
  },
  "sections": [
    {
      "id": "research_content",
      "placeholder": "RESEARCH_CONTENT_SUBDOC",
      "flag_name": "ENABLE_RESEARCH_CONTENT",
      "enabled": true,
      "blocks": [ ... ]
    }
  ],
  "attachments": [
    {
      "id": "appendix_1",
      "placeholder": "APPENDIX_1_SUBDOC",
      "flag_name": "ENABLE_APPENDIX_1",
      "enabled": true,
      "title": "附件1：代表性成果目录",
      "blocks": [ ... ]
    }
  ],
  "attachments_bundle": {
    "enabled": true,
    "placeholder": "APPENDICES_SUBDOC",
    "flag_name": "ENABLE_APPENDICES",
    "page_break_between_attachments": true,
    "include_attachment_title": true
  }
}
```

## 当前支持的块类型
- `heading`
- `paragraph`
- `bullet_list`
- `numbered_list`
- `table`
- `image`
- `page_break`

## 什么时候用哪一种
- **章节内容很复杂**：用单独 subdoc 占位符；
- **附件很多，模板不想太碎**：用 `APPENDICES_SUBDOC` 总附件区；
- **章节可能出现/不出现**：模板里配合 `{%p if ENABLE_XXX %}` 使用。

## 模板必须预置的样式
建议在主模板里提前创建并至少用过一次：
- `Heading 2`
- `Heading 3`
- `Body Text`
- `TableCaption`
- `FigureCaption`
- `Legend`
- `Figure Paragraph`
- `ResearchTable`
- `List Bullet`
- `List Number`

## 你下一步最实际的改法
1. 在真实申报书模板中，为每个复杂章节增加一个 subdoc 占位符；
2. 对可能关闭的章节，用 `{%p if ENABLE_XXX %}` 包住标题和内容；
3. 对附件，优先使用总附件区 `APPENDICES_SUBDOC`，模板改动最少；
4. 让大模型输出 `sections + attachments` 结构化 JSON，而不是整篇富文本。
