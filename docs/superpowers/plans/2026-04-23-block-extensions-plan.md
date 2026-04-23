# Block 类型扩展实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为报告引擎新增 11 种 block 类型，分 P1/P2/P3 三批实施。

**Architecture:** 每种 block 类型遵循统一路径：注册校验字段 → 实现 renderer 函数 → 注册到 BlockRegistry → 添加样式 fallback → 写测试。`Block` 模型使用 `extra="allow"`，无需修改 schema。

**Tech Stack:** Python, python-docx, docxtpl, Pydantic, pytest

**Spec:** `docs/superpowers/specs/2026-04-23-block-extensions-design.md`

---

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `src/report_engine/validator.py:10-18` | 修改 | `BLOCK_REQUIRED_FIELDS` 新增 11 个条目 |
| `src/report_engine/blocks.py:12-22` | 修改 | `DEFAULT_STYLE_MAP` 新增样式映射 |
| `src/report_engine/blocks.py:163-172` | 修改 | `create_default_registry()` 注册 11 个新 renderer |
| `src/report_engine/blocks.py` | 新增函数 | 11 个 `add_*_block()` 函数 |
| `src/report_engine/schema.py` | 可选修改 | 新增 `RichSegment`、`ChecklistItem` 模型（如需严格校验） |
| `tests/test_blocks.py` | 修改 | 新增每种 block 的渲染测试 |
| `tests/test_validator.py` | 修改 | 新增每种 block 的校验测试 |
| `data/examples/grant_advanced_demo.json` | 修改 | 新增示例 block |
| `docs/report_engine_payload_spec.md` | 修改 | 文档更新 |

---

## P1：4 种 block 类型

### Task 1: 扩展 validator — 注册 P1 校验字段

**Files:**
- Modify: `src/report_engine/validator.py:10-18`

- [ ] **Step 1: 在 BLOCK_REQUIRED_FIELDS 中新增 P1 的 4 个条目**

```python
BLOCK_REQUIRED_FIELDS = {
    # 已有 7 种
    "heading": ["text"],
    "paragraph": ["text"],
    "bullet_list": ["items"],
    "numbered_list": ["items"],
    "table": ["headers", "rows"],
    "image": ["path"],
    "page_break": [],
    # P1 新增
    "rich_paragraph": ["segments"],
    "note": ["text"],
    "quote": ["text"],
    "two_images_row": ["images"],
}
```

- [ ] **Step 2: 运行现有测试确保无回归**

Run: `pytest tests/test_validator.py -v`
Expected: 全部 PASS

- [ ] **Step 3: Commit**

```bash
git add src/report_engine/validator.py
git commit -m "feat(validator): register P1 block type required fields"
```

---

### Task 2: P1 renderer — rich_paragraph

**Files:**
- Modify: `src/report_engine/blocks.py` — 新增 `add_rich_paragraph_block` 函数
- Modify: `src/report_engine/blocks.py:163-172` — 注册到 registry
- Modify: `src/report_engine/blocks.py:12-22` — 无需新增样式（复用 body）

- [ ] **Step 1: 写失败测试**

在 `tests/test_blocks.py` 中新增：

```python
def test_rich_paragraph_block(subdoc, style_map, registry):
    block = {
        "type": "rich_paragraph",
        "segments": [
            {"text": "普通文本 "},
            {"text": "粗体", "bold": True},
            {"text": " 斜体", "italic": True},
            {"text": "H", "sub": True},
            {"text": "2O"},
        ],
    }
    registry.render(subdoc, block, style_map)
    assert len(subdoc.paragraphs) == 1
    p = subdoc.paragraphs[0]
    assert len(p.runs) == 5
    assert p.runs[0].text == "普通文本 "
    assert p.runs[1].bold is True
    assert p.runs[2].italic is True
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_blocks.py::test_rich_paragraph_block -v`
Expected: FAIL — `AttributeError` 或 `BlockRenderError`

- [ ] **Step 3: 实现 add_rich_paragraph_block**

在 `src/report_engine/blocks.py` 的 `add_image_block` 函数之后添加：

