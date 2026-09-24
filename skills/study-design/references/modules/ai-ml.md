# Module C — AI/ML Medical Research（医学人工智能研究）

> **本模块是必须覆盖的清单，不是填空表：按本研究的实际情况写；不适用的条目写"不适用 + 理由"；禁止照抄示例中的数字、例数和措辞。**

`study-design/SKILL.md` 的 Study Type Router 判定为 `type: ai-ml` 时读取本文件。
这里只放 AI/ML 研究特有的判断；通用 Workflow（Step 0 分析真实条件 + Step 1–5）、Output、Hard Checkpoint、衔接规则都在 SKILL.md。

## 适用范围

医学影像 AI、手术视频 AI、临床预测模型、LLM/VLM 评估、数字健康、医学 NLP、智能医疗器械。

## 研究类型决策树

```
研究目标？
├── 开发新 AI 模型？
│     ├── 有临床验证？ → 开发+验证研究（TRIPOD+AI；外部验证）
│     └── 仅技术验证？ → 技术开发研究（仍需独立测试集）
├── 评估已有 AI 模型/工具？
│     ├── 诊断准确性？ → STARD 2015（STARD-AI 无本地清单，需人工核对）
│     ├── 临床效果？ → RCT（CONSORT 2025 + CONSORT-AI 2020）
│     ├── 多模型对比 / LLM 评估？ → Benchmark（TRIPOD-LLM）
│     ├── 可用性？ → 人因工程（混合方法，定性部分走 Module D）
│     └── AI 决策支持早期评估？ → DECIDE-AI 2022
├── 构建数据集/标注体系？
│     ├── 影像数据集？ → Datasheets for Datasets（无本地清单，需人工核对）
│     ├── 视频标注？ → 标注一致性（Kappa/ICC）
│     └── Benchmark 集？ → Benchmark 论文
├── 开发新设备/传感器？
│     ├── 按 IDEAL 框架定位阶段
│     ├── Stage 1 原理验证 → Bench-top
│     ├── Stage 2a-2b 可行性 → Pilot / 前瞻性队列
│     └── Stage 3 对比验证 → RCT / Bland-Altman
└── 综合 AI 医学证据？
      ├── 系统综述 → PRISMA 2020 + PRISMA-S
      └── Meta 分析 → PRISMA 2020 + QUADAS-2 / PROBAST
```

## Core Design Elements

### 1. Dataset

- 训练/验证/测试必须独立（禁止 data leakage）
- 同一患者的数据不能分在训练和测试集（患者级划分）
- 优先外部验证（不同中心/时间段）
- 必须报告：来源、时间范围、纳入排除标准、数据量、类别分布、去标识化方式

**数据划分策略（按样本量分档）** 只维护一份，在
`${CLAUDE_PLUGIN_ROOT}/skills/data-analysis-planning/references/stat-method-decision-tree.yaml` 的
`deep_learning_training.data_split`。分档边界：`n > 1000` / `200 ≤ n ≤ 1000` / `50 ≤ n < 200` / `n < 50`。
这里的 n 是 SKILL.md Step 0 查到的真实可用患者数（排除后），不是计划中的理想数。
设计时读取该表决定 hold-out / K-fold / 迁移学习 + nested CV / LOOCV，并注意：
- K-fold 中同一患者的所有数据必须在同一折；报告每折性能和整体均值±SD
- 使用迁移学习时报告预训练数据集和微调策略
- n < 50 时深度学习样本不足：外部验证为**强制**项，并在 Limitations 充分讨论

### 2. Ground Truth

- 标注者资历和数量
- 标注一致性（Cohen's Kappa / Fleiss' Kappa / ICC）
- 争议解决机制（共识讨论 / 多数投票 / 专家裁决）
- 标注流程是否盲法（标注者不知道模型输出和其他标注者结果）

### 3. Performance Metrics

按任务类型选择指标 → 读取 `references/metrics-and-reporting.yaml`（分类 / 检测分割 / LLM-VLM / 连续回归 `regression` / 风险预测 `risk_prediction` / 公平性 / 稳健性 / 校准）。
风险预测类必须同时报告区分度（AUROC）、校准（校准曲线、Brier）和临床净获益（DCA）。

### 4. Human-AI Comparison

- 相同信息输入（公平对比条件）
- 说明专家水平（年资、例数）
- 最好三组：AI alone / Human alone / AI-assisted Human
- 阅片 washout period

### 5. Reproducibility

- 代码开源（GitHub + DOI via Zenodo）
- 模型权重共享或推理 API
- 环境配置（requirements.txt / Docker）
- 随机种子固定，并记录划分种子

