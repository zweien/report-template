from typing import Any, Dict


def generate_empty_sections(parsed_structure: dict) -> Dict[str, Any]:
    """Generate BlockNote blocks for each section, using template headings when available."""
    sections = {}
    for section in parsed_structure.get("sections", []):
        template_headings = section.get("template_headings", [])
        if template_headings:
            blocks = []
            for idx, h in enumerate(template_headings):
                blocks.append({
                    "id": f"heading-{section['id']}-{idx}",
                    "type": "heading",
                    "props": {"level": h.get("level", 1)},
                    "content": [{"type": "text", "text": h.get("text", "")}],
                })
            sections[section["id"]] = blocks
        else:
            sections[section["id"]] = [
                {
                    "id": f"heading-{section['id']}",
                    "type": "heading",
                    "props": {"level": 1},
                    "content": [{"type": "text", "text": section.get("title", section["id"])}],
                }
            ]
    return sections


def generate_empty_context(parsed_structure: dict) -> Dict[str, str]:
    """Generate empty context variables from template."""
    return {var: "" for var in parsed_structure.get("context_vars", [])}
