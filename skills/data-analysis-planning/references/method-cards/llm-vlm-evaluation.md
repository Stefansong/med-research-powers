# LLM/VLM 评测研究 — 方法要点卡

> 适用：用大语言模型（LLM）或视觉语言模型（VLM）回答医学问题、做诊断或分类、生成报告/摘要、看影像或手术视频作答的评测研究；多个模型之间、模型与医生之间的比较。　不适用：传统影像 AI 的分类/检测评价（看 `diagnostic-accuracy-and-ai-evaluation.md`）；模型训练或微调方案本身（按 `ai-ml-sap-extension.md`）；把 LLM 放进临床流程的前瞻性效果研究（按 RCT 或 DECIDE-AI 设计）。

## 1. 计划前先看数据的什么

只看结构和质量，**不先让模型试做测试题**来决定指标或提示词：
- 题目数与病例数：共多少道题，每个病例（视频/影像/病历）下有几道题（聚类结构）；题型（选择、判断、开放式）、专科、难度的分布。
- 参考答案：谁定的、依据什么（指南、病理、专家共识）；有争议或可能有多个正确答案的题有多少。
- 题目来源与公开时间：公开题库/考试/教材/网页，还是未公开或新构建；题目最早公开日期与各模型训练数据截止日期的先后（评估污染风险）。
- 输入形式：纯文本、单图、多图还是视频帧（抽几帧、分辨率）；输入长度是否超出某些模型的上下文限制；图像是否已去除可识别信息。
- 开放式回答要人工评分时：能找到几名评分者、每人能评多少条。
- 人类专家基线：可招募几名医生、年资分布。

## 2. 计划里必须预先写明

- **模型与版本**：每个模型的名称、具体版本号或快照、访问日期（起止）、接口（API 或网页端）、调用参数（温度、top_p、最大输出长度、种子〔如支持〕、系统提示词）；数据收集期间版本是否固定（TRIPOD-LLM 要求报告）。网页端可能自带系统提示、记忆或联网，优先用 API。
- **提示词**：主提示词全文事先定稿，只在另外的开发题上调试，不在测试题上改；另备 2–3 个改写变体（措辞、选项顺序、是否要求逐步推理）作敏感性分析。
- **重复运行**：每个模型每道题至少运行 3 次（本插件默认下限）；主要分析取哪一次或怎么汇总（多数票、每题平均正确率）事先定好；报告运行间一致性（各次答案完全相同的题目比例；把各次运行当"评分者"算 Fleiss' kappa）。
- **温度与种子**：固定在事先选定的值（一般就是实际使用时的设置）并报告，不看结果再调。温度设 0 或固定种子也不保证完全可复现，仍要重复运行。
- **污染检查**：逐题登记来源和公开时间，对照模型训练截止日期；尽量用未公开、新构建的题或真实病例；公开题与新题分开报告；排除不了污染时写进局限性。
- **答案解析规则**：怎样从输出里提取答案（规则/正则/人工）；拒答、给出多个答案、格式错误怎样计分（算错，或单列一类）；解析时对模型身份设盲；报告解析失败率。
- **主要指标**：准确率及 95% CI——题目相互独立时用 Wilson 法；题目嵌套在病例/视频内时按病例聚类（按病例重抽样的 bootstrap 或 GEE，Miller 2024）；按题型、专科、难度分层报告。
- **模型比较**：同一套题上做配对比较——McNemar 检验（不一致的题目对少时用精确法），或以题目（有聚类时以病例）为单位的配对 bootstrap 求准确率差值的 CI；每题多次运行时，用"题目"作随机效应的混合模型，或用每题平均正确率做配对分析（Miller 2024）。
- **多重比较**：事先指定一个主要比较（如目标模型 vs 最强的对照模型）；其余"模型 × 指标"的比较用 Holm 校正或标为探索性；≥ 3 个模型可先做 Cochran's Q 总体检验。
- **开放式回答的人工评分**：≥ 2 名评分者；对模型身份（以及答案来自模型还是人）设盲，呈现顺序随机；评分细则（维度、Likert 级数及每级定义）事先写好并做校准培训；报告评分者间一致性（加权 kappa / ICC，见 `agreement-and-reliability.md`）；分歧由第三名资深评分者裁决或讨论达成共识（Tam 2024）。用 LLM 当裁判时：先在一部分样本上与人工评分比对一致性，一致性不够就不能替代人工；对裁判隐去答案出自哪个模型；两两比较时随机调换两个答案的先后位置（或两种顺序各评一次）；尽量用与被评模型不同来源的裁判模型；检查裁判是否偏爱更长的回答（按回答长度分层看评分）；裁判模型的版本、提示词和调用参数同样固定并报告。
- **人类专家基线**：同一套题、同样的输入信息和时间限制、是否允许查资料；专家人数与年资；专家的准确率及 CI，并与模型做配对比较。
- **样本量**：按预期准确率和可接受的 CI 宽度，或按两个模型的预期差值做配对比例的功效计算。
- **准确率之外**：按研究问题预先选定——有害或错误信息、拒答率、校准（模型给出置信度时；预先写明置信度怎么得到——模型用文字自报的把握程度、输出词元的概率〔token log-probabilities，网页端通常拿不到〕、还是多次采样后答案的一致比例；三种来源含义不同，不能混用）、不同语言/人群间的差异（Bedi 2025：多数评测只报准确率，少用真实病例数据）。

## 3. 写代码：推荐的成熟包