```python
def add_rich_paragraph_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    style_name = _get_style_name(doc, style_map["body"], "Normal")
    p = doc.add_paragraph(style=style_name)
    for seg in block["segments"]:
        run = p.add_run(str(seg.get("text", "")))
        if seg.get("bold"):
            run.bold = True
        if seg.get("italic"):
            run.italic = True
        if seg.get("sub"):
            rpr = run._element.get_or_add_rPr()
            vert_align = OxmlElement("w:vertAlign")
            vert_align.set(qn("w:val"), "subscript")
            rpr.append(vert_align)
        if seg.get("sup"):
            rpr = run._element.get_or_add_rPr()
            vert_align = OxmlElement("w:vertAlign")
            vert_align.set(qn("w:val"), "superscript")
            rpr.append(vert_align)
```

- [ ] **Step 4: 注册到 create_default_registry**

在 `create_default_registry()` 中添加：

```python
registry.register("rich_paragraph", add_rich_paragraph_block)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_blocks.py::test_rich_paragraph_block -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/report_engine/blocks.py tests/test_blocks.py
git commit -m "feat(blocks): add rich_paragraph renderer with inline formatting"
```

---

### Task 3: P1 renderer — note

**Files:**
- Modify: `src/report_engine/blocks.py` — 新增 `add_note_block` 函数
- Modify: `src/report_engine/blocks.py:12-22` — `DEFAULT_STYLE_MAP` 新增 `"note": "Note"`

- [ ] **Step 1: 写失败测试**

```python
def test_note_block(subdoc, style_map, registry):
    block = {"type": "note", "text": "注：本表数据为示意数据。"}
    registry.render(subdoc, block, style_map)
    assert len(subdoc.paragraphs) == 1
    p = subdoc.paragraphs[0]
    # 前缀 "注：" 应为加粗 run
    assert p.runs[0].text == "注："
    assert p.runs[0].bold is True
    assert p.runs[1].text == "本表数据为示意数据。"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_blocks.py::test_note_block -v`
Expected: FAIL

- [ ] **Step 3: 实现 add_note_block**

```python
def add_note_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    style_name = _get_style_name(doc, style_map.get("note", "Note"), style_map["body"])
    p = doc.add_paragraph(style=style_name)
    prefix_run = p.add_run("注：")
    prefix_run.bold = True
    p.add_run(str(block["text"]))
```

- [ ] **Step 4: 更新 DEFAULT_STYLE_MAP**

在 `DEFAULT_STYLE_MAP` 中添加：

```python
"note": "Note",
```

- [ ] **Step 5: 注册到 create_default_registry**

```python
registry.register("note", add_note_block)
```

- [ ] **Step 6: 运行测试确认通过**

Run: `pytest tests/test_blocks.py::test_note_block -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/report_engine/blocks.py tests/test_blocks.py
git commit -m "feat(blocks): add note renderer"
```

---

### Task 4: P1 renderer — quote

**Files:**
- Modify: `src/report_engine/blocks.py` — 新增 `add_quote_block` 函数
- Modify: `src/report_engine/blocks.py:12-22` — `DEFAULT_STYLE_MAP` 新增 `"quote": "Quote"`

- [ ] **Step 1: 写失败测试**

```python
def test_quote_block_with_source(subdoc, style_map, registry):
    block = {
        "type": "quote",
        "text": "教育是国之大计、党之大计。",
        "source": "《中国教育现代化2035》",
    }
    registry.render(subdoc, block, style_map)
    assert len(subdoc.paragraphs) == 2
    assert "教育是国之大计" in subdoc.paragraphs[0].text
    assert "中国教育现代化" in subdoc.paragraphs[1].text

def test_quote_block_without_source(subdoc, style_map, registry):
    block = {"type": "quote", "text": "引用文本。"}
    registry.render(subdoc, block, style_map)
    assert len(subdoc.paragraphs) == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_blocks.py::test_quote_block_with_source tests/test_blocks.py::test_quote_block_without_source -v`
Expected: FAIL

