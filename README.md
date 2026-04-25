# report-template

[![CI](https://github.com/zweien/report-template/actions/workflows/ci.yml/badge.svg)](https://github.com/zweien/report-template/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-pytest-brightgreen)](https://pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

一个基于 `docxtpl + python-docx` 的 **Word 报告模板引擎**。通过结构化 JSON payload 驱动 `.docx` 模板渲染，实现"模板管样式，数据管内容"的分离。

---

## 特性

- **模板与内容分离**：模板负责版式、样式和固定框架，JSON payload 负责结构化内容
- **丰富的 Block 类型**：支持 19 种内容块，涵盖标题、段落、列表、表格、图片、公式、代码、多列布局等
- **学术三线表**：原生支持学术规范的三线表格（粗顶线/底线 + 细表头底线）
- **Subdoc 渲染**：复杂正文通过子文档生成，不将富文本逻辑堆到主模板
- **章节开关**：支持按条件启用/禁用章节和附件
- **校验与检查**：渲染前自动校验 payload 结构、检查模板样式和占位符契约
- **兼容旧入口**：保留早期脚本的兼容 wrapper，平滑迁移

---

## 安装

需要 Python 3.10+。

```bash
# 使用 uv（推荐）
uv pip install -e ".[dev]"

# 或使用 pip
pip install -e ".[dev]"
```

---

## 快速开始

### 1. 准备模板

模板是一个普通的 `.docx` 文件，使用 `docxtpl` 语法预留占位符：

```text
{{PROJECT_NAME}}

{%p if ENABLE_RESEARCH_CONTENT %}
一、研究内容
{{p RESEARCH_CONTENT_SUBDOC }}
{%p endif %}
```

模板中需要预置以下样式：

**段落样式**：`Heading 2`、`Heading 3`、`Body Text`、`TableCaption`、`FigureCaption`、`Legend`、`Figure Paragraph`、`List Bullet`、`List Number`、`Note`、`Quote`、`CodeBlock`、`Checklist`

**表格样式**：`ResearchTable`、`AppendixTable`

### 2. 编写 Payload

```json
{
  "context": {
    "PROJECT_NAME": "示例项目"
  },
  "sections": [
    {
      "id": "research_content",
      "placeholder": "RESEARCH_CONTENT_SUBDOC",
      "flag_name": "ENABLE_RESEARCH_CONTENT",
      "enabled": true,
      "blocks": [
        {"type": "heading", "text": "1.1 研究目标", "level": 2},
        {"type": "paragraph", "text": "本项目旨在..."},
        {
          "type": "three_line_table",
          "title": "表1 实验结果",
          "headers": ["组别", "样本量", "均值"],
          "rows": [["对照组", "50", "10.2"], ["实验组", "50", "15.6"]]
        }
      ]
    }
  ],
  "attachments_bundle": {
    "enabled": true,
    "placeholder": "APPENDICES_SUBDOC",
    "flag_name": "ENABLE_APPENDICES"
  },
  "style_map": {}
}
```

### 3. 校验、检查并渲染

```bash
# 校验 payload
report-engine validate --payload payload.json

# 检查模板与 payload 的契约
report-engine check-template --template template.docx --payload payload.json

# 渲染报告
report-engine render --template template.docx --payload payload.json --output output.docx
```

更多示例见 `data/examples/`。

---

## 支持的 Block 类型

| Block | 说明 |
|-------|------|
| `heading` | 标题（支持 level 1-5） |
| `paragraph` | 普通段落 |
| `rich_paragraph` | 富文本段落（bold / italic / sub / sup） |
| `bullet_list` | 无序列表 |
| `numbered_list` | 有序列表 |
| `table` | 表格（支持标题、样式、边框） |
| `three_line_table` | 学术三线表 |
| `image` | 图片（支持宽度、图题、图例） |
| `page_break` | 分页符 |
| `note` | 注释块（带"注："前缀） |
| `quote` | 引用块（支持来源） |
| `two_images_row` | 双图并排 |
| `appendix_table` | 附录表格 |
| `checklist` | 清单（☐/☑） |
| `horizontal_rule` | 水平分隔线 |
| `toc_placeholder` | 目录占位符 |
| `code_block` | 代码块（等宽字体 + 灰底） |
| `formula` | 公式（LaTeX，三级降级） |
| `columns` | 多列布局（嵌套 block） |
| `ascii_diagram` | ASCII 示意图（渲染为图片） |

完整字段说明见 `docs/report_engine_payload_spec.md`。

---

## 项目结构

```text
report-template/
├── src/report_engine/          # 核心引擎
│   ├── blocks.py               # Block 注册表与渲染器
│   ├── renderer.py             # 主渲染编排
│   ├── validator.py            # Payload 校验
│   ├── schema.py               # Pydantic 模型
│   ├── style_checker.py        # 模板样式检查
│   ├── template_checker.py     # 模板占位符/flag 契约检查
│   ├── subdoc.py               # Subdoc 构建
│   ├── compat.py               # 旧结构兼容
│   └── cli.py                  # CLI 入口
├── tests/                      # 测试（pytest）
├── scripts/                    # 辅助脚本
├── data/examples/              # 示例 payload
├── templates/                  # 示例模板
├── docs/                       # 文档
│   ├── report_engine_payload_spec.md
│   ├── report_engine_template_spec.md
│   └── phase1_status.md
└── output/                     # 输出目录
```

---

## 开发

```bash
# 运行测试
pytest

# 运行单文件测试
pytest tests/test_blocks.py -v

# 运行单个测试
pytest tests/test_blocks.py::test_heading_block -v
```

### 添加新的 Block 类型

1. `src/report_engine/blocks.py` — 实现 renderer 并注册到 `create_default_registry()`
2. `src/report_engine/validator.py` — 在 `BLOCK_REQUIRED_FIELDS` 中添加必填字段
3. `tests/test_blocks.py` — 添加单元测试
4. `docs/report_engine_payload_spec.md` — 补充字段文档
5. `README.md` — 更新 Block 类型表
6. `data/examples/test_all_blocks.json` — 添加示例实例
7. 重新生成模板并渲染验证

---

## 文档

| 文档 | 内容 |
|------|------|
| `docs/report_engine_payload_spec.md` | Payload 字段规范、block 类型说明 |
| `docs/report_engine_template_spec.md` | 模板占位符、条件开关、样式要求 |
| `docs/template_check_troubleshooting.md` | check-template 报错排查 |
| `docs/grant_template_upgrade_guide.md` | 基础模板升级到 Advanced 结构 |

---

## 许可

MIT
