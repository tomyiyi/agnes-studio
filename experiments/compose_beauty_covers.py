#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高定美妆封面 · 对角拆字 + 负空间排版（学习资料落地）

遵循 TYPOGRAPHY_AND_POSTER_DESIGN.md 与 learned_poster_rules.json：
- 负空间：左侧设计光域，不压人脸
- 对角拆字：主标错位两行 + 发丝线
- 10:1 字阶：Display vs Micro
- 盘古之白：中英 0.25em 间隙
- 不居中、无装饰色块框
"""

from __future__ import annotations

import argparse
import base64
import html as html_escape
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import env_config
from env_config import ASSETS_DIR, FONTS_DIR, PROJECT_ROOT, resolve_chrome_path
from PIL import Image
from playwright.sync_api import sync_playwright

OUT = ROOT / "experiments"
FONTS = FONTS_DIR
ASSETS = ASSETS_DIR
CHROME = resolve_chrome_path()
W, H = 2350, 1000
SRC = OUT / "_beauty_hero.png"

FALLBACK_SRCS = [
    SRC,
    ASSETS / "macro_beauty_02.png",
    ASSETS / "subjects" / "muse_real.png",
    ASSETS / "agnes_1789995698_9987.png",
]


def resolve_source_image(src: Path | str | None = None) -> Path:
    """解析可用的背景底图路径，支持显式传入、默认实验图与素材库 fallback。"""
    if src:
        p = Path(src)
        if not p.is_file():
            raise FileNotFoundError(f"Source image not found: {src}")
        return p

    for candidate in FALLBACK_SRCS:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        f"No valid beauty background image found (checked: {[str(c) for c in FALLBACK_SRCS]})"
    )


def image_to_base64_uri(path: Path | str) -> str:
    """将图片文件编码为 data URI。"""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    ext = p.suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
    encoded = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def cover_html(
    bg_uri: str,
    title_band: str = "safe",
    title_a: str = "东方",
    title_b: str = "神颜",
    title_accent: str = "颜",
    latin: str = "ORIENTAL BEAUTY",
    slogan: str = "她以骨相写诗，以眉眼成章",
    font_file: str | None = None,
) -> str:
    """title_band: safe=左上安全区 | risk=底部 25% 遮挡带（实验用）"""
    if title_band == "safe":
        block_css = "top: 11%; left: 7%;"
    else:
        block_css = "bottom: 6%; left: 7%;"

    safe_title_a = html_escape.escape(title_a or "")
    raw_title_b = title_b or ""
    if title_accent and title_accent in raw_title_b:
        parts = raw_title_b.split(title_accent, 1)
        safe_title_b = (
            f"{html_escape.escape(parts[0])}<em>{html_escape.escape(title_accent)}</em>{html_escape.escape(parts[1])}"
        )
    else:
        safe_title_b = html_escape.escape(raw_title_b)

    safe_latin = html_escape.escape(latin or "").replace(" ", "&nbsp;")
    safe_slogan = html_escape.escape(slogan or "")
    font_name = font_file or "SmileySans-Oblique.ttf"
    font_url = f"file://{FONTS}/{font_name}"

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<style>
  @font-face {{
    font-family: 'SmileySans';
    src: url('{font_url}') format('truetype');
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: {W}px; height: {H}px; overflow: hidden;
    background: #0c0b0a;
    font-family: 'SmileySans', 'PingFang SC', sans-serif;
    color: #f6f1e8;
    -webkit-font-smoothing: antialiased;
    text-rendering: geometricPrecision;
  }}
  .photo {{
    position: absolute; inset: 0;
    background: url('{bg_uri}') center 20% / cover no-repeat;
    filter: saturate(0.92) contrast(1.05);
  }}
  /* 左侧光域负空间：环境色渐隐，不是色块框 */
  .scrim {{
    position: absolute; inset: 0;
    background:
      linear-gradient(96deg,
        rgba(12, 11, 10, 0.78) 0%,
        rgba(12, 11, 10, 0.55) 28%,
        rgba(12, 11, 10, 0.18) 48%,
        rgba(12, 11, 10, 0.02) 62%,
        transparent 72%),
      linear-gradient(180deg, rgba(12,11,10,0.18) 0%, transparent 22%, transparent 78%, rgba(12,11,10,0.35) 100%);
  }}
  .vignette {{
    position: absolute; inset: 0;
    box-shadow: inset 0 0 160px rgba(20, 12, 8, 0.45);
    pointer-events: none;
  }}

  .block {{
    position: absolute; {block_css} z-index: 5;
    width: 920px;
  }}
  .rule {{
    width: 72px; height: 1px;
    background: linear-gradient(90deg, #c9a063, rgba(201,160,99,0));
    margin: 18px 0 22px;
  }}
  /* 对角拆字：两行错位，建立动势 */
  .title-a {{
    font-size: 148px;
    line-height: 0.92;
    letter-spacing: 0.08em;
    font-weight: 400;
    text-shadow: 0 12px 48px rgba(20, 12, 8, 0.55);
  }}
  .title-b {{
    font-size: 148px;
    line-height: 0.92;
    letter-spacing: 0.08em;
    margin-left: 132px;
    margin-top: 8px;
    font-weight: 400;
    text-shadow: 0 12px 48px rgba(20, 12, 8, 0.55);
  }}
  .title-b em {{
    font-style: normal;
    color: #c9a063;
  }}
  /* 盘古之白：中英之间物理间隙 */
  .latin {{
    margin-top: 26px;
    font-family: ui-monospace, 'SF Mono', Menlo, monospace;
    font-size: 15px;
    letter-spacing: 0.38em;
    color: rgba(246, 241, 232, 0.78);
  }}
  .slogan {{
    margin-top: 18px;
    font-family: 'Songti SC', 'Source Han Serif SC', serif;
    font-size: 22px;
    letter-spacing: 0.18em;
    color: rgba(246, 241, 232, 0.88);
  }}
  /* 交付成图禁止角落小字/规格水印/页码 —— 2026-09-23 反馈 */
</style></head>
<body>
  <div class="photo"></div>
  <div class="scrim"></div>
  <div class="vignette"></div>

  <div class="block">
    <div class="rule"></div>
    <div class="title-a">{safe_title_a}</div>
    <div class="title-b">{safe_title_b}</div>
    <div class="latin">{safe_latin}</div>
    <div class="slogan">{safe_slogan}</div>
  </div>
</body></html>"""


