#!/usr/bin/env bash
# ==============================================================================
# Agnes Studio - 一键多端双向极速同步脚本 (Robust Rebase Flow)
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=============================================================================="
echo "🚀 [Agnes Studio] 正在与 GitHub 执行双向同步..."
echo "=============================================================================="

# 1. 检查并提交本地改动
CHANGES=$(git status --porcelain)
HAS_LOCAL_COMMIT=false

if [ -n "$CHANGES" ]; then
    echo "📦 1/3 检测到本地有改动，正在打包更新..."
    git status -s
    COMMIT_MSG="${1:-"chore(sync): update posters and assets ($(date '+%Y-%m-%d %H:%M:%S'))"}"
    git add .
    git commit -m "$COMMIT_MSG"
    HAS_LOCAL_COMMIT=true
else
    echo "✨ 1/3 本地工作区干净，无未提交修改。"
fi

# 2. 安全拉取远端更新并进行变基合并 (确保多台电脑提交保持线性整洁)
echo "📥 2/3 正在检查并拉取远端最新改动 (git pull --rebase)..."
git pull --rebase origin main || {
    echo "⚠️ 发现严重合并冲突，请先手动检查解决！"
    exit 1
}

# 3. 检查是否有需要推送到远端的提交
AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "0")
if [ "$AHEAD" -gt 0 ]; then
    echo "📤 3/3 检测到 $AHEAD 个本地提交待推送，正在推送至 GitHub (git push)..."
    git push origin main
    echo "=============================================================================="
    echo "✅ 同步圆满完成！远程地址: https://github.com/tomyiyi/agnes-studio"
    echo "=============================================================================="
else
    echo "✅ 3/3 本地与远程完全一致，已是最新状态！"
fi
