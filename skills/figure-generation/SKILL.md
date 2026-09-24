---
name: figure-generation
description: Use when creating publication-quality statistical figures from analysis results for journal submission. Triggers on "画图"、"作图"、"出图"、"figure generation"、"热图"、"箱线图"、"ROC"、"生存曲线"、"森林图"、"火山图".
---

# Figure Generation

## Overview

每张图必须达到直接投稿的质量，而且每张图都要有存在的理由。顺序固定：先分析实际结果、论文主线和目标期刊的图表限制 → 写图表计划（`figure-plan.md`）→ 按 checkpoint_mode 确认 → 按实际数据现写作图代码。`${CLAUDE_PLUGIN_ROOT}/skills/figure-generation/scripts/pub_style.py` 只负责期刊样式（字体、尺寸、dpi、配色、导出格式），不决定画什么、怎么画（运行目录是用户项目，不是插件目录，必须用 `${CLAUDE_PLUGIN_ROOT}` 定位）。数据只能来自 `results-summary.md` / 分析产出，绝不编造数据点。

## When to Use

- 已有统计分析结果（`results-summary.md`），要生成投稿用的统计图表
- 已有图要改成期刊要求的格式 / 配色 / 分辨率

## When NOT to Use

- 数据探索阶段的草图（不走本 skill）；按组画的结局图（如分组 KM 曲线）受总调度结局盲规则约束：SAP 确认前只在用户明确要探索性分析时画，标 exploratory
- 流程图 / 架构图（CONSORT、PRISMA、STROBE 参与者流程图等）→ 不属于统计作图，用 graphviz / draw.io / PowerPoint 手工绘制；流程图**内容**要求由 `reporting-standards` 给出
- 要从原始数据画结局相关的图但还没有分析结果 → 先 `statistical-analysis`（没有 SAP 时走 `data-analysis-planning` 快速路径）

## Workflow

### Step 0: 读取用户偏好

读取 `~/.claude/mrp-user-profile.json` 的 `preferences.preferred_figure_style`（取值 nature / lancet / jama / nejm / default，对应 `COLORS` 的 key）。没有该字段 → 只问这一个问题（"图表配色风格用 Nature / Lancet / JAMA / NEJM 哪一种？"），并问是否保存到该文件供以后使用。目标期刊已定（`.mrp-state.json` 的 `target_journal`）时以期刊要求优先。

### Step 1: 分析实际结果、论文主线和期刊限制

画图之前先弄清楚下面几件事（只读已有产物，不重新分析数据）。**只改已有图的格式**（不改数据和内容）时不需要 `results-summary.md`、SAP 和 `figure-plan.md`：跳过 Step 1–2，从 Step 3 开始，与 `figure-plan.md` 有关的检查项免查。
- **实际结果**：读 `results-summary.md`——主要结局的结果与效应大小，次要 / 亚组 / 敏感性结果各有哪些，哪些结论稳健。其中的 "Figures Needed"（如有）只是分析阶段的初步建议，不是最终清单。
- **论文主线**：从 `study-protocol.md` 的研究问题和主要结局出发，想清楚论文要讲的那条线（例如主要结局 → 支持它的次要结果 → 稳健性），每张图都要服务这条线。
- **目标期刊限制**：取 `.mrp-state.json` 的 `target_journal`，用 `python3 "${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/get_journal_template.py" --id <期刊id>` 取该刊的 `figures` / `tables` 字段（正文图表数量上限、图和表是否合并计数、多面板限制、补充材料规则）。期刊不在库里 → 按 `manuscript-writing` 的规则写项目目录的 `journal-overrides.yaml`；还没暂定期刊 → 提醒用户（可先走 `journal-selection`），计划里注明"期刊定后复核数量"。
- **用图还是用表**：读者要查精确数值的（基线特征、多个结局的效应量与 CI）用表；要看趋势、分布、随时间变化或多组对比的（生存曲线、ROC、亚组森林图、个体数据分布）用图。同一组数据不要既画图又列表（ICMJE 建议）。

### Step 2: 写图表计划 → 按 checkpoint_mode 确认

写 `figure-plan.md`，每张图 / 表一行：

| 编号 | 回答什么问题（一句话） | 数据来源（`results-summary.md` 的哪一节 / 哪个结果文件） | 图型及理由 | 正文 / 补充材料 | 面板数与栏宽 |
|------|------|------|------|------|------|

