---
name: figure-generation
description: Use when creating publication-quality figures for journal submission. Triggers on "画图"、"做图"、"可视化"、"Figure"、"热图"、"箱线图"、"ROC"、"生存曲线"、"森林图"、"火山图".
---

# Figure Generation

## Overview

每张图必须达到直接投稿的质量。使用 `scripts/pub_style.py` 设置全局样式。

## When to Use

生成任何用于论文投稿的统计图表。

## When NOT to Use

- 数据探索阶段的草图（可以用默认样式）
- 流程图/架构图（用 graphviz 或手动工具）

## Workflow

### Setup

```python
import sys; sys.path.insert(0, 'scripts')
from pub_style import setup, save_figure, COLORS, COLORBLIND_SAFE

colors, width = setup(journal='nature', single_column=True)
```

## Journal Requirements

| 项目 | 要求 |
|------|------|
| 格式 | TIFF（首选）或 PDF |
| 分辨率 | ≥ 300 DPI（线条图 ≥ 600 DPI） |
| 字体 | Arial / Helvetica |
| 最小字号 | 6pt（缩放后） |
| 单栏宽度 | 85mm ≈ 3.35 inch |
| 双栏宽度 | 170mm ≈ 6.7 inch |
| 颜色 | CMYK（打印）或 RGB（在线），推荐色盲友好 |

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

## 衔接规则

### 前置依赖
- **必须**有完成的统计分析结果（`statistical-analysis`）

### 强制衔接
- 所有图表完成后 → 传递给 `manuscript-writing` 使用
