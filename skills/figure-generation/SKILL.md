---
name: figure-generation
description: Use when creating publication-quality figures for journal submission. Triggers on "画图"、"做图"、"可视化"、"Figure"、"热图"、"箱线图"、"ROC"、"生存曲线"、"森林图"、"火山图".
---

# Figure Generation

## Overview

每张图必须达到直接投稿的质量。使用 `${CLAUDE_PLUGIN_ROOT}/skills/figure-generation/scripts/pub_style.py` 设置全局样式（运行目录是用户项目，不是插件目录，必须用 `${CLAUDE_PLUGIN_ROOT}` 定位）。

## When to Use

生成任何用于论文投稿的统计图表。

## When NOT to Use

- 数据探索阶段的草图（可以用默认样式）
- 流程图/架构图（用 graphviz 或手动工具）

## Workflow

### Setup

```python
import sys; sys.path.insert(0, 'scripts')
from pub_style import (
    setup, save_figure, COLORS, COLORBLIND_SAFE,
    add_significance, journal_figsize,
)

# 全局样式 + 单栏宽度（85mm）
colors, width = setup(journal='nature', single_column=True)

# 按期刊和面板数选图尺寸（返回 (w, h) inches）
figsize = journal_figsize(journal='nature', n_panels=1)

# 组间比较图上添加显著性标注桥（自动 ***/**/*/ns）
# add_significance(ax, x1=0, x2=1, y=y_top, p_value=0.003)

# 保存为投稿格式（默认 TIFF + PDF, 300 DPI）
# save_figure(fig, 'figure1')
```

`pub_style.py` 提供：`setup`（全局 rcParams + 配色 + 宽度）、`save_figure`（多格式导出）、`add_significance`（显著性桥标注）、`journal_figsize`（按期刊/面板数定尺寸）、`COLORS`（各期刊配色）、`COLORBLIND_SAFE`（Okabe-Ito 色盲友好调色板）。

## Journal Requirements

完整的格式 / 分辨率 / 字体 / 栏宽 / 颜色规范见 `references/figure-specs.yaml`（TIFF 首选，≥300 DPI、线条图≥600 DPI，Arial/Helvetica ≥6pt，单栏 85mm / 双栏 170mm，色盲友好）。目标期刊有特殊要求时以其 "Instructions for Authors" 为准。

## Common Figure Types

1. **箱线图 + 散点** — 组间比较，显示个体值 + p 值标注
2. **ROC 曲线** — AUC + 95% CI，最佳截断点，多模型不同颜色
3. **Kaplan-Meier** — 风险表 + 95% CI 阴影 + log-rank p 值
4. **森林图** — 效应量 + CI + 异质性 I² + 总体效应菱形
5. **火山图** — log2(FC) vs -log10(p)，标注差异显著的分子
6. **热图** — Z-score 标准化 + 层次聚类 + 侧边注释
7. **PCA/PLS-DA** — 95% 置信椭圆 + 解释方差 %
8. **CONSORT/STROBE 流程图** — 参与者筛选流程

## Quality Checklist

每张图生成后检查：
- [ ] 字体 Arial，≥ 6pt
- [ ] 分辨率 ≥ 300 DPI
- [ ] 坐标轴标签完整（含单位）
- [ ] 图例清晰，位置不遮挡数据
- [ ] 配色色盲友好（用 `COLORBLIND_SAFE` 调色板或在线检验）
- [ ] p 值标注格式正确（*P* < 0.05, *P* = 0.001）
- [ ] 保存了 TIFF + PDF 双格式

## Output

每张图必须产出可直接投稿的文件 + 配套图注：

| 产出 | 必须/可选 | 说明 |
|------|---------|------|
| `figureN.tiff` | 必须 | 投稿主格式，≥300 DPI（线条图 ≥600 DPI），LZW 压缩 |
| `figureN.pdf` | 必须 | 矢量备份格式，便于排版与缩放 |
| Figure legend | 必须 | 每张图配独立图注（标题句 + 各 panel 说明 + 缩写 + 统计方法 + 样本量 + 显著性符号含义） |
| 多 panel 标签 | 如适用 | 子图用 a/b/c 标注，与图注对应 |

- 文件统一用 `save_figure(fig, 'figureN')` 导出（默认同时生成 TIFF + PDF）。
- Figure legends 可单独存为 `figure-legends.md`，按图号排列，交付给 `manuscript-writing`。
- 不交付 PNG/JPG 作为投稿文件（仅探索阶段可用）。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "用默认 matplotlib 样式够了" | 默认样式字体/字号/线宽全不达标 |
| "柱状图展示数据就行" | 必须叠加个体数据点，柱状图隐藏分布 |
| "用 PNG 就行" | 期刊要求 TIFF 或矢量 PDF |
| "颜色好看就行" | 必须色盲友好（~8% 男性色觉异常） |
| "图例写 Group 1/2/3" | 用有意义的标签，审稿人不知道 Group 1 是什么 |

## Convergence

当以下条件全部满足时完成：
1. 所有需要的图表已生成
2. 每张图通过质量 checklist
3. 保存了 TIFF + PDF 格式
4. Figure legends 已撰写

## Red Flags — STOP

- 用图中没有的数据 / 编造数据点作图 → 绝对禁止，立即停止
- 柱状图隐藏分布（无个体数据点、无误差棒）→ 停，叠加散点或改用箱线图
- 配色非色盲友好 → 停，改用 `COLORBLIND_SAFE` 或重新配色
- 导出为 PNG/JPG 作为投稿文件 → 停，必须 TIFF + PDF
- 字体非 Arial/Helvetica 或字号 <6pt（缩放后）→ 停，重设样式
- 显著性标注的 p 值与 `results-summary.md` 不一致 → 停，核对来源

## 衔接规则

### 前置依赖
- **必须**有完成的统计分析结果（`statistical-analysis`）

### 强制衔接
- 所有图表完成后 → 传递给 `manuscript-writing` 使用

### 可选衔接
- 目标期刊有特殊图形规范 → 可调用 `journal-selection` / 查 `manuscript-writing` 的 `references/journal-templates.yaml` 确认
- 投稿前需核对图形是否符合报告规范 → 可调用 `reporting-standards`（如 CONSORT 流程图、PRISMA 流程图）
