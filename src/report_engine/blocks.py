from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict

from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm


DEFAULT_STYLE_MAP = {
    "heading_2": "Heading 2",
    "heading_3": "Heading 3",
    "body": "Body Text",
    "caption": "Caption",
    "legend": "Legend",
    "figure_paragraph": "Figure Paragraph",
    "table": "ResearchTable",
    "bullet_list": "List Bullet",
    "numbered_list": "List Number",
    "note": "Note",
    "quote": "Quote",
    "appendix_table": "AppendixTable",
    "checklist": "Checklist",
    "code_block": "CodeBlock",
}


class BlockRenderError(ValueError):
    pass


class BlockRegistry:
    def __init__(self) -> None:
        self._renderers: Dict[str, Callable[..., None]] = {}

    def register(self, block_type: str, renderer_fn: Callable[..., None]) -> None:
        self._renderers[block_type] = renderer_fn

    def render(self, doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
        block_type = block["type"]
        renderer = self._renderers.get(block_type)
        if renderer is None:
            raise BlockRenderError(f"Unsupported block type: {block_type}")
        renderer(doc, block, style_map)


def _get_style_name(doc: Any, preferred: str, fallback: str) -> str:
    style_names = {style.name for style in doc.styles}
    return preferred if preferred in style_names else fallback


def _set_table_borders(table: Any) -> None:
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)

    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "8")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "000000")


def add_heading_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    level = int(block.get("level", 2))
    if level <= 2:
        style_name = _get_style_name(doc, style_map["heading_2"], "Heading 2")
    else:
        style_name = _get_style_name(doc, style_map["heading_3"], "Heading 3")
    doc.add_paragraph(str(block["text"]), style=style_name)


def add_paragraph_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    style_name = _get_style_name(doc, style_map["body"], "Normal")
    doc.add_paragraph(str(block["text"]), style=style_name)


def add_bullet_list_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    style_name = _get_style_name(doc, style_map["bullet_list"], style_map["body"])
    for item in block["items"]:
        p = doc.add_paragraph(style=style_name)
        p.add_run(str(item))


def add_numbered_list_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    style_name = _get_style_name(doc, style_map["numbered_list"], style_map["body"])
    for item in block["items"]:
        p = doc.add_paragraph(style=style_name)
        p.add_run(str(item))


def add_page_break_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    p = doc.add_paragraph()
    run = p.add_run()
    run.add_break(WD_BREAK.PAGE)


def add_table_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    if block.get("title"):
        caption_style = _get_style_name(doc, style_map["caption"], "Caption")
        doc.add_paragraph(str(block["title"]), style=caption_style)

    headers = block["headers"]
    rows = block["rows"]
    table_style = block.get("style") or style_map["table"]
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


def add_image_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    image_path = Path(block["path"])

    figure_style = _get_style_name(doc, style_map["figure_paragraph"], style_map["body"])
    p = doc.add_paragraph(style=figure_style)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    if image_path.exists():
        run = p.add_run()
        width_cm = block.get("width_cm")
        if width_cm is not None:
            run.add_picture(str(image_path), width=Cm(float(width_cm)))
        else:
            run.add_picture(str(image_path))
    else:
        p.add_run(f"[图片缺失：{image_path}]")

    if block.get("caption"):
        caption_style = _get_style_name(doc, style_map["caption"], "Caption")
        cp = doc.add_paragraph(str(block["caption"]), style=caption_style)
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    if block.get("legend"):
        legend_style = _get_style_name(doc, style_map["legend"], style_map["body"])
        lp = doc.add_paragraph(str(block["legend"]), style=legend_style)
        lp.alignment = WD_ALIGN_PARAGRAPH.LEFT

    body_style = _get_style_name(doc, style_map["body"], "Normal")
    doc.add_paragraph("", style=body_style)


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


def add_note_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    style_name = _get_style_name(doc, style_map.get("note", "Note"), style_map["body"])
    p = doc.add_paragraph(style=style_name)
    prefix_run = p.add_run("注：")
    prefix_run.bold = True
    p.add_run(str(block["text"]))


def add_quote_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    quote_style = _get_style_name(doc, style_map.get("quote", "Quote"), style_map["body"])
    doc.add_paragraph(str(block["text"]), style=quote_style)
    if block.get("source"):
        source_style = _get_style_name(doc, style_map["body"], "Normal")
        sp = doc.add_paragraph(str(block["source"]), style=source_style)
        sp.alignment = WD_ALIGN_PARAGRAPH.RIGHT


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


def add_checklist_block(doc: Any, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
    style_name = _get_style_name(doc, style_map.get("checklist", "Checklist"), style_map.get("bullet_list", style_map["body"]))
    for item in block["items"]:
        p = doc.add_paragraph(style=style_name)
        prefix = "☑" if item.get("checked", False) else "☐"
        p.add_run(f"{prefix} {str(item['text'])}")


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
        rPr = lr._element.get_or_add_rPr()
        color = OxmlElement("w:color")
        color.set(qn("w:val"), "808080")
        rPr.append(color)


def create_default_registry() -> BlockRegistry:
    registry = BlockRegistry()
    registry.register("heading", add_heading_block)
    registry.register("paragraph", add_paragraph_block)
    registry.register("bullet_list", add_bullet_list_block)
    registry.register("numbered_list", add_numbered_list_block)
    registry.register("table", add_table_block)
    registry.register("image", add_image_block)
    registry.register("page_break", add_page_break_block)
    registry.register("rich_paragraph", add_rich_paragraph_block)
    registry.register("note", add_note_block)
    registry.register("quote", add_quote_block)
    registry.register("two_images_row", add_two_images_row_block)
    registry.register("appendix_table", add_appendix_table_block)
    registry.register("checklist", add_checklist_block)
    registry.register("horizontal_rule", add_horizontal_rule_block)
    registry.register("toc_placeholder", add_toc_placeholder_block)
    registry.register("code_block", add_code_block_block)
    return registry
