#!/usr/bin/env python3
"""海报标题字设计（Title Lettering Design）——字本身被设计，不是摆字。"""
from __future__ import annotations
import base64, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "public" / "fonts"
NSB = (F / "NotoSerifCJKsc-Black.otf").resolve()
PHH = (F / "Alibaba-PuHuiTi-Heavy.ttf").resolve()
PHM = (F / "Alibaba-PuHuiTi-Medium.ttf").resolve()
SMILEY = (F / "SmileySans-Oblique.ttf").resolve()
DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"
IMPACT = "/System/Library/Fonts/Supplemental/Impact.ttf"
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
    print("OK", Path(out).name)

def shell(img, title_html, extra_css="", rest=""):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    @font-face{{font-family:'NSB';src:url('file://{NSB}') format('opentype');}}
    @font-face{{font-family:'PHH';src:url('file://{PHH}') format('truetype');}}
    @font-face{{font-family:'PHM';src:url('file://{PHM}') format('truetype');}}
    @font-face{{font-family:'SM';src:url('file://{SMILEY}') format('truetype');}}
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{width:864px;height:1152px;overflow:hidden;background:#000}}
    .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
    .bg{{width:100%;height:100%;object-fit:cover}}
    .lat{{font-family:Didot,Futura,serif;letter-spacing:.5em;text-transform:uppercase;font-size:12px}}
    {extra_css}
    </style></head><body><div class="s"><img class="bg" src="{img}">{title_html}{rest}</div></body></html>"""

def main():
    base = ROOT / "outputs" / "epic_compare" / "clean_base.png"
    out = ROOT / "outputs" / "title_design"
    out.mkdir(parents=True, exist_ok=True)
    img = b64(base)

    # ── T1 切割字：竖线切开宋体大字，字形被「设计」过 ──
    shot(shell(img, f"""
      <div class="wrap" style="position:absolute;left:8%;top:12%">
        <div class="lat" style="color:rgba(244,240,232,.75);margin-bottom:16px">Night Voyage</div>
        <div class="cut" style="position:relative;display:inline-block">
          <div class="ns" style="font-family:'NSB',serif;font-size:148px;letter-spacing:.08em;line-height:.9;color:#F4F0E8">夜航</div>
          <div class="slash" style="position:absolute;left:42%;top:-8%;width:6px;height:116%;background:#C8102E;transform:rotate(12deg);z-index:5"></div>
        </div>
        <div class="sub" style="margin-top:18px;font-family:'PHM',sans-serif;font-size:16px;letter-spacing:.35em;color:rgba(244,240,232,.8)">她把城市调成静音</div>
      </div>
    """, extra_css=".wrap{filter:drop-shadow(0 8px 24px rgba(0,0,0,.35))}"), out / "t1_cut_slash.png")

    # ── T2 双层错位字：描边字 + 实心字错位叠 ──
    shot(shell(img, f"""
      <div style="position:absolute;left:10%;top:14%">
        <div class="lat" style="color:#D4B896;margin-bottom:20px">Night Voyage · 2026</div>
        <div style="position:relative;height:170px">
          <div style="position:absolute;left:18px;top:18px;font-family:'PHH',sans-serif;font-size:128px;letter-spacing:.06em;color:transparent;-webkit-text-stroke:1.5px rgba(244,240,232,.55);line-height:1">夜航</div>
          <div style="position:absolute;left:0;top:0;font-family:'PHH',sans-serif;font-size:128px;letter-spacing:.06em;color:#F4F0E8;line-height:1">夜航</div>
        </div>
      </div>
    """), out / "t2_double_offset.png")

    # ── T3 反白块切割：色块切入字，字被裁切设计 ──
    shot(shell(img, f"""
      <div style="position:absolute;left:7%;top:18%">
        <div class="lat" style="color:rgba(244,240,232,.7);margin-bottom:14px">A Film Still</div>
        <div style="position:relative;display:inline-block;overflow:hidden;padding:8px 0">
          <div style="font-family:'NSB',serif;font-size:132px;letter-spacing:.16em;line-height:1;color:#F4F0E8;clip-path:polygon(0 0,100% 0,100% 58%,0 48%)">夜航</div>
          <div style="position:absolute;left:0;top:48%;font-family:'NSB',serif;font-size:132px;letter-spacing:.16em;line-height:1;color:#C8102E;clip-path:polygon(0 12%,100% 0,100% 100%,0 100%)">夜航</div>
        </div>
        <div style="margin-top:12px;font-family:'PHM',sans-serif;font-size:15px;letter-spacing:.32em;color:rgba(244,240,232,.85)">她把城市调成静音</div>
      </div>
    """), out / "t3_color_split.png")

    # ── T4 字内图窗：标题字用照片填充 ──
    shot(shell(img, f"""
      <div style="position:absolute;left:8%;top:16%;width:80%">
        <div class="lat" style="color:rgba(244,240,232,.8);margin-bottom:22px">Night Voyage</div>
        <div style="font-family:'PHH',sans-serif;font-size:150px;line-height:.92;letter-spacing:.04em;
          background-image:url('{img}');background-size:120% auto;background-position:30% 20%;
          -webkit-background-clip:text;background-clip:text;color:transparent;
          -webkit-text-stroke:1px rgba(244,240,232,.25);">夜航</div>
        <div style="margin-top:20px;width:48px;height:2px;background:#C8102E"></div>
        <div style="margin-top:14px;font-family:'PHM',sans-serif;font-size:15px;letter-spacing:.38em;color:rgba(244,240,232,.8)">她把城市调成静音</div>
      </div>
    """), out / "t4_image_in_type.png")

    # ── T5 几何锁字：字被几何框锁，像 logo ──
    shot(shell(img, f"""
      <div style="position:absolute;left:50%;top:16%;transform:translateX(-50%);text-align:center">
        <div class="lat" style="color:rgba(244,240,232,.75);margin-bottom:18px">Night Voyage</div>
        <div style="position:relative;display:inline-block;padding:28px 40px">
          <div style="position:absolute;left:0;top:0;width:28px;height:28px;border-left:2px solid #D4B896;border-top:2px solid #D4B896"></div>
          <div style="position:absolute;right:0;top:0;width:28px;height:28px;border-right:2px solid #D4B896;border-top:2px solid #D4B896"></div>
          <div style="position:absolute;left:0;bottom:0;width:28px;height:28px;border-left:2px solid #D4B896;border-bottom:2px solid #D4B896"></div>
          <div style="position:absolute;right:0;bottom:0;width:28px;height:28px;border-right:2px solid #D4B896;border-bottom:2px solid #D4B896"></div>
          <div style="font-family:'NSB',serif;font-size:118px;letter-spacing:.28em;line-height:1;color:#F4F0E8;padding-left:.28em">夜航</div>
        </div>
        <div style="margin-top:20px;font-family:'PHM',sans-serif;font-size:14px;letter-spacing:.42em;color:rgba(244,240,232,.8)">她把城市调成静音</div>
      </div>
    """), out / "t5_geo_lock.png")

    # ── T6 渐变描边大字 + 侧向挤压 ──
    shot(shell(img, f"""
      <div style="position:absolute;left:6%;top:20%">
        <div class="lat" style="color:#D4B896;margin-bottom:12px">2026 / NIGHT</div>
        <div style="font-family:'PHH',sans-serif;font-size:160px;line-height:.86;letter-spacing:-.02em;
          color:transparent;-webkit-text-stroke:2.5px #F4F0E8;
          text-shadow: 0 0 40px rgba(244,240,232,.15);
          transform:scaleX(0.92);transform-origin:left center;">夜航</div>
        <div style="margin-top:22px;display:flex;align-items:center;gap:16px">
          <div style="width:64px;height:1px;background:rgba(244,240,232,.5)"></div>
          <div style="font-family:'PHM',sans-serif;font-size:15px;letter-spacing:.34em;color:rgba(244,240,232,.85)">她把城市调成静音</div>
        </div>
      </div>
    """), out / "t6_outline_stretch.png")

    print("done", out)

if __name__ == "__main__":
    main()
