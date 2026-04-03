# Med-Research-Powers 用户手册

> **版本**: v5.0.0 | **更新日期**: 2026-03-29 | **仓库**: https://github.com/Stefansong/med-research-powers

---

## 目录

1. [这是什么](#1-这是什么)
2. [安装](#2-安装)
3. [快速开始](#3-快速开始)
4. [完整工作流](#4-完整工作流pipeline)
5. [16 个技能详解](#5-16-个技能详解)
6. [5 个斜杠命令](#6-5-个斜杠命令)
7. [6-Gate 投稿前验证](#7-6-gate-投稿前验证)
8. [4 审稿人模拟评审](#8-4-审稿人模拟评审)
9. [报告规范速查（~40 个）](#9-报告规范速查40-个)
10. [内置脚本和参考文件](#10-内置脚本和参考文件)
11. [常见场景示例](#11-常见场景示例)
12. [常见问题 FAQ](#12-常见问题-faq)

---

## 1. 这是什么

Med-Research-Powers（MRP）是一套**医学科研方法论框架**，以 Claude Code Plugin 的形式运行。它解决一个核心问题：

> AI 辅助写代码时会跳步骤、不测试、不规划。AI 辅助做科研时也一样——跳过文献调研、用错统计方法、忽略报告规范、生成不可复现的分析。

MRP 用 **16 个技能**覆盖从"我想研究一个课题"到"论文投出去"的完整流程，并在关键节点设置**强制门控**——比如没有分析计划就不能跑统计，论文没过 6-Gate 验证就不能说"可以投了"。

### 与其他工具的区别

| 特性 | 通用学术框架 | Med-Research-Powers |
|------|------------|-------------------|
| 报告规范 | 不覆盖或仅提 APA | ~40 个医学规范（CONSORT 2025、DECIDE-AI、IDEAL...） |
| 伦理审查 | 不涉及 | 强制检查 IRB/IACUC、知情同意、数据隐私 |
| 实验设计 | 不涉及 | WB/qPCR/动物实验设计模板 |
| 样本量计算 | 不涉及 | 内置 5 种场景的 Python 脚本 |
| 统计假设检验 | 不涉及 | 内置自动检验 + 方法推荐脚本 |
| 研究类型路由 | 通用 | 区分临床 / 基础 / AI-ML / 手术创新 |
| 投稿验证 | 基本检查 | 6-Gate（含 Claim Verification 防 AI 幻觉） |
| 审稿模拟 | 基本 | 4 审稿人（含 Devil's Advocate）+ 0-100 评分 |

### 设计灵感

MRP 的架构灵感来自 [Superpowers](https://github.com/obra/superpowers)——一套软件工程方法论框架。核心理念相同：**先想后做、流程强制、质量门控**。只是把"先写测试再写代码"换成了"先写分析计划再跑统计"。

---

## 2. 安装

### 方式 1：Claude Code Plugin（推荐）

```bash
git clone https://github.com/Stefansong/med-research-powers.git
```

然后在 Claude Code 中执行：

```
/plugin install ./med-research-powers
```

重启 Claude Code 后，每次新 session 会自动看到 MRP 引导信息。

### 方式 2：交互式安装

```bash
git clone https://github.com/Stefansong/med-research-powers.git
cd med-research-powers
./install.sh
```

安装脚本会：
- 检测你的操作系统（macOS / Linux / Windows）
- 找到 Claude Code 的配置目录
- 提供三种安装方式供选择：
  - **Plugin 安装**（推荐）— 支持 hooks 和自动更新
  - **复制安装** — 简单直接，但没有 hooks
  - **符号链接** — 开发者模式，编辑源文件立即生效
- 检查 Python 依赖（scipy、statsmodels、matplotlib）

### 方式 3：手动复制

```bash
git clone https://github.com/Stefansong/med-research-powers.git
cp -r med-research-powers/skills ~/.claude/skills/
```

> **注意**：手动复制不会启用 session-start hook，Claude 不会自动发现 MRP 技能。

### 验证安装

启动一个新的 Claude Code session。如果你看到类似这样的提示，说明安装成功：

```
You have Med-Research-Powers (MRP) — a medical research methodology framework.
Before ANY research-related task, check if a MRP skill applies.
```

试试输入：`/mrp:research-question` 或直接说"帮我设计一个研究"。

### Python 依赖（可选）

MRP 的核心技能不依赖 Python。但如果你想使用内置的统计脚本（假设检验、样本量计算、出版级图表），需要安装：

```bash
pip install scipy statsmodels matplotlib pandas numpy
```

---

## 3. 快速开始

### 3 分钟体验

1. 在 Claude Code 中说：**"我想研究 AI 辅助前列腺 MRI 诊断的准确性"**
2. Claude 会自动调用 `research-question-formulation`，按 PICO 框架逐步追问
3. 追问完成后生成 `research-question.md`
4. Claude 会建议下一步：查文献（`literature-synthesis`）或设计研究（`ai-medical-study-design`）

### 最常用的 5 个命令

| 你想做什么 | 说什么 / 输入什么 |
|-----------|----------------|
| 构建研究问题 | `/mrp:research-question` 或"帮我想想选题" |
| 分析数据 | `/mrp:analyze-data` 或"帮我分析这个数据" |
| 写论文 | `/mrp:write-manuscript` 或"帮我写 Introduction" |
| 投稿前检查 | `/mrp:check-standards` 或"帮我检查报告规范" |
| 模拟审稿 | `/mrp:peer-review` 或"帮我审一下" |

---

## 4. 完整工作流（Pipeline）

MRP 的设计是一条**推荐流水线**，其中 4 个硬性检查点（Protocol / SAP / 期刊 / 投稿前验证）锁定不可逆决策，其余步骤支持灵活推进和 Fast-Track Mode。

```
                    ┌─────────────────────┐
                    │ 1. 研究问题构建      │ ← "我想研究..."
                    │ (PICO + FINER)       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ 2. 文献综合          │ ← "这个领域有什么研究？"
                    │ (系统检索 + gap 分析) │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ 3a. 临床     │  │ 3b. 基础     │  │ 3c. AI/ML   │ ← 按类型路由
    │ study-design │  │ basic-design │  │ ai-design   │
    └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
           └────────────────┼────────────────┘
                            │
                 ┌──────────▼──────────┐
                 │ 4. 分析计划          │ ← "用什么统计方法？"
                 │ (SAP, 先写再跑)      │
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │ 5. 统计分析执行      │ ← "帮我跑分析"
                 │ (假设检验→执行→敏感性)│
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │ 6. 出版级图表        │ ← "帮我画图"
                 │ (期刊标准 + 色盲友好) │
                 └──────────┬──────────┘
                            │
                 ┌──────────▼──────────┐
                 │ 7. 论文撰写          │ ← "帮我写论文"
                 │ (IMRaD 结构)         │
                 └──────────┬──────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼                           ▼
    ┌─────────────────┐         ┌─────────────────┐
    │ 8. 模拟审稿      │         │ 9. 投稿前验证    │ ← 必须通过！
    │ (4人 + 0-100分)  │────────▶│ (6-Gate)        │
    └─────────────────┘         └────────┬────────┘
                                         │
                                         │ 全部通过
                                         ▼
                                    ✅ 可以投稿
                                         │
                                         │ 收到审稿意见
                                         ▼
                              ┌──────────────────┐
                              │ 10. 回复审稿人    │
                              │ (逐条 + 修改追踪)  │
                              └──────────────────┘
```

### 强制规则

- **没有 `research-question.md`** → `data-analysis-planning` 拒绝执行
- **没有 `analysis-plan.md`** → `statistical-analysis` 拒绝执行
- **没有分析结果** → `manuscript-writing` 拒绝执行
- **论文"写完了"** → 自动触发 `pre-submission-verification`，不可跳过
- **6-Gate 任一失败** → 阻止投稿，列出修改项

### 1% Rule

即使只有 1% 的可能性某个技能适用，Claude 也会调用检查。宁可调用后发现不适用，也不跳过。

---

## 5. 16 个技能详解

### 流水线技能（按顺序）

#### 5.1 research-question-formulation（科学问题构建）

**触发词**："我想研究..."、"选题"、"科学问题"

按苏格拉底式追问法逐步明确研究问题：
- **Round 1 (PICO)**：Population、Intervention/Exposure、Comparison、Outcome
- **Round 2 (FINER)**：可行性、趣味性、新颖性、伦理、相关性（各打 1-5 分）
- **Round 3**：零假设 H0、备择假设 H1、预期结果

**输出**：`research-question.md`

**收敛条件**：PICO 四要素全部明确 + 假设可用统计语言表述 + 用户确认

---

#### 5.2 literature-synthesis（文献综合）

**触发词**："帮我查文献"、"research gap"、"文献综述"

系统性检索（优先用 PubMed MCP）→ 文献筛选 → 证据评价（Oxford CEBM + RoB 2 / ROBINS-I / NOS）→ 按主题综合（不是按时间排列）→ 识别 research gap

**输出**：`search-strategy.md`（可复现的检索策略）+ gap 分析

**绝对禁止**：编造不存在的文献、只引用支持自己观点的文献

---

#### 5.3 study-design / basic-medical-study-design / ai-medical-study-design（研究设计三件套）

根据研究类型自动路由：

| 研究类型 | 用哪个 skill | 关键特点 |
|---------|-------------|---------|
| RCT、队列、横断面、诊断准确性 | `study-design` | CONSORT 2025、STARD、STROBE |
| 细胞/动物/分子/蛋白实验 | `basic-medical-study-design` | 对照设置、生物学重复 vs 技术重复、ARRIVE 2.0 |
| AI 影像/手术视频/LLM 评估/器械 | `ai-medical-study-design` | TRIPOD-AI、DECIDE-AI、IDEAL 框架、data leakage 防控 |

**输出**：`study-protocol.md`

**关键提醒**：
- 基础研究："3 个复孔 ≠ n=3"，n 只算生物学重复
- AI 研究："同一患者的数据不能同时出现在训练和测试集"
- 器械创新："先用 IDEAL 框架定位你在哪个阶段，Stage 1-2 不要做 RCT"

---

#### 5.4 data-analysis-planning（分析计划）

**触发词**："帮我分析数据"、"用什么统计方法"

先写分析计划再跑分析——防止 p-hacking 和事后假设。生成 `analysis-plan.md` 包含：数据概览 → 预处理策略 → 描述性统计 → 主要分析方法（含决策树）→ 亚组分析 → 敏感性分析 → 多重比较策略。

统计方法选择可参考内置的 `references/stat-method-decision-tree.yaml`。

**输出**：`analysis-plan.md`（用户确认后才能进入执行阶段）

---

#### 5.5 statistical-analysis（统计分析执行）

**触发词**："跑分析"、"统计检验"、"回归"、"生存分析"

按 `analysis-plan.md` 逐步执行。两个关键要求：
1. **先检验前提假设再跑参数检验**（可直接调用 `scripts/assumption_tests.py`）
2. **每个结果必须报告统计量 + p 值 + 效应量 + 95% CI**（不只 p < 0.05）

**输出**：`results-summary.md` + 完整可执行 Python 脚本

---

#### 5.6 figure-generation（出版级图表）

**触发词**："画图"、"Figure"、"ROC 曲线"、"热图"

使用内置 `scripts/pub_style.py` 一键设置期刊级样式（Nature/Lancet/JAMA/NEJM 配色）。

**要求**：Arial 字体、≥300 DPI、色盲友好配色、坐标轴完整标签、TIFF + PDF 双格式保存

---

#### 5.7 manuscript-writing（论文撰写）

**触发词**："写论文"、"写 Introduction"、"写 Discussion"

推荐写作顺序（不是论文顺序）：Methods → Results → Introduction → Discussion → Abstract → Title

**关键禁区**：
- Results 中不讨论意义
- Discussion 中不引入 Results 没有的数据
- "significantly" 只能指统计学显著
- 不用 "prove"，用 "support" 或 "suggest"

**完成后**：自动触发 `pre-submission-verification`（不可跳过）

---

### 质量保障技能

#### 5.8 reporting-standards（报告规范检查）

覆盖 ~40 个报告规范。核心路由：

| 研究类型 | 用哪个规范 |
|---------|----------|
| RCT | **CONSORT 2025**（⚠️ 不是 2010） |
| 观察性研究 | STROBE |
| 系统综述 | PRISMA 2020 |
| 诊断准确性 | STARD 2015 |
| AI 预测模型 | TRIPOD+AI 2024 |
| LLM/VLM 评估 | TRIPOD-LLM 2024 |
| AI 决策支持 | DECIDE-AI 2022 |
| 手术/器械创新 | IDEAL 框架 |
| 医学影像 AI | CLAIM 2020 |
| 动物实验 | ARRIVE 2.0 |

完整的 ~40 个规范主索引在 `references/checklists/standards-index.yaml`。

**输出**：逐条检查报告（✅/⚠️/❌） + 格式化的投稿 checklist

---

#### 5.9 peer-review-simulation（模拟审稿）

**4 位审稿人**：
1. 方法学专家 — 设计、统计、偏倚控制
2. 临床专家 — 临床意义、可操作性
3. 学术编辑 — 结构、语言、期刊匹配
4. **Devil's Advocate** — 专门挑战最强结论、找盲点、提出最不利的替代解释

**0-100 量化评分**（8 个维度）：

| 维度 | 权重 |
|------|------|
| 创新性 Originality | 15% |
| 方法学 Methodology | 20% |
| 结果可靠性 Results | 15% |
| 临床意义 Clinical Impact | 15% |
| 写作质量 Writing | 10% |
| 图表 Figures & Tables | 10% |
| 参考文献 References | 5% |
| 可复现性 Reproducibility | 10% |

**综合分映射**：80+ Accept/Minor → 65-79 Minor → 50-64 Major → <50 Reject

---

#### 5.10 pre-submission-verification（投稿前验证）

**6-Gate 强制检查**，全部通过才能投稿：

| Gate | 检查内容 | 说明 |
|------|---------|------|
| Gate 1 | 报告规范合规 | 0 个 Critical ❌ 项 |
| Gate 2 | 统计完整性 | 效应量 + CI，不只 p 值 |
| **Gate 3** | **Claim Verification** | **参考文献真实性、数据一致性、claims-evidence 对应、AI 幻觉检测** |
| Gate 4 | 图表质量 | Arial、≥300 DPI、色盲友好 |
| Gate 5 | 伦理合规 | IRB 号、知情同意、COI |
| Gate 6 | 形式检查 | 字数、参考文献数、Running title |

**Gate 3 (Claim Verification) 详细说明**：

- **Phase A**：每篇引用的文献是否真实存在（PMID/DOI 可查）
- **Phase B**：Abstract 中的数字是否与 Results/Tables 一致
- **Phase C**：每个"我们发现..."断言是否有对应统计结果
- **Phase D**：Methods 描述的每个分析在 Results 中是否都有结果
- **Phase E**：检查是否有典型 AI 幻觉模式（编造的引用、过于对称的数据）

---

#### 5.11 research-ethics（伦理合规）

检查 6 个方面：
1. 伦理审查（IRB/EC + IACUC）
2. 知情同意（前瞻性/回顾性豁免/特殊群体）
3. 数据隐私（去标识化 + 法规合规：个人信息保护法/GDPR/HIPAA）
4. 研究注册（ClinicalTrials.gov / ChiCTR / PROSPERO）
5. 利益冲突
6. 数据共享

**绝对禁止**：没有伦理批准就建议开始数据收集

---

### 响应型技能

#### 5.12 responding-to-reviewers（回复审稿意见）

**触发词**："审稿意见"、"revision"、"大修/小修"

对每条审稿意见：分类（方法学/补充分析/文字改进/不合理要求）→ 逐条回复（感谢→回应→标注修改位置）→ 生成修改追踪表 → 修改后强制再跑 `pre-submission-verification`

---

#### 5.13 writing-mrp-skills（元技能）

教你如何为 MRP 创建新的技能。包含 SKILL.md 写作规范、内容分层规则、测试方法。

---

#### 5.14 using-med-research-powers（编排器）

元技能——所有其他技能的路由中心。包含完整的触发场景表、红旗清单（22 条"想法→现实"对照）、5 个质量门控。

---

## 6. 5 个斜杠命令

在 Claude Code 中直接输入：

| 命令 | 功能 | 调用的技能 |
|------|------|----------|
| `/mrp:research-question` | 构建研究问题 | research-question-formulation |
| `/mrp:analyze-data` | 制定分析计划 + 执行统计 | data-analysis-planning → statistical-analysis |
| `/mrp:write-manuscript` | 按 IMRaD 写论文 | manuscript-writing |
| `/mrp:check-standards` | 报告规范检查 + 6-Gate 验证 | reporting-standards + pre-submission-verification |
| `/mrp:peer-review` | 4 人模拟审稿 + 评分 | peer-review-simulation |

---

## 7. 6-Gate 投稿前验证

详见 [5.10 节](#510-pre-submission-verification投稿前验证)。

**为什么需要 Gate 3 (Claim Verification)**：

AI 辅助写论文时最大的风险不是格式问题，而是内容不真实——编造的参考文献、Abstract 和 Results 中数据不一致、结论超出数据支持范围。Gate 3 用 5 个 Phase（A-E）系统性地验证内容真实性，这是学术诚信的底线。

---

## 8. 4 审稿人模拟评审

详见 [5.9 节](#59-peer-review-simulation模拟审稿)。

**为什么需要 Devil's Advocate**：

前三个审稿人各司其职，但都倾向于"评价"论文而非"挑战"论文。Devil's Advocate 的职责是：
- "如果这个发现是假阳性呢？需要什么证据才能排除？"
- "你最强的结论依赖的最弱假设是什么？"
- "如果审稿人完全不信你的方法学，你怎么辩护？"

他提出的问题就是你在真实审稿中最难回答的问题。提前准备好防御策略，投稿后收到类似质疑时就不会手忙脚乱。

---

## 9. 报告规范速查（~40 个）

### 最常用的 10 个

| 研究类型 | 规范 | 条目数 | 关键提醒 |
|---------|------|--------|---------|
| RCT | CONSORT 2025 | 30 | ⚠️ 2010 已被取代 |
| 观察性 | STROBE | 22 | 队列/病例对照/横断面通用 |
| 系统综述 | PRISMA 2020 | 27 | 必须含可复现的检索策略 |
| 诊断 | STARD 2015 | 30 | 需要流程图 |
| AI 预测 | TRIPOD+AI 2024 | 27 | 取代了旧版 TRIPOD |
| LLM 评估 | TRIPOD-LLM 2024 | 视版本 | 新标准 |
| AI 决策支持 | DECIDE-AI 2022 | 17 | 早期评估专用 |
| 手术创新 | IDEAL | 5 阶段 | 框架而非 checklist |
| 影像 AI | CLAIM 2020 | 40 | 最详细的 AI 规范 |
| 动物实验 | ARRIVE 2.0 | 21 | 越来越多期刊强制要求 |

### 偏倚风险评估工具

| 工具 | 适用场景 |
|------|---------|
| Cochrane RoB 2 | RCT 偏倚 |
| ROBINS-I | 非随机干预研究 |
| NOS | 观察性研究质量 |
| MINORS | 非随机外科研究 |
| QUADAS-2 | 诊断准确性偏倚 |
| PROBAST | 预测模型偏倚 |

完整列表见 `skills/reporting-standards/references/checklists/standards-index.yaml`。

---

## 10. 内置脚本和参考文件

### Python 脚本（3 个）

#### pub_style.py（出版级图表样式）

```python
import sys; sys.path.insert(0, 'skills/figure-generation/scripts')
from pub_style import setup, save_figure, COLORS, COLORBLIND_SAFE

# 一键设置 Nature 风格
colors, width = setup(journal='nature', single_column=True)

# 支持的期刊：nature, lancet, jama, nejm, default
# 色盲安全调色板：COLORBLIND_SAFE（Okabe-Ito 8 色）
# 保存多格式：save_figure(fig, 'figure1', formats=('tiff', 'pdf'))
```

#### assumption_tests.py（假设检验 + 方法推荐）

```python
import sys; sys.path.insert(0, 'skills/statistical-analysis/scripts')
from assumption_tests import full_check, effect_size_cohens_d

# 一行搞定：正态性 + 方差齐性 + 推荐方法
result = full_check(group1, group2, paired=False)
print(result['recommended_test'])  # e.g., "Independent t-test"

# 效应量
d = effect_size_cohens_d(group1, group2)
print(f"Cohen's d = {d['cohens_d']} ({d['magnitude']})")
```

#### power_analysis.py（样本量计算）

```python
import sys; sys.path.insert(0, 'skills/statistical-analysis/scripts')
from power_analysis import two_groups, diagnostic, survival, correlation, proportion

# 两组比较
r = two_groups(effect_size=0.5, power=0.80, dropout=0.15)
# → n_per_group=64, adjusted=76

# 诊断准确性研究
r = diagnostic(sensitivity=0.90, prevalence=0.3, precision=0.05)
# → n_total=464

# 生存分析
r = survival(hazard_ratio=0.7, event_rate=0.4)
# → events_needed=494, n_total=1373
```

### 参考文件（8 个）

| 文件 | 位置 | 内容 |
|------|------|------|
| `consort-2025.yaml` | reporting-standards/references/ | 完整 30 项清单（含 2025 新增标记） |
| `standards-index.yaml` | reporting-standards/references/ | ~40 个规范的主索引 |
| `stat-method-decision-tree.yaml` | data-analysis-planning/references/ | 统计方法选择指南 |
| `metrics-and-reporting.yaml` | ai-medical-study-design/references/ | AI 研究指标 + 规范映射 |
| `western-blot.md` | basic-medical-study-design/references/ | WB 实验设计模板 |
| `qpcr.md` | basic-medical-study-design/references/ | qPCR 实验设计模板 |
| `animal-study.md` | basic-medical-study-design/references/ | 动物实验设计模板 |
| `omics-methods.md` | data-analysis-planning/references/ | 组学分析流程 |

---

## 11. 常见场景示例

### 场景 1：从零开始一个 AI 影像诊断研究

```
你："我想做一个用 AI 辅助前列腺 MRI PI-RADS 评分的研究"
```

MRP 会依次触发：
1. `research-question-formulation` → PICO 追问 → 生成 `research-question.md`
2. `ai-medical-study-design` → 识别为"AI 辅助诊断" → 推荐 STARD + CLAIM → 讨论 ground truth 标注方案
3. `data-analysis-planning` → SAP：AUROC + DCA + 亚组分析
4. ...后续跟着 pipeline 走

### 场景 2：论文写完了要投稿

```
你："论文差不多写完了，帮我检查一下再投 BJU International"
```

MRP 自动触发 `pre-submission-verification`：
- Gate 1：检查 STARD/CLAIM/STROBE（取决于研究类型）
- Gate 2：检查统计完整性
- Gate 3：验证引用真实性、数据一致性
- Gate 4-6：图表、伦理、形式

如果发现问题 → 列出修改项 → 修复后重新检查

### 场景 3：收到审稿意见

```
你："收到 BJU Int 的大修意见，审稿人要我补亚组分析和解释样本量偏小的问题"
```

MRP 触发 `responding-to-reviewers`：
- 逐条分类意见
- 补充亚组分析 → 调用 `statistical-analysis`
- 生成 response letter（逐条回复 + 修改位置标注）
- 修改后强制再跑 `pre-submission-verification`

### 场景 4：设计智能穿刺针的可行性研究

```
你："我想发表智能 PCNL 穿刺针的概念验证数据"
```

MRP 识别为器械创新 → `ai-medical-study-design` → IDEAL 框架 → 定位为 Stage 1 (Idea) → 建议写 case report/case series 格式 → 参考 CARE 2017 规范

---

## 12. 常见问题 FAQ

### Q: MRP 会帮我写论文吗？

MRP 不会替你写论文。它帮你确保**方法学正确、规范合规、结果可靠**。具体的科学判断——研究问题怎么定、数据怎么解读、临床意义是什么——必须由你来做。MRP 是你的方法学顾问，不是代笔。

### Q: 我只想查个 p 值，一定要走完整 pipeline 吗？

不需要。MRP 的技能可以单独使用。但 Claude 可能会问你"有分析计划吗"——如果你说有或者这只是一个快速问题，它不会强制你走全流程。强制流水线只在你做完整的研究项目时才会严格执行。

### Q: CONSORT 2010 和 2025 有什么区别？为什么必须用 2025？

2025 版新增了 7 项（含开放科学专节）、修订了 3 项、删除了 1 项，从 25 项扩展到 30 项。2025 年 4 月五大顶级期刊（BMJ/JAMA/Lancet/Nature Medicine/PLOS Medicine）同时发布并宣布 2010 版正式被取代。现在投稿用 2010 版清单会被编辑退回。

### Q: 我做基础研究不做临床，MRP 对我有用吗？

有用。`basic-medical-study-design` 覆盖细胞/动物/分子实验的设计规范（对照设置、生物学重复 vs 技术重复、盲法、随机化）。内置 Western blot、qPCR、动物实验的设计模板。还有 ARRIVE 2.0 报告规范检查。

### Q: 我的研究跨了多个类型（比如 AI 分析病理切片 + 动物实验验证），怎么办？

叠加使用。涉及 AI 的部分用 `ai-medical-study-design`（CLAIM + TRIPOD-AI），涉及动物的部分用 `basic-medical-study-design`（ARRIVE 2.0）。两个 skill 可以在同一个研究中同时生效。

### Q: Python 脚本是必须的吗？

不是。脚本是为了提高效率——Claude 直接 import 就行，不用每次重写代码。即使不装 Python 依赖，MRP 的所有 skill 仍然正常工作，只是 Claude 会自行生成等效代码。

### Q: 怎么贡献新的 skill？

阅读 `skills/writing-mrp-skills/SKILL.md`，按规范编写 → 测试 → 提交 PR。核心要求：description 不总结工作流、必须有 Common Mistakes 表、必须有收敛信号。

---

## 附录：项目结构

```
med-research-powers/
├── .claude-plugin/plugin.json        # 插件元数据
├── hooks/session-start.sh            # 启动时自动注入上下文
├── commands/ (5)                     # 斜杠命令
│   ├── research-question.md
│   ├── analyze-data.md
│   ├── write-manuscript.md
│   ├── check-standards.md
│   └── peer-review.md
├── skills/ (16)                      # 技能
│   ├── using-med-research-powers/    # 编排器
│   ├── research-question-formulation/
│   ├── literature-synthesis/
│   ├── study-design/
│   ├── basic-medical-study-design/
│   │   └── references/experiment-templates/ (WB, qPCR, animal)
│   ├── ai-medical-study-design/
│   │   └── references/ (metrics, reporting map)
│   ├── data-analysis-planning/
│   │   └── references/ (decision tree, omics)
│   ├── statistical-analysis/
│   │   └── scripts/ (assumption_tests.py, power_analysis.py)
│   ├── figure-generation/
│   │   └── scripts/ (pub_style.py)
│   ├── manuscript-writing/
│   ├── reporting-standards/
│   │   └── references/checklists/ (consort-2025, standards-index)
│   ├── peer-review-simulation/
│   ├── research-ethics/
│   ├── pre-submission-verification/
│   ├── responding-to-reviewers/
│   └── writing-mrp-skills/
├── examples/showcase/                # 真实 pipeline 产出物
├── install.sh                        # 交互式安装
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE (MIT)
└── README.md
```

---

*Med-Research-Powers 由 BTCH Uro AI Lab 开发维护。*
*灵感来自 [Superpowers](https://github.com/obra/superpowers) by Jesse Vincent。*
