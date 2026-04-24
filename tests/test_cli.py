from docx import Document

from report_engine.cli import main


def test_cli_validate(payload_path):
    rc = main(["validate", "--payload", payload_path])
    assert rc == 0


def test_cli_check_template(minimal_template, payload_path):
    rc = main([
        "check-template",
        "--template",
        minimal_template,
        "--payload",
        payload_path,
    ])
    assert rc == 0


def test_cli_render(minimal_template, payload_path, tmp_path):
    output_path = tmp_path / "cli_render.docx"
    rc = main([
        "render",
        "--template",
        minimal_template,
        "--payload",
        payload_path,
        "--output",
        str(output_path),
    ])
    assert rc == 0
    assert output_path.exists()

    doc = Document(str(output_path))
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "测试项目" in full_text
    assert "测试单位" in full_text
    assert "研究目标" in full_text
    assert "这是测试正文。" in full_text
    assert "附件内容。" in full_text
    assert "不会输出。" not in full_text
