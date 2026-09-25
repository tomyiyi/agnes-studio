#!/usr/bin/env python3
"""全量版式变体 — 不挡人物，少特效。统一用 clean_base，字只进负空间。"""
from __future__ import annotations
import base64, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "public" / "fonts"
NSB = (F / "NotoSerifCJKsc-Black.otf").resolve()
PHH = (F / "Alibaba-PuHuiTi-Heavy.ttf").resolve()
PHM = (F / "Alibaba-PuHuiTi-Medium.ttf").resolve()
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
        page.wait_for_timeout(450)
        page.screenshot(path=str(out), type="png")
        b.close()
    print("OK", Path(out).name)

def shell(img, inner, extra=""):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    @font-face{{font-family:'NSB';src:url('file://{NSB}') format('opentype');}}
    @font-face{{font-family:'PHH';src:url('file://{PHH}') format('truetype');}}
    @font-face{{font-family:'PHM';src:url('file://{PHM}') format('truetype');}}
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{width:864px;height:1152px;overflow:hidden;background:#000}}
    .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
    .bg{{width:100%;height:100%;object-fit:cover}}
    .lat{{font-family:Didot,Futura,serif;letter-spacing:.5em;text-transform:uppercase;font-size:12px}}
    .ph{{font-family:'PHH',sans-serif}}
    .ns{{font-family:'NSB',serif}}
    .sup{{font-family:'PHM',sans-serif;letter-spacing:.28em;font-size:15px}}
    {extra}
    </style></head><body><div class="s"><img class="bg" src="{img}">{inner}</div></body></html>"""

def main():
    base = ROOT / "outputs" / "epic_compare" / "clean_base.png"
    out = ROOT / "outputs" / "verify_batch"
    out.mkdir(parents=True, exist_ok=True)
    img = b64(base)
    # NOTE: clean_base has subject lower-right, sky/void upper-left

    # V1 顶部标题 — 字在天空，不碰人
    shot(shell(img, f"""
      <div style="position:absolute;left:8%;right:8%;top:8%;text-align:center;color:#F4F0E8">
        <div class="lat" style="opacity:.75;margin-bottom:20px">Night Voyage</div>
        <div class="ns" style="font-size:110px;letter-spacing:.24em;line-height:1">夜航</div>
      </div>
      <div style="position:absolute;left:0;right:0;bottom:5%;text-align:center">
        <div class="sup" style="color:rgba(244,240,232,.85)">她把城市调成静音</div>
      </div>
    """), out / "v1_top_title.png")

    # V2 左上角字 — 图右侧人物完整
    shot(shell(img, f"""
      <div style="position:absolute;left:7%;top:10%;width:38%;color:#F4F0E8">
        <div class="lat" style="opacity:.8;margin-bottom:18px">Night Voyage</div>
        <div class="ns" style="font-size:96px;letter-spacing:.12em;line-height:.95">夜航</div>
        <div class="sup" style="margin-top:18px;color:rgba(244,240,232,.8)">她把城市调成静音</div>
      </div>
    """), out / "v2_topleft.png")

    # V3 竖排右上 — 字在空场，人完整
    shot(shell(img, f"""
      <div style="position:absolute;right:8%;top:9%;writing-mode:vertical-rl;color:#F4F0E8">
        <div class="ns" style="font-size:88px;letter-spacing:.22em;line-height:1">夜航</div>
      </div>
      <div style="position:absolute;left:7%;top:10%;writing-mode:vertical-rl">
        <div class="lat" style="color:rgba(244,240,232,.75);letter-spacing:.45em">Night Voyage</div>
      </div>
    """), out / "v3_vertical_corner.png")

    # V4 极简角标 — 仅 micro + 小主标
    shot(shell(img, f"""
      <div style="position:absolute;left:7%;bottom:7%;color:#F4F0E8">
        <div class="ns" style="font-size:72px;letter-spacing:.18em">夜航</div>
        <div class="lat" style="margin-top:12px;opacity:.7">Night Voyage</div>
      </div>
    """), out / "v4_bottom_left_min.png")

    # V5 负空间大留白 — 字更小更少
    shot(shell(img, f"""
      <div style="position:absolute;left:10%;top:12%;color:#F4F0E8">
        <div class="lat" style="opacity:.7;margin-bottom:14px">2026</div>
        <div class="ns" style="font-size:84px;letter-spacing:.2em">夜航</div>
      </div>
    """), out / "v5_whisper.png")

    # V6 中轴顶部横排 + 下方短句（人物中下，不加暗角）
    shot(shell(img, f"""
      <div style="position:absolute;left:0;right:0;top:7%;text-align:center;color:#F4F0E8">
        <div class="ph" style="font-size:104px;letter-spacing:.22em;line-height:1;font-weight:900">夜航</div>
        <div class="lat" style="margin-top:16px;opacity:.7">Night Voyage</div>
      </div>
    """), out / "v6_center_top.png")

    # V7 对角：左上西文 + 左下小字，中间人全露
    shot(shell(img, f"""
      <div style="position:absolute;left:8%;top:8%;color:#F4F0E8">
        <div class="lat" style="opacity:.8">Night Voyage</div>
      </div>
      <div style="position:absolute;left:8%;bottom:8%;color:#F4F0E8">
        <div class="ns" style="font-size:64px;letter-spacing:.16em">夜航</div>
      </div>
    """), out / "v7_diag_minimal.png")

    # V8 仅竖排书名 + 印章，零渐变
    shot(shell(img, f"""
      <div style="position:absolute;right:7%;top:12%;writing-mode:vertical-rl">
        <div class="ns" style="font-size:92px;letter-spacing:.24em;color:#F4F0E8;line-height:1">夜航</div>
      </div>
      <div style="position:absolute;right:7%;bottom:10%;width:42px;height:42px;border:1.5px solid #B4232A;color:#B4232A;display:flex;align-items:center;justify-content:center;font-family:'NSB',serif;font-size:16px">航</div>
    """), out / "v8_vertical_seal.png")

    print("done", out)

if __name__ == "__main__":
    main()
