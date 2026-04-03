---
name: using-med-research-powers
description: Use when any research-related task is detected. This is the orchestrator — check it before any scientific response. Triggers on any mention of 论文、数据分析、统计、图表、文献、研究设计、伦理、投稿.
---

# Using Med-Research-Powers

## Priority

User instructions (CLAUDE.md) > MRP skills > Default behavior.

## When to Use

Any research-related task. If there is even 1% chance a skill applies, invoke it.

## Core Rule

**Before ANY research-related response, check if a skill applies. 1% Rule: even 1% chance → invoke it.**

## Workflow

```
对话开始时:
  → 检查 .mrp-state.json 是否存在
  → 如存在 → 显示: "上次完成到 [current_stage]，下一步是 [next_steps[0]]。继续？"
  → 如不存在 → 正常路由

User message → Research-related? 
  → YES → Check skill table → Invoke skill → Announce "Using [skill] to [purpose]"
  → NO → Respond directly
```

## Fast-Track Mode（快速模式）

当用户明确表示不需要逐步确认时（如"一直做到最后"、"按你的想法来"、"不用问我"），进入 fast-track 模式：
- **仅在 Hard Checkpoint 暂停**（protocol / SAP / journal / pre-submission）
- **Soft Checkpoint 自动跳过**（文献综述、图表、各章节等）
- 在 `.mrp-user-profile.json` 记录用户偏好

## Checkpoint Protocol（每步完成后的报告与确认）

**每个 skill 执行完成后，必须向用户报告并征求确认，然后再进入下一步。禁止静默跳转。**

### 报告格式

每个 skill 完成时，向用户输出以下结构化报告：

```
────────────────────────────────────────
✅ [Skill 名称] 已完成

📄 生成的文件：
  • [file1.md] — [一句话描述]
  • [file2.py] — [一句话描述]

📊 关键发现/决策：
  • [1-3 条最重要的发现或决策]

⚠️ 需要注意：
  • [如有问题或需要用户判断的事项]

➡️ 建议下一步：[下一个 skill 名称] — [做什么]
────────────────────────────────────────
是否继续？还是需要修改当前步骤的内容？
```

### 确认规则

**用户响应示例：**
- "继续" / "好的" / "下一步" / "OK" → 进入下一个 skill
- "等一下，[变量名]改成[新名]" → 修改后重新报告
- "跳过文献检索" → 记录跳过原因，进入下一步
- "回到研究设计" → 回溯到 study-design
- 不回应但直接说"帮我分析数据" → 按新指令路由，当前步骤视为已确认

| 情况 | 行为 |
|------|------|
| 用户说"继续" / "好" / "下一步" | → 进入建议的下一个 skill |
| 用户说"等一下" / 提出修改 | → 修改当前 skill 的输出，修改后重新报告 |
| 用户说"跳过 [skill]" | → 记录跳过原因，进入再下一个 skill（但不能跳过 pre-submission-verification） |
| 用户说"回到 [skill]" | → 回溯到指定 skill（参考 Pipeline 回溯规则） |
| 用户无响应但给了新指令 | → 按新指令路由，当前 skill 视为已确认 |

### 不可跳过的确认点（Hard Checkpoint）

以下 4 个节点**必须**获得用户明确确认才能继续，不接受"无响应默认通过"：

1. **`study-protocol.md` 确认**（study-design 完成后）
   - 研究类型、主要结局、样本量一旦确认即锁定
   - 主要结局事后更改 = outcome switching = 学术不端
   - protocol 注册后不可大幅更改

2. **`analysis-plan.md` 确认**（data-analysis-planning 完成后）
   - SAP 一旦确认，后续偏差需要记录理由
   - 这是防 p-hacking 的核心机制

3. **`journal-selection-report.md` 确认**（journal-selection 完成后）
   - 目标期刊决定了后续写作格式和投稿规格

4. **`submission-readiness-report.md` 确认**（pre-submission-verification 完成后）
   - 6 个 Gate 全部通过才能投稿
   - 任何 Gate 失败必须返回修复

### Pipeline 完整 Checkpoint 流程

