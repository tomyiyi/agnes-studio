#!/usr/bin/env python3
"""纪念碑式高级字排：思源宋/黑 Black + 阿里普惠 Heavy + 真西文。

字当建筑，不只当标签。
"""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "public" / "fonts"

PUHUI_H = FONTS / "Alibaba-PuHuiTi-Heavy.ttf"
PUHUI_B = FONTS / "Alibaba-PuHuiTi-Bold.ttf"
NOTO_SERIF_BLACK = FONTS / "NotoSerifCJKsc-Black.otf"
NOTO_SANS_BLACK = FONTS / "NotoSansCJKsc-Black.otf"
NOTO_SERIF_BOLD = FONTS / "NotoSerifCJKsc-Bold.otf"
SMILEY = FONTS / "SmileySans-Oblique.ttf"
LXGW = FONTS / "LXGWWenKai-Regular.ttf"
BODONI = "/System/Library/Fonts/Supplemental/Bodoni 72.ttc"
DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"
FUTURA = "/System/Library/Fonts/Supplemental/Futura.ttc"
BASK = "/System/Library/Fonts/Supplemental/Baskerville.ttc"


def b64(p: Path) -> str:
    data = p.read_bytes()
    mime = "png" if p.suffix.lower() == ".png" else "jpeg"
    return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"


def render_html(html: str, out: Path, size=(864, 1152)):
    from playwright.sync_api import sync_playwright
    sys.path.insert(0, str(ROOT / "scripts"))
    from pro_poster_renderer import CHROME_PATH
    w, h = size
    with sync_playwright() as p:
        kw = {"headless": True}
        if CHROME_PATH:
            kw["executable_path"] = CHROME_PATH
        browser = p.chromium.launch(**kw)
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
        page.set_content(html)
        page.wait_for_timeout(600)
        page.screenshot(path=str(out), type="png")
        browser.close()
    print(f"  ✓ {out.name} ({out.stat().st_size//1024} KB)")


# ---------- 三套「大气」构图 ----------