- [ ] **Step 3: 实现 add_quote_block**

```python
def add_quote_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    quote_style = _get_style_name(doc, style_map.get("quote", "Quote"), style_map["body"])
    doc.add_paragraph(str(block["text"]), style=quote_style)
    if block.get("source"):
        source_style = _get_style_name(doc, style_map["body"], "Normal")
        sp = doc.add_paragraph(str(block["source"]), style=source_style)
        sp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
```

- [ ] **Step 4: 更新 DEFAULT_STYLE_MAP**

```python
"quote": "Quote",
```

- [ ] **Step 5: 注册到 create_default_registry**

```python
registry.register("quote", add_quote_block)
```

- [ ] **Step 6: 运行测试确认通过**

Run: `pytest tests/test_blocks.py -v -k quote`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/report_engine/blocks.py tests/test_blocks.py
git commit -m "feat(blocks): add quote renderer with optional source"
```

---

### Task 5: P1 renderer — two_images_row

**Files:**
- Modify: `src/report_engine/blocks.py` — 新增 `add_two_images_row_block` 函数

- [ ] **Step 1: 写失败测试**

```python
def test_two_images_row_block(subdoc, style_map, registry):
    block = {
        "type": "two_images_row",
        "images": [
            {"path": "missing_left.png", "width_cm": 7, "caption": "图1a"},
            {"path": "missing_right.png", "width_cm": 7, "caption": "图1b"},
        ],
    }
    registry.render(subdoc, block, style_map)
    assert len(subdoc.tables) == 1
    table = subdoc.tables[0]
    assert len(table.columns) == 2
    assert len(table.rows) == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_blocks.py::test_two_images_row_block -v`
Expected: FAIL

- [ ] **Step 3: 实现 add_two_images_row_block**

```python
def add_two_images_row_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    images = block["images"]
    if len(images) != 2:
        raise BlockRenderError(f"two_images_row requires exactly 2 images, got {len(images)}")

    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # 移除边框
    tbl = table._tbl
    tbl_pr = tbl.tblPr if tbl.tblPr is not None else OxmlElement("w:tblPr")
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "none")
        element.set(qn("w:sz"), "0")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "auto")
        borders.append(element)
    tbl_pr.append(borders)

    figure_style = _get_style_name(doc, style_map["figure_paragraph"], style_map["body"])
    caption_style = _get_style_name(doc, style_map["caption"], "Caption")

    for i, img in enumerate(images):
        cell = table.cell(0, i)
        cell.text = ""
        p = cell.paragraphs[0]
        p.style = doc.styles[figure_style] if figure_style in [s.name for s in doc.styles] else doc.styles[style_map["body"]]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        image_path = Path(img["path"])
        if image_path.exists():
            run = p.add_run()
            width_cm = img.get("width_cm")
            if width_cm is not None:
                run.add_picture(str(image_path), width=Cm(float(width_cm)))
            else:
                run.add_picture(str(image_path))
        else:
            p.add_run(f"[图片缺失：{image_path}]")

        if img.get("caption"):
            cp = cell.add_paragraph(str(img["caption"]))
            cp.style = doc.styles[caption_style] if caption_style in [s.name for s in doc.styles] else doc.styles[style_map["body"]]
            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    body_style = _get_style_name(doc, style_map["body"], "Normal")
    doc.add_paragraph("", style=body_style)
```

- [ ] **Step 4: 注册到 create_default_registry**

```python
registry.register("two_images_row", add_two_images_row_block)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_blocks.py::test_two_images_row_block -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/report_engine/blocks.py tests/test_blocks.py
git commit -m "feat(blocks): add two_images_row renderer"
```

---

### Task 6: P1 集成测试 — 全部 4 种 block 端到端

**Files:**
- Modify: `tests/test_blocks.py` — 新增集成测试

- [ ] **Step 1: 写集成测试**

```python
def test_p1_blocks_in_registry():
    registry = create_default_registry()
    assert "rich_paragraph" in registry._renderers
    assert "note" in registry._renderers
    assert "quote" in registry._renderers
    assert "two_images_row" in registry._renderers
