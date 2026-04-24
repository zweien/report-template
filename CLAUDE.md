# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **report-engine**, a Python library for generating `.docx` Word reports from structured JSON payloads using `docxtpl` + `python-docx`. The core design principle is: **the template owns styles/layout, the payload owns content structure, and complex rich text is rendered via subdocs** (not shoved into the main template). There are 19 supported block types (heading, paragraph, rich_paragraph, bullet_list, numbered_list, table, image, page_break, note, quote, two_images_row, appendix_table, checklist, horizontal_rule, toc_placeholder, code_block, formula, ascii_diagram, columns).

## Development Commands

- Install dependencies: `pip install -e ".[dev]"` (or `pip install -r requirements.txt`)
- Run all tests: `pytest`
- Run single test file: `pytest tests/test_blocks.py -v`
- Run single test: `pytest tests/test_blocks.py::test_heading_block -v`
- CLI entry point after install: `report-engine --help`

## CLI Usage

```bash
# Validate a payload JSON
report-engine validate --payload data/examples/grant_advanced_demo.json

# Check that a template satisfies placeholder/flag/style contracts for a payload
report-engine check-template \
  --template templates/grant_template_demo_clean_v3.docx \
  --payload data/examples/grant_advanced_demo.json

# Render a report
report-engine render \
  --template templates/grant_template_demo_clean_v3.docx \
  --payload data/examples/grant_advanced_demo.json \
  --output output/demo.docx
```

## High-Level Architecture

### Rendering Pipeline

`render_report()` in `src/report_engine/renderer.py` is the main orchestrator:

1. **Normalize** — `compat.normalize_payload()` migrates legacy top-level fields (e.g. `project_name`) into `context`.
2. **Validate** — `validator.validate_payload()` checks Pydantic schema, required block fields, duplicate IDs/placeholders/flags, and optionally verifies image paths exist (`strict_images=True`).
3. **Template Checks** (optional, `check_template=True`) — `style_checker.ensure_template_styles()` verifies required paragraph/table styles exist; `template_checker.ensure_template_contract()` verifies all placeholders and Jinja flags referenced by the payload exist in the template XML.
4. **Build Context** — For each enabled `Section`, render its blocks into a subdoc via `subdoc.build_subdoc()` and assign to the placeholder variable. For each enabled `Attachment`, do the same. If `attachments_bundle` is enabled, concatenate all enabled attachments (with optional page breaks and titles) into a single `APPENDICES_SUBDOC` subdoc.
5. **Render & Save** — `DocxTemplate.render(context)` + `save()`.

### Module Responsibilities

| Module | Role |
|--------|------|
| `schema.py` | Pydantic models: `Payload`, `Section`, `Attachment`, `AttachmentsBundle`, `Block` |
| `compat.py` | Legacy field normalization (`project_name` → `context["PROJECT_NAME"]`) and default `style_map` injection |
| `validator.py` | Runtime payload validation: schema, block required fields, duplicates, image existence |
| `style_checker.py` | Verify template contains required styles (`Heading 2`, `Body Text`, `ResearchTable`, etc.) with correct types |
| `template_checker.py` | Verify template XML contains all placeholders (`RESEARCH_CONTENT_SUBDOC`) and Jinja flags (`ENABLE_RESEARCH_CONTENT`) declared by payload |
| `blocks.py` | `BlockRegistry` + 18 block renderers. Each renderer takes a `doc` (or subdoc/cell), a block dict, and a `style_map`, and mutates the document in place. |
| `subdoc.py` | `build_subdoc(tpl, blocks, style_map)` — creates a new subdoc, optionally prepends a title heading, then renders all blocks sequentially |
| `renderer.py` | Main `render_report()` orchestrator and legacy `render_grant_advanced()` wrapper |
| `cli.py` | `argparse` subcommands: `validate`, `check-template`, `render` |

### Payload Structure

```json
{
  "context": { "PROJECT_NAME": "..." },
  "sections": [
    {
      "id": "research_content",
      "placeholder": "RESEARCH_CONTENT_SUBDOC",
      "flag_name": "ENABLE_RESEARCH_CONTENT",
      "enabled": true,
      "blocks": [{"type": "heading", "text": "...", "level": 2}, ...]
    }
  ],
  "attachments": [...],
  "attachments_bundle": {
    "enabled": true,
    "placeholder": "APPENDICES_SUBDOC",
    "flag_name": "ENABLE_APPENDICES"
  },
  "style_map": {}
}
```

- `context`: scalar Jinja variables for the main template (e.g. `{{PROJECT_NAME}}`).
- `sections`: each maps to a subdoc slot in the main template.
- `attachments`: each can render individually or be bundled into `attachments_bundle`.
- `attachments_bundle`: when enabled, all enabled attachments are concatenated into a single `APPENDICES_SUBDOC`.
- `style_map`: optional overrides for style names (e.g. `{"body": "My Body Text"}`).

### Two Payload Compatibility Levels

The codebase maintains backward compatibility with an older "basic" payload that only had a single `RESEARCH_CONTENT_SUBDOC`. The modern "advanced" payload supports multiple sections, attachments, and the appendices bundle.

- Basic example: `data/grant_payload_demo.json`
- Advanced example: `data/examples/grant_advanced_demo.json` (preferred for development)

**Important**: Do not run `check-template` with an advanced payload against a basic template. Missing placeholders/flags are expected in that mismatch.

### Template Requirements

A valid template must define:
- **Paragraph styles**: `Heading 2`, `Heading 3`, `Body Text`, `Caption`, `Legend`, `Figure Paragraph`, `List Bullet`, `List Number`, `Note`, `Quote`, `CodeBlock`, `Checklist`
- **Table styles**: `ResearchTable`, `AppendixTable` (optional, falls back to `ResearchTable`)
- **Placeholder variables**: e.g. `{{PROJECT_NAME}}`, `{{p RESEARCH_CONTENT_SUBDOC }}`
- **Jinja condition flags**: e.g. `{%p if ENABLE_RESEARCH_CONTENT %}`

See `docs/report_engine_template_spec.md` for full spec and `scripts/build_test_template.py` for a reference generator.

### Tests

Tests are in `tests/` and use `pytest`. `conftest.py` provides:
- `registry` — a default `BlockRegistry`
- `minimal_template` — a programmatically built `.docx` with required styles and placeholders
- `advanced_payload` — a full advanced payload dict
- `tpl` — `DocxTemplate(minimal_template)`

To add a new block type: register a renderer in `blocks.py`, add required fields to `validator.BLOCK_REQUIRED_FIELDS`, and add tests in `tests/test_blocks.py`.

## Development Workflow

When working on an Issue (e.g. #2, #3, #4, #5):

1. **Create a branch** from `master`:
   ```bash
   git checkout -b fix/issue-N-short-description
   ```
2. **Develop and test locally** — run `pytest` after every meaningful change.
3. **Commit** with conventional commit messages (e.g. `refactor: ...`, `test: ...`, `feat: ...`).
4. **Push the branch** and **open a Pull Request**:
   ```bash
   git push -u origin fix/issue-N-short-description
   gh pr create --title "..." --body "Closes #N"
   ```
5. **Wait for user confirmation** before merging. Do not merge without explicit approval.
