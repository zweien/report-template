# 通用报告模板引擎 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有项目申报书原型重构为通用报告模板引擎，含模块化渲染架构、CLI 工具和 Agent Skill。

**Architecture:** 扁平模块结构，`src/report_engine/` 下按职责拆分（schema / blocks / subdoc / validator / style_checker / renderer / cli）。Agent Skill 包裹整个流程，输出结构化 JSON 供用户确认后渲染。

**Tech Stack:** Python 3.10+, docxtpl, python-docx, pydantic, pyyaml, pytest

---

## File Structure

| File | Responsibility |
|---|---|
| `pyproject.toml` | 项目元数据、依赖、CLI 入口 |
| `src/report_engine/__init__.py` | 包初始化、版本号 |
| `src/report_engine/schema.py` | Pydantic model：Payload / Section / Attachment / Block |
| `src/report_engine/blocks.py` | BlockRegistry 注册表 + 7 种 block 渲染函数 |
| `src/report_engine/subdoc.py` | SubdocBuilder：遍历 blocks 构建子文档 |
| `src/report_engine/validator.py` | Payload 校验：Pydantic + 图片路径 + block 字段完整性 |
| `src/report_engine/style_checker.py` | 模板样式缺失检查 |
| `src/report_engine/renderer.py` | TemplateRenderer：编排渲染全流程 |
| `src/report_engine/cli.py` | CLI 入口：list-templates / validate / check-styles / render |
| `templates/grant/template.docx` | 申报书模板（从现有文件复制） |
| `templates/grant/schema.yaml` | 模板元数据（占位符、样式） |
| `data/examples/grant_demo.json` | 基础示例数据（迁移） |
| `data/examples/grant_advanced_demo.json` | 进阶示例数据（迁移） |
| `tests/conftest.py` | 测试公共 fixture |
| `tests/test_schema.py` | Schema 模型测试 |
| `tests/test_blocks.py` | Block 注册表 + 渲染器测试 |
| `tests/test_subdoc.py` | Subdoc 构建器测试 |
| `tests/test_validator.py` | 校验器测试 |
| `tests/test_style_checker.py` | 样式检查测试 |
| `tests/test_renderer.py` | 渲染器集成测试 |
| `tests/test_cli.py` | CLI 测试 |

---

### Task 1: 项目脚手架

**Files:**
- Create: `pyproject.toml`
- Create: `src/report_engine/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `output/.gitkeep`
- Create: `assets/.gitkeep`
- Modify: `requirements.txt`
- Init: git repo

- [ ] **Step 1: 初始化 git 仓库**

```bash
cd /home/z/codebase/report-template
git init
```

- [ ] **Step 2: 创建目录结构**

```bash
mkdir -p src/report_engine tests templates/grant data/examples output assets skills/report-generator
```

- [ ] **Step 3: 创建 pyproject.toml**

```toml
[project]
name = "report-engine"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "docxtpl[subdoc]",
    "python-docx",
    "pydantic>=2.0",
    "pyyaml",
]

[project.optional-dependencies]
dev = ["pytest"]

[project.scripts]
report-engine = "report_engine.cli:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 4: 更新 requirements.txt**

```
docxtpl[subdoc]
python-docx
pydantic>=2.0
pyyaml
pytest
```

- [ ] **Step 5: 创建 src/report_engine/__init__.py**

```python
"""通用报告模板引擎"""

__version__ = "0.1.0"
```

- [ ] **Step 6: 创建 tests/__init__.py**（空文件）

- [ ] **Step 7: 创建 tests/conftest.py**

```python
import json
from pathlib import Path
from typing import Any, Dict

import pytest
from docx import Document
from docxtpl import DocxTemplate


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture
def minimal_template(tmp_path: Path) -> str:
    """创建最小 docxtpl 测试模板，包含常用占位符和样式。"""
    doc = Document()

    # 确保样式存在
    from docx.enum.style import WD_STYLE_TYPE

    styles_to_add = {
        "Heading 2": WD_STYLE_TYPE.PARAGRAPH,
        "Heading 3": WD_STYLE_TYPE.PARAGRAPH,
        "Body Text": WD_STYLE_TYPE.PARAGRAPH,
        "Caption": WD_STYLE_TYPE.PARAGRAPH,
        "Legend": WD_STYLE_TYPE.PARAGRAPH,
        "Figure Paragraph": WD_STYLE_TYPE.PARAGRAPH,
        "List Bullet": WD_STYLE_TYPE.PARAGRAPH,
        "List Number": WD_STYLE_TYPE.PARAGRAPH,
    }
    for name, style_type in styles_to_add.items():
        try:
            doc.styles.add_style(name, style_type)
        except ValueError:
            pass

    doc.add_paragraph("{{PROJECT_NAME}}", style="Normal")
    doc.add_paragraph("{%p if ENABLE_RESEARCH_CONTENT %}", style="Normal")
    doc.add_paragraph("{{p RESEARCH_CONTENT_SUBDOC }}", style="Normal")
    doc.add_paragraph("{%p endif %}", style="Normal")
    doc.add_paragraph("{%p if ENABLE_APPENDICES %}", style="Normal")
    doc.add_paragraph("{{p APPENDICES_SUBDOC }}", style="Normal")
    doc.add_paragraph("{%p endif %}", style="Normal")

    path = str(tmp_path / "test_template.docx")
    doc.save(path)
    return path


@pytest.fixture
def tpl(minimal_template: str) -> DocxTemplate:
    return DocxTemplate(minimal_template)


@pytest.fixture
def grant_payload() -> Dict[str, Any]:
    return {
        "context": {
            "PROJECT_NAME": "测试项目",
            "APPLICANT_ORG": "测试单位",
        },
        "sections": [
            {
                "id": "research_content",
                "placeholder": "RESEARCH_CONTENT_SUBDOC",
                "flag_name": "ENABLE_RESEARCH_CONTENT",
                "enabled": True,
                "blocks": [
                    {"type": "heading", "text": "研究目标", "level": 2},
                    {"type": "paragraph", "text": "这是测试正文。"},
                ],
            }
        ],
        "attachments": [],
        "attachments_bundle": {
            "enabled": True,
            "placeholder": "APPENDICES_SUBDOC",
            "flag_name": "ENABLE_APPENDICES",
        },
    }
```

