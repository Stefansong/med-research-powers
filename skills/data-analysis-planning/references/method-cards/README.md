# 方法要点卡（Method Cards）

写分析计划（`data-analysis-planning`）和写分析代码（`statistical-analysis`）时，**只读用到的那几张**。

要点卡告诉你每种方法：计划前要先看数据的什么（只看结构和质量，不看与结局的关系）、计划里必须预先写明什么、用哪个成熟的 R / Python 包、常见的坑、结果必须报告什么、对应哪个报告规范。它们**不是代码模板**——代码要针对具体数据现写。

| 卡片 | 什么时候读 |
|------|-----------|
| [baseline-and-group-comparison.md](baseline-and-group-comparison.md) | 基线表（Table 1）、两组/多组比较、效应量 |
| [regression-and-prediction-models.md](regression-and-prediction-models.md) | 多因素回归（解释性）或临床预测模型、列线图、内部/外部验证 |
| [survival-analysis.md](survival-analysis.md) | KM、log-rank、Cox、竞争风险、不朽时间偏倚 |
| [propensity-score.md](propensity-score.md) | 观察性数据比较两种治疗：倾向性评分匹配或加权 |
| [missing-data.md](missing-data.md) | 任何分析里有缺失（含"/""未查"、999 这类伪装缺失） |
| [diagnostic-accuracy-and-ai-evaluation.md](diagnostic-accuracy-and-ai-evaluation.md) | 诊断试验、AI 模型评价、AI 与医生对比、读片者研究 |
| [clustered-and-repeated-data.md](clustered-and-repeated-data.md) | 同一患者多条记录、多中心、同一术者多台手术、视频多帧 |
| [meta-analysis.md](meta-analysis.md) | 系统综述的定量合并、诊断试验 Meta、偏倚风险与 GRADE |
| [agreement-and-reliability.md](agreement-and-reliability.md) | 评分者一致性、两种测量方法一致性、标注一致性 |
| [llm-vlm-evaluation.md](llm-vlm-evaluation.md) | 大语言模型 / 视觉语言模型的医学评测研究 |

每张卡的包名和函数名都核对过 CRAN / PyPI；个别参数只有较新版本才有，卡片里就地写明最低版本和旧版本的替代写法（如 `pairwise_tukeyhsd(..., use_var="unequal")` 要 statsmodels 0.15 及以上）。方法学规则在"参考"节给出文献与 DOI。发现过时或错误，按 CONTRIBUTING.md 提交修正并附出处。
