#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
封面需求变量解析器 Brief → Style
================================

海报需求是变量，不是固定模板。本模块把简报映射为：
  - gen_prompt   生图提示词骨架
  - font_stack   字体组合
  - mode         文字版式
  - palette      色板
  - layout       排版旋钮（字阶/scrim/标题区）
  - copy_tone    文案语气

简报字段（均可缺省，缺省走 goal/platform 默认链）：
  platform: wechat | wechat-sq | xhs | xhs-sq
  goal:     editorial | ctr | brand | story
  subject:  beauty | product | scenery | character | abstract | none
  tone:     luxury | minimal | cyber | neo-chinese | magazine | warm | fresh
  mode:     auto | diag | bignews | stack
  style_skill: S05 | S07 | ...   # 可选，生图 Skill 合集 71 项 ID
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "data" / "style_catalog.json"


@dataclass
class CoverStyle:
    name: str
    mode: str
    hero_size: int
    sub_size: int
    font_css: str
    palette: dict
    scrim: str
    photo_filter: str
    gen_prompt: str
    copy_tone: str
    title_zone_default: str
    place: list
    notes: str
    style_skill: str = ""
    skill_call_name: str = ""
    license_note: str = ""
    lineage: str = ""
    move: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def resolve_style(brief: dict) -> CoverStyle:
    """按 subject/tone/goal/platform 组合出最终样式；显式字段优先于推导。"""
    cat = load_catalog()
    subject = brief.get("subject") or "beauty"
    tone = brief.get("tone") or "luxury"
    goal = brief.get("goal") or "editorial"
    platform = brief.get("platform") or "wechat"
    style_skill = (brief.get("style_skill") or brief.get("skill_id") or "").strip()
    lineage = (brief.get("lineage") or "").strip()
    move = (brief.get("move") or "").strip()
    skill = (cat.get("skill_styles") or {}).get(style_skill) if style_skill else None
    if style_skill and not skill:
        style_skill = ""  # 未知 ID 不注入、不误标

    subj = cat["subjects"].get(subject) or cat["subjects"]["beauty"]
    ton = cat["tones"].get(tone) or cat["tones"]["luxury"]
    gol = cat["goals"].get(goal) or cat["goals"]["editorial"]
    plat = cat["platform_tune"].get(platform) or cat["platform_tune"]["wechat"]

    mode = brief.get("mode") or "auto"
    if mode == "auto":
        mode = (skill or {}).get("mode") or gol["mode"]
    if skill and skill.get("tone") and not brief.get("tone"):
        ton = cat["tones"].get(skill["tone"]) or ton

    # 字体：tone 主导，subject 可覆盖衬线感
    font_css = ton["font_css"]
    if subject in ("scenery", "product") and tone not in ("cyber",):
        font_css = cat["font_stacks"]["serif_east"]

    palette = {**ton["palette"], **plat.get("palette_overlay", {})}
    hero = int(plat["hero_size"] * ton.get("type_scale", 1.0))
    sub = max(11, int(plat["sub_size"] * ton.get("type_scale", 1.0)))

    grand_space = "cinematic scale contrast, negative space 40-55% for typography, no clutter, premium restraint"
    clean_frame = (
        "absolutely clean frame, no text, no letters, no captions, no logo, "
        "no watermark, no signature, no timestamp, no UI overlay, no badge, "
        "no small print, no corner stamp, no floating sticker, no glitch block, "
        "no rectangular artifact, seamless background, ultra sharp"
    )
    if skill:
        # skill.fragment 已含净框/留字策略，避免与 clean_frame 双重否定
        gen_prompt = (
            f"{subj['gen_prompt']}, {ton['gen_prompt']}, {gol['gen_prompt']}, "
            f"{skill['prompt_fragment']}, ultra sharp"
        )
        notes = (
            f"tone={tone} subject={subject} goal={goal} platform={platform} "
            f"style_skill={style_skill}/{skill['call_name']}"
        )
    else:
        gen_prompt = (
            f"{subj['gen_prompt']}, {ton['gen_prompt']}, {gol['gen_prompt']}, "
            f"{clean_frame}, {grand_space}"
        )
        notes = f"tone={tone} subject={subject} goal={goal} platform={platform}"

    return CoverStyle(
        name=f"{tone}/{subject}/{goal}/{mode}"
        + (f"/{style_skill}" if style_skill else ""),
        mode=mode,
        hero_size=hero,
        sub_size=sub,
        font_css=font_css,
        palette=palette,
        scrim=ton["scrim"],
        photo_filter=ton.get("photo_filter", "saturate(0.92) contrast(1.05)"),
        gen_prompt=gen_prompt,
        copy_tone=gol["copy_tone"],
        title_zone_default=gol.get("title_zone", "safe"),
        place=list(plat.get("place", [0.58, 0.4])),
        notes=notes,
        style_skill=style_skill,
        skill_call_name=(skill or {}).get("call_name", ""),
        license_note=(skill or {}).get("license_note", ""),
        lineage=lineage,
        move=move,
    )


def load_brief(path: str | Path) -> dict:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="解析封面简报 → 样式")
    ap.add_argument("brief")
    ap.add_argument("--style-skill", default=None, help="覆盖简报中的 Skill ID，如 S05")
    args = ap.parse_args()
    brief = load_brief(args.brief)
    if args.style_skill:
        brief["style_skill"] = args.style_skill
    st = resolve_style(brief)
    print(json.dumps(st.to_dict(), ensure_ascii=False, indent=2))