- [ ] **Step 8: 创建 output/.gitkeep 和 assets/.gitkeep**

```bash
touch output/.gitkeep assets/.gitkeep
```

- [ ] **Step 9: 创建 .gitignore**

```
__pycache__/
*.pyc
*.egg-info/
dist/
build/
output/*.docx
!output/.gitkeep
.venv/
```

- [ ] **Step 10: 安装依赖并验证**

```bash
pip install -e ".[dev]"
python -c "from report_engine import __version__; print(__version__)"
```

Expected: `0.1.0`

- [ ] **Step 11: 提交**

```bash
git add -A
git commit -m "chore: init project scaffolding with pyproject.toml"
```

---

### Task 2: Pydantic Schema 模型

**Files:**
- Create: `src/report_engine/schema.py`
- Create: `tests/test_schema.py`

- [ ] **Step 1: 写 schema 模型的失败测试**

```python
# tests/test_schema.py
import pytest
from pydantic import ValidationError

from report_engine.schema import (
    AttachmentsBundle,
    Block,
    Payload,
    Section,
    Attachment,
)


class TestBlock:
    def test_accepts_type_only(self):
        b = Block(type="heading")
        assert b.type == "heading"

    def test_accepts_extra_fields(self):
        b = Block(type="heading", text="标题", level=2)
        assert b.text == "标题"
        assert b.level == 2

    def test_requires_type(self):
        with pytest.raises(ValidationError):
            Block()


class TestSection:
    def test_minimal(self):
        s = Section(id="test", placeholder="TEST_SUBDOC", blocks=[])
        assert s.id == "test"
        assert s.enabled is True
        assert s.blocks == []

    def test_full(self):
        s = Section(
            id="research",
            placeholder="RESEARCH_SUBDOC",
            flag_name="ENABLE_RESEARCH",
            enabled=False,
            blocks=[Block(type="paragraph", text="hello")],
        )
        assert s.flag_name == "ENABLE_RESEARCH"
        assert s.enabled is False

    def test_requires_id_and_placeholder(self):
        with pytest.raises(ValidationError):
            Section(placeholder="X")
        with pytest.raises(ValidationError):
            Section(id="x")


class TestAttachment:
    def test_minimal(self):
        a = Attachment(id="app1", placeholder="APP1_SUBDOC", blocks=[])
        assert a.enabled is True

    def test_with_title(self):
        a = Attachment(
            id="app1",
            placeholder="APP1_SUBDOC",
            title="附件1",
            blocks=[Block(type="paragraph", text="内容")],
        )
        assert a.title == "附件1"


class TestAttachmentsBundle:
    def test_defaults(self):
        b = AttachmentsBundle()
        assert b.enabled is True
        assert b.placeholder == "APPENDICES_SUBDOC"
        assert b.flag_name == "ENABLE_APPENDICES"
        assert b.page_break_between_attachments is True
        assert b.include_attachment_title is True


class TestPayload:
    def test_minimal(self):
        p = Payload(context={"PROJECT_NAME": "测试"})
        assert p.sections == []
        assert p.attachments == []

    def test_full(self):
        p = Payload(
            context={"PROJECT_NAME": "测试"},
            sections=[
                Section(id="s1", placeholder="S1_SUBDOC", blocks=[])
            ],
            attachments=[
                Attachment(id="a1", placeholder="A1_SUBDOC", blocks=[])
            ],
            attachments_bundle=AttachmentsBundle(),
            style_map={"body": "Body Text"},
        )
        assert len(p.sections) == 1
        assert p.style_map["body"] == "Body Text"

    def test_context_required(self):
        with pytest.raises(ValidationError):
            Payload()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_schema.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'report_engine.schema'`

- [ ] **Step 3: 实现 schema.py**

```python
# src/report_engine/schema.py
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class Block(BaseModel):
    type: str
    model_config = ConfigDict(extra="allow")


class Section(BaseModel):
    id: str
    placeholder: str
    flag_name: Optional[str] = None
    enabled: bool = True
    blocks: List[Block] = []


class Attachment(BaseModel):
    id: str
    placeholder: str
    flag_name: Optional[str] = None
    enabled: bool = True
    title: Optional[str] = None
    title_level: int = 2
    blocks: List[Block] = []


class AttachmentsBundle(BaseModel):
    enabled: bool = True
    placeholder: str = "APPENDICES_SUBDOC"
    flag_name: str = "ENABLE_APPENDICES"
    page_break_between_attachments: bool = True
    include_attachment_title: bool = True


class Payload(BaseModel):
    context: Dict[str, str]
    sections: List[Section] = []
    attachments: List[Attachment] = []
    attachments_bundle: Optional[AttachmentsBundle] = None
    style_map: Optional[Dict[str, str]] = None
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_schema.py -v
```

Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add src/report_engine/schema.py tests/test_schema.py
git commit -m "feat: add Pydantic schema models for payload validation"
```

---

### Task 3: Block 注册表 + 7 种 Block 渲染器

**Files:**
- Create: `src/report_engine/blocks.py`
- Create: `tests/test_blocks.py`

- [ ] **Step 1: 写 Block 注册表和渲染器的失败测试**

```python
# tests/test_blocks.py
import pytest
from docx import Document
from docxtpl import DocxTemplate

from report_engine.blocks import BlockRegistry, create_default_registry


