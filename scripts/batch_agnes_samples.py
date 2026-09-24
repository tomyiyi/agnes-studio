#!/usr/bin/env python3
"""按 data/gpt_image_agnes_prompts.json 逐条 Agnes 出样张。"""
from __future__ import annotations
import json, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from agnes_gateway import generate, save_image

LIB = ROOT / "data" / "gpt_image_agnes_prompts.json"
OUT = ROOT / "outputs" / "agnes_samples"
OUT.mkdir(parents=True, exist_ok=True)

def slugify(s: str) -> str:
    s = re.sub(r"[^\w一-鿿-]+", "-", s).strip("-")
    return s[:36] or "item"

def one(item: dict) -> dict:
    iid = str(item["id"]).replace("/", "-")
    name = f"{iid}_{slugify(item.get('title') or 'x')}.png"
    path = OUT / name
    if path.exists() and path.stat().st_size > 20_000:
        return {"id": iid, "ok": True, "skipped": True, "path": str(path)}
    prompt = item.get("agnes_prompt") or item.get("gpt_image_prompt") or ""
    if len(prompt) < 40:
        return {"id": iid, "ok": False, "error": "prompt too short"}
    size = item.get("agnes_size") or "1088x1456"
    res = generate(prompt, size=size, model="agnes-image-2.5-flash", retries=2)
    if not res.get("ok"):
        return {"id": iid, "ok": False, "error": str(res)[:200]}
    save_image(res, path)
    return {"id": iid, "ok": True, "path": str(path), "cost_s": res.get("cost_s"), "kb": path.stat().st_size // 1024}

def main() -> None:
    data = json.loads(LIB.read_text(encoding="utf-8"))
    items = data["items"]
    print(f"items={len(items)} → {OUT}")
    results = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(one, it): it for it in items}
        done = 0
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            done += 1
            mark = "✓" if r.get("ok") else "✗"
            print(f"{mark} [{done}/{len(items)}] {r.get('id')} {r.get('kb', 0)}KB {r.get('error', '')[:60]}", flush=True)
    ok = sum(1 for r in results if r.get("ok"))
    (OUT / "batch_report.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"done ok={ok}/{len(results)}")

if __name__ == "__main__":
    main()
