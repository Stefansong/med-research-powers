---
name: statistical-analysis
description: Use when analysis-plan.md already exists and the analysis must now be run on collected data（已有分析计划时执行分析）. Triggers on "跑分析"、"统计检验"、"回归"、"生存分析"、"run the analysis"、"regression"、"survival analysis".
---

# Statistical Analysis

## Overview

按已确认的 `analysis-plan.md`（SAP），**针对这份真实数据现写代码**：先体检数据并对照 SAP 的假设，再现写清洗和分析代码，执行后必须自检（重跑结果一致、人数前后对得上、SAP 每一条都有着落）。不套模板，不拿现成脚本改改变量名就跑。所有结果都要有可复现的代码。本 skill 只"执行"计划，不"制定"计划——方法选择在 `data-analysis-planning` 完成。

> 总调度规则（直接调用本 skill 也适用，原文见 `${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/SKILL.md`）：**结局盲**——SAP 确认前只看数据结构与质量，不看任何变量与结局的关系；**患者级数据不进对话**——不把原始数据行读出或打印出来，只看脚本输出的汇总（research-ethics checklist §4"外部 AI 服务"）；**缺前置产物**——说缺什么，light / auto 下先往下做并记缺口，不拒绝；**checkpoint_mode** 默认 light，只在硬确认处等；**只要一个产物**（如只要 Table 1）时交付后停下。

## When to Use

- 已有确认的 `analysis-plan.md`，数据已收集完毕，要执行统计分析、建模、检验，或只出其中一部分（如 Table 1）
- 审稿人要求的补充分析（标注 post hoc / exploratory，见 Step 4 末尾）

## When NOT to Use

- 还没有 `analysis-plan.md` → 先用 `data-analysis-planning`（"帮我分析数据"、"给我出 Table 1"但无计划时也归它，走快速路径，确认一次）
- 需要做图 → `figure-generation`
- 主要分析的方法要换、而 SAP 没写预定备选 → 回 `data-analysis-planning` 修订 SAP（版本、日期、理由，由用户决定），再回来执行
- 已确认的 SAP 只有描述性部分（如只为 Table 1），现在要做结局分析或按组的结局图 → 回 `data-analysis-planning` 补全 SAP（新版本，再过硬确认 2），再回来执行；这不是 post hoc

## Scripts

四个固定脚本都是检查或计算工具：只报告，不替你做决定，也不改数据。脚本在插件目录，运行目录是用户项目，必须用 `${CLAUDE_PLUGIN_ROOT}` 定位：

| 脚本 | 用途 | 一行可运行示例 |
|------|------|---------------|
| `data_profile.py` | 数据体检（只读）：结构、缺失与伪装缺失、截断值、检验单异常标记、重复 ID/聚类、结局事件数、疑似隐私字段（只报列名）；分类取值只在能区分患者（`--id`，或每行一名患者时 `--rows-are-patients`）且至少 5 名患者共有时显示，7 位以上的整数从不显示；不算变量与结局的关系（退出码 0 完成 / 2 参数或文件错误） | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/data_profile.py" data.csv --id patient_id --outcome recurrence --report data-profile.md` |
| `assumption_tests.py` | 前提诊断（JSON）：正态性、方差齐性、配对差值、球形性（Mauchly、Greenhouse-Geisser ε）只作描述；默认推荐：两组 Welch t 检验，三个及以上重复测量为线性混合模型或 Greenhouse-Geisser 校正的重复测量方差分析；分组 / 受试者 ID 缺失的行剔除并记在 rows_excluded | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/assumption_tests.py" data_clean.csv --value outcome --group arm` |
| `power_analysis.py` | 只复核 protocol 的先验样本量（two-groups / proportion / survival / diagnostic / correlation）；优效性默认双侧（--sides 1 单侧），两组均值和两组率另有非劣效 / 等效（--hypothesis … --margin …），诊断准确性接近 0 或 1 时用 --ci-method wilson；覆盖和不覆盖的设计见 --help | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/power_analysis.py" survival --hr 0.7 --event-rate 0.5` |
| `reproduce_check.py` | 在全新子进程里把分析跑 N 次（每次运行前清空 `--outputs`；之外的缓存不清空，报告列出能认出的），比较输出文件（加 `--compare-stdout` / `--compare-stderr` 时也比较屏幕输出 / 错误输出）是否一致（退出码 0 一致 / 1 不一致 / 2 运行失败或参数有误） | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/reproduce_check.py" --cmd "python3 analysis_script.py" --outputs results/ --compare-stdout` |

