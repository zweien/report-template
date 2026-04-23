# 通用报告模板引擎 Specification

> Status: Draft for implementation  
> Companion plan: `docs/superpowers/plans/2026-04-23-report-engine-revised.md`

## 1. Overview

This specification defines the first-phase product and engineering requirements for a reusable, template-driven Word report engine built on top of the current grant-report prototype.

The intent of this spec is to make implementation unambiguous, reduce refactor risk, and keep the work aligned with the revised implementation plan.

This spec is the source of truth for:

- first-phase scope;
- compatibility guarantees;
- required engine behaviors;
- validation and checking requirements;
- CLI behavior;
- acceptance criteria.

---

## 2. Problem Statement

The repository already contains a working prototype for rendering grant application documents from structured JSON into `.docx` templates using `docxtpl` and `python-docx`.

However, the current implementation is prototype-style and has several limitations:

- rendering logic is concentrated in scripts rather than reusable modules;
- validation is not explicit enough before rendering;
- template style requirements are implicit;
- template placeholder/flag contract is not checked systematically;
- migration risk is high if the current script is rewritten from scratch.

The engine must therefore evolve from a one-off script into a maintainable local project without breaking the working advanced demo path.

---

## 3. Goals

### 3.1 Phase 1 goals

The system shall provide:

1. a modular Python package for report rendering;
2. structured payload validation before rendering;
3. explicit template style checking before rendering;
4. explicit template placeholder / section-flag contract checking before rendering;
5. a compatibility layer preserving the current advanced rendering flow;
6. a CLI for local validation, checking, and rendering;
7. a clear path for future multi-template and Agent Skill expansion.

### 3.2 Non-goals for Phase 1

The system shall not require or implement in Phase 1:

- Agent Skill packaging;
- LLM-driven prompt-to-payload orchestration;
- breaking payload schema changes for current examples;
- broad expansion to many new block types beyond proven demand;
- UI or web application packaging.

---

## 4. Existing Baseline to Preserve

The implementation must preserve the current baseline represented by:

- `scripts/render_grant_advanced.py`
- `data/grant_payload_advanced_demo.json`
- `docs/grant_render_advanced_readme.md`

The baseline currently supports:

- multiple section subdocs;
- multiple attachments;
- bundled appendix rendering via `APPENDICES_SUBDOC`;
- section and attachment enable/disable switches;
- block-based content rendering.

This baseline is not optional. It is the migration anchor for Phase 1.

---

## 5. Compatibility Requirements

### 5.1 Script compatibility

The existing script path `scripts/render_grant_advanced.py` must remain usable in Phase 1.

The file may be converted into a thin wrapper around the new package API, but the repository must continue to support the current invocation pattern and advanced demo scenario.

### 5.2 Payload compatibility

The system must continue to accept the current advanced payload structure, including:

- `context`
- `sections`
- `attachments`
- `attachments_bundle`
- `style_map`

The compatibility layer must also continue to accept legacy top-level fields where present, including but not limited to:

- `project_name`
- `applicant_org`
- `project_leader`

### 5.3 Behavior compatibility

The Phase 1 engine must preserve the observable behavior of the current advanced flow unless a stricter pre-render validation is intentionally added.

Examples:

- sections marked `enabled=false` must remain effectively disabled;
- bundled appendices must still render;
- current block ordering semantics must remain intact;
- missing-image placeholder behavior may remain, subject to validator/checker policy.

---

## 6. Core Design Principles

The implementation shall follow these principles:

1. the main template owns fixed layout and styles;
2. complex body content is rendered through subdocs, not large inline Jinja loops;
3. the engine consumes structured JSON payloads, not Word-rich text fragments;
4. validation and checking happen before render by default;
5. migration safety takes priority over greenfield elegance;
6. compatibility is preserved until replacement behavior is verified by tests.

---

## 7. Target Package Structure

The package should follow this logical structure:

- `src/report_engine/schema.py`
- `src/report_engine/blocks.py`
- `src/report_engine/subdoc.py`
- `src/report_engine/validator.py`
- `src/report_engine/style_checker.py`
- `src/report_engine/template_checker.py`
- `src/report_engine/renderer.py`
- `src/report_engine/compat.py`
- `src/report_engine/cli.py`

Supporting files may include:

- `pyproject.toml`
- `tests/...`
- `data/examples/...`
- `templates/...`

`schema.yaml` may exist later, but it is not a required first-phase dependency.

---

## 8. Functional Requirements

### 8.1 Payload schema

The engine shall define explicit Pydantic models for at least:

- `Block`
- `Section`
- `Attachment`
- `AttachmentsBundle`
- `Payload`

The models must:

- avoid mutable literal defaults;
- allow extensible block fields;
- allow `context` values beyond plain strings;
- preserve compatibility with current payload naming.

