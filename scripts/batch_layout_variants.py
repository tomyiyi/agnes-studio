#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agnes Studio · 12 款经典构图版式编号册生成器 (L1 级版式变体).

12 种构图范式（非字在人后，强调负空间、瑞士网格、中轴庄严、对角张力等）：
- 01 瑞士非对称 · 左字塔右图窗 (FORM)
- 02 瑞士非对称 · 变体词 (SILK)
- 03 上字带下图场 (MODE)
- 04 上字带下图场 · 变体 (ARIA)
- 05 对角张力 (LUXE)
- 06 对角张力 · 变体 (RUSH)
- 07 杂志开窗 (OPEN)
- 08 杂志开窗 · 变体 (VIEW)
- 09 独主体 + 大空场 (ALONE)
- 10 中轴庄严 (SOLEMN)
- 11 上文下图（电影感） (NOIR)
- 12 巨字极简 (VOID)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from agnes_gateway import generate, save_image  # noqa: E402
except ImportError:
    generate = None  # type: ignore
    save_image = None  # type: ignore

DEFAULT_OUT_DIR = ROOT / "outputs" / "layout_variants" / "L1"
OUT = DEFAULT_OUT_DIR


def classify_generation_error(error: object) -> str:
    """将网关/认证/业务失败分层，避免报告把 502 误报成版式生图失败。"""
    text = str(error or "").lower()
    if "http 502" in text or "bad gateway" in text:
        return "gateway_502"
    if any(token in text for token in ("http 401", "http 403", "unauthorized", "forbidden", "token_rejected")):
        return "auth"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    return "generation_error"


