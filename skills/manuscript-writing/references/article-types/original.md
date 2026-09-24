# A. Original Research — IMRaD

> **章节结构是期刊的通用要求；内容必须来自本项目的实际产物，不写套话；缺少的数据写 `[待补：来源]` 占位，不编造。**

> 由 `manuscript-writing` SKILL.md 的 Article Type Router 按需加载。适用：有自己的数据/实验结果的原始研究（RCT、队列、病例对照、诊断准确性、预测模型、AI 研究、基础研究等）。

## 前置依赖（按章节）

| 章节 | 前置文件 | 必须/推荐 |
|------|---------|----------|
| Methods | `study-protocol.md` + `analysis-plan.md` | 必须 |
| Introduction | `research-question.md` + `literature-synthesis-summary.md` | 必须 |
| Results | `results-summary.md` + 图表文件（`figure-generation` 产物） | 必须 |
| Discussion | Results 章节已完成 | 必须 |
| Abstract | 全文各章节已完成 | 必须 |
| Title | Abstract 已完成 | 推荐 |

**可以在没有 `results-summary.md` 的情况下先写 Methods 和 Introduction。** 缺其他必须项时按 SKILL.md Step 1 处理（告知用户、给选择，先写时缺的内容写 `[待补：来源]`）。分析完成后，按 `analysis-log.md` 回头补写 Methods 中与 SAP 的偏离。

## 写作顺序（按效率，不按论文顺序）

1. **Methods** — 最客观，最容易写
2. **Results** — 基于已有分析结果
3. **Introduction** — 此时更清楚 gap 在哪
4. **Discussion** — 需要最多思考
5. **Abstract** — 概括已完成全文
6. **Title** — 精炼到一句话
7. **期刊特殊元素** — Key Points（JAMA 家族）/ Research in Context（Lancet 家族）/ Patient Summary（European Urology 家族），以模板 `special` 字段为准

## 章节规则

**Methods**：研究设计、参与者（纳入/排除、时间地点）、变量定义、统计方法（可复现程度：软件与版本、模型、缺失数据处理）、样本量依据、伦理批准与知情同意声明、试验/研究注册号（如适用）。与 `study-protocol.md` / `analysis-plan.md` 不一致处必须说明原因并标注"与预注册分析计划的偏离"——逐条对应 `analysis-log.md` 的偏离表，每条都写在 Methods（改了什么、为什么；Gate 2 查这里），对结论可能有影响的再在 Limitations 讨论，不能略去或只放补充材料。

**Results**：参与者流程图 → 基线表 → 主要结局 → 次要结局 → 亚组/敏感性分析。**禁止**在 Results 讨论意义；每个数字都必须能在 `results-summary.md` 或分析输出里找到出处，**禁止**出现找不到出处的数字。效应量必须带 95% CI。

**Introduction**：漏斗形（背景 → 已知 → gap → 本研究目的），通常 3–4 段，最后一句明确研究目的/假设。

**Discussion**：主要发现 → 与文献比较 → 机制/解释 → 临床意义 → 局限性（诚实、具体）→ 结论。**禁止**引入 Results 中没有的数据。

**Abstract**：结构化小标题与字数**以目标期刊模板为准**（`get_journal_template.py` 输出的 `abstract` 字段），常见为 Background/Methods/Results/Conclusions；JAMA 家族为 7 段式（Importance … Conclusions and Relevance）；Lancet 家族含 Funding。

**Title**：含研究设计类型 + 关键变量 + 人群，≤20 词；RCT 标题含 "randomized"（CONSORT 要求）。

## Output Structure

```
manuscript/
├── title-page.md
├── abstract.md
├── introduction.md
├── methods.md
├── results.md
├── discussion.md
├── references.md
├── supplementary.md            ← 可选
├── figure-legends.md           ← 可选（figure-generation 产物）
├── key-points.md               ← JAMA 家族必须（Question / Findings / Meaning，≤100 词）
└── research-in-context.md      ← Lancet 家族必须（Evidence before this study / Added value / Implications）
```

文件名与 `manuscript-export` 的 section id 一一对应（`key-points` / `research-in-context`），导出脚本按期刊 `family` 决定是否纳入及顺序。

## 报告规范

按研究类型选择并在写作时对照：CONSORT 2025（RCT，30 项，含子项共 42 行）/ STROBE（观察性）/ STARD 2015（诊断准确性）/ TRIPOD+AI（预测模型）/ CLAIM 2024（影像 AI，44 项）/ ARRIVE 2.0（动物）。完整清单由 `reporting-standards` skill 提供。
