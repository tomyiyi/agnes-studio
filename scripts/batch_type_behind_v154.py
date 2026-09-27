#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agnes Studio · 字在人后 (Type Behind Person) v154–v159 未测维度评测生成引擎.

包含 6 大高维拓展设计评测维度（共 36 组实验）：
- v154 户外街景 (Outdoor Street): 6 组，大地色/风衣/混凝土空街
- v155 夜景暗调 (Night Studio): 6 组，黑丝/丝绸/月光/深灰夜景
- v156 产品互嵌 (Product Hybrid): 6 组，包袋/香氛/高跟鞋/丝绸/玫瑰/珍珠
- v157 中文多字 (Chinese Multi-Char): 6 组，清欢/风骨/留白/暮色/一念/静观
- v158 建筑长词 (Long English Words): 6 组，ELEGANT/MODERN/SILHOUETTE/STUDIO/ARCH/LUXURY
- v159 A/B对照 (A/B Comparative): 6 组，强结构三层排版 vs 弱描述对照

用法示例:
    python3 scripts/batch_type_behind_v154.py --list-experiments
    python3 scripts/batch_type_behind_v154.py --dry-run --version v154
    python3 scripts/batch_type_behind_v154.py --dry-run --stems r154_out,r157_cn_qing
"""
from __future__ import annotations

import argparse
import json
import os
import re
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

DEFAULT_OUT_DIR = ROOT / "outputs" / "workflow_iter"
DEFAULT_MODEL = "agnes-image-2.5-flash"
DEFAULT_SIZE = "864x1152"
DEFAULT_RETRIES = 3

VERSION_METADATA: dict[str, dict[str, str]] = {
    "v154": {
        "title": "户外街景 (Outdoor Street)",
        "desc": "大地色系、风衣、混凝土空街与柔和日光，检验街景建筑穿插",
    },
    "v155": {
        "title": "夜景暗调 (Night Studio)",
        "desc": "黑丝、丝绸、月光窗台与深灰微光，检验暗调高反差排版",
    },
    "v156": {
        "title": "产品互嵌 (Product Hybrid)",
        "desc": "包袋、香氛、高跟鞋、丝绸、玫瑰与珍珠，检验商业静物融合",
    },
    "v157": {
        "title": "中文多字 (Chinese Multi-Char)",
        "desc": "清欢、风骨、留白、暮色、一念、静观，检验双字中文黑体/宋体穿插",
    },
    "v158": {
        "title": "建筑长词 (Long English Words)",
        "desc": "ELEGANT, MODERN, SILHOUETTE 等长词，检验多字母宽幅遮挡与留白",
    },
    "v159": {
        "title": "A/B对照 (A/B Comparative)",
        "desc": "强三层约束提示词 vs 弱描述提示词，检验图层控制对构图的决定性作用",
    },
}

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
    "SECONDARY: the word MODE near her head. "
    "Photorealistic fashion portrait."
)

EXPERIMENTS: list[tuple[str, str, str]] = [
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


def list_versions() -> list[str]:
    """返回所有评测版本列表（按顺序排列）。"""
    seen: list[str] = []
    for ver, _, _ in EXPERIMENTS:
        if ver not in seen:
            seen.append(ver)
    return seen


def list_experiments(version: str | None = None) -> list[tuple[str, str, str]]:
    """返回指定版本或全部实验配置列表。"""
    if not version:
        return list(EXPERIMENTS)

    v_clean = str(version).strip().lower()
    if not v_clean.startswith("v"):
        v_clean = f"v{v_clean}"

    return [exp for exp in EXPERIMENTS if exp[0].lower() == v_clean]


def get_experiment_by_stem(stem: str) -> tuple[str, str, str] | None:
    """根据实验 stem 唯一标识获取实验元数据。"""
    if not stem or not isinstance(stem, str):
        return None
    s_clean = stem.strip()
    for exp in EXPERIMENTS:
        if exp[1] == s_clean:
            return exp
    return None


def generate_single_experiment(
    ver: str,
    stem: str,
    prompt: str,
    out_dir: Path | str = DEFAULT_OUT_DIR,
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    retries: int = DEFAULT_RETRIES,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Callable[..., dict[str, Any]] | None = None,
    save_image_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """执行单组「字在人后」v154-v159 实验海报渲染。"""
    if not stem or not str(stem).strip():
        return {"version": ver, "stem": str(stem), "ok": False, "err": "Stem cannot be empty"}
    if not prompt or not str(prompt).strip():
        return {"version": ver, "stem": stem, "ok": False, "err": "Prompt cannot be empty"}

    ver_clean = ver.strip() if ver else "misc"
    stem_clean = stem.strip()

    target_dir = Path(out_dir) / ver_clean
    target_dir.mkdir(parents=True, exist_ok=True)
    fp = target_dir / f"{stem_clean}.png"

    # 若文件已存在且未开启强制覆盖，且大于 20KB 则跳过
    if fp.exists() and fp.stat().st_size > 20_000 and not force:
        return {
            "version": ver_clean,
            "stem": stem_clean,
            "ok": True,
            "skipped": True,
            "path": str(fp),
            "size_kb": fp.stat().st_size // 1024,
        }

    if dry_run:
        return {
            "version": ver_clean,
            "stem": stem_clean,
            "ok": True,
            "dry_run": True,
            "path": str(fp),
            "prompt_len": len(prompt),
        }

    gen = generate_fn or generate
    saver = save_image_fn or save_image

    if not callable(gen):
        return {
            "version": ver_clean,
            "stem": stem_clean,
            "ok": False,
            "err": "agnes_gateway.generate is not available or not callable",
        }

    try:
        r = gen(prompt, size=size, model=model, retries=retries)
        if isinstance(r, dict) and r.get("ok"):
            if callable(saver):
                saver(r, fp)
            size_kb = fp.stat().st_size // 1024 if fp.exists() else 0
            return {
                "version": ver_clean,
                "stem": stem_clean,
                "ok": True,
                "path": str(fp),
                "size_kb": size_kb,
                "cost_s": r.get("cost_s"),
                "via": r.get("via"),
            }
        err_msg = r.get("error") if isinstance(r, dict) else str(r)
        return {
            "version": ver_clean,
            "stem": stem_clean,
            "ok": False,
            "err": err_msg or "Unknown generation error",
        }
    except Exception as exc:
        return {
            "version": ver_clean,
            "stem": stem_clean,
            "ok": False,
            "err": str(exc),
        }


def run_batch_v154(
    experiments: list[tuple[str, str, str]] | None = None,
    versions: list[str] | str | None = None,
    stems: list[str] | str | None = None,
    limit: int | None = None,
    out_dir: Path | str = DEFAULT_OUT_DIR,
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    retries: int = DEFAULT_RETRIES,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Callable[..., dict[str, Any]] | None = None,
    save_image_fn: Callable[..., Any] | None = None,
) -> list[dict[str, Any]]:
    """批量执行「字在人后」v154-v159 评测并输出汇总报告。"""
    target_base = Path(out_dir)
    target_base.mkdir(parents=True, exist_ok=True)

    # 1. 过滤候选集
    if experiments is not None:
        pool = list(experiments)
    else:
        pool = list(EXPERIMENTS)

    if versions:
        if isinstance(versions, str):
            v_list = {v.strip().lower() for v in versions.split(",") if v.strip()}
        else:
            v_list = {str(v).strip().lower() for v in versions if str(v).strip()}
        # 兼容不带 v 前缀匹配
        norm_v_list = set()
        for v in v_list:
            norm_v_list.add(v)
            if not v.startswith("v"):
                norm_v_list.add(f"v{v}")
        pool = [exp for exp in pool if exp[0].lower() in norm_v_list]

    if stems:
        if isinstance(stems, str):
            s_list = {s.strip() for s in stems.split(",") if s.strip()}
        else:
            s_list = {str(s).strip() for s in stems if str(s).strip()}
        pool = [exp for exp in pool if exp[1] in s_list]

    if limit is not None and limit > 0:
        pool = pool[:limit]

    results: list[dict[str, Any]] = []
    print(f"Agnes Studio · 字在人后 v154-v159 批处理: 共 {len(pool)} 组实验")

    for idx, (ver, stem, prompt) in enumerate(pool, 1):
        res = generate_single_experiment(
            ver=ver,
            stem=stem,
            prompt=prompt,
            out_dir=target_base,
            model=model,
            size=size,
            retries=retries,
            force=force,
            dry_run=dry_run,
            generate_fn=generate_fn,
            save_image_fn=save_image_fn,
        )
        results.append(res)
        if res.get("ok"):
            status_tag = "SKIP" if res.get("skipped") else ("DRY" if res.get("dry_run") else "OK")
            print(f"[{idx}/{len(pool)}] {status_tag} {stem} -> {res.get('path', '')}")
        else:
            print(f"[{idx}/{len(pool)}] FAIL {stem} -> {res.get('err', '')[:80]}")

    summary = {
        "total": len(results),
        "ok": sum(1 for r in results if r.get("ok")),
        "failed": sum(1 for r in results if not r.get("ok")),
        "skipped": sum(1 for r in results if r.get("skipped")),
        "dry_run": dry_run,
        "results": results,
    }

    report_path = target_base / "batch_v154_report.json"
    try:
        report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    return results


def main(argv: list[str] | None = None) -> int:
    """CLI 入口函数。"""
    parser = argparse.ArgumentParser(
        description="Agnes Studio · 字在人后 (Type Behind Person) v154-v159 批处理评测工具"
    )
    parser.add_argument(
        "--list-experiments",
        action="store_true",
        help="查看所有内置实验版本与详细案例清单",
    )
    parser.add_argument(
        "-v", "--version",
        default=None,
        help="筛选执行的版本代号（如 v154、v157 或逗号分隔 v154,v158）",
    )
    parser.add_argument(
        "--stems",
        default=None,
        help="筛选执行的特定实验标识（逗号分隔，如 r154_out,r157_cn_qing）",
    )
    parser.add_argument(
        "-n", "--limit",
        type=int,
        default=None,
        help="限制最大执行数量",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT_DIR),
        help=f"实验海报输出基准目录 (默认: {DEFAULT_OUT_DIR})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"生图模型名称 (默认: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--size",
        default=DEFAULT_SIZE,
        help=f"生图分辨率 (默认: {DEFAULT_SIZE})",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"失败重试次数 (默认: {DEFAULT_RETRIES})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新生成已存在的文件",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="演练模式，仅组装提示词不请求实际生图 API",
    )

    args = parser.parse_args(argv)

    if args.list_experiments:
        print("Agnes Studio · 字在人后 v154-v159 实验矩阵清单:")
        versions = list_versions()
        for ver in versions:
            meta = VERSION_METADATA.get(ver, {})
            title = meta.get("title", ver)
            desc = meta.get("desc", "")
            items = list_experiments(ver)
            print(f"\n[{ver.upper()}] {title} (共 {len(items)} 组)")
            if desc:
                print(f"  设计目标: {desc}")
            for _, stem, _ in items:
                print(f"    - {stem}")
        return 0

    results = run_batch_v154(
        versions=args.version,
        stems=args.stems,
        limit=args.limit,
        out_dir=args.out,
        model=args.model,
        size=args.size,
        retries=args.retries,
        force=args.force,
        dry_run=args.dry_run,
    )

    if results and all(not r.get("ok") for r in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