```
research-question-formulation
  └─ 报告: PICO + 假设 → 用户确认 ✓
      │
literature-synthesis
  └─ 报告: 检索结果 + Gap → 用户确认 ✓
      │
study-design / basic / ai
  └─ 报告: 研究方案摘要 → ⚠️ Hard Checkpoint: 用户必须确认研究方案（锁定研究类型+主要结局）
      │
journal-selection
  └─ 报告: 3 梯队推荐 → ⚠️ Hard Checkpoint: 用户必须确认目标期刊
      │
data-analysis-planning
  └─ 报告: SAP 全文 → ⚠️ Hard Checkpoint: 用户必须确认分析计划
      │
data-collection-tools
  └─ 报告: 生成的工具清单 → 用户确认 ✓ → [用户执行数据收集]
      │
statistical-analysis
  └─ 报告: 清洗日志 + 关键结果 + 脚本 → 用户确认 ✓
      │
figure-generation
  └─ 报告: 图表列表 → 用户确认 ✓
      │
manuscript-writing
  └─ 报告: 各章节完成状态 → 用户确认 ✓
      │
manuscript-export
  └─ 报告: .docx 生成 + 格式检查 + 字数统计 → 用户确认 ✓
      │
peer-review-simulation
  └─ 报告: 评分 + Critical 问题列表 → 用户确认 ✓
      │
pre-submission-verification
  └─ 报告: 6-Gate 结果 → ⚠️ Hard Checkpoint: 用户必须确认全部通过
      │
cover-letter-writing
  └─ 报告: Cover Letter 草稿 → 用户确认 ✓
      │
submission-system-guide
  └─ 报告: 投稿 Checklist → 用户确认 ✓
```

## Skill Routing

| Skill | Trigger |
|-------|---------|
| research-question-formulation | 模糊研究想法、需要明确假设 |
| literature-synthesis | 查文献、research gap、综述 |
| study-design | 所有研究设计（临床/基础/AI/定性/调查，内置 type router） |
| journal-selection | 选刊策略、影响因子、投哪个期刊 |
| data-analysis-planning | 制定分析策略 |
| data-collection-tools | 根据 protocol 生成标注表、推理脚本、CRF、数据目录 |
| statistical-analysis | 执行统计分析 |
| figure-generation | 出版级图表 |
| manuscript-writing | 写论文各章节（原始研究 + 5 种综述，内置 type router） |
| manuscript-export | Markdown → .docx 导出、期刊排版、格式检查 |
| reporting-standards | 报告规范检查 |
| peer-review-simulation | 模拟审稿（4 审稿人含 Devil's Advocate + 期刊校准评分） |
| research-ethics | 伦理、隐私、知情同意 |
| **pre-submission-verification** | **论文完成后强制检查（6 Gate 含 PubMed MCP Claim Verification），不通过不能投稿** |
| submission-preparation | Cover Letter 写作 + 投稿系统操作指南 |
| revision-response | 修稿策略 + 逐条回复审稿意见 |
| pubmed-search | PubMed MCP 深度检索、引用验证、批量元数据、引用格式化 |
| team-collaboration | 多 agent 并行协作 |
| using-med-research-powers | Orchestrator：路由、检查点、用户记忆、pipeline 状态 |
| writing-mrp-skills | 创建/改进 MRP skill |

**研究类型路由（全部在 `study-design` 内部）：**
- 临床（RCT/队列/横断面/交叉/非劣效/适应性/真实世界/注册研究）→ Type A
- 基础（细胞/动物/分子）→ Type B
- AI/ML（影像/视频/LLM/器械）→ Type C
- 定性（访谈/焦点小组/扎根理论/混合方法）→ Type D
- 问卷/调查/Delphi → Type E
- 多类型 → 叠加使用

## Mandatory Pipeline

```
research-question → literature-synthesis → study-design → journal-selection →
data-analysis-planning → data-collection-tools → [用户执行数据收集] →
statistical-analysis → figure-generation →
manuscript-writing → manuscript-export → pre-submission-verification →
submission-preparation → [投稿] → revision-response
```

**辅助 skill（随时可调用，不在主线上）：**
- `pubmed-search` — 被 literature-synthesis / pre-submission-verification / manuscript-writing 调用
- `manuscript-export` — 被 manuscript-writing 完成后自动建议
- `data-collection-tools` — study-design 完成后自动建议，生成数据收集工具

4 个 Hard Checkpoint（Protocol / SAP / Journal / Pre-submission）锁定不可逆决策。其余步骤遵循推荐顺序，支持灵活推进和 Fast-Track Mode。

