---
name: journal-selection
description: Use when choosing or re-checking a target journal (tentative after study design, re-checked before writing). Triggers on "投哪个期刊"、"选刊"、"journal selection"、"impact factor"、"哪个杂志合适".
---

# Journal Selection

## Overview

选对期刊是投稿成功的第一步。投错期刊 = desk reject + 浪费 2–6 个月。研究设计阶段就**暂定**目标期刊（按其格式写作），写作前和投稿前各复核一次——目标期刊是**软确认**，随时可以换，不锁定流程。

## When to Use

- `study-design`（硬确认 `study-protocol.md`）与 `research-ethics` 之后 → 暂定目标期刊（软确认）
- `manuscript-writing` 开始前 → 复核一次目标期刊是否仍合适（软确认）
- 被拒后改投 → 重新选刊
- 用户问"投哪个期刊"、"影响因子多少"、"这篇论文能投几分"

## When NOT to Use

- 研究问题尚未明确 → 先 `research-question-formulation`
- 已知目标期刊、只问格式 → `manuscript-writing`（用 `get_journal_template.py` 取模板）
- 写 cover letter / 投稿清单 → `submission-preparation`

## Workflow

### Step 0：读取用户画像（懒采集）

读取 `~/.claude/mrp-user-profile.json` 的 `preferences.favorite_journals`。文件或字段不存在 → 只问这一个问题（"你常投的期刊有哪些？"），并问是否保存；用户跳过则不保存。`favorite_journals` 只作为候选来源之一，仍要走 Step 2 评分，不能因为"常投"就直接推荐。

### Step 1：研究画像分析

从 `research-question.md`、`study-protocol.md` 和论文草稿中提取：
- **研究类型**：RCT / 队列 / 诊断准确性 / 预测模型 / AI / 基础 / 综述 / 病例报告
- **学科领域**：主学科 + 交叉学科（决定候选期刊池与 JCR 学科类别）
- **创新程度**：颠覆性发现 / 增量改进 / 方法创新 / 验证性研究
- **样本量级别**：大规模（>1000）/ 中等（100–1000）/ 小样本（<100）；是否有外部验证
- **临床可转化性**：直接改变实践 / 间接影响 / 基础机制
- **时间需求**：毕业 / 结题 / 抢发 → 决定对审稿周期的要求

据此给出**论文水平档位**（用于 Step 3 分梯队）：

| 档位 | 典型特征 | 对应期刊层级 |
|------|---------|-------------|
| A | 多中心 / 外部验证 / 改变实践的证据 / 方法创新 | 学科 Q1 前半（Top 10%） |
| B | 单中心大样本、设计严谨、增量创新 | 学科 Q1 |
| C | 单中心中等样本、验证性、无外部验证 | 学科 Q2 |
| D | 小样本 / 回顾性 / 探索性 | 学科 Q3–Q4 |

### 数据来源规则（Step 2 之前必读）

- 库内 `IF_approx` 的年份看该条目的 `IF_year`（有则为出版社公布的 JCR 2025/2024 值，来源在 `IF_source`）；没有 `IF_year` 的条目仍是 **JCR 2022** 值；APC 同理看 `apc_year`（规则见库文件顶层 `data_as_of`）。**报告里每个 IF 必须标注 JCR 年份与来源**，如 "IF 29.1 (JCR 2025, sciencedirect.com)"。
- 库内没有分区、接收率、审稿周期、ORCID 要求等字段。**报告前必须用 WebSearch 复核 Top 3 期刊的最新 IF 与 JCR/中科院分区**，并写明年份与来源 URL。
- 无法查到的数据一律写 **N/A**，禁止凭印象填数。

