---
name: route-data-collection-inference
tags: [routing]
runs: 3
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

我们在做一个 AI 基准测试：比较 3 个本地部署的开源视觉语言模型（VLM）识别膀胱镜图像里肿瘤的准确率，研究方案和统计分析计划都已经确认了，模型的输出还没开始跑。帮我写批量调用这些模型的推理脚本，把每张图、每个模型的回答存下来。
