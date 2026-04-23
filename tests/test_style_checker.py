from docx import Document
from docx.enum.style import WD_STYLE_TYPE

from report_engine.style_checker import check_template_styles


def _save_doc(tmp_path, *, include_table_style=True, wrong_table_type=False):
    doc = Document()
    for name in [
        "Heading 2",
        "Heading 3",
        "Body Text",
        "Caption",
        "Legend",
        "Figure Paragraph",
        "List Bullet",
        "List Number",
    ]:
        try:
            doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        except ValueError:
            pass

    if include_table_style:
        try:
            style_type = WD_STYLE_TYPE.PARAGRAPH if wrong_table_type else WD_STYLE_TYPE.TABLE
            doc.styles.add_style("ResearchTable", style_type)
        except ValueError:
            pass

    path = tmp_path / "styled.docx"
    doc.save(path)
    return str(path)


def test_style_checker_all_present(tmp_path):
    path = _save_doc(tmp_path)
    result = check_template_styles(path)
    assert result.ok is True
    assert result.missing == []
    assert result.wrong_type == []


def test_style_checker_missing_table_style(tmp_path):
    path = _save_doc(tmp_path, include_table_style=False)
    result = check_template_styles(path)
    assert result.ok is False
    assert "ResearchTable" in result.missing


def test_style_checker_wrong_table_style_type(tmp_path):
    path = _save_doc(tmp_path, include_table_style=True, wrong_table_type=True)
    result = check_template_styles(path)
    assert result.ok is False
    assert "ResearchTable" in result.wrong_type