# 12 款版式注册表
LAYOUT_VARIANTS: dict[str, dict[str, Any]] = {
    "01_swiss_asym": {
        "index": 1,
        "stem": "01_swiss_asym",
        "category": "swiss_asym",
        "name": "瑞士非对称 · 左字塔右图窗",
        "word": "FORM",
        "prompt": (
            "Elegant fashion poster, Swiss asymmetric layout. LEFT 38% vertical type tower on warm greige paper: "
            "small kicker, huge condensed title word FORM, thin slogan line, tiny number 01. "
            "RIGHT 52% photo window of young Asian woman cream knit sweater, soft studio light. "
            "Type NEVER overlaps her face or body; type lives in left column only. "
            "12-column awareness, outer margin 7%, left-aligned system. "
            "FORBIDDEN: type in front of person, stickers, gradient on face, UI chrome, border frame. "
            "Large negative space, editorial luxury, cream #F3EDE3 ink. Exactly one main word FORM."
        ),
    },
    "02_swiss_asym": {
        "index": 2,
        "stem": "02_swiss_asym",
        "category": "swiss_asym",
        "name": "瑞士非对称 · 变体词",
        "word": "SILK",
        "prompt": (
            "Elegant fashion poster, Swiss asymmetric editorial grid. LEFT third: stacked type tower — "
            "tiny kicker, monumental condensed word SILK, micro caption, index 02. "
            "RIGHT two-thirds: portrait window, young Asian woman in silk blouse, warm greige studio. "
            "Strict column alignment, no type over face or body. "
            "Whitespace 45%+, one thin rule + tiny number only. "
            "FORBIDDEN: type in front, stickers, face gradient, UI, border. Exactly one main word SILK."
        ),
    },
    "03_type_band": {
        "index": 3,
        "stem": "03_type_band",
        "category": "type_band",
        "name": "上字带下图场",
        "word": "MODE",
        "prompt": (
            "Cinematic poster layout: TOP 38% solid warm greige text band with giant condensed title MODE, "
            "small kicker and right-aligned micro info. BOTTOM 62% photo field: young Asian woman cream knit, "
            "soft fashion light, greige seamless. Soft gradient scrim only at band/image seam. "
            "Main title NEVER placed on the photo, never over her face. Type scale 8:1 inside band. "
            "FORBIDDEN: type on person, stickers, face gradient, UI, hard black bars. Exactly one main word MODE."
        ),
    },
    "04_type_band": {
        "index": 4,
        "stem": "04_type_band",
        "category": "type_band",
        "name": "上字带下图场 · 变体",
        "word": "ARIA",
        "prompt": (
            "Editorial poster: upper 40% ivory text band with monumental word ARIA, thin Latin subline, "
            "tiny date-like micro text. Lower 60% full photo — young Asian woman long black hair, cream knit, "
            "quiet studio. Soft fade at seam. Title stays in band only. "
            "Luxury fashion magazine density: huge title + tiny facts, nothing else. "
            "FORBIDDEN: type over face/body, stickers, face gradient, UI, border. Exactly one main word ARIA."
        ),
    },
    "05_axis_tension": {
        "index": 5,
        "stem": "05_axis_tension",
        "category": "axis_tension",
        "name": "对角张力",
        "word": "LUXE",
        "prompt": (
            "Dynamic fashion poster with diagonal tension layout. Upper RIGHT: small Western word CHIC + year-like number, "
            "long thin tracking line. Lower LEFT: monumental condensed title LUXE pressed to the corner. "
            "CENTER 40% reserved for young Asian woman, cream knit, greige studio, soft light. "
            "Reading path forms a diagonal Z. Title highest weight, Western tracking +300%. "
            "Type never covers face or body. FORBIDDEN: type in front of person, stickers, face gradient, UI. "
            "Exactly one main word LUXE."
        ),
    },
    "06_axis_tension": {
        "index": 6,
        "stem": "06_axis_tension",
        "category": "axis_tension",
        "name": "对角张力 · 变体",
        "word": "RUSH",
        "prompt": (
            "Bold editorial poster, diagonal composition. Top-right thin Latin word plus tracking line and micro number. "
            "Bottom-left giant black condensed word RUSH. Middle diagonal lane holds young Asian woman in motion-ready pose, "
            "cream and greige palette, soft light. High energy via layout not effects. "
            "Type in corners only, person fully readable. FORBIDDEN: type on face, stickers, gradients, UI chrome. "
            "Exactly one main word RUSH."
        ),
    },
    "07_window_editorial": {
        "index": 7,
        "stem": "07_window_editorial",
        "category": "window_editorial",
        "name": "杂志开窗",
        "word": "OPEN",
        "prompt": (
            "Minimal magazine spread poster: vast ivory paper, large negative space. Center rectangular photo window "
            "showing young Asian woman cream knit sweater, soft light. LEFT side vertical spine title stacked as "
            "one elegant word OPEN. Thin caption line under window. Small index 07. "
            "No type inside window over her. Quiet gallery/editorial luxury. "
            "FORBIDDEN: type in front of person, stickers, face gradient, UI, heavy frames. Exactly one main word OPEN."
        ),
    },
    "08_window_editorial": {
        "index": 8,
        "stem": "08_window_editorial",
        "category": "window_editorial",
        "name": "杂志开窗 · 变体",
        "word": "VIEW",
        "prompt": (
            "Art-book poster: cream paper field with generous margins. A single off-center photo window with "
            "young Asian woman, warm greige studio. Vertical Chinese-free Latin spine word VIEW at left edge, "
            "tiny caption under window, one thin rule. Extremely calm, 55% whitespace. "
            "Type never overlays the photo subject. FORBIDDEN: type on person, stickers, face gradient, UI, border. "
            "Exactly one main word VIEW."
        ),
    },
    "09_solo_space": {
        "index": 9,
        "stem": "09_solo_space",
        "category": "solo_space",
        "name": "独主体 + 大空场",
        "word": "ALONE",
        "prompt": (
            "Grand minimal poster: one small-medium figure of young Asian woman cream knit sweater placed on "
            "lower-right third, floating in vast greige empty field. Tiny Latin word ALONE high left, "
            "one thin rule, nothing else. Subject 25% visual weight, air 60%+. "
            "Monumental emptiness. Type far from her, never overlapping. "
            "FORBIDDEN: type in front, stickers, face gradient, UI, clutter. Exactly one main word ALONE."
        ),
    },
    "10_axis_center": {
        "index": 10,
        "stem": "10_axis_center",
        "category": "axis_center",
        "name": "中轴庄严",
        "word": "SOLEMN",
        "prompt": (
            "Solemn centered poster, ceremonial symmetry. Vertical axis: small kicker, huge centered condensed word "
            "SOLEMN, thin flanking micro lines left and right. Young Asian woman centered below or behind the axis "
            "field in cream knit, greige studio. Symmetric, few colors, heavy material quietness. "
            "Type and figure share the axis without type covering face. "
            "FORBIDDEN: type in front of face, stickers, face gradient, UI. Exactly one main word SOLEMN."
        ),
    },
    "11_text_top": {
        "index": 11,
        "stem": "11_text_top",
        "category": "text_top",
        "name": "上文下图（电影感）",
        "word": "NOIR",
        "prompt": (
            "Film-poster layout: pure cream/greige top text zone with monumental title NOIR, kicker and one micro line. "
            "Below, a clean photo zone of young Asian woman, dramatic soft light, cream knit. "
            "Hard soft-scrim divide. Title never on the photo. Calm luxury cinema poster. "
            "FORBIDDEN: type on person, stickers, face gradient, UI chrome. Exactly one main word NOIR."
        ),
    },
    "12_giant_minimal": {
        "index": 12,
        "stem": "12_giant_minimal",
        "category": "giant_minimal",
        "name": "巨字极简",
        "word": "VOID",
        "prompt": (
            "Extreme minimal giant-type poster: one enormous condensed word VOID filling the upper field in cream "
            "on greige, one thin Latin line and a tiny number only. Young Asian woman small, lower third, "
            "cream knit sweater, quiet light. Nearly nothing else. Poster impact from scale contrast 16:1. "
            "Type is backdrop field, person sits in front of type field but face fully clear; "
            "or type is solid area separate from person. Never sticker type on face. "
            "FORBIDDEN: type in front of face as sticker, face gradient, UI, borders, extra words. "
            "Exactly one main word VOID."
        ),
    },
}

