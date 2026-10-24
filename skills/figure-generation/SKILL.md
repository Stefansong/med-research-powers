---
name: figure-generation
description: Use when making or restyling journal figures from analysis results. Triggers on "画图"、"出图"、"投稿图"、"生存曲线"、"森林图"、"make a figure"、"KM plot"、"forest plot"、"journal figure format".
---

# Figure Generation

## Overview

每张图必须达到直接投稿的质量，而且每张图都要有存在的理由。顺序固定：先分析实际结果、论文主线和目标期刊的图表限制 → 写图表计划（`figure-plan.md`）→ 按 checkpoint_mode 确认 → 按实际数据现写作图代码（`pub_style.py` 只管样式，见 Step 3）。数据只能来自 `results-summary.md` / 分析产出，绝不编造数据点。

> 总调度规则（直接调用本 skill 也适用，原文见 `${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/SKILL.md`）：**结局盲**——SAP 确认前不画按组的结局图（规则见下方"还没有分析结果时"）；**缺前置产物**——说缺什么，light / auto 下先往下做并记缺口，不拒绝；**checkpoint_mode** 默认 light，计划展示后直接做；**只要一张图**时交付后停下。

**还没有分析结果时**（只有原始数据、没有已确认的 SAP——或 SAP 只有描述性部分、没有这张图对应的分析——用户要按组的结局图，如分组 KM 曲线、按组的结局箱线图、ROC）：这类图本身就是在看变量与结局的关系。只问一次：
- **要进论文** → 走 `data-analysis-planning`（没有 SAP 走快速路径，只有描述性 SAP 就补全它），SAP 里写好这张图对应的分析（如 KM + log-rank / Cox），问题和 SAP 草稿一次给用户、确认一次 → `statistical-analysis` 出结果 → 回本 skill 出图；
- **只想先看看** → 直接画，图题和文件名标 exploratory；按总调度结局盲规则记进状态文件（`python3 "${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py" note "SAP 前看过：<图>（exploratory）" --skill figure-generation`——只留备注，不用 `done`：SAP 还没确认，figure-generation 不算完成），`data-analysis-planning` 写 SAP 时照录进第 1 节；之后不拿它选 SAP 的方法。

不按组的描述性图（总体 KM、变量分布、人数流程）不受此限。

## When to Use

- 已有统计分析结果（`results-summary.md`），要生成投稿用的统计图表
- 已有图要改成期刊要求的格式 / 配色 / 分辨率

## When NOT to Use

- 数据探索阶段的草图（不走本 skill）；SAP 确认前按组画的结局图 → 按 Overview 的"还没有分析结果时"处理
- 流程图 / 架构图（CONSORT、PRISMA、STROBE 参与者流程图等）→ 不属于统计作图，用 graphviz / draw.io / PowerPoint 手工绘制；流程图**内容**要求由 `reporting-standards` 给出

## Workflow

### Step 0: 读取用户偏好

目标期刊已定（`.mrp-state.json` 的 `target_journal`，存的是期刊库 id）时以期刊要求为准，把这个 id 直接传给 `setup(journal=...)` / `journal_figsize(...)`：Nature / Lancet / JAMA 系列的刊用本系列的栏宽和配色，其他期刊用通用栏宽和色盲友好的 Okabe-Ito 配色，并在 stderr 提示一行（按该刊作者须知核对尺寸）。否则读 `~/.claude/mrp-user-profile.json` 的 `preferred_figure_style`（nature / lancet / jama / nejm / default，对应 `COLORS` 的 key，default = Okabe-Ito）；没有设置时用 default，不为此停下来问，摘要里说一句"配色用了默认 Okabe-Ito，可换 Nature / Lancet / JAMA / NEJM 风格并保存为偏好"。

### Step 1: 分析实际结果、论文主线和期刊限制

