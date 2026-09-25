#!/usr/bin/env python3
"""把 skill71 样张并入 public/index.html 画廊 + 修正分类计数。"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "public" / "index.html"
SAMPLES = ROOT / "outputs" / "skill71_samples"
ASSETS = ROOT / "public" / "assets" / "skill71_samples"
INDEX = ROOT / "data" / "skills_71_index.json"
ASSETS.mkdir(parents=True, exist_ok=True)

GROUP_META = {
    "照片转超现实叙事": ("skill-surreal", "照片转超现实叙事"),
    "光色与氛围改造": ("skill-atmosphere", "光色与氛围改造"),
    "照片转插画与材质": ("skill-illustration", "照片转插画与材质"),
    "照片转编辑海报": ("skill-poster", "照片转编辑海报"),
    "照片转明信片与记忆档案": ("skill-memory", "照片转明信片与记忆档案"),
    "照片抽象转译": ("skill-abstract", "照片抽象转译"),
}


def main() -> None:
    t = HTML.read_text(encoding="utf-8")
    skills = json.loads(INDEX.read_text(encoding="utf-8"))["skills"]
    report = {}
    rp = SAMPLES / "batch_report.json"
    if rp.exists():
        report = {r["id"]: r for r in json.loads(rp.read_text(encoding="utf-8"))}

    items = []
    copied = 0
    for s in skills:
        sid = s["id"]
        r = report.get(sid) or {}
        src = Path(r["path"]) if r.get("path") else None
        if not src or not src.exists():
            # fallback: any matching sample
            cands = list(SAMPLES.glob(f"{sid}_*.png"))
            src = cands[0] if cands else None
        if not src or not src.exists():
            print("MISS", sid)
            continue
        dest = ASSETS / src.name
        dest.write_bytes(src.read_bytes())
        copied += 1
        gid, gname = GROUP_META[s["group"]]
        items.append(
            {
                "id": f"skill71_{sid}",
                "title": f"{sid} · {s['display_name']}",
                "category_id": gid,
                "category_name": gname,
                "style_tag": f"{sid} · {s['declared_skill_name']}",
                "style_slug": s["declared_skill_name"],
                "desc": s.get("style") or "",
                "prompt": f"style_skill:{sid} · {s['declared_skill_name']} · {s.get('style') or ''}",
                "duration": round(float(r.get("cost_s") or 0), 2),
                "img": f"skill71_samples/{src.name}",
                "aspect_ratio": "3:4",
                "model": "agnes-image-2.5-flash",
                "series": "生图 Skill 合集 · 71 项",
                "license": s.get("license_note") or "",
            }
        )

    print(f"copied {copied} samples, gallery items {len(items)}")

    # inject/replace SKILL71_GALLERY
    payload = json.dumps(items, ensure_ascii=False)
    const = f"const SKILL71_GALLERY = {payload};\n"
    if "const SKILL71_GALLERY" in t:
        t = re.sub(r"const SKILL71_GALLERY = \[.*?\];\n", const, t, count=1, flags=re.S)
    else:
        t = t.replace("const ALL_GALLERY =", const + "const ALL_GALLERY =", 1)

    t = t.replace(
        "const ALL_GALLERY = [...GPT_AGNES_GALLERY, ...MASTER_GALLERY];",
        "const ALL_GALLERY = [...GPT_AGNES_GALLERY, ...MASTER_GALLERY, ...(typeof SKILL71_GALLERY !== 'undefined' ? SKILL71_GALLERY : [])];",
        1,
    )

    # rebuild MASTER_CATEGORIES with real counts from all three lists
    # parse existing galleries
    def load_const(name: str) -> list:
        m = re.search(rf"const {name} = (\[.*?\]);\n", t, re.S)
        return json.loads(m.group(1)) if m else []

    gpt = load_const("GPT_AGNES_GALLERY")
    master = load_const("MASTER_GALLERY")
    skill = items
    all_items = gpt + master + skill
    counts = Counter(x["category_id"] for x in all_items)
    names = {x["category_id"]: x["category_name"] for x in all_items}

    # preserve original category order, then skill groups
    order = [
        ("all", "全部作品全景"),
        ("asian-portraits", "亚洲美人写真"),
        ("character-consistency", "角色一致性 (同一人跨场景)"),
        ("fullbody-fashion", "全身站姿与高级时装"),
        ("commercial-posters", "动漫概念海报 (中文矢量排版)"),
        ("infographics", "Bento 便当格信息图"),
        ("product-commercial", "商业静物与产品摄影"),
        ("3d-assets", "3D 黏土资产与盲盒"),
        ("gpt-portrait", "GPT 人像写真"),
        ("gpt-commercial", "GPT 商业广告"),
        ("gpt-poster", "GPT 海报"),
        ("gpt-infographic", "GPT 信息图"),
    ]
    for g, (gid, gname) in GROUP_META.items():
        order.append((gid, gname))

    cats = []
    for cid, cname in order:
        n = len(all_items) if cid == "all" else counts.get(cid, 0)
        if cid != "all" and n == 0:
            continue
        cats.append({"id": cid, "name": cname, "count": n})
    cats_js = json.dumps(cats, ensure_ascii=False)
    t = re.sub(
        r"const MASTER_CATEGORIES = \[.*?\];\n",
        f"const MASTER_CATEGORIES = {cats_js};\n",
        t,
        count=1,
        flags=re.S,
    )

    # nav label
    total = len(all_items)
    t = re.sub(
        r"资产画廊 \(\d+\)",
        f"资产画廊 ({total})",
        t,
        count=1,
    )

    HTML.write_text(t, encoding="utf-8")
    meta = {
        "gallery_total": total,
        "skill71": len(skill),
        "categories": cats,
        "copied": copied,
    }
    (ROOT / "data" / "gallery_skill71_merge.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
