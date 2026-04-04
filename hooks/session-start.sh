#!/bin/bash
# Med-Research-Powers — dynamic session-start hook
# Fires on: startup, clear, compact
# Does NOT fire on: --resume (context already loaded)

# ── 1. Collect state ──────────────────────────────────────────────────────────

HAS_JQ=false
command -v jq &>/dev/null && HAS_JQ=true

# Project state (.mrp-state.json in current directory)
STAGE="" ; PROJECT="" ; TARGET_JOURNAL="" ; COMPLETED=""
if [ -f ".mrp-state.json" ] && $HAS_JQ; then
  STAGE=$(jq -r '.current_stage // ""' .mrp-state.json 2>/dev/null)
  PROJECT=$(jq -r '.project // ""' .mrp-state.json 2>/dev/null)
  TARGET_JOURNAL=$(jq -r '.target_journal // ""' .mrp-state.json 2>/dev/null)
  COMPLETED=$(jq -r '[.completed_skills[].skill] | join(" → ")' .mrp-state.json 2>/dev/null)
fi

# User profile (.mrp-user-profile.json in current dir, then home)
PROFILE=""
[ -f ".mrp-user-profile.json" ] && PROFILE=".mrp-user-profile.json"
[ -z "$PROFILE" ] && [ -f "$HOME/.mrp-user-profile.json" ] && PROFILE="$HOME/.mrp-user-profile.json"

USER_NAME="" ; FAV_JOURNAL="" ; STATS_TOOL=""
if [ -n "$PROFILE" ] && $HAS_JQ; then
  USER_NAME=$(jq -r '.profile.name // ""' "$PROFILE" 2>/dev/null)
  FAV_JOURNAL=$(jq -r '.preferences.favorite_journals[0].name // ""' "$PROFILE" 2>/dev/null)
  STATS_TOOL=$(jq -r '.preferences.preferred_stats_tool // ""' "$PROFILE" 2>/dev/null)
fi

# Artifact detection (infer stage when no .mrp-state.json)
ARTIFACTS=""
[ -f "research-question.md" ]        && ARTIFACTS="$ARTIFACTS rq"
[ -f "study-protocol.md" ]           && ARTIFACTS="$ARTIFACTS protocol"
[ -f "journal-selection-report.md" ] && ARTIFACTS="$ARTIFACTS journal"
[ -f "analysis-plan.md" ]            && ARTIFACTS="$ARTIFACTS sap"
[ -f "results-summary.md" ]          && ARTIFACTS="$ARTIFACTS results"
[ -d "manuscript" ]                  && ARTIFACTS="$ARTIFACTS manuscript"
[ -f "submission-readiness-report.md" ] && ARTIFACTS="$ARTIFACTS submission"

# Environment check
ENV_WARN=""
python3 -c "import docx" 2>/dev/null || ENV_WARN="⚠️  python-docx not installed — manuscript-export unavailable (pip install python-docx)"

# ── 2. Determine recommended next step ────────────────────────────────────────

NEXT=""
case "$STAGE" in
  "research-question-formulation") NEXT="literature-synthesis 或 study-design" ;;
  "literature-synthesis")          NEXT="study-design" ;;
  "study-design")                  NEXT="data-collection-tools + journal-selection + data-analysis-planning" ;;
  "data-collection-tools")         NEXT="data-analysis-planning" ;;
  "journal-selection")             NEXT="data-analysis-planning" ;;
  "data-analysis-planning")        NEXT="statistical-analysis" ;;
  "statistical-analysis")          NEXT="figure-generation" ;;
  "figure-generation")             NEXT="manuscript-writing" ;;
  "manuscript-writing")            NEXT="manuscript-export → peer-review-simulation" ;;
  "manuscript-export"|"peer-review-simulation") NEXT="pre-submission-verification (MANDATORY)" ;;
  "pre-submission-verification")   NEXT="submission-preparation" ;;
  "submission-preparation")        NEXT="revision-response (等待审稿意见后)" ;;
  "revision-response")             NEXT="流程完成 ✅" ;;
  *)
    # Infer from artifacts when no state file
    if echo "$ARTIFACTS" | grep -q "submission"; then
      NEXT="submission-preparation"
    elif echo "$ARTIFACTS" | grep -q "manuscript"; then
      NEXT="manuscript-export 或 peer-review-simulation"
    elif echo "$ARTIFACTS" | grep -q "results"; then
      NEXT="manuscript-writing"
    elif echo "$ARTIFACTS" | grep -q "sap"; then
      NEXT="statistical-analysis"
    elif echo "$ARTIFACTS" | grep -q "journal"; then
      NEXT="data-analysis-planning"
    elif echo "$ARTIFACTS" | grep -q "protocol"; then
      NEXT="journal-selection + data-analysis-planning"
    elif echo "$ARTIFACTS" | grep -q "rq"; then
      NEXT="study-design"
    fi
    ;;
