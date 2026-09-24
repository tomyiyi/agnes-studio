#!/usr/bin/env python3
"""按 data/gpt_image_agnes_prompts.json 逐条 Agnes 出图。"""
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
REPORT = OUT / "_batch_report.json"

def slugify(s: str) -> str:
    s = re.sub(r"[^\w一-鿿-]+", "-", s).strip("-")
    return s[:32] or "item"

def run_one(item: dict) -> dict:
    iid = str(item.get("id")).replace("/", "-")
    name = f"{iid}_{slugify(item.get('title') or '')}.png"
    out = OUT / name
    rec = {"id": iid, "title": item.get("title"), "file": name, "ok": False}
    if out.exists() and out.stat().st_size > 20_000:
        rec.update(ok=True, skipped=True, kb=out.stat().st_size // 1024)
        return rec
    prompt = item.get("agnes_prompt") or item.get("gpt_image_prompt") or ""
    size = item.get("agnes_size") or "1088x1456"
    try:
        res = generate(prompt, size=size, retries=2)
    except Exception as e:
        rec["error"] = f"exc:{e}"
        return rec
    if not res.get("ok"):
        rec["error"] = str(res)[:300]
        return rec
    save_image(res, out)
    rec.update(ok=True, kb=out.stat().st_size // 1024, cost_s=res.get("cost_s"), via=res.get("via"))
    return rec

def main() -> None:
    data = json.loads(LIB.read_text(encoding="utf-8"))
    items = data["items"]
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    if only:
        items = [it for it in items if str(it.get("id")) in set(only)]
    print(f"items={len(items)} → {OUT}")
    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(run_one, it): it for it in items}
        for i, fut in enumerate(as_completed(futs), 1):
            rec = fut.result()
            results.append(rec)
            status = "✓" if rec.get("ok") else "✗"
            print(f"{status} [{i}/{len(items)}] {rec['id']} {rec.get('file','')} {rec.get('kb','')}KB {rec.get('error','')[:80]}", flush=True)
    ok = sum(1 for r in results if r.get("ok"))
    REPORT.write_text(json.dumps({"ok": ok, "total": len(results), "elapsed_s": round(time.time()-t0,1), "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"done ok={ok}/{len(results)} report={REPORT}")

if __name__ == "__main__":
    main()
