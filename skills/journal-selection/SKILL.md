---
name: journal-selection
description: Use when a manuscript is nearing completion and the user needs to choose a target journal. Triggers on "投哪个期刊"、"选刊"、"journal selection"、"impact factor"、"哪个杂志合适"、"投稿目标". Also auto-triggers when study-design completes (early selection recommended).
---

# Journal Selection

## Overview

选对期刊是投稿成功的第一步。投错期刊 = desk reject + 浪费 2-6 个月。在研究设计阶段就应初步确定目标期刊，写作阶段按期刊要求调整。

## When to Use

- 用户完成 study-design 后 → **建议触发**（早期选刊，指导后续写作格式）
- 用户完成 manuscript-writing 后 → **强制触发**（最终确认投稿目标）
- 用户问"投哪个期刊"、"影响因子多少"、"这篇论文能投几分"

## When NOT to Use

- 研究问题尚未明确 → 先 `research-question-formulation`
- 纯写作格式问题（已知目标期刊）→ `manuscript-writing`

## Workflow: 4-Step Journal Matching

### Step 1: 研究画像分析

从已有的 `research-question.md` 和论文草稿中提取：
- **研究类型**：RCT / 队列 / AI / 基础 / 综述 / 病例报告
- **学科领域**：主学科 + 交叉学科
- **创新程度**：颠覆性发现 / 增量改进 / 方法创新 / 验证性研究
- **样本量级别**：大规模（>1000）/ 中等（100-1000）/ 小样本（<100）
- **临床可转化性**：直接改变实践 / 间接影响 / 基础机制

### Step 2: 期刊匹配评分

为每个候选期刊评估 5 个维度（每项 1-5 分）：

| 维度 | 评估内容 |
|------|---------|
| **Scope Match** | 期刊的 Aims & Scope 是否涵盖本研究主题 |
| **Impact Match** | 论文质量是否匹配期刊的 Impact Factor 和接收标准 |
| **Audience Match** | 期刊读者是否是本研究的目标受众 |
| **Format Match** | 论文类型（original article / letter / brief communication）是否被接受 |
| **Timeline Match** | 期刊审稿速度是否满足时间需求（毕业/基金结题/抢发） |

**总分 = Scope×3 + Impact×2 + Audience×2 + Format×1 + Timeline×1**（加权 25 分满分）

### Step 3: 期刊推荐排序

生成 3 梯队推荐：

| 梯队 | 策略 | 匹配分 |
|------|------|--------|
| **Tier 1: Reach** | 冲刺高影响因子期刊 | ≥20 |
| **Tier 2: Target** | 最匹配的期刊（推荐首投） | ≥16 |
| **Tier 3: Safety** | 接收率高、审稿快的期刊 | ≥12 |

每个梯队推荐 1-2 个期刊，共 3-6 个候选。

### Step 4: 投稿规格提取

为 Top 3 期刊分别提取：

- [ ] 字数限制（正文 / 摘要 / Running title）
- [ ] 参考文献上限和格式（Vancouver / APA / 期刊自定义）
- [ ] 图表数量限制
- [ ] 结构化摘要 vs 非结构化
- [ ] Supplementary materials 政策
- [ ] Open access 选项和费用（APC）
- [ ] 投稿系统类型（ScholarOne / EditorialManager / 其他）
- [ ] 是否需要临床试验注册号
- [ ] 是否要求 Data availability statement
- [ ] 是否要求 ORCID
- [ ] 特殊要求（如 Nature Medicine 要求 Reporting Summary）

### Step 4b: Unknown Journal Auto-Collection（未知期刊信息自动采集）

当推荐的期刊不在 `journal-templates.yaml` 模板库中时（如新创刊期刊），执行以下自动采集流程：

```
1. WebSearch("[期刊名] instructions for authors submission guidelines")
   → 定位期刊的 "Instructions for Authors" / "Guide for Authors" 页面

2. WebFetch(URL) 或从搜索结果提取以下关键字段:
   → journal: [全名]
   → publisher: [出版社]
   → IF_approx: [影响因子，如新刊则标注"新刊"]
   → word_limit: [字数限制]
   → abstract: [结构化/非结构化, 字数限制]
   → references: [上限, 格式]
   → figures: [数量限制]
   → tables: [数量限制]
   → sections: [章节要求和顺序]
   → special: [特殊要求列表]
   → system: [投稿系统名称]
   → apc: [OA 费用]
   → review_time: [平均审稿周期]

3. 将采集结果格式化为 YAML 条目:
   - id: [kebab-case-id]
     journal: [全名]
     publisher: [出版社]
     IF_approx: [IF]
     word_limit: [限制]
     ...

4. 追加到 journal-templates.yaml（如用户同意永久保存）
   或仅在当前项目的 journal-selection-report.md 中记录（临时使用）

5. 向用户确认采集的信息是否准确
```

