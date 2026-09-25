#!/usr/bin/env python3
"""其它版式编号册：12 种构图（非字在人后），出图后拼编号板。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from agnes_gateway import generate, save_image  # noqa: E402

OUT = ROOT / "outputs" / "layout_variants" / "L1"

# 12 种版式（大气/高级/设计感；与「字在人后」区分开）
LAYOUTS = [
    # 01 瑞士非对称 · 左字塔右图窗
    ("01_swiss_asym", (
        "Elegant fashion poster, Swiss asymmetric layout. LEFT 38% vertical type tower on warm greige paper: "
        "small kicker, huge condensed title word FORM, thin slogan line, tiny number 01. "
        "RIGHT 52% photo window of young Asian woman cream knit sweater, soft studio light. "
        "Type NEVER overlaps her face or body; type lives in left column only. "
        "12-column awareness, outer margin 7%, left-aligned system. "
        "FORBIDDEN: type in front of person, stickers, gradient on face, UI chrome, border frame. "
        "Large negative space, editorial luxury, cream #F3EDE3 ink. Exactly one main word FORM."
    )),
    # 02 瑞士非对称 · 变体词
    ("02_swiss_asym", (
        "Elegant fashion poster, Swiss asymmetric editorial grid. LEFT third: stacked type tower — "
        "tiny kicker, monumental condensed word SILK, micro caption, index 02. "
        "RIGHT two-thirds: portrait window, young Asian woman in silk blouse, warm greige studio. "
        "Strict column alignment, no type over face or body. "
        "Whitespace 45%+, one thin rule + tiny number only. "
        "FORBIDDEN: type in front, stickers, face gradient, UI, border. Exactly one main word SILK."
    )),
    # 03 上字带下图场
    ("03_type_band", (
        "Cinematic poster layout: TOP 38% solid warm greige text band with giant condensed title MODE, "
        "small kicker and right-aligned micro info. BOTTOM 62% photo field: young Asian woman cream knit, "
        "soft fashion light, greige seamless. Soft gradient scrim only at band/image seam. "
        "Main title NEVER placed on the photo, never over her face. Type scale 8:1 inside band. "
        "FORBIDDEN: type on person, stickers, face gradient, UI, hard black bars. Exactly one main word MODE."
    )),
    # 04 上字带下图场 · 变体
    ("04_type_band", (
        "Editorial poster: upper 40% ivory text band with monumental word ARIA, thin Latin subline, "
        "tiny date-like micro text. Lower 60% full photo — young Asian woman long black hair, cream knit, "
        "quiet studio. Soft fade at seam. Title stays in band only. "
        "Luxury fashion magazine density: huge title + tiny facts, nothing else. "
        "FORBIDDEN: type over face/body, stickers, face gradient, UI, border. Exactly one main word ARIA."
    )),
    # 05 对角张力
    ("05_axis_tension", (
        "Dynamic fashion poster with diagonal tension layout. Upper RIGHT: small Western word CHIC + year-like number, "
        "long thin tracking line. Lower LEFT: monumental condensed title LUXE pressed to the corner. "
        "CENTER 40% reserved for young Asian woman, cream knit, greige studio, soft light. "
        "Reading path forms a diagonal Z. Title highest weight, Western tracking +300%. "
        "Type never covers face or body. FORBIDDEN: type in front of person, stickers, face gradient, UI. "
        "Exactly one main word LUXE."
    )),
    # 06 对角张力 · 变体
    ("06_axis_tension", (
        "Bold editorial poster, diagonal composition. Top-right thin Latin word plus tracking line and micro number. "
        "Bottom-left giant black condensed word RUSH. Middle diagonal lane holds young Asian woman in motion-ready pose, "
        "cream and greige palette, soft light. High energy via layout not effects. "
        "Type in corners only, person fully readable. FORBIDDEN: type on face, stickers, gradients, UI chrome. "
        "Exactly one main word RUSH."
    )),
    # 07 杂志开窗
    ("07_window_editorial", (
        "Minimal magazine spread poster: vast ivory paper, large negative space. Center rectangular photo window "
        "showing young Asian woman cream knit sweater, soft light. LEFT side vertical spine title stacked as "
        "one elegant word OPEN. Thin caption line under window. Small index 07. "
        "No type inside window over her. Quiet gallery/editorial luxury. "
        "FORBIDDEN: type in front of person, stickers, face gradient, UI, heavy frames. Exactly one main word OPEN."
    )),
    # 08 杂志开窗 · 变体
    ("08_window_editorial", (
        "Art-book poster: cream paper field with generous margins. A single off-center photo window with "
        "young Asian woman, warm greige studio. Vertical Chinese-free Latin spine word VIEW at left edge, "
        "tiny caption under window, one thin rule. Extremely calm, 55% whitespace. "
        "Type never overlays the photo subject. FORBIDDEN: type on person, stickers, face gradient, UI, border. "
        "Exactly one main word VIEW."
    )),
    # 09 独主体 + 大空场
    ("09_solo_space", (
        "Grand minimal poster: one small-medium figure of young Asian woman cream knit sweater placed on "
        "lower-right third, floating in vast greige empty field. Tiny Latin word ALONE high left, "
        "one thin rule, nothing else. Subject 25% visual weight, air 60%+. "
        "Monumental emptiness. Type far from her, never overlapping. "
        "FORBIDDEN: type in front, stickers, face gradient, UI, clutter. Exactly one main word ALONE."
    )),
    # 10 中轴庄严
    ("10_axis_center", (
        "Solemn centered poster, ceremonial symmetry. Vertical axis: small kicker, huge centered condensed word "
        "SOLEMN, thin flanking micro lines left and right. Young Asian woman centered below or behind the axis "
        "field in cream knit, greige studio. Symmetric, few colors, heavy material quietness. "
        "Type and figure share the axis without type covering face. "
        "FORBIDDEN: type in front of face, stickers, face gradient, UI. Exactly one main word SOLEMN."
    )),
    # 11 上文下图（电影感）
    ("11_text_top", (
        "Film-poster layout: pure cream/greige top text zone with monumental title NOIR, kicker and one micro line. "
        "Below, a clean photo zone of young Asian woman, dramatic soft light, cream knit. "
        "Hard soft-scrim divide. Title never on the photo. Calm luxury cinema poster. "
        "FORBIDDEN: type on person, stickers, face gradient, UI chrome. Exactly one main word NOIR."
    )),
    # 12 巨字极简
    ("12_giant_minimal", (
        "Extreme minimal giant-type poster: one enormous condensed word VOID filling the upper field in cream "
        "on greige, one thin Latin line and a tiny number only. Young Asian woman small, lower third, "
        "cream knit sweater, quiet light. Nearly nothing else. Poster impact from scale contrast 16:1. "
        "Type is backdrop field, person sits in front of type field but face fully clear; "
        "or type is solid area separate from person. Never sticker type on face. "
        "FORBIDDEN: type in front of face as sticker, face gradient, UI, borders, extra words. "
        "Exactly one main word VOID."
    )),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report = []
    for stem, prompt in LAYOUTS:
        fp = OUT / f"{stem}.png"
        if fp.exists() and fp.stat().st_size > 20_000:
            print("SKIP", stem)
            report.append({"stem": stem, "ok": True, "skipped": True})
            continue
        r = generate(prompt, size="864x1152", model="agnes-image-2.5-flash", retries=3)
        if r.get("ok"):
            save_image(r, fp)
            print("OK", stem, fp.stat().st_size // 1024)
            report.append({"stem": stem, "ok": True})
        else:
            print("FAIL", stem, str(r)[:100])
            report.append({"stem": stem, "ok": False, "err": str(r)[:200]})
    (OUT / "batch_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("DONE", sum(1 for x in report if x.get("ok")), "/", len(report))


if __name__ == "__main__":
    main()