已有数据的 AI/预测模型研究不经过 data-collection-tools：SAP 规定划分训练/验证/测试集时，直接调用护栏脚本 `python3 "${CLAUDE_PLUGIN_ROOT}/skills/data-collection-tools/scripts/patient_level_split.py" labels.csv --patient-col patient_id --label-col label`，不要现写划分代码。

**分析代码必须能脱离插件复现**（论文的代码公开后，别人没有这个插件）：`analysis_script.py` 里要用前提检验函数时，先把脚本复制进项目根目录，再从项目里的副本 import；不要从插件安装路径 import，也不要往 `sys.path` 里塞插件目录：

```bash
cp "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/assumption_tests.py" .
```

```python
from assumption_tests import full_check, effect_size_cohens_d   # 项目根目录里的副本
```

副本随分析代码一起保存和公开，`analysis-log.md` 记下它的来源与 sha256。只在命令行跑一次、结果写进日志的检查（`data_profile.py`、`reproduce_check.py`）直接用插件路径即可。

## Workflow

### Step 0: 核对前置条件

1. 读取 `analysis-plan.md`（`status: confirmed`，auto 模式的 `confirmed_by: auto` 同样有效），列出全部计划分析（主要、次要、亚组、敏感性）及各自的 SAP 编号、方法、前提假设。快速 SAP 只写了描述性部分（如只为 Table 1）时，本次就只执行这些条目；要加结局分析见 When NOT to Use
2. 确认原始数据文件存在（默认 `data.csv`，也可能是 xlsx 或多张表），变量名与 SAP 一致
3. 没有已确认的 SAP → 不做确证性分析：告诉用户，转 `data-analysis-planning`（已有数据走快速路径：研究问题、分组变量等问题和 SAP 草稿一次给用户，确认一次）；用户只想先看看 → 只做标明 exploratory 的分析，记进 `analysis-log.md` 并按总调度结局盲规则在状态文件里留 note（写 SAP 时照录进第 1 节）。找不到数据 → 问用户

### Step 1: 数据体检并对照 SAP

1. 运行体检。计划阶段体检过也要再跑——数据可能已更新；报告里的 sha256 可与计划阶段的 `data-profile.md` 对比：
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/data_profile.py" data.csv \
     --id patient_id --outcome <主要结局列> --report data-profile.md
   ```
   被当成 ID 的整数列其实是测量值（费用、计数）时加 `--not-id <列>` 重跑；列名里有换行的用空格代替。`--id <患者ID列>` 每次都要给；数据每行一名患者、又没有患者 ID 列时，用 `--rows-are-patients` 代替。两者都不给时，脚本只按列名尽力自动认一列患者 ID（列名像患者 ID、取值在多行重复、10 个以上取值、不像就诊/随访序号，且只有一列符合；报告开头写明用了哪列）——这只是方便，可能认错或认不出；认不出时报告不显示任何分类取值，只给取值个数和分布形状，问题清单会提示要加哪一个。某个缺失码只适用于一列时写 `--missing-tokens 列名=取值`（如 `--missing-tokens age=0`）；对所有列追加的数字不会用在 0/1 编码列和该数字落在取值范围之内或紧挨着它的列（问题清单会写明没有用在哪些列）。
2. 逐条核对 SAP 第 1 节的假设：样本量与患者数、结局事件数、关键变量的缺失比例与形式、聚类结构（每人几条记录、几个中心/术者）、变量名与编码、单位。前瞻性研究按 SAP 写好的预案核对。
3. 不符合时：

| 偏差 | 处理 |
|------|------|
| 不影响主要分析的小偏差（例：次要变量多了一种缺失写法、缺失比例略高于预期，但对缺失机制的判断和 SAP 所选的处理方式不变） | 记入 `analysis-log.md`，继续 |
| 影响主要分析方法或主要结局（例：事件数远少于计划、发现同一患者多条记录而 SAP 按独立样本设计、主要结局缺失远超预期） | SAP 写了这种情况的预案或预定备选 → 告诉用户，按预案做并记为偏离；没写 → **停下来**，向用户说明情况，回 `data-analysis-planning` 由用户决定是否修订 SAP；修订要记录版本、日期和理由 |

4. 样本量复核（只复核先验）：`power_analysis.py` 只用来核对 protocol 里的先验计算（参数是否抄对、实际入组与事件数是否达到）。**禁止用观察到的效应量算"事后 power"**——它只是 p 值的换算，审稿人会直接指出。样本不足如实写进 Limitations。
5. 这一步只看结构和质量（结局盲），**不看组间结果**。

### Step 2: 现写清洗代码（按 SAP 第 2 节）

根据体检结果和 SAP 第 2 节现写，放在 `analysis_script.py`（或 `.R`）开头或单独的清洗脚本里：
- 常见动作：把"未查""/"等写法转成缺失（`999` 这类数字码只在数据字典确认它代表缺失的那几列转换，不要全表统一替换）；"<0.1" 按 SAP 规定处理；统一单位与编码；合并多张表；按患者汇总；生成派生变量
- 每个动作在代码注释（`# SAP 2.x: ...`）和 `data-cleaning-log.md` 里写明对应的 SAP 条目和影响的行数
- 原始数据永不修改；清洗后另存（如 `data_clean.csv`），后续分析只读清洗后的数据
- SAP 没写到的清洗需求：小问题处理后记为偏离；影响主要分析的按 Step 1 第 3 点停下来
- **缺失数据**：按 SAP 已选的策略执行；写代码前读要点卡 `${CLAUDE_PLUGIN_ROOT}/skills/data-analysis-planning/references/method-cards/missing-data.md`（m 的取法、Rubin 合并公式、Little 检验的实现都在卡里）。硬规矩：多重插补 = m 份、各自分析、Rubin 规则合并——sklearn `IterativeImputer` 跑一次只是单次插补
- **异常值**：只按 SAP 预先规定处理（保留并标注 / Winsorize / 移除 + 敏感性分析），**禁止不说明理由地删除**
- 产出：清洗后数据 + `data-cleaning-log.md`（格式见 `references/output-templates.md` §1）

