#!/usr/bin/env python3
"""从简化内容描述构建合法的 report-engine payload。

用法:
    python build_payload.py --template template.docx --content content.json --output payload.json

content.json 格式（比完整 payload 简单得多）:
{
  "title": "AI教育研究报告",
  "org": "XX大学",
  "leader": "张三",
  "period": "2026年1月-12月",
  "sections": [
    {
      "name": "研究内容与技术路线",
      "blocks": [
        {"type": "paragraph", "text": "本项目旨在..."},
        {"type": "table", "headers": ["指标","目标"], "rows": [["准确率","95%"]]}
      ]
    }
  ],
  "attachments": [
    {
      "name": "经费预算",
      "blocks": [
        {"type": "appendix_table", "headers": ["科目","金额"], "rows": [["设备费","50万"]]}
      ]
    }
  ]
}

脚本自动完成:
  - 从 name 生成 id/placeholder/flag_name
  - 合并默认 style_map
  - 添加 attachments_bundle 配置
  - 校验 block 字段完整性
  - 输出合法的 payload JSON
"""

import argparse
import json
import re
from pathlib import Path


# ── 默认 style_map ─────────────────────────────────────────

DEFAULT_STYLE_MAP = {
    "table": "ResearchTable",
    "appendix_table": "AppendixTable",
    "figure_paragraph": "Figure Paragraph",
    "legend": "Legend",
    "note": "Note",
    "quote": "Quote",
    "checklist": "Checklist",
    "code_block": "CodeBlock",
}

# ── block 必填字段 ─────────────────────────────────────────

BLOCK_REQUIRED = {
    "heading": ["text"],
    "paragraph": ["text"],
    "bullet_list": ["items"],
    "numbered_list": ["items"],
    "table": ["headers", "rows"],
    "image": ["path"],
    "page_break": [],
    "rich_paragraph": ["segments"],
    "note": ["text"],
    "quote": ["text"],
    "two_images_row": ["images"],
    "appendix_table": ["headers", "rows"],
    "checklist": ["items"],
    "horizontal_rule": [],
    "toc_placeholder": [],
    "code_block": ["code"],
    "formula": ["latex"],
    "columns": ["count", "columns"],
}


# 常见中文章节名到标准 id 的映射
SECTION_NAME_MAP = {
    "研究内容": "research_content",
    "研究内容与技术路线": "research_content",
    "研究基础": "research_basis",
    "研究基础与条件保障": "research_basis",
    "实施计划": "implementation_plan",
    "实施计划与进度安排": "implementation_plan",
    "经费预算": "budget",
    "参考文献": "references",
    "文献综述": "literature_review",
    "研究方法": "methodology",
    "预期成果": "expected_results",
    "目录": "toc",
}


def name_to_id(name: str) -> str:
    """将中文名称转为 snake_case id。"""
    # 去掉中文数字前缀
    cleaned = re.sub(r"^[一二三四五六七八九十]+[、．.]\s*", "", name).strip()

    # 先查映射表
    for key, val in SECTION_NAME_MAP.items():
        if key in cleaned:
            return val

    # 如果是纯中文，返回 None 由调用方决定
    if re.search(r"[\u4e00-\u9fff]", cleaned):
        return None

    # 英文：转 snake_case
    return re.sub(r"[^a-z0-9]+", "_", cleaned.lower()).strip("_")


def build_section(section: dict, index: int) -> dict:
    """构建一个 section 对象。"""
    name = section.get("name", f"Section {index + 1}")
    blocks = section.get("blocks", [])

    # 允许用户手动指定 placeholder/flag_name/id
    sid = section.get("id") or name_to_id(name)
    if sid is None:
        sid = f"section_{index + 1}"

    placeholder = section.get("placeholder") or f"{sid.upper()}_SUBDOC"
    flag_name = section.get("flag_name") or f"ENABLE_{sid.upper()}"

    # 校验 blocks
    for i, block in enumerate(blocks):
        btype = block.get("type")
        if not btype:
            raise ValueError(f"Section '{name}' block[{i}]: missing 'type'")
        if btype not in BLOCK_REQUIRED:
            raise ValueError(f"Section '{name}' block[{i}]: unknown type '{btype}'")
        missing = [f for f in BLOCK_REQUIRED[btype] if f not in block]
        if missing:
            raise ValueError(
                f"Section '{name}' block[{i}] ({btype}): missing fields: {', '.join(missing)}"
            )

    return {
        "id": sid,
        "placeholder": placeholder,
        "flag_name": flag_name,
        "enabled": section.get("enabled", True),
        "blocks": blocks,
        "order": index + 1,
    }


