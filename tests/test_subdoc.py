import pytest

from report_engine.blocks import BlockRenderError
from report_engine.subdoc import build_subdoc


@pytest.fixture
def style_map():
    return {
        "heading_1": "Heading 1",
        "heading_2": "Heading 2",
        "heading_3": "Heading 3",
        "heading_4": "Heading 4",
        "heading_5": "Heading 5",
        "body": "Body Text",
        "table_caption": "TableCaption",
        "figure_caption": "FigureCaption",
        "legend": "Legend",
        "figure_paragraph": "Figure Paragraph",
        "table": "ResearchTable",
        "bullet_list": "List Bullet",
        "numbered_list": "List Number",
    }


def test_build_subdoc_with_title_and_blocks(tpl, style_map):
    blocks = [
        {"type": "paragraph", "text": "正文"},
        {"type": "page_break"},
    ]
    subdoc = build_subdoc(tpl, blocks, style_map, title="章节标题", title_level=2)
    assert subdoc.paragraphs[0].text == "章节标题"
    assert any(p.text == "正文" for p in subdoc.paragraphs)


def test_build_subdoc_empty_blocks(tpl, style_map):
    subdoc = build_subdoc(tpl, [], style_map)
    assert len(subdoc.paragraphs) == 0


def test_build_subdoc_unsupported_block_raises(tpl, style_map):
    with pytest.raises(BlockRenderError, match="Unsupported block type"):
        build_subdoc(tpl, [{"type": "unknown"}], style_map)