### Step 3: 前提假设诊断

方法已由 SAP 定好（独立两组默认 Welch t 检验），这一步只诊断，不按检验的 p 值重新挑方法：

```python
result = full_check(group1, group2, paired=False)    # 或 paired=True（按完整配对过滤、看差值分布）
print(result)                                         # 诊断结果写进 analysis-log.md
```

看残差图、Q-Q 图和脚本输出（检验的 p 值只作描述：小样本查不出问题，大样本微小偏离也"显著"）。诊断显示计划方法明显不适合时，才换 SAP 写好的备选方法并记为偏离；SAP 没写备选 → 按 When NOT to Use 回 `data-analysis-planning`。方法对照表：`${CLAUDE_PLUGIN_ROOT}/skills/data-analysis-planning/references/stat-method-decision-tree.yaml`。

### Step 4: 现写分析代码（按 SAP 逐条）

先主要分析，再次要、亚组、敏感性。写每一类分析之前先读对应的方法要点卡（`${CLAUDE_PLUGIN_ROOT}/skills/data-analysis-planning/references/method-cards/<file>.md`，SAP 第 4 节写了用哪几张），按卡里推荐的成熟包和"常见的坑"来写。语言用 `preferred_stats_tool` 对应的 R 或 Python（偏好 SPSS/Stata 时也生成可复现的 R/Python 脚本）。

写代码的规矩：
1. 开头记录运行环境与包版本（Python/R 版本，以及用到的 pandas、statsmodels、lifelines 或 R 包的版本）
2. 固定并打印随机种子（bootstrap、插补、交叉验证、机器学习都要）
3. 只读清洗后的数据，不碰原始数据；不打印患者级的行（`df.head()`、逐例列表），只打印汇总
4. 每段代码开头注释 `# SAP x.y: <分析名>`，与 SAP 条目一一对应
5. **每个结果都写进结果文件**（`results/` 下的表格 `.csv` 或 `.json`——`results/` 只放分析脚本写出的结果，分析要读的文件如 AI 模型的推理输出放 `data/model_outputs/`：估计值、95% CI、p、n、事件数，位数不少于论文里要报告的位数）；同时可按统一格式打印（如 `[SAP 4.1] Cox: HR=…, 95% CI …–…, p=…, n=…, events=…`）方便查看。只打印在屏幕上的数字不能进 `results-summary.md` 或论文——Step 5 的重跑检查默认只比较文件
6. 不在代码里硬写从结果里抄来的数字：样本量、阈值、系数都由代码算出或来自 SAP
7. 每一步的人数（纳入、排除及原因、清洗后、进入每个分析）写进结果文件（如 `results/flow.csv`）并打印，供 Step 5 核对
8. 输出文件名固定；文件和屏幕输出里都不写运行时间、进度条这类每次不同的内容，方便重跑比较

