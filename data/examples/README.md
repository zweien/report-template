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

推荐优先使用：

```bash
report-engine validate --payload data/examples/grant_advanced_demo.json
```

渲染时请搭配一个已按约定预留占位符和样式的 `.docx` 模板使用。
