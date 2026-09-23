#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H1 标题位置 / H3 导出格式 · 微信头图 2350×1000 最小对照实验。

单变量：
  H1 — 仅改主标锚点（上安全区 vs 底部 25% 遮挡带）
  H3 — 同版式，仅导出 PNG-24 vs JPEG q90，并附模拟二次压缩结果

构图铁律（2026-09-23 用户反馈后固化）：
  - 去掉无信息量的色块/描边框（含粉红竖条、青色尺寸徽标框）
  - 人物必须是主体，头部完整可见（2.35:1 裁切禁止居中砍头）
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments"
FONTS = ROOT / "public" / "fonts"
ASSETS = ROOT / "public" / "assets"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 2350, 1000
RATIO = 2.35

BG_SRC = ASSETS / "agnes_1789995698_9987.png"


def make_subject_crop(src: Path, dst: Path) -> Path:
    """1:1 人像 → 2.35:1，顶对齐裁切保住完整头部；人像为画面主体。"""
    im = Image.open(src).convert("RGB")
    w, h = im.size
    crop_h = int(round(w / RATIO))
    # 头部在上 1/3：从 y=0 起裁，保证发顶完整
    y0 = 0
    im.crop((0, y0, w, y0 + crop_h)).save(dst, "PNG")
    return dst


