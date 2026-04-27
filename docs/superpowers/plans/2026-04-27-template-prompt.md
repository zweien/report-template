# 模板内嵌 AI 提示词实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 report-engine 模板中支持 `[[PROMPT: ...]]` 注释语法，渲染时自动过滤，report-generator 分析时读取。

**Architecture:** 新增 `prompt_parser.py` 模块负责解析和过滤 PROMPT 段落；`renderer.py` 在渲染前调用过滤函数；`analyze_template.py` 在分析时提取 prompts 输出到 JSON。

**Tech Stack:** Python, python-docx, docxtpl, pytest

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `src/report_engine/prompt_parser.py` | 新增：解析 PROMPT 文本、过滤 PROMPT 段落、提取 prompts 列表 |
| `src/report_engine/renderer.py` | 修改：渲染前调用 `_filter_prompt_paragraphs()` 删除 PROMPT 段落 |
| `.claude/skills/report-generator/scripts/analyze_template.py` | 修改：分析结果中增加 `prompts` 字段 |
| `tests/test_prompt_parser.py` | 新增：prompt_parser 的单元测试 |
| `tests/test_renderer.py` | 修改：增加渲染过滤集成测试 |

---

### Task 1: prompt_parser 核心模块

**Files:**
- Create: `src/report_engine/prompt_parser.py`
- Test: `tests/test_prompt_parser.py`

- [ ] **Step 1: Write the failing test for `_parse_prompt_text`**

```python
import pytest
from report_engine.prompt_parser import _parse_prompt_text


def test_parse_full_prompt():
    text = "[[PROMPT: 立项依据: 请从国内外研究现状撰写 | mode=auto]]"
    result = _parse_prompt_text(text)
    assert result == {
        "target": "立项依据",
        "prompt": "请从国内外研究现状撰写",
        "mode": "auto",
        "level": "section",
    }


def test_parse_prompt_without_mode():
    text = "[[PROMPT: 研究目标: 列出3-5个具体目标]]"
    result = _parse_prompt_text(text)
    assert result == {
        "target": "研究目标",
        "prompt": "列出3-5个具体目标",
        "mode": "auto",
        "level": "section",
    }


def test_parse_paragraph_level_prompt():
    text = "[[PROMPT: 研究内容.技术路线: 描述技术路线 | mode=interactive]]"
    result = _parse_prompt_text(text)
    assert result == {
        "target": "研究内容.技术路线",
        "prompt": "描述技术路线",
        "mode": "interactive",
        "level": "paragraph",
    }


def test_parse_invalid_mode_defaults_to_auto():
    text = "[[PROMPT: 测试: 内容 | mode=invalid]]"
    result = _parse_prompt_text(text)
    assert result["mode"] == "auto"


def test_parse_multiline_prompt():
    text = "[[PROMPT: 立项依据: 请从以下几个方面撰写：\n1. 现状\n2. 意义 | mode=auto]]"
    result = _parse_prompt_text(text)
    assert result["target"] == "立项依据"
    assert "1. 现状" in result["prompt"]


def test_parse_empty_target_returns_none():
    text = "[[PROMPT: : 只有提示没有目标]]"
    assert _parse_prompt_text(text) is None


def test_parse_non_prompt_returns_none():
    assert _parse_prompt_text("普通段落文本") is None
    assert _parse_prompt_text("[[PROMPT: 没有结尾") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_prompt_parser.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'report_engine.prompt_parser'"

- [ ] **Step 3: Write minimal implementation**

```python
"""模板 PROMPT 注释解析器。

支持 [[PROMPT: 目标: 提示内容 | mode=auto/interactive]] 语法的解析和过滤。
"""

import logging
import re
from typing import Any, Dict, List, Optional

from docx import Document

logger = logging.getLogger("report_engine")

PROMPT_PREFIX = "[[PROMPT:"
PROMPT_SUFFIX = "]]"


def _parse_prompt_text(text: str) -> Optional[Dict[str, Any]]:
    """解析单个 PROMPT 注释文本。

    返回 dict: {target, prompt, mode, level} 或 None（解析失败时）。
    """
    text = text.strip()
    if not (text.startswith(PROMPT_PREFIX) and text.endswith(PROMPT_SUFFIX)):
        return None

    content = text[len(PROMPT_PREFIX) : -len(PROMPT_SUFFIX)].strip()
    if not content:
        logger.warning("Empty PROMPT content: %s", text)
        return None

    # 提取 mode（从最后一个 | 分隔的部分）
    mode = "auto"
    mode_match = re.search(r"\|\s*mode\s*=\s*(\w+)\s*$", content, re.IGNORECASE)
    if mode_match:
        mode_val = mode_match.group(1).lower()
        if mode_val in ("auto", "interactive"):
            mode = mode_val
        else:
            logger.warning("Invalid PROMPT mode '%s', defaulting to 'auto'", mode_val)
        content = content[: mode_match.start()].strip()

    # 分割目标和提示内容（第一个冒号）
    if ":" not in content:
        logger.warning("PROMPT missing target separator: %s", text)
        return None

    target, prompt = content.split(":", 1)
    target = target.strip()
    prompt = prompt.strip()

    if not target:
        logger.warning("PROMPT has empty target: %s", text)
        return None

    level = "paragraph" if "." in target else "section"

    return {
        "target": target,
        "prompt": prompt,
        "mode": mode,
        "level": level,
    }