@pytest.fixture
def subdoc(tpl: DocxTemplate):
    return tpl.new_subdoc()


@pytest.fixture
def style_map():
    return {
        "heading_2": "Heading 2",
        "heading_3": "Heading 3",
        "body": "Body Text",
        "caption": "Caption",
        "legend": "Legend",
        "figure_paragraph": "Figure Paragraph",
        "table": "ResearchTable",
        "bullet_list": "List Bullet",
        "numbered_list": "List Number",
    }


class TestBlockRegistry:
    def test_unknown_type_raises(self, subdoc, style_map):
        registry = BlockRegistry()
        with pytest.raises(ValueError, match="Unsupported block type"):
            registry.render(subdoc, {"type": "unknown"}, style_map)

    def test_register_and_call(self, subdoc, style_map):
        registry = BlockRegistry()
        called = []

        def fake_renderer(doc, block, sm):
            called.append(block["text"])

        registry.register("fake", fake_renderer)
        registry.render(subdoc, {"type": "fake", "text": "hello"}, style_map)
        assert called == ["hello"]


class TestHeadingBlock:
    def test_heading_level2(self, subdoc, style_map):
        registry = create_default_registry()
        registry.render(subdoc, {"type": "heading", "text": "标题", "level": 2}, style_map)
        assert len(subdoc.paragraphs) == 1
        assert subdoc.paragraphs[0].text == "标题"

    def test_heading_default_level(self, subdoc, style_map):
        registry = create_default_registry()
        registry.render(subdoc, {"type": "heading", "text": "标题"}, style_map)
        assert len(subdoc.paragraphs) == 1


class TestParagraphBlock:
    def test_paragraph(self, subdoc, style_map):
        registry = create_default_registry()
        registry.render(subdoc, {"type": "paragraph", "text": "正文内容"}, style_map)
        assert len(subdoc.paragraphs) == 1
        assert subdoc.paragraphs[0].text == "正文内容"


class TestBulletListBlock:
    def test_bullet_list(self, subdoc, style_map):
        registry = create_default_registry()
        registry.render(
            subdoc,
            {"type": "bullet_list", "items": ["项目1", "项目2"]},
            style_map,
        )
        assert len(subdoc.paragraphs) == 2
        assert subdoc.paragraphs[0].text == "项目1"


class TestNumberedListBlock:
    def test_numbered_list(self, subdoc, style_map):
        registry = create_default_registry()
        registry.render(
            subdoc,
            {"type": "numbered_list", "items": ["步骤1", "步骤2"]},
            style_map,
        )
        assert len(subdoc.paragraphs) == 2


class TestTableBlock:
    def test_table_with_title(self, subdoc, style_map):
        registry = create_default_registry()
        registry.render(
            subdoc,
            {
                "type": "table",
                "title": "表1 测试",
                "headers": ["A", "B"],
                "rows": [["1", "2"]],
            },
            style_map,
        )
        # title paragraph + table + trailing paragraph
        assert len(subdoc.paragraphs) >= 2
        assert subdoc.tables[0].rows[0].cells[0].text == "A"
        assert subdoc.tables[0].rows[1].cells[0].text == "1"

    def test_table_without_title(self, subdoc, style_map):
        registry = create_default_registry()
        registry.render(
            subdoc,
            {"type": "table", "headers": ["X"], "rows": [["val"]]},
            style_map,
        )
        assert len(subdoc.tables) == 1


class TestImageBlock:
    def test_missing_image_inserts_placeholder(self, subdoc, style_map):
        registry = create_default_registry()
        registry.render(
            subdoc,
            {"type": "image", "path": "nonexistent.png"},
            style_map,
        )
        assert any("图片缺失" in p.text for p in subdoc.paragraphs)

    def test_image_with_caption_and_legend(self, subdoc, style_map):
        registry = create_default_registry()
        registry.render(
            subdoc,
            {
                "type": "image",
                "path": "nonexistent.png",
                "caption": "图1 测试图",
                "legend": "注：说明文字",
            },
            style_map,
        )
        texts = [p.text for p in subdoc.paragraphs]
        assert any("图1 测试图" in t for t in texts)
        assert any("注：说明文字" in t for t in texts)


class TestPageBreakBlock:
    def test_page_break(self, subdoc, style_map):
        registry = create_default_registry()
        registry.render(subdoc, {"type": "page_break"}, style_map)
        assert len(subdoc.paragraphs) == 1
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_blocks.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 实现 blocks.py**

