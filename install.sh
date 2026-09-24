#!/bin/bash
# Med-Research-Powers (MRP) installer — v6.4.0
#
# Two install methods:
#   1) Claude Code plugin  (recommended; auto-updates via the marketplace)
#   2) Whole-repo symlink into ~/.claude/skills/med-research-powers
#      (loaded as the plugin "mrp@skills-dir" — hooks and ${CLAUDE_PLUGIN_ROOT} work,
#       edits to the checkout take effect immediately; for development)
#
# Usage:
#   ./install.sh                 interactive (asks which method)
#   ./install.sh --method 1|2    non-interactive
#   ./install.sh --help
#
# When stdin is not a terminal (e.g. `curl ... | bash`) the script never prompts
# and defaults to method 1.

set -eu

MRP_VERSION="6.4.0"
PLUGIN_ID="mrp@med-research-powers"
GITHUB_REPO="Stefansong/med-research-powers"

# ─── Colors (only when stdout is a terminal) ───
if [ -t 1 ]; then
    RED="$(printf '\033[0;31m')"
    GREEN="$(printf '\033[0;32m')"
    YELLOW="$(printf '\033[1;33m')"
    CYAN="$(printf '\033[0;36m')"
    BOLD="$(printf '\033[1m')"
    NC="$(printf '\033[0m')"
else
    RED=""; GREEN=""; YELLOW=""; CYAN=""; BOLD=""; NC=""
fi

say()  { printf '%s\n' "$*"; }
ok()   { printf '%s\n' "${GREEN}✓${NC} $*"; }
warn() { printf '%s\n' "${YELLOW}⚠${NC} $*"; }
fail() { printf '%s\n' "${RED}✗${NC} $*" >&2; }

usage() {
    say "Usage: $0 [--method 1|2] [--help]"
    say "  --method 1   install as a Claude Code plugin (default)"
    say "  --method 2   symlink the whole repo into ~/.claude/skills/med-research-powers"
}

# ─── Parse arguments ───
INSTALL_METHOD=""
while [ $# -gt 0 ]; do
    case "$1" in
        --method)
            [ $# -ge 2 ] || { fail "--method needs a value (1 or 2)"; exit 2; }
            INSTALL_METHOD="$2"; shift 2 ;;
        --method=*)
            INSTALL_METHOD="${1#--method=}"; shift ;;
        -h|--help)
            usage; exit 0 ;;
        *)
            fail "Unknown option: $1"; usage; exit 2 ;;
    esac
done

say ""
say "${BOLD}╔══════════════════════════════════════════════╗${NC}"
say "${BOLD}║     Med-Research-Powers v${MRP_VERSION} Installer     ║${NC}"
say "${BOLD}║     医学科研方法论框架                        ║${NC}"
say "${BOLD}╚══════════════════════════════════════════════╝${NC}"
say ""

# ─── Detect OS ───
case "$(uname -s)" in
    Darwin*)              PLATFORM="macOS" ;;
    Linux*)               PLATFORM="Linux" ;;
    MINGW*|MSYS*|CYGWIN*) PLATFORM="Windows" ;;
    *)                    PLATFORM="Unknown" ;;
esac
say "${CYAN}Platform: ${PLATFORM}${NC}"
if [ "$PLATFORM" = "Windows" ]; then
    warn "On Windows please use the plugin method (1). Symlinks made by Git Bash are plain copies and will not auto-update."
fi

# ─── Locate this checkout and sanity-check it ───
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ ! -f "$SCRIPT_DIR/.claude-plugin/plugin.json" ] || [ ! -f "$SCRIPT_DIR/skills/using-med-research-powers/SKILL.md" ]; then
    fail "Cannot find the MRP plugin files in $SCRIPT_DIR"
    say "  Run this script from inside the med-research-powers checkout."
    exit 1
fi

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

# ─── Choose install method ───
if [ -z "$INSTALL_METHOD" ]; then
    if [ -t 0 ]; then
        say ""
        say "${BOLD}Installation method:${NC}"
        say "  1) Claude Code plugin (recommended — auto-updates, hook enabled)"
        say "  2) Symlink this checkout into ~/.claude/skills/ (development — edits take effect immediately)"
        say ""
        printf 'Choose [1/2] (default: 1): '
        read -r INSTALL_METHOD || INSTALL_METHOD=""
        INSTALL_METHOD="${INSTALL_METHOD:-1}"
    else
        INSTALL_METHOD="1"
        say "(non-interactive: using method 1 — plugin install)"
    fi
fi

if [ "$INSTALL_METHOD" = "2" ] && [ "$PLATFORM" = "Windows" ]; then
    warn "Symlink method is not reliable on Windows — falling back to the plugin method."
    INSTALL_METHOD="1"
fi

INSTALL_STATUS="pending"   # installed | manual | pending

