# MRP State & Memory Schemas

This file holds the full JSON schemas for the two local state files the orchestrator maintains. The orchestrator SKILL.md keeps only a short pointer + key fields inline; consult this file when you need the complete structure.

Both files live in the **project directory** only, are never uploaded, and may be deleted by the user at any time.

---

## `.mrp-state.json` — Session / Pipeline State

Tracks research progress across sessions. On a new session, check for this file → if present, show "上次完成到 [current_stage]，下一步是 [next_skill]？".

Key fields: `project`, `current_stage`, `completed_skills[]`, `artifacts{}`.

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

---

## `.mrp-user-profile.json` — User Memory

Remembers identity, preferences, and history across sessions. Collected via conversation on first MRP use, then auto-updated.

Key fields: `profile.role`, `profile.research_domains[]`, `preferences.favorite_journals[]`, `preferences.preferred_stats_tool`, `history.skills_most_used[]`.

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
    "skills_most_used": ["study-design", "statistical-analysis", "manuscript-writing"]
  },
  "last_updated": "2026-04-02"
}
```
