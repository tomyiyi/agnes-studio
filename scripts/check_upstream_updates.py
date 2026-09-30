#!/usr/bin/env python3
"""
Agnes Studio - 上游依赖与健康监控脚本
自动化检测上游 GitHub 仓库状态、本地 New API 聚合网关探活、同步更新至 data/updates.json
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

STUDIO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KEY_PATH = Path.home() / ".new-api" / "local_key.json"
DEFAULT_BASE_URL = "http://127.0.0.1:13000/v1"
UPDATES_PATH = str(STUDIO_ROOT / "data" / "updates.json")


def get_local_auth_key(key_path: Path | str | None = None) -> str:
    """获取本地或环境变量中的 New API 鉴权密钥"""
    env_key = os.environ.get("NEW_API_KEY") or os.environ.get("AGNES_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    target_path = Path(key_path) if key_path else DEFAULT_KEY_PATH
    if target_path.exists():
        try:
            data = json.loads(target_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                key = str(data.get("api_key") or "").strip()
                if key:
                    return key
        except Exception:
            pass
    return ""


def get_local_base_url(key_path: Path | str | None = None) -> str:
    "Resolve the active image gateway from the same local source as Studio."
    env_base = os.environ.get("NEW_API_BASE_URL") or os.environ.get("AGNES_BASE_URL")
    if env_base and env_base.strip():
        return env_base.strip().rstrip("/")

    target_path = Path(key_path) if key_path else DEFAULT_KEY_PATH
    if target_path.exists():
        try:
            data = json.loads(target_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                configured = str(data.get("image_base_url") or data.get("base_url") or "").strip()
                if configured:
                    return configured.rstrip("/")
        except Exception:
            pass
    return DEFAULT_BASE_URL


def check_new_api_health(
    base_url: str | None = None,
    api_key: str | None = None,
    timeout: float = 5.0,
) -> dict:
    """检测 New API 聚合网关探活状态并获取可用模型清单"""
    raw_base = base_url or get_local_base_url()
    raw_base = raw_base.rstrip("/")
    if raw_base.endswith("/v1"):
        url = f"{raw_base}/models"
    else:
        url = f"{raw_base}/v1/models"

    key = api_key if api_key is not None else get_local_auth_key()
    headers = {"User-Agent": "Agnes-Studio-Sentinel/1.0"}
    if key:
        headers["Authorization"] = f"Bearer {key}"

    req = urllib.request.Request(url, headers=headers)
    start_t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = int((time.time() - start_t) * 1000)
            status_code = getattr(resp, "status", 200)
            if status_code == 200:
                raw_body = resp.read().decode("utf-8")
                try:
                    data = json.loads(raw_body)
                except Exception as json_err:
                    return {
                        "status": "unhealthy",
                        "error": f"Invalid JSON response: {json_err}",
                        "latency_ms": elapsed,
                    }
                data_list = data.get("data", []) if isinstance(data, dict) else []
                models = []
                if isinstance(data_list, list):
                    for m in data_list:
                        if isinstance(m, dict) and "id" in m and m["id"]:
                            models.append(str(m["id"]))
                return {
                    "status": "healthy",
                    "latency_ms": elapsed,
                    "available_models_count": len(models),
                    "image_models": [
                        m for m in models if "image" in m.lower() or "dall-e" in m.lower()
                    ],
                }
            return {
                "status": "unhealthy",
                "error": f"HTTP {status_code}",
                "latency_ms": elapsed,
            }
    except urllib.error.HTTPError as e:
        elapsed = int((time.time() - start_t) * 1000)
        return {
            "status": "unhealthy",
            "error": f"HTTPError {e.code}: {e.reason}",
            "latency_ms": elapsed,
        }
    except Exception as e:
        elapsed = int((time.time() - start_t) * 1000)
        return {"status": "unhealthy", "error": str(e), "latency_ms": elapsed}


def check_github_repo(
    owner_repo: str,
    timeout: float = 5.0,
    branch: str = "main",
) -> dict:
    """检测上游 GitHub 仓库最新提交与同步状态"""
    if not owner_repo or not isinstance(owner_repo, str) or "/" not in owner_repo:
        return {
            "repo": str(owner_repo),
            "status": "invalid_repo",
            "note": "Invalid repository specification, expected owner/repo",
        }

    api_url = f"https://api.github.com/repos/{owner_repo}/commits/{branch}"
    req = urllib.request.Request(
        api_url,
        headers={
            "User-Agent": "Agnes-Studio-Sentinel/1.0",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status_code = getattr(resp, "status", 200)
            if status_code == 200:
                raw_body = resp.read().decode("utf-8")
                data = json.loads(raw_body)
                if isinstance(data, dict):
                    sha = str(data.get("sha", ""))[:7]
                    commit_obj = data.get("commit") or {}
                    msg = str(commit_obj.get("message", "")).split("\n")[0]
                    author_obj = commit_obj.get("author") or {}
                    commit_date = str(author_obj.get("date", ""))
                    return {
                        "repo": owner_repo,
                        "latest_commit": sha,
                        "date": commit_date,
                        "message": msg,
                        "status": "synchronized",
                    }
            return {
                "repo": owner_repo,
                "status": "cached",
                "note": f"HTTP {status_code}",
            }
    except Exception as e:
        # 无网络或触发 GitHub API 频率限制时的静默兜底
        return {
            "repo": owner_repo,
            "status": "cached",
            "note": f"Local cached or rate-limited: {e}",
        }


def run_lifecycle_monitor(
    output_path: Path | str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    repos: list[str] | None = None,
    timeout: float = 5.0,
    save: bool = True,
) -> dict:
    """执行完整的生命周期与上游依赖巡检，组织并写盘更新结构"""
    print("🛰️ [Agnes Studio Sentinel] 正在启动生命周期与上游依赖巡检...")

    # 1. 检测本地网关
    gateway_status = check_new_api_health(base_url=base_url, api_key=api_key, timeout=timeout)
    print(
        f"  * 本地网关状态: {gateway_status.get('status')} (耗时: {gateway_status.get('latency_ms', 0)}ms)"
    )

    # 2. 检测上游仓库
    target_repos = repos if repos is not None else ["ConardLi/garden-skills"]
    upstream_list = []
    for r in target_repos:
        repo_info = check_github_repo(r, timeout=timeout)
        print(f"  * 上游 {r} 仓库状态: {repo_info.get('status')}")
        upstream_list.append(repo_info)

    upstream_list.append({"repo": "QuantumNous/new-api", "status": "stable_v1.0.0-rc.24"})

    backup_dir = str(Path.home() / ".new-api" / "backups")

    # 3. 组织更新结构
    summary = {
        "last_checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "gateway": gateway_status,
        "upstream_repositories": upstream_list,
        "cron_jobs": [
            {"job": "db_backup", "schedule": "0 3 * * *", "target": backup_dir}
        ],
    }

    if save:
        target_path = Path(output_path) if output_path else Path(UPDATES_PATH)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ 监控报告已成功同步写盘至: {target_path}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Agnes Studio Sentinel & Upstream Monitor")
    parser.add_argument("--out", type=str, default=UPDATES_PATH, help="Output JSON path")
    parser.add_argument("--base-url", type=str, default=None, help="New API base URL")
    parser.add_argument("--api-key", type=str, default=None, help="New API auth key")
    parser.add_argument("--timeout", type=float, default=5.0, help="Request timeout in seconds")
    parser.add_argument("--no-save", action="store_true", help="Do not write output to file")
    args = parser.parse_args()

    run_lifecycle_monitor(
        output_path=args.out,
        base_url=args.base_url,
        api_key=args.api_key,
        timeout=args.timeout,
        save=not args.no_save,
    )


if __name__ == "__main__":
    main()

