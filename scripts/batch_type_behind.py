#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agnes Studio · 字在人后 (Type Behind Person) 时尚海报批量生成引擎.

核心构图范式：
- 严格三层图层结构：BACKGROUND -> TYPE -> PERSON
- 人物层在最前，发丝与肩膀轮廓自然穿插并遮挡背景字体
- 巨幅浓缩英文或建筑感中文作为背景建筑体 (BACKDROP architecture)
- 严禁字贴脸、严禁水印 UI、严禁杂乱边框

用法示例:
    python3 scripts/batch_type_behind.py --words MODE,CHIC --out outputs/custom
    python3 scripts/batch_type_behind.py --list-presets
    python3 scripts/batch_type_behind.py --dry-run --words MODE,留白
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

DEFAULT_OUT_DIR = ROOT / "outputs" / "type_behind_batch"
DEFAULT_MODEL = "agnes-image-2.5-flash"
DEFAULT_SIZE = "864x1152"
DEFAULT_INK_COLOR = "#F3EDE3"
DEFAULT_PRIMARY = (
    "young Asian woman long black hair cream knit sweater, warm greige studio, soft fashion light."
)

# 经典预设词库
PRESET_WORDS: dict[str, list[str]] = {
    "fashion": ["MODE", "CHIC", "SILK", "VOGUE", "LUXE"],
    "zen": ["留白", "清欢", "风骨", "暮色", "静观"],
    "cinema": ["NOIR", "ECHO", "DUSK", "AURA", "VOID"],
}

EN_PROMPT_TEMPLATE = (
    "PRIMARY: {primary} "
    "SECONDARY: giant English condensed word {word} in cream {ink_color} as BACKDROP architecture. "
    "ABSOLUTE LAYER ORDER: BACKGROUND then TYPE then PERSON. "
    "Letters {word} pass BEHIND her head and body; hair/face/shoulder silhouette cuts through letterforms; "
    "part of each letter hidden behind her. "
    "FORBIDDEN: type in front of face/body, sticker on her, face gradient, UI, border. "
    "Exactly ONE word {word}. No other text."
)

CN_PROMPT_TEMPLATE = (
    "PRIMARY: {primary} "
    "SECONDARY: giant Chinese characters {word} in cream {ink_color} as BACKDROP architecture, "
    "modern heavy heiti or song style, architectural scale. "
    "ABSOLUTE LAYER ORDER: BACKGROUND then TYPE then PERSON. "
    "Characters {word} pass BEHIND her head and body; hair/face/shoulder silhouette cuts through the glyphs; "
    "part of each character hidden behind her. "
    "FORBIDDEN: type in front of face/body, sticker on her, face gradient, UI, border, garbled strokes. "
    "Exactly the characters {word}. No other text."
)


def get_preset_words(category: str | None = None) -> list[str]:
    """返回指定类别或全部预设词汇列表。"""
    if category and category in PRESET_WORDS:
        return list(PRESET_WORDS[category])
    all_words: list[str] = []
    for words in PRESET_WORDS.values():
        all_words.extend(words)
    return all_words


def detect_language(text: str) -> str:
    """根据文本字符判断语言模式：包含中文字符返回 'cn'，否则返回 'en'。"""
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            return "cn"
    return "en"


def build_type_behind_prompt(
    word: str,
    primary: str | None = None,
    ink_color: str = DEFAULT_INK_COLOR,
    lang: str | None = None,
) -> str:
    """构建「字在人后」专业生图提示词，支持中英文排版适配。"""
    if not word or not word.strip():
        raise ValueError("word cannot be empty")

    word_str = word.strip()
    primary_clean = (primary or DEFAULT_PRIMARY).strip()
    target_lang = lang if lang in ("cn", "en") else detect_language(word_str)

    if target_lang == "cn":
        return CN_PROMPT_TEMPLATE.format(
            primary=primary_clean,
            word=word_str,
            ink_color=ink_color,
        )
    return EN_PROMPT_TEMPLATE.format(
        primary=primary_clean,
        word=word_str,
        ink_color=ink_color,
    )


def prompt(word: str) -> str:
    """向后兼容的提示词构建函数。"""
    return build_type_behind_prompt(word)