```

- [ ] **Step 2: 运行全量测试**

Run: `pytest tests/ -v`
Expected: 全部 PASS，无回归

- [ ] **Step 3: Commit**

```bash
git add tests/test_blocks.py
git commit -m "test(blocks): add P1 integration test for registry completeness"
```

---

## P2：3 种 block 类型

### Task 7: 扩展 validator — 注册 P2 校验字段

**Files:**
- Modify: `src/report_engine/validator.py:10-18`

- [ ] **Step 1: 在 BLOCK_REQUIRED_FIELDS 中新增 P2 的 3 个条目**

```python
"P2 新增":
    "appendix_table": ["headers", "rows"],
    "checklist": ["items"],
    "horizontal_rule": [],
```

- [ ] **Step 2: 运行现有测试确保无回归**

Run: `pytest tests/test_validator.py -v`
Expected: 全部 PASS

- [ ] **Step 3: Commit**

```bash
git add src/report_engine/validator.py
git commit -m "feat(validator): register P2 block type required fields"
```

---

### Task 8: P2 renderer — appendix_table

**Files:**
- Modify: `src/report_engine/blocks.py` — 新增 `add_appendix_table_block` 函数
- Modify: `src/report_engine/blocks.py:12-22` — `DEFAULT_STYLE_MAP` 新增 `"appendix_table": "AppendixTable"`

- [ ] **Step 1: 写失败测试**

```python
def test_appendix_table_block(subdoc, style_map, registry):
    block = {
        "type": "appendix_table",
        "title": "附表1：经费预算",
        "headers": ["项目", "金额"],
        "rows": [["设备费", "50"]],
    }
    registry.render(subdoc, block, style_map)
    assert len(subdoc.tables) == 1
    table = subdoc.tables[0]
    assert len(table.rows) == 2  # header + 1 data row
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_blocks.py::test_appendix_table_block -v`
Expected: FAIL

- [ ] **Step 3: 实现 add_appendix_table_block**

复用 `add_table_block` 逻辑，仅样式名不同：

```python
def add_appendix_table_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    if block.get("title"):
        caption_style = _get_style_name(doc, style_map["caption"], "Caption")
        doc.add_paragraph(str(block["title"]), style=caption_style)

    headers = block["headers"]
    rows = block["rows"]
    table_style = block.get("style") or style_map.get("appendix_table", style_map["table"])
    table_style = _get_style_name(doc, table_style, "Table Grid")

    table = doc.add_table(rows=1, cols=len(headers))
    table.style = table_style

    hdr_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        hdr_cells[i].text = "" if header is None else str(header)

    for row in rows:
        row_cells = table.add_row().cells
        for i, value in enumerate(row):
            row_cells[i].text = "" if value is None else str(value)

    if block.get("force_borders", True):
        _set_table_borders(table)

    body_style = _get_style_name(doc, style_map["body"], "Normal")
    doc.add_paragraph("", style=body_style)
```

- [ ] **Step 4: 更新 DEFAULT_STYLE_MAP + 注册 registry**

```python
"appendix_table": "AppendixTable",
```
```python
registry.register("appendix_table", add_appendix_table_block)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_blocks.py::test_appendix_table_block -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/report_engine/blocks.py tests/test_blocks.py
git commit -m "feat(blocks): add appendix_table renderer"
```

---

### Task 9: P2 renderer — checklist

**Files:**
- Modify: `src/report_engine/blocks.py` — 新增 `add_checklist_block` 函数
- Modify: `src/report_engine/blocks.py:12-22` — `DEFAULT_STYLE_MAP` 新增 `"checklist": "Checklist"`

- [ ] **Step 1: 写失败测试**

```python
def test_checklist_block(subdoc, style_map, registry):
    block = {
        "type": "checklist",
        "items": [
            {"text": "已完成文献综述", "checked": True},
            {"text": "已提交伦理审查", "checked": False},
        ],
    }
    registry.render(subdoc, block, style_map)
    assert len(subdoc.paragraphs) == 2
    assert "☑" in subdoc.paragraphs[0].text
    assert "☐" in subdoc.paragraphs[1].text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_blocks.py::test_checklist_block -v`
Expected: FAIL

- [ ] **Step 3: 实现 add_checklist_block**

```python
def add_checklist_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    style_name = _get_style_name(doc, style_map.get("checklist", "Checklist"), style_map.get("bullet_list", style_map["body"]))
    for item in block["items"]:
        p = doc.add_paragraph(style=style_name)
        prefix = "☑" if item.get("checked", False) else "☐"
        p.add_run(f"{prefix} {str(item['text'])}")
