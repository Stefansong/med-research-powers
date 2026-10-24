---
name: research-ethics
description: Use when checking ethical compliance of research involving human subjects, animals, or patient data. Triggers on "伦理"、"IRB"、"知情同意"、"数据隐私"、"IACUC"、"利益冲突"、"人类遗传资源"、"数据出境"、"临床试验注册".
---

# Research Ethics

## Overview

伦理与注册必须在收集任何数据之前完成。本 skill 在流水线中位于 `study-design`（protocol 确认）之后、`journal-selection` 与数据收集之前，由 `study-design` 自动调用；投稿前 `pre-submission-verification` Gate 5 再读取本 skill 的产物复核。涉及人体数据时主动提醒用户，缺项以提醒形式告知，不替用户编造批准信息。

> 总调度规则（直接调用本 skill 也适用，原文见 `${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/SKILL.md`）：**缺前置产物**——说缺什么，light / auto 下先往下做并记缺口，不拒绝；**checkpoint_mode** 默认 light，只在 3 个硬确认处等；**只要一个产物**时交付后停下。

## When to Use

- `study-design` 的 Hard Checkpoint 通过后自动进入（执行 Step 1-2，再视情况完成 Step 3-4）
- 涉及人体研究、患者数据、知情同意、动物实验、数据隐私、中国人类遗传资源、研究注册
- `pre-submission-verification` Gate 5 复核伦理声明
- 用户直接问伦理、IRB、知情同意、数据出境等问题

## When NOT to Use

- 纯计算/模拟研究，不涉及人体、动物或患者数据
- 只想改伦理声明里的一句措辞 → 直接改

## Workflow

### Step 1: 判断适用范围

读取 `study-protocol.md` 的 `type:` 与"伦理与注册"章节，确认研究是否涉及：人体/患者数据、动物实验、数据隐私、中国人类遗传资源（生物样本、基因数据、国际合作、出境）、需要注册的设计（干预性试验、系统综述、诊断/预测模型）。全部不涉及 → 见 When NOT to Use；否则继续。

### Step 2: 加载并逐条核对 checklist

加载 `references/ethics-checklist.yaml`，逐条核对 6 个章节：
1. 伦理审查（IRB / EC）——含二次使用数据是否在批准范围、《涉及人的生命科学和医学研究伦理审查办法》(2023) 的审查类别、免除审查的前提（不涉及敏感个人信息等）与书面依据
2. 动物实验伦理（IACUC）
3. 知情同意（含回顾性豁免——条件须同时满足，去标识化本身不是理由；特殊群体、AI 训练用途）
4. 数据隐私与数据治理——去标识化 ≠ 匿名化；个人信息保护法（医疗健康信息是敏感个人信息、单独同意、委托处理协议、个人信息保护影响评估、数据出境的安全评估 / 标准合同 / 认证与 2024 年跨境流动规定的门槛）；《人类遗传资源管理条例》（样本/基因数据、国际合作、向境外提供）；GDPR / HIPAA；外部 AI 服务的使用条件
5. 研究注册（含中国研究者发起的临床研究在国家医学研究登记备案信息系统的上传）
6. 利益冲突与数据共享

每条标记状态（已满足 / 缺失 / N/A 并说明原因）。涉及人体取 1/3/4/5/6，涉及动物取 2（含临床样本时再加 1/3/4），公开数据集仍需确认原始数据的伦理批准与许可覆盖本研究用途。

由 `study-design` 自动调用时：Step 1-2 必做；批准号（或免除审查的书面认定）、注册号尚未取得的写"待办 + 预计时间"，不阻断进入 `journal-selection`，但数据收集前必须补齐。

### Step 3: 撰写 Methods 伦理声明

用 `references/ethics-checklist.yaml` 的 `methods_statement_template` 生成伦理声明，填入真实批准号（或免除审查的认定依据与文件编号/日期）、知情同意/豁免表述、（如适用）人类遗传资源审批/备案号与注册号。没有真实编号时留 `[待补：xxx]`，绝不编造。

### Step 4: 生成输出、提醒并记录状态

汇总核对结果生成 `ethics-statement.md`（见 Output）。缺失项以**提醒**形式列出（不阻断流程），输出 3-5 行摘要，然后更新 `.mrp-state.json`（`${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py`：`completed_skills` 追加 research-ethics，登记 `ethics-statement.md`，`next_step` 设为 journal-selection）。

## Output

