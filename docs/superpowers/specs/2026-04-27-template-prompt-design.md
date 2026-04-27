# 模板内嵌 AI 提示词设计文档

## 背景

report-engine 模板当前支持三种占位元素：标量占位符（`{{变量}}`）、subdoc 插槽（`{{p SUBDOC }}`）和条件开关（`{%p if ... %}`）。当使用 report-generator skill 基于模板生成完整报告时，AI 需要根据模板结构推断每个章节应该写什么内容，这个过程缺乏明确的指导。

本设计在模板中引入 `[[PROMPT: ...]]` 注释语法，让模板作者可以在模板中直接嵌入 AI 提示词，指导 AI 生成对应章节的内容。

## 目标

1. 模板作者可以在 .docx 模板中嵌入 AI 提示词
2. report-engine 渲染时自动忽略/删除提示词段落
3. report-generator 分析模板时读取提示词，用于指导内容生成
4. 支持章节级和段落级两种粒度
5. 支持 `auto`（自动执行）和 `interactive`（交互式确认）两种模式

## 语法规范

### 基本格式

```
[[PROMPT: 目标: 提示内容 | mode=auto]]
```

- `[[PROMPT:` 和 `]]` 为定界符，必须成对出现
- **目标**（target）：提示词作用的对象标识
  - 章节级：章节名称，如 `立项依据`、`研究目标`
  - 段落级：点号分隔的层级标识，如 `研究内容.技术路线`
- **提示内容**（prompt）：给 AI 的具体指令，支持自然语言描述
- **mode**（可选）：执行模式，默认 `auto`
  - `auto`：AI 自动根据提示词生成内容
  - `interactive`：AI 生成内容前与用户确认

### 放置位置

**章节级** — 放在条件开关内、subdoc 占位符之前：

```
{%p if ENABLE_立项依据 %}
[[PROMPT: 立项依据: 请从国内外研究现状、研究意义等方面撰写立项依据，字数不少于2000字 | mode=auto]]
{{p 立项依据_SUBDOC }}
{%p endif %}
```

**段落级** — 放在需要细粒度指导的占位符附近：

```
{%p if ENABLE_研究内容 %}
[[PROMPT: 研究内容.技术路线: 请描述具体的技术路线，包含至少3个关键技术点 | mode=interactive]]
{{p 研究内容_SUBDOC }}
{%p endif %}
```

### 多行提示词

提示词内容较长时，允许多行书写（段落内换行）：

```
[[PROMPT: 立项依据: 请从以下几个方面撰写：
1. 国内外研究现状综述
2. 本项目的研究意义
3. 现有研究的不足之处
4. 本项目的创新点 | mode=auto]]
```

## 架构设计

### report-engine 侧（渲染时过滤）

在 `renderer.py` 的 `render_report()` 流程中增加预处理步骤：

```
加载模板文档
  ↓
[新增] 扫描并删除所有 [[PROMPT: ...]] 段落
  ↓
构建 context（subdoc 渲染等）
  ↓
DocxTemplate.render(context)
  ↓
保存输出文档
```

实现细节：
- 识别逻辑：遍历模板文档的所有段落，检查段落文本是否以 `[[PROMPT:` 开头并以 `]]` 结尾
- 删除逻辑：从文档 XML 中移除匹配的段落元素
- 不对原始模板文件做修改（仅在内存中处理）
- 该步骤在渲染流程的最早期执行，确保提示词不会进入后续任何处理环节

### report-generator 侧（生成时读取）

在 `analyze_template.py` 中增加 PROMPT 解析模块：

```python
def parse_prompts(doc: Document) -> List[PromptInfo]:
    """扫描文档中的所有 PROMPT 注释。"""
    prompts = []
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text.startswith("[[PROMPT:") and text.endswith("]]"):
            parsed = _parse_prompt_text(text)
            if parsed:
                prompts.append(parsed)
    return prompts
```

解析后输出结构化数据：

```json
{
  "prompts": [
    {
      "target": "立项依据",
      "prompt": "请从国内外研究现状...",
      "mode": "auto",
      "level": "section"
    },
    {
      "target": "研究内容.技术路线",
      "prompt": "请描述具体的技术路线...",
      "mode": "interactive",
      "level": "paragraph"
    }
  ]
}
```

`level` 推断规则：
- 如果 `target` 不含点号（`.`）→ `level: "section"`
- 如果 `target` 含点号 → `level: "paragraph"`

### 模块职责

| 模块 | 职责 | 新增/修改 |
|------|------|-----------|
| `renderer.py` | 渲染前删除 PROMPT 段落 | 修改 |
| `analyze_template.py` | 解析模板中的 PROMPT 注释 | 修改 |
| `build_custom_template.py` | 生成模板时支持添加 PROMPT 段落 | 修改（可选） |
| `docs/` | 更新模板规范和 payload 规范 | 新增文档 |

## 错误处理

1. **语法不完整**：`[[PROMPT:` 开头但没有对应的 `]]` → 警告日志，跳过该段落
2. **mode 值非法**：不是 `auto` 或 `interactive` → 默认回退到 `auto`，记录警告
3. **目标为空**：无法解析目标 → 跳过，记录警告
4. **目标章节不存在**：report-generator 分析时发现目标对应的章节/占位符在模板中不存在 → 记录警告，继续处理其他提示词

## 测试策略

1. **单元测试**：
   - `_parse_prompt_text()` 的各种输入组合（完整语法、缺少 mode、多行内容、非法 mode）
   - `_filter_prompt_paragraphs()` 的删除逻辑（确认 PROMPT 段落被删除、非 PROMPT 段落保留）

2. **集成测试**：
   - 带 PROMPT 段落的模板渲染后，输出文档中不包含 PROMPT 文本
   - analyze_template 正确提取并输出提示词 JSON

3. **端到端测试**：
   - 完整流程：创建带 PROMPT 的模板 → 渲染 → 确认干净 → 分析 → 确认提示词被提取

## 兼容性

- 向后兼容：不带 PROMPT 注释的模板行为不变
- 与 `[[FORMAT: ...]]` 注释共存：两者使用不同的前缀，互不干扰
- 与现有占位符语法共存：PROMPT 段落可以放在条件开关内、subdoc 占位符旁边