def generate_type_behind(
    word: str,
    out_dir: Path | str = DEFAULT_OUT_DIR,
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    retries: int = 2,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Callable[..., dict[str, Any]] | None = None,
    save_image_fn: Callable[..., Any] | None = None,
    primary: str | None = None,
    lang: str | None = None,
    ink_color: str = DEFAULT_INK_COLOR,
) -> dict[str, Any]:
    """生成单张「字在人后」海报。"""
    if not word or not word.strip():
        return {
            "word": str(word),
            "ok": False,
            "err": "Word cannot be empty",
        }

    word_str = word.strip()
    clean_word = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", word_str).strip("_")
    if not clean_word:
        clean_word = "word"

    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    fp = target_dir / f"behind_{clean_word}.png"

    # 若文件已存在且未开启强制覆盖，且大于 20KB 则跳过
    if fp.exists() and fp.stat().st_size > 20_000 and not force:
        return {
            "word": word_str,
            "clean_word": clean_word,
            "ok": True,
            "skipped": True,
            "path": str(fp),
            "size_kb": fp.stat().st_size // 1024,
        }

    try:
        prompt_text = build_type_behind_prompt(
            word_str,
            primary=primary,
            ink_color=ink_color,
            lang=lang,
        )
    except Exception as exc:
        return {
            "word": word_str,
            "clean_word": clean_word,
            "ok": False,
            "err": str(exc),
        }

    # 演练模式直接返回成功模拟
    if dry_run:
        return {
            "word": word_str,
            "clean_word": clean_word,
            "ok": True,
            "dry_run": True,
            "path": str(fp),
            "prompt_len": len(prompt_text),
        }

    gen = generate_fn or generate
    saver = save_image_fn or save_image

    if not callable(gen):
        return {
            "word": word_str,
            "clean_word": clean_word,
            "ok": False,
            "err": "agnes_gateway.generate is not available or not callable",
        }

    try:
        r = gen(prompt_text, size=size, model=model, retries=retries)
        if isinstance(r, dict) and r.get("ok"):
            if callable(saver):
                saver(r, fp)
            size_kb = fp.stat().st_size // 1024 if fp.exists() else 0
            return {
                "word": word_str,
                "clean_word": clean_word,
                "ok": True,
                "path": str(fp),
                "size_kb": size_kb,
                "cost_s": r.get("cost_s"),
                "via": r.get("via"),
            }
        err_msg = r.get("error") if isinstance(r, dict) else str(r)
        return {
            "word": word_str,
            "clean_word": clean_word,
            "ok": False,
            "err": err_msg or "Unknown generation error",
        }
    except Exception as exc:
        return {
            "word": word_str,
            "clean_word": clean_word,
            "ok": False,
            "err": str(exc),
        }


def run_batch_type_behind(
    words: list[str] | str | None = None,
    out_dir: Path | str = DEFAULT_OUT_DIR,
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    retries: int = 2,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Callable[..., dict[str, Any]] | None = None,
    save_image_fn: Callable[..., Any] | None = None,
    primary: str | None = None,
    lang: str | None = None,
    ink_color: str = DEFAULT_INK_COLOR,
) -> list[dict[str, Any]]:
    """批量生成「字在人后」海报并输出批处理摘要报告。"""
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    if words is None:
        words_list = ["MODE"]
    elif isinstance(words, str):
        words_list = [w.strip() for w in words.split(",") if w.strip()]
    else:
        words_list = [str(w).strip() for w in words if str(w).strip()]

    results: list[dict[str, Any]] = []
    print(f"Agnes Studio · 字在人后批量渲染: 共 {len(words_list)} 个字设目标")

    for idx, w in enumerate(words_list, 1):
        res = generate_type_behind(
            w,
            out_dir=target_dir,
            model=model,
            size=size,
            retries=retries,
            force=force,
            dry_run=dry_run,
            generate_fn=generate_fn,
            save_image_fn=save_image_fn,
            primary=primary,
            lang=lang,
            ink_color=ink_color,
        )
        results.append(res)
        if res.get("ok"):
            status_tag = "SKIP" if res.get("skipped") else ("DRY" if res.get("dry_run") else "OK")
            print(f"[{idx}/{len(words_list)}] {status_tag} {w} -> {res.get('path', '')}")
        else:
            print(f"[{idx}/{len(words_list)}] FAIL {w} -> {res.get('err', '')[:80]}")

    summary = {
        "total": len(results),
        "ok": sum(1 for r in results if r.get("ok")),
        "failed": sum(1 for r in results if not r.get("ok")),
        "skipped": sum(1 for r in results if r.get("skipped")),
        "dry_run": dry_run,
        "results": results,
    }

    report_path = target_dir / "batch_report.json"
    try:
        report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    return results


def main(argv: list[str] | None = None) -> int:
    """CLI 入口函数。"""
    parser = argparse.ArgumentParser(
        description="Agnes Studio · 字在人后 (Type Behind Person) 时尚海报批量生成工具"
    )
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="查看内置预设词库清单",
    )
    parser.add_argument(
        "--words",
        default="MODE",
        help="逗号分隔的目标词（如 MODE,CHIC,留白）",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT_DIR),
        help=f"海报输出目录 (默认: {DEFAULT_OUT_DIR})",
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
        default=2,
        help="失败重试次数 (默认: 2)",
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
    parser.add_argument(
        "--primary",
        default=None,
        help="自定义主体提示词描述",
    )
    parser.add_argument(
        "--ink-color",
        default=DEFAULT_INK_COLOR,
        help=f"字设色彩 (默认: {DEFAULT_INK_COLOR})",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "cn"],
        default=None,
        help="显式指定提示词语言模式 (en/cn)",
    )

    args = parser.parse_args(argv)

    if args.list_presets:
        print("Agnes Studio · 字在人后经典预设词库:")
        for category, words in PRESET_WORDS.items():
            print(f"  [{category.upper()}]: {', '.join(words)}")
        return 0

    results = run_batch_type_behind(
        words=args.words,
        out_dir=args.out,
        model=args.model,
        size=args.size,
        retries=args.retries,
        force=args.force,
        dry_run=args.dry_run,
        primary=args.primary,
        lang=args.lang,
        ink_color=args.ink_color,
    )

    if results and all(not r.get("ok") for r in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
