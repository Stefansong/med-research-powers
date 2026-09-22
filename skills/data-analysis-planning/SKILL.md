---
name: data-analysis-planning
description: Use when no analysis-plan.md exists yet and a statistical analysis plan must be written before any analysis（没有分析计划时先制定）. Triggers on "帮我分析数据"、"用什么统计方法"、"分析策略"、"SAP"、"分析计划".
---

# Data Analysis Planning

## Overview

先写分析计划再跑分析——如同 TDD 先写测试再写代码。防止 p-hacking 和事后假设。产物 `analysis-plan.md` 是流水线的**硬确认 2**：用户明确同意后才能进入数据收集与分析。

## When to Use

- 研究方案（`study-protocol.md`）已确认，要在收集/分析数据之前定统计方法
- 用户说"帮我分析数据"但项目里还没有 `analysis-plan.md`
- 审稿人要求补充 SAP

## When NOT to Use

- 已有 `analysis-plan.md`，要执行分析 → `statistical-analysis`
- 还没有研究方案 → `study-design`（SAP 里的结局、变量、样本量都来自 protocol）
- 还没有明确的研究问题 → `research-question-formulation`

## Workflow

### Step 0: 读取用户偏好与前置产物

1. 读取 `~/.claude/mrp-user-profile.json` 的 `preferences.preferred_stats_tool`（Python / R / SPSS / Stata）。没有该字段 → 只问这一个问题（"统计分析主要用 Python、R 还是 SPSS/Stata？"），并问是否保存到该文件供以后使用。SAP 里的代码模板按此语言写。
2. 读取 `study-protocol.md`：研究类型（Type A–E）、主要/次要结局、变量、样本量与先验效应量、分组与分层因素。
3. 若有 `journal-selection-report.md`（暂定期刊），记下其统计报告要求（如强制 CI、禁止基线 p 值）。

### Step 1: 生成 `analysis-plan.md`（7 个部分）

#### 1. 数据概览
数据来源、采集时间、样本量（protocol 预期 vs 实际可得）、变量清单及类型、患者/样本层级关系（一个患者多条记录时必须写明）。

#### 2. 数据预处理
- **缺失值**：按 `references/stat-method-decision-tree.yaml` 的 `missing_data`（比例 × 机制二维表，**规则只在 yaml 维护**）预先写明：每个关键变量的预期缺失比例、机制判断方法、处理策略、Rubin 合并、MNAR 敏感性分析。
- **异常值**：检测方法（IQR / Z-score / 临床合理范围）+ 处理策略（保留并标注 / Winsorize / 移除并做敏感性分析）——策略在这里定，`statistical-analysis` 只执行。
- 数据转换、变量重编码规则、派生变量定义。

#### 3. 描述性统计
- 连续变量：均值±SD（正态）或中位数(IQR)（非正态）；分类变量：频数(%)
- 组间基线比较：RCT 用 SMD 不做 p 值检验；观察性研究可报 p 值或 SMD

#### 4. 主要分析
为每个研究目标明确：统计方法、前提假设及验证方式（正态性 / 方差齐性 / 配对差值 / 比例风险 / 球形性）、前提不满足时的备选方法、效应量指标 + 95% CI、协变量与调整策略。

方法选择 → 加载 `references/stat-method-decision-tree.yaml`（两组连续变量先分配对/独立：配对看差值正态性，独立先正态性再方差齐性；两组 × 有序结局用 Mann-Whitney / CMH；有序分组 × 二分类结局才用 Cochran-Armitage）。前提检验统一用 `${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/assumption_tests.py`。

#### 5. 次要分析和亚组分析
预先指定的亚组及其合理性说明、交互效应检验（报告交互 p 值，不只报亚组内 p 值）、亚组数 >3 时的校正。

#### 6. 敏感性分析
至少一种替代方法、缺失数据敏感性（完整病例 vs 插补；MNAR tipping point）、异常值影响、（观察性研究）未测混杂 E-value。

#### 7. 多重比较策略
- 主要结局：不校正（单一主要结局）
- 多个次要结局：Bonferroni / Holm / FDR
- 组学数据：BH-FDR；置换检验 ≥1000 次、bootstrap ≥2000 次（yaml `resampling`）

组学研究 → 参考 `references/omics-methods.md`（非靶向/靶向代谢组学、蛋白质组学、转录组学/基因组学、多组学整合）。

### Step 2: AI/ML 研究追加第 8–16 部分

研究类型为 AI/ML（study-design Type C）时，SAP 追加 9 个部分，内容要求见 `references/ai-ml-sap-extension.md`：