```python
# src/report_engine/blocks.py
from pathlib import Path
from typing import Any, Callable, Dict, List

from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm


DEFAULT_STYLE_MAP = {
    "heading_2": "Heading 2",
    "heading_3": "Heading 3",
    "body": "Body Text",
    "caption": "Caption",
    "legend": "Legend",
    "figure_paragraph": "Figure Paragraph",
    "table": "ResearchTable",
    "bullet_list": "List Bullet",
    "numbered_list": "List Number",
}


class BlockRegistry:
    def __init__(self):
        self._renderers: Dict[str, Callable] = {}

    def register(self, block_type: str, renderer_fn: Callable) -> None:
        self._renderers[block_type] = renderer_fn

    def render(self, doc, block: Dict[str, Any], style_map: Dict[str, str]) -> None:
        block_type = block["type"]
        fn = self._renderers.get(block_type)
        if fn is None:
            raise ValueError(f"Unsupported block type: {block_type}")
        fn(doc, block, style_map)


def _get_style(doc, preferred: str, fallback: str) -> str:
    names = {s.name for s in doc.styles}
    return preferred if preferred in names else fallback


def _set_table_borders(table) -> None:
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        el = borders.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            borders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "8")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")


def _add_heading(doc, block: Dict[str, Any], sm: Dict[str, str]) -> None:
    level = block.get("level", 2)
    style = sm.get("heading_2", "Heading 2") if level <= 2 else sm.get("heading_3", "Heading 3")
    style = _get_style(doc, style, "Normal")
    doc.add_paragraph(str(block["text"]), style=style)


def _add_paragraph(doc, block: Dict[str, Any], sm: Dict[str, str]) -> None:
    style = _get_style(doc, sm.get("body", "Body Text"), "Normal")
    doc.add_paragraph(str(block["text"]), style=style)


def _add_bullet_list(doc, block: Dict[str, Any], sm: Dict[str, str]) -> None:
    style = _get_style(doc, sm.get("bullet_list", "List Bullet"), sm.get("body", "Normal"))
    for item in block["items"]:
        p = doc.add_paragraph(style=style)
        p.add_run(str(item))


def _add_numbered_list(doc, block: Dict[str, Any], sm: Dict[str, str]) -> None:
    style = _get_style(doc, sm.get("numbered_list", "List Number"), sm.get("body", "Normal"))
    for item in block["items"]:
        p = doc.add_paragraph(style=style)
        p.add_run(str(item))


def _add_table(doc, block: Dict[str, Any], sm: Dict[str, str]) -> None:
    if block.get("title"):
        cap_style = _get_style(doc, sm.get("caption", "Caption"), "Normal")
        doc.add_paragraph(str(block["title"]), style=cap_style)

    headers = block["headers"]
    rows = block["rows"]
    table_style = block.get("style") or sm.get("table", "Table Grid")
    table_style = _get_style(doc, table_style, "Table Grid")

    table = doc.add_table(rows=1, cols=len(headers))
    table.style = table_style

    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = "" if h is None else str(h)
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = "" if val is None else str(val)

    if block.get("force_borders", True):
        _set_table_borders(table)

    body_style = _get_style(doc, sm.get("body", "Body Text"), "Normal")
    doc.add_paragraph("", style=body_style)


def _add_image(doc, block: Dict[str, Any], sm: Dict[str, str]) -> None:
    fig_style = _get_style(doc, sm.get("figure_paragraph", "Figure Paragraph"), sm.get("body", "Normal"))
    p = doc.add_paragraph(style=fig_style)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    image_path = Path(block["path"])
    if image_path.exists():
        run = p.add_run()
        width = block.get("width_cm")
        if width is not None:
            run.add_picture(str(image_path), width=Cm(float(width)))
        else:
            run.add_picture(str(image_path))
    else:
        p.add_run(f"[图片缺失：{image_path}]")

    if block.get("caption"):
        cap_style = _get_style(doc, sm.get("caption", "Caption"), "Normal")
        cp = doc.add_paragraph(str(block["caption"]), style=cap_style)
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    if block.get("legend"):
        leg_style = _get_style(doc, sm.get("legend", "Legend"), sm.get("body", "Normal"))
        lp = doc.add_paragraph(str(block["legend"]), style=leg_style)
        lp.alignment = WD_ALIGN_PARAGRAPH.LEFT

    body_style = _get_style(doc, sm.get("body", "Body Text"), "Normal")
    doc.add_paragraph("", style=body_style)


def _add_page_break(doc, block: Dict[str, Any], sm: Dict[str, str]) -> None:
    p = doc.add_paragraph()
    run = p.add_run()
    run.add_break(WD_BREAK.PAGE)


def create_default_registry() -> BlockRegistry:
    registry = BlockRegistry()
    registry.register("heading", _add_heading)
    registry.register("paragraph", _add_paragraph)
    registry.register("bullet_list", _add_bullet_list)
    registry.register("numbered_list", _add_numbered_list)
    registry.register("table", _add_table)
    registry.register("image", _add_image)
    registry.register("page_break", _add_page_break)
    return registry
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_blocks.py -v
```

Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add src/report_engine/blocks.py tests/test_blocks.py
git commit -m "feat: add BlockRegistry with 7 block renderers"
```

---

### Task 4: Subdoc 构建器

**Files:**
- Create: `src/report_engine/subdoc.py`
- Create: `tests/test_subdoc.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_subdoc.py
import pytest
from docxtpl import DocxTemplate

from report_engine.subdoc import build_subdoc


@pytest.fixture
def style_map():
    return {
        "heading_2": "Heading 2",
        "heading_3": "Heading 3",
        "body": "Body Text",
        "caption": "Caption",
        "legend": "Legend",
        "figure_paragraph": "Figure Paragraph",
        "table": "ResearchTable",
        "bullet_list": "List Bullet",
        "numbered_list": "List Number",
    }


def test_build_subdoc_with_blocks(tpl: DocxTemplate, style_map):
    blocks = [
        {"type": "heading", "text": "标题", "level": 2},
        {"type": "paragraph", "text": "正文"},
        {"type": "page_break"},
    ]
    subdoc = build_subdoc(tpl, blocks, style_map)
    # heading + paragraph + page_break
    assert len(subdoc.paragraphs) == 3


def test_build_subdoc_with_title(tpl: DocxTemplate, style_map):
    blocks = [{"type": "paragraph", "text": "内容"}]
    subdoc = build_subdoc(tpl, blocks, style_map, title="章节标题", title_level=2)
    # title heading + content paragraph
    assert len(subdoc.paragraphs) == 2
    assert subdoc.paragraphs[0].text == "章节标题"


def test_build_subdoc_empty_blocks(tpl: DocxTemplate, style_map):
    subdoc = build_subdoc(tpl, [], style_map)
    assert len(subdoc.paragraphs) == 0


def test_build_subdoc_unsupported_block_raises(tpl: DocxTemplate, style_map):
    with pytest.raises(ValueError, match="Unsupported block type"):
        build_subdoc(tpl, [{"type": "unknown"}], style_map)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_subdoc.py -v
```

- [ ] **Step 3: 实现 subdoc.py**

```python
# src/report_engine/subdoc.py
from typing import Any, Dict, List, Optional

