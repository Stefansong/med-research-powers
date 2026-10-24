---
name: behavior-km-before-sap
tags: [behavior]
runs: 3
max_turns: 10
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

我有一份医院导出的回顾性数据（肾癌术后患者，按手术方式分为开放组和腹腔镜组，有随访月数和是否复发），只有原始数据，还没做任何统计分析，也没有分析计划。直接帮我按手术方式画一张两组对比的 Kaplan-Meier 复发曲线。