画图之前先弄清楚下面几件事（只读已有产物，不重新分析数据）。**只改已有图的格式**（不改数据和内容）时不需要 `results-summary.md`、SAP 和 `figure-plan.md`：跳过 Step 1–2，从 Step 3 开始，与 `figure-plan.md` 有关的检查项免查。
- **实际结果**：读 `results-summary.md`——主要结局的结果与效应大小，次要 / 亚组 / 敏感性结果各有哪些，哪些结论稳健。其中的 "Figures Needed"（如有）只是分析阶段的初步建议，不是最终清单。
- **论文主线**：从 `study-protocol.md` 的研究问题和主要结局出发，想清楚论文要讲的那条线（例如主要结局 → 支持它的次要结果 → 稳健性），每张图都要服务这条线。
- **目标期刊限制**：取 `.mrp-state.json` 的 `target_journal`，用 `python3 "${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/get_journal_template.py" --id <期刊id>` 取该刊 `limits` 里的 `figures` / `tables`（图和表合并计数时只有 `display_items`）作为正文图表数量上限；多面板限制、补充材料规则看原文 `figures` / `tables` / `special` 字段。脚本提示条目未核实（无 `guidelines_checked`）时，把警告转告用户，计划里注明"期刊图表上限待官网确认"。综述等非原始研究看 `limits_by_type`。期刊不在库里 → 按 `manuscript-writing` 的规则写项目目录的 `journal-overrides.yaml`；还没暂定期刊 → 提醒用户（可先走 `journal-selection`），计划里注明"期刊定后复核数量"。
- **用图还是用表**：读者要查精确数值的（基线特征、多个结局的效应量与 CI）用表；要看趋势、分布、随时间变化或多组对比的（生存曲线、ROC、亚组森林图、个体数据分布）用图。同一组数据不要既画图又列表（ICMJE 建议）。

### Step 2: 写图表计划 → 按 checkpoint_mode 确认

写 `figure-plan.md`，每张图 / 表一行：

| 编号 | 回答什么问题（一句话） | 数据来源（`results-summary.md` 的哪一节 / 哪个结果文件） | 图型及理由 | 正文 / 补充材料 | 面板数与栏宽 |
|------|------|------|------|------|------|

末尾核对数量：正文图表总数不超过期刊上限（流程图也占名额；图表合并计数的期刊把表也算上），超出的移到补充材料或合并面板。

把计划和理由给用户看，按总调度的 checkpoint_mode 处理计划确认。

### Step 3: 样式设置

`${CLAUDE_PLUGIN_ROOT}/skills/figure-generation/scripts/pub_style.py` 只管期刊样式：字体、字号、线宽、配色、栏宽尺寸、导出格式与 dpi、显著性标注。画什么、用什么图型、数据怎么整理，由 Step 2 的计划和实际数据决定，作图代码现写。

作图代码要能脱离插件重新出图：先把 `pub_style.py` 复制进项目根目录（它是单个文件，运行时不读插件里的其他文件），作图脚本从这份副本 import，不从插件安装路径 import、不往 `sys.path` 里塞插件目录；副本随作图脚本一起保存和公开：

```bash
cp "${CLAUDE_PLUGIN_ROOT}/skills/figure-generation/scripts/pub_style.py" .
```

```python
from pub_style import (setup, save_figure, add_significance, journal_figsize,
                       COLORS, COLORBLIND_SAFE)
import matplotlib.pyplot as plt

# 全局 rcParams + 配色 + 单栏宽度（英寸）；字体链 Arial → Helvetica → Liberation Sans → DejaVu Sans
# journal 按 Step 0 填：目标期刊 id（如 'nature-medicine'；期刊库里写的全名如 'Nature Medicine' 也行）或偏好风格（'nature' 只是示例）
colors, width = setup(journal='nature', single_column=True)

# 按期刊和面板数选图尺寸：nature 系列 89/183 mm；lancet / jama 系列、bmj 约 85/175 mm；
# 其他期刊用通用 85/170 mm（会提示一行，按该刊作者须知核对）
# layout='constrained' 可用；不要传 bbox_inches='tight'（导出按这个尺寸原样保存，保证正好是期刊栏宽）
fig, ax = plt.subplots(figsize=journal_figsize(journal='nature', n_panels=1), layout='constrained')

# 组间比较图上添加显著性桥（***/**/*/ns；height 是坐标轴高度的比例，默认 2%，对数轴按数量级算）
# p 值缺失、NaN 或不在 0–1 之间时 p_to_stars 会报 ValueError：这时自己传 text=（不要标成 ns）
# add_significance(ax, x1=0, x2=1, y=y_top, p_value=0.003)

# 保存为投稿格式：TIFF（RGB、无透明通道、LZW 压缩）+ PDF，尺寸与图幅一致、不裁边；
# 线条图默认 600 dpi，照片/热图用 line_art=False → 300 dpi；内容超出图幅时会警告；
# 文件里不写创建时间、SVG 编号固定：图没变时重新出图逐字节相同（reproduce_check 一致）；
# 要写标题、作者等元数据用 metadata={'Title': ..., 'Author': ...}：每种格式只写它能存的键（SVG 把 Author 记成 Creator，
# EPS 只存 Creator），其余跳过并提示一次；有值写不进去时报错，一个文件也不写
save_figure(fig, 'figure1')                       # → figure1.tiff + figure1.pdf
```