## Pipeline 回溯（Backward Links）

在后续阶段发现问题时，允许回溯到上游 skill：

| 当前阶段 | 发现的问题 | 回溯到 |
|---------|-----------|--------|
| manuscript-writing | 研究问题定义不准确 | → research-question-formulation |
| manuscript-writing | 分析方法需要调整 | → data-analysis-planning |
| statistical-analysis | 假设检验不通过 | → data-analysis-planning（修改 SAP） |
| pre-submission-verification | 报告规范不合规 | → manuscript-writing |
| pre-submission-verification | 统计不完整 | → statistical-analysis |
| peer-review-simulation | 方法学有 Critical 问题 | → study-design |
| revision-strategy | 审稿人要求补充分析 | → statistical-analysis |

**回溯规则：** 回溯后修改的 artifact 必须标注修改原因和日期，下游依赖 skill 需要重新验证。

## Session State Tracking

推荐在项目目录维护 `.mrp-state.json`，追踪研究进度：

```json
{
  "project": "研究标题",
  "created": "2026-04-02",
  "last_updated": "2026-04-02",
  "target_journal": "期刊名",
  "completed_skills": [
    {"skill": "research-question-formulation", "output": "research-question.md", "date": "..."},
    {"skill": "study-design", "output": "study-design.md", "date": "..."}
  ],
  "current_stage": "data-analysis-planning",
  "artifacts": {
    "research-question.md": {"version": 1, "date": "..."},
    "analysis-plan.md": {"version": 2, "date": "...", "change_log": "Revised after lit review"}
  }
}
```

**用法：** 新会话开始时，检查 `.mrp-state.json` → 显示："上次完成到 [stage]，下一步是 [next_skill]？"

## User Memory（用户记忆系统）

跨会话记住用户的身份、偏好和历史，避免每次从零开始。

### 记忆文件：`.mrp-user-profile.json`

在项目目录维护，首次使用 MRP 时通过对话收集，后续自动更新。

```json
{
  "profile": {
    "name": "用户姓名",
    "role": "PI / 博士生 / 博士后 / 住院医 / 数据分析师",
    "department": "科室/实验室",
    "institution": "机构名称",
    "expertise_level": "senior / mid / junior",
    "research_domains": ["泌尿外科", "医学AI", "肿瘤学"],
    "methods_familiar": ["RCT", "cohort", "deep learning", "survival analysis"],
    "methods_unfamiliar": ["Bayesian", "mediation analysis"],
    "preferred_language": "中文 / English / 双语"
  },
  "preferences": {
    "favorite_journals": [
      {"name": "European Urology", "id": "european-urology", "times_targeted": 3},
      {"name": "Lancet Digital Health", "id": "lancet-digital-health", "times_targeted": 1}
    ],
    "preferred_stats_tool": "Python / R / SPSS / Stata",
    "preferred_figure_style": "nature / lancet / jama",
    "writing_language": "English",
    "detail_level": "detailed / concise"
  },
  "history": {
    "projects_completed": [
      {
        "title": "AI-assisted diagnosis of bladder cancer on CT",
        "date": "2026-03",
        "type": "ai-diagnostic",
        "journal_submitted": "Radiology",
        "outcome": "accepted / revision / rejected",
        "lessons_learned": "审稿人要求补充外部验证集"
      }
    ],
    "common_reviewer_feedback": [
      "需要更大的外部验证集",
      "缺少与现有方法的对比",
      "统计方法描述不够详细"
    ],
    "skills_most_used": ["ai-medical-study-design", "statistical-analysis", "manuscript-writing"]
  },
  "last_updated": "2026-04-02"
}
```

### 记忆采集规则

**首次使用时（.mrp-user-profile.json 不存在）：**

在第一个 skill 触发前，自动询问：

```
────────────────────────────────────────
👤 MRP 首次使用 — 建立用户画像

为了更好地辅助你的研究，请告诉我：

1. 你的身份？（PI / 博士生 / 博士后 / 住院医 / 其他）
2. 你的研究领域？（如：泌尿外科AI、肿瘤流行病学）
3. 你常投的期刊？（如：European Urology、Lancet Digital Health）
4. 你熟悉的统计方法？（如：t-test、Cox 回归、深度学习）
5. 你偏好的分析工具？（Python / R / SPSS / Stata）

可以简单回答，也可以说"跳过"以后再补充。
────────────────────────────────────────
```