8 模型架构选择 · 9 训练策略（超参可复现） · 10 数据划分方案 · 11 数据增强策略 · 12 类别不平衡处理 · 13 消融实验 · 14 模型比较统计检验 · 15 模型可解释性方案 · 16 不确定性量化

三条硬规则（其余见 reference）：
- 数据划分表只在 `references/stat-method-decision-tree.yaml` 的 `deep_learning_training.data_split` 维护，SAP 引用并写明所选档位；**必须按患者 ID 划分**，报告随机种子与各集合类别分布
- 评估指标、数据划分、Ground Truth 定义必须与 Type C `study-protocol.md` 一致；新增指标标记 post-hoc / exploratory
- 不能只报点估计：每个指标 95% CI + 比较检验（DeLong / McNemar / bootstrap / 置换）

### Step 3: 硬确认 2

把 `analysis-plan.md` 的关键锁定项列给用户（主要结局及其分析方法、亚组清单、缺失/异常值策略、多重比较策略、AI 研究的数据划分与指标），**等用户明确同意**后在文件头写 `status: confirmed` 与日期。用户说"一直做到底"时不等待，但仍把锁定内容写进文件。

### Step 4: 更新项目状态

输出 3–5 行摘要，然后更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：`completed_skills` 追加 data-analysis-planning、`artifacts` 登记 `analysis-plan.md`、`next_step` 设为 data-collection-tools），进入 `data-collection-tools`。

## Output

唯一交付物：`analysis-plan.md`（即 SAP, Statistical Analysis Plan）。

- 临床/基础/调查研究：第 1–7 部分
- AI/ML 研究：第 1–16 部分（第 8–16 部分按 `references/ai-ml-sap-extension.md`）
- 文件头：`status: draft | confirmed`、确认日期、对应的 `study-protocol.md` 版本、所用统计工具（来自 preferred_stats_tool）
- 定稿后的任何偏差由 `statistical-analysis` 记录在 `analysis-log.md` 并说明理由

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "分析很简单不需要计划" | 无计划 = p-hacking 的温床 |
| "先看看数据再决定方法" | 看了数据再选方法 = 事后假设 |
| "只分析主要结局就行" | 必须预先指定所有计划分析 |
| "缺失数据直接删掉" | 必须按比例 + 机制选策略（yaml `missing_data`）并预先写明 |
| "两组比较先看方差齐不齐" | 先分配对/独立：配对只看差值正态性，根本不做方差齐性 |
| "有序结局用趋势检验" | 两组 × 有序结局是 Mann-Whitney/CMH；Cochran-Armitage 是有序分组 × 二分类结局 |
| "不需要敏感性分析" | 审稿人一定会要求 |

## Convergence

当以下条件全部满足时完成：
1. 每个统计方法的前提假设与备选方法已列出
2. 多重比较校正策略已确定
3. 缺失数据与异常值处理策略已明确（引用 yaml 规则并写明所选项）
4. 敏感性分析已规划
5. AI/ML 研究：第 8–16 部分齐全，指标与 protocol 一致
6. `analysis-plan.md` 已生成并经用户确认（硬确认 2），`.mrp-state.json` 已更新

## Red Flags — STOP

- **禁止在查看数据/结果后再选择统计方法或假设**（事后假设 = HARKing）
- **禁止在执行分析后修改主要结局或主要分析方法**（偏差须记录在 `analysis-log.md`）
- **禁止反复尝试多种方法只报告"显著"的那个**（p-hacking）
- **禁止把未预先指定的亚组分析当作确证性结论**（必须标记 exploratory）
- **AI/ML：禁止用测试集调参或在测试集上做数据增强**（数据泄漏）
- **AI/ML：禁止只报告点估计**（必须有 95% CI 和统计检验）
- 没有 `study-protocol.md` 就写 SAP → 停，先 `study-design`

## 衔接规则

### 前置依赖（不满足则阻止）
- **必须**有已确认的 `study-protocol.md`（`study-design`，硬确认 1）
- **必须**已完成 `research-ethics`（伦理/注册在收集数据之前）
- **推荐**有 `journal-selection-report.md`（暂定期刊的统计报告要求，软确认，可随时更换）

### 强制衔接（不可跳过）
- `analysis-plan.md` 经硬确认 2 后 → `data-collection-tools`（按 SAP 的变量名与数据格式生成收集工具）
- 数据收集完成后 → `statistical-analysis` 按本计划执行
- 最后一步固定为更新 `.mrp-state.json`（Step 4）

### 可选衔接
- 组学数据 → `references/omics-methods.md`
- AI/ML → `references/ai-ml-sap-extension.md`；报告规范逐条清单 → `reporting-standards`
- 审稿阶段补充分析（`revision-response`）→ 回到本 skill 增补 SAP 并标注 post-hoc