```

- [ ] **Step 4: 更新 DEFAULT_STYLE_MAP + 注册 registry**

```python
"checklist": "Checklist",
```
```python
registry.register("checklist", add_checklist_block)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_blocks.py::test_checklist_block -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/report_engine/blocks.py tests/test_blocks.py
git commit -m "feat(blocks): add checklist renderer with ☐/☑ symbols"
```

---

### Task 10: P2 renderer — horizontal_rule

**Files:**
- Modify: `src/report_engine/blocks.py` — 新增 `add_horizontal_rule_block` 函数

- [ ] **Step 1: 写失败测试**

```python
def test_horizontal_rule_block(subdoc, style_map, registry):
    block = {"type": "horizontal_rule"}
    registry.render(subdoc, block, style_map)
    assert len(subdoc.paragraphs) == 1
    p = subdoc.paragraphs[0]
    # 检查段落有底部边框
    pPr = p._element.pPr
    assert pPr is not None
    pBdr = pPr.find(qn("w:pBdr"))
    assert pBdr is not None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_blocks.py::test_horizontal_rule_block -v`
Expected: FAIL

- [ ] **Step 3: 实现 add_horizontal_rule_block**

```python
def add_horizontal_rule_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    p = doc.add_paragraph()
    pPr = p._element.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "auto")
    pBdr.append(bottom)
    pPr.append(pBdr)
```

- [ ] **Step 4: 注册到 create_default_registry**

```python
registry.register("horizontal_rule", add_horizontal_rule_block)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_blocks.py::test_horizontal_rule_block -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/report_engine/blocks.py tests/test_blocks.py
git commit -m "feat(blocks): add horizontal_rule renderer"
```

---

### Task 11: P2 集成测试 + 全量回归

**Files:**
- Modify: `tests/test_blocks.py`

- [ ] **Step 1: 写 P2 注册完整性测试**

```python
def test_p2_blocks_in_registry():
    registry = create_default_registry()
    assert "appendix_table" in registry._renderers
    assert "checklist" in registry._renderers
    assert "horizontal_rule" in registry._renderers
```

- [ ] **Step 2: 运行全量测试**

Run: `pytest tests/ -v`
Expected: 全部 PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_blocks.py
git commit -m "test(blocks): add P2 integration test"
```

---

## P3：4 种 block 类型

### Task 12: 扩展 validator — 注册 P3 校验字段

**Files:**
- Modify: `src/report_engine/validator.py:10-18`

- [ ] **Step 1: 在 BLOCK_REQUIRED_FIELDS 中新增 P3 的 4 个条目**

```python
"P3 新增":
    "toc_placeholder": [],
    "code_block": ["code"],
    "formula": ["latex"],
    "columns": ["count", "columns"],
```

- [ ] **Step 2: 运行现有测试确保无回归**

Run: `pytest tests/test_validator.py -v`
Expected: 全部 PASS

- [ ] **Step 3: Commit**

```bash
git add src/report_engine/validator.py
git commit -m "feat(validator): register P3 block type required fields"
```

---

### Task 13: P3 renderer — toc_placeholder

**Files:**
- Modify: `src/report_engine/blocks.py` — 新增 `add_toc_placeholder_block` 函数

- [ ] **Step 1: 写失败测试**