### 8.2 Block types

Phase 1 must support these block types:

- `heading`
- `paragraph`
- `bullet_list`
- `numbered_list`
- `table`
- `image`
- `page_break`

Unknown block types must raise explicit errors rather than fail silently.

### 8.3 Subdoc construction

The engine shall build section and attachment content as subdocs.

Subdoc construction must support:

- ordered block rendering;
- optional title insertion;
- style map overrides;
- integration with a reusable block registry.

### 8.4 Payload validation

The engine shall validate payloads before rendering.

Validation must cover at least:

- schema conformance;
- block-specific required fields;
- duplicate section ids;
- duplicate attachment ids;
- duplicate placeholders;
- duplicate flags where disallowed;
- image path existence policy.

### 8.5 Style checking

The engine shall check required template styles before rendering.

Style checks must verify both:

- style existence;
- expected style type.

The checker must distinguish at least:

- paragraph styles;
- table styles.

### 8.6 Template contract checking

The engine shall check that the template contains the placeholders and control structure required by the payload.

At minimum, the checker must detect:

- missing section subdoc placeholders;
- missing appendix bundle placeholder when bundle rendering is enabled;
- mismatches between expected flags and template usage conventions.

The checker should also provide warnings for risky patterns when detectable.

### 8.7 Rendering

The renderer shall:

- load the main template;
- normalize payload through the compatibility layer;
- build subdocs for sections and attachments;
- support bundled appendices;
- assemble final rendering context;
- write the output `.docx` file.

### 8.8 CLI

Phase 1 shall expose a CLI with at least these commands:

- `validate`
- `check-template`
- `render`

`render` shall, by default, run validation and template checks before document generation.

---

## 9. Required Style Contract

The template must provide the styles needed by the engine. At minimum, Phase 1 expects:

### Paragraph styles

- `Heading 2`
- `Heading 3`
- `Body Text`
- `Caption`
- `Legend`
- `Figure Paragraph`
- `List Bullet`
- `List Number`

### Table styles

- `ResearchTable`

The checker must report missing styles and wrong-type styles separately.

---

## 10. Required Template Contract

The template contract must support the following patterns:

- section subdoc placeholders such as `{{p RESEARCH_CONTENT_SUBDOC }}`;
- bundle placeholder such as `{{p APPENDICES_SUBDOC }}`;
- optional control flags such as `{%p if ENABLE_RESEARCH_CONTENT %}`.

Recommended template usage is:

```text
{%p if ENABLE_RESEARCH_CONTENT %}
二、研究内容
{{p RESEARCH_CONTENT_SUBDOC }}
{%p endif %}
```

If the title remains outside the conditional block, the system may warn, because hiding the section content alone may leave a dangling heading.

---

## 11. CLI Behavior Specification

### 11.1 `validate`

Input:
- payload path

Behavior:
- load payload;
- run schema and structural validation;
- return success or actionable errors.

### 11.2 `check-template`

Input:
- template path
- payload path

Behavior:
- load payload;
- run style checks;
- run template contract checks;
- return success, warnings, and actionable errors.

### 11.3 `render`

Input:
- template path
- payload path
- output path

Behavior:
- run validation;
- run template checks;
- render document if checks pass;
- write output file.

Optional fallback flags may be added later, but they must not silently weaken the default safety path.

---

## 12. Error Handling Requirements

Errors must be explicit and actionable.

The engine should prefer:

- fail fast for structural payload errors;
- separate reporting for missing styles vs wrong style types;
- separate reporting for missing placeholders vs contract warnings;
- configurable warning/error policy for missing image files.

The system must avoid a workflow where document generation appears successful but silently produces malformed formatting due to missing styles or template mismatch.

---

## 13. Testing Requirements

The implementation must include tests for:

1. compatibility baseline behavior;
2. schema models;
3. block rendering;
4. subdoc construction;
5. validator behavior;
6. style checker behavior;
7. template checker behavior;
8. renderer integration;
9. CLI smoke paths.

Compatibility tests are mandatory and must be created before aggressive refactor work.

---

## 14. Acceptance Criteria

Phase 1 is accepted only if all of the following are true:

1. the advanced demo still renders successfully through the compatibility script path;
2. the new package API can render the same scenario;
3. style issues are surfaced before rendering;
4. template placeholder/flag issues are surfaced before rendering;
5. CLI supports `validate`, `check-template`, and `render`;
6. tests cover both compatibility and modularized behavior;
7. the repository shows incremental evolution rather than disconnected rewrite.

---

## 15. Phase 2 Boundary

After Phase 1 stabilizes, a separate specification may define:

- Agent Skill integration;
- payload preview / confirmation flow;
- LLM-assisted structured payload generation;
- richer block types such as `quote`, `note`, or `two_images_row`.

Those items are intentionally outside this spec.