def cover_html(bg_uri: str, title_top: bool) -> str:
    # 左侧文案栏，不压人脸（人头偏画面中右）
    if title_top:
        title_style = "top:20%; left:6%;"
        sub_style = "top:54%; left:6%;"
    else:
        # 刻意落入底部 25% 遮挡带（H1 失败信号）；脚注上移避免与主标叠字
        title_style = "bottom:8%; left:6%;"
        sub_style = "bottom:28%; left:6%;"
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family:'SmileySans'; src:url('file://{FONTS}/SmileySans-Oblique.ttf') format('truetype'); }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  width:{W}px; height:{H}px; overflow:hidden; background:#0A0B10; color:#F9FAFB;
  position:relative; font-family:'SmileySans','PingFang SC',sans-serif;
  -webkit-font-smoothing:antialiased;
}}
.bg {{
  position:absolute; inset:0;
  background-image:url('{bg_uri}');
  background-size:cover; background-position:center top;
}}
/* 只压左侧文案区，右侧人物保持明亮，确保人脸是主体 */
.veil {{
  position:absolute; inset:0;
  background:linear-gradient(90deg,
    rgba(10,11,16,0.88) 0%,
    rgba(10,11,16,0.72) 34%,
    rgba(10,11,16,0.18) 52%,
    rgba(10,11,16,0) 68%);
}}
.kicker {{
  position:absolute; top:7%; left:6%; z-index:5;
  font-family:ui-monospace,Menlo,monospace;
  font-size:26px; letter-spacing:8px; color:rgba(249,250,251,0.7);
}}
.title {{
  position:absolute; {title_style} z-index:5;
  font-size:120px; line-height:1.05; letter-spacing:10px;
  text-shadow:0 8px 40px rgba(0,0,0,0.45);
}}
.title .dot {{ color:#E11D48; }}
.sub {{
  position:absolute; {sub_style} z-index:5;
  font-family:ui-monospace,Menlo,monospace; font-size:28px; letter-spacing:7px;
  color:rgba(249,250,251,0.82);
  text-shadow:0 4px 20px rgba(0,0,0,0.4);
}}
</style></head><body>
  <div class="bg"></div>
  <div class="veil"></div>
  <div class="kicker">AGNES STUDIO // 2.35:1</div>
  <div class="title">苏黎世秩序<span class="dot">.</span></div>
  <div class="sub">STRUCTURE &amp; ESSENCE</div>
</body></html>"""


def render(html: str, out_path: Path, fmt: str = "png") -> Path:
    with sync_playwright() as p:
        launch = {"headless": True}
        if CHROME and os.path.exists(CHROME):
            launch["executable_path"] = CHROME
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.set_content(html)
        page.wait_for_timeout(450)
        if fmt == "jpeg":
            page.screenshot(path=str(out_path), type="jpeg", quality=90)
        else:
            page.screenshot(path=str(out_path), type="png")
        browser.close()
    return out_path


def save_q90_copy(src: Path, dst: Path) -> Path:
    Image.open(src).convert("RGB").save(dst, "JPEG", quality=90, optimize=True)
    return dst


def simulate_wechat_reencode(src: Path, dst: Path) -> Path:
    im = Image.open(src).convert("RGB")
    small = im.resize((int(im.width * 0.92), int(im.height * 0.92)), Image.Resampling.LANCZOS)
    small.resize(im.size, Image.Resampling.BICUBIC).save(dst, "JPEG", quality=65, optimize=True)
    return dst


def head_visible_probe(path: Path) -> str:
    """粗检：画面上部 8–38% 中带是否有足够肤色/亮度结构（头应在框内）。"""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    band = im.crop((int(w * 0.35), int(h * 0.05), int(w * 0.72), int(h * 0.42)))
    px = list(band.resize((40, 24)).getdata())
    skin = 0
    for r, g, b in px:
        if r > 60 and g > 40 and b > 30 and r > g > b and (r - b) > 15 and r < 230:
            skin += 1
    ratio = skin / len(px)
    return f"head-band skin≈{ratio:.0%} ({'OK' if ratio > 0.08 else 'REVIEW'})"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    subject = OUT / "_bg_subject_235x100.png"
    make_subject_crop(BG_SRC, subject)
    bg_uri = f"data:image/png;base64,{__import__('base64').b64encode(subject.read_bytes()).decode()}"

    h1_top = OUT / "H1_title_top_safe.png"
    h1_bot = OUT / "H1_title_bottom_risk.png"
    h3_png = OUT / "H3_export_png24.png"
    h3_jpg = OUT / "H3_export_jpeg_q90.jpg"
    h3_png_x = OUT / "H3_png24_after_wechat_sim.jpg"
    h3_jpg_x = OUT / "H3_jpeg_q90_after_wechat_sim.jpg"

    print("▶ 裁切：顶对齐 2.35:1 人像主体…", head_visible_probe(subject))
    print("▶ H1 title position…")
    render(cover_html(bg_uri, True), h1_top)
    render(cover_html(bg_uri, False), h1_bot)
    print("  ", h1_top.name, head_visible_probe(h1_top))
    print("  ", h1_bot.name, head_visible_probe(h1_bot))

    print("▶ H3 export format…")
    render(cover_html(bg_uri, True), h3_png)
    save_q90_copy(h3_png, h3_jpg)
    print("▶ H3 simulated re-encode…")
    simulate_wechat_reencode(h3_png, h3_png_x)
    simulate_wechat_reencode(h3_jpg, h3_jpg_x)

    for p in (h1_top, h1_bot, h3_png, h3_jpg, h3_png_x, h3_jpg_x):
        im = Image.open(p)
        print(f"  ✓ {p.name:44} {im.format:4} {im.size[0]}×{im.size[1]} {p.stat().st_size//1024} KB")

    (OUT / "README.md").write_text(
        """# H1 / H3 微信头图对照实验（2350×1000）

## 构图约束（已按反馈修正）

- **人物是主体**：2.35:1 采用**顶对齐**裁切，完整保留头部与肩部；禁止居中裁切砍头。
- **去掉装饰框**：不使用粉红竖条、青色尺寸徽标框等无信息色块/描边。
- **文案不压脸**：文字靠左，veil 只压文案区，右侧人脸保持可辨。

## H1 · 标题位置（单变量：主标锚点）

| 文件 | 变量 | 预期 |
| --- | --- | --- |
| `H1_title_top_safe.png` | 主标落在安全区 | 列表标题条遮挡下主标仍完整 |
| `H1_title_bottom_risk.png` | 主标落入底部 25% 遮挡带 | 失败信号：主标被切断 |

**判读**：真机订阅号列表截图，看主标是否被切。
**数据**：不可读像素占比、可读性 1–5、遮挡线与基线重叠。

## H3 · 导出格式（版式与 H1-top 相同）

| 文件 | 变量 |
| --- | --- |
| `H3_export_png24.png` | PNG-24 |
| `H3_export_jpeg_q90.jpg` | JPEG q90 |
| `H3_png24_after_wechat_sim.jpg` | PNG → 模拟二次压缩 |
| `H3_jpeg_q90_after_wechat_sim.jpg` | JPEG q90 → 模拟二次压缩 |

**判读**：200% 看字缘/发丝毛刺。
**成功信号**：PNG 链路毛刺显著更少。

## 常量

2350×1000 · sRGB · Smiley Sans · `#0A0B10`/`#E11D48`/`#F9FAFB` · 仅动所标单变量
""",
        encoding="utf-8",
    )
    print("✓ README.md")


if __name__ == "__main__":
    main()
