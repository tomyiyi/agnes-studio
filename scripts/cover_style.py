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

sys_path_scripts = Path(__file__).resolve().parent
if str(sys_path_scripts) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(sys_path_scripts))

from env_config import DATA_DIR

CATALOG_PATH = DATA_DIR / "style_catalog.json"


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


def resolve_style(brief: dict | None = None, **kwargs) -> CoverStyle:
    """按 subject/tone/goal/platform 组合出最终样式；显式字段优先于推导。"""
    cat = load_catalog()
    combined_brief = dict(brief or {})
    combined_brief.update({k: v for k, v in kwargs.items() if v is not None})
    subject = combined_brief.get("subject") or "beauty"
    tone = combined_brief.get("tone") or "luxury"
    goal = combined_brief.get("goal") or "editorial"
    platform = combined_brief.get("platform") or "wechat"
    style_skill = (combined_brief.get("style_skill") or combined_brief.get("skill_id") or "").strip()
    lineage = (combined_brief.get("lineage") or "").strip()
    move = (combined_brief.get("move") or "").strip()
    skill = (cat.get("skill_styles") or {}).get(style_skill) if style_skill else None
    if style_skill and not skill:
        style_skill = ""  # 未知 ID 不注入、不误标

    subj = cat["subjects"].get(subject) or cat["subjects"]["beauty"]
    ton = cat["tones"].get(tone) or cat["tones"]["luxury"]
    gol = cat["goals"].get(goal) or cat["goals"]["editorial"]
    plat = cat["platform_tune"].get(platform) or cat["platform_tune"]["wechat"]

    mode = combined_brief.get("mode") or "auto"
    if mode == "auto":
        mode = (skill or {}).get("mode") or gol["mode"]
    if skill and skill.get("tone") and not combined_brief.get("tone"):
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


def list_catalog_options() -> dict[str, list[str]]:
    """列出样式目录中支持的所有枚举选项（subjects, tones, goals, platforms, modes）"""
    cat = load_catalog()
    return {
        "subjects": sorted(list((cat.get("subjects") or {}).keys())),
        "tones": sorted(list((cat.get("tones") or {}).keys())),
        "goals": sorted(list((cat.get("goals") or {}).keys())),
        "platforms": sorted(list((cat.get("platform_tune") or {}).keys())),
        "modes": ["auto", "diag", "bignews", "stack", "vertical"],
    }


def list_skill_styles() -> list[dict[str, str]]:
    """列出样式目录中预设的生图 Skill 样式映射清单"""
    cat = load_catalog()
    skills = cat.get("skill_styles") or {}
    result: list[dict[str, str]] = []
    for sid, info in sorted(skills.items(), key=lambda x: x[0]):
        result.append({
            "id": sid,
            "call_name": str(info.get("call_name", "")),
            "tone": str(info.get("tone", "")),
            "mode": str(info.get("mode", "")),
        })
    return result


def build_arg_parser():
    import argparse
    parser = argparse.ArgumentParser(
        description="Agnes Studio · 封面需求简报至样式推导引擎 (Cover Style Resolver)"
    )
    parser.add_argument(
        "brief_file",
        nargs="?",
        default=None,
        help="简报 JSON 文件路径（可选，未提供时可通过参数或标准默认推导）",
    )
    parser.add_argument(
        "-b", "--brief",
        dest="brief_opt",
        default=None,
        help="简报 JSON 文件路径（与位置参数 brief_file 等效）",
    )
    parser.add_argument(
        "-j", "--json",
        dest="brief_json",
        default=None,
        help="内联简报 JSON 字符串（如 '{\"subject\": \"product\", \"tone\": \"cyber\"}'）",
    )
    parser.add_argument(
        "--subject",
        default=None,
        help="主体覆盖/指定 (beauty | product | scenery | character | abstract | none)",
    )
    parser.add_argument(
        "--tone",
        default=None,
        help="格调/基调覆盖 (luxury | minimal | cyber | neo-chinese | magazine | warm | fresh | epic)",
    )
    parser.add_argument(
        "--goal",
        default=None,
        help="商业诉求覆盖 (editorial | ctr | brand | story | vertical)",
    )
    parser.add_argument(
        "-p", "--platform",
        default=None,
        help="目标发布平台 (wechat | wechat-sq | xhs | xhs-sq)",
    )
    parser.add_argument(
        "-m", "--mode",
        default=None,
        help="文字排版模式 (auto | diag | bignews | stack | vertical)",
    )
    parser.add_argument(
        "-s", "--style-skill", "--skill",
        dest="style_skill",
        default=None,
        help="覆盖简报中的 Skill ID，如 S05, S07 等",
    )
    parser.add_argument(
        "-o", "--out",
        dest="out_path",
        default=None,
        help="将解析后的样式 JSON 写入指定文件路径",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="列出目录支持的所有选项（主体、基调、目标、平台、排版模式）",
    )
    parser.add_argument(
        "--list-skills",
        action="store_true",
        help="列出目录内置的所有生图 Skill 样式映射清单",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="静默模式，抑制标准输出打印",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式，当指定简报文件不存在或 JSON 格式非法时返回退出码 1",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    import sys
    parser = build_arg_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    try:
        if args.list:
            opts = list_catalog_options()
            if not args.quiet:
                print("Agnes Studio · 封面样式目录预设选项:")
                for category, values in opts.items():
                    print(f"  [{category}]: {', '.join(values)}")
            return 0

        if args.list_skills:
            skills = list_skill_styles()
            if not args.quiet:
                print(f"Agnes Studio · 封面预设 Skill 样式映射 (共 {len(skills)} 项):")
                for item in skills:
                    print(f"  [{item['id']:<5}] {item['call_name']:<18} | tone: {item['tone']:<12} | mode: {item['mode']}")
            return 0

        brief_path = args.brief_opt or args.brief_file
        brief_data: dict = {}

        if brief_path:
            p = Path(brief_path)
            if not p.is_file():
                if not args.quiet:
                    sys.stderr.write(f"❌ 找不到简报文件: {brief_path}\n")
                return 1
            try:
                brief_data = load_brief(p)
            except Exception as e:
                if not args.quiet:
                    sys.stderr.write(f"❌ 解析简报文件失败 {brief_path}: {e}\n")
                return 1
        elif args.brief_json:
            try:
                brief_data = json.loads(args.brief_json)
                if not isinstance(brief_data, dict):
                    raise ValueError("JSON 根对象必须为字典")
            except Exception as e:
                if not args.quiet:
                    sys.stderr.write(f"❌ 解析简报 JSON 字符串失败: {e}\n")
                return 1

        # CLI 参数覆盖优先级最高
        if args.subject:
            brief_data["subject"] = args.subject
        if args.tone:
            brief_data["tone"] = args.tone
        if args.goal:
            brief_data["goal"] = args.goal
        if args.platform:
            brief_data["platform"] = args.platform
        if args.mode:
            brief_data["mode"] = args.mode
        if args.style_skill:
            brief_data["style_skill"] = args.style_skill

        style = resolve_style(brief_data)
        out_dict = style.to_dict()
        out_json_str = json.dumps(out_dict, ensure_ascii=False, indent=2)

        if args.out_path:
            out_p = Path(args.out_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(out_json_str, encoding="utf-8")

        if not args.quiet:
            print(out_json_str)
        return 0
    except Exception as e:
        if not args.quiet:
            sys.stderr.write(f"❌ 封面样式推导异常: {e}\n")
        return 1


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