末尾核对数量：正文图表总数不超过期刊上限（流程图也占名额；图表合并计数的期刊把表也算上），超出的移到补充材料或合并面板。

把计划和理由给用户看，按 `checkpoint_mode`：`step` 等用户确认后再画；`light` / `auto` 展示后直接画，用户随时可以改计划。

### Step 3: 样式设置

`pub_style.py` 只管期刊样式：字体、字号、线宽、配色、栏宽尺寸、导出格式与 dpi、显著性标注。画什么、用什么图型、数据怎么整理，由 Step 2 的计划和实际数据决定，作图代码现写。

```python
import os, sys
sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."),
                                "skills", "figure-generation", "scripts"))
from pub_style import (setup, save_figure, add_significance, journal_figsize,
                       COLORS, COLORBLIND_SAFE)
import matplotlib.pyplot as plt

# 全局 rcParams + 配色 + 单栏宽度（英寸）；字体链 Arial → Helvetica → Liberation Sans → DejaVu Sans
# journal 按 Step 0 的偏好 / 目标期刊填（'nature' 只是示例）
colors, width = setup(journal='nature', single_column=True)

# 按期刊和面板数选图尺寸：nature 89/183 mm；lancet/bmj/jama 约 85/175 mm；未知期刊用通用 85/170 mm
fig, ax = plt.subplots(figsize=journal_figsize(journal='nature', n_panels=1))

# 组间比较图上添加显著性桥（***/**/*/ns；height 是 y 轴范围的比例，默认 2%）
# add_significance(ax, x1=0, x2=1, y=y_top, p_value=0.003)

# 保存为投稿格式：TIFF (LZW) + PDF；线条图默认 600 dpi，照片/热图用 line_art=False → 300 dpi
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

把每张图的图注写进 `figure-legends.md`；输出 3–5 行摘要，然后更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：`completed_skills` 追加 figure-generation 及产物、`next_step` 设为 manuscript-writing），按 checkpoint_mode 进入 `manuscript-writing`。

## Journal Requirements

完整的格式 / 分辨率 / 字体 / 栏宽 / 颜色规范见 `references/figure-specs.yaml`（TIFF 首选；线条图 600 DPI、半色调 300 DPI；Arial/Helvetica ≥6pt；栏宽按期刊，通用 85/170 mm；色盲友好）。目标期刊的图表数量限制按 Step 1 用脚本取（不要整读 `journal-templates.yaml`），并以其 "Instructions for Authors" 为准。

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
| `figure-legends.md` | 必须 | 每张图配独立图注：标题句 + 各 panel 说明 + 缩写 + 统计方法 + 样本量 + 显著性符号含义；按图号排列，交付给 `manuscript-writing` |
| 多 panel 标签 | 如适用 | 子图用 a/b/c 标注，与图注对应 |
| 作图脚本（如 `make_figures.py`） | 推荐 | 现写的作图代码，数据改了能一键重新出图 |

不交付 PNG/JPG 作为投稿文件（仅探索阶段可用）。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "照常见图型清单每种画一张" | 图由实际结果和论文主线决定；期刊图数有限，精确数值多的结果用表 |
| "用默认 matplotlib 样式够了" | 默认样式字体/字号/线宽全不达标 |
| "柱状图展示数据就行" | 必须叠加个体数据点，柱状图隐藏分布 |
| "用 PNG 就行" | 期刊要求 TIFF 或矢量 PDF；PNG 多为屏幕分辨率 |
| "颜色好看就行" | 必须色盲友好（~8% 男性色觉异常） |
| "图例写 Group 1/2/3" | 用有意义的标签，审稿人不知道 Group 1 是什么 |
| "Linux 没 Arial 无所谓" | 期刊按字体检查；先用回退字体出图，投稿前在有 Arial 的机器重导 |

## Convergence

当以下条件全部满足时完成：
1. `figure-plan.md` 已写好（每张图回答的问题、图型、正文 / 补充）并按 checkpoint_mode 确认；正文图表数不超期刊上限
2. 计划中的图全部生成，每张通过质量 checklist
3. 保存了 TIFF + PDF 格式
4. `figure-legends.md` 已撰写
5. `.mrp-state.json` 已更新

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
