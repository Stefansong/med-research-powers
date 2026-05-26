---
description: Systematically search and synthesize research literature (PRISMA flow + gap map)
argument-hint: [research topic or PICO]
---

# Literature Synthesis

Systematically search and synthesize research literature.

Invoke the `literature-synthesis` skill, which contains the authoritative database-selection rules, search-strategy build (PICO → MeSH → Boolean), PRISMA screening flow, and thematic evidence synthesis. Pass through the user's topic: $ARGUMENTS

The skill produces 4 files: `search-strategy.md`, `screening-log.md`, `literature-references.md`, and `literature-synthesis-summary.md` (evidence map + gap analysis).

## Mandatory next step
After completion, proceed to `/study-design` or `/write-manuscript` (Introduction).
