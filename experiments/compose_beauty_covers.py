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

import os
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments"
FONTS = ROOT / "public" / "fonts"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 2350, 1000
SRC = OUT / "_beauty_hero.png"


def render(html: str, out_path: Path, fmt: str = "png") -> Path:
    with sync_playwright() as p:
        launch = {"headless": True}
        if CHROME and os.path.exists(CHROME):
            launch["executable_path"] = CHROME
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.set_content(html)
        page.wait_for_timeout(500)
        if fmt == "jpeg":
            page.screenshot(path=str(out_path), type="jpeg", quality=92)
        else:
            page.screenshot(path=str(out_path), type="png")
        browser.close()
    return out_path


def cover_html(bg_uri: str, title_band: str = "safe") -> str:
    """title_band: safe=左上安全区 | risk=底部 25% 遮挡带（实验用）"""
    if title_band == "safe":
        block_css = "top: 11%; left: 7%;"
    else:
        block_css = "bottom: 6%; left: 7%;"

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<style>
  @font-face {{
    font-family: 'SmileySans';
    src: url('file://{FONTS}/SmileySans-Oblique.ttf') format('truetype');
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
    <div class="title-a">东方</div>
    <div class="title-b">神<em>颜</em></div>
    <div class="latin">ORIENTAL&nbsp;BEAUTY</div>
    <div class="slogan">她以骨相写诗，以眉眼成章</div>
  </div>
</body></html>"""


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f'missing {SRC}')
    bg_uri = "data:image/png;base64," + __import__("base64").b64encode(SRC.read_bytes()).decode()

    safe = OUT / "H1_title_top_safe.png"
    risk = OUT / "H1_title_bottom_risk.png"
    h3 = OUT / "H3_export_png24.png"

    print("▶ 渲染高定封面 SAFE / RISK / H3…")
    render(cover_html(bg_uri, "safe"), safe)
    render(cover_html(bg_uri, "risk"), risk)
    render(cover_html(bg_uri, "safe"), h3)
    Image.open(h3).convert("RGB").save(OUT / "H3_export_jpeg_q90.jpg", "JPEG", quality=92, optimize=True)

    for p in (safe, risk, h3):
        im = Image.open(p)
        print(f"  ✓ {p.name:28} {im.size} {p.stat().st_size//1024} KB")


if __name__ == "__main__":
    main()
