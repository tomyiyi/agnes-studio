#!/usr/bin/env bash
# 上游自动同步：工作目录与代理均可用环境变量覆盖
#   AGNES_WORK_DIR  本地仓库目录（默认 ~/Work/agnes-studio）
#   HTTP_PROXY      git 使用的代理（默认局域网 192.168.1.164:7897）
#   HTTPS_PROXY     https 代理（默认跟随 HTTP_PROXY）
WORK_DIR="${AGNES_WORK_DIR:-$HOME/Work/agnes-studio}"
PROXY="${HTTP_PROXY:-http://192.168.1.164:7897}"
HTTPS_P="${HTTPS_PROXY:-$PROXY}"
cd "$WORK_DIR" || { echo "[SYNC] 工作目录不存在: $WORK_DIR" >&2; exit 1; }
# Fetch changes silently using proxy
git -c "http.proxy=$PROXY" -c "https.proxy=$HTTPS_P" fetch origin main 2>&1
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)
if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[SYNC] New updates detected from MacBook Pro on GitHub! Syncing..."
    git -c "http.proxy=$PROXY" -c "https.proxy=$HTTPS_P" pull --rebase --autostash origin main
    echo "[SYNC] Synced successfully to: $(git log -n 1 --oneline)"
fi
