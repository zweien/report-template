# Report Engine Payload 规范（Phase 1）

## 1. 目的

本文档定义 Phase 1 中 `report_engine` 使用的结构化 payload 约定。

目标是：

- 统一大模型、脚本和渲染器之间的输入格式
- 让 payload 可以被校验、测试和复用
- 让模板与内容生成解耦

---

## 2. 顶层结构

Phase 1 推荐 payload 结构如下：

```json
{
  "context": {},
  "sections": [],
  "attachments": [],
  "attachments_bundle": {},
  "style_map": {}
}
```

### 字段说明

- `context`：标量上下文，用于普通模板变量替换
- `sections`：正文章节数组，每个章节通常对应一个 subdoc 插槽
- `attachments`：附件数组
- `attachments_bundle`：附件总区配置
- `style_map`：样式名覆盖映射

---

## 3. context

`context` 用于承载简单标量数据，例如：

```json
{
  "PROJECT_NAME": "智能生成式设计关键技术研究项目申报书",
  "APPLICANT_ORG": "XX研究院",
  "PROJECT_LEADER": "张三",
  "PROJECT_PERIOD": "2026年1月—2027年12月"
}
```

### 说明

- 推荐使用大写 key，与 Word 模板占位符保持一致
- 值不要求全为字符串，Phase 1 模型允许 `Any`
- 旧版顶层字段会通过 `compat.py` 自动归一化进 `context`

旧字段示例：

- `project_name` → `PROJECT_NAME`
- `applicant_org` → `APPLICANT_ORG`
- `project_leader` → `PROJECT_LEADER`

---

## 4. sections

### 结构

```json
{
  "id": "research_content",
  "placeholder": "RESEARCH_CONTENT_SUBDOC",
  "flag_name": "ENABLE_RESEARCH_CONTENT",
  "enabled": true,
  "blocks": [],
  "order": 1,
  "subdoc_title": "研究内容与技术路线",
  "subdoc_title_level": 2
}
```

### 字段说明

- `id`：章节唯一标识
- `placeholder`：模板中对应的 subdoc 插槽变量名
- `flag_name`：模板中的条件开关变量名
- `enabled`：是否启用该章节
- `blocks`：章节内容块数组
- `order`：可选顺序字段
- `subdoc_title`：可选，自动插入到 subdoc 顶部的标题
- `subdoc_title_level`：标题级别，默认 2

### 约束

- `id` 不可重复
- `placeholder` 不可重复
- `flag_name` 不可重复
- `blocks` 中的 block 类型必须受支持

---

## 5. attachments

### 结构

```json
{
  "id": "appendix_1",
  "placeholder": "APPENDIX_1_SUBDOC",
  "flag_name": "ENABLE_APPENDIX_1",
  "enabled": true,
  "title": "附件1：代表性成果目录",
  "title_level": 2,
  "blocks": [],
  "order": 1
}
```

### 说明

- `id`：附件唯一标识
- `placeholder`：模板中单独附件的 subdoc 插槽变量名
- `flag_name`：模板中单独附件的条件开关变量名
- `enabled`：是否启用该附件
- `title`：附件标题
- `title_level`：附件标题级别
- `blocks`：附件内容块数组
- `order`：可选顺序字段

附件有两种模板策略：

#### 策略 A：每个附件单独占位

模板中为每个附件都预留 `{{p APPENDIX_X_SUBDOC }}`。

#### 策略 B：使用附件总区

模板中只预留：

- `{{p APPENDICES_SUBDOC }}`
- `ENABLE_APPENDICES`

当前 Phase 1 的 `template_checker` 已兼容这种方式：如果 bundle 已启用且总附件区存在，则不强制要求每个附件都有独立 placeholder。

---

## 6. attachments_bundle

### 结构

```json
{
  "enabled": true,
  "placeholder": "APPENDICES_SUBDOC",
  "flag_name": "ENABLE_APPENDICES",
  "page_break_between_attachments": true,
  "include_attachment_title": true
}
```

### 字段说明

- `enabled`：是否启用附件总区
- `placeholder`：附件总区 subdoc 插槽，默认 `APPENDICES_SUBDOC`
- `flag_name`：附件总区开关变量，默认 `ENABLE_APPENDICES`
- `page_break_between_attachments`：附件之间是否分页
- `include_attachment_title`：总附件区中是否自动带附件标题

---

## 7. style_map

`style_map` 用于覆盖默认样式名，例如：

```json
{
  "table": "ResearchTable",
  "figure_paragraph": "Figure Paragraph",
  "legend": "Legend"
}
```

当前支持的样式键：

- `heading_2`
- `heading_3`
- `body`
- `caption`
- `legend`
- `figure_paragraph`
- `table`
- `bullet_list`
- `numbered_list`

---

## 8. block 类型

Phase 1 当前支持以下 block：

### `heading`

```json
{"type": "heading", "text": "1. 研究目标", "level": 2}
```

### `paragraph`

```json
{"type": "paragraph", "text": "这是正文段落。"}
```

### `bullet_list`

```json
{"type": "bullet_list", "items": ["条目1", "条目2"]}
```

### `numbered_list`

```json
{"type": "numbered_list", "items": ["步骤1", "步骤2"]}
```

### `table`

```json
{
  "type": "table",
  "title": "表1 示例表格",
  "headers": ["列1", "列2"],
  "rows": [["A", "B"]],
  "style": "ResearchTable",
  "force_borders": true
}
```

### `image`

```json
{
  "type": "image",
  "path": "figures/example.png",
  "width_cm": 14,
  "caption": "图1 示例图片",
  "legend": "注：这是图例。"
}
```

### `page_break`

```json
{"type": "page_break"}
```

---

## 9. 最小 advanced payload 示例

```json
{
  "context": {
    "PROJECT_NAME": "测试项目",
    "APPLICANT_ORG": "测试单位"
  },
  "sections": [
    {
      "id": "research_content",
      "placeholder": "RESEARCH_CONTENT_SUBDOC",
      "flag_name": "ENABLE_RESEARCH_CONTENT",
      "enabled": true,
      "blocks": [
        {"type": "paragraph", "text": "这是正文。"}
      ]
    }
  ],
  "attachments": [],
  "attachments_bundle": {
    "enabled": true,
    "placeholder": "APPENDICES_SUBDOC",
    "flag_name": "ENABLE_APPENDICES"
  },
  "style_map": {}
}
```

---

## 10. 推荐实践

- 优先使用 `data/examples/grant_advanced_demo.json` 作为参考
- 让大模型输出结构化 payload，而不是整篇富文本
- 模板和 payload 要一一对应，不要用基础模板去检查 advanced payload
- 图片素材路径建议统一管理
- 新增 block 类型时，先补 schema / validator / tests，再补 renderer

---

## 11. 参考文档

- `docs/report_engine_template_spec.md`
- `docs/grant_render_advanced_readme.md`
- `docs/template_check_troubleshooting.md`
