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
- `note`
- `quote`
- `appendix_table`
- `checklist`
- `code_block`

---

## 8. block 类型

Phase 1 当前支持以下 19 种 block：

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

### `three_line_table`

学术三线表，顶线与底线为粗线（1.5pt），表头底线为细线（0.5pt），无竖线、无中间横线。适用于论文、报告中的规范表格。

```json
{
  "type": "three_line_table",
  "title": "表2 实验结果",
  "headers": ["实验组", "样本量", "均值", "标准差"],
  "rows": [
    ["对照组", "50", "10.25", "1.34"],
    ["实验组", "50", "15.67", "1.89"]
  ]
}
```

**字段说明：**

- `headers`（必填）：表头字符串数组
- `rows`（必填）：二维数据数组
- `title`（可选）：表格标题
- `style`（可选）：Word 表格样式名，默认 `ResearchTable`

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

### `rich_paragraph`

带富文本格式的段落，支持行内加粗、斜体、上标、下标。

```json
{
  "type": "rich_paragraph",
  "segments": [
    {"text": "普通文本"},
    {"text": "加粗文本", "bold": true},
    {"text": "斜体文本", "italic": true},
    {"text": "下标", "sub": true},
    {"text": "上标", "sup": true}
  ]
}
```

**字段说明：**

- `segments`（必填）：文本片段数组
  - `text`（必填）：片段文本内容
  - `bold`（可选）：是否加粗，默认 `false`
  - `italic`（可选）：是否斜体，默认 `false`
  - `sub`（可选）：是否为下标，默认 `false`
  - `sup`（可选）：是否为上标，默认 `false`

---

### `note`

注释块，自动添加"注："前缀并加粗。

```json
{"type": "note", "text": "注：以上经费为预算上限，实际支出以审计结果为准。"}
```

**字段说明：**

- `text`（必填）：注释文本内容

---

### `quote`

引用块，用于引用政策文件、领导讲话等。可附带来源信息。

```json
{
  "type": "quote",
  "text": "教育是国之大计、党之大计。",
  "source": "《中国教育现代化2035》"
}
```

**字段说明：**

- `text`（必填）：引用文本内容
- `source`（可选）：引用来源，渲染为右对齐文本

---

### `two_images_row`

双图并排块，将两张图片以无边框表格形式左右并排放置。

```json
{
  "type": "two_images_row",
  "images": [
    {
      "path": "figures/fig1.png",
      "width_cm": 8,
      "caption": "图1 左侧图片"
    },
    {
      "path": "figures/fig2.png",
      "width_cm": 8,
      "caption": "图2 右侧图片"
    }
  ]
}
```

**字段说明：**

- `images`（必填）：恰好 2 个图片对象的数组
  - `path`（必填）：图片文件路径
  - `width_cm`（可选）：图片宽度（厘米）
  - `caption`（可选）：图片说明文字

---

### `appendix_table`

附录表格，与 `table` 类型结构相同，但默认使用 `AppendixTable` 样式（适用于附录中的表格）。

```json
{
  "type": "appendix_table",
  "title": "表A-1 附录表格",
  "headers": ["列1", "列2", "列3"],
  "rows": [["A", "B", "C"]],
  "style": "AppendixTable",
  "force_borders": true
}
```

**字段说明：**

- `headers`（必填）：表头字符串数组
- `rows`（必填）：二维数据数组
- `title`（可选）：表格标题
- `style`（可选）：Word 表格样式名，默认 `AppendixTable`
- `force_borders`（可选）：是否强制边框，默认 `true`

---

### `checklist`

清单/复选框列表，每项带有勾选状态。

```json
{
  "type": "checklist",
  "items": [
    {"text": "完成文献综述", "checked": true},
    {"text": "完成实验设计", "checked": true},
    {"text": "提交伦理审查", "checked": false}
  ]
}
```

**字段说明：**

- `items`（必填）：清单项数组
  - `text`（必填）：清单项文本
  - `checked`（可选）：是否已勾选，默认 `false`

---

### `horizontal_rule`

水平分隔线，用于视觉分隔不同内容区域。

```json
{"type": "horizontal_rule"}
```

**字段说明：**

- 无额外字段

---

### `toc_placeholder`

目录占位符，插入 TOC 域代码。在 Word 中右键更新域即可生成目录。

```json
{
  "type": "toc_placeholder",
  "title": "目录"
}
```

**字段说明：**

- `title`（可选）：目录标题，默认 `"目录"`

---

### `code_block`

代码块，使用等宽字体（Courier New）渲染代码，带有灰色底纹背景。

```json
{
  "type": "code_block",
  "code": "def hello():\n    print('Hello, World!')",
  "language": "Python"
}
```

**字段说明：**

- `code`（必填）：代码文本内容
- `language`（可选）：语言标注，渲染为右对齐灰色小字

---

### `formula`

数学公式块，优先使用 matplotlib 渲染 LaTeX 公式为图片；若 matplotlib 不可用则降级为纯文本。

```json
{
  "type": "formula",
  "latex": "E = mc^2",
  "caption": "公式1 爱因斯坦质能方程"
}
```

**字段说明：**

- `latex`（必填）：LaTeX 格式的数学公式
- `caption`（可选）：公式说明文字

---

### `ascii_diagram`

ASCII 示意图块，将 ASCII 艺术文本渲染为图片插入文档。适用于架构图、流程图、简单示意图等场景。

```json
{
  "type": "ascii_diagram",
  "ascii": "  +---+     +---+\n  | A |---->| B |\n  +---+     +---+",
  "caption": "图1 系统架构",
  "width_cm": 10,
  "font_size": 14,
  "bg_color": "#F8F8F8",
  "fg_color": "#333333",
  "padding": 20
}
```

**字段说明：**

- `ascii`（必填）：ASCII 艺术文本内容
- `caption`（可选）：图片说明文字
- `width_cm`（可选）：插入图片的宽度（厘米），不指定则按原始尺寸
- `font_size`（可选）：字体大小，默认 `14`
- `bg_color`（可选）：背景色，默认 `#F8F8F8`
- `fg_color`（可选）：文字颜色，默认 `#333333`
- `padding`（可选）：内边距（像素），默认 `20`

**降级行为**：若 Pillow 不可用，则降级为等宽字体文本段落。

---

### `columns`

多栏布局块，将内容分为指定数量的列（使用无边框表格实现）。

```json
{
  "type": "columns",
  "count": 2,
  "columns": [
    [
      {"type": "paragraph", "text": "左栏内容"},
      {"type": "bullet_list", "items": ["条目1", "条目2"]}
    ],
    [
      {"type": "paragraph", "text": "右栏内容"},
      {"type": "image", "path": "figures/side.png", "width_cm": 7}
    ]
  ]
}
```

**字段说明：**

- `count`（必填）：列数，必须与 `columns` 数组长度一致
- `columns`（必填）：嵌套 block 数组，每个子数组为一列的内容

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
