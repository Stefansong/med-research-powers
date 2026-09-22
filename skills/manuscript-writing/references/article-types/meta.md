# D. Meta-Analysis（含 D2 Network Meta-Analysis）

> 由 `manuscript-writing` SKILL.md 的 Article Type Router 按需加载。**在 `systematic.md` 基础上追加**：前置依赖、写作顺序、Output Structure 同 Systematic Review，另需 Meta 分析统计结果 + 森林图（`statistical-analysis` / `figure-generation` 产物）。

## Methods 增加

- Effect Measure（OR / RR / HR / MD / SMD + 选择理由）
- Heterogeneity Assessment（I², Cochran Q, τ², 预测区间）
- Model Selection：**模型在方案/注册时预先指定**（随机效应 vs 固定效应 + 理由，如研究间临床/方法学异质性预期）。I² 只用于**报告**异质性程度，不作为事后切换模型的依据
- Subgroup Analysis（预先指定的亚组变量 + 理由；事后亚组须标注 post hoc）
- Sensitivity Analysis（逐一排除法 / 只保留低偏倚风险研究）
- Publication Bias（≥10 项研究时 Funnel plot + Egger's test；<10 项时说明不做检验的原因）
- Software（R `meta` / `metafor`、RevMan、Stata `metan`，写明版本）

## Results 增加

- **Forest Plot（必须）** — 主要结局，含各研究权重、合并效应与 95% CI
- Heterogeneity（I², p, τ², 预测区间）
- Subgroup Forest Plots（含亚组间交互检验 p 值）
- **Funnel Plot** — 发表偏倚（如适用）
- Sensitivity Analysis Results
- GRADE Evidence Table（Summary of Findings，推荐）

## 报告规范

PRISMA 2020；观察性研究 Meta 分析加 MOOSE；诊断准确性 Meta 分析加 PRISMA-DTA。

---

# D2. Network Meta-Analysis (NMA)

**在 Meta-Analysis 基础上，增加网络结构和间接比较。**

## 与标准 MA 的关键差异

| 维度 | 标准 Meta-Analysis | 网络 Meta-Analysis |
|------|-------------------|-------------------|
| 比较 | 两两直接比较（A vs B） | 多干预网络（A vs B vs C vs D） |
| 数据 | 直接证据 | 直接 + 间接证据 |
| 核心图表 | Forest plot | **Network plot** + Forest plot + **League table** |
| 排序 | 无 | **SUCRA / P-score / Mean rank** |
| 一致性 | N/A | **全局一致性 + 局部一致性检验** |
| 模型 | 频率学派为主 | 频率学派（netmeta）或贝叶斯（gemtc/JAGS） |
| 报告规范 | PRISMA 2020 | **PRISMA-NMA extension** |

## Methods 增加

- Network Geometry（节点数、边数、连通性）
- Statistical Model（频率学派 R `netmeta` vs 贝叶斯 R `gemtc` / JAGS / OpenBUGS + 选择理由）
- Transitivity Assumption（可传递性假设评估——NMA 的核心假设：各比较的研究人群/干预/时间可比）
- Consistency Assessment（全局 Design-by-Treatment + 局部 Node-Splitting）
- Ranking（SUCRA / P-score / Mean rank）
- Comparison-Adjusted Funnel Plot（发表偏倚）

## Results 增加

- **Network Plot（必须）** — 节点大小 = 样本量，边粗细 = 研究数量
- **League Table（必须）** — 所有两两比较的效应量矩阵
- Consistency Results（全局 + 局部）
- **SUCRA / Rankogram** — 干预排序
- Comparison-Adjusted Funnel Plot
- 如有不一致 → Sensitivity analysis excluding inconsistent loops

## NMA 特有的 Common Mistakes

| 想法 | 现实 |
|------|------|
| "有间接证据就能做 NMA" | 必须评估可传递性假设 |
| "不一致可以忽略" | 统计一致性 + 临床一致性都必须检验并报告 |
| "SUCRA 最高就是最好" | SUCRA 接近时排序不可靠，必须看 CrI 重叠 |
| "用 PRISMA 2020 就行" | 必须用 PRISMA-NMA extension |
