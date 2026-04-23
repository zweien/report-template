from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from zipfile import ZipFile

from report_engine.schema import Payload


@dataclass
class TemplateCheckResult:
    ok: bool
    missing_placeholders: List[str] = field(default_factory=list)
    missing_flags: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


class TemplateCheckError(ValueError):
    pass


def _read_template_xml(template_path: str) -> str:
    with ZipFile(template_path) as zf:
        xml_parts = []
        for name in zf.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                xml_parts.append(zf.read(name).decode("utf-8", errors="ignore"))
        return "\n".join(xml_parts)


def check_template_contract(template_path: str, payload: Payload) -> TemplateCheckResult:
    xml = _read_template_xml(template_path)

    missing_placeholders: List[str] = []
    missing_flags: List[str] = []
    warnings: List[str] = []
    notes: List[str] = []

    for section in payload.sections:
        token = section.placeholder
        if token not in xml:
            missing_placeholders.append(token)
        if section.flag_name and section.flag_name not in xml:
            missing_flags.append(section.flag_name)

    for attachment in payload.attachments:
        token = attachment.placeholder
        if token not in xml:
            missing_placeholders.append(token)
        if attachment.flag_name and attachment.flag_name not in xml:
            missing_flags.append(attachment.flag_name)

    if payload.attachments_bundle and payload.attachments_bundle.enabled:
        bundle = payload.attachments_bundle
        if bundle.placeholder not in xml:
            missing_placeholders.append(bundle.placeholder)
        if bundle.flag_name and bundle.flag_name not in xml:
            missing_flags.append(bundle.flag_name)

    # heuristic only: if placeholder exists but matching flag is absent, note likely fixed-title template usage
    if missing_flags and not missing_placeholders:
        notes.append("Some placeholders exist without matching flags; template may use fixed titles outside condition blocks.")

    return TemplateCheckResult(
        ok=not missing_placeholders and not missing_flags,
        missing_placeholders=missing_placeholders,
        missing_flags=missing_flags,
        warnings=warnings,
        notes=notes,
    )


def ensure_template_contract(template_path: str, payload: Payload) -> None:
    result = check_template_contract(template_path, payload)
    if not result.ok:
        parts = []
        if result.missing_placeholders:
            parts.append(f"missing placeholders: {', '.join(result.missing_placeholders)}")
        if result.missing_flags:
            parts.append(f"missing flags: {', '.join(result.missing_flags)}")
        raise TemplateCheckError("; ".join(parts))