`setup()` 若发现系统没有 Arial/Helvetica，会**只提示一次**并回退到 Liberation Sans / DejaVu Sans——此时图能生成，但投稿前要在装有 Arial 的机器上重新导出（Ubuntu：`sudo apt install ttf-mscorefonts-installer`）。`python3 "${CLAUDE_PLUGIN_ROOT}/skills/figure-generation/scripts/pub_style.py" --check` 可查看字体和各期刊栏宽。

### Step 4: 按计划逐图现写作图代码

按 `figure-plan.md` 逐张画。作图代码按这张图的实际数据现写（图型、坐标轴、分组、标注都按数据和计划定，不套固定模板）；数据从分析输出（结果表 CSV、模型导出）读取，不手抄数字、不从图上估读；每张图的 p 值、n、效应量必须与 `results-summary.md` 一致。作图代码保存成脚本（如 `make_figures.py`），能一键重新出图。

### Step 5: 质量检查（每张图）

- [ ] 与 `figure-plan.md` 一致；正文图表数不超期刊上限
- [ ] 字体 Arial/Helvetica，最终缩放后 ≥ 6pt
- [ ] 线条图 ≥ 600 DPI，照片/热图 ≥ 300 DPI
- [ ] 坐标轴标签完整（含单位）；图例清晰、不遮挡数据
- [ ] 配色色盲友好（`COLORBLIND_SAFE` 或 `setup(colorblind_safe=True)`）
- [ ] p 值标注格式正确（*P* < 0.05, *P* = 0.001）
- [ ] 保存了 TIFF + PDF 双格式；多 panel 用 a/b/c 标注并与图注对应

### Step 6: 图注 + 更新状态

把每张图的图注写进 `manuscript/figure-legends.md`（每条以 "**Figure N.**" 开头；manuscript-export 先读这里，没有时才读项目根目录的 `figure-legends.md`，导出报告会写明用的是哪个，两处都有时只导出 manuscript/ 那份）；输出 3–5 行摘要，然后 `python3 ${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py done figure-generation --output manuscript/figure-legends.md [--output figure-plan.md] --next manuscript-writing`，按 checkpoint_mode 进入 `manuscript-writing`。

**只改已有图的格式**时：图注只在编号或面板变了时更新；`--output` 写重新导出的图文件（如 `--output figure1.tiff --output figure1.pdf`），`--next` 写用户接下来要做的；交付后停下，不自动进入 `manuscript-writing`。

## Journal Requirements

完整的格式 / 分辨率 / 字体 / 栏宽 / 颜色规范见 `references/figure-specs.yaml`；图表数量限制按 Step 1 用脚本取（不要整读 `journal-templates.yaml`），并以期刊 "Instructions for Authors" 为准。

## Common Figure Types（参考，不是必须清单）

按图表计划选用：不要求每篇都画，也不限于这些。下面只列各图型必须包含的要素。