from docxtpl import DocxTemplate

from report_engine.blocks import BlockRegistry, create_default_registry, DEFAULT_STYLE_MAP


def build_subdoc(
    tpl: DocxTemplate,
    blocks: List[Dict[str, Any]],
    style_map: Optional[Dict[str, str]] = None,
    registry: Optional[BlockRegistry] = None,
    title: Optional[str] = None,
    title_level: int = 2,
) -> Any:
    sm = dict(DEFAULT_STYLE_MAP)
    if style_map:
        sm.update(style_map)

    reg = registry or create_default_registry()
    subdoc = tpl.new_subdoc()

    if title:
        reg.render(subdoc, {"type": "heading", "text": title, "level": title_level}, sm)

    for block in blocks:
        reg.render(subdoc, block, sm)

    return subdoc
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_subdoc.py -v
```

- [ ] **Step 5: 提交**

```bash
git add src/report_engine/subdoc.py tests/test_subdoc.py
git commit -m "feat: add SubdocBuilder"
```

---

### Task 5: 样式检查器

**Files:**
- Create: `src/report_engine/style_checker.py`
- Create: `tests/test_style_checker.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_style_checker.py
import pytest
from docx import Document

from report_engine.style_checker import check_template_styles, StyleCheckResult


@pytest.fixture
def style_map():
    return {
        "heading_2": "Heading 2",
        "body": "Body Text",
        "table": "ResearchTable",
    }


def _save_doc_with_styles(tmp_path, style_names):
    """创建包含指定样式的 docx 文件。"""
    doc = Document()
    from docx.enum.style import WD_STYLE_TYPE

    for name in style_names:
        try:
            doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        except ValueError:
            pass
    path = str(tmp_path / "styled.docx")
    doc.save(path)
    return path


def test_all_styles_present(tmp_path, style_map):
    path = _save_doc_with_styles(tmp_path, ["Heading 2", "Body Text", "ResearchTable"])
    result = check_template_styles(path, style_map)
    assert result.missing == []
    assert result.ok is True


def test_missing_styles_reported(tmp_path, style_map):
    path = _save_doc_with_styles(tmp_path, ["Heading 2"])
    result = check_template_styles(path, style_map)
    assert "Body Text" in result.missing
    assert "ResearchTable" in result.missing
    assert result.ok is False


def test_empty_style_map_passes(tmp_path):
    path = _save_doc_with_styles(tmp_path, [])
    result = check_template_styles(path, {})
    assert result.ok is True
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_style_checker.py -v
```

- [ ] **Step 3: 实现 style_checker.py**

```python
# src/report_engine/style_checker.py
from dataclasses import dataclass, field
from typing import Dict, List

from docx import Document


@dataclass
class StyleCheckResult:
    missing: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.missing) == 0


def check_template_styles(template_path: str, style_map: Dict[str, str]) -> StyleCheckResult:
    doc = Document(template_path)
    available = {s.name for s in doc.styles}
    required = set(style_map.values())
    missing = sorted(required - available)
    return StyleCheckResult(missing=missing)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_style_checker.py -v
```

- [ ] **Step 5: 提交**

```bash
git add src/report_engine/style_checker.py tests/test_style_checker.py
git commit -m "feat: add style checker for template validation"
```

---

### Task 6: Payload 校验器

**Files:**
- Create: `src/report_engine/validator.py`
- Create: `tests/test_validator.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_validator.py
import json
import pytest
from pathlib import Path

from report_engine.validator import validate_payload, ValidationResult


def test_valid_payload_passes():
    payload = {
        "context": {"PROJECT_NAME": "测试"},
        "sections": [],
    }
    result = validate_payload(payload)
    assert result.ok is True
    assert result.errors == []


def test_invalid_payload_fails():
    result = validate_payload({"sections": "bad"})
    assert result.ok is False
    assert len(result.errors) > 0


def test_missing_image_warns(tmp_path):
    payload = {
        "context": {"PROJECT_NAME": "测试"},
        "sections": [
            {
                "id": "s1",
                "placeholder": "S1_SUBDOC",
                "blocks": [
                    {"type": "image", "path": "nonexistent.png"},
                ],
            }
        ],
    }
    result = validate_payload(payload, base_dir=tmp_path)
    assert result.ok is True
    assert len(result.warnings) > 0
    assert any("nonexistent.png" in w for w in result.warnings)


def test_existing_image_no_warning(tmp_path):
    img = tmp_path / "test.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    payload = {
        "context": {"PROJECT_NAME": "测试"},
        "sections": [
            {
                "id": "s1",
                "placeholder": "S1_SUBDOC",
                "blocks": [
                    {"type": "image", "path": "test.png"},
                ],
            }
        ],
    }
    result = validate_payload(payload, base_dir=tmp_path)
    assert len(result.warnings) == 0


def test_block_field_validation():
    payload = {
        "context": {"PROJECT_NAME": "测试"},
        "sections": [
            {
                "id": "s1",
                "placeholder": "S1_SUBDOC",
                "blocks": [
                    {"type": "heading"},
                ],
            }
        ],
    }
    result = validate_payload(payload)
    assert result.ok is False
    assert any("text" in e for e in result.errors)


def test_json_string_input():
    json_str = json.dumps({"context": {"PROJECT_NAME": "测试"}})
    result = validate_payload(json_str)
    assert result.ok is True
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_validator.py -v
```

- [ ] **Step 3: 实现 validator.py**

```python
# src/report_engine/validator.py
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from report_engine.schema import Payload


BLOCK_REQUIRED_FIELDS = {
    "heading": ["text"],
    "paragraph": ["text"],
    "bullet_list": ["items"],
    "numbered_list": ["items"],
    "table": ["headers", "rows"],
    "image": ["path"],
    "page_break": [],
}


