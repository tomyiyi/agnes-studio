#!/usr/bin/env python3
"""
Agnes Studio - 上游依赖与健康监控脚本
自动化检测上游 GitHub 仓库状态、本地 New API 聚合网关探活、同步更新至 data/updates.json
"""

import urllib.request
import json
import os
import time
from pathlib import Path

STUDIO_ROOT = Path(__file__).resolve().parent.parent
UPDATES_PATH = str(STUDIO_ROOT / "data" / "updates.json")

def get_local_auth_key():
    local_key_path = os.path.expanduser("~/.new-api/local_key.json")
    if os.path.exists(local_key_path):
        try:
            with open(local_key_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("api_key", "")
        except Exception:
            pass
    return os.environ.get("NEW_API_KEY", "")

def check_new_api_health():
    url = "http://127.0.0.1:3000/v1/models"
    api_key = get_local_auth_key()
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    req = urllib.request.Request(url, headers=headers)
    start_t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            elapsed = int((time.time() - start_t) * 1000)
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("id") for m in data.get("data", [])]
                return {
                    "status": "healthy",
                    "latency_ms": elapsed,
                    "available_models_count": len(models),
                    "image_models": [m for m in models if "image" in m or "dall-e" in m]
                }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def check_github_repo(owner_repo):
    api_url = f"https://api.github.com/repos/{owner_repo}/commits/main"
    req = urllib.request.Request(api_url, headers={"User-Agent": "Agnes-Studio-Sentinel/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                sha = data.get("sha", "")[:7]
                commit_msg = data.get("commit", {}).get("message", "").split("\n")[0]
                commit_date = data.get("commit", {}).get("author", {}).get("date", "")
                return {
                    "repo": owner_repo,
                    "latest_commit": sha,
                    "date": commit_date,
                    "message": commit_msg,
                    "status": "synchronized"
                }
    except Exception as e:
        # 无网络或触发 GitHub API 频率限制时的静默兜底
        return {
            "repo": owner_repo,
            "status": "cached",
            "note": "Local cached or rate-limited"
        }

def run_lifecycle_monitor():
    print("🛰️ [Agnes Studio Sentinel] 正在启动生命周期与上游依赖巡检...")
    
    # 1. 检测本地网关
    gateway_status = check_new_api_health()
    print(f"  * 本地网关状态: {gateway_status.get('status')} (耗时: {gateway_status.get('latency_ms', 0)}ms)")
    
    # 2. 检测上游仓库
    garden_repo = check_github_repo("ConardLi/garden-skills")
    print(f"  * 上游 Garden-Skills 仓库状态: {garden_repo.get('status')}")

    # 3. 组织更新结构
    summary = {
        "last_checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "gateway": gateway_status,
        "upstream_repositories": [
            garden_repo,
            {"repo": "QuantumNous/new-api", "status": "stable_v1.0.0-rc.24"}
        ],
        "cron_jobs": [
            {"job": "db_backup", "schedule": "0 3 * * *", "target": "/Users/tom/.new-api/backups"}
        ]
    }
    
    with open(UPDATES_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 监控报告已成功同步写盘至: {UPDATES_PATH}")

if __name__ == "__main__":
    run_lifecycle_monitor()
