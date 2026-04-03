#!/bin/bash
# Med-Research-Powers GitHub 一键推送脚本
# 用法: ./push-to-github.sh

set -e

echo "=== Med-Research-Powers → GitHub ==="
echo ""

# 检查 gh 是否已登录
if ! gh auth status &>/dev/null; then
    echo "⚠️  gh 未登录，先执行: gh auth login"
    echo ""
    gh auth login
fi

GITHUB_USER=$(gh api user -q .login)
echo "✓ 已登录: $GITHUB_USER"

REPO_NAME="med-research-powers"

# 替换 YOUR_USERNAME
echo "→ 替换占位符为 $GITHUB_USER ..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s|YOUR_USERNAME|$GITHUB_USER|g" README.md install.sh
    sed -i '' "s|btch-uro-ai-lab|$GITHUB_USER|g" .claude-plugin/plugin.json
else
    sed -i "s|YOUR_USERNAME|$GITHUB_USER|g" README.md install.sh
    sed -i "s|btch-uro-ai-lab|$GITHUB_USER|g" .claude-plugin/plugin.json
fi
echo "✓ 占位符已替换"

# 补提交
git add -A
git diff --cached --quiet || git commit -m "chore: replace placeholder with $GITHUB_USER"

# 创建仓库并推送
echo "→ 创建 GitHub 仓库: $GITHUB_USER/$REPO_NAME ..."
gh repo create "$REPO_NAME" \
    --public \
    --description "Medical research methodology framework for AI coding agents — 16 skills, ~40 reporting standards, mandatory pre-submission verification" \
    --source . \
    --remote origin \
    --push

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✅ 推送完成!                                    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  仓库地址: https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""
echo "  建议后续操作:"
echo "  1. 添加 Topics: claude-code, skills, medical-research"
echo "  2. 创建 Release: gh release create v5.0.0 --title 'v5.0.0' --notes-file CHANGELOG.md"
echo "  3. 本地安装测试: /plugin install ./$REPO_NAME"
echo ""
