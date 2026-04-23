import pytest

from report_engine.blocks import BlockRenderError, BlockRegistry, create_default_registry


@pytest.fixture
def subdoc(tpl):
    return tpl.new_subdoc()


@pytest.fixture
def style_map():
    return {
        "heading_2": "Heading 2",
        "heading_3": "Heading 3",
        "body": "Body Text",
        "caption": "Caption",
        "legend": "Legend",
        "figure_paragraph": "Figure Paragraph",
        "table": "ResearchTable",
        "bullet_list": "List Bullet",
        "numbered_list": "List Number",
    }


def test_unknown_block_type_raises(subdoc, style_map):
    registry = BlockRegistry()
    with pytest.raises(BlockRenderError, match="Unsupported block type"):
        registry.render(subdoc, {"type": "unknown"}, style_map)


def test_heading_block(subdoc, style_map):
    registry = create_default_registry()
    registry.render(subdoc, {"type": "heading", "text": "标题", "level": 2}, style_map)
    assert subdoc.paragraphs[0].text == "标题"


def test_paragraph_block(subdoc, style_map):
    registry = create_default_registry()
    registry.render(subdoc, {"type": "paragraph", "text": "正文"}, style_map)
    assert subdoc.paragraphs[0].text == "正文"


def test_bullet_list_block(subdoc, style_map):
    registry = create_default_registry()
    registry.render(subdoc, {"type": "bullet_list", "items": ["A", "B"]}, style_map)
    assert len(subdoc.paragraphs) == 2
    assert subdoc.paragraphs[0].text == "A"


def test_numbered_list_block(subdoc, style_map):
    registry = create_default_registry()
    registry.render(subdoc, {"type": "numbered_list", "items": ["1", "2"]}, style_map)
    assert len(subdoc.paragraphs) == 2


def test_table_block(subdoc, style_map):
    registry = create_default_registry()
    registry.render(
        subdoc,
        {"type": "table", "title": "表1", "headers": ["A"], "rows": [["1"]]},
        style_map,
    )
    assert len(subdoc.tables) == 1
    assert subdoc.tables[0].rows[0].cells[0].text == "A"
    assert subdoc.tables[0].rows[1].cells[0].text == "1"


def test_image_block_missing_file(subdoc, style_map):
    registry = create_default_registry()
    registry.render(subdoc, {"type": "image", "path": "missing.png"}, style_map)
    assert any("图片缺失" in p.text for p in subdoc.paragraphs)

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

def test_note_block(subdoc, style_map, registry):
    block = {"type": "note", "text": "本表数据为示意数据。"}
    registry.render(subdoc, block, style_map)
    assert len(subdoc.paragraphs) == 1
    p = subdoc.paragraphs[0]
    assert p.runs[0].text == "注："
    assert p.runs[0].bold is True
    assert p.runs[1].text == "本表数据为示意数据。"