**触发条件:** 在 Step 2-3 评分过程中，如果候选期刊的 ID 不在 `journal-templates.yaml` 中，自动触发 Step 4b。

**采集失败处理:**
- 如 WebSearch 无法找到 Instructions for Authors → 标记为"需手动查阅"
- 如信息不完整 → 填入已获取的字段，缺失字段标注 "[未确认]"
- 向用户报告哪些字段需要手动确认

## Output

生成 `journal-selection-report.md`：

```markdown
# Journal Selection Report

**Research:** [标题]
**Date:** [日期]
**Research Type:** [RCT/Cohort/AI/...]

## Research Profile
- Innovation level: [颠覆性/增量/验证性]
- Sample size: [n=X]
- Clinical translatability: [高/中/低]

## Recommended Journals

### Tier 1 — Reach
| Journal | IF | Acceptance Rate | Review Time | Score |
|---------|---:|----------------:|------------:|------:|
| [期刊1] | X.X | ~X% | X months | XX/25 |

### Tier 2 — Target (recommended first submission)
| Journal | IF | Acceptance Rate | Review Time | Score |
|---------|---:|----------------:|------------:|------:|
| [期刊2] | X.X | ~X% | X months | XX/25 |

### Tier 3 — Safety
| Journal | IF | Acceptance Rate | Review Time | Score |
|---------|---:|----------------:|------------:|------:|
| [期刊3] | X.X | ~X% | X months | XX/25 |

## Submission Specs (Top 3)

### [期刊名]
- Word limit: X
- Abstract: structured / unstructured, ≤X words
- References: ≤X, Vancouver format
- Figures: ≤X, 300 DPI
- System: ScholarOne / EditorialManager
- APC: $X (OA) / $0 (subscription)

## Cascade Strategy
If rejected by Tier 2 → reformat for [Tier 3 期刊]
Key changes needed: [字数/格式/重点调整]
```

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "先投 Nature/Lancet 试试" | 浪费 3-6 个月，除非创新程度真的够 |
| "影响因子越高越好" | Scope 不匹配的高 IF 期刊 = 100% desk reject |
| "写完再选期刊" | 应该设计阶段就初选，按目标期刊格式写作 |
| "这个领域没有好期刊" | 几乎所有领域都有 Q1 期刊，需要扩展搜索 |
| "投中文期刊容易" | 部分中文 SCI 期刊的接收率比同级别英文期刊更低 |
| "开放获取都是水刊" | Nature Communications、PLOS Medicine 都是 OA 顶刊 |

## Convergence

当以下条件满足时完成：
1. 至少 3 个候选期刊已评分排序
2. Top 1 期刊的投稿规格已完整提取
3. 用户确认目标期刊
4. Cascade 策略已制定（被拒后改投方案）

## Red Flags — STOP

- 用户选择的期刊 Scope 完全不匹配 → 警告，建议替代
- 论文质量与期刊 IF 差距过大（>3 分 IF 差距）→ 建议降梯队
- 掠夺性期刊（predatory journal）→ 强烈警告，推荐 Beall's List 检查

## 衔接规则

### 前置依赖
- **推荐**已有 `research-question.md`（至少明确研究类型和领域）
- **推荐**已有论文初稿或 study-design 完成

### 强制衔接
- 完成后 → 将期刊规格传递给 `manuscript-writing`（格式适配）
- 完成后 → 将期刊规格传递给 `pre-submission-verification` Gate 6（形式检查）

### 被动触发
- `study-design` 完成后 → 建议触发（早期选刊）
- `manuscript-writing` 完成后 → 建议触发（最终确认）
- 用户说"投哪个期刊" → 自动触发

### 可选衔接
- 被拒后 → 触发 `submission-preparation`（改写 Cover Letter 适配新期刊）
