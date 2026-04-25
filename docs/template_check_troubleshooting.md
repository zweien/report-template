# 模板检查失败排查说明

当你执行：

```bash
report-engine check-template --template <template.docx> --payload data/examples/grant_advanced_demo.json
```

如果出现类似下面的输出：

- Missing styles
- Missing placeholders
- Missing flags
- image not found warning

这通常不表示程序本身有问题，而是表示：**当前模板还没有适配对应的 payload 结构。**

---

## 1. 常见原因

### 情况 A：你拿“基础版模板”去检查“advanced payload”

例如模板里只预留了：

- `RESEARCH_CONTENT_SUBDOC`

但 advanced payload 里还包含：

- `RESEARCH_BASIS_SUBDOC`
- `IMPLEMENTATION_PLAN_SUBDOC`
- `APPENDICES_SUBDOC`
- `ENABLE_RESEARCH_BASIS`
- `ENABLE_IMPLEMENTATION_PLAN`
- `ENABLE_APPENDICES`

这时 checker 报缺失是正常的。

### 情况 B：模板没有预置所需样式

如果模板中没有这些样式：

- `Legend`
- `Figure Paragraph`
- `ResearchTable`

checker 也会明确报出缺失。

### 情况 C：图片素材不存在

如果 payload 中的图片路径，比如：

- `figures/tech_route.png`

在当前工作目录中不存在，validator 会给 warning。

这类 warning 默认不会阻止渲染，但会提示你素材尚未准备好。

---

## 2. 如何判断这是不是预期结果

如果你使用的是：

- 旧版 / 基础版模板
- 只支持单个 `research_content` 章节的模板
- 还没有插入 appendix 总区和条件开关的模板

那么下面这些缺失是**预期行为**：

- `RESEARCH_BASIS_SUBDOC`
- `IMPLEMENTATION_PLAN_SUBDOC`
- `APPENDICES_SUBDOC`
- `ENABLE_RESEARCH_BASIS`
- `ENABLE_IMPLEMENTATION_PLAN`
- `ENABLE_APPENDICES`

也就是说，checker 正在正确告诉你：

> 这个模板还不是 advanced payload 对应的模板。

---

## 3. 处理方式

### 方式 1：换成真正适配 advanced payload 的模板

模板中应至少补上：

```text
{%p if ENABLE_RESEARCH_CONTENT %}
二、研究内容与技术路线
{{p RESEARCH_CONTENT_SUBDOC }}
{%p endif %}

{%p if ENABLE_RESEARCH_BASIS %}
三、研究基础
{{p RESEARCH_BASIS_SUBDOC }}
{%p endif %}

{%p if ENABLE_IMPLEMENTATION_PLAN %}
四、实施计划
{{p IMPLEMENTATION_PLAN_SUBDOC }}
{%p endif %}

{%p if ENABLE_APPENDICES %}
附件
{{p APPENDICES_SUBDOC }}
{%p endif %}
```

### 方式 2：使用与模板匹配的基础版 payload

如果你的模板还是基础版单章节模板，不要用 advanced payload 去校验。

优先改用：

```bash
report-engine validate --payload data/examples/grant_demo.json
```

或者使用基础版脚本 / 基础版结构继续验证。

### 方式 3：先补样式

请在模板里至少预置并用过一次以下样式：

- `Heading 2`
- `Heading 3`
- `Body Text`
- `TableCaption`
- `FigureCaption`
- `Legend`
- `Figure Paragraph`
- `List Bullet`
- `List Number`
- `ResearchTable`

### 方式 4：准备图片素材或暂时忽略 warning

如果只是图片文件还没准备好，可以暂时保留 warning，后续把对应图片放到 payload 指向的位置即可。

---

## 4. 针对这类报错的结论

如果你看到：

- 缺 `Legend / Figure Paragraph / ResearchTable`
- 缺 `APPENDICES_SUBDOC / RESEARCH_BASIS_SUBDOC / IMPLEMENTATION_PLAN_SUBDOC`
- 缺 `ENABLE_APPENDICES / ENABLE_RESEARCH_BASIS / ENABLE_IMPLEMENTATION_PLAN`

最常见的解释就是：

> **你当前检查的是一个尚未升级到 advanced 结构的模板。**

这说明 checker 已经在正常工作。

---

## 5. 推荐阅读

- `docs/grant_template_upgrade_guide.md`
- `docs/grant_render_advanced_readme.md`
- `docs/superpowers/specs/2026-04-23-report-engine-design.md`
