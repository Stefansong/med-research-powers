---
name: manuscript-export
description: Use when exporting manuscript markdown into a journal-formatted .docx after pre-submission checks pass. Triggers on "导出Word"、"生成docx"、"论文按期刊排版"、"格式化论文"、"export manuscript to docx".
---

# Manuscript Export

## Overview

把 `manuscript/*.md` 导出为符合目标期刊排版规范的 .docx。期刊的字数/图表/参考文献上限和家族（`family`）都来自 `journal-templates.yaml`，脚本一键生成文件和导出报告。**本 skill 只做格式转换，不改内容。**

## When to Use

- `pre-submission-verification` 6-Gate 全部通过，准备生成投稿文件
- 需要按另一个期刊的格式重新导出（改投）
- 需要把 `supplementary.md` 单独导出为 .docx
- 用户说"帮我排版"、"导出 Word"

## When NOT to Use

- 还在写内容 → `manuscript-writing`
- 还没过 `pre-submission-verification` → 先过 6-Gate，否则每次 Gate 失败都要重导
- 需要生成图表 → `figure-generation`
- 只想核对报告规范 → `reporting-standards`

## Prerequisites

- `manuscript/` 目录下至少有 1 个章节 .md（文件名见 Step 2）
- 目标期刊 id：来自 `journal-selection-report.md` / `.mrp-state.json` 的 `target_journal`，或用户指定
- Python 包：`python-docx`、`pyyaml`（`pip install python-docx pyyaml`；缺包时脚本会给出提示）

## Workflow

### Step 1：确定目标期刊 id

```
1. 读取 journal-selection-report.md（或 .mrp-state.json 的 target_journal）→ 首选期刊
2. 确认 id 存在（不要整读 YAML）：
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/get_journal_template.py --search <关键词>
3. 期刊不在库中 → 按 manuscript-writing 的做法把规范写入项目目录 journal-overrides.yaml
   （同 templates 结构，含 family 字段）；导出脚本默认会先读 ./journal-overrides.yaml
4. 向用户确认：期刊 id + family（决定章节顺序和特殊元素）
```

期刊数据只有一处：`${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/references/journal-templates.yaml`（240 刊，顶层 `data_as_of` 标明 IF/APC 年份）。每条的 `family` 字段（lancet / jama / nature / ieee / standard）决定导出行为；缺该字段时脚本按 id/名称关键词推断。

### Step 2：收集稿件文件

```
manuscript/
  ├── title-page.md
  ├── key-points.md            ← JAMA 家族（Key Points box）
  ├── abstract.md
  ├── research-in-context.md   ← Lancet 家族（Research in Context panel）
  ├── introduction.md
  ├── methods.md
  ├── results.md
  ├── discussion.md
  ├── conclusion.md            ← 可选
  ├── references.md
  ├── figure-legends.md        ← 可选，排在 References 之后
  └── supplementary.md         ← 可选，用 --supplementary 单独导出

检查:
  → 哪些文件存在？家族要求的文件缺了（如 JAMA 缺 key-points.md）→ 报告里 ⚠️，不阻断
  → 综述类的 section-N-*.md 不在导出顺序中 → 先合并进 discussion.md，否则报告列为"未导出"
  → 是否还有 <!-- PLACEHOLDER/TODO/TBD/pending/待补 -->、[TBD]、[TODO]、[pending]、[INSERT、[待补…]、[待填…]（含全角 【待补…】、［待补…］）标记？
```

### Step 3：生成 .docx

调用现成脚本（位于插件目录，用 `${CLAUDE_PLUGIN_ROOT}` 定位——运行目录是用户项目，**不是**插件目录），**不要手写转换代码**：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/manuscript-export/scripts/export_docx.py \
  --manuscript-dir ./manuscript \
  --journal <journal-id> \
  --output manuscript/manuscript.docx \
  --report export-report.md \
  --supplementary        # 可选：把 supplementary.md 单独导出为 manuscript/supplementary.docx
  --report-only          # 只出报告不生成 .docx（pre-submission-verification Gate 6 用）
