# Block 类型扩展 — 设计文档

日期：2026-04-23
状态：设计完成，待实施

## 1. 背景

Phase 1 已实现 7 种 block 类型（heading、paragraph、bullet_list、numbered_list、table、image、page_break），报告引擎基础骨架可用。

本文档定义 **11 种新增 block 类型** 的设计，按优先级分 3 批实施。

## 2. 实施策略

按优先级分批（方案 A），每批完成后可独立验证：

| 批次 | 类型 | 数量 | 难度 |
|------|------|------|------|
| P1 | rich_paragraph、note、quote、two_images_row | 4 | 低~中 |
| P2 | appendix_table、checklist、horizontal_rule | 3 | 低~中 |
| P3 | toc_placeholder、code_block、formula、columns | 4 | 中~高 |

## 3. 总体架构

现有架构无需改动，每种新类型遵循统一实现路径：

```
定义 schema → 注册校验 → 实现 renderer → 注册到 registry → 添加样式 fallback → 写测试 → 更新示例 payload
```

### 3.1 校验层

在 `validator.py` 的 `BLOCK_REQUIRED_FIELDS` 中注册每种新类型的必填字段。

### 3.2 渲染层

为每种类型新增 `add_*_block()` 函数，注册到 `blocks.py` 的 `BlockRegistry`。

### 3.3 样式层

新增的 block 类型需要在模板中定义对应 Word 样式，或在 renderer 中提供 fallback。

### 3.4 架构变化

- `rich_paragraph` 引入内联格式模型，是第一个需要结构化 `text` 字段的类型
- `columns` 需要递归构建 subdoc，`build_subdoc()` 需支持接收外部 block 列表
- `formula` 需要引入 LaTeX→Word 转换依赖

## 4. P1 详细设计

### 4.1 `rich_paragraph`

**Payload 结构**：

```json
{
  "type": "rich_paragraph",
  "segments": [
    {"text": "本项目研究", "bold": false},
    {"text": "人工智能", "bold": true, "italic": true},
    {"text": "在教育领域的应用，重点关注", "bold": false},
    {"text": "H₂O", "sub": true},
    {"text": "等化学式。"}
  ]
}
```

**字段定义**：

- `segments`（必填）：`RichSegment[]`，每个 segment 包含：
  - `text`（必填）：字符串
  - `bold`（可选，默认 false）
  - `italic`（可选，默认 false）
  - `sub`（可选，默认 false）— 下标
  - `sup`（可选，默认 false）— 上标

**渲染逻辑**：遍历 segments，每个 segment 添加一个 Run，设置对应的 bold/italic 属性。下标/上标通过 `OxmlElement('w:vertAlign')` 设置 `w:val="subscript"` 或 `w:val="superscript"`。

**样式**：复用 `style_map["body"]`。

**校验**：`BLOCK_REQUIRED_FIELDS["rich_paragraph"] = ["segments"]`。

### 4.2 `note`

**Payload 结构**：

```json
{
  "type": "note",
  "text": "注：本表数据为示意数据，正式提交时请替换。"
}
```

**字段定义**：

- `text`（必填）：注释文本

**渲染逻辑**：添加一个段落，前缀 "注：" 加粗（通过单独 Run），其余为正文。使用 `style_map["note"]`，fallback 到 `style_map["body"]` + 左缩进。

**样式**：建议模板中定义 `Note` 样式（灰底 + 左缩进），或通过 XML 操作设置底纹。

**校验**：`BLOCK_REQUIRED_FIELDS["note"] = ["text"]`。

### 4.3 `quote`

**Payload 结构**：

```json
{
  "type": "quote",
  "text": "教育是国之大计、党之大计。",
  "source": "《中国教育现代化2035》"
}
```

**字段定义**：

- `text`（必填）：引用文本
- `source`（可选）：来源说明

**渲染逻辑**：引用文本用 `style_map["quote"]`（斜体 + 左缩进），source 用右对齐正文样式追加为独立段落。无 source 时只渲染引用文本。

**样式**：需要 `Quote` 样式（斜体 + 左侧竖线或左缩进）。

**校验**：`BLOCK_REQUIRED_FIELDS["quote"] = ["text"]`。