def extract_prompts(doc: Document) -> List[Dict[str, Any]]:
    """从文档中提取所有 PROMPT 注释。

    Args:
        doc: python-docx Document 对象

    Returns:
        List[Dict]: 每个 dict 包含 target, prompt, mode, level
    """
    prompts = []
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        parsed = _parse_prompt_text(text)
        if parsed:
            prompts.append(parsed)
    return prompts


def _is_prompt_paragraph(paragraph) -> bool:
    """检查段落是否为 PROMPT 注释段落。"""
    text = paragraph.text.strip()
    return text.startswith(PROMPT_PREFIX) and text.endswith(PROMPT_SUFFIX)


def filter_prompt_paragraphs(doc: Document) -> int:
    """删除文档中的所有 PROMPT 注释段落。

    Args:
        doc: python-docx Document 对象（会被修改）

    Returns:
        int: 删除的段落数量
    """
    removed = 0
    # 从后往前删除，避免索引变化
    for idx in range(len(doc.paragraphs) - 1, -1, -1):
        paragraph = doc.paragraphs[idx]
        if _is_prompt_paragraph(paragraph):
            paragraph._element.getparent().remove(paragraph._element)
            removed += 1
    if removed:
        logger.debug("Removed %d PROMPT paragraph(s)", removed)
    return removed
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_prompt_parser.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add src/report_engine/prompt_parser.py tests/test_prompt_parser.py
git commit -m "$(cat <<'EOF'
feat: add prompt_parser module for [[PROMPT:...]] annotations

- _parse_prompt_text: parse target, prompt, mode, level
- extract_prompts: scan document for all prompts
- filter_prompt_paragraphs: remove prompt paragraphs from doc

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: renderer.py 集成过滤

**Files:**
- Modify: `src/report_engine/renderer.py:123-125`
- Test: `tests/test_renderer.py`

- [ ] **Step 1: Write the failing test**

在 `tests/test_renderer.py` 末尾添加：

```python
def test_render_report_filters_prompt_paragraphs(minimal_template, advanced_payload, tmp_path):
    """渲染时应自动删除 [[PROMPT: ...]] 段落。"""
    # 在 minimal_template 中添加 PROMPT 段落
    from docx import Document
    doc = Document(minimal_template)
    # 在第一个条件开关前插入 PROMPT 段落
    prompt_para = doc.add_paragraph("[[PROMPT: 研究内容: 请撰写研究内容 | mode=auto]]")
    # 将 PROMPT 段落移到条件开关之前
    body = doc.element.body
    body.insert(2, prompt_para._element)
    doc.save(minimal_template)

    output_path = tmp_path / "result_no_prompt.docx"
    render_report(minimal_template, str(output_path), advanced_payload)

    doc = Document(str(output_path))
    full_text = "\n".join(p.text for p in doc.paragraphs)

    # PROMPT 段落不应出现在输出中
    assert "[[PROMPT:" not in full_text
    assert "请撰写研究内容" not in full_text
    # 正常内容应保留
    assert "测试项目" in full_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_renderer.py::test_render_report_filters_prompt_paragraphs -v`
Expected: FAIL — PROMPT 文本出现在输出中

- [ ] **Step 3: Write minimal implementation**

修改 `src/report_engine/renderer.py`：

在文件顶部 imports 后添加：
```python
from report_engine.prompt_parser import filter_prompt_paragraphs
```

在 `render_report()` 函数中，`tpl = DocxTemplate(template_path)` 之后添加：
```python
    tpl = DocxTemplate(template_path)
    # 删除模板中的 PROMPT 注释段落
    filter_prompt_paragraphs(tpl.docx)
```

完整修改位置（renderer.py:123-125 附近）：
```python
    tpl = DocxTemplate(template_path)
    filter_prompt_paragraphs(tpl.docx)  # 新增
    context: Dict[str, Any] = dict(payload_model.context)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_renderer.py::test_render_report_filters_prompt_paragraphs -v`
Expected: PASS

- [ ] **Step 5: Run all renderer tests**

Run: `pytest tests/test_renderer.py -v`
Expected: 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/report_engine/renderer.py tests/test_renderer.py
git commit -m "$(cat <<'EOF'
feat(renderer): filter out [[PROMPT:...]] paragraphs before rendering

Call filter_prompt_paragraphs() after loading DocxTemplate to remove
prompt annotations before they reach the output document.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: analyze_template.py 集成 prompts 提取

**Files:**
- Modify: `.claude/skills/report-generator/scripts/analyze_template.py`

