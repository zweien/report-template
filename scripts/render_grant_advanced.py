from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from report_engine.renderer import render_grant_advanced as _render_grant_advanced


def render_grant_advanced(template_path: str, output_path: str, payload: Dict[str, Any]) -> List[str]:
    """Compatibility wrapper preserved for existing callers."""
    return _render_grant_advanced(template_path, output_path, payload)


if __name__ == "__main__":
    payload_path = Path("grant_payload_advanced_demo.json")
    template_path = Path("grant_template_demo_clean_v3.docx")
    output_path = Path("grant_output_advanced_demo.docx")

    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    warnings = render_grant_advanced(str(template_path), str(output_path), payload)
    print(f"Generated: {output_path.resolve()}")
    for warning in warnings:
        print(f"WARNING: {warning}")
