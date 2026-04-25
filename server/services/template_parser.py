import re
from typing import List, Tuple
from zipfile import ZipFile


def _read_template_xml(template_path: str) -> str:
    with ZipFile(template_path) as zf:
        xml_parts = []
        for name in zf.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                xml_parts.append(zf.read(name).decode("utf-8", errors="ignore"))
        return "\n".join(xml_parts)


def _extract_scalar_vars(xml: str) -> List[str]:
    pattern = r"\{\{\s*([A-Z_][A-Z0-9_]*)\b"
    return sorted(set(re.findall(pattern, xml)))


def _extract_subdoc_placeholders(xml: str) -> List[str]:
    pattern = r"\{\{p\s+([A-Z_][A-Z0-9_]*)\s*\}\}"
    return sorted(set(re.findall(pattern, xml)))


def _extract_flags(xml: str) -> List[str]:
    pattern = r"\{%p\s+if\s+([A-Z_][A-Z0-9_]*)\s*%\}"
    return sorted(set(re.findall(pattern, xml)))


def _pair_flags_with_subdocs(flags, subdocs):
    sections = []
    for flag in flags:
        base = flag.replace("ENABLE_", "")
        placeholder = f"{base}_SUBDOC"
        if placeholder in subdocs:
            title = base.replace("_", " ").title()
            sections.append({
                "id": base.lower(),
                "placeholder": placeholder,
                "flag_name": flag,
                "title": title,
                "required_styles": [],
            })
    return sections


def parse_template(template_path: str) -> Tuple[dict, List[str]]:
    warnings = []
    xml = _read_template_xml(template_path)
    scalar_vars = _extract_scalar_vars(xml)
    subdocs = _extract_subdoc_placeholders(xml)
    flags = _extract_flags(xml)
    context_vars = [v for v in scalar_vars if not v.startswith("ENABLE_")]
    sections = _pair_flags_with_subdocs(flags, subdocs)

    paired_subdocs = {s["placeholder"] for s in sections}
    for sd in subdocs:
        if sd not in paired_subdocs and sd != "APPENDICES_SUBDOC":
            warnings.append(f"Subdoc {sd} has no ENABLE flag, will default to enabled")

    if not sections:
        warnings.append("No recognizable sections found in template")

    attachments_bundle = None
    if "APPENDICES_SUBDOC" in subdocs:
        attachments_bundle = {"placeholder": "APPENDICES_SUBDOC", "flag_name": "ENABLE_APPENDICES"}

    structure = {
        "context_vars": context_vars,
        "sections": sections,
        "attachments_bundle": attachments_bundle,
        "required_styles": [],
    }
    return structure, warnings