@dataclass
class ValidationResult:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def validate_payload(
    payload: Union[Dict[str, Any], str],
    base_dir: Optional[Path] = None,
) -> ValidationResult:
    result = ValidationResult()

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as e:
            result.errors.append(f"Invalid JSON: {e}")
            return result

    # Pydantic schema 校验
    try:
        parsed = Payload.model_validate(payload)
    except Exception as e:
        result.errors.append(str(e))
        return result

    # Block 字段完整性校验
    all_blocks = []
    for section in parsed.sections:
        all_blocks.extend(section.blocks)
    for attachment in parsed.attachments:
        all_blocks.extend(attachment.blocks)

    for i, block in enumerate(all_blocks):
        required = BLOCK_REQUIRED_FIELDS.get(block.type)
        if required is None:
            result.errors.append(f"Block #{i}: unknown type '{block.type}'")
            continue
        for field_name in required:
            if not hasattr(block, field_name) or getattr(block, field_name) is None:
                result.errors.append(
                    f"Block #{i} (type={block.type}): missing required field '{field_name}'"
                )

    # 图片路径检查
    base = base_dir or Path(".")
    for i, block in enumerate(all_blocks):
        if block.type == "image" and hasattr(block, "path"):
            img_path = base / block.path
            if not img_path.exists():
                result.warnings.append(f"Block #{i}: image not found: {block.path}")

    return result
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_validator.py -v
```

- [ ] **Step 5: 提交**

```bash
git add src/report_engine/validator.py tests/test_validator.py
git commit -m "feat: add payload validator with block field and image checks"
```

---

### Task 7: TemplateRenderer 主渲染器

**Files:**
- Create: `src/report_engine/renderer.py`
- Create: `tests/test_renderer.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_renderer.py
import json
from pathlib import Path

import pytest
from docx import Document
from docxtpl import DocxTemplate

from report_engine.renderer import TemplateRenderer


@pytest.fixture
def style_map():
    return {
        "heading_2": "Heading 2",
        "heading_3": "Heading 3",
        "body": "Body Text",
        "caption": "Caption",
        "legend": "Legend",
        "figure_paragraph": "Figure Paragraph",
        "table": "ResearchTable",
        "bullet_list": "List Bullet",
        "numbered_list": "List Number",
    }


def test_render_basic_context(minimal_template, tmp_path, style_map):
    payload = {
        "context": {"PROJECT_NAME": "测试项目名称"},
        "sections": [],
        "style_map": style_map,
    }
    output = str(tmp_path / "output.docx")
    renderer = TemplateRenderer(minimal_template)
    renderer.render(payload, output)

    doc = Document(output)
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "测试项目名称" in full_text


def test_render_with_section(minimal_template, tmp_path, style_map):
    payload = {
        "context": {"PROJECT_NAME": "测试"},
        "sections": [
            {
                "id": "research_content",
                "placeholder": "RESEARCH_CONTENT_SUBDOC",
                "flag_name": "ENABLE_RESEARCH_CONTENT",
                "enabled": True,
                "blocks": [
                    {"type": "heading", "text": "研究目标", "level": 2},
                    {"type": "paragraph", "text": "正文内容"},
                ],
            }
        ],
        "style_map": style_map,
    }
    output = str(tmp_path / "output.docx")
    renderer = TemplateRenderer(minimal_template)
    renderer.render(payload, output)

    doc = Document(output)
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "研究目标" in full_text
    assert "正文内容" in full_text


def test_render_disabled_section_omitted(minimal_template, tmp_path, style_map):
    payload = {
        "context": {"PROJECT_NAME": "测试"},
        "sections": [
            {
                "id": "disabled_section",
                "placeholder": "RESEARCH_CONTENT_SUBDOC",
                "flag_name": "ENABLE_RESEARCH_CONTENT",
                "enabled": False,
                "blocks": [{"type": "paragraph", "text": "不应出现"}],
            }
        ],
        "style_map": style_map,
    }
    output = str(tmp_path / "output.docx")
    renderer = TemplateRenderer(minimal_template)
    renderer.render(payload, output)

    doc = Document(output)
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "不应出现" not in full_text


def test_render_with_attachments_bundle(minimal_template, tmp_path, style_map):
    payload = {
        "context": {"PROJECT_NAME": "测试"},
        "sections": [],
        "attachments": [
            {
                "id": "app1",
                "placeholder": "APP1_SUBDOC",
                "title": "附件1",
                "blocks": [{"type": "paragraph", "text": "附件内容"}],
            }
        ],
        "attachments_bundle": {
            "enabled": True,
            "placeholder": "APPENDICES_SUBDOC",
            "flag_name": "ENABLE_APPENDICES",
        },
        "style_map": style_map,
    }
    output = str(tmp_path / "output.docx")
    renderer = TemplateRenderer(minimal_template)
    renderer.render(payload, output)

    doc = Document(output)
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "附件1" in full_text
    assert "附件内容" in full_text
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_renderer.py -v
```

- [ ] **Step 3: 实现 renderer.py**

```python
# src/report_engine/renderer.py
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from docxtpl import DocxTemplate

from report_engine.blocks import DEFAULT_STYLE_MAP
from report_engine.schema import Payload
from report_engine.subdoc import build_subdoc
from report_engine.validator import validate_payload

logger = logging.getLogger(__name__)