取库内模板一律用脚本（**禁止整读 `journal-templates.yaml`**，3600 多行会被截断）：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/get_journal_template.py --list --specialty urology
python3 ${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/get_journal_template.py --search prostate
python3 ${CLAUDE_PLUGIN_ROOT}/skills/manuscript-writing/scripts/get_journal_template.py --id european-urology
```

### Step 2：期刊匹配评分（过滤用）

为每个候选期刊评估 5 个维度（每项 1–5 分）：

| 维度 | 评估内容 |
|------|---------|
| **Scope Match** | 期刊 Aims & Scope 是否涵盖本研究主题（WebSearch 期刊官网核对） |
| **Impact Match** | 论文水平档位与期刊层级是否相称 |
| **Audience Match** | 期刊读者是否是本研究的目标受众 |
| **Format Match** | 论文类型（original article / brief report / letter）是否被接受、字数是否装得下 |
| **Timeline Match** | 审稿速度是否满足时间需求（有来源才能打高分） |

**总分 = Scope×3 + Impact×2 + Audience×2 + Format×1 + Timeline×1**（满分 45：5×3 + 5×2 + 5×2 + 5×1 + 5×1）

匹配分**只作过滤阈值**，不决定梯队：**总分 ≥ 29/45 且 Scope ≥ 4** 的期刊才能进入候选；Scope ≤ 3 的期刊无论 IF 多高都剔除（scope 不匹配 = desk reject）。

### Step 3：分梯队（按期刊层级相对论文水平）

梯队由期刊的 IF/分区**相对于论文水平档位**决定，不由匹配分高低决定：

| 梯队 | 定义 | 例（论文档位 C = Q2） |
|------|------|---------------------|
| **Reach（冲高）** | 比论文档位高一级的期刊；接收率低、周期长，值得试一次 | Q1 期刊 |
| **Target（推荐首投）** | 与论文档位相当的期刊 | Q2 期刊 |
| **Safe（保底）** | 比论文档位低一级、接收率高、审稿快的期刊 | Q3 期刊 |

每个梯队 1–2 个期刊，共 3–6 个候选；三个梯队都必须先通过 Step 2 的 ≥29 分过滤。同一梯队内按匹配分排序。

### Step 4：投稿规格提取（Top 3）

对 Top 3 期刊各运行一次 `get_journal_template.py --id <id>`，提取：
- [ ] 字数限制（正文 / 摘要）、结构化摘要小标题
- [ ] 参考文献上限和格式
- [ ] 图表数量限制
- [ ] Supplementary 政策、期刊特殊元素（Key Points / Research in Context / Patient Summary / Reporting Summary）
- [ ] 投稿系统（ScholarOne / Editorial Manager / eJournalPress / Snapp 等，库内 `system` 字段）
- [ ] 是否需要试验注册号、Data availability statement
- [ ] APC（库内为 2022 价，标年份；WebSearch 复核最新价，查不到写 N/A）
- [ ] ORCID 是否必须（库内只有部分条目有 `orcid` 字段；无则 WebSearch 期刊官网，查不到写 N/A）

### Step 4b：期刊不在库中（Unknown Journal）

```
1. WebSearch("[期刊名] instructions for authors")
   → 定位 "Instructions for Authors" / "Guide for Authors" 页面
2. WebFetch(URL) 提取：journal, publisher, IF_approx（标年份与来源；新刊写"新刊，无 IF"）,
   word_limit, abstract, references, figures, tables, sections, special, system, apc
3. 写成 YAML 条目并保存到 **项目目录** ./journal-overrides.yaml（与库文件相同结构；
   family 按规则填：名称含 lancet → lancet；jama → jama；nature/npj → nature；ieee → ieee；其余 standard）：
   templates:
     - id: [kebab-case-id]
       journal: [全名]
       publisher: [出版社]
       IF_approx: "[值] (JCR [年份], 来源: [URL])"
       word_limit: ...
       family: standard
   → manuscript-writing / manuscript-export 的脚本会优先读取该文件；不确定的字段写 verify
4. 向用户确认采集的信息；WebSearch 找不到的字段标注 "[未确认]"
```

**不要写入插件安装目录的 `journal-templates.yaml`**——更新插件会丢失。

### Step 5：收尾

1. 生成 `journal-selection-report.md`（模板见 Output）。
2. 输出 3–5 行摘要（Target 首选 + 备选 + 需人工核实的项），默认直接进入下一步；本步是**软确认**，不等待。
3. 更新项目目录 `.mrp-state.json` 的 `target_journal`（`python3 ${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`）；用户同意时把目标期刊写入 `~/.claude/mrp-user-profile.json` 的 `favorite_journals`。
4. 下一步：首次选刊 → `data-analysis-planning`；写作前复核 → `manuscript-writing`；改投 → `submission-preparation`。

## Output

生成 `journal-selection-report.md`：

```markdown
# Journal Selection Report

**Research:** [标题]
**Date:** [日期]
**Research Type:** [RCT/Cohort/AI/...]
**Paper level (Step 1):** [A/B/C/D] → 目标层级 [Q1 top / Q1 / Q2 / Q3–Q4]
**Data sources:** 库内 IF 年份按条目 `IF_year`（无则 JCR 2022，见 journal-templates.yaml data_as_of）；最新 IF/分区/接收率/周期/APC/ORCID 来自 WebSearch，逐项附 URL；查不到写 N/A

## Research Profile
- Innovation level: [颠覆性/增量/验证性]
- Sample size: [n=X]，外部验证 [有/无]
- Clinical translatability: [高/中/低]
- Timeline need: [无/毕业/结题/抢发]

## Recommended Journals
（每行的 IF 必须带 JCR 年份；分区必须带年份与来源；Acceptance / Review time / APC / ORCID 必须附来源 URL，否则写 N/A）

### Reach（比论文档位高一级）
| Journal | IF (JCR yyyy) | Quartile (来源, yyyy) | Score /45 | Acceptance rate (来源) | Review time (来源) | APC (yyyy, 来源) | ORCID (来源) |
|---------|--------------:|-----------------------|----------:|------------------------|--------------------|------------------|--------------|
| [期刊1] | 25 (JCR 2024, URL) | Q1 (JCR 2024, URL) | XX | N/A | ~3 months (URL) | USD 3000 (2025, URL) | required (URL) |

### Target（推荐首投）
| Journal | IF (JCR yyyy) | Quartile (来源, yyyy) | Score /45 | Acceptance rate (来源) | Review time (来源) | APC (yyyy, 来源) | ORCID (来源) |
|---------|--------------:|-----------------------|----------:|------------------------|--------------------|------------------|--------------|

### Safe（保底）
| Journal | IF (JCR yyyy) | Quartile (来源, yyyy) | Score /45 | Acceptance rate (来源) | Review time (来源) | APC (yyyy, 来源) | ORCID (来源) |
|---------|--------------:|-----------------------|----------:|------------------------|--------------------|------------------|--------------|

## Submission Specs (Top 3, from get_journal_template.py + WebSearch)

### [期刊名]（id: [journal-id]）
- Word limit: X；Abstract: structured / unstructured, ≤X words（小标题：…）
- References: ≤X, [format]；Figures: ≤X；Tables: ≤X
- Special: [Key Points / Research in Context / Patient Summary / Reporting Summary …]
- System: [ScholarOne / Editorial Manager / eJournalPress / Snapp]
- APC: [USD X (yyyy, URL)] / subscription (no APC) / N/A
- Registration / Data availability / ORCID: [要求，来源]

## Cascade Strategy
Target 被拒 → 改投 [Safe 期刊]；需要调整：[字数 / 摘要格式 / 特殊元素 / 参考文献上限]
Reach 被拒（有审稿意见）→ 按意见修改后投 Target

## Items to verify manually
- [列出所有写了 N/A 或 "[未确认]" 的项]
```

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "先投 Nature/Lancet 试试" | 浪费 3–6 个月，除非论文档位真的是 A |
| "影响因子越高越好" | Scope 不匹配的高 IF 期刊 = 100% desk reject；Scope ≤3 直接剔除 |
| "库里写的 IF 直接报" | 先看条目 `IF_year`；没有的是 JCR 2022 旧值；报告前必须 WebSearch 复核并标年份与来源 |
| "接收率大概 20% 吧" | 没有来源的数字一律写 N/A，不能编 |
| "写完再选期刊" | 设计阶段就暂定，按目标期刊格式写作；写作前再复核一次 |
| "选定期刊就不能换了" | 目标期刊是软确认，随时可换；只有 protocol / SAP / pre-submission 是硬确认 |
| "这个领域没有好期刊" | 几乎所有领域都有 Q1 期刊，用 `--list --specialty` 扩展搜索 |
| "开放获取都是水刊" | Nature Communications、PLOS Medicine、eClinicalMedicine 都是 OA 顶刊；掠夺性与否看 Think.Check.Submit / DOAJ / COPE |
| "期刊不在库里就补进插件的 YAML" | 写项目目录 `journal-overrides.yaml` |

## Convergence

当以下条件全部满足时完成：
1. 至少 3 个候选期刊已过 ≥29/45 过滤并按梯队排序
2. Top 3 期刊的 IF/分区已 WebSearch 复核并标注年份与来源；查不到的项写 N/A
3. Top 1 期刊的投稿规格已用 `get_journal_template.py` 完整提取
4. 用户暂定目标期刊（软确认，可随时更换）
5. Cascade 策略已制定（被拒后改投方案）
6. `.mrp-state.json` 的 `target_journal` 已更新

## Red Flags — STOP

- 用户选择的期刊 Scope 完全不匹配（Scope ≤ 2）→ 警告，建议替代
- 论文档位对应分区与期刊分区相差 ≥2 级（如 D 档投 Q1），或学科排名百分位相差 >50 个百分点 → 建议降梯队
- 疑似掠夺性期刊 → 强烈警告：按 Think.Check.Submit 清单核对，OA 期刊查 DOAJ 收录，出版社查 COPE 会员，同时确认 PubMed/MEDLINE 或 Web of Science 收录
- 报告里出现没有来源的接收率/审稿周期/APC 数字 → 停，改为 N/A 或补来源

## 衔接规则

### 前置依赖
- **推荐**已有 `research-question.md`（至少明确研究类型和领域）
- **推荐**已有 `study-protocol.md`（硬确认后）；复核时推荐有论文初稿

### 强制衔接（不可跳过）
- 首次选刊（`study-design` → `research-ethics` 之后）→ 生成 `journal-selection-report.md` → `data-analysis-planning`
- `manuscript-writing` 开始前 → 复核一次目标期刊（软确认），期刊规格由 `get_journal_template.py` 传递给写作
- 期刊规格 → `pre-submission-verification` Gate 6（形式检查）与 `manuscript-export`（`--journal <id>`）

### 可选衔接
- 被拒后改投 → 重新分梯队 → `submission-preparation`（改写 cover letter）
- 期刊不在库中 → Step 4b 写 `journal-overrides.yaml`