# 保持完全向后兼容的元组列表
LAYOUTS: list[tuple[str, str]] = [
    (stem, info["prompt"]) for stem, info in LAYOUT_VARIANTS.items()
]


def get_layout_variants_catalog() -> list[dict[str, Any]]:
    """返回所有 12 款构图版式的完整元数据列表。"""
    return [
        {
            "stem": stem,
            "index": info["index"],
            "name": info["name"],
            "category": info["category"],
            "word": info["word"],
            "prompt": info["prompt"],
        }
        for stem, info in LAYOUT_VARIANTS.items()
    ]


def find_layout_variant(key: str | int) -> dict[str, Any] | None:
    """根据编号、stem、关键字或主词查询版式配置。"""
    if key is None:
        return None

    raw = str(key).strip()
    if not raw:
        return None

    # 1. 尝试直接通过 stem 查找
    if raw in LAYOUT_VARIANTS:
        return LAYOUT_VARIANTS[raw]

    # 2. 数字编号 (如 "01", 1, "1")
    if raw.isdigit():
        idx = int(raw)
        for entry in LAYOUT_VARIANTS.values():
            if entry["index"] == idx:
                return entry

    # 3. 前缀编号匹配 (如 "01_")
    prefix = raw.lower()
    for stem, entry in LAYOUT_VARIANTS.items():
        if stem.lower().startswith(prefix) or prefix in stem.lower():
            return entry

    # 4. 主词匹配 (如 "FORM", "SILK")
    upper_raw = raw.upper()
    for entry in LAYOUT_VARIANTS.values():
        if entry["word"].upper() == upper_raw:
            return entry

    return None


def build_layout_prompt(key: str | int, word: str | None = None) -> str:
    """构建指定版式的渲染提示词，支持动态替换主词。"""
    variant = find_layout_variant(key)
    if not variant:
        raise KeyError(f"未知的版式编号或标识: {key}")

    base_prompt = variant["prompt"]
    default_word = variant["word"]

    if word and word.strip() and word.strip() != default_word:
        replacement = word.strip()
        # 替换 prompt 中的主词
        return base_prompt.replace(default_word, replacement)

    return base_prompt