- [ ] **Step 1: Write the failing test（手动验证）**

创建一个带 PROMPT 的测试模板：

```bash
python3 -c "
from docx import Document
doc = Document()
doc.add_paragraph('{{PROJECT_NAME}}')
doc.add_paragraph('{%p if ENABLE_CONTENT %}')
doc.add_paragraph('[[PROMPT: 研究内容: 请撰写研究内容 | mode=auto]]')
doc.add_paragraph('{{p CONTENT_SUBDOC }}')
doc.add_paragraph('{%p endif %}')
doc.add_paragraph('[[PROMPT: 研究内容.技术路线: 描述路线 | mode=interactive]]')
doc.save('/tmp/test_prompt_template.docx')
"
```

运行 analyze_template：
```bash
python .claude/skills/report-generator/scripts/analyze_template.py --template /tmp/test_prompt_template.docx --json
```

Expected: 输出中没有 `prompts` 字段

- [ ] **Step 2: Modify analyze_template.py**

在文件顶部添加 import：
```python
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from report_engine.prompt_parser import extract_prompts
```

在 `analyze_template()` 函数中，在返回 dict 之前添加：
```python
    # 提取 PROMPT 注释
    prompts = extract_prompts(doc)

    return {
        ...
        "prompts": prompts,
    }
```

完整修改后的返回部分：
```python
    return {
        "path": template_path,
        "scalar_placeholders": sorted(set(scalars)),
        "subdoc_placeholders": sorted(set(subdocs)),
        "conditional_flags": sorted(set(flags)),
        "styles": sorted(styles),
        "headings": headings,
        "paragraphs_count": len(doc.paragraphs),
        "tables_count": len(doc.tables),
        "prompts": prompts,
    }
```

- [ ] **Step 3: Run analyze_template 验证**

```bash
python .claude/skills/report-generator/scripts/analyze_template.py --template /tmp/test_prompt_template.docx --json
```

Expected: JSON 输出中包含 `prompts` 字段，包含两个解析后的 prompt：
```json
{
  "prompts": [
    {
      "target": "研究内容",
      "prompt": "请撰写研究内容",
      "mode": "auto",
      "level": "section"
    },
    {
      "target": "研究内容.技术路线",
      "prompt": "描述路线",
      "mode": "interactive",
      "level": "paragraph"
    }
  ]
}
```

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/report-generator/scripts/analyze_template.py
git commit -m "$(cat <<'EOF'
feat(analyze_template): extract [[PROMPT:...]] annotations from templates

Add prompts field to analyze_template output, containing structured
prompt info (target, prompt text, mode, level).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: 端到端测试与回归验证

- [ ] **Step 1: Run full test suite**

```bash
pytest -q
```

Expected: All tests PASS (当前 67 个 + 新增 8 个 = 75 个)

- [ ] **Step 2: End-to-end verification**

使用现有模板渲染，确认 PROMPT 段落被过滤：

```bash
# 在 payload 示例模板中添加 PROMPT 后渲染
python3 -c "
from docx import Document
doc = Document('templates/project_proposal_template.docx')
# 在第一个章节前插入 PROMPT
body = doc.element.body
prompt = doc.add_paragraph('[[PROMPT: 立项依据: 测试提示词 | mode=auto]]')
body.insert(9, prompt._element)
doc.save('/tmp/test_e2e_template.docx')
"

report-engine render \
  --template /tmp/test_e2e_template.docx \
  --payload data/examples/project_proposal_payload.json \
  --output /tmp/test_e2e_output.docx

python3 -c "
from docx import Document
doc = Document('/tmp/test_e2e_output.docx')
full = '\n'.join(p.text for p in doc.paragraphs)
assert '[[PROMPT:' not in full, 'PROMPT should be filtered'
assert '测试提示词' not in full, 'prompt text should be filtered'
print('E2E PASS: PROMPT paragraphs are correctly filtered')
"
```

- [ ] **Step 3: Commit**

```bash
git commit --allow-empty -m "$(cat <<'EOF'
test: e2e verification for prompt annotation filtering

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Plan Self-Review

**1. Spec coverage:**
- ✅ 语法解析 → Task 1
- ✅ 渲染过滤 → Task 2
- ✅ analyze_template 提取 → Task 3
- ✅ 章节级/段落级 level 推断 → Task 1 `_parse_prompt_text`
- ✅ auto/interactive mode → Task 1 `_parse_prompt_text`
- ✅ 错误处理（非法 mode、空目标） → Task 1 tests

**2. Placeholder scan:** 无 TBD/TODO/"implement later" 等占位符。

**3. Type consistency:**
- `_parse_prompt_text` 返回 `Optional[Dict[str, Any]]` — 一致
- `filter_prompt_paragraphs` 参数 `doc: Document` — 一致
- `extract_prompts` 返回 `List[Dict[str, Any]]` — 一致

无类型不一致问题。

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-27-template-prompt.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
