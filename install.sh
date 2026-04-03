#!/bin/bash
# Med-Research-Powers Installer
# Works on macOS and Linux

set -e

# ─── Colors ───
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║     Med-Research-Powers v5 Installer         ║${NC}"
echo -e "${BOLD}║     医学科研方法论框架                        ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ─── Detect OS ───
OS="$(uname -s)"
case "$OS" in
    Darwin*) PLATFORM="macOS" ;;
    Linux*)  PLATFORM="Linux" ;;
    MINGW*|MSYS*|CYGWIN*) PLATFORM="Windows" ;;
    *) PLATFORM="Unknown" ;;
esac
echo -e "${CYAN}Platform: ${PLATFORM}${NC}"

# ─── Detect Claude Code ───
CLAUDE_DIR=""
if [ -d "$HOME/.claude" ]; then
    CLAUDE_DIR="$HOME/.claude"
    echo -e "${GREEN}✓ Found Claude Code config: $CLAUDE_DIR${NC}"
else
    echo -e "${YELLOW}⚠ Claude Code config not found at ~/.claude${NC}"
    echo -e "  If Claude Code is installed elsewhere, enter the path:"
    read -r -p "  Path (or press Enter to create ~/.claude): " CUSTOM_PATH
    if [ -n "$CUSTOM_PATH" ] && [ -d "$CUSTOM_PATH" ]; then
        CLAUDE_DIR="$CUSTOM_PATH"
    else
        CLAUDE_DIR="$HOME/.claude"
        mkdir -p "$CLAUDE_DIR"
        echo -e "${GREEN}✓ Created $CLAUDE_DIR${NC}"
    fi
fi

# ─── Get script directory (where MRP was cloned) ───
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ─── Verify MRP files exist ───
if [ ! -f "$SCRIPT_DIR/skills/using-med-research-powers/SKILL.md" ]; then
    echo -e "${RED}✗ Error: Cannot find MRP skill files in $SCRIPT_DIR${NC}"
    echo "  Make sure you run this script from the med-research-powers directory."
    exit 1
fi

# ─── Choose install method ───
echo ""
echo -e "${BOLD}Installation method:${NC}"
echo "  1) Claude Code Plugin (recommended — auto-updates, hooks work)"
echo "  2) Copy skills to ~/.claude/skills/ (manual, no hooks)"
echo "  3) Symlink (development — edit files in place)"
echo ""
read -r -p "Choose [1/2/3] (default: 1): " INSTALL_METHOD
INSTALL_METHOD=${INSTALL_METHOD:-1}

case "$INSTALL_METHOD" in
    1)
        echo ""
        echo -e "${CYAN}Installing as Claude Code plugin...${NC}"
        echo ""
        echo -e "Run the following command in Claude Code:"
        echo ""
        echo -e "  ${BOLD}/plugin install $SCRIPT_DIR${NC}"
        echo ""
        echo -e "Or if you've pushed to GitHub:"
        echo ""
        echo -e "  ${BOLD}/plugin install https://github.com/Stefansong/med-research-powers${NC}"
        echo ""
        echo -e "${GREEN}✓ Plugin files are ready. Run the command above in Claude Code.${NC}"
        ;;
    2)
        SKILLS_DIR="$CLAUDE_DIR/skills"
        mkdir -p "$SKILLS_DIR"
        
        # Copy skills
        echo -e "${CYAN}Copying skills to $SKILLS_DIR ...${NC}"
        cp -r "$SCRIPT_DIR/skills/"* "$SKILLS_DIR/"
        echo -e "${GREEN}✓ Skills copied ($(ls -d "$SKILLS_DIR"/*/  | wc -l | tr -d ' ') skills)${NC}"
        
        # Copy commands if commands dir exists in claude
        COMMANDS_DIR="$CLAUDE_DIR/commands"
        if [ -d "$SCRIPT_DIR/commands" ]; then
            mkdir -p "$COMMANDS_DIR"
            cp "$SCRIPT_DIR/commands/"* "$COMMANDS_DIR/"
            echo -e "${GREEN}✓ Commands copied ($(ls "$COMMANDS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ') commands)${NC}"
        fi
        
        echo ""
        echo -e "${YELLOW}⚠ Note: Manual install does not enable session-start hook.${NC}"
        echo -e "  Claude won't auto-discover MRP skills unless you tell it."
        echo -e "  Consider using Plugin install (method 1) for full functionality."
        ;;
    3)
        SKILLS_DIR="$CLAUDE_DIR/skills"
        mkdir -p "$SKILLS_DIR"
        
        echo -e "${CYAN}Creating symlinks...${NC}"
        for skill_dir in "$SCRIPT_DIR/skills"/*/; do
            skill_name=$(basename "$skill_dir")
            target="$SKILLS_DIR/$skill_name"
            if [ -L "$target" ]; then
                rm "$target"
            elif [ -d "$target" ]; then
                echo -e "${YELLOW}  ⚠ $skill_name already exists (not a symlink), skipping${NC}"
                continue
            fi
            ln -s "$skill_dir" "$target"
            echo -e "  ${GREEN}✓${NC} $skill_name → $skill_dir"
        done
        echo -e "${GREEN}✓ Symlinks created. Edits to source files take effect immediately.${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac

# ─── Check Python dependencies (for scripts) ───
echo ""
echo -e "${BOLD}Checking optional dependencies for scripts...${NC}"

check_python_pkg() {
    python3 -c "import $1" 2>/dev/null && echo -e "  ${GREEN}✓${NC} $1" || echo -e "  ${YELLOW}○${NC} $1 (optional — install with: pip install $1)"
}

if command -v python3 &>/dev/null; then
    echo -e "${GREEN}✓ Python3 found: $(python3 --version 2>&1)${NC}"
    check_python_pkg "scipy"
    check_python_pkg "statsmodels"
    check_python_pkg "matplotlib"
    check_python_pkg "pandas"
    check_python_pkg "numpy"
else
    echo -e "${YELLOW}○ Python3 not found. Scripts in figure-generation/ and statistical-analysis/ won't run.${NC}"
    echo -e "  This is optional — MRP skills work without them, just less efficiently."
fi

# ─── Done ───
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║  ${GREEN}Installation complete!${NC}${BOLD}                       ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Quick start:${NC}"
echo -e "  1. Start a new Claude Code session"
echo -e "  2. You should see MRP auto-discovery message"
echo -e "  3. Try: ${CYAN}/mrp:research-question${NC}"
echo -e "  4. Or just say: ${CYAN}\"帮我设计一个 AI 辅助诊断的研究\"${NC}"
echo ""
echo -e "  ${BOLD}Available commands:${NC}"
echo -e "  /mrp:research-question  — 构建研究问题（PICO/FINER）"
echo -e "  /mrp:analyze-data       — 制定分析计划并执行统计"
echo -e "  /mrp:write-manuscript   — 按 IMRaD 写论文"
echo -e "  /mrp:check-standards    — 检查报告规范（投稿前必做）"
echo -e "  /mrp:peer-review        — 模拟同行评审"
echo ""
echo -e "  ${BOLD}Documentation:${NC} https://github.com/Stefansong/med-research-powers"
echo ""