每个推断分析必须报告：

| 必须报告 | 说明 |
|---------|------|
| 统计量 + 值 | 如 t=2.35, F=4.12, χ²=8.91 |
| p 值 | 精确值，如 p=0.023（p<0.001 时写 p<0.001） |
| 效应量 | Cohen's d / OR / HR / η² 等 |
| 95% CI | 效应量的置信区间 |
| 样本量 | 每组 n（含缺失后实际进入分析的 n）；生存分析另报事件数 |

解读时不拿 0.05 当硬界线：p=0.06 既不写"接近显著 / 有趋势"，也不写成"没有差异 / 无效"——报效应量、95% CI 和精确 p，说明 CI 覆盖的范围（含哪些临床上有意义的效应），结论按 CI 和临床意义下。

**SAP 之外的新分析**（审稿人要求，或用户临时想加；补全只有描述性部分的 SAP 不算，见 When NOT to Use）：在本 skill 做，不改 SAP 原文——先在 `analysis-log.md` 写明这个分析的定义（问题、方法及理由、由谁要求），代码段注释 `# post hoc: …`，结果单独呈现并标 post hoc / exploratory，不改写成主要结论。

### Step 5: 自检（四项全部要做）

1. **重跑一致**：
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/statistical-analysis/scripts/reproduce_check.py" \
     --cmd "python3 analysis_script.py" --outputs results/ --compare-stdout --report reproduce-check.md
   ```
   通过 = 退出码 0、加了 `--compare-stdout`（结果写在 stderr 时再加 `--compare-stderr`）、报告"需要留意"里的项（`--outputs` 之外的缓存、运行日期）已处理。不一致时按报告提示修改（多半是没固定种子，或输出里写了时间），改完再跑。`--outputs` 只放分析写出的文件：输入（数据、配置、`data/model_outputs/` 里的模型推理输出）放进去会在检查前被移走。R 脚本、清洗单独成脚本时怎么串起来、`--exclude`、Office 文件的比较、`.reproduce-check/` 副本与 `--keep-last` 见 `references/reproduce-check-guide.md`。
2. **人数连得上**：纳入 → 排除（各原因）→ 清洗后 → 进入每个分析的人数前后对得上，能直接画出流程图（CONSORT / STROBE flow）；对不上要查清原因。
3. **SAP 对照表**：SAP 每一条 → 代码位置（文件名 + `# SAP x.y` 段）→ 结果位置（结果文件名 + 行/列，不能只写"屏幕输出"）；没做的写理由。
4. **偏离记录**：所有与 SAP 不同的地方（方法切换、SAP 里的分析没做或删掉、清洗规则变化）写进 `analysis-log.md` 的偏离表，注明理由和对结果的影响；SAP 之外新增的分析不算偏离，按 Step 4 末尾记在 Post hoc / Exploratory Analyses 表。

四项结果写进 `analysis-log.md` 的"SAP 对照表"和"自检结果"两节（`references/output-templates.md` §2）。任何一项不通过，不进入下一步。

### Step 6: 生成输出文件

按下方 Output 表生成文件；`results-summary.md` 里的数字全部来自脚本写出的结果文件，不手工改写。只出 Table 1 时，`results-summary.md` 只有样本特征一节。

### Step 7: 更新项目状态

输出 3–5 行摘要（产物、关键决策、自检结果、待注意），然后 `python3 ${CLAUDE_PLUGIN_ROOT}/skills/using-med-research-powers/scripts/mrp_state.py done statistical-analysis --output results-summary.md --output analysis-log.md --next figure-generation`，按 checkpoint_mode 进入 `figure-generation`。用户只要一部分结果（如只要 Table 1）时交付后停下，`--next` 写用户接下来要做的，摘要里提示下一步。

## Output

