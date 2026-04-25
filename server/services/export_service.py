import tempfile

from report_engine.renderer import render_report
from server.services.converter import draft_to_payload


def export_draft_to_docx(
    draft_data: dict,
    template_path: str,
    parsed_structure: dict,
) -> str:
    """Render a draft to .docx and return the output file path."""
    payload = draft_to_payload(draft_data, parsed_structure)
    output_path = tempfile.mktemp(suffix=".docx")
    render_report(
        template_path=template_path,
        payload=payload,
        output_path=output_path,
        check_template=False,
    )
    return output_path