```

可选参数：`--overrides ./journal-overrides.yaml`（默认就是这个路径）、`--yaml <路径>`（默认用插件内置库）。

退出码：`0` 成功；`2` 期刊 id 不存在（提示用 `get_journal_template.py --search`），或 journal-overrides.yaml / 期刊库格式错误（一行 `Error: …`）；`1` 目录/文件/依赖缺失。

脚本自动完成：
- 按 `family` 设置字体、字号、行距、页边距（Nature/Lancet/standard：Times New Roman 12pt 双倍行距；JAMA 11pt；IEEE 10pt 单倍）
- 按 `family` 排列章节顺序（见下表）；Key Points / Research in Context 缺文件时报告 ⚠️
- Markdown → docx 元素转换（见转换规则表）；表格：表头加粗 + 灰底，单元格支持行内格式
- 分页只出现在题页之后、摘要之后、参考文献之前
- 统计：正文 / 摘要 / 参考文献分桶字数、图数、表数、placeholder 位置 → 生成导出报告

#### 章节顺序（按 family）

| family | 章节顺序 |
|--------|---------|
| **nature** | Title → Abstract → Introduction → Results → Discussion → Methods → References |
| **lancet** | Title → Abstract → Research in Context → Introduction → Methods → Results → Discussion → References |
| **jama** | Title → Key Points → Abstract → Introduction → Methods → Results → Discussion → References |
| **ieee** | Title → Abstract → Introduction → Related Work → Methods → Results → Discussion → References |
| **standard** | Title → Abstract → Introduction → Methods → Results → Discussion → References |

（每个家族的顺序末尾还可有 Conclusion、Figure Legends，文件存在才纳入。）

#### Markdown → docx 转换规则

| Markdown | docx 元素 |
|---------|----------|
| 连续的多行文字（软换行） | 合并为一个段落（中文字符之间不加空格）；空行分段；行尾两个空格或 `\` 保留换行 |
| `#` … `######`；文字下一行 `===` / `---` | Heading 1–6（加粗，字号随 family） |
| `**bold**`、`*italic*`、`***both***`、`__bold__`、`_italic_` | Bold / Italic run，可嵌套（`**a *b* c**`）；`snake_case_names` 这类词内下划线不算强调 |
| `^x^`、`~x~`（闭合、无空格） | Superscript / Subscript run |
| 未成对的 `* ^ ~`（如 `~90%`、`2^10`、`marked with *`） | **原样保留** |
| `` `code` ``；` ``` ` / `~~~` 围栏代码块 | 等宽字体（Courier New）；代码块内容原样保留（不解析标题/强调、不计字数）；4 空格缩进不算代码块 |
| `[text](url)`、`<https://…>` | 超链接（显示 text） |
| `[@key]`、`@key`（Pandoc 引文） | **不转换**，文字原样保留；报告 "Conversion notes" 列出每个 key 及位置 |
| `- item`（缩进表示嵌套） | List Bullet / List Bullet 2 / List Bullet 3（更深的层级用第 3 级） |
| `1. item`（缩进表示嵌套） | 编号保留为文本 "1. item"，按层级缩进（List Number / List Number 2 …；不用 Word 自动编号，参考文献与正文列表不会串号） |
| `> quote` | 缩进斜体段落 |
| 单独一行 `---` / `***` / `___` | 水平分隔线（段落下边框，不是文字） |
| `<!-- comment -->` | 删除（代码块内的保留）；但 `<!-- PLACEHOLDER/TODO/TBD/pending/待补 -->` 会先被记入报告 |
| `\| table \|` | docx Table（带边框）；对齐行 `\|:-:\|--:\|` 设置列对齐；`\\|` 是单元格内的竖线；有对齐行时可省略首尾 `\|`；某行单元格多于表头 → 表格加宽、不丢内容，报告 ⚠️ |
| `![alt](path)` | 保留为文字并计入图数；**图片不嵌入**，图文件单独上传 |

### Step 4：读导出报告

脚本能做到的检查（都写在 `export-report.md`）：

```
□ 字数分桶
  → Body = Introduction + Methods + Results + Discussion（+ Related Work / Conclusion）
    只用 Body 与模板 word_limit 比较；模板写 "excluding Methods" 时自动扣除 Methods
  → Abstract 单独计数，与模板 abstract 字段里的 ≤N words 比较
  → 题页 / Key Points / Research in Context 单独列出，不计入限制
□ 参考文献条数（references.md 中 "N. " 行数）与 references 上限比较
□ 图数（"**Figure N.**" 图注去重 + "![" 嵌入次数，取大者）、表数，与 figures / tables 上限比较；
  模板写 "combined" 时按图+表合计比较
□ 章节：实际顺序、纳入的文件、⚠️ 缺失的家族必需文件、ℹ️ 未导出的多余文件
□ 模板 special 字段原样列出（Reporting Summary、Patient Summary 等），需人工核对
□ Placeholder：<!-- PLACEHOLDER/TODO/TBD/pending/待补 -->、[pending]、[TBD]、[TODO]、[INSERT、[待补…]、[待填…]（含全角 【待补…】、［待补…］）、含 placeholder 的文字 — 覆盖段落、列表、标题、表格单元格，给出 文件:行号
```

