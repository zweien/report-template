from typing import Any, Dict


def generate_empty_sections(parsed_structure: dict) -> Dict[str, Any]:
    """Generate empty BlockNote blocks for each section in the template."""
    sections = {}
    for section in parsed_structure.get("sections", []):
        sections[section["id"]] = [
            {
                "id": f"heading-{section['id']}",
                "type": "heading",
                "props": {"level": 1},
                "content": [
                    {
                        "type": "text",
                        "text": section.get("title", section["id"]),
                    }
                ],
            }
        ]
    return sections


def generate_empty_context(parsed_structure: dict) -> Dict[str, str]:
    """Generate empty context variables from template."""
    return {var: "" for var in parsed_structure.get("context_vars", [])}
