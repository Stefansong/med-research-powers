# C. Systematic Review（不含定量合并）

> **章节结构是期刊的通用要求；内容必须来自本项目的实际产物，不写套话；缺少的数据写 `[待补：来源]` 占位，不编造。**

> 由 `manuscript-writing` SKILL.md 的 Article Type Router 按需加载。需要统计合并时改读 `meta.md`（在本文件基础上追加）。

## 前置依赖

| 前置文件 | 必须/推荐 |
|---------|----------|
| 注册信息：PROSPERO 等注册号，**或**明确说明未注册及原因（PRISMA 2020 item 24a 要求报告注册信息，未注册须写明） | 必须 |
| `search-strategy.md` + `screening-log.md`（`literature-synthesis` 产物） | 必须 |
| `literature-references.md`（`literature-synthesis` Systematic 模式产物：逐篇研究类型、样本量、核心发现、偏倚风险） | 必须 |
| PRISMA 2020 Checklist（`reporting-standards` 提供） | 必须 |
| 偏倚风险评估结果（RoB 2 / ROBINS-I / NOS（满分 9）/ QUADAS-2（诊断准确性）/ PROBAST（预测模型）） | 必须 |

## 写作顺序

1. **Methods** — 最客观（检索策略、筛选标准、偏倚评估方法）
2. **Results** — PRISMA 流程图 → 纳入研究特征 → 偏倚评估 → 综合结果
3. **Introduction** — 已有综述的不足 → 本综述的目的（PICO）
4. **Discussion** — 主要发现 → 证据质量 → 局限性 → 启示
5. **Abstract** — 结构化（PRISMA 2020 for Abstracts）
6. **Title** — 必须含 "systematic review"

## 章节规则

**Methods（必须详细，PRISMA 2020 items 3–15）**
- Protocol and Registration（注册号 + 注册平台；未注册则说明）
- Eligibility Criteria（PICO 框架 + 研究类型、语言、年份）
- Information Sources（数据库列表 + 各库最后检索日期）
- Search Strategy（至少一个数据库的完整检索式，其余附 Appendix）
- Study Selection Process（双人独立筛选 + 分歧解决方式；如用自动化工具需说明）
- Data Extraction（提取变量列表、双人/单人 + 核对）
- Risk of Bias Assessment（工具按研究类型：RoB 2 / ROBINS-I / NOS / QUADAS-2 / PROBAST）
- Synthesis Methods（叙述性综合的分组与呈现方式；如做定量合并见 `meta.md`）
- Certainty of Evidence（GRADE，如适用）

**Results**
- Study Selection → **PRISMA 2020 Flow Diagram（必须）**，各环节数字与 `screening-log.md` 一致
- Study Characteristics → 纳入研究汇总表（从 `literature-references.md` 整理）
- Risk of Bias → 汇总图/表
- Synthesis Results → 按结局分组报告；叙述性综合不得用"票数法"（多少研究显著）代替效应方向与大小

**Discussion**：主要发现 → 与已有综述对比 → 证据质量（GRADE）→ 局限性（证据层面 + 综述过程层面）→ 临床/研究启示

**Abstract**：结构化，小标题与字数**以目标期刊模板为准**；须含注册号（或"未注册"）与纳入研究数。

## Output Structure

```
manuscript/
├── title-page.md
├── abstract.md
├── introduction.md
├── methods.md
├── results.md
├── discussion.md
├── conclusion.md
├── references.md
├── supplementary.md            ← 含：完整检索式 / 排除研究清单及理由 / 偏倚评估明细
└── prisma-checklist.md         ← PRISMA 2020（27 项）逐条对应页码
```

## 报告规范

PRISMA 2020（27 项）+ PRISMA 2020 for Abstracts；诊断准确性综述加 PRISMA-DTA；完整清单由 `reporting-standards` 提供。
