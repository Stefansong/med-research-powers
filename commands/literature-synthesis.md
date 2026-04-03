# Literature Synthesis

Invoke the `literature-synthesis` skill to systematically search and synthesize research literature.

## Workflow

### Step 1: Select databases
Based on research type, choose database combination (minimum 2; systematic reviews minimum 3):
- **PubMed** (PubMed MCP) — biomedical core
- **arXiv** (WebSearch) — AI/ML algorithms
- **Cochrane** (WebSearch) — systematic reviews
- **IEEE/ACM** (WebSearch) — engineering/CS
- **medRxiv/bioRxiv** (WebSearch) — preprints

### Step 2: Build search strategy
PICO → keywords → MeSH + free text + Boolean operators → execute per database.

### Step 3: Screen (PRISMA flow)
Deduplicate → title/abstract screening → full-text screening → snowball search → final inclusion.

### Step 4: Evidence synthesis
Organize by theme (not chronology): Known → Unknown → Controversial → Research gap.

## Output (4 files)
- `search-strategy.md` — reproducible search queries per database
- `screening-log.md` — PRISMA flow diagram data (counts + exclusion reasons)
- `literature-references.md` — structured record per included study
- `literature-synthesis-summary.md` — evidence map + gap analysis

## Mandatory next step
After completion → `study-design` or `manuscript-writing` (Introduction).