### 6. Prompt 标准化（LLM / VLM 研究必写）

- 每个任务的 Prompt 全文、变体（简洁 / 标准 / 详细）用于敏感性分析
- 推理参数：temperature、max_tokens、seed、重复次数
- 模型版本与访问日期（API 模型会静默更新）
- 输出解析规则（MCQ 抽取、开放题评分标准）
- 这一章节会被 `data-collection-tools` 直接读取生成 Prompt 模板与推理脚本

### 7. Data Augmentation（数据增强）

- 必须在 protocol 中预先规划增强策略
- 几何变换：rotation, flip, scaling, elastic deformation
- 强度变换：brightness, contrast, noise, blur, gamma correction
- 高级增强：CutMix, MixUp（如适用）
- 报告要求：所有增强类型、参数范围、应用概率
- **禁止在测试集上做增强**（TTA 除外，需单独说明）

### 8. Class Imbalance Handling（类别不平衡处理）

- 在 protocol 中报告各类别样本量和比例
- 策略选择：

  | 方案 | 方法 | 适用场景 |
  |------|------|---------|
  | 数据层面 | Oversampling (SMOTE) / Undersampling | 中度不平衡 (1:3~1:10) |
  | 损失函数 | Weighted CE / Focal Loss / Dice Loss | 严重不平衡 (>1:10) |
  | 采样策略 | Balanced batch sampling | 训练时平衡各类别 |
  | 评估层面 | **不用 Accuracy**，用 AUROC/AUPRC/F1 | 所有不平衡场景 |

- 必须在 Methods 中报告采用的策略和理由

### 9. Model Interpretability / Explainability（模型可解释性）

- **临床 AI 研究必须报告可解释性**（DECIDE-AI 要求）
- 方法选择：

  | 任务 | 方法 | 用途 |
  |------|------|------|
  | 分类 | Grad-CAM, SHAP, Attention maps | 模型关注区域可视化 |
  | 分割 | Uncertainty maps, Attention maps | 预测置信度可视化 |
  | 预测 | SHAP, LIME, Feature importance | 特征贡献度分析 |

- 报告要求：至少 3-5 例典型案例（typical / best / worst case）的可解释性可视化；如有条件，邀请临床医生评估可解释性输出是否可理解

## Reporting Standards

研究类型 → 规范映射在 `references/metrics-and-reporting.yaml` 的 `mapping` 部分（名称与 `reporting-standards` 索引一致；标注"无本地清单"的需人工核对）。
影像 AI 统一用 **CLAIM 2024（44 项）**，CLAIM 2020 已被取代。

## Common Mistakes（AI/ML 特有）

| 想法 | 现实 |
|------|------|
| "Accuracy 95% 说明模型很好" | 类别不平衡时 Accuracy 毫无意义，必须看 AUROC/AUPRC |
| "训练集上效果好就行" | 没有独立测试集/外部验证的结果不可信 |
| "数据随机划分就行" | 同一患者不能同时在训练和测试集 |
| "AUROC 高就有临床价值" | 必须做校准 + DCA 评估临床净获益 |
| "这是 AI 研究不需要临床规范" | 需要同时满足技术和临床两套规范 |
| "我的器械直接做 RCT" | 先用 IDEAL 定位阶段，Stage 1-2 不适合 RCT |
| "黑箱模型也能发表 / AI 评估不用报告可用性" | DECIDE-AI 要求报告可解释性、人机交互和用户体验 |
| "数据增强不需要报告" | 增强策略和参数必须完整报告，可复现 |
| "200 例够 train/val/test 三分了" | 200 例应考虑 5-fold CV + 迁移学习 |
| "LLM 的 prompt 随手写就行" | Prompt、参数、模型版本都是方法的一部分，必须标准化并报告 |

## Convergence（AI/ML 特有完成条件）

1. 研究类型已明确，对应报告规范已确定
2. 数据集方案完整（来源、纳排、患者级划分、标注流程与一致性、Ground Truth 定义）
3. 评估指标已选择并有依据（风险预测含校准与 DCA）
4. 外部验证计划已写明（或说明为何暂无并列入 Limitations）
5. 人机对比方案已设计（如适用）
6. 可复现性方案已规划（seed / 代码 / 环境）；LLM 研究已写 Prompt 标准化章节

## Red Flags（AI/ML 特有）

- **禁止患者级泄漏**：同一患者数据跨训练/测试集
- **禁止只报训练集或内部验证的性能就宣称"可临床应用"**
- **禁止用 Accuracy 作为不平衡数据的主要指标**
- **禁止 LLM 研究不记录模型版本、prompt 与推理参数**