case "$INSTALL_METHOD" in
    1)
        say ""
        say "${CYAN}Installing as a Claude Code plugin...${NC}"
        if command -v claude >/dev/null 2>&1; then
            if ! claude plugin marketplace add "$SCRIPT_DIR"; then
                warn "Could not add the marketplace from $SCRIPT_DIR (it may already be registered) — trying the install anyway."
            fi
            if claude plugin install "$PLUGIN_ID"; then
                INSTALL_STATUS="installed"
                ok "Plugin installed: $PLUGIN_ID"
            else
                INSTALL_STATUS="manual"
                fail "claude plugin install failed. Run these inside Claude Code instead:"
            fi
        else
            INSTALL_STATUS="manual"
            warn "The 'claude' CLI is not on PATH. Run these two commands inside Claude Code:"
        fi
        if [ "$INSTALL_STATUS" = "manual" ]; then
            say ""
            say "  ${BOLD}/plugin marketplace add ${GITHUB_REPO}${NC}"
            say "  ${BOLD}/plugin install ${PLUGIN_ID}${NC}"
            say ""
            say "  (for this local checkout: /plugin marketplace add $SCRIPT_DIR)"
        fi
        ;;
    2)
        SKILLS_DIR="$CLAUDE_DIR/skills"
        TARGET="$SKILLS_DIR/med-research-powers"
        mkdir -p "$SKILLS_DIR"
        say ""
        say "${CYAN}Linking $SCRIPT_DIR → $TARGET${NC}"
        if [ -L "$TARGET" ]; then
            rm "$TARGET"
        elif [ -e "$TARGET" ]; then
            fail "$TARGET already exists and is not a symlink. Move it away and re-run."
            exit 1
        fi
        ln -s "$SCRIPT_DIR" "$TARGET"
        INSTALL_STATUS="installed"
        ok "Symlink created. Claude Code loads it as the plugin 'mrp@skills-dir' (hook + \${CLAUDE_PLUGIN_ROOT} work)."
        ;;
    *)
        fail "Invalid method '$INSTALL_METHOD' (expected 1 or 2)."
        exit 2
        ;;
esac

# ─── Check Python dependencies for the bundled scripts (same list as requirements.txt) ───
say ""
say "${BOLD}Checking Python dependencies for the bundled scripts (optional)...${NC}"

PY=""
if command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
fi

# usage: check_python_pkg <import name> <pip name>
check_python_pkg() {
    if "$PY" -c "import $1" >/dev/null 2>&1; then
        say "  ${GREEN}✓${NC} $2"
    else
        say "  ${YELLOW}○${NC} $2  (missing — pip install $2)"
        MISSING="$MISSING $2"
    fi
}

MISSING=""
if [ -n "$PY" ]; then
    ok "Python found: $("$PY" --version 2>&1)"
    check_python_pkg scipy       scipy
    check_python_pkg statsmodels statsmodels
    check_python_pkg matplotlib  matplotlib
    check_python_pkg pandas      pandas
    check_python_pkg numpy       numpy
    check_python_pkg docx        python-docx
    check_python_pkg openpyxl    openpyxl
    check_python_pkg yaml        pyyaml
    if [ -n "$MISSING" ]; then
        say ""
        say "  Install everything at once:  ${CYAN}pip install -r $SCRIPT_DIR/requirements.txt${NC}"
    fi
else
    warn "Python not found. The skills still work; only the bundled scripts (statistics, figures, .docx export) need Python."
fi

# ─── Summary ───
say ""
if [ "$INSTALL_STATUS" = "installed" ]; then
    say "${BOLD}╔══════════════════════════════════════════════╗${NC}"
    say "${BOLD}║  ${GREEN}Installation complete!${NC}${BOLD}                       ║${NC}"
    say "${BOLD}╚══════════════════════════════════════════════╝${NC}"
else
    say "${BOLD}╔══════════════════════════════════════════════╗${NC}"
    say "${BOLD}║  ${YELLOW}Files ready — finish inside Claude Code${NC}${BOLD}     ║${NC}"
    say "${BOLD}╚══════════════════════════════════════════════╝${NC}"
fi
say ""
say "  ${BOLD}Verify:${NC}"
say "  ${CYAN}claude plugin list${NC}   → should list ${PLUGIN_ID} (method 1) or mrp@skills-dir (method 2)"
say "  Then, in a new Claude Code session, try: ${CYAN}/mrp:research-question${NC}"
say "  or just say: ${CYAN}\"帮我设计一个 AI 辅助诊断的研究\"${NC}"
say ""
say "  ${BOLD}Commands (/mrp:<command>):${NC}"
say "  /mrp:research-question  — 构建研究问题（PICO / FINER）"
say "  /mrp:analyze-data       — 无分析计划先做计划，有计划则执行统计"
say "  /mrp:write-manuscript   — 按 IMRaD 写论文"
say "  /mrp:peer-review        — 模拟 4 位审稿人评审"
say "  /mrp:check-standards    — 只检查报告规范（CONSORT/STROBE/PRISMA…）"
say "  /mrp:pre-submission     — 投稿前 6-Gate 核验（投稿前必做）"
say "  /mrp:using-mrp          — 编排器：路由、流水线、检查点"
say "  其余 skill 直接用 /mrp:<skill> 调用，例如 /mrp:study-design、/mrp:journal-selection"
say ""
say "  ${BOLD}Upgrading from 6.2.x:${NC} the plugin was renamed — first run /plugin uninstall med-research-powers@med-research-powers"
say "  ${BOLD}Uninstall:${NC} /plugin uninstall ${PLUGIN_ID}   (method 2: rm \"$CLAUDE_DIR/skills/med-research-powers\")"
say "  ${BOLD}Documentation:${NC} https://github.com/${GITHUB_REPO}"
say ""