脚本**做不到**、需要人工/其他 skill 完成的：页数估算、字体/行距的"验证"（脚本按 family 设置，不再回读核验）、图片嵌入、题页单独文件（部分期刊要求单独上传题页：从 manuscript.docx 复制第一页即可）、参考文献格式正确性（`pubmed-search` Mode 6）。

### Step 5：输出报告

```
────────────────────────────────────────
✅ Manuscript Export Complete

📄 生成的文件:
  • manuscript/manuscript.docx（主文件）
  • manuscript/supplementary.docx（加了 --supplementary 且 supplementary.md 存在时）
  • export-report.md

📏 检查（来自 export-report.md）:
  • 期刊: [journal name]（family: [nature/lancet/jama/ieee/standard]）
  • 正文字数: [N] / [limit] ✅ or ⚠️ 超出 [N]
  • 摘要字数: [N] / [limit]
  • 参考文献: [N] / [limit]；图: [N] / [limit]；表: [N] / [limit]
  • 章节顺序: ✅ [family]；⚠️ 缺失: [key-points.md …]

⚠️ Placeholder 警告:
  • [file:line] — "[placeholder text]"

➡️ 建议下一步: submission-preparation（cover letter、投稿系统清单）
────────────────────────────────────────
```

导出后更新项目目录 `.mrp-state.json`（`python3 ${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`，记录 `manuscript.docx` 与 `export-report.md`）。

## Output

| 文件 | 说明 |
|------|------|
| `manuscript/manuscript.docx` | 投稿主文件 |
| `manuscript/supplementary.docx` | 补充材料（`--supplementary` 且有 supplementary.md 时） |
| `export-report.md` | 导出质量报告（字数分桶、图表数、章节、placeholder） |

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "直接复制粘贴到 Word 就行" | Markdown 格式不会自动转换，会丢失结构和格式 |
| "所有期刊格式都一样" | Nature 系 Methods 放最后，JAMA 需要 Key Points，Lancet 需要 Research in Context——由 `family` 决定 |
| "字数超了一点没关系" | 超限会被 desk rejection；只比正文字数，摘要和参考文献分开算 |
| "`~90%` 会被当成下标" | 只有闭合的 `~x~` / `^x^` 才转格式，未成对符号原样保留 |
| "写作一结束就导出" | 先过 `peer-review-simulation` 和 `pre-submission-verification`，否则每次修改都要重导 |
| "表格用截图就行" | 多数期刊要求可编辑的表格，不接受图片形式 |
| "参考文献手动排版" | 用 `pubmed-search` Mode 6 自动格式化，减少人工错误 |
| "期刊不在库里就改插件目录的 YAML" | 写项目目录 `journal-overrides.yaml`，脚本会优先读取 |

## Convergence

当以下条件全部满足时完成：
1. `manuscript.docx` 已生成（需要时 `supplementary.docx` 也已生成）
2. 章节顺序与目标期刊 `family` 一致，家族必需文件无 ⚠️ 缺失
3. 正文/摘要字数、图表数、参考文献数均在模板限制内，或超限已明确告知用户
4. Placeholder 已清零，或已列出并告知用户
5. `export-report.md` 已生成，`.mrp-state.json` 已更新

## Red Flags — STOP

- **不要在导出时修改论文内容** — 内容修改回 `manuscript-writing`
- **不要忽略字数超限** — 必须明确告知用户
- **不要跳过 Placeholder 检测** — 带 placeholder 投稿会被 desk reject
- **不要手写 Markdown→docx 转换代码** — 用脚本，否则行内符号（`~`、`^`）可能被静默吞掉
- 脚本 exit 2（期刊 id 不存在）→ 停，用 `--search` 找 id 或写 `journal-overrides.yaml`，不要硬凑一个 family 导出

## 衔接规则

### 前置依赖（缺了按总调度"缺前置产物时"处理；6-Gate 是硬确认 3）
- `manuscript/` 下至少 1 个章节 .md
- 投稿版必须已通过 `pre-submission-verification`（`submission-readiness-report.md` 6-Gate 全过）；没通过时只导出给合作者看的草稿（文件名加 `-draft`，告诉用户不能用来投稿）
- **推荐**有 `journal-selection-report.md`（确定期刊 id）

### 强制衔接（不可跳过）
- `pre-submission-verification` 通过后 → 本 skill → `submission-preparation`（cover letter、投稿清单）
- 导出后 → 更新 `.mrp-state.json`

### 可选衔接
- `revision-response` 修改后 → 重新导出
- 改投另一个期刊 → 换 `--journal` id 重新导出（Key Points / Research in Context 按新家族增删）
- 需要格式化参考文献 → `pubmed-search` Mode 6
