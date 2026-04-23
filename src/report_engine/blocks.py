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


def create_default_registry() -> BlockRegistry:
    registry = BlockRegistry()
    registry.register("heading", add_heading_block)
    registry.register("paragraph", add_paragraph_block)
    registry.register("bullet_list", add_bullet_list_block)
    registry.register("numbered_list", add_numbered_list_block)
    registry.register("table", add_table_block)
    registry.register("image", add_image_block)
    registry.register("page_break", add_page_break_block)
    return registry

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
    return registry
