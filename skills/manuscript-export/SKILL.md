---
name: manuscript-export
description: Use when exporting manuscript markdown into a journal-formatted .docx after pre-submission checks pass. Triggers on "导出Word"、"生成docx"、"论文按期刊排版"、"格式化论文"、"export manuscript to docx".
---

# Manuscript Export

## Overview

把 `manuscript/*.md` 导出为符合目标期刊排版规范的 .docx。期刊的字数/图表/参考文献上限和家族（`family`）都来自 `journal-templates.yaml`，脚本一键生成文件和导出报告。**本 skill 只做格式转换，不改内容。**

> 总调度规则（直接调用本 skill 也适用，原文见 `${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/SKILL.md`）：**缺前置产物**——说缺什么，light / auto 下先往下做并记缺口，不拒绝；但投稿版导出前必须已过 6-Gate（硬确认 3）；**只要一个产物**时交付后停下。

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
- 目标期刊 id：来自 `journal-selection-report.md` / `.mrp-state.json` 的 `target_journal`，或用户指定；用户只要一个 Word 版、还没定期刊 → 用 `--journal generic`
- Python 包：`python-docx`、`pyyaml`（`pip install python-docx pyyaml`；缺包时脚本会给出提示）

## Workflow

### Step 1：确定目标期刊 id

```
1. 读取 journal-selection-report.md（或 .mrp-state.json 的 target_journal）→ 首选期刊
2. 确认 id 存在（不要整读 YAML）：
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/get_journal_template.py --search <关键词>
3. 期刊不在库中 → 按 manuscript-writing 的做法把规范写入项目目录 journal-overrides.yaml
   （同 templates 结构，含 family 字段）；导出脚本默认会先读 ./journal-overrides.yaml
4. 有目标期刊时向用户确认：期刊 id + family（决定章节顺序和特殊元素）+ 文章类型（--article-type）
5. 用户只是要一个 Word 版（给合作者看、还没定期刊）→ 不用追问期刊，直接 --journal generic
   （standard 版式，不检查任何期刊限制；投稿前再按目标期刊重导）
```

期刊数据只有一处：`${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/references/journal-templates.yaml`（240 刊，顶层 `data_as_of` 标明 IF/APC 年份）。每条的 `family` 字段（lancet / jama / nature / ieee / standard）决定导出行为；缺该字段时脚本按 id/名称关键词推断。数字限制只用条目里结构化的 `limits`（文章类型不是 original 时用 `limits_by_type.<类型>`）；没有 `limits` 的条目（例如用户的 journal-overrides.yaml）脚本才去读 word_limit 等文字字段，读不出唯一上限的（"typically"、范围混着图表数、页数限制、最少条数、只写 "see author guidelines"）一律不给数字，报告里写"Check manually"；数字后面才出现的 "no limit on references"、"no limit for reviews" 说的是别的部分，不取消前面的上限。

条目没有 `guidelines_checked`（未按期刊现行投稿指南核对过）时，报告限制部分第一行是 ⚠️ **Unverified journal entry**，通过的检查标 ✅*：**把这条提醒原样转告用户**，请他投稿前到期刊官网核对限制。条目有以 `待核实` 开头的 special 项时（`get_journal_template.py --id` 的第二行警告），这些值不在 `limits` 里，报告里对应的行是 "ℹ️ no limit in the library"：同样转告用户，请他到期刊官网确认，不要说成通过。

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
  ├── section-N-*.md           ← 综述的主题板块：按 N 的数字顺序排在 Introduction 之后，计入正文
  ├── figure-legends.md        ← 可选，排在 References 之后；manuscript/ 里没有时读项目根目录（manuscript/ 的上一级，
  │                               或包含 manuscript/ 的当前目录）的 figure-legends.md（较早的项目写在那里；figure-generation
  │                               现在写 manuscript/），报告注明用的是哪个；不包含 manuscript/ 的当前目录里的那份不读
  └── supplementary.md         ← 可选，用 --supplementary 单独导出

