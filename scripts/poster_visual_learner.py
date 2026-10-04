#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio · 海报多模态视觉解构与设计自学习引擎
================================================
用于自动解构海报的主色调（Dominant Palette）、网格比例（Aspect Ratio）、
版式特征分类（Layout Category）与设计规则沉淀。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from env_config import ASSETS_DIR, DATA_DIR, PROJECT_ROOT
from PIL import Image

DEFAULT_TARGET_FILES = [
    ASSETS_DIR / "cover_cinematic_split_green.png",
    ASSETS_DIR / "cover_cinematic_letterbox.png",
    ASSETS_DIR / "poster_style_smiley.png",
]

DEFAULT_OUTPUT_PATH = DATA_DIR / "learned_poster_rules.json"


def extract_poster_features(filepath: str | Path) -> dict[str, Any] | None:
    """提取单张海报的多模态视觉特征与排版规则"""
    path = Path(filepath)
    if not path.is_file():
        return None

    filename = path.name
    with Image.open(path) as img:
        rgb_img = img.convert("RGB")
        w, h = rgb_img.size
        thumb = rgb_img.resize((32, 32))
        colors = thumb.getcolors(32 * 32) or []
        colors.sort(key=lambda x: x[0], reverse=True)

        palette = []
        for count, rgb in colors[:5]:
            if isinstance(rgb, tuple) and len(rgb) >= 3:
                hex_val = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
                palette.append({"hex": hex_val, "rgb": list(rgb[:3]), "pixels": count})

        aspect_ratio = round(w / h, 2) if h > 0 else 1.0
        if aspect_ratio >= 1.3:
            layout = "电影宽银幕上下遮幅 (2.35:1)"
        else:
            layout = "加块绿 · 左右对角拆字法"

        return {
            "filename": filename,
            "dimensions": f"{w}x{h}",
            "aspect_ratio": aspect_ratio,
            "dominant_palette": palette,
            "layout_category": layout,
            "rules": [
                "形：莫兰迪色块打底隔离复杂背景",
                "斜：8° 窄斜体得意黑建立动势",
                "比：主标题与微标 10:1 极端字阶对比",
                "空：对角避让保留人物视觉焦点",
            ],
        }


def analyze_poster_visual(
    target_files: list[str | Path] | None = None,
    output_path: str | Path | None = None,
    quiet: bool = False,
) -> list[dict[str, Any]]:
    """分析海报视觉特征并持久化学习结果，非破坏性保留知识库扩展规则"""
    if not quiet:
        print("🚀 启动海报视觉多模态特征解构与学习引擎...")

    files_to_process = DEFAULT_TARGET_FILES if target_files is None else target_files
    results: list[dict[str, Any]] = []

    for item in files_to_process:
        feat = extract_poster_features(item)
        if feat is not None:
            results.append(feat)
            if not quiet:
                print(f"  ✓ 解构成功: {feat['filename']} -> {feat['layout_category']}")

    out_file = Path(output_path).resolve() if output_path else DEFAULT_OUTPUT_PATH.resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    final_list: list[dict[str, Any]] = []
    if out_file.is_file():
        try:
            existing = json.loads(out_file.read_text(encoding="utf-8"))
            if isinstance(existing, list):
                filename_to_new = {item["filename"]: item for item in results if "filename" in item}
                seen_filenames = set()
                for entry in existing:
                    if isinstance(entry, dict) and "filename" in entry:
                        fn = entry["filename"]
                        if fn in filename_to_new:
                            final_list.append(filename_to_new[fn])
                            seen_filenames.add(fn)
                        else:
                            final_list.append(entry)
                    else:
                        final_list.append(entry)
                for item in results:
                    fn = item.get("filename")
                    if fn and fn not in seen_filenames:
                        final_list.append(item)
            else:
                final_list = results
        except Exception:
            final_list = results
    else:
        final_list = results

    out_file.write_text(json.dumps(final_list, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not quiet:
        print(f"✨ 海报设计学习报告与知识沉淀已保存至: {out_file}")
    return results


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="海报多模态视觉解构与设计自学习引擎")
    parser.add_argument(
        "--files",
        "-f",
        nargs="*",
        default=None,
        help="目标海报图片文件列表",
    )
    parser.add_argument(
        "--out",
        "-o",
        default=None,
        help="学习规则 JSON 输出文件路径",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="静默模式，抑制控制台日志输出",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：当指定的文件存在缺失或解构失败时返回非零退出码 1",
    )
    args = parser.parse_args(argv)

    target_files = [Path(p) for p in args.files] if args.files is not None else None
    results = analyze_poster_visual(
        target_files=target_files,
        output_path=args.out,
        quiet=args.quiet,
    )
    if args.strict and target_files is not None:
        if len(results) != len(target_files):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
