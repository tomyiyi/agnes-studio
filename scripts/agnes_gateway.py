#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes 生图客户端（经 New API 轮换）
=================================

经验沉淀：
  - 不直连 apihub 打单 Key，统一走本机 New API（127.0.0.1:3000）
  - New API 渠道池 Agnes-Hub-01..06 多 Key 权重轮换 + 失败熔断 + 自动探活
  - Token 从 ~/.new-api/local_key.json 读取，不写死在代码
  - 超时重试沿用网关 RetryTimes，客户端只做幂等落地

用法：
  python3 scripts/agnes_gateway.py --prompt "..." --out out.png
  python3 scripts/agnes_gateway.py --brief data/briefs/xhs_fresh_ctr.json --out out.png
"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KEY_PATH = Path.home() / ".new-api" / "local_key.json"
DEFAULT_BASE = "http://127.0.0.1:3000/v1"
DEFAULT_MODEL = "agnes-image-2.5-flash"


def load_gateway(key_path: Path | str | None = None) -> tuple[str, str, str]:
    target_path = Path(key_path) if key_path else DEFAULT_KEY_PATH
    base, key, model = DEFAULT_BASE, "", DEFAULT_MODEL
    if target_path.exists():
        try:
            data = json.loads(target_path.read_text(encoding="utf-8"))
            base = data.get("base_url") or base
            key = data.get("api_key") or key
            models = (data.get("models") or {}).get("image_generation") or []
            if models:
                model = models[0]
        except Exception:
            pass

    # 环境变量具备最高优先级或用于兜底补全
    base = os.environ.get("NEW_API_BASE_URL") or os.environ.get("AGNES_BASE_URL") or base
    key = os.environ.get("NEW_API_KEY") or key
    model = os.environ.get("AGNES_IMAGE_MODEL") or model
    return base, key, model


def generate(
    prompt: str,
    *,
    size: str = "1024x1024",
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    retries: int = 2,
    timeout: int = 90,
    key_path: Path | str | None = None,
) -> dict:
    if not prompt or not isinstance(prompt, str) or not prompt.strip():
        return {"ok": False, "error": "Prompt must be a non-empty string", "via": "new-api-rotation-pool"}

    base, key, default_model = load_gateway(key_path=key_path)
    base = (base_url or base).rstrip("/")
    key = api_key or key
    model = model or default_model

    payload = {"model": model, "prompt": prompt, "size": size, "n": 1}
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/images/generations",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "AgnesStudio-CoverPipeline/1.1",
            **({"Authorization": f"Bearer {key}"} if key else {}),
        },
    )

    last_err = None
    for attempt in range(retries + 1):
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            item = (data.get("data") or [{}])[0]
            return {
                "ok": True,
                "model": model,
                "base_url": base,
                "cost_s": round(time.time() - t0, 2),
                "url": item.get("url"),
                "b64_json": item.get("b64_json"),
                "attempt": attempt + 1,
                "via": "new-api-rotation-pool",
            }
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:200]}"
        except Exception as e:
            last_err = str(e)
        time.sleep(0.8 * (attempt + 1))
    return {"ok": False, "error": last_err, "via": "new-api-rotation-pool"}


def save_image(result: dict, out: Path | str) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if result.get("b64_json"):
        try:
            out.write_bytes(base64.b64decode(result["b64_json"]))
        except (binascii.Error, ValueError) as e:
            raise ValueError(f"[gateway] invalid base64 image payload: {e}") from e
    elif result.get("url"):
        urllib.request.urlretrieve(result["url"], str(out))
    else:
        raise ValueError(f"[gateway] no image payload: {result}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Agnes 生图 · New API 轮换网关")
    ap.add_argument("--prompt")
    ap.add_argument("--brief", help="简报 JSON，使用其 gen_prompt 或拼 title")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--model")
    args = ap.parse_args()

    prompt = args.prompt
    if args.brief:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from cover_style import load_brief, resolve_style

        brief = load_brief(args.brief)
        style = resolve_style(brief)
        prompt = prompt or style.gen_prompt
        print(f"· style {style.name}")
        print(f"· prompt {prompt[:100]}...")

    if not prompt:
        raise SystemExit("need --prompt or --brief")

    res = generate(prompt, size=args.size, model=args.model)
    if not res.get("ok"):
        raise SystemExit(f"[gateway] {res}")
    try:
        save_image(res, Path(args.out))
    except Exception as e:
        raise SystemExit(f"[gateway] {e}")
    print(
        f"✓ {args.out} via {res['via']} model={res['model']} "
        f"cost={res['cost_s']}s attempt={res['attempt']}"
    )


if __name__ == "__main__":
    main()