生成 `ethics-statement.md`，包含：
- 6 章节逐条核对状态（已满足 / 缺失 / N/A）
- 伦理审批号或免除审查的书面依据，知情同意/豁免状态（豁免写明满足的每一项条件）；人类遗传资源审批/备案状态（如适用）
- 数据隐私与数据治理合规结论（去标识化还是匿名化、敏感个人信息的处理依据、个人信息保护影响评估、出境途径、外部 AI 服务是否使用及其依据）
- 研究注册状态（平台 + 号 / 待办；中国 IIT 的登记备案状态）
- 利益冲突、资金来源、数据与代码共享声明
- **可直接粘贴进论文 Methods 的伦理声明段落**（`manuscript-writing` 写 Methods 时引用；`pre-submission-verification` Gate 5 据此复核）
- 缺失项清单（标注"数据收集前必须补齐"或"投稿前补齐"）

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "回顾性研究不需要伦理" | 需要伦理审查，或有书面依据的免除审查（只限不涉及敏感个人信息等情形，如匿名化数据） |
| "伦理批准号以后再补" | 事后补办多数机构不接受；必须在数据收集前完成 |
| "原来的批件可以拿来训练 AI" | 二次使用必须在原批准范围内，否则需修正案或新申请 |
| "数据已经脱敏了没问题" | 去标识化（脱敏）后仍是个人信息，医疗数据还是敏感个人信息；只有匿名化后才不是。基因数据/生物样本还涉及人类遗传资源管理 |
| "数据去标识化了，所以可以免除知情同意" | 免除知情同意的条件须同时满足（不豁免无法开展、社会价值、风险不超过最小风险等），去标识化只是保护措施 |
| "把患者数据传给 AI 分析" | 去标识化的患者级数据也不能直接发给外部 AI 服务（包括本插件所在的 AI 会话）：默认只发匿名化数据或汇总结果，否则须满足 checklist §4 的全部条件；服务器在境外还要走出境程序 |
| "利益冲突就写'无'" | 必须认真评估并如实声明 |

## Convergence

当以下条件全部满足时完成：
1. 伦理审查状态已确认（批准号或免除审查的书面依据，或明确的待办与时间）
2. 知情同意状况已明确
3. 数据隐私与数据治理合规已检查（含敏感个人信息、出境、外部 AI 服务、人类遗传资源，如适用）
4. 研究注册状态已确认（或说明不需要）
5. 利益冲突声明已准备
6. 伦理声明段落已生成（写入 `ethics-statement.md`，`manuscript-writing` 会引用）
7. `.mrp-state.json` 已更新

## Red Flags — STOP

- 没有伦理批准就要开始收集数据 → **提醒**必须先取得批准，或有书面依据的免除审查（免除知情同意不能代替二者；不阻断当前对话，但明确写进缺失项）
- 要把患者级数据（含去标识化 / 假名化数据）发给外部 AI 服务、境外服务器，或让 AI 直接读取患者级数据文件 → STOP：默认只用匿名化数据或汇总结果；否则先确认 checklist §4 的条件全部满足（合法性基础、委托处理协议、个人信息保护影响评估、出境程序、数据持有方书面许可且伦理批准的方案写明此用途），缺一条就改在本地分析
- 涉及中国人类遗传资源的国际合作或数据出境未办审批/备案 → 提醒，属于法定要求
- **禁止编造伦理审查批准信息** → 绝不虚构批准号、委员会名称、注册号

## 衔接规则

### 强制衔接（不可跳过）
- `study-design` Hard Checkpoint 通过后 → 自动进入本 skill（Step 1-2），产物 `ethics-statement.md`
- 完成后 → `journal-selection`（暂定目标期刊）→ `data-analysis-planning`
- `pre-submission-verification` Gate 5 → 读取 `ethics-statement.md` 复核批准号（或免除审查的书面依据）、同意/豁免、利益冲突、资金、数据可用性、注册号与登记备案、数据治理缺失项；失败回到本 skill
- `manuscript-writing` 写 Methods → 引用 `ethics-statement.md` 的声明段落

### 前置依赖（缺了按总调度"缺前置产物时"处理）
- 有已确认的 `study-protocol.md`（`type:` 与"伦理与注册"章节）；用户单独咨询伦理问题时可不依赖 protocol，但要先问清研究类型与数据来源

### 可选衔接
- 需把伦理声明并入投稿材料 → `submission-preparation`
- 临床试验/系统综述未注册 → 提醒在数据收集/数据提取前完成注册（ClinicalTrials.gov / ChiCTR / PROSPERO；范围综述 PROSPERO 不接受，注册到 OSF Registries 等）；中国医疗卫生机构的研究者发起的临床研究 → 另提醒立项审核通过时在国家医学研究登记备案信息系统上传
- 动物实验 → protocol 按 ARRIVE 2.0 写，投稿前 `reporting-standards` 检查