```python
def test_toc_placeholder_block(subdoc, style_map, registry):
    block = {"type": "toc_placeholder", "title": "目 录"}
    registry.render(subdoc, block, style_map)
    # 至少有标题段落 + TOC 域段落
    assert len(subdoc.paragraphs) >= 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_blocks.py::test_toc_placeholder_block -v`
Expected: FAIL

- [ ] **Step 3: 实现 add_toc_placeholder_block**

```python
def add_toc_placeholder_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    title = block.get("title", "目录")
    title_style = _get_style_name(doc, style_map.get("heading_2", "Heading 2"), "Heading 2")
    doc.add_paragraph(str(title), style=title_style)

    # 插入 TOC 域代码
    p = doc.add_paragraph()
    run = p.add_run()
    fldChar_begin = OxmlElement("w:fldChar")
    fldChar_begin.set(qn("w:fldCharType"), "begin")
    run._element.append(fldChar_begin)

    run2 = p.add_run()
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = ' TOC \\o "1-3" \\h \\z \\u '
    run2._element.append(instrText)

    run3 = p.add_run()
    fldChar_separate = OxmlElement("w:fldChar")
    fldChar_separate.set(qn("w:fldCharType"), "separate")
    run3._element.append(fldChar_separate)

    run4 = p.add_run("[请右键更新域以生成目录]")

    run5 = p.add_run()
    fldChar_end = OxmlElement("w:fldChar")
    fldChar_end.set(qn("w:fldCharType"), "end")
    run5._element.append(fldChar_end)
```

- [ ] **Step 4: 注册到 create_default_registry**

```python
registry.register("toc_placeholder", add_toc_placeholder_block)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_blocks.py::test_toc_placeholder_block -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/report_engine/blocks.py tests/test_blocks.py
git commit -m "feat(blocks): add toc_placeholder renderer with TOC field code"
```

---

### Task 14: P3 renderer — code_block

**Files:**
- Modify: `src/report_engine/blocks.py` — 新增 `add_code_block_block` 函数
- Modify: `src/report_engine/blocks.py:12-22` — `DEFAULT_STYLE_MAP` 新增 `"code_block": "CodeBlock"`

- [ ] **Step 1: 写失败测试**

```python
def test_code_block_single_line(subdoc, style_map, registry):
    block = {"type": "code_block", "code": "print('hello')", "language": "python"}
    registry.render(subdoc, block, style_map)
    assert len(subdoc.paragraphs) >= 1

def test_code_block_multiline(subdoc, style_map, registry):
    block = {"type": "code_block", "code": "def foo():\n    return 1\n\nfoo()"}
    registry.render(subdoc, block, style_map)
    # 4 行代码 = 4 个段落
    assert len(subdoc.paragraphs) == 4
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_blocks.py::test_code_block_single_line -v`
Expected: FAIL

- [ ] **Step 3: 实现 add_code_block_block**

```python
def add_code_block_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    code = str(block["code"])
    lines = code.split("\n")
    style_name = _get_style_name(doc, style_map.get("code_block", "CodeBlock"), style_map["body"])

    for line in lines:
        p = doc.add_paragraph(style=style_name)
        run = p.add_run(line)
        run.font.name = "Courier New"
        run.font.size = Cm(0.28)  # ~8pt
        # 灰色底纹
        rPr = run._element.get_or_add_rPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "F2F2F2")
        rPr.append(shd)

    # 语言标注（可选）
    if block.get("language"):
        lang_style = _get_style_name(doc, style_map["body"], "Normal")
        lp = doc.add_paragraph(style=lang_style)
        lp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        lr = lp.add_run(str(block["language"]))
        lr.font.size = Cm(0.21)  # ~6pt
        lr.font.color.rgb = None  # 灰色通过 XML 设置
        rPr = lr._element.get_or_add_rPr()
        color = OxmlElement("w:color")
        color.set(qn("w:val"), "808080")
        rPr.append(color)
```

- [ ] **Step 4: 更新 DEFAULT_STYLE_MAP + 注册 registry**

