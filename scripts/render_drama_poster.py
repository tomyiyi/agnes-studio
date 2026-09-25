#!/usr/bin/env python3
"""反 slop 海报：一个巨型事件 + 三级字阶 + 最多一种表现手法。"""
from __future__ import annotations
import base64, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "public" / "fonts"
NSB = F / "NotoSerifCJKsc-Black.otf"
PHH = F / "Alibaba-PuHuiTi-Heavy.ttf"
PHM = F / "Alibaba-PuHuiTi-Medium.ttf"
DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"
FUTURA = "/System/Library/Fonts/Supplemental/Futura.ttc"

def b64(p):
    return "data:image/png;base64," + base64.b64encode(Path(p).read_bytes()).decode()

def shot(html, out):
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
    print(" ✓", Path(out).name)

def css():
    return f"""
    @font-face{{font-family:'NSB';src:url('file://{NSB}') format('opentype');}}
    @font-face{{font-family:'PHH';src:url('file://{PHH}') format('truetype');}}
    @font-face{{font-family:'PHM';src:url('file://{PHM}') format('truetype');}}
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{width:864px;height:1152px;overflow:hidden;background:#000}}
    .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
    .bg{{width:100%;height:100%;object-fit:cover;filter:contrast(1.08) saturate(.9)}}
    .micro{{font-family:Futura,'Helvetica Neue',sans-serif;font-size:11px;letter-spacing:.42em;text-transform:uppercase}}
    .sup{{font-family:'PHM',sans-serif;font-size:16px;letter-spacing:.28em}}
    """

def mega_bleed(image, out):
    """named move: mega-title-bleed — 巨字贴边裁切，仅 macro+micro。"""
    img = b64(image)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css()}
      .bg{{filter:contrast(1.12) saturate(.85) brightness(.92)}}
      .macro{{
        position:absolute;left:4%;right:-6%;bottom:18%;
        font-family:'PHH',sans-serif;font-size:176px;line-height:.82;
        letter-spacing:-.03em;color:#F2EEE6;font-weight:900;
        white-space:nowrap;
      }}
      .micro-t{{position:absolute;left:5%;top:8%;color:rgba(242,238,230,.85)}}
      .micro-b{{position:absolute;right:6%;bottom:8%;color:rgba(212,184,150,.95)}}
      .fade{{position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(0,0,0,.55) 100%)}}
    </style></head><body><div class="s">
      <img class="bg" src="{img}"><div class="fade"></div>
      <div class="micro micro-t">Night Voyage</div>
      <div class="macro">夜航</div>
      <div class="micro micro-b">Agnes · 2026</div>
    </div></body></html>"""
    shot(html, out)

def hard_field(image, out):
    """named move: hard-field-inversion — 底部硬色场反转，标题可读通道。"""
    img = b64(image)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css()}
      .field{{
        position:absolute;left:0;right:0;bottom:0;height:36%;
        background:#0A0A0C;
      }}
      .macro{{
        position:absolute;left:7%;bottom:16%;
        font-family:'NSB',serif;font-size:128px;letter-spacing:.22em;
        color:#F2EEE6;line-height:1;
      }}
      .sup{{position:absolute;left:7%;bottom:9%;color:rgba(212,184,150,.92)}}
      .micro-t{{position:absolute;left:7%;top:7%;color:rgba(242,238,230,.8)}}
    </style></head><body><div class="s">
      <img class="bg" src="{img}" style="height:68%">
      <div class="field"></div>
      <div class="micro micro-t">A Film Still</div>
      <div class="macro">夜航</div>
      <div class="sup">她把城市调成静音</div>
    </div></body></html>"""
    shot(html, out)

def chinese_corner(image, out):
    """named move: 边角式 + 计白当黑 — 字藏一角，中间全给图。"""
    img = b64(image)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css()}
      .veil{{position:absolute;inset:0;background:linear-gradient(215deg,rgba(0,0,0,.62) 0%,transparent 42%)}}
      .macro{{
        position:absolute;right:8%;top:10%;
        writing-mode:vertical-rl;
        font-family:'NSB',serif;font-size:108px;letter-spacing:.2em;
        color:#F2EEE6;line-height:1;
      }}
      .sup{{
        position:absolute;right:calc(8% + 130px);top:12%;
        writing-mode:vertical-rl;
        font-family:'PHM',sans-serif;font-size:13px;letter-spacing:.35em;
        color:rgba(242,238,230,.7);
      }}
      .micro-b{{position:absolute;left:7%;bottom:7%;color:rgba(212,184,150,.9)}}
      .seal{{
        position:absolute;right:8%;bottom:10%;
        width:40px;height:40px;border:1.5px solid #B4232A;color:#B4232A;
        display:flex;align-items:center;justify-content:center;
        font-family:'NSB',serif;font-size:16px;
      }}
    </style></head><body><div class="s">
      <img class="bg" src="{img}"><div class="veil"></div>
      <div class="macro">夜航</div>
      <div class="sup">Night Voyage</div>
      <div class="micro micro-b">Agnes Studio</div>
      <div class="seal">航</div>
    </div></body></html>"""
    shot(html, out)

def main():
    base = ROOT / "outputs" / "epic_compare" / "clean_base.png"
    out = ROOT / "outputs" / "drama_study"
    out.mkdir(parents=True, exist_ok=True)
    mega_bleed(base, out / "drama_01_mega_bleed.png")
    hard_field(base, out / "drama_02_hard_field.png")
    chinese_corner(base, out / "drama_03_corner.png")
    print("done")

if __name__ == "__main__":
    main()
