# examples

本目录放置可直接用于本地验证与测试的示例 payload。

当前包含：

- `grant_demo.json`：基础版示例，对应早期单章节 `research_content` 渲染思路
- `grant_advanced_demo.json`：进阶版示例，覆盖：
  - 多章节 subdoc
  - 多附件
  - 附件汇总区 `APPENDICES_SUBDOC`
  - 章节 / 附件开关
  - 表格、图片、分页符等 block
- `test_all_blocks.json`：全量 block 测试示例，覆盖全部 **18 种** block 类型：
  - P1：`rich_paragraph`、`note`、`quote`、`two_images_row`
  - P2：`appendix_table`、`checklist`、`horizontal_rule`
  - P3：`toc_placeholder`、`code_block`、`formula`、`columns`
  - 原有：`heading`、`paragraph`、`bullet_list`、`numbered_list`、`table`、`image`、`page_break`

推荐优先使用 `grant_advanced_demo.json` 进行日常开发验证，使用 `test_all_blocks.json` 进行全量 block 类型测试。

```bash
# 日常验证
report-engine validate --payload data/examples/grant_advanced_demo.json

# 全量 block 测试（需搭配 templates/test_all_blocks.docx）
report-engine validate --payload data/examples/test_all_blocks.json
report-engine render --template templates/test_all_blocks.docx --payload data/examples/test_all_blocks.json --output output/test_all_blocks.docx
```

渲染时请搭配一个已按约定预留占位符和样式的 `.docx` 模板使用。
