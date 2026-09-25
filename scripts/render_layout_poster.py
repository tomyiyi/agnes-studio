#!/usr/bin/env python3
"""海报「设计排版」范式库：同字体，改结构。

排版问题 = 网格 / 重心 / 层级关系 / 主题落位，不是换字。
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "public" / "fonts"
NS_BLACK = FONTS / "NotoSerifCJKsc-Black.otf"
NS_BOLD = FONTS / "NotoSerifCJKsc-Bold.otf"
PH_H = FONTS / "Alibaba-PuHuiTi-Heavy.ttf"
PH_B = FONTS / "Alibaba-PuHuiTi-Bold.ttf"
PH_M = FONTS / "Alibaba-PuHuiTi-Medium.ttf"
BODONI = "/System/Library/Fonts/Supplemental/Bodoni 72.ttc"
DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"
FUTURA = "/System/Library/Fonts/Supplemental/Futura.ttc"
BASK = "/System/Library/Fonts/Supplemental/Baskerville.ttc"


def b64(p: Path) -> str:
    mime = "png" if p.suffix.lower() == ".png" else "jpeg"
    return f"data:image/{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def render(html: str, out: Path, size=(864, 1152)):
    from playwright.sync_api import sync_playwright
    sys.path.insert(0, str(ROOT / "scripts"))
    from pro_poster_renderer import CHROME_PATH
    w, h = size
    with sync_playwright() as p:
        kw = {"headless": True}
        if CHROME_PATH:
            kw["executable_path"] = CHROME_PATH
        b = p.chromium.launch(**kw)
        page = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
        page.set_content(html)
        page.wait_for_timeout(550)
        page.screenshot(path=str(out), type="png")
        b.close()
    print(" ✓", out.name, out.stat().st_size // 1024, "KB")


def base_css(img):
    return f"""
      @font-face{{font-family:'NSB';src:url('file://{NS_BLACK}') format('opentype');}}
      @font-face{{font-family:'NS';src:url('file://{NS_BOLD}') format('opentype');}}
      @font-face{{font-family:'PHH';src:url('file://{PH_H}') format('truetype');}}
      @font-face{{font-family:'PHB';src:url('file://{PH_B}') format('truetype');}}
      @font-face{{font-family:'PHM';src:url('file://{PH_M}') format('truetype');}}
      *{{margin:0;padding:0;box-sizing:border-box}}
      body{{width:864px;height:1152px;overflow:hidden;background:#0A0A0C}}
      .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
      .bg{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:contrast(1.06) saturate(.88)}}
      .lat{{font-family:Didot,Bodoni,Baskerville,serif;letter-spacing:.5em;text-transform:uppercase;font-size:13px}}
      .ui{{font-family:Futura,'Helvetica Neue',sans-serif;letter-spacing:.35em;text-transform:uppercase;font-size:11px}}
      .cn{{font-family:'NSB','NS','Songti SC',serif}}
      .ph{{font-family:'PHH','PHB','PingFang SC',sans-serif}}
      .body{{font-family:'PHM','PingFang SC',sans-serif;letter-spacing:.18em;font-size:17px;line-height:1.8}}
    """


def layout_swiss_asym(image, out, title="夜航", latin="Night Voyage", slogan="她把城市调成静音"):
    """瑞士非对称：左栏字塔 + 右侧大图重心；12 列意识。"""
    img = b64(image)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css(img)}
      .colL{{position:absolute;left:7%;top:10%;bottom:10%;width:38%;display:flex;flex-direction:column;justify-content:space-between}}
      .colR{{position:absolute;left:48%;right:6%;top:14%;bottom:14%}}
      .imgWin{{width:100%;height:100%;object-fit:cover;filter:contrast(1.08) saturate(.9)}}
      .top-lat{{color:rgba(244,240,232,.75)}}
      .t1{{font-family:'PHH','PHB',sans-serif;font-size:92px;line-height:.9;letter-spacing:.02em;color:#F4F0E8;font-weight:900}}
      .t2{{margin-top:18px;font-family:'PHM',sans-serif;font-size:15px;letter-spacing:.42em;color:rgba(212,184,150,.95);text-transform:uppercase;font-family:Futura,sans-serif}}
      .rule{{width:48px;height:1px;background:rgba(244,240,232,.5);margin:22px 0}}
      .sl{{color:rgba(244,240,232,.82)}}
      .foot{{display:flex;justify-content:space-between;align-items:end}}
      .num{{font-family:Didot,serif;font-size:22px;letter-spacing:.2em;color:rgba(212,184,150,.85)}}
    </style></head><body><div class="s">
      <img class="bg" src="{img}" style="filter:contrast(1.04) saturate(.8) brightness(.92)">
      <div class="colL">
        <div>
          <div class="lat top-lat">{latin}</div>
          <div class="rule"></div>
          <div class="t1">{title}</div>
          <div class="t2">Poster System</div>
        </div>
        <div>
          <div class="body sl">{slogan}</div>
          <div class="foot" style="margin-top:28px">
            <div class="ui" style="color:rgba(244,240,232,.45)">Swiss · Asym</div>
            <div class="num">01</div>
          </div>
        </div>
      </div>
      <div class="colR"><img class="imgWin" src="{img}"></div>
    </div></body></html>"""
    render(html, out)


def layout_type_band(image, out, title="夜航", latin="Night Voyage", slogan="一部还没写完的电影"):
    """上字带 / 下图场：信息与视觉分区，电影预告结构。"""
    img = b64(image)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css(img)}
      .band{{position:absolute;left:0;right:0;top:0;height:38%;
        background:linear-gradient(180deg,#0E0E12 0%,#0E0E12 78%,transparent 100%);
        padding:8% 8% 0;display:flex;flex-direction:column;justify-content:flex-end}}
      .field{{position:absolute;left:0;right:0;top:34%;bottom:0;overflow:hidden}}
      .field img{{width:100%;height:100%;object-fit:cover;object-position:center 30%;filter:contrast(1.08) saturate(.9)}}
      .kick{{color:rgba(212,184,150,.9);margin-bottom:18px}}
      .t1{{font-family:'NSB',serif;font-size:112px;letter-spacing:.12em;color:#F4F0E8;line-height:1}}
      .row{{display:flex;justify-content:space-between;align-items:end;margin-top:22px;padding-bottom:6%}}
      .sl{{color:rgba(244,240,232,.7);max-width:50%}}
      .side{{text-align:right;color:rgba(244,240,232,.5)}}
    </style></head><body><div class="s">
      <div class="field"><img src="{img}"></div>
      <div class="band">
        <div class="lat kick">{latin}</div>
        <div class="t1">{title}</div>
        <div class="row">
          <div class="body sl">{slogan}</div>
          <div class="ui side">Layout 02<br>Band / Field</div>
        </div>
      </div>
    </div></body></html>"""
    render(html, out)


def layout_axis_tension(image, out, title="夜航", latin="Night Voyage", slogan="她把城市调成静音"):
    """对角张力：字块左下压角，西文右上拉线，中间留给主体。"""
    img = b64(image)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css(img)}
      .veil{{position:absolute;inset:0;background:
        linear-gradient(25deg,rgba(10,10,12,.78) 0%,rgba(10,10,12,.15) 42%,transparent 60%),
        linear-gradient(200deg,rgba(10,10,12,.35),transparent 35%)}}
      .tr{{position:absolute;right:8%;top:8%;text-align:right}}
      .tr .lat{{color:rgba(244,240,232,.8)}}
      .tr .year{{font-family:Didot,serif;font-size:34px;letter-spacing:.12em;color:rgba(212,184,150,.92);margin-top:10px}}
      .bl{{position:absolute;left:7%;bottom:12%;right:28%}}
      .t1{{font-family:'PHH',sans-serif;font-size:120px;line-height:.88;letter-spacing:-.01em;color:#F4F0E8;font-weight:900}}
      .sl{{margin-top:20px;max-width:12em;color:rgba(244,240,232,.82)}}
      .en{{margin-top:14px;font-family:Futura,sans-serif;letter-spacing:.48em;font-size:12px;color:rgba(212,184,150,.9);text-transform:uppercase}}
    </style></head><body><div class="s">
      <img class="bg" src="{img}">
      <div class="veil"></div>
      <div class="tr">
        <div class="lat">{latin}</div>
        <div class="year">MMXXVI</div>
      </div>
      <div class="bl">
        <div class="t1">{title}</div>
        <div class="body sl">{slogan}</div>
        <div class="en">Agnes Layout · Diagonal</div>
      </div>
    </div></body></html>"""
    render(html, out)


def layout_window_editorial(image, out, title="夜航", latin="Night Voyage", slogan="一部还没写完的电影"):
    """杂志开窗：大留白纸面 + 开窗看图 + 书脊式标题。"""
    img = b64(image)
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css(img)}
      .paper{{position:absolute;inset:0;background:#F2EDE4}}
      .win{{position:absolute;left:18%;right:18%;top:18%;bottom:32%;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.12)}}
      .win img{{width:100%;height:100%;object-fit:cover}}
      .spine{{position:absolute;left:7%;top:16%;bottom:28%;width:1px;background:rgba(20,18,16,.18)}}
      .t1{{position:absolute;left:10%;top:12%;writing-mode:vertical-rl;
        font-family:'NSB',serif;font-size:64px;letter-spacing:.28em;color:#1A1612;font-weight:900}}
      .cap{{position:absolute;left:18%;right:18%;bottom:14%}}
      .cap .lat{{color:rgba(26,22,18,.55)}}
      .cap .sl{{font-family:'PHM',sans-serif;font-size:16px;letter-spacing:.22em;color:#2A241E;margin-top:12px}}
      .idx{{position:absolute;right:8%;top:12%;font-family:Didot,serif;font-size:28px;letter-spacing:.15em;color:rgba(26,22,18,.55)}}
    </style></head><body><div class="s">
      <div class="paper"></div>
      <div class="win"><img src="{img}"></div>
      <div class="spine"></div>
      <div class="t1">{title}</div>
      <div class="idx">No.01</div>
      <div class="cap">
        <div class="lat">{latin}</div>
        <div class="sl">{slogan}</div>
      </div>
    </div></body></html>"""
    render(html, out)


def main():
    base = ROOT / "outputs" / "epic_compare" / "clean_base.png"
    out = ROOT / "outputs" / "layout_study"
    out.mkdir(parents=True, exist_ok=True)
    if not base.exists():
        raise SystemExit("need clean_base.png")
    layout_swiss_asym(base, out / "layout_01_swiss_asym.png")
    layout_type_band(base, out / "layout_02_type_band.png")
    layout_axis_tension(base, out / "layout_03_axis_tension.png")
    layout_window_editorial(base, out / "layout_04_window_editorial.png")
    print("done →", out)


if __name__ == "__main__":
    main()
