#!/bin/sh
# Med-Research-Powers session-start hook
# Fires on: startup, clear, compact
# Does NOT fire on: --resume (context already loaded)

cat <<'MRP_HOOK'
<session-start-hook>
<EXTREMELY_IMPORTANT>
You have Med-Research-Powers (MRP) — a medical research methodology framework.

**Before ANY research-related task, check if a MRP skill applies.**

## Quick routing

| User intent | Action |
|-------------|--------|
| 模糊的研究想法 / "我想研究..." | → research-question-formulation |
| 查文献 / 文献综述 / research gap | → literature-synthesis |
| 研究设计 / 样本量 / protocol | → study-design (clinical) or basic-medical-study-design (bench) or ai-medical-study-design (AI/ML) |
| 分析数据 / 用什么统计方法 | → data-analysis-planning THEN statistical-analysis |
| 画图 / Figure / 可视化 | → figure-generation |
| 写论文 / manuscript / Introduction | → manuscript-writing |
| 检查规范 / CONSORT / checklist | → reporting-standards |
| 模拟审稿 / reviewer | → peer-review-simulation |
| 审稿意见 / revision / 大修小修 | → responding-to-reviewers |
| 伦理 / IRB / 知情同意 | → research-ethics |
| 投哪个期刊 / 选刊 / impact factor | → journal-selection |
| cover letter / 投稿信 | → cover-letter-writing |
| 投稿系统 / 怎么投稿 / 上传 | → submission-system-guide |
| 怎么改 / 大修 / 小修 / revision | → revision-strategy THEN responding-to-reviewers |
| 并行 / 团队协作 / agent team | → team-collaboration |
| 写完了 / 可以投了 / 定稿 | → **pre-submission-verification (MANDATORY, 6-Gate)** |

## Rules

1. **1% Rule**: If there is even 1% chance a skill applies, invoke it.
2. **Read before acting**: Read the full SKILL.md — do NOT rely on the description alone.
3. **Never skip pre-submission-verification** before declaring a manuscript complete.
4. **Announce**: Say "Using [skill] to [purpose]" before invoking.
6. **Checkpoint**: 每个 skill 完成后，向用户报告生成的文件和关键发现，询问是否继续下一步。禁止静默跳转。
7. **Hard Checkpoint**: 研究方案确认、SAP 确认、目标期刊确认、投稿前检查确认——这 4 个节点必须获得用户明确确认。
8. **User Memory**: 启动时检查 `.mrp-user-profile.json`。存在 → 加载用户偏好（常投期刊、熟悉方法、图表风格）；不存在 → 首个 skill 触发前询问用户建立画像。
5. **CONSORT 2025**: CONSORT 2010 is officially superseded. Always use CONSORT 2025 (30 items).

## Slash commands

- /mrp:research-question — Formulate research question (PICO/FINER)
- /mrp:analyze-data — Plan and execute statistical analysis
- /mrp:write-manuscript — Write manuscript sections
- /mrp:check-standards — Check reporting standard compliance (MANDATORY pre-submission)
- /mrp:peer-review — Simulate peer review

</EXTREMELY_IMPORTANT>
</session-start-hook>
MRP_HOOK
