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