def style_monument(image: Path, out: Path, title="夜航", latin="NIGHT VOYAGE", sub="一部还没写完的电影"):
    """思源宋 Black · 电影纪念碑：巨字顶满宽度，西文细带，竖线分隔。"""
    img = b64(image)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      @font-face{{font-family:'NS';src:url('file://{NOTO_SERIF_BLACK}') format('opentype');}}
      @font-face{{font-family:'PB';src:url('file://{PUHUI_B}') format('truetype');}}
      *{{margin:0;padding:0;box-sizing:border-box}}
      body{{width:864px;height:1152px;overflow:hidden;background:#0B0B0E}}
      .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
      .bg{{width:100%;height:100%;object-fit:cover;filter:contrast(1.1) saturate(.88)}}
      .veil{{position:absolute;inset:0;background:
        linear-gradient(180deg,rgba(11,11,14,.55) 0%,rgba(11,11,14,.05) 38%,rgba(11,11,14,.15) 62%,rgba(11,11,14,.72) 100%)}}
      .latin{{
        position:absolute;left:8%;top:7%;
        font-family:Didot,Bodoni 72,Baskerville,serif;
        font-size:15px;letter-spacing:.55em;color:rgba(244,240,232,.85);
        text-transform:uppercase;font-weight:400;
      }}
      .title{{
        position:absolute;left:7%;right:7%;top:12%;
        font-family:'NS','Songti SC',serif;
        font-size:148px;line-height:.92;font-weight:900;
        letter-spacing:.06em;color:#F4F0E8;
        text-shadow:0 8px 40px rgba(0,0,0,.25);
      }}
      .bar{{position:absolute;left:8%;bottom:22%;width:1px;height:72px;background:rgba(244,240,232,.45)}}
      .sub{{
        position:absolute;left:calc(8% + 28px);bottom:23%;
        font-family:'PB','Noto Sans SC',sans-serif;
        font-size:20px;letter-spacing:.28em;color:rgba(244,240,232,.78);font-weight:500;
      }}
      .meta{{
        position:absolute;left:8%;bottom:8%;
        font-family:Futura,Helvetica Neue,sans-serif;
        font-size:11px;letter-spacing:.42em;color:rgba(244,240,232,.45);text-transform:uppercase;
      }}
      .year{{position:absolute;right:8%;bottom:8%;font-family:Didot,serif;font-size:28px;letter-spacing:.12em;color:rgba(212,184,150,.9)}}
    </style></head><body><div class="s">
      <img class="bg" src="{img}"><div class="veil"></div>
      <div class="latin">{latin}</div>
      <div class="title">{title}</div>
      <div class="bar"></div>
      <div class="sub">{sub}</div>
      <div class="meta">Agnes Studio · Monument</div>
      <div class="year">2026</div>
    </div></body></html>"""
    render_html(html, out)


def style_puhui_mega(image: Path, out: Path, title="夜航", latin="NIGHT VOYAGE"):
    """阿里普惠 Heavy · 巨字建筑：字占下半屏当图形。"""
    img = b64(image)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      @font-face{{font-family:'PH';src:url('file://{PUHUI_H}') format('truetype');}}
      *{{margin:0;padding:0;box-sizing:border-box}}
      body{{width:864px;height:1152px;overflow:hidden;background:#0A0A0C}}
      .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
      .bg{{width:100%;height:100%;object-fit:cover;filter:contrast(1.08) saturate(.9)}}
      .fade{{position:absolute;left:0;right:0;bottom:0;height:48%;
        background:linear-gradient(180deg,transparent,rgba(10,10,12,.92) 55%)}}
      .latin{{
        position:absolute;right:8%;top:8%;
        writing-mode:vertical-rl;
        font-family:Futura,Helvetica Neue,sans-serif;
        font-size:13px;letter-spacing:.48em;color:rgba(244,240,232,.7);
        text-transform:uppercase;
      }}
      .title{{
        position:absolute;left:5%;right:5%;bottom:14%;
        font-family:'PH','PingFang SC',sans-serif;
        font-size:168px;line-height:.86;font-weight:900;
        letter-spacing:-.02em;color:#F4F0E8;
      }}
      .en{{
        position:absolute;left:5.5%;bottom:8%;
        font-family:Futura,Avenir,sans-serif;
        font-size:14px;letter-spacing:.52em;color:rgba(212,184,150,.95);text-transform:uppercase;
      }}
    </style></head><body><div class="s">
      <img class="bg" src="{img}"><div class="fade"></div>
      <div class="latin">{latin}</div>
      <div class="title">{title}</div>
      <div class="en">{latin}</div>
    </div></body></html>"""
    render_html(html, out)


def style_vertical_epic(image: Path, out: Path, title="夜航", latin="NIGHT VOYAGE", slogan="她把城市调成静音"):
    """思源宋 · 中轴竖排东方史诗。"""
    img = b64(image)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      @font-face{{font-family:'NS';src:url('file://{NOTO_SERIF_BLACK}') format('opentype');}}
      @font-face{{font-family:'PH';src:url('file://{PUHUI_B}') format('truetype');}}
      *{{margin:0;padding:0;box-sizing:border-box}}
      body{{width:864px;height:1152px;overflow:hidden;background:#0A0A0C}}
      .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
      .bg{{width:100%;height:100%;object-fit:cover;filter:contrast(1.06) saturate(.85)}}
      .veil{{position:absolute;inset:0;background:
        radial-gradient(ellipse at 70% 40%, transparent 20%, rgba(10,10,12,.55) 100%),
        linear-gradient(90deg,rgba(10,10,12,.55),transparent 40%)}}
      .vtitle{{
        position:absolute;right:10%;top:10%;
        writing-mode:vertical-rl;
        font-family:'NS','Songti SC',serif;
        font-size:96px;letter-spacing:.22em;font-weight:900;color:#F4F0E8;line-height:1;
      }}
      .lat{{
        position:absolute;left:9%;top:12%;
        font-family:Didot,Bodoni,serif;font-size:14px;letter-spacing:.5em;
        color:rgba(244,240,232,.8);text-transform:uppercase;
      }}
      .sl{{
        position:absolute;left:9%;bottom:16%;
        font-family:'PH','PingFang SC',sans-serif;
        font-size:18px;letter-spacing:.32em;color:rgba(244,240,232,.82);font-weight:500;
      }}
      .line{{position:absolute;left:9%;bottom:13%;width:64px;height:1px;background:rgba(212,184,150,.7)}}
      .seal{{
        position:absolute;right:10%;bottom:12%;
        width:48px;height:48px;border:1.5px solid rgba(180,35,42,.88);color:rgba(180,35,42,.92);
        display:flex;align-items:center;justify-content:center;
        font-family:'NS','Songti SC',serif;font-size:20px;
      }}
    </style></head><body><div class="s">
      <img class="bg" src="{img}"><div class="veil"></div>
      <div class="lat">{latin}</div>
      <div class="vtitle">{title}</div>
      <div class="sl">{slogan}</div>
      <div class="line"></div>
      <div class="seal">航</div>
    </div></body></html>"""
    render_html(html, out)


def main():
    base = ROOT / "outputs" / "epic_compare" / "clean_base.png"
    out = ROOT / "outputs" / "epic_compare"
    if not base.exists():
        raise SystemExit("need clean_base.png")
    style_monument(base, out / "type_monument_song.png")
    style_puhui_mega(base, out / "type_puhui_mega.png")
    style_vertical_epic(base, out / "type_vertical_epic.png")
    print("done")


if __name__ == "__main__":
    main()
