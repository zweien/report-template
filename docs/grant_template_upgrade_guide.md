# 模板改造指南：支持多章节 subdoc / 多附件 / 可选章节

下面是一种推荐的 Word 模板占位方式。

## 主体章节

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
```

## 附件区（推荐总附件区）

```text
{%p if ENABLE_APPENDICES %}
附件
{{p APPENDICES_SUBDOC }}
{%p endif %}
```

## 如果你一定要每个附件单独控制

```text
{%p if ENABLE_APPENDIX_1 %}
{{p APPENDIX_1_SUBDOC }}
{%p endif %}

{%p if ENABLE_APPENDIX_2 %}
{{p APPENDIX_2_SUBDOC }}
{%p endif %}
```

## 注意
- `{%p if ... %}`、`{{p ... }}` 最好单独占段，不要和正文混写。
- 每个复杂章节只留一个 subdoc 插槽，不要把表格和图片散落在主模板里。
- 图题、图例、表题都放在 subdoc 中生成，更容易保持一致。
