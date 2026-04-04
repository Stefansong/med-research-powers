#!/bin/sh
# Med-Research-Powers — session-start hook
# Fires on: startup, clear, compact
# Does NOT fire on: --resume (context already loaded)

echo "<session-start-hook>"
echo "<EXTREMELY_IMPORTANT>"
echo "You have Med-Research-Powers (MRP) v6.2.1 — medical research methodology framework."
echo "**Before ANY research-related task, check if a MRP skill applies (1% Rule).**"

# ── Project state: raw dump so Claude sees everything ─────────────────────────
if [ -f "./.mrp-state.json" ]; then
    echo ""
    echo "### Current Project State:"
    cat "./.mrp-state.json"
    echo ""
    echo "Based on the state above, identify the current stage and tell the user the recommended next step. Do NOT show the full routing table."
fi

# ── User profile: raw dump, or prompt to build one ───────────────────────────
if [ -f "./.mrp-user-profile.json" ]; then
    echo ""
    echo "### User Profile:"
    cat "./.mrp-user-profile.json"
else
    echo ""
    echo "### ACTION REQUIRED: No .mrp-user-profile.json found."
    echo "Before running the first skill, ask the user these 5 questions (one at a time):"
    echo "1. Role? (PI / PhD / resident / postdoc / other)"
    echo "2. Research domain? (e.g. urologic oncology, medical AI)"
    echo "3. Journals you usually target?"
    echo "4. Familiar statistical methods?"
    echo "5. Preferred analysis tool? (Python / R / SPSS / Stata)"
    echo "Save answers to .mrp-user-profile.json before proceeding."
fi

# ── Environment check ─────────────────────────────────────────────────────────
python3 -c "import docx" 2>/dev/null || echo ""
python3 -c "import docx" 2>/dev/null || echo "⚠️  python-docx not installed — manuscript-export unavailable (pip install python-docx)"

# ── Routing table: only for new projects ─────────────────────────────────────
if [ ! -f "./.mrp-state.json" ]; then
    cat <<'ROUTING'

## Quick routing

| User intent | Skill |
|-------------|-------|
| 模糊想法 / "我想研究..." | research-question-formulation |
| 查文献 / 综述 / research gap | literature-synthesis |
| 查PubMed / 引用验证 / PMID | pubmed-search |
| 研究设计 / 样本量 / protocol | study-design (统一入口) |
| 数据收集工具 / CRF / 标注表 | data-collection-tools |
| 分析数据 / 统计方法 | data-analysis-planning → statistical-analysis |
| 画图 / Figure / 可视化 | figure-generation |
| 写论文 / manuscript | manuscript-writing |
| 导出Word / 格式排版 | manuscript-export |
| 规范 / CONSORT / checklist | reporting-standards |
| 模拟审稿 / reviewer | peer-review-simulation |
| 修稿 / 审稿意见 | revision-response |
| 伦理 / IRB | research-ethics |
| 投哪个期刊 / 选刊 | journal-selection |
| cover letter / 投稿系统 | submission-preparation |
| 并行协作 / agent team | team-collaboration |
| 写完了 / 可以投了 | **pre-submission-verification (MANDATORY — 6-Gate)** |
ROUTING
fi

# ── Core rules (always) ───────────────────────────────────────────────────────
cat <<'RULES'

## Rules
1. **1% Rule** — even 1% chance → invoke the skill
2. **Read before acting** — read full SKILL.md, not just the description
3. **Never skip pre-submission-verification** before declaring a manuscript complete
4. **Checkpoint** — report after each skill; ask before next step; no silent transitions
5. **Hard Checkpoints** — study protocol / SAP / target journal / pre-submission: explicit user confirmation required
6. **CONSORT 2025** (not 2010) — 30 items, officially supersedes 2010
</EXTREMELY_IMPORTANT>
</session-start-hook>
RULES
