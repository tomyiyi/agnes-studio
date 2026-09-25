#!/usr/bin/env python3
"""71 项生图 Skill 各出 1 张风格样张（Agnes / New API，禁止 MiMo image_gen）。"""
from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from agnes_gateway import generate, save_image  # noqa: E402

INDEX = ROOT / "data" / "skills_71_index.json"
OUT = ROOT / "outputs" / "skill71_samples"
OUT.mkdir(parents=True, exist_ok=True)

# 统一主体，便于横向比风格；净框后缀去水印/角标
BASE_SUBJECT = (
    "editorial photograph of a young East Asian woman in a light linen dress, "
    "three-quarter view, soft daylight, city cafe terrace with plants, "
    "clear subject identity, natural skin texture, film-like grain"
)
CLEAN = (
    "absolutely clean frame, no text, no letters, no logo, no watermark, "
    "no signature, no corner stamp, no glitch block, ultra sharp, 8k"
)


def slugify(s: str) -> str:
    s = re.sub(r"[^\w一-鿿-]+", "-", s).strip("-")
    return s[:28] or "item"


def one(s: dict) -> dict:
    sid = s["id"]
    path = OUT / f"{sid}_{slugify(s['display_name'])}.png"
    if path.exists() and path.stat().st_size > 20_000:
        return {"id": sid, "ok": True, "skipped": True, "path": str(path)}
    style = s.get("style") or s.get("scope") or s["declared_skill_name"]
    keep_text = (s.get("ages") or {}).get("keep_text")
    frame = (
        "intentional poster lettering allowed if the style requires typography"
        if keep_text
        else CLEAN
    )
    prompt = (
        f"{BASE_SUBJECT}. "
        f"Visual style transform: {style}. "
        f"Constraints: {s.get('scope') or ''}. "
        f"{frame}. "
        "photo-derived restyle, preserve core subject identity and scene facts"
    )
    res = generate(prompt, size="1088x1456", model="agnes-image-2.5-flash", retries=2)
    if not res.get("ok"):
        return {"id": sid, "ok": False, "error": str(res)[:220]}
    save_image(res, path)
    return {
        "id": sid,
        "ok": True,
        "path": str(path),
        "file": path.name,
        "cost_s": res.get("cost_s"),
        "kb": path.stat().st_size // 1024,
        "prompt": prompt,
    }


def main() -> None:
    skills = json.loads(INDEX.read_text(encoding="utf-8"))["skills"]
    print(f"skills={len(skills)} → {OUT}", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(one, s): s for s in skills}
        done = 0
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            done += 1
            mark = "✓" if r.get("ok") else "✗"
            print(
                f"{mark} [{done}/{len(skills)}] {r.get('id')} "
                f"{r.get('kb', 0)}KB {r.get('error', '')[:70]}",
                flush=True,
            )
    ok = sum(1 for r in results if r.get("ok"))
    (OUT / "batch_report.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"done ok={ok}/{len(results)}", flush=True)


if __name__ == "__main__":
    main()