esac

# ── 3. Output to Claude context ───────────────────────────────────────────────

echo '<session-start-hook>'
echo '<EXTREMELY_IMPORTANT>'
echo 'You have Med-Research-Powers (MRP) v6.2.1 — medical research methodology framework.'
echo '**Before ANY research-related task, check if a MRP skill applies (1% Rule).**'

# ── Project status block ──────────────────────────────────────────────────────
if [ -n "$PROJECT" ] || [ -n "$ARTIFACTS" ]; then
  echo ''
  if [ -n "$PROJECT" ]; then
    echo "## Resuming: $PROJECT"
  else
    echo '## Project files detected in current directory'
  fi
  [ -n "$STAGE" ]          && echo "Current stage : $STAGE"
  [ -n "$TARGET_JOURNAL" ] && echo "Target journal: $TARGET_JOURNAL"
  [ -n "$COMPLETED" ]      && echo "Completed     : $COMPLETED"
  if [ -n "$NEXT" ]; then
    echo ''
    echo "**→ Recommended next step: $NEXT**"
    echo ''
    echo 'Continue from here, or describe a new task.'
  fi
else
  # New project — full routing table
  cat <<'ROUTING'

## New project — skill routing

| User intent | Skill |
|-------------|-------|
| 模糊的研究想法 / "我想研究..." | research-question-formulation |
| 查文献 / 文献综述 / research gap | literature-synthesis |
| 研究设计 / 样本量 / protocol | study-design (clinical/bench/AI-ML/qualitative/survey) |
| 数据收集工具 / CRF / 推理脚本 / 标注表 | data-collection-tools |
| 分析数据 / 统计方法 | data-analysis-planning → statistical-analysis |
| 画图 / Figure / 可视化 | figure-generation |
| 写论文 / manuscript | manuscript-writing |
| 导出Word / 排版 / docx | manuscript-export |
| 查PubMed / 引用验证 / PMID | pubmed-search |
| 检查规范 / CONSORT / checklist | reporting-standards |
| 模拟审稿 / reviewer | peer-review-simulation |
| 审稿意见 / 修稿 | revision-response |
| 伦理 / IRB / 知情同意 | research-ethics |
| 投哪个期刊 / 选刊 | journal-selection |
| cover letter / 投稿系统 / 怎么投稿 | submission-preparation |
| 并行 / 团队协作 | team-collaboration |
| 写完了 / 可以投了 | **pre-submission-verification (MANDATORY — 6-Gate)** |
ROUTING
fi

# ── User preferences ──────────────────────────────────────────────────────────
if [ -n "$USER_NAME" ] || [ -n "$FAV_JOURNAL" ] || [ -n "$STATS_TOOL" ]; then
  echo ''
  echo '## User preferences'
  [ -n "$USER_NAME" ]  && echo "- User         : $USER_NAME"
  [ -n "$FAV_JOURNAL" ] && echo "- Pref journal : $FAV_JOURNAL"
  [ -n "$STATS_TOOL" ] && echo "- Stats tool   : $STATS_TOOL"
fi

# ── Environment warnings ──────────────────────────────────────────────────────
if [ -n "$ENV_WARN" ]; then
  echo ''
  echo "$ENV_WARN"
fi

# ── Core rules (always shown) ─────────────────────────────────────────────────
cat <<'RULES'

## Rules
1. **1% Rule** — even 1% chance → invoke the skill
2. **Checkpoint** — report after each skill; ask before proceeding to next
3. **Hard Checkpoints** — study protocol / SAP / target journal / pre-submission: explicit confirmation required
4. **Never skip pre-submission-verification** before declaring a manuscript complete
5. **CONSORT 2025** (not 2010) — 30 items, supersedes 2010
</EXTREMELY_IMPORTANT>
</session-start-hook>
RULES