### 4.4 `two_images_row`

**Payload 结构**：

```json
{
  "type": "two_images_row",
  "images": [
    {"path": "figures/left.png", "width_cm": 7, "caption": "图1a"},
    {"path": "figures/right.png", "width_cm": 7, "caption": "图1b"}
  ]
}
```

**字段定义**：

- `images`（必填）：恰好 2 个 image 对象，每个包含：
  - `path`（必填）：图片路径
  - `width_cm`（可选）：宽度
  - `caption`（可选）：图片说明

**渲染逻辑**：创建一个 1 行 2 列的无边框表格，居中对齐。每个单元格内插入图片（或缺失占位符）和 caption。通过 `WD_TABLE_ALIGNMENT.CENTER` 居中，移除表格边框。

**样式**：表格用无边框样式。

**校验**：`BLOCK_REQUIRED_FIELDS["two_images_row"] = ["images"]`。运行时校验 `len(images) == 2`。

## 5. P2 详细设计

### 5.1 `appendix_table`

**Payload 结构**：

```json
{
  "type": "appendix_table",
  "title": "附表1：经费预算明细",
  "headers": ["项目", "金额（万元）", "备注"],
  "rows": [["设备费", "50", "含服务器"]]
}
```

**字段定义**：与 `table` 完全相同（`title`、`headers`、`rows`、`style`、`force_borders`）。

**渲染逻辑**：与 `table` 基本一致，使用 `style_map["appendix_table"]`，fallback 到 `style_map["table"]`。语义上用于附录。

**校验**：`BLOCK_REQUIRED_FIELDS["appendix_table"] = ["headers", "rows"]`。

### 5.2 `checklist`

**Payload 结构**：

```json
{
  "type": "checklist",
  "items": [
    {"text": "已完成文献综述", "checked": true},
    {"text": "已提交伦理审查", "checked": false}
  ]
}
```

**字段定义**：

- `items`（必填）：`ChecklistItem[]`，每个包含：
  - `text`（必填）：任务文本
  - `checked`（可选，默认 false）

**渲染逻辑**：每个 item 渲染为一个段落，前缀 `☑`（checked=true）或 `☐`（checked=false）符号。使用 `style_map["checklist"]`，fallback 到 `style_map["bullet_list"]`。

**校验**：`BLOCK_REQUIRED_FIELDS["checklist"] = ["items"]`。

### 5.3 `horizontal_rule`

**Payload 结构**：

```json
{
  "type": "horizontal_rule"
}
```

**字段定义**：无额外字段。

**渲染逻辑**：添加一个段落，通过 `OxmlElement('w:pBdr')` 设置底部边框（单线、灰色、0.5pt）。段落内无文本内容。

**校验**：无必填字段。

## 6. P3 详细设计

### 6.1 `toc_placeholder`

**Payload 结构**：

```json
{
  "type": "toc_placeholder",
  "title": "目 录"
}
```

**字段定义**：

- `title`（可选，默认 "目录"）：目录标题文本

**渲染逻辑**：插入 TOC 域代码（`w:fldChar` begin + `w:instrText` TOC + `w:fldChar` separate + `w:fldChar` end）。Word 打开后右键更新域即可生成目录。

**校验**：无必填字段。

### 6.2 `code_block`

**Payload 结构**：

```json
{
  "type": "code_block",
  "code": "def hello():\n    print('world')",
  "language": "python"
}
```

**字段定义**：

- `code`（必填）：代码字符串
- `language`（可选）：语言标注（仅显示，不做语法高亮）

**渲染逻辑**：创建段落，设置 Courier New 字体 + 灰色底纹（`w:shd`）。多行代码按 `\n` 分割为多个段落。language 如有则作为右对齐小字标注。

**样式**：需要 `CodeBlock` 样式（等宽字体 + 灰底）。

**校验**：`BLOCK_REQUIRED_FIELDS["code_block"] = ["code"]`。

### 6.3 `formula`

**Payload 结构**：

```json
{
  "type": "formula",
  "latex": "E = mc^2",
  "caption": "公式1：质能方程"
}
```

**字段定义**：

- `latex`（必填）：LaTeX 公式字符串
- `caption`（可选）：公式编号/说明