| 文件 | 必须 | 内容 | 模板 | 下游 |
|------|------|------|------|------|
| `data-profile.md` | 是 | 执行前的数据体检报告 | `data_profile.py` 生成 | Step 1 对照 SAP；`analysis-log.md` 引用 |
| `data-cleaning-log.md` | 是 | 每个清洗动作 → 对应 SAP 条目与影响行数；缺失、异常值、类型校正、重编码；清洗前后 N | `references/output-templates.md` §1 | `manuscript-writing` Methods 数据预处理段 |
| `analysis_script.py`（或 `.R`） | 是 | 清洗 + 分析的完整源代码；现写，结构要求见 Step 4 的规矩；用到的插件辅助脚本以副本形式放在项目里 | 无（按 Step 4 规矩现写） | `pre-submission-verification` Gate 2 |
| `analysis-log.md` | 是 | 前提检验、逐条执行记录、SAP 对照表、自检结果、与 SAP 的偏离、post hoc 分析的定义、敏感性分析、问题 | `references/output-templates.md` §2 | `pre-submission-verification` Gate 2 |
| `results-summary.md` | 是 | 样本特征、主要/次要/亚组/敏感性结果、Key Numbers、所需图表清单 | `references/output-templates.md` §3 | `figure-generation`、`manuscript-writing` Results、Gate 3 |

`results-summary.md` 的基线表：RCT 不填 p 值（随机化后差异只能来自机会），用标准化均数差 SMD 描述均衡性；观察性研究可报 p 值或 SMD。脚本写出的结果文件（`results/`）和 `reproduce-check.md` 一并保留。

## Common Mistakes

| 想法 | 现实 |
|------|------|
| "拿现成脚本改改变量名就跑" | 数据的编码、缺失形式、聚类结构不同，必须按体检结果现写 |
| "多做几个检验总有显著的" | p-hacking，必须做多重比较校正 |
| "用 Excel 算就行" | 生成可复现的 Python/R 脚本 |
| "不做敏感性分析也行" | 审稿人一定会要求，主动做 |

## Convergence

当以下条件全部满足时完成：
1. 执行前已体检并对照 SAP 第 1 节；影响主要分析的偏差已按 SAP 预案处理或由用户决定，并已记录
2. `analysis-plan.md` 中每个预定分析都已执行，或写明了没做的理由
3. 推断分析的前提假设已诊断，效应量 + 95% CI 已计算，SAP 规定的敏感性分析已完成（只做描述性条目时不适用）
4. Step 5 自检四项全部通过（重跑检查按第 1 项的标准）
5. Output 表中的文件全部生成，`.mrp-state.json` 已更新

## Red Flags — STOP

- 没有已确认的 SAP 却要做确证性分析 → 停，见 Step 0
- 体检发现与 SAP 假设不符、影响主要分析且 SAP 没有预案 → 停，回 `data-analysis-planning` 由用户决定
- 没做前提诊断就报结果 → 停，先看残差 / Q-Q 图并记录
- 只报告"显著"的结果 → 必须报告所有预定分析
- 在原始数据上直接分析或改写原始数据 → 停，走 Step 2
- 看到结果后想换方法 / 换主要结局 → 停，回 SAP 并记录偏离
- `reproduce_check.py` 不一致或运行失败还想往下走 → 停，先修

## 衔接规则

### 前置依赖（缺了按总调度"缺前置产物时"处理；SAP 是硬确认，见 Step 0）
- 已确认的 `analysis-plan.md`（`data-analysis-planning` 生成，硬确认 2）
- 数据文件（用户按 `data-collection-tools` 生成的工具收集完毕，或回顾性研究已有的数据）

### 强制衔接（不可跳过）
- 完成后 → `figure-generation`（读取 `results-summary.md` 的"Figures Needed"）
- 产物的下游（`manuscript-writing`、Gate 2）见 Output 表
- 最后一步固定为更新 `.mrp-state.json`（Step 7）

### 可选衔接
- 主要分析要换方法而 SAP 没有预定备选，或只有描述性 SAP 而要做结局分析 → 回 `data-analysis-planning` 修订 / 补全 SAP；SAP 之外的新分析（含 `revision-response` 转来的审稿人要求）→ 本 skill 按 Step 4 末尾做，标 post hoc / exploratory
- 结果报告规范检查 → `reporting-standards`（CONSORT / STROBE / TRIPOD 等）