class TemplateRenderer:
    def __init__(self, template_path: str):
        self.template_path = template_path

    def render(self, payload: Dict[str, Any], output_path: str) -> None:
        parsed = Payload.model_validate(payload)
        style_map = dict(DEFAULT_STYLE_MAP)
        if parsed.style_map:
            style_map.update(parsed.style_map)

        tpl = DocxTemplate(self.template_path)
        context = dict(parsed.context)

        # Sections
        for section in parsed.sections:
            flag = section.flag_name or f"ENABLE_{section.id.upper()}"
            context[flag] = section.enabled
            if section.enabled:
                context[section.placeholder] = build_subdoc(
                    tpl, [b.model_dump() for b in section.blocks], style_map
                )
            else:
                context[section.placeholder] = ""

        # Individual attachments
        enabled_attachments = []
        for att in parsed.attachments:
            flag = att.flag_name or f"ENABLE_{att.id.upper()}"
            context[flag] = att.enabled
            if att.enabled:
                enabled_attachments.append(att)
                context[att.placeholder] = build_subdoc(
                    tpl,
                    [b.model_dump() for b in att.blocks],
                    style_map,
                    title=att.title,
                    title_level=att.title_level,
                )
            else:
                context[att.placeholder] = ""

        # Bundle attachments
        if parsed.attachments_bundle and parsed.attachments_bundle.enabled and enabled_attachments:
            bundle = parsed.attachments_bundle
            context[bundle.flag_name] = True
            bundle_subdoc = tpl.new_subdoc()

            for idx, att in enumerate(enabled_attachments):
                if idx > 0 and bundle.page_break_between_attachments:
                    from report_engine.blocks import create_default_registry

                    reg = create_default_registry()
                    reg.render(bundle_subdoc, {"type": "page_break"}, style_map)

                sub = build_subdoc(
                    tpl,
                    [b.model_dump() for b in att.blocks],
                    style_map,
                    title=att.title if bundle.include_attachment_title else None,
                    title_level=att.title_level,
                )
                for element in sub.body:
                    bundle_subdoc.body.append(element)

            context[bundle.placeholder] = bundle_subdoc
        elif parsed.attachments_bundle:
            context[parsed.attachments_bundle.flag_name] = False
            context[parsed.attachments_bundle.placeholder] = ""

        tpl.render(context, autoescape=True)
        tpl.save(output_path)
        logger.info("Generated: %s", output_path)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_renderer.py -v
```

- [ ] **Step 5: 提交**

```bash
git add src/report_engine/renderer.py tests/test_renderer.py
git commit -m "feat: add TemplateRenderer with sections and attachments support"
```

---

### Task 8: CLI 入口

**Files:**
- Create: `src/report_engine/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_cli.py
import json
import subprocess
import sys
from pathlib import Path

import pytest


def _run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "report_engine.cli", *args],
        capture_output=True,
        text=True,
    )


def test_list_templates(project_root: Path):
    # 需要 templates/grant/ 存在（后续 Task 9 会迁移）
    result = _run_cli("list-templates")
    # 不应崩溃，返回码 0
    assert result.returncode == 0


def test_validate_valid_payload(tmp_path, project_root: Path):
    payload = {"context": {"PROJECT_NAME": "测试"}, "sections": []}
    payload_file = tmp_path / "test.json"
    payload_file.write_text(json.dumps(payload, ensure_ascii=False))
    result = _run_cli("validate", "--payload", str(payload_file))
    assert result.returncode == 0


def test_validate_invalid_payload(tmp_path):
    payload_file = tmp_path / "bad.json"
    payload_file.write_text("{bad json")
    result = _run_cli("validate", "--payload", str(payload_file))
    assert result.returncode != 0
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_cli.py -v
```

- [ ] **Step 3: 实现 cli.py**

```python
# src/report_engine/cli.py
import argparse
import json
import logging
import sys
from pathlib import Path

from report_engine.renderer import TemplateRenderer
from report_engine.validator import validate_payload

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


def _find_templates() -> list:
    templates = []
    if not TEMPLATES_DIR.exists():
        return templates
    for d in sorted(TEMPLATES_DIR.iterdir()):
        if d.is_dir() and (d / "template.docx").exists():
            templates.append(d.name)
    return templates


def cmd_list_templates(args):
    templates = _find_templates()
    if not templates:
        print("No templates found.")
        return
    for name in templates:
        print(f"  {name}")


def cmd_validate(args):
    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    result = validate_payload(payload)
    if result.ok:
        print("Validation passed.")
        for w in result.warnings:
            print(f"  WARNING: {w}")
    else:
        print("Validation failed:")
        for e in result.errors:
            print(f"  ERROR: {e}")
        sys.exit(1)


def cmd_check_styles(args):
    from report_engine.style_checker import check_template_styles
    from report_engine.blocks import DEFAULT_STYLE_MAP

    template_dir = TEMPLATES_DIR / args.template
    template_path = template_dir / "template.docx"
    if not template_path.exists():
        print(f"Template not found: {template_path}")
        sys.exit(1)

    result = check_template_styles(str(template_path), DEFAULT_STYLE_MAP)
    if result.ok:
        print("All required styles present.")
    else:
        print("Missing styles:")
        for s in result.missing:
            print(f"  {s}")
        sys.exit(1)


