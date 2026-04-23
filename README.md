# report-template

一个基于 `docxtpl + python-docx` 的 Word 报告模板实验仓库，当前正在从“项目申报书自动生成原型”演进为一个**通用报告模板引擎**。

## 当前状态

仓库当前已经有一套可运行的 advanced 原型，支持：

- 多章节 subdoc
- 多附件
- 附件汇总区 `APPENDICES_SUBDOC`
- 章节 / 附件开关
- 基础 block 类型：
  - `heading`
  - `paragraph`
  - `bullet_list`
  - `numbered_list`
  - `table`
  - `image`
  - `page_break`

当前 Phase 1 的目标，是在**保持现有行为兼容**的前提下，把这套原型工程化为一个可维护、可验证、可扩展的本地模板引擎。

## 阅读顺序

### 1. Phase 1 实施基准
- `docs/superpowers/plans/2026-04-23-report-engine-revised.md`

### 2. Phase 1 设计文档
- `docs/superpowers/specs/2026-04-23-report-engine-design.md`

### 3. 当前行为基线
- `docs/grant_render_advanced_readme.md`
- `scripts/render_grant_advanced.py`
- `data/grant_payload_advanced_demo.json`

### 4. 模板改造参考
- `docs/grant_template_upgrade_guide.md`

### 5. 基础版示例（可选）
- `docs/grant_render_readme.md`
- `scripts/render_grant_demo.py`
- `data/grant_payload_demo.json`

## 当前文档分工

- `revised plan`：定义 Phase 1 做什么、按什么顺序做
- `design spec`：定义 Phase 1 为什么这么设计、模块如何划分
- `advanced readme`：描述当前 advanced 原型已经做到什么
- `template upgrade guide`：描述 Word 模板应如何预留 subdoc / flag / appendix 插槽

## Phase 1 关键原则

- 先冻结当前行为，再重构
- 不从零重写，不断裂式替换
- 主模板负责样式与固定框架，程序负责内容插入
- 复杂章节继续使用 subdoc
- 渲染前先做 validation + template checks
- 旧脚本最终收敛为 wrapper，而不是长期维护两套实现

## 计划中的目标结构

```text
src/report_engine/
  blocks.py
  cli.py
  compat.py
  renderer.py
  schema.py
  style_checker.py
  subdoc.py
  template_checker.py
  validator.py
```

## 本地运行当前 advanced 原型

安装依赖：

```bash
pip install "docxtpl[subdoc]" python-docx
```

运行示例：

```bash
python scripts/render_grant_advanced.py
```

具体输入输出与模板写法说明见：
- `docs/grant_render_advanced_readme.md`

## 清理说明

仓库中的旧“总提示词式交接文档”已不再作为实施依据。后续如需让 coding agent 执行任务，请直接以：

- `docs/superpowers/plans/2026-04-23-report-engine-revised.md`
- `docs/superpowers/specs/2026-04-23-report-engine-design.md`

为准。