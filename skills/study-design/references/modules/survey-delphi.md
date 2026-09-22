# Module E — Survey / Questionnaire / Delphi（问卷 / 量表 / 共识）

`study-design/SKILL.md` 的 Study Type Router 判定为 `type: survey` 时读取本文件。
这里只放问卷/调查研究特有的判断；通用 5 步 Workflow、Output、Hard Checkpoint、衔接规则都在 SKILL.md。
查阅型表格（测量属性、抽样策略、样本量公式、Delphi 规则、采集方式）在 `references/survey-reference.yaml`。

## 适用范围

横断面调查（KAP）、问卷/量表开发与验证、Delphi 共识研究、需求评估调查、医学教育调查。

**问卷/调查研究有独立的方法学要求——不是"发个问卷收数据"这么简单。**

## Survey Type Router

```
研究目的？
├── 描述群体特征（KAP/患病率/满意度）→ Cross-sectional Survey（STROBE；在线用 CHERRIES）
├── 开发新问卷/量表 → Questionnaire Development（COSMIN）
├── 验证已有问卷 → Validation Study（COSMIN）
├── 专家共识 → Delphi Study（CROSS 报告调查方法；共识标准预先定义）
├── 纵向变化 → Longitudinal Survey（→ 考虑 Module A 队列）
└── 在线调查 → Web-based Survey（报告: CHERRIES）
```

## Workflow（问卷专属步骤，对应 SKILL.md 通用 Step 2-4）

### Step 1: 问卷设计

**新开发问卷：**

```
1. 概念框架 (Conceptual Framework)
   → 明确测量的构念（construct）
   → 文献综述确定维度
   → 访谈/焦点小组获取条目（→ 可先走 Module D. Qualitative）

2. 条目生成 (Item Generation)
   → 每个维度 3-5 倍条目（预留筛选空间）
   → 条目措辞规则：
     - 避免双重否定
     - 每条只测一个概念
     - 避免引导性措辞
     - 适合目标人群的阅读水平

3. 专家内容效度 (Content Validity)
   → 5-10 位专家评审
   → 计算 I-CVI（条目水平）和 S-CVI（量表水平）
   → I-CVI >= 0.78, S-CVI/Ave >= 0.90

4. 认知访谈 (Cognitive Interviewing)
   → 5-10 位目标人群测试
   → 出声思维法（Think-aloud）
   → 修改不清楚的条目

5. 预试验 (Pilot Testing)
   → n >= 30
   → 检查完成时间、天花板/地板效应、缺失率
```

**使用已有问卷：**

```
→ 确认原始量表的信效度证据
→ 如需翻译：正向翻译 → 回译 → 专家审核 → 预试验
→ 需要在目标人群重新验证信效度
```

### Step 2: 测量属性（量表验证）

8 项测量属性（内容/结构/收敛/区分/效标效度 + 内部一致性/重测信度/反应度）的方法和判定标准表 → 读取 `references/survey-reference.yaml` 的 `psychometric_properties`。

**样本量关键判断：** EFA 至少条目数 × 5-10；CFA 至少 200 人；EFA 与 CFA 必须用不同样本。

### Step 3: 抽样策略

6 种抽样策略（简单随机/分层/整群/便利/配额/滚雪球）的适用与优缺点表 → 读取 `references/survey-reference.yaml` 的 `sampling_strategies`。

### Step 4: 样本量计算

公式与参数（横断面 n = Z²·p·(1-p)/d²、有限总体与应答率修正、量表验证、Delphi）→ 读取 `references/survey-reference.yaml` 的 `sample_size`。

### Step 5: Delphi 方法（如适用）

轮次流程、共识标准（>= 70-80% 同意率 / IQR <= 1 / 中位数 >= 7/9）、报告要求 → 读取 `references/survey-reference.yaml` 的 `delphi`。

关键判断：通常 3 轮（最多 4 轮）；共识标准、停止规则、专家资格必须**预先定义**并写进 protocol。

### Step 6: 数据收集

4 种采集方式（在线/纸质/电话/面对面）的工具与优劣表 → 读取 `references/survey-reference.yaml` 的 `data_collection_modes`。

**在线调查报告规范：CHERRIES**；一般调查方法报告：CROSS。

## Output

生成 `study-protocol.md`（`type: survey`），骨架在 `references/protocol-templates.md` 的 "E. Survey" 部分。
报告规范按 Survey Type Router：STROBE（横断面）/ CHERRIES（在线）/ CROSS（调查方法）/ COSMIN（量表开发与验证）。

## Common Mistakes（问卷特有）

| 想法 | 现实 |
|------|------|
| "问卷随便写几个问题就行" | 需要概念框架、条目生成、专家审核、认知访谈、预试验 |
| "Cronbach's alpha > 0.7 就行了" | 还需要结构效度（EFA/CFA）、收敛/区分效度 |
| "样本越大越好" | 大样本 + 低应答率 = 偏倚比小样本 + 高应答率更严重 |
| "便利抽样没问题" | 必须在 Limitations 中讨论选择偏倚 |
| "翻译量表直接用" | 必须回译 + 目标人群信效度重新验证 |
| "Delphi 两轮就够了" | 至少 2 轮有反馈的评分，通常 3 轮 |
| "同意率 51% 就是共识" | 预先定义共识标准，通常 >= 70-80% |
| "在线调查不需要伦理审查" | 收集人类受试者数据都需要伦理审查 |

## Convergence（问卷特有完成条件）

1. 问卷/量表设计完成或已有量表确认（含翻译与再验证计划）
2. 抽样策略和样本量已确定（含应答率修正）
3. 信效度验证计划已规划（如适用；EFA/CFA 分样本）
4. 数据收集方式和平台已选定
5. 分析计划已明确
6. 伦理审查已考虑
7. 报告规范已确定

## Red Flags（问卷特有）

- **禁止未经验证的自编量表直接用于正式研究** — 至少需要内容效度 + 预试验
- **禁止忽略应答率** — 必须报告应答率，低于 60% 需要讨论偏倚
- **禁止 EFA 和 CFA 用同一份数据** — 必须分样本或使用独立数据集
- **禁止 Delphi 事后定共识标准**
