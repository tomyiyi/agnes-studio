#!/usr/bin/env python3
"""字在人后 · v154–v159 未测维度补齐（户外/夜景/产品/多字中文/长英文/A-B）。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from agnes_gateway import generate, save_image  # noqa: E402

BASE = (
    "PRIMARY: {primary} "
    "SECONDARY: giant English condensed word {word} in cream #F3EDE3 as BACKDROP architecture. "
    "ABSOLUTE LAYER ORDER: BACKGROUND then TYPE then PERSON. "
    "Letters {word} pass BEHIND her head and body; hair/face/shoulder silhouette cuts through letterforms; "
    "part of each letter hidden behind her. "
    "FORBIDDEN: type in front of face/body, sticker on her, face gradient, UI, border. "
    "Exactly ONE word {word}. No other text."
)

CN_BASE = (
    "PRIMARY: {primary} "
    "SECONDARY: giant Chinese characters {word} in cream #F3EDE3 as BACKDROP architecture, "
    "modern heavy heiti or song style, architectural scale. "
    "ABSOLUTE LAYER ORDER: BACKGROUND then TYPE then PERSON. "
    "Characters {word} pass BEHIND her head and body; hair/face/shoulder silhouette cuts through the glyphs; "
    "part of each character hidden behind her. "
    "FORBIDDEN: type in front of face/body, sticker on her, face gradient, UI, border, garbled strokes. "
    "Exactly the characters {word}. No other text."
)

WEAK_BASE = (
    "PRIMARY: {primary} "
    f"SECONDARY: the word MODE near her head. "
    "Photorealistic fashion portrait."
)

EXPERIMENTS = [
    # v154 outdoor street
    ("v154", "r154_out", BASE.format(
        primary="young Asian woman long black hair beige trench coat walking on quiet city street, overcast soft daylight, muted asphalt and stone tones, fashion editorial",
        word="OUT")),
    ("v154", "r154_solo", BASE.format(
        primary="young Asian woman cream trench coat standing by concrete wall on empty street, soft daylight, greige urban palette",
        word="SOLO")),
    ("v154", "r154_walk", BASE.format(
        primary="young Asian woman long coat mid-walk city sidewalk, warm greige buildings bokeh, soft fashion light",
        word="WALK")),
    ("v154", "r154_road", BASE.format(
        primary="young Asian woman wool coat on empty road, muted stone and fog, cinematic soft light, fashion editorial",
        word="ROAD")),
    ("v154", "r154_city", BASE.format(
        primary="young Asian woman cream knit and coat against grey concrete architecture, outdoor soft light, fashion poster",
        word="CITY")),
    ("v154", "r154_dawn", BASE.format(
        primary="young Asian woman long hair trench coat at dawn street, pale warm greige atmosphere, soft directional light",
        word="DAWN")),
    # v155 night
    ("v155", "r155_nite", BASE.format(
        primary="young Asian woman long black hair black silk blouse, night studio, soft key light with deep greige shadows, fashion editorial",
        word="NITE")),
    ("v155", "r155_moon", BASE.format(
        primary="young Asian woman cream silk dress, moonlit window night interior, cool soft light, muted charcoal palette",
        word="MOON")),
    ("v155", "r155_ink", BASE.format(
        primary="young Asian woman black hair pale skin black coat, deep charcoal night backdrop, single soft rim light, fashion poster",
        word="INK")),
    ("v155", "r155_hush", BASE.format(
        primary="young Asian woman dark knit, quiet night room, low soft key, warm cream type contrast, editorial",
        word="HUSH")),
    ("v155", "r155_glow", BASE.format(
        primary="young Asian woman silk slip dress, night window city glow bokeh muted, soft fashion light, no neon spam",
        word="GLOW")),
    ("v155", "r155_dusk", BASE.format(
        primary="young Asian woman long hair grey wool coat, dusk greige studio, soft fading light, fashion poster",
        word="DUSK")),
    # v156 product
    ("v156", "r156_bag", BASE.format(
        primary="young Asian woman holding cream leather handbag close, warm greige studio, soft fashion light, product editorial",
        word="BAG")),
    ("v156", "r156_scent", BASE.format(
        primary="young Asian woman with clear perfume bottle at chest, cream and greige studio, soft light, beauty editorial",
        word="SCENT")),
    ("v156", "r156_shoe", BASE.format(
        primary="young Asian woman seated with cream leather shoe on pedestal, greige studio, soft fashion light",
        word="SHOE")),
    ("v156", "r156_silk", BASE.format(
        primary="young Asian woman draping cream silk fabric, warm greige studio, soft light, fashion still-life hybrid",
        word="SILK")),
    ("v156", "r156_rose", BASE.format(
        primary="young Asian woman holding single cream rose, greige studio, soft fashion light, product editorial",
        word="ROSE")),
    ("v156", "r156_pearl", BASE.format(
        primary="young Asian woman with pearl jewelry close-up, cream greige studio, soft beauty light",
        word="PEARL")),
    # v157 Chinese multi-char
    ("v157", "r157_cn_qing", CN_BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="清欢")),
    ("v157", "r157_cn_feng", CN_BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="风骨")),
    ("v157", "r157_cn_liu", CN_BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="留白")),
    ("v157", "r157_cn_mu", CN_BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="暮色")),
    ("v157", "r157_cn_yi", CN_BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="一念")),
    ("v157", "r157_cn_ji", CN_BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="静观")),
    # v158 long English
    ("v158", "r158_eleg", BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="ELEGANT")),
    ("v158", "r158_mod", BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="MODERN")),
    ("v158", "r158_silh", BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="SILHOUETTE")),
    ("v158", "r158_stat", BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="STUDIO")),
    ("v158", "r158_arch", BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="ARCH")),
    ("v158", "r158_luxe", BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="LUXURY")),
    # v159 A/B
    ("v159", "r159_strong_mode", BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="MODE")),
    ("v159", "r159_strong_chic", BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="CHIC")),
    ("v159", "r159_strong_luxe", BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light",
        word="LUXE")),
    ("v159", "r159_weak_mode", WEAK_BASE.format(
        primary="young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light")),
    ("v159", "r159_weak_chic", (
        "PRIMARY: young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light. "
        "SECONDARY: the word CHIC near her head. Photorealistic fashion portrait."
    )),
    ("v159", "r159_weak_luxe", (
        "PRIMARY: young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light. "
        "SECONDARY: the word LUXE near her head. Photorealistic fashion portrait."
    )),
]


def main() -> None:
    report = []
    for ver, stem, prompt in EXPERIMENTS:
        out_dir = ROOT / "outputs" / "workflow_iter" / ver
        out_dir.mkdir(parents=True, exist_ok=True)
        fp = out_dir / f"{stem}.png"
        if fp.exists() and fp.stat().st_size > 20_000:
            print("SKIP", stem)
            report.append({"stem": stem, "ok": True, "skipped": True})
            continue
        r = generate(prompt, size="864x1152", model="agnes-image-2.5-flash", retries=3)
        if r.get("ok"):
            save_image(r, fp)
            print("OK", stem, fp.stat().st_size // 1024)
            report.append({"stem": stem, "ok": True, "path": str(fp)})
        else:
            print("FAIL", stem, str(r)[:100])
            report.append({"stem": stem, "ok": False, "err": str(r)[:200]})
    (ROOT / "outputs" / "workflow_iter" / "batch_v154_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    ok = sum(1 for x in report if x.get("ok"))
    print(f"DONE {ok}/{len(report)}")


if __name__ == "__main__":
    main()