def generate_layout_variant(
    stem_or_key: str | int,
    out_dir: Path | str = OUT,
    model: str = "agnes-image-2.5-flash",
    size: str = "864x1152",
    retries: int = 3,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Callable[..., dict[str, Any]] | None = None,
    save_image_fn: Callable[..., Any] | None = None,
    word: str | None = None,
) -> dict[str, Any]:
    """生成单张版式变体底图。"""
    variant = find_layout_variant(stem_or_key)
    if not variant:
        err = f"Unknown layout variant: {stem_or_key}"
        return {
            "stem": str(stem_or_key),
            "ok": False,
            "err": err,
            "error_class": classify_generation_error(err),
        }

    stem = variant["stem"]
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    fp = target_dir / f"{stem}.png"

    # 若文件已存在且未开启强制覆盖，且大于 20KB 则跳过
    if fp.exists() and fp.stat().st_size > 20_000 and not force:
        return {
            "stem": stem,
            "ok": True,
            "skipped": True,
            "path": str(fp),
            "size_kb": fp.stat().st_size // 1024,
        }

    prompt = build_layout_prompt(stem, word=word)

    # 演练模式直接返回成功模拟
    if dry_run:
        return {
            "stem": stem,
            "ok": True,
            "dry_run": True,
            "path": str(fp),
            "prompt_len": len(prompt),
        }

    gen = generate_fn or generate
    saver = save_image_fn or save_image

    if not callable(gen):
        err = "agnes_gateway.generate is not available or not callable"
        return {
            "stem": stem,
            "ok": False,
            "err": err,
            "error_class": classify_generation_error(err),
        }

    try:
        r = gen(prompt, size=size, model=model, retries=retries)
        if isinstance(r, dict) and r.get("ok"):
            if callable(saver):
                saver(r, fp)
            size_kb = (fp.stat().st_size // 1024) if fp.is_file() else 0
            return {
                "stem": stem,
                "ok": True,
                "path": str(fp),
                "size_kb": size_kb,
            }
        else:
            err_msg = r.get("error") if isinstance(r, dict) and r.get("error") else (str(r)[:200] if r is not None else "Empty response")
            return {
                "stem": stem,
                "ok": False,
                "err": err_msg or "Unknown generation error",
                "error_class": classify_generation_error(err_msg),
            }
    except Exception as exc:
        return {
            "stem": stem,
            "ok": False,
            "err": str(exc),
            "error_class": classify_generation_error(exc),
        }


def run_batch_layout_variants(
    out_dir: Path | str = OUT,
    stems: list[str | int] | None = None,
    model: str = "agnes-image-2.5-flash",
    size: str = "864x1152",
    retries: int = 3,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Callable[..., dict[str, Any]] | None = None,
    save_image_fn: Callable[..., Any] | None = None,
    write_report: bool = True,
    word: str | None = None,
    quiet: bool = False,
) -> list[dict[str, Any]]:
    """批量执行版式生成任务并持久化写入 batch_report.json。"""
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    # 选定需要执行的目标
    if stems:
        targets: list[str] = []
        for s in stems:
            matched = find_layout_variant(s)
            if matched:
                targets.append(matched["stem"])
            else:
                targets.append(str(s))
    else:
        targets = list(LAYOUT_VARIANTS.keys())

    report: list[dict[str, Any]] = []
    for stem in targets:
        res = generate_layout_variant(
            stem_or_key=stem,
            out_dir=target_dir,
            model=model,
            size=size,
            retries=retries,
            force=force,
            dry_run=dry_run,
            generate_fn=generate_fn,
            save_image_fn=save_image_fn,
            word=word,
        )
        report.append(res)

        if not quiet:
            if res.get("skipped"):
                print("SKIP", stem)
            elif res.get("ok"):
                sz = res.get("size_kb", 0)
                print("OK", stem, sz if sz else "(dry_run)" if dry_run else "")
            else:
                print("FAIL", stem, res.get("err", "")[:100])

    if write_report:
        report_path = target_dir / "batch_report.json"
        try:
            report_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as e:
            if not quiet:
                print(f"WARN: Failed to write {report_path}: {e}", file=sys.stderr)

    ok_count = sum(1 for x in report if x.get("ok"))
    if not quiet:
        print(f"DONE {ok_count} / {len(report)}")
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="Agnes Studio · 12 款经典构图版式编号册生成器 (L1 级版式变体)"
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="列出所有 12 种构图版式与主词",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出结果 (版式清单或批处理报告)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="静默模式，抑制进度与诊断输出",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格质检模式，若有任何一项失败或未生成成功则返回非零退出码",
    )
    parser.add_argument(
        "--stems",
        "--variants",
        dest="stems",
        default=None,
        help="逗号分隔的版式编号或 stem（如 01,03 或 01_swiss_asym）",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT_DIR),
        help=f"输出目录 (默认: {DEFAULT_OUT_DIR})",
    )
    parser.add_argument(
        "--model",
        default="agnes-image-2.5-flash",
        help="生图模型 (默认: agnes-image-2.5-flash)",
    )
    parser.add_argument(
        "--size",
        default="864x1152",
        help="生图分辨率 (默认: 864x1152)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="失败重试次数 (默认: 3)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新生成即使文件已存在",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="演练模式，不触发实际 API 请求",
    )
    parser.add_argument(
        "--word",
        default=None,
        help="覆盖主文字符串（针对单个版式）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """命令行主执行入口。"""
    parser = build_arg_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    try:
        if args.list:
            catalog = get_layout_variants_catalog()
            if args.json:
                print(json.dumps(catalog, ensure_ascii=False, indent=2))
            elif not args.quiet:
                print("Agnes Studio · 12 款经典构图版式清单:")
                for item in catalog:
                    print(f"  [{item['index']:02d}] {item['stem']:<20} | {item['word']:<8} | {item['name']}")
            return 0

        stems_list = None
        if args.stems:
            stems_list = [x.strip() for x in args.stems.split(",") if x.strip()]

        # 在 --json 模式下自动静默内部打印，避免污染标准输出
        quiet = args.quiet or args.json

        report = run_batch_layout_variants(
            out_dir=args.out,
            stems=stems_list,
            model=args.model,
            size=args.size,
            retries=args.retries,
            force=args.force,
            dry_run=args.dry_run,
            word=args.word,
            quiet=quiet,
        )

        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))

        if args.strict:
            if not report or any(not x.get("ok") for x in report):
                return 1
            return 0

        # 常规模式：只要存在成功或跳过即视为正常；如全部失败或为空则返回 1
        if not report or all(not x.get("ok") for x in report):
            return 1
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        elif not args.quiet:
            print(f"❌ 12 款经典构图版式批量生成失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