def build_attachment(attachment: dict, index: int) -> dict:
    """构建一个 attachment 对象。"""
    name = attachment.get("name", f"Appendix {index + 1}")
    blocks = attachment.get("blocks", [])

    aid = f"appendix_{index + 1}"
    placeholder = f"APPENDIX_{index + 1}_SUBDOC"
    flag_name = f"ENABLE_APPENDIX_{index + 1}"

    # 校验 blocks
    for i, block in enumerate(blocks):
        btype = block.get("type")
        if not btype:
            raise ValueError(f"Attachment '{name}' block[{i}]: missing 'type'")
        if btype not in BLOCK_REQUIRED:
            raise ValueError(f"Attachment '{name}' block[{i}]: unknown type '{btype}'")
        missing = [f for f in BLOCK_REQUIRED[btype] if f not in block]
        if missing:
            raise ValueError(
                f"Attachment '{name}' block[{i}] ({btype}): missing fields: {', '.join(missing)}"
            )

    return {
        "id": aid,
        "placeholder": placeholder,
        "flag_name": flag_name,
        "enabled": True,
        "title": name,
        "title_level": 2,
        "blocks": blocks,
        "order": index + 1,
    }


def build_payload(content: dict) -> dict:
    """从简化内容描述构建完整 payload。"""
    # context
    context = {}
    if content.get("title"):
        context["PROJECT_NAME"] = content["title"]
    if content.get("org"):
        context["APPLICANT_ORG"] = content["org"]
    if content.get("leader"):
        context["PROJECT_LEADER"] = content["leader"]
    if content.get("period"):
        context["PROJECT_PERIOD"] = content["period"]

    # sections
    sections = []
    for i, sec in enumerate(content.get("sections", [])):
        sections.append(build_section(sec, i))

    # attachments
    attachments = []
    for i, att in enumerate(content.get("attachments", [])):
        attachments.append(build_attachment(att, i))

    # attachments_bundle
    has_attachments = len(attachments) > 0
    attachments_bundle = {
        "enabled": has_attachments,
        "placeholder": "APPENDICES_SUBDOC",
        "flag_name": "ENABLE_APPENDICES",
        "page_break_between_attachments": True,
        "include_attachment_title": True,
    }

    # style_map
    style_map = dict(DEFAULT_STYLE_MAP)
    if content.get("style_map"):
        style_map.update(content["style_map"])

    return {
        "context": context,
        "sections": sections,
        "attachments": attachments,
        "attachments_bundle": attachments_bundle,
        "style_map": style_map,
    }


def main():
    parser = argparse.ArgumentParser(description="从简化内容描述构建 payload")
    parser.add_argument("--content", required=True, help="内容描述 JSON 文件路径")
    parser.add_argument("--output", required=True, help="输出 payload 路径")
    parser.add_argument("--template", help="模板文件路径（可选，用于交叉校验）")
    args = parser.parse_args()

    content = json.loads(Path(args.content).read_text(encoding="utf-8"))

    try:
        payload = build_payload(content)
    except ValueError as e:
        print(f"错误: {e}", file=sys.exit(1))
        return

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Payload 已生成: {args.output}")
    print(f"  context: {len(payload['context'])} 个字段")
    print(f"  sections: {len(payload['sections'])} 个")
    print(f"  attachments: {len(payload['attachments'])} 个")

    # 可选：用 report-engine 校验
    if args.template:
        import subprocess
        result = subprocess.run(
            ["report-engine", "check-template",
             "--template", args.template,
             "--payload", args.output],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"校验失败: {result.stderr}", file=sys.stderr)


if __name__ == "__main__":
    import sys
    main()
