# Writing MRP Skills

Invoke the `writing-mrp-skills` skill to learn how to create or improve MRP skills.

## SKILL.md Structure

```yaml
---
name: kebab-case-name
description: "Use when [condition]. Triggers on [keywords]."
---
```

## Required Sections
1. **Overview** — one sentence
2. **When to Use / When NOT to Use** — clear boundaries
3. **Workflow** — step-by-step with concrete outputs
4. **Common Mistakes** — table format (想法 | 现实)
5. **Convergence** — when to stop (numbered conditions)
6. **Red Flags — STOP** — hard blocks
7. **衔接规则** — upstream dependencies + downstream handoffs

## Rules
- Do NOT summarize workflow in the description
- Keep SKILL.md self-contained (don't require reading other files to understand)
- Include concrete output file templates
- Test with at least 1 real scenario before contributing