def cmd_render(args):
    template_dir = TEMPLATES_DIR / args.template
    template_path = template_dir / "template.docx"
    if not template_path.exists():
        print(f"Template not found: {template_path}")
        sys.exit(1)

    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))

    result = validate_payload(payload)
    if not result.ok:
        print("Payload validation failed:")
        for e in result.errors:
            print(f"  {e}")
        sys.exit(1)
    for w in result.warnings:
        print(f"  WARNING: {w}")

    output = args.output or "output/rendered.docx"
    Path(output).parent.mkdir(parents=True, exist_ok=True)

    renderer = TemplateRenderer(str(template_path))
    renderer.render(payload, output)
    print(f"Generated: {Path(output).resolve()}")


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(prog="report-engine", description="通用报告模板引擎")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list-templates", help="列出可用模板")

    val_parser = sub.add_parser("validate", help="校验 JSON payload")
    val_parser.add_argument("--payload", required=True, help="JSON 文件路径")

    style_parser = sub.add_parser("check-styles", help="检查模板样式")
    style_parser.add_argument("--template", required=True, help="模板名称")

    render_parser = sub.add_parser("render", help="渲染文档")
    render_parser.add_argument("--template", required=True, help="模板名称")
    render_parser.add_argument("--payload", required=True, help="JSON 文件路径")
    render_parser.add_argument("--output", help="输出路径")

    args = parser.parse_args()

    handlers = {
        "list-templates": cmd_list_templates,
        "validate": cmd_validate,
        "check-styles": cmd_check_styles,
        "render": cmd_render,
    }

    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)
    handler(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_cli.py -v
```

- [ ] **Step 5: 提交**

```bash
git add src/report_engine/cli.py tests/test_cli.py
git commit -m "feat: add CLI entry point with list/validate/check-styles/render commands"
```

---

### Task 9: 模板和数据迁移

**Files:**
- Create: `templates/grant/template.docx`（复制）
- Create: `templates/grant/schema.yaml`
- Create: `data/examples/grant_demo.json`（迁移）
- Create: `data/examples/grant_advanced_demo.json`（迁移）

- [ ] **Step 1: 迁移模板文件**

```bash
cp templates/grant_template_demo_clean_v3.docx templates/grant/template.docx
```

- [ ] **Step 2: 迁移示例数据**

```bash
cp data/grant_payload_demo.json data/examples/grant_demo.json
cp data/grant_payload_advanced_demo.json data/examples/grant_advanced_demo.json
```

- [ ] **Step 3: 创建 templates/grant/schema.yaml**

```yaml
name: grant_proposal
description: 科研项目申报书模板
placeholders:
  - PROJECT_NAME
  - APPLICANT_ORG
  - PROJECT_LEADER
  - PROJECT_PERIOD
required_styles:
  - Heading 2
  - Heading 3
  - Body Text
  - Caption
  - Legend
  - Figure Paragraph
  - ResearchTable
  - List Bullet
  - List Number
subdoc_slots:
  - RESEARCH_CONTENT_SUBDOC
  - RESEARCH_BASIS_SUBDOC
  - IMPLEMENTATION_PLAN_SUBDOC
  - APPENDICES_SUBDOC
```

- [ ] **Step 4: 提交**

```bash
git add templates/grant/ data/examples/
git commit -m "chore: migrate templates and example data to new structure"
```

---

### Task 10: 端到端冒烟测试

**Files:**
- Create: `tests/test_e2e.py`

- [ ] **Step 1: 写端到端测试**

```python
# tests/test_e2e.py
import json
from pathlib import Path

import pytest
from docx import Document

from report_engine.renderer import TemplateRenderer


@pytest.fixture
def grant_template_path(project_root: Path) -> str:
    path = project_root / "templates" / "grant" / "template.docx"
    if not path.exists():
        pytest.skip("Grant template not yet migrated")
    return str(path)


@pytest.fixture
def advanced_payload(project_root: Path) -> dict:
    path = project_root / "data" / "examples" / "grant_advanced_demo.json"
    if not path.exists():
        pytest.skip("Advanced payload not yet migrated")
    return json.loads(path.read_text(encoding="utf-8"))


def test_full_render(grant_template_path, advanced_payload, tmp_path):
    output = str(tmp_path / "e2e_output.docx")
    renderer = TemplateRenderer(grant_template_path)
    renderer.render(advanced_payload, output)

    assert Path(output).exists()
    doc = Document(output)
    full_text = "\n".join(p.text for p in doc.paragraphs)

    # 检查标量上下文
    assert "智能生成式设计关键技术研究项目申报书" in full_text
    assert "XX研究院" in full_text

    # 检查章节内容
    assert "研究目标" in full_text
    assert "需求建模" in full_text

    # 检查表格存在
    assert len(doc.tables) >= 1


def test_cli_render(grant_template_path, advanced_payload, tmp_path):
    """测试 CLI 命令行渲染流程。"""
    import subprocess
    import sys

    payload_file = tmp_path / "payload.json"
    payload_file.write_text(json.dumps(advanced_payload, ensure_ascii=False))
    output_file = tmp_path / "cli_output.docx"

    result = subprocess.run(
        [
            sys.executable, "-m", "report_engine.cli",
            "render",
            "--template", "grant",
            "--payload", str(payload_file),
            "--output", str(output_file),
        ],
        capture_output=True,
        text=True,
        env={
            **__import__("os").environ,
        },
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    assert output_file.exists()
```

- [ ] **Step 2: 运行全部测试**

```bash
pytest tests/ -v
```

Expected: 全部 PASS（部分测试可能 skip 如果模板未迁移，但 Task 9 完成后不会）

- [ ] **Step 3: 提交**

```bash
git add tests/test_e2e.py
git commit -m "test: add end-to-end smoke test"
```

---

### Task 11: Agent Skill（使用 skill-creator）

此任务使用 skill-creator 技能生成 Agent Skill。

- [ ] **Step 1: 确认引擎已可用**

```bash
report-engine list-templates
report-engine validate --payload data/examples/grant_advanced_demo.json
```

- [ ] **Step 2: 使用 skill-creator 创建 skill**

调用 `skill-creator` skill，传入以下要求：
- Skill 名称：`report-generator`
- 功能：从自然语言描述生成结构化 JSON payload，用户确认后调用 `report-engine render` 输出 Word 文档
- 输入：用户自然语言描述的项目信息
- 输出：`output/` 下的 `.docx` 文件
- 约束：Agent 只生成 JSON，不控制 Word 格式；用户必须确认后才渲染

- [ ] **Step 3: 测试 Skill 端到端流程**

手动触发 skill，验证从描述到生成 docx 的完整流程。

- [ ] **Step 4: 提交**

```bash
git add skills/
git commit -m "feat: add report-generator agent skill"
```