```python
"code_block": "CodeBlock",
```
```python
registry.register("code_block", add_code_block_block)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_blocks.py -v -k code_block`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/report_engine/blocks.py tests/test_blocks.py
git commit -m "feat(blocks): add code_block renderer with monospace + gray bg"
```

---

### Task 15: P3 renderer — formula（三级降级）

**Files:**
- Modify: `src/report_engine/blocks.py` — 新增 `add_formula_block` 函数
- Modify: `pyproject.toml` — 可选依赖 `latex2mathml`

- [ ] **Step 1: 写失败测试**

```python
def test_formula_block_text_fallback(subdoc, style_map, registry):
    """纯文本降级：latex2mathml 不可用时的行为"""
    block = {"type": "formula", "latex": "E = mc^2", "caption": "公式1"}
    registry.render(subdoc, block, style_map)
    # 至少有公式段落 + 可选 caption
    assert len(subdoc.paragraphs) >= 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_blocks.py::test_formula_block_text_fallback -v`
Expected: FAIL

- [ ] **Step 3: 实现 add_formula_block**

```python
def add_formula_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    latex = str(block["latex"])

    # 方案 1: LaTeX → OMML（推荐）
    # python-docx 不直接支持 OMML 插入。完整实现需要：
    # 1. latex2mathml 将 LaTeX 转为 MathML
    # 2. 手动将 MathML XML 转为 OOXML OMML XML
    # 3. 通过 OxmlElement 插入到段落
    # 当前版本暂不实现方案 1，直接降级到方案 2。
    # 后续版本可通过自定义 omml.py 模块实现。
    omml_inserted = False

    # 方案 2: LaTeX → 图片（降级）
    if not omml_inserted:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from io import BytesIO

            fig, ax = plt.subplots(figsize=(0.01, 0.01))
            ax.axis("off")
            text = ax.text(0.5, 0.5, f"${latex}$", fontsize=14, ha="center", va="center")
            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=150, transparent=True)
            plt.close(fig)
            buf.seek(0)

            style_name = _get_style_name(doc, style_map["body"], "Normal")
            p = doc.add_paragraph(style=style_name)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run()
            run.add_picture(buf, width=Cm(8))
            omml_inserted = True
        except Exception:
            pass

    # 方案 3: 纯文本降级
    if not omml_inserted:
        style_name = _get_style_name(doc, style_map.get("code_block", "CodeBlock"), style_map["body"])
        p = doc.add_paragraph(style=style_name)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(latex)
        run.font.name = "Courier New"

    # caption（可选）
    if block.get("caption"):
        caption_style = _get_style_name(doc, style_map["caption"], "Caption")
        cp = doc.add_paragraph(str(block["caption"]), style=caption_style)
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

- [ ] **Step 4: 注册到 create_default_registry**

```python
registry.register("formula", add_formula_block)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_blocks.py::test_formula_block_text_fallback -v`
Expected: PASS（降级到纯文本）

- [ ] **Step 6: Commit**

```bash
git add src/report_engine/blocks.py tests/test_blocks.py
git commit -m "feat(blocks): add formula renderer with 3-level fallback"
```

---

### Task 16: P3 renderer — columns（嵌套 block）

**Files:**
- Modify: `src/report_engine/blocks.py` — 新增 `add_columns_block` 函数
- Modify: `src/report_engine/subdoc.py` — `build_subdoc` 已支持接收 `blocks` 参数（无需改动）

- [ ] **Step 1: 写失败测试**

```python
def test_columns_block(subdoc, style_map, registry):
    block = {
        "type": "columns",
        "count": 2,
        "columns": [
            [{"type": "paragraph", "text": "左列"}],
            [{"type": "paragraph", "text": "右列"}],
        ],
    }
    registry.render(subdoc, block, style_map)
    assert len(subdoc.tables) == 1
    table = subdoc.tables[0]
    assert len(table.columns) == 2
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_blocks.py::test_columns_block -v`
Expected: FAIL

- [ ] **Step 3: 实现 add_columns_block**