| 任务 | R | Python |
|---|---|---|
| 准确率 + CI | `binom::binom.confint(x, n, methods = "wilson")`；`DescTools::BinomCI(x, n, method = "wilson")` | `statsmodels.stats.proportion.proportion_confint(k, n, method="wilson")` |
| 按病例聚类的 CI | 按病例重抽样的 bootstrap（现写，B ≥ 2000）；或 `geepack::geeglm(correct ~ 1, id = case_id, family = binomial)` | 同左现写；或 `statsmodels.formula.api.gee("correct ~ 1", groups="case_id", data=df, family=sm.families.Binomial())` |
| 两模型配对比较 | `exact2x2::mcnemar.exact(tab)`；`mcnemar.test(tab)` | `statsmodels.stats.contingency_tables.mcnemar(tab, exact=True)`；题目独立时差值 CI：`scipy.stats.bootstrap((a, b), 差值函数, paired=True)` |
| ≥ 3 个模型总体检验 | `DescTools::CochranQTest(y, groups, blocks)` | `statsmodels.stats.contingency_tables.cochrans_q(x)` |
| 每题多次运行（题目随机效应） | `lme4::glmer()`（公式见表下） | 无公认成熟的频率学派实现，建议用 R；或 GEE（`groups="question_id"`） |
| 多重比较校正 | `p.adjust(p, method = "holm")` | `statsmodels.stats.multitest.multipletests(p, method="holm")` |
| 运行间 / 评分者间一致性 | `irr::kappam.fleiss()`；`irr::kappa2(r, weight = "squared")`；`irr::icc()` | `statsmodels.stats.inter_rater.fleiss_kappa()`；`sklearn.metrics.cohen_kappa_score(weights="quadratic")`；`pingouin.intraclass_corr()` |

```r
lme4::glmer(correct ~ model + (1 | question_id), family = binomial, data = d)  # 每题多次运行
```

## 4. 常见的坑

- 只写"ChatGPT"，不写版本和访问日期；在网页端测试（带记忆、联网或内置提示），结果无法复现。
- 每题只跑一次，把单次结果当确定值；或跑了多次只报最好的一次。
- 在测试题上反复改提示词，再用同一套题报告结果——等于在测试集上调参。
- 用公开考试题或教材题，不做污染评估就宣称"模型具备临床推理能力"。
- 答案解析规则事后才定，或不同模型用不同规则；拒答和格式错误的计分不统一。
- 同一套题上比较两个模型却用独立样本卡方检验（应配对）。
- 同一病例下的多道题当独立样本算 CI。
- 比较了很多模型和指标，只报显著的差异。
- 人工评分时评分者知道答案出自哪个模型；只有 1 名评分者；只报裁决后的分数。
- 用 LLM 当裁判却不和人工评分比对，也不控制答案位置、回答长度和"裁判偏爱自家模型"这些偏差。
- 只与 1–2 名医生比较，就下"模型优于医生"的结论。

## 5. 结果必须报告

- 模型清单表：名称、版本/快照、访问日期、接口、调用参数、系统提示词。
- 提示词全文（可放附录）、答案解析规则；题目来源、公开时间与污染风险评估。
- 题目数、病例数，题型/专科/难度分布；参考答案的产生方式。
- 各模型准确率及 95% CI（CI 方法、是否按病例聚类），分层结果。
- 重复运行一致性；提示词变体的敏感性分析结果。
- 模型间差值及 95% CI、P 值和多重比较校正方法。
- 人工评分：评分者人数与资质、盲法、评分细则、评分者间一致性、裁决方式；用 LLM 当裁判时，报告裁判模型与版本、它与人工评分的一致性、做了哪些偏差控制。
- 报告校准时写明置信度的来源和计算方式。
- 人类专家基线及比较；错误类型分析（幻觉、遗漏、有害建议）；拒答率和解析失败率。
- 代码、提示词、可公开的题目与模型输出的获取方式。

## 6. 对应报告规范

- `tripod-llm`（TRIPOD-LLM 2025）：仓库索引有条目，暂无本地清单。按官方网站 https://tripod-llm.vercel.app/ 的最新版逐条人工核对，并注明所用版本（它是持续更新的"活文档"）。
- 评价聊天机器人给出的健康建议、总结临床证据（医学问答类研究）：另按 CHART（Chatbot Assessment Reporting Tool，2025；12 条 39 小条，含模型标识、提示词工程、提问策略、样本量）逐条核对。仓库索引无条目、无本地清单，按原文人工核对。
- VLM 处理医学影像：另按 `claim`（CLAIM 2024）核对图像来源、预处理和参考标准相关条目。
- 以诊断准确性为框架的评测：`stard`；进入临床流程的早期评价：`decide-ai`。

## 参考

- CHART Collaborative. Reporting guideline for chatbot health advice studies: the Chatbot Assessment Reporting Tool (CHART) statement. *BMJ Med*. 2025;4(1):e001632. doi:10.1136/bmjmed-2025-001632
- Gallifant J, Afshar M, Ameen S, et al. The TRIPOD-LLM reporting guideline for studies using large language models. *Nat Med*. 2025;31(1):60-69. doi:10.1038/s41591-024-03425-5
- Miller E. Adding error bars to evals: a statistical approach to language model evaluations. arXiv:2411.00640 [预印本]. 2024. doi:10.48550/arXiv.2411.00640
- Tam TYC, Sivarajkumar S, Kapoor S, et al. A framework for human evaluation of large language models in healthcare derived from literature review. *NPJ Digit Med*. 2024;7(1):258. doi:10.1038/s41746-024-01258-7
- Bedi S, Liu Y, Orr-Ewing L, et al. Testing and evaluation of health care applications of large language models: a systematic review. *JAMA*. 2025;333(4):319-328. doi:10.1001/jama.2024.21700
