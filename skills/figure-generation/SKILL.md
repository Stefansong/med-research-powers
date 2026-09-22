---
name: figure-generation
description: Use when creating publication-quality statistical figures from analysis results for journal submission. Triggers on "画图"、"作图"、"出图"、"figure generation"、"热图"、"箱线图"、"ROC"、"生存曲线"、"森林图"、"火山图".
---

# Figure Generation

## Overview

每张图必须达到直接投稿的质量。用 `${CLAUDE_PLUGIN_ROOT}/skills/figure-generation/scripts/pub_style.py` 设置全局样式（运行目录是用户项目，不是插件目录，必须用 `${CLAUDE_PLUGIN_ROOT}` 定位）。数据只能来自 `results-summary.md` / 分析产出，绝不编造数据点。

## When to Use

- 已有统计分析结果（`results-summary.md`），要生成投稿用的统计图表
- 已有图要改成期刊要求的格式 / 配色 / 分辨率

## When NOT to Use

- 数据探索阶段的草图（用默认样式即可，不走本 skill）
- 流程图 / 架构图（CONSORT、PRISMA、STROBE 参与者流程图等）→ 不属于统计作图，用 graphviz / draw.io / PowerPoint 手工绘制；流程图**内容**要求由 `reporting-standards` 给出
- 还没有分析结果 → 先 `statistical-analysis`

## Workflow

### Step 0: 读取用户偏好

读取 `~/.claude/mrp-user-profile.json` 的 `preferences.preferred_figure_style`（取值 nature / lancet / jama / nejm / default，对应 `COLORS` 的 key）。没有该字段 → 只问这一个问题（"图表配色风格用 Nature / Lancet / JAMA / NEJM 哪一种？"），并问是否保存到该文件供以后使用。目标期刊已定（`.mrp-state.json` 的 `target_journal`）时以期刊要求优先。

### Step 1: 样式设置

```python
import os, sys
sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", "."),
                                "skills", "figure-generation", "scripts"))
from pub_style import (setup, save_figure, add_significance, journal_figsize,
                       COLORS, COLORBLIND_SAFE)
import matplotlib.pyplot as plt

# 全局 rcParams + 配色 + 单栏宽度（英寸）；字体链 Arial → Helvetica → Liberation Sans → DejaVu Sans
colors, width = setup(journal='nature', single_column=True)

# 按期刊和面板数选图尺寸：nature 89/183 mm；lancet/bmj/jama 约 85/175 mm；未知期刊用通用 85/170 mm
fig, ax = plt.subplots(figsize=journal_figsize(journal='nature', n_panels=1))

# 组间比较图上添加显著性桥（***/**/*/ns；height 是 y 轴范围的比例，默认 2%）
# add_significance(ax, x1=0, x2=1, y=y_top, p_value=0.003)

# 保存为投稿格式：TIFF (LZW) + PDF；线条图默认 600 dpi，照片/热图用 line_art=False → 300 dpi
save_figure(fig, 'figure1')                       # → figure1.tiff + figure1.pdf
```

`setup()` 若发现系统没有 Arial/Helvetica，会**只提示一次**并回退到 Liberation Sans / DejaVu Sans——此时图能生成，但投稿前要在装有 Arial 的机器上重新导出（Ubuntu：`sudo apt install ttf-mscorefonts-installer`）。`python3 "${CLAUDE_PLUGIN_ROOT}/skills/figure-generation/scripts/pub_style.py" --check` 可查看字体和各期刊栏宽。

### Step 2: 逐图生成

按 `results-summary.md` 的 "Figures Needed" 清单逐张生成；每张图的 p 值、n、效应量必须与 `results-summary.md` 一致。

### Step 3: 质量检查（每张图）

- [ ] 字体 Arial/Helvetica，最终缩放后 ≥ 6pt
- [ ] 线条图 ≥ 600 DPI，照片/热图 ≥ 300 DPI
- [ ] 坐标轴标签完整（含单位）；图例清晰、不遮挡数据
- [ ] 配色色盲友好（`COLORBLIND_SAFE` 或 `setup(colorblind_safe=True)`）
- [ ] p 值标注格式正确（*P* < 0.05, *P* = 0.001）
- [ ] 保存了 TIFF + PDF 双格式；多 panel 用 a/b/c 标注并与图注对应

### Step 4: 图注 + 更新状态

把每张图的图注写进 `figure-legends.md`；输出 3–5 行摘要，然后更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：`completed_skills` 追加 figure-generation 及产物、`next_step` 设为 manuscript-writing），直接进入 `manuscript-writing`。

## Journal Requirements

完整的格式 / 分辨率 / 字体 / 栏宽 / 颜色规范见 `references/figure-specs.yaml`（TIFF 首选；线条图 600 DPI、半色调 300 DPI；Arial/Helvetica ≥6pt；栏宽按期刊，通用 85/170 mm；色盲友好）。目标期刊的具体要求查 `${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/references/journal-templates.yaml` 中该期刊的 `figures` 字段（只抽取该期刊条目，不整读文件），并以其 "Instructions for Authors" 为准。

## Common Figure Types

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
| `figureN.tiff` | 必须 | 投稿主格式，线条图 600 DPI / 半色调 300 DPI，LZW 压缩 |
| `figureN.pdf` | 必须 | 矢量备份格式，便于排版与缩放（字体以 TrueType 嵌入，可编辑） |
| `figure-legends.md` | 必须 | 每张图配独立图注：标题句 + 各 panel 说明 + 缩写 + 统计方法 + 样本量 + 显著性符号含义；按图号排列，交付给 `manuscript-writing` |
| 多 panel 标签 | 如适用 | 子图用 a/b/c 标注，与图注对应 |

不交付 PNG/JPG 作为投稿文件（仅探索阶段可用）。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "用默认 matplotlib 样式够了" | 默认样式字体/字号/线宽全不达标 |
| "柱状图展示数据就行" | 必须叠加个体数据点，柱状图隐藏分布 |
| "用 PNG 就行" | 期刊要求 TIFF 或矢量 PDF；PNG 多为屏幕分辨率 |
| "颜色好看就行" | 必须色盲友好（~8% 男性色觉异常） |
| "图例写 Group 1/2/3" | 用有意义的标签，审稿人不知道 Group 1 是什么 |
| "Linux 没 Arial 无所谓" | 期刊按字体检查；先用回退字体出图，投稿前在有 Arial 的机器重导 |

## Convergence

当以下条件全部满足时完成：
1. `results-summary.md` 中所有需要的图表已生成
2. 每张图通过质量 checklist
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

## 衔接规则

### 前置依赖（不满足则阻止）
- **必须**有 `results-summary.md`（`statistical-analysis` 生成）

### 强制衔接（不可跳过）
- 完成后 → `manuscript-writing`（图文件 + `figure-legends.md`）
- 最后一步固定为更新 `.mrp-state.json`（Step 4）

### 可选衔接
- 目标期刊有特殊图形规范 → 查 `${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/references/journal-templates.yaml` 该期刊条目；换期刊时由 `journal-selection` 更新 `target_journal`
- 报告规范对图的要求（如 TRIPOD 的校准图、PRISMA/CONSORT 流程图内容）→ `reporting-standards`
- 投稿前的图形合规复核 → `pre-submission-verification`
