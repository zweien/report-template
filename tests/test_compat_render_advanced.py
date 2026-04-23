from pathlib import Path

from scripts.render_grant_advanced import render_grant_advanced


def test_compat_wrapper_renders_docx(minimal_template, advanced_payload, tmp_path):
    output_path = tmp_path / "compat_output.docx"
    warnings = render_grant_advanced(minimal_template, str(output_path), advanced_payload)
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    assert isinstance(warnings, list)


def test_compat_wrapper_handles_disabled_section(minimal_template, advanced_payload, tmp_path):
    payload = dict(advanced_payload)
    output_path = tmp_path / "compat_disabled.docx"
    warnings = render_grant_advanced(minimal_template, str(output_path), payload)
    assert output_path.exists()
    assert isinstance(warnings, list)
