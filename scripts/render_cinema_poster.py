#!/usr/bin/env python3
"""电影级极简海报：去掉一切教材腔，只留图 + 极少字 + 真负空间。"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "public" / "fonts"
NS_BLACK = F / "NotoSerifCJKsc-Black.otf"
PH_H = F / "Alibaba-PuHuiTi-Heavy.ttf"
PH_M = F / "Alibaba-PuHuiTi-Medium.ttf"
DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"
FUTURA = "/System/Library/Fonts/Supplemental/Futura.ttc"


def b64(p: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


def shot(html, out: Path):
    from playwright.sync_api import sync_playwright
    sys.path.insert(0, str(ROOT / "scripts"))
    from pro_poster_renderer import CHROME_PATH
    with sync_playwright() as p:
        kw = {"headless": True}
        if CHROME_PATH:
            kw["executable_path"] = CHROME_PATH
        b = p.chromium.launch(**kw)
        page = b.new_page(viewport={"width": 864, "height": 1152}, device_scale_factor=2)
        page.set_content(html)
        page.wait_for_timeout(500)
        page.screenshot(path=str(out), type="png")
        b.close()
    print(" ✓", out.name, out.stat().st_size // 1024, "KB")


def wrap(img, inner, extra_css=""):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      @font-face{{font-family:'NSB';src:url('file://{NS_BLACK}') format('opentype');}}
      @font-face{{font-family:'PHH';src:url('file://{PH_H}') format('truetype');}}
      @font-face{{font-family:'PHM';src:url('file://{PH_M}') format('truetype');}}
      *{{margin:0;padding:0;box-sizing:border-box}}
      body{{width:864px;height:1152px;overflow:hidden;background:#000}}
      .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
      .bg{{width:100%;height:100%;object-fit:cover;filter:contrast(1.05) saturate(.92)}}
      .cream{{color:#F3EFE6}}
      .lat{{font-family:Didot,Futura,serif;letter-spacing:.55em;text-transform:uppercase;font-size:12px}}
      .ph{{font-family:'PHH','PHM',sans-serif;font-weight:900}}
      .ns{{font-family:'NSB','Songti SC',serif}}
      {extra_css}
    </style></head><body><div class="s"><img class="bg" src="{img}">{inner}</div></body></html>"""


def film_bottom(image, out):
    """经典电影海报：巨标压底，西文其上，几乎无装饰。"""
    img = b64(image)
    inner = f"""
      <div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 42%,rgba(0,0,0,.25) 62%,rgba(0,0,0,.88) 100%)"></div>
      <div style="position:absolute;left:0;right:0;bottom:14%;text-align:center">
        <div class="lat cream" style="opacity:.75;margin-bottom:22px">Night Voyage</div>
        <div class="ph cream" style="font-size:132px;letter-spacing:.18em;line-height:1">夜航</div>
        <div class="lat cream" style="opacity:.55;margin-top:26px;letter-spacing:.35em;font-family:Futura,sans-serif;font-size:11px">A FILM STILL · AGNES</div>
      </div>"""
    shot(wrap(img, inner), out)


def film_top(image, out):
    """上标下图：字在天空/空场，主体完整。"""
    img = b64(image)
    inner = f"""
      <div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.72) 0%,rgba(0,0,0,.15) 28%,transparent 48%)"></div>
      <div style="position:absolute;left:0;right:0;top:9%;text-align:center">
        <div class="lat cream" style="opacity:.7;margin-bottom:28px">Night Voyage</div>
        <div class="ns cream" style="font-size:118px;letter-spacing:.28em;line-height:1">夜航</div>
      </div>
      <div style="position:absolute;left:0;right:0;bottom:7%;text-align:center">
        <div class="lat cream" style="opacity:.5;font-family:Futura,sans-serif;letter-spacing:.4em;font-size:11px">她把城市调成静音</div>
      </div>"""
    shot(wrap(img, inner), out)


def side_rail(image, out):
    """极简左轴：竖排大标 + 一条细线，其余全给图。"""
    img = b64(image)
    inner = f"""
      <div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.55) 0%,rgba(0,0,0,.1) 32%,transparent 55%)"></div>
      <div style="position:absolute;left:8%;top:12%;bottom:12%;display:flex;flex-direction:column;justify-content:space-between">
        <div>
          <div class="lat cream" style="opacity:.75;writing-mode:vertical-rl;letter-spacing:.45em;height:180px">Night Voyage</div>
        </div>
        <div>
          <div class="ns cream" style="writing-mode:vertical-rl;font-size:96px;letter-spacing:.22em;line-height:1">夜航</div>
          <div style="width:1px;height:48px;background:rgba(243,239,230,.45);margin:24px 0 0 8px"></div>
          <div class="ph cream" style="font-size:13px;letter-spacing:.32em;opacity:.7;margin-top:20px">她把城市调成静音</div>
        </div>
      </div>"""
    shot(wrap(img, inner), out)


def main():
    base = ROOT / "outputs" / "epic_compare" / "clean_base.png"
    out = ROOT / "outputs" / "cinema_study"
    out.mkdir(parents=True, exist_ok=True)
    film_bottom(base, out / "cine_01_bottom.png")
    film_top(base, out / "cine_02_top.png")
    side_rail(base, out / "cine_03_rail.png")
    print("done")


if __name__ == "__main__":
    main()