**后续自动更新（不打扰用户）：**

| 触发事件 | 更新内容 |
|---------|---------|
| journal-selection 完成 | → 更新 `favorite_journals`（计数 +1） |
| statistical-analysis 使用某方法 | → 更新 `methods_familiar` |
| 用户说"我不熟悉 X" | → 添加到 `methods_unfamiliar` |
| pre-submission-verification 通过 | → 添加到 `projects_completed` |
| 收到审稿意见并处理 | → 更新 `common_reviewer_feedback` |
| 任何 skill 被调用 | → 更新 `skills_most_used` 计数 |

### 记忆使用规则

**各 skill 如何利用用户记忆：**

| Skill | 使用方式 |
|-------|---------|
| `research-question-formulation` | 根据 `research_domains` 引导方向，根据 `expertise_level` 调整提问深度 |
| `literature-synthesis` | 根据 `research_domains` 预设数据库组合和 MeSH 关键词 |
| `study-design` | 根据 `methods_familiar` 推荐熟悉的设计，对 `methods_unfamiliar` 提供更多解释 |
| `journal-selection` | 根据 `favorite_journals` 优先推荐，根据历史投稿结果调整梯队 |
| `data-analysis-planning` | 根据 `preferred_stats_tool` 生成对应语言的脚本模板 |
| `statistical-analysis` | 对 `methods_unfamiliar` 的方法提供详细注释和解释 |
| `figure-generation` | 根据 `preferred_figure_style` 预设配色和样式 |
| `manuscript-writing` | 根据 `favorite_journals` 自动加载期刊模板 |
| `peer-review-simulation` | 根据 `common_reviewer_feedback` 重点检查历史弱项 |
| `revision-strategy` | 根据历史审稿反馈模式提供针对性建议 |

### 隐私规则

- 记忆文件仅存储在本地项目目录，不上传到任何服务
- 用户随时可以删除 `.mrp-user-profile.json` 清除所有记忆
- 用户可以说"忘记我的 [某项信息]"来删除特定字段
- 不记录敏感信息（密码、患者数据、伦理批准号等）

## Red Flags — STOP

| 想法 | 现实 |
|------|------|
| "直接跑个 t 检验就行" | 先确认分布、样本量、前提假设 |
| "这个分析很简单不需要计划" | 无计划 = p-hacking 温床 |
| "先出图再说" | 先完成统计分析再可视化 |
| "不需要查文献" | 最新方法学进展可能改变最佳实践 |
| "伦理审查不是 AI 的事" | 必须提醒确认伦理状态 |
| "样本量够大没问题" | 必须正式 power analysis |
| "p < 0.05 就是显著" | 效应量 + CI + 临床意义综合判断 |
| "Accuracy 95% 模型很好" | 类别不平衡时看 AUROC/AUPRC |
| "训练集效果好就行" | 没有独立测试集/外部验证不可信 |
| "AI 研究不需要临床规范" | 需要同时满足技术和临床两套 |
| "数据随机划分就行" | 同一患者不能同时在训练和测试集 |
| "AUROC 高就有临床价值" | 必须 DCA 评估净获益 |
| "回顾性不需要伦理" | 需要伦理审查或豁免 |
| "做了 3 个复孔就是 n=3" | 技术重复 n=1 |
| "不需要阴性对照" | 无对照结果不可解读 |
| "WB 肉眼可见不用定量" | 必须灰度值定量 |
| "SD 太大换 SEM" | 数据美化，如实用 SD |
| "动物实验不用随机" | 必须随机，否则分配偏倚 |
| "用 CONSORT 2010 就行" | 2025 已取代 2010（30 项） |
| "器械/AI 直接做 RCT" | 先 IDEAL 定位阶段 |
| "AI 评估不报告可用性" | DECIDE-AI 要求报告 |
| "论文写完就可以投了" | **必须过 pre-submission-verification** |

## Quality Gates (cannot skip)

1. **分析前** — 必须有明确的科学问题和假设
2. **方法选择后** — 必须验证前提假设
3. **结果出来后** — 必须做敏感性分析
4. **写结论前** — 必须区分统计显著性和临床意义
5. **投稿前** — **必须通过 pre-submission-verification（CONSORT 2025 / SPIRIT 2025）**
