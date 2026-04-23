# grant templates

本目录用于放置 `grant` 类 Word 模板。

## 推荐约定

- 默认模板文件：`template.docx`
- 如需保留历史版本，可使用更明确的命名，例如：
  - `grant_template_demo_clean_v3.docx`
  - `grant_template_demo_clean_v3_advanced.docx`
- 如果某一份模板已经通过当前 Phase 1 校验与渲染，建议额外保留一份稳定名称：
  - `template.docx`

这样 CLI 和后续文档引用会更稳定。

## 当前模板要求

如果模板要配合 `data/examples/grant_advanced_demo.json` 使用，至少应支持：

- `{{PROJECT_NAME}}`
- `{{APPLICANT_ORG}}`
- `{{PROJECT_LEADER}}`
- `{{PROJECT_PERIOD}}`
- `{{p RESEARCH_CONTENT_SUBDOC }}`
- `{{p RESEARCH_BASIS_SUBDOC }}`
- `{{p IMPLEMENTATION_PLAN_SUBDOC }}`
- `{{p APPENDICES_SUBDOC }}`
- `{%p if ENABLE_RESEARCH_CONTENT %}`
- `{%p if ENABLE_RESEARCH_BASIS %}`
- `{%p if ENABLE_IMPLEMENTATION_PLAN %}`
- `{%p if ENABLE_APPENDICES %}`

## 推荐样式

### 段落样式

- `Heading 2`
- `Heading 3`
- `Body Text`
- `Caption`
- `Legend`
- `Figure Paragraph`
- `List Bullet`
- `List Number`

### 表格样式

- `ResearchTable`

## 推荐做法

1. 把已经验证通过的模板复制或重命名为 `template.docx`
2. 用它执行：

```bash
report-engine check-template --template templates/grant/template.docx --payload data/examples/grant_advanced_demo.json
```

3. 再执行：

```bash
report-engine render --template templates/grant/template.docx --payload data/examples/grant_advanced_demo.json --output output/demo.docx
```

## 参考文档

- `docs/grant_template_upgrade_guide.md`
- `docs/template_check_troubleshooting.md`
- `docs/grant_render_advanced_readme.md`