def render(
    html: str,
    out_path: Path | str,
    fmt: str = "png",
    chrome: str | None = None,
    dry_run: bool = False,
) -> Path:
    """将 HTML 渲染为指定格式图片（支持 dry_run 模拟与自动建目录）。"""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        im_format = "JPEG" if fmt.lower() in ("jpeg", "jpg") else "PNG"
        im = Image.new("RGB", (W, H), color=(20, 20, 20))
        im.save(out_path, format=im_format)
        return out_path

    chrome_exec = chrome or CHROME or resolve_chrome_path()
    with sync_playwright() as p:
        launch = {"headless": True}
        if chrome_exec and os.path.exists(chrome_exec):
            launch["executable_path"] = chrome_exec
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.set_content(html)
        page.wait_for_timeout(500)
        if fmt.lower() in ("jpeg", "jpg"):
            page.screenshot(path=str(out_path), type="jpeg", quality=92)
        else:
            page.screenshot(path=str(out_path), type="png")
        browser.close()
    return out_path


def run_beauty_experiment(
    src: Path | str | None = None,
    out_dir: Path | str | None = None,
    title_band: str = "all",
    dry_run: bool = False,
    quiet: bool = False,
) -> dict:
    """执行美妆封面 SAFE / RISK / H3 全套排版渲染实验。"""
    source_path = resolve_source_image(src)
    dest_dir = Path(out_dir) if out_dir else OUT
    dest_dir.mkdir(parents=True, exist_ok=True)

    bg_uri = image_to_base64_uri(source_path)

    safe_png = dest_dir / "H1_title_top_safe.png"
    risk_png = dest_dir / "H1_title_bottom_risk.png"
    h3_png = dest_dir / "H3_export_png24.png"
    h3_jpg = dest_dir / "H3_export_jpeg_q90.jpg"

    rendered_files: list[Path] = []

    if not quiet:
        print(f"▶ 渲染高定美妆封面 (src: {source_path.name}, dry_run={dry_run})…")

    if title_band in ("safe", "all"):
        render(cover_html(bg_uri, "safe"), safe_png, fmt="png", dry_run=dry_run)
        rendered_files.append(safe_png)

    if title_band in ("risk", "all"):
        render(cover_html(bg_uri, "risk"), risk_png, fmt="png", dry_run=dry_run)
        rendered_files.append(risk_png)

    if title_band == "all":
        render(cover_html(bg_uri, "safe"), h3_png, fmt="png", dry_run=dry_run)
        rendered_files.append(h3_png)

        if dry_run:
            render(cover_html(bg_uri, "safe"), h3_jpg, fmt="jpeg", dry_run=True)
        else:
            with Image.open(h3_png) as im:
                im.convert("RGB").save(h3_jpg, "JPEG", quality=92, optimize=True)
        rendered_files.append(h3_jpg)

    if not quiet:
        for p in rendered_files:
            size_kb = p.stat().st_size // 1024 if p.exists() else 0
            print(f"  ✓ {p.name:28} {size_kb} KB")

    return {
        "ok": True,
        "src": str(source_path),
        "out_dir": str(dest_dir),
        "dry_run": dry_run,
        "rendered_files": [str(p) for p in rendered_files],
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="高定美妆封面 · 对角拆字 + 负空间排版实验生成器")
    parser.add_argument("--src", type=str, default=None, help="底图路径 (默认自动 fallback 至素材库)")
    parser.add_argument("--out-dir", type=str, default=None, help="输出目录 (默认: experiments)")
    parser.add_argument(
        "--title-band",
        choices=["safe", "risk", "all"],
        default="all",
        help="排版变量模式 (safe/risk/all, 默认 all)",
    )
    parser.add_argument("--dry-run", action="store_true", help="演练模式 (不启动真实 Chromium)")
    parser.add_argument("--json", type=str, default=None, help="将运行报告写入指定的 JSON 文件")
    parser.add_argument("--quiet", action="store_true", help="静默模式")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        report = run_beauty_experiment(
            src=args.src,
            out_dir=args.out_dir,
            title_band=args.title_band,
            dry_run=args.dry_run,
            quiet=args.quiet,
        )
        if args.json:
            p = Path(args.json)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0
    except Exception as exc:
        print(f"❌ 运行失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
