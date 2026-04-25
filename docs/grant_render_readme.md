# 配套说明：研究内容 subdoc 渲染示例

这套文件与 `grant_template_demo_clean_v3.docx` 对应，适用于：

- 主模板负责整体版式、标题样式、页眉页脚、固定信息区
- `研究内容` 章节使用一个整体插槽：`{{p RESEARCH_CONTENT_SUBDOC }}`
- Python 程序将多段正文、表格、图片、图题、图例动态构造成一个 subdoc 再插回主模板

## 文件
- `grant_payload_demo.json`：示例输入数据
- `render_grant_demo.py`：示例渲染脚本
- `grant_template_demo_clean_v3.docx`：主模板（你已下载）

## 依赖
建议安装：

```bash
pip install "docxtpl[subdoc]" python-docx
```

## 运行方式

将这三个文件放在同一目录下，然后运行：

```bash
python render_grant_demo.py
```

默认会读取：
- `grant_payload_demo.json`
- `grant_template_demo_clean_v3.docx`

然后输出：
- `grant_output_demo.docx`

## 你后续最需要改的地方
1. 把模板中的固定占位符名称和脚本中的 `context` 对齐
2. 在模板中提前定义并使用这些样式：
   - Heading 2
   - Heading 3
   - Body Text
   - TableCaption
   - FigureCaption
   - Legend
   - Figure Paragraph
   - ResearchTable
3. 让大模型输出结构化 JSON，而不是直接输出 Word 富文本
4. 图片文件先生成到本地目录，再由脚本按 `path` 插入

## 推荐的块类型
当前示例已支持：
- `heading`
- `paragraph`
- `bullet_list`
- `table`
- `image`

后续你还可以扩展：
- `numbered_list`
- `page_break`
- `quote`
- `appendix_table`
- `two_images_row`

## 实践建议
- 复杂富内容章节优先用 subdoc，不要在主模板里写过多循环和条件
- 固定框架留在主模板，混合内容放到 subdoc
- 图题和图例都单独成段，避免和图片混在一起
