from report_engine.renderer import render_report


def test_render_report_outputs_docx(minimal_template, advanced_payload, tmp_path):
    output_path = tmp_path / "result.docx"
    warnings = render_report(minimal_template, str(output_path), advanced_payload)
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    assert isinstance(warnings, list)


def test_render_report_can_skip_template_checks(minimal_template, advanced_payload, tmp_path):
    broken_payload = dict(advanced_payload)
    broken_payload["attachments_bundle"] = None
    output_path = tmp_path / "result_no_checks.docx"
    warnings = render_report(
        minimal_template,
        str(output_path),
        broken_payload,
        check_template=False,
    )
    assert output_path.exists()
    assert isinstance(warnings, list)
