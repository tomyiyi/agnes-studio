#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""海报「设计排版」范式库：同字体，改结构。

排版问题 = 网格 / 重心 / 层级关系 / 主题落位，不是换字。
涵盖 4 大专业版式系统：
1. 瑞士非对称网格 (layout_swiss_asym)
2. 上字带 / 下图场 (layout_type_band)
3. 对角张力 (layout_axis_tension)
4. 杂志开窗 (layout_window_editorial)
"""
from __future__ import annotations

import base64
from html import escape
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from env_config import (
    PROJECT_ROOT,
    FONTS_DIR,
    resolve_chrome_path,
    resolve_font_path,
)


def b64(p: str | Path) -> str:
    """将图片文件转化为 base64 数据 URI；若已经是 data URI 则直接返回。"""
    if isinstance(p, str) and p.startswith("data:image/"):
        return p
    path = Path(p)
    if not path.is_file():
        raise FileNotFoundError(f"Image file not found: {p}")
    suffix = path.suffix.lower()
    mime = "png"
    if suffix in (".jpg", ".jpeg"):
        mime = "jpeg"
    elif suffix == ".webp":
        mime = "webp"
    elif suffix == ".svg":
        mime = "svg+xml"
    elif suffix == ".gif":
        mime = "gif"
    return f"data:image/{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def sanitize_img_uri(uri: str) -> str:
    """过滤 URI 中可能引起 CSS 注入的换行与闭合字符。"""
    return (
        str(uri or "")
        .replace("\r", "")
        .replace("\n", "")
        .replace("'", "%27")
        .replace('"', "%22")
        .replace("<", "%3C")
        .replace(">", "%3E")
    )


def base_css(
    img: str = "",
    serif_font: str | None = None,
    sans_font: str | None = None,
    medium_font: str | None = None,
    extra_css: str = "",
) -> str:
    serif_p = resolve_font_path(serif_font or "serif")
    sans_p = resolve_font_path(sans_font or "sans")
    medium_p = resolve_font_path(medium_font or "wenkai")
    return f"""
      @font-face{{font-family:'NSB';src:url('file://{serif_p}') format('opentype'), url('file://{serif_p}') format('truetype');}}
      @font-face{{font-family:'NS';src:url('file://{serif_p}') format('opentype'), url('file://{serif_p}') format('truetype');}}
      @font-face{{font-family:'PHH';src:url('file://{sans_p}') format('truetype'), url('file://{sans_p}') format('opentype');}}
      @font-face{{font-family:'PHB';src:url('file://{sans_p}') format('truetype'), url('file://{sans_p}') format('opentype');}}
      @font-face{{font-family:'PHM';src:url('file://{medium_p}') format('truetype'), url('file://{medium_p}') format('opentype');}}
      *{{margin:0;padding:0;box-sizing:border-box}}
      body{{width:864px;height:1152px;overflow:hidden;background:#0A0A0C}}
      .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
      .bg{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:contrast(1.06) saturate(.88)}}
      .lat{{font-family:Didot,Bodoni,Baskerville,serif;letter-spacing:.5em;text-transform:uppercase;font-size:13px}}
      .ui{{font-family:Futura,'Helvetica Neue',sans-serif;letter-spacing:.35em;text-transform:uppercase;font-size:11px}}
      .cn{{font-family:'NSB','NS','Songti SC',serif}}
      .ph{{font-family:'PHH','PHB','PingFang SC',sans-serif}}
      .body{{font-family:'PHM','PingFang SC',sans-serif;letter-spacing:.18em;font-size:17px;line-height:1.8}}
      {extra_css}
    """


# ---------- 四套版式 HTML 构建器 ----------

def build_swiss_asym_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    system_tag: str = "Swiss · Asym",
    num: str = "01",
    extra_css: str = "",
) -> str:
    """构建【瑞士非对称：左栏字塔 + 右侧大图重心】海报 HTML。"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "Night Voyage"))
    safe_slogan = escape(str(slogan if slogan is not None else "她把城市调成静音"))
    safe_tag = escape(str(system_tag if system_tag is not None else "Swiss · Asym"))
    safe_num = escape(str(num if num is not None else "01"))

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css(image, extra_css=extra_css)}
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
      <img class="bg" src="{image}" style="filter:contrast(1.04) saturate(.8) brightness(.92)">
      <div class="colL">
        <div>
          <div class="lat top-lat">{safe_latin}</div>
          <div class="rule"></div>
          <div class="t1">{safe_title}</div>
          <div class="t2">Poster System</div>
        </div>
        <div>
          <div class="body sl">{safe_slogan}</div>
          <div class="foot" style="margin-top:28px">
            <div class="ui" style="color:rgba(244,240,232,.45)">{safe_tag}</div>
            <div class="num">{safe_num}</div>
          </div>
        </div>
      </div>
      <div class="colR"><img class="imgWin" src="{image}"></div>
    </div></body></html>"""


def build_type_band_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "一部还没写完的电影",
    tag: str = "Layout 02<br>Band / Field",
    extra_css: str = "",
) -> str:
    """构建【上字带 / 下图场：信息与视觉分区】海报 HTML。"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "Night Voyage"))
    safe_slogan = escape(str(slogan if slogan is not None else "一部还没写完的电影"))
    raw_tag = str(tag if tag is not None else "Layout 02<br>Band / Field")
    safe_tag = "<br>".join(escape(part.strip()) for part in raw_tag.split("<br>"))

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css(image, extra_css=extra_css)}
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
      <div class="field"><img src="{image}"></div>
      <div class="band">
        <div class="lat kick">{safe_latin}</div>
        <div class="t1">{safe_title}</div>
        <div class="row">
          <div class="body sl">{safe_slogan}</div>
          <div class="ui side">{safe_tag}</div>
        </div>
      </div>
    </div></body></html>"""


def build_axis_tension_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    year_text: str = "MMXXVI",
    tag: str = "Agnes Layout · Diagonal",
    extra_css: str = "",
) -> str:
    """构建【对角张力：字块左下压角，西文右上拉线】海报 HTML。"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "Night Voyage"))
    safe_slogan = escape(str(slogan if slogan is not None else "她把城市调成静音"))
    safe_year = escape(str(year_text if year_text is not None else "MMXXVI"))
    safe_tag = escape(str(tag if tag is not None else "Agnes Layout · Diagonal"))

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css(image, extra_css=extra_css)}
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
      <img class="bg" src="{image}">
      <div class="veil"></div>
      <div class="tr">
        <div class="lat">{safe_latin}</div>
        <div class="year">{safe_year}</div>
      </div>
      <div class="bl">
        <div class="t1">{safe_title}</div>
        <div class="body sl">{safe_slogan}</div>
        <div class="en">{safe_tag}</div>
      </div>
    </div></body></html>"""


def build_window_editorial_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "一部还没写完的电影",
    idx_text: str = "No.01",
    extra_css: str = "",
) -> str:
    """构建【杂志开窗：大留白纸面 + 开窗看图 + 书脊式标题】海报 HTML。"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "Night Voyage"))
    safe_slogan = escape(str(slogan if slogan is not None else "一部还没写完的电影"))
    safe_idx = escape(str(idx_text if idx_text is not None else "No.01"))

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css(image, extra_css=extra_css)}
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
      <div class="win"><img src="{image}"></div>
      <div class="spine"></div>
      <div class="t1">{safe_title}</div>
      <div class="idx">{safe_idx}</div>
      <div class="cap">
        <div class="lat">{safe_latin}</div>
        <div class="sl">{safe_slogan}</div>
      </div>
    </div></body></html>"""


# ---------- 渲染与对外输出接口 ----------

def render_html(html: str, out: str | Path, size=(864, 1152), timeout_ms: int = 550) -> Path:
    """使用 Playwright 渲染 HTML 为高清海报 PNG。"""
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright

    chrome_path = resolve_chrome_path()
    kw = {"headless": True}
    if chrome_path:
        kw["executable_path"] = chrome_path
    w, h = size
    with sync_playwright() as p:
        browser = p.chromium.launch(**kw)
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
        page.set_content(html)
        if timeout_ms > 0:
            page.wait_for_timeout(timeout_ms)
        page.screenshot(path=str(out_path), type="png")
        browser.close()
    size_kb = out_path.stat().st_size // 1024 if out_path.exists() else 0
    print(f"  ✓ {out_path.name} ({size_kb} KB)")
    return out_path


def render(html: str, out: str | Path, size=(864, 1152), timeout_ms: int = 550) -> Path:
    """向下兼容别名，调用 render_html。"""
    return render_html(html, out, size=size, timeout_ms=timeout_ms)


def layout_swiss_asym(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    system_tag: str = "Swiss · Asym",
    num: str = "01",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 550,
) -> Path:
    """瑞士非对称：左栏字塔 + 右侧大图重心；12 列意识。"""
    img = sanitize_img_uri(b64(image))
    html = build_swiss_asym_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        system_tag=system_tag,
        num=num,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms)


def layout_type_band(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "一部还没写完的电影",
    tag: str = "Layout 02<br>Band / Field",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 550,
) -> Path:
    """上字带 / 下图场：信息与视觉分区，电影预告结构。"""
    img = sanitize_img_uri(b64(image))
    html = build_type_band_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        tag=tag,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms)


def layout_axis_tension(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    year_text: str = "MMXXVI",
    tag: str = "Agnes Layout · Diagonal",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 550,
) -> Path:
    """对角张力：字块左下压角，西文右上拉线，中间留给主体。"""
    img = sanitize_img_uri(b64(image))
    html = build_axis_tension_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        year_text=year_text,
        tag=tag,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms)


def layout_window_editorial(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "一部还没写完的电影",
    idx_text: str = "No.01",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 550,
) -> Path:
    """杂志开窗：大留白纸面 + 开窗看图 + 书脊式标题。"""
    img = sanitize_img_uri(b64(image))
    html = build_window_editorial_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        idx_text=idx_text,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms)


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="海报「设计排版」范式库渲染器")
    parser.add_argument("--input", "-i", type=str, default=None, help="底图路径")
    parser.add_argument("--out-dir", "-o", type=str, default=None, help="输出目录")
    parser.add_argument("--title", type=str, default="夜航", help="主标题")
    parser.add_argument("--latin", type=str, default="Night Voyage", help="西文大标")
    parser.add_argument("--slogan", type=str, default=None, help="文案副标")
    args = parser.parse_args(argv)

    if args.input:
        base = Path(args.input)
    else:
        base = ROOT / "outputs" / "epic_compare" / "clean_base.png"
        if not base.exists():
            base = ROOT / "public" / "assets" / "agnes_1789995698_9987.png"

    if not base.exists():
        print(f"⚠️ 未找到可用底图: {base}")
        return 1

    out_dir = Path(args.out_dir) if args.out_dir else (ROOT / "outputs" / "layout_study")
    out_dir.mkdir(parents=True, exist_ok=True)

    slogan_default_1 = args.slogan or "她把城市调成静音"
    slogan_default_2 = args.slogan or "一部还没写完的电影"

    layout_swiss_asym(base, out_dir / "layout_01_swiss_asym.png", title=args.title, latin=args.latin, slogan=slogan_default_1)
    layout_type_band(base, out_dir / "layout_02_type_band.png", title=args.title, latin=args.latin, slogan=slogan_default_2)
    layout_axis_tension(base, out_dir / "layout_03_axis_tension.png", title=args.title, latin=args.latin, slogan=slogan_default_1)
    layout_window_editorial(base, out_dir / "layout_04_window_editorial.png", title=args.title, latin=args.latin, slogan=slogan_default_2)
    print("done →", out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