检查:
  → 哪些文件存在？家族要求的文件缺了（如 JAMA 缺 key-points.md）→ 报告里 ⚠️，不阻断
    （有 section-N-*.md 的综述不要求 methods.md / results.md）
  → manuscript/ 和项目根目录各有一份 figure-legends.md → 只导出 manuscript/ 那份，报告 ⚠️，先合并
  → 是否还有占位标记？<!-- PLACEHOLDER/TODO/TBD/pending/待补 -->（多行注释也算）、[TBD]、[TODO]、
    [pending]、[INSERT、[待补…]、[待填…]（含全角 【待补…】、［待补…］）、大写 TODO / TBD / FIXME、
    待补 / 待填 / 待核实（不带括号也算）、[ref]、[cite]、[citation needed]
```

### Step 3：生成 .docx

调用现成脚本（位于插件目录，用 `${CLAUDE_PLUGIN_ROOT}` 定位——运行目录是用户项目，**不是**插件目录），**不要手写转换代码**：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/manuscript-export/scripts/export_docx.py \
  --manuscript-dir ./manuscript \
  --journal <journal-id> \
  --output manuscript/manuscript.docx \
  --report export-report.md \
  --article-type original   # 默认 original；另有 review / systematic_review / research_letter / brief_report / case_report
  --supplementary        # 可选：把 supplementary.md 单独导出为 manuscript/supplementary.docx
  --report-only          # 只出报告不生成 .docx（pre-submission-verification Gate 6 用）
```

可选参数：`--journal generic`（期刊中立导出，不查限制）、`--overrides ./journal-overrides.yaml`（默认就是这个路径）、`--yaml <路径>`（默认用插件内置库）、`--no-page-numbers` / `--no-line-numbers`。

`--article-type` 不是 original 时，只用该刊 `limits_by_type` 里这一类型的限制；库里没有时报告写一行"库里没有该类型的限制，请查期刊投稿指南"，所有数字限制都标"not checked"，不会出现 ✅。模板文字里的"no fixed limit"和"每个图表折合 N 词"只说原始研究，不套用到其他类型（这一类型没写的项标"no limit in the library — check the journal's guidelines"）。

退出码：`0` 成功；`2` 出错（一行 `Error: …`，无 traceback）：参数错误、期刊 id 不存在（提示用 `get_journal_template.py --search`）、journal-overrides.yaml / 期刊库格式错误、目录或文件缺失、文件不是 UTF-8、缺依赖、输出路径会覆盖输入文件（`--report` / `--supplementary` / `--output` 指向某个 .md 输入或期刊库）或覆盖一个不是旧导出结果的已有文件。

脚本自动完成：
- 按 `family` 设置字体、字号、行距、页边距（Nature/Lancet/standard：Times New Roman 12pt 双倍行距；JAMA 11pt；IEEE 10pt 单倍）
- 页码（页脚居中）和连续行号：默认按期刊库 `defaults` 加上；条目自带 `page_numbers` / `line_numbers`（false = 不要）时按条目，`--no-page-numbers` / `--no-line-numbers` 可关闭
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
| `^x^`、`~x~`（闭合、无空格） | Superscript / Subscript run；每处下标都列进报告 "Conversion notes"（ℹ️），便于核对 |
| 数字后面的 `~`（范围，如 `18~65岁`、`50~80kg`、`IQR 2~5`）；含中文或 `,` `;` 的 `~…~` | **原样保留**，不当下标 |
| 未成对的 `* ^ ~`（如 `~90%`、`2^10`、`marked with *`） | **原样保留** |
| `` `code` ``；` ``` ` / `~~~` 围栏代码块 | 等宽字体（Courier New）；代码块内容原样保留（不解析标题/强调、不计字数）；4 空格缩进不算代码块 |
| `[text](url)`、`<https://…>` | 超链接（显示 text） |
| `[@key]`、`@key`（Pandoc 引文） | **不转换**，文字原样保留；报告 "Conversion notes" 列出每个 key 及位置 |
| `- item`（缩进表示嵌套） | List Bullet / List Bullet 2 / List Bullet 3（更深的层级用第 3 级） |
| `1. item`（缩进表示嵌套） | 编号保留为文本 "1. item"，按层级缩进（List Number / List Number 2 …；不用 Word 自动编号，参考文献与正文列表不会串号） |
| `> quote` | 缩进斜体段落 |
| 单独一行 `---` / `***` / `___` | 水平分隔线（段落下边框，不是文字） |
| `<!-- comment -->`（可跨行） | 删除（代码块内的保留）；占位注释（`<!-- PLACEHOLDER/TODO/TBD/pending/待补 -->` 等）记入 Placeholder warnings，其余注释在 Conversion notes 里列出位置（ℹ️ 已删除） |
| 脚注 `[^1]`、引用式链接 `[text][id]` / `[id]: url`、行内 HTML（`<sup>` `<sub>` `<br>` 以外）、`$…$` 公式、列表项里的标题 | **不转换**，原样作为文字；Conversion notes 逐条 ⚠️ 列出位置，导出前改写 |
| `\| table \|` | docx Table（带边框）；对齐行 `\|:-:\|--:\|` 设置列对齐；`\\|` 是单元格内的竖线；有对齐行时可省略首尾 `\|`；某行单元格多于表头 → 表格加宽、不丢内容，报告 ⚠️ |
| `![alt](path)` | 保留为文字并计入图数（注释和代码里的不算）；**图片不嵌入**，图文件单独上传 |
| UTF-8 BOM（Windows 记事本"UTF-8"保存） | 自动去掉；不是 UTF-8 的文件（如 GBK）→ exit 2，提示另存为 UTF-8 |

### Step 4：读导出报告

脚本能做到的检查（都写在 `export-report.md`）：

```
□ 字数分桶（只用期刊 limits 的数字比较；报告下方一行写明正文算了哪些部分、没算哪些、依据是什么）
  → Body = Introduction（+ section-N 综述板块）+ Methods + Results + Discussion（+ Related Work / Conclusion），
    再按 limits 的 body_excludes 增减：列为排除的不算（如 Nature Medicine / Cancer Cell / Cell Research 不算
    Methods），没列为排除的要算（如 Nature 的 summary paragraph 算在正文里）；条目没写 body_excludes 时按惯例
    （不算摘要、参考文献、图注、表格、Key Points）并注明
  → 正文文件里的图注 / 表题段落（"**Figure 1.** …"、"Table 2. …"）不算正文，单列一行
  → 中文 / 日文：每个汉字（假名）算 1 个词（按字计，不含标点），其余按空格分词；报告注明——
    期刊对中文字数的计法不一（有的含标点），以期刊要求为准
  → Abstract 单独计数；题页 / Key Points / Research in Context 单独列出
  → 模板写"每个图表折合 N 词"时，多给一行"正文 + N × 图表数"，按它判断（正文那一行不给 ✅，写"text only"）；
    库里该条没有 body_words 时这一行只给总数、不判断，和报告下方 Raw limits 里的原文人工比对
□ 参考文献条数：references.md 里 "1." / "[1]" / "(1)" / "- " 开头的条目（每行一条也行）；
  只有不带编号的段落时 → ❓（不会给 ✅）
□ 图数 = 不同的图注编号（"Figure 1." / "**Figure 1. …**" / "## Figure 1" / "Fig. 1 |" / "图1 …"）、
  正文引用到的最大图号、嵌入的 "![" 三者取大；Supplementary / Extended Data / eFigure / Figure S1 不算；
  中文"如图1""见表2""（图3）"算引用，"发表5篇""代表4级""试图9次"、附图 / 补充表里的 图 / 表 不算；
  figure-legends.md 有内容但认不出 "Figure N" → ❓
  表数 = Markdown 表格数、表题编号、正文引用的最大表号三者取大；
  期刊按图 + 表合计（display items / "included in figure limit"）时出一行 Display items
□ 状态：✅ 在限制内 · ✅* 在限制内但条目未核对（转告用户）· ⚠️ 超出 · ℹ️ 超出的是参考值（soft）/
  无限制 / 未检查 · ❓ 计数不确定，人工核对（≥N 表示至少 N）· 页数限制（如 IEEE）只列出，脚本不数页
□ 章节：实际顺序、纳入的文件、⚠️ 缺失的家族必需文件、ℹ️ 未导出的多余文件、图注文件的位置
□ 模板 special 字段原样列出（Reporting Summary、Patient Summary 等），需人工核对
□ Placeholder：见 Step 2 的标记清单（多行注释也算）— 覆盖段落、列表、标题、表格单元格，给出 文件:行号
```

脚本**做不到**、需要人工/其他 skill 完成的：页数估算（页数限制的期刊要在期刊模板里排版后数页）、字体/行距的"验证"（脚本按 family 设置，不再回读核验）、图片嵌入、题页单独文件（部分期刊要求单独上传题页：从 manuscript.docx 复制第一页即可）、参考文献格式正确性（`pubmed-search` Mode 6）。

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
  • 期刊条目未核对（报告里有 Unverified journal entry）→ 原样转告，请用户到期刊官网核对限制
  • 正文字数: [N] / [limit] ✅ / ✅* / ⚠️ 超出 [N] / ℹ️ / ❓（照报告写，不要把 ❓ 或 not checked 说成通过）
  • 摘要字数: [N] / [limit]
  • 参考文献: [N] / [limit]；图: [N] / [limit]；表: [N] / [limit]（或 Display items 合计）
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
| `manuscript/manuscript.docx` | 投稿主文件（带页码和连续行号，审稿回复可按 页码/行号 定位） |
| `manuscript/supplementary.docx` | 补充材料（`--supplementary` 且有 supplementary.md 时） |
| `export-report.md` | 导出质量报告（字数分桶、图表数、章节、placeholder） |

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "直接复制粘贴到 Word 就行" | Markdown 格式不会自动转换，会丢失结构和格式 |
| "所有期刊格式都一样" | Nature 系 Methods 放最后，JAMA 需要 Key Points，Lancet 需要 Research in Context——由 `family` 决定 |
| "字数超了一点没关系" | 超限会被 desk rejection；只比正文字数，摘要和参考文献分开算 |
| "`~90%` 会被当成下标" | 只有闭合的 `~x~` / `^x^` 才转格式，未成对符号原样保留 |
| "`18~65岁` 会被当成下标" | 数字后面的 `~` 是范围，原样保留；真正的下标（`H~2~O`）报告里逐条列出 |
| "报告里没有 ⚠️ 就是全部合格" | ❓（数不准）、ℹ️ not checked（该文章类型库里没有限制）、页数限制、✅*（条目未核对）都要人工核对或告诉用户 |
| "只是给导师看个 Word 版，也得先选期刊" | 用 `--journal generic`：期刊中立版式，不查限制；投稿前再按目标期刊重导 |
| "写作一结束就导出" | 先过 `peer-review-simulation` 和 `pre-submission-verification`，否则每次修改都要重导 |
| "表格用截图就行" | 多数期刊要求可编辑的表格，不接受图片形式 |
| "参考文献手动排版" | 用 `pubmed-search` Mode 6 自动格式化，减少人工错误 |
| "期刊不在库里就改插件目录的 YAML" | 写项目目录 `journal-overrides.yaml`，脚本会优先读取 |

## Convergence

当以下条件全部满足时完成：
1. `manuscript.docx` 已生成（需要时 `supplementary.docx` 也已生成）
2. 章节顺序与目标期刊 `family` 一致，家族必需文件无 ⚠️ 缺失
3. 正文/摘要字数、图表数、参考文献数均在模板限制内，或超限 / ❓ 无法确定 / 未检查（含 Unverified journal entry 提醒）已明确告知用户
4. Placeholder 已清零，或已列出并告知用户
5. `export-report.md` 已生成，`.mrp-state.json` 已更新

## Red Flags — STOP

- **不要在导出时修改论文内容** — 内容修改回 `manuscript-writing`
- **不要忽略字数超限** — 必须明确告知用户
- **不要把 ❓、not checked、✅* 说成"通过"** — 照报告原样告知用户，未核对的期刊条目请用户上官网确认
- **不要跳过 Placeholder 检测** — 带 placeholder 投稿会被 desk reject
- **不要手写 Markdown→docx 转换代码** — 用脚本，否则行内符号（`~`、`^`）可能被静默吞掉
- 脚本 exit 2（期刊 id 不存在）→ 停，用 `--search` 找 id 或写 `journal-overrides.yaml`，不要硬凑一个 family 导出（只要期刊中立的 Word 版时才用 `--journal generic`）
- 脚本 exit 2（输出路径会覆盖输入）→ 换一个输出文件名，不要删输入文件

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
