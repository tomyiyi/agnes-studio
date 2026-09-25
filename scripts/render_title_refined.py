#!/usr/bin/env python3
"""高级中文海报标题字设 — 精工而非特效。

参照华语电影海报标题：端正、极简、字距/比例/材质说话。
"""
from __future__ import annotations
import base64, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "public" / "fonts"
NSB = (F / "NotoSerifCJKsc-Black.otf").resolve()
NSBOLD = (F / "NotoSerifCJKsc-Bold.otf").resolve()
PHM = (F / "Alibaba-PuHuiTi-Medium.ttf").resolve()
PHH = (F / "Alibaba-PuHuiTi-Heavy.ttf").resolve()
DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"
BASK = "/System/Library/Fonts/Supplemental/Baskerville.ttc"
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
        page.wait_for_timeout(550)
        page.screenshot(path=str(out), type="png")
        b.close()
    print("OK", Path(out).name)


BASE_CSS = f"""
@font-face{{font-family:'NSB';src:url('file://{NSB}') format('opentype');}}
@font-face{{font-family:'NSBO';src:url('file://{NSBOLD}') format('opentype');}}
@font-face{{font-family:'PHM';src:url('file://{PHM}') format('truetype');}}
@font-face{{font-family:'PHH';src:url('file://{PHH}') format('truetype');}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:864px;height:1152px;overflow:hidden;background:#0a0a0c}}
.s{{position:relative;width:864px;height:1152px;overflow:hidden}}
.bg{{width:100%;height:100%;object-fit:cover}}
.latin{{font-family:Didot,Baskerville,serif;letter-spacing:.48em;text-transform:uppercase}}
.sup{{font-family:'PHM','PingFang SC',sans-serif;letter-spacing:.36em}}
"""


def main():
    base = ROOT / "outputs" / "epic_compare" / "clean_base.png"
    out = ROOT / "outputs" / "title_refined"
    out.mkdir(parents=True, exist_ok=True)
    img = b64(base)

    # R1 · 东方电影海报：大宋体居中偏下，西文极细，朱印
    shot(f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE_CSS}
      .v{{position:absolute;inset:0;
        background:
          radial-gradient(ellipse at 50% 70%, rgba(0,0,0,.18), transparent 55%);
      }}
      .block{{position:absolute;left:0;right:0;top:58%;text-align:center;color:#F2EDE4}}
      .t1{{
        font-family:'NSB',serif;
        font-size:128px;letter-spacing:.22em;line-height:1;
        padding-left:.22em; /* optical centering for tracking */
        font-weight:900;
        text-shadow:0 2px 28px rgba(0,0,0,.25);
      }}
      .latin{{font-size:13px;opacity:.78;margin-top:28px;color:#F2EDE4}}
      .rule{{width:36px;height:1px;background:rgba(242,237,228,.55);margin:22px auto 16px}}
      .sup{{font-size:14px;opacity:.82;color:#F2EDE4}}
      .seal{{
        position:absolute;right:12%;top:58%;
        width:36px;height:36px;border:1.2px solid rgba(180,35,42,.9);
        color:rgba(180,35,42,.95);font-family:'NSB',serif;font-size:15px;
        display:flex;align-items:center;justify-content:center;
      }}
    </style></head><body><div class="s">
      <img class="bg" src="{img}">
      <div class="v"></div>
      <div class="block">
        <div class="t1">夜航</div>
        <div class="latin">Night Voyage</div>
        <div class="rule"></div>
        <div class="sup">她把城市调成静音</div>
      </div>
      <div class="seal">航</div>
    </div></body></html>""", out / "r1_oriental_center.png")

    # R2 · 黑宋大标偏左，极简西文小号，无装饰
    shot(f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE_CSS}
      .wrap{{position:absolute;left:9%;top:22%;color:#F2EDE4}}
      .t1{{
        font-family:'NSB',serif;
        font-size:156px;letter-spacing:.14em;line-height:.95;
        font-weight:900;
      }}
      .latin{{font-size:12px;opacity:.7;margin-top:32px}}
      .sup{{font-size:15px;opacity:.85;margin-top:18px}}
    </style></head><body><div class="s">
      <img class="bg" src="{img}">
      <div class="wrap">
        <div class="t1">夜航</div>
        <div class="latin">Night Voyage</div>
        <div class="sup">她把城市调成静音</div>
      </div>
    </div></body></html>""", out / "r2_left_big.png")

    # R3 · 竖排书脊标题 + 底部横向英文，像画册扉页
    shot(f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE_CSS}
      .vtitle{{
        position:absolute;right:11%;top:11%;
        writing-mode:vertical-rl;
        font-family:'NSB',serif;
        font-size:104px;letter-spacing:.28em;line-height:1;
        color:#F2EDE4;font-weight:900;
      }}
      .latin{{
        position:absolute;left:9%;bottom:8%;
        font-family:Didot,Baskerville,serif;
        font-size:14px;letter-spacing:.52em;text-transform:uppercase;
        color:rgba(242,237,228,.85);
      }}
      .sup{{
        position:absolute;left:9%;bottom:12%;
        font-family:'PHM',sans-serif;font-size:13px;letter-spacing:.32em;
        color:rgba(242,237,228,.7);
      }}
    </style></head><body><div class="s">
      <img class="bg" src="{img}">
      <div class="vtitle">夜航</div>
      <div class="sup">她把城市调成静音</div>
      <div class="latin">Night Voyage · Agnes</div>
    </div></body></html>""", out / "r3_vertical_spine.png")

    # R4 · 标题嵌入天空负空间（中上），比例黄金分割
    shot(f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE_CSS}
      .wrap{{position:absolute;left:12%;top:18%;width:58%;color:#F2EDE4}}
      .t1{{
        font-family:'NSBO','NSB',serif;
        font-size:112px;letter-spacing:.18em;line-height:1.05;
        font-weight:900;
      }}
      .latin{{font-size:12px;opacity:.72;margin-top:26px;letter-spacing:.55em}}
      .sup{{font-size:14px;opacity:.8;margin-top:14px}}
    </style></head><body><div class="s">
      <img class="bg" src="{img}">
      <div class="wrap">
        <div class="t1">夜 航</div>
        <div class="latin">Night Voyage</div>
        <div class="sup">她把城市调成静音</div>
      </div>
    </div></body></html>""", out / "r4_sky_field.png")

    # R5 · 电影海报式：底部居中主标 + 上方小 Latin，像院线海报
    shot(f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{BASE_CSS}
      .top{{position:absolute;left:0;right:0;top:7%;text-align:center;
        color:rgba(242,237,228,.8)}}
      .top .latin{{font-size:13px;letter-spacing:.58em}}
      .bot{{position:absolute;left:0;right:0;bottom:12%;text-align:center;color:#F2EDE4}}
      .t1{{
        font-family:'NSB',serif;
        font-size:120px;letter-spacing:.28em;line-height:1;
        padding-left:.28em;font-weight:900;
      }}
      .sup{{margin-top:18px;font-size:15px;opacity:.88;letter-spacing:.4em}}
    </style></head><body><div class="s">
      <img class="bg" src="{img}">
      <div class="top"><div class="latin">Night Voyage</div></div>
      <div class="bot">
        <div class="t1">夜航</div>
        <div class="sup">她把城市调成静音</div>
      </div>
    </div></body></html>""", out / "r5_film_bottom.png")

    print("done", out)


if __name__ == "__main__":
    main()