**渲染方案**：

**方案 1（推荐）：LaTeX→OMML**
使用 `latex2mathml` 库将 LaTeX 转为 MathML，再通过 `python-docx` 的 OMML 支持插入 Word 公式对象。公式在 Word 中可编辑。

**方案 2（降级）：LaTeX→图片**
使用 `matplotlib` 将 LaTeX 渲染为图片，按 image block 插入。公式不可编辑但视觉效果好。

**方案 3（最低降级）：纯文本**
将 LaTeX 作为等宽字体文本插入。最简单但不美观。

实现时优先尝试方案 1，依赖不可用时自动降级到方案 2，最终降级到方案 3。

**校验**：`BLOCK_REQUIRED_FIELDS["formula"] = ["latex"]`。

### 6.4 `columns`

**Payload 结构**：

```json
{
  "type": "columns",
  "count": 2,
  "gap_cm": 1,
  "columns": [
    [
      {"type": "paragraph", "text": "左列内容"},
      {"type": "image", "path": "figures/left.png", "width_cm": 6}
    ],
    [
      {"type": "paragraph", "text": "右列内容"}
    ]
  ]
}
```

**字段定义**：

- `count`（必填）：列数（2-4）
- `gap_cm`（可选，默认 0.5）：列间距
- `columns`（必填）：`Block[][]`，每个元素是一列的 block 列表

**渲染逻辑**：创建一个 1 行 N 列的无边框表格，每个单元格内递归调用 `build_subdoc()` 渲染该列的 block 列表。

**依赖**：`build_subdoc()` 需要支持接收外部 block 列表参数（当前它从 section/attachment 读取 blocks）。需要重构 `build_subdoc()` 签名，使其可接受 `blocks` 参数。

**校验**：`BLOCK_REQUIRED_FIELDS["columns"] = ["count", "columns"]`。运行时校验 `len(columns) == count`。

## 7. 样式需求汇总

| Block 类型 | 样式名 | 属性 | Fallback |
|-----------|--------|------|----------|
| rich_paragraph | Body | 正文 | Normal |
| note | Note | 灰底 + 左缩进 | Body |
| quote | Quote | 斜体 + 左缩进 | Body |
| two_images_row | — | 无边框表格 | — |
| appendix_table | AppendixTable | 同 table | ResearchTable |
| checklist | Checklist | 类似 bullet_list | BulletList |
| horizontal_rule | — | 底部边框 XML | — |
| toc_placeholder | TOC Heading | 目录标题 | Heading 2 |
| code_block | CodeBlock | 等宽字体 + 灰底 | Body |
| formula | — | 居中段落 | Body |
| columns | — | 无边框表格 | — |

## 8. 实现路径

每种 block 的实现步骤：

1. 在 `schema.py` 中定义字段（如有新模型）
2. 在 `validator.py` 的 `BLOCK_REQUIRED_FIELDS` 中注册
3. 在 `blocks.py` 中实现 `add_*_block()` 函数
4. 在 `blocks.py` 的 `BlockRegistry` 中注册类型
5. 在 renderer 中添加样式 fallback
6. 在 `tests/` 中添加单元测试
7. 在 `data/examples/` 中更新示例 payload
8. 更新 `docs/report_engine_payload_spec.md`
9. 更新 `docs/report_engine_template_spec.md`

## 9. 测试策略

每种新 block 类型至少需要：

- **校验测试**：必填字段缺失时正确报错
- **渲染测试**：block 正确渲染到 Word 文档（检查段落数、样式名、表格结构）
- **集成测试**：在完整 payload 中使用新 block 类型，端到端渲染成功

P3 的 formula 和 columns 需要额外的降级测试和嵌套测试。

## 10. 风险与降级

| 风险 | 影响 | 降级方案 |
|------|------|----------|
| LaTeX→OMML 转换库不可用 | formula 无法渲染为可编辑公式 | 降级到图片或纯文本 |
| Word 样式缺失 | 新 block 使用 fallback 样式 | renderer 已有 fallback 机制 |
| columns 嵌套过深 | subdoc 构建复杂度增加 | 限制嵌套层数为 1 |
| 模板缺少新样式 | 渲染效果不理想 | style_checker 提示警告 |
