#!/usr/bin/env bash
cd /home/tom/Work/agnes-studio
# Fetch changes silently using proxy
git -c http.proxy=http://192.168.1.164:7897 -c https.proxy=http://192.168.1.164:7897 fetch origin main 2>&1
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)
if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[SYNC] New updates detected from MacBook Pro on GitHub! Syncing..."
    git -c http.proxy=http://192.168.1.164:7897 -c https.proxy=http://192.168.1.164:7897 pull --rebase --autostash origin main
    echo "[SYNC] Synced successfully to: $(git log -n 1 --oneline)"
fi