```python
def add_columns_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    count = int(block["count"])
    columns = block["columns"]
    if len(columns) != count:
        raise BlockRenderError(f"columns: expected {count} columns, got {len(columns)}")

    table = doc.add_table(rows=1, cols=count)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # 移除边框
    tbl = table._tbl
    tbl_pr = tbl.tblPr if tbl.tblPr is not None else OxmlElement("w:tblPr")
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "none")
        element.set(qn("w:sz"), "0")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "auto")
        borders.append(element)
    tbl_pr.append(borders)

    registry = create_default_registry()

    for i, col_blocks in enumerate(columns):
        cell = table.cell(0, i)
        cell.text = ""
        # 在单元格内渲染 blocks
        for b in col_blocks:
            # 使用单元格的第一个段落作为 doc 代理
            # 需要通过 cell.paragraphs[0] 或 cell.add_paragraph() 来添加内容
            registry.render(cell, b, style_map)

    body_style = _get_style_name(doc, style_map["body"], "Normal")
    doc.add_paragraph("", style=body_style)
```

注意：`registry.render(cell, b, style_map)` 需要 cell 对象支持 `add_paragraph()` 和 `add_table()` 方法。python-docx 的 `_Cell` 对象支持 `add_paragraph()` 但不支持 `add_table()`。如果 columns 内嵌套 table，需要特殊处理。

对于 P3 初始实现，限制 columns 内不支持嵌套 table 类型。

- [ ] **Step 4: 注册到 create_default_registry**

```python
registry.register("columns", add_columns_block)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_blocks.py::test_columns_block -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/report_engine/blocks.py tests/test_blocks.py
git commit -m "feat(blocks): add columns renderer with nested block support"
```

---

### Task 17: P3 集成测试 + 全量回归

**Files:**
- Modify: `tests/test_blocks.py`

- [ ] **Step 1: 写 P3 注册完整性测试**

```python
def test_p3_blocks_in_registry():
    registry = create_default_registry()
    assert "toc_placeholder" in registry._renderers
    assert "code_block" in registry._renderers
    assert "formula" in registry._renderers
    assert "columns" in registry._renderers
```

- [ ] **Step 2: 运行全量测试**

Run: `pytest tests/ -v`
Expected: 全部 PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_blocks.py
git commit -m "test(blocks): add P3 integration test"
```

---

## 收尾：更新文档和示例

### Task 18: 更新示例 payload

**Files:**
- Modify: `data/examples/grant_advanced_demo.json`

- [ ] **Step 1: 在示例 payload 的某个 section 中添加新 block 类型示例**

在现有 payload 的合适 section 中添加每种新 block 类型的示例。至少包含：
- 1 个 `rich_paragraph`
- 1 个 `note`
- 1 个 `quote`
- 1 个 `horizontal_rule`
- 1 个 `checklist`

- [ ] **Step 2: 运行 validate + render 验证**

Run:
```bash
report-engine validate --payload data/examples/grant_advanced_demo.json
report-engine render --template templates/grant/template.docx --payload data/examples/grant_advanced_demo.json --output output/test_new_blocks.docx
```

Expected: 成功，无报错

- [ ] **Step 3: Commit**

```bash
git add data/examples/grant_advanced_demo.json
git commit -m "docs: add new block type examples to demo payload"
```

---

### Task 19: 更新 payload spec 文档

**Files:**
- Modify: `docs/report_engine_payload_spec.md`

- [ ] **Step 1: 在 payload spec 的 block 类型章节中添加 11 种新类型的 JSON 示例和字段说明**

- [ ] **Step 2: Commit**

```bash
git add docs/report_engine_payload_spec.md
git commit -m "docs: add 11 new block types to payload spec"
```

---

## 总结

| 批次 | Task 范围 | Block 类型 | 状态 |
|------|-----------|-----------|------|
| P1 | Task 1-6 | rich_paragraph, note, quote, two_images_row | 待实施 |
| P2 | Task 7-11 | appendix_table, checklist, horizontal_rule | 待实施 |
| P3 | Task 12-17 | toc_placeholder, code_block, formula, columns | 待实施 |
| 收尾 | Task 18-19 | 示例 payload + 文档更新 | 待实施 |