1. **箱线图 + 散点** — 组间比较，显示个体值 + p 值标注
2. **ROC 曲线** — AUC + 95% CI，最佳截断点，多模型不同颜色
3. **Kaplan-Meier** — 风险表 + 95% CI 阴影 + log-rank p 值
4. **森林图** — 效应量 + CI + 异质性 I² + 总体效应菱形
5. **火山图** — log2(FC) vs -log10(p)，标注差异显著的分子
6. **热图** — Z-score 标准化 + 层次聚类 + 侧边注释
7. **PCA/PLS-DA** — 95% 置信椭圆 + 解释方差 %
8. **校准曲线 / DCA** — 预测模型必备（TRIPOD）

## Output

| 产出 | 必须/可选 | 说明 |
|------|---------|------|
| `figure-plan.md` | 必须（只改格式时不需要） | 图表计划：每张图 / 表回答的问题、数据来源、图型及理由、正文 / 补充、期刊数量核对 |
| `figureN.tiff` | 必须 | 投稿主格式，线条图 600 DPI / 半色调 300 DPI，LZW 压缩 |
| `figureN.pdf` | 必须 | 矢量备份格式，便于排版与缩放（字体以 TrueType 嵌入，可编辑） |
| `manuscript/figure-legends.md` | 必须（只改格式时沿用已有图注） | 每张图配独立图注：标题句 + 各 panel 说明 + 缩写 + 统计方法 + 样本量 + 显著性符号含义；按图号排列，交付给 `manuscript-writing` |
| 多 panel 标签 | 如适用 | 子图用 a/b/c 标注，与图注对应 |
| 作图脚本（如 `make_figures.py`） | 推荐 | 现写的作图代码，数据改了能一键重新出图 |

不交付 PNG/JPG 作为投稿文件（仅探索阶段可用）。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "照常见图型清单每种画一张" | 图由实际结果和论文主线决定；期刊图数有限，精确数值多的结果用表 |
| "用默认 matplotlib 样式够了" | 默认样式字体/字号/线宽全不达标 |
| "图例写 Group 1/2/3" | 用有意义的标签，审稿人不知道 Group 1 是什么 |

## Convergence

当以下条件全部满足时完成：
1. 新画统计图：`figure-plan.md` 已写好（每张图回答的问题、图型、正文 / 补充）并按 checkpoint_mode 确认，正文图表数不超期刊上限；只改已有图的格式：不需要 `figure-plan.md`
2. 要交付的图全部生成，每张通过 Step 5 质量 checklist，保存了 TIFF + PDF 格式
3. `manuscript/figure-legends.md` 已撰写（只改格式时：编号或面板变了的图注已更新）
4. `.mrp-state.json` 已更新（只改格式时按 Step 6 的写法）

## Red Flags — STOP

- 用图中没有的数据 / 编造数据点作图 → 绝对禁止，立即停止
- 柱状图隐藏分布（无个体数据点、无误差棒）→ 停，叠加散点或改用箱线图
- 配色非色盲友好 → 停，改用 `COLORBLIND_SAFE` 或重新配色
- 导出为 PNG/JPG 作为投稿文件 → 停，必须 TIFF + PDF
- 字体非 Arial/Helvetica 或字号 <6pt（缩放后）→ 停，重设样式
- 显著性标注的 p 值与 `results-summary.md` 不一致 → 停，核对来源
- 正文图表数已超过目标期刊上限还在加图 → 停，回 `figure-plan.md` 取舍（移到补充材料、合并面板或改用表）

## 衔接规则

### 前置依赖（缺了按总调度"缺前置产物时"处理）
- 新画统计图：`results-summary.md`（`statistical-analysis` 生成）；只改已有图的格式不需要

### 强制衔接（不可跳过）
- 完成后 → `manuscript-writing`（图文件 + `figure-legends.md`）
- 最后一步固定为更新 `.mrp-state.json`（Step 6）
- `figure-plan.md`（正文 / 补充的分配）→ `manuscript-writing` 列提纲时对照

### 可选衔接
- 换期刊时由 `journal-selection` 更新 `target_journal`，并按新期刊的限制复核 `figure-plan.md`
- 报告规范对图的要求（如 TRIPOD 的校准图、PRISMA/CONSORT 流程图内容）→ `reporting-standards`
- 投稿前的图形合规复核 → `pre-submission-verification`
