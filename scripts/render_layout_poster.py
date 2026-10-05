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

def render_html(html: str, out: str | Path, size=(864, 1152), timeout_ms: int = 550, quiet: bool = False) -> Path:
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
    if not quiet:
        size_kb = out_path.stat().st_size // 1024 if out_path.exists() else 0
        print(f"  ✓ {out_path.name} ({size_kb} KB)")
    return out_path


def render(html: str, out: str | Path, size=(864, 1152), timeout_ms: int = 550, quiet: bool = False) -> Path:
    """向下兼容别名，调用 render_html。"""
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet)


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
    quiet: bool = False,
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
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet)


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
    quiet: bool = False,
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
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet)


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
    quiet: bool = False,
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
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet)


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
    quiet: bool = False,
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
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet)


# =============================================================================
# 风格注册表与多风格派发器
# =============================================================================

LAYOUT_POSTER_STYLES = {
    "swiss_asym": {
        "name": "瑞士非对称网格 (Swiss Asymmetric)",
        "func": layout_swiss_asym,
        "default_file": "layout_01_swiss_asym.png",
        "default_slogan": "她把城市调成静音",
    },
    "type_band": {
        "name": "杂志色块字带 (Magazine Type Band)",
        "func": layout_type_band,
        "default_file": "layout_02_type_band.png",
        "default_slogan": "一部还没写完的电影",
    },
    "axis_tension": {
        "name": "对角轴线张力 (Diagonal Axis Tension)",
        "func": layout_axis_tension,
        "default_file": "layout_03_axis_tension.png",
        "default_slogan": "她把城市调成静音",
    },
    "window_editorial": {
        "name": "杂志开窗视界 (Window Editorial)",
        "func": layout_window_editorial,
        "default_file": "layout_04_window_editorial.png",
        "default_slogan": "一部还没写完的电影",
    },
}


def list_layout_poster_styles() -> list[dict[str, str]]:
    """列出所有已注册的海报设计排版范式预设"""
    return [
        {"key": k, "name": v["name"], "default_file": v["default_file"]}
        for k, v in LAYOUT_POSTER_STYLES.items()
    ]


def render_layout_poster_style(
    style: str,
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str | None = None,
    system_tag: str | None = None,
    num: str | None = None,
    tag: str | None = None,
    year_text: str | None = None,
    idx_text: str | None = None,
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 550,
    quiet: bool = False,
    **kwargs,
) -> Path:
    """按版式范式名称派发渲染对应的海报"""
    key = style.strip().lower()
    if key not in LAYOUT_POSTER_STYLES:
        raise KeyError(f"Unknown layout poster style: '{style}'. Available: {list(LAYOUT_POSTER_STYLES.keys())}")
    style_meta = LAYOUT_POSTER_STYLES[key]
    func = style_meta["func"]
    effective_slogan = slogan if slogan is not None else style_meta["default_slogan"]

    if key == "swiss_asym":
        s_tag = system_tag if system_tag is not None else "Swiss · Asym"
        n_str = num if num is not None else "01"
        return func(
            image=image,
            out=out,
            title=title,
            latin=latin,
            slogan=effective_slogan,
            system_tag=s_tag,
            num=n_str,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
        )
    elif key == "type_band":
        t_str = tag if tag is not None else "Layout 02<br>Band / Field"
        return func(
            image=image,
            out=out,
            title=title,
            latin=latin,
            slogan=effective_slogan,
            tag=t_str,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
        )
    elif key == "axis_tension":
        y_str = year_text if year_text is not None else "MMXXVI"
        t_str = tag if tag is not None else "Agnes Layout · Diagonal"
        return func(
            image=image,
            out=out,
            title=title,
            latin=latin,
            slogan=effective_slogan,
            year_text=y_str,
            tag=t_str,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
        )
    elif key == "window_editorial":
        i_str = idx_text if idx_text is not None else "No.01"
        return func(
            image=image,
            out=out,
            title=title,
            latin=latin,
            slogan=effective_slogan,
            idx_text=i_str,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
        )
    else:
        return func(
            image=image,
            out=out,
            title=title,
            latin=latin,
            slogan=effective_slogan,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
            **kwargs,
        )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Agnes Studio · 海报「设计排版」范式库渲染引擎 (Layout Poster Renderer)")
    parser.add_argument(
        "--style",
        "-s",
        default="all",
        choices=["swiss_asym", "type_band", "axis_tension", "window_editorial", "all"],
        help="海报版式风格: swiss_asym | type_band | axis_tension | window_editorial | all (默认: all)",
    )
    parser.add_argument(
        "--src",
        "--image",
        default=None,
        help="输入背景底图路径（未指定时探查默认底图）",
    )
    parser.add_argument(
        "--input",
        "-i",
        default=None,
        help="输入背景底图路径（兼容选项）",
    )
    parser.add_argument(
        "--out",
        "-o",
        default=None,
        help="输出海报路径（在 style=all 时将自动附加风格后缀）",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="输出目录（如果指定且未提供 --out，海报将输出至该目录）",
    )
    parser.add_argument(
        "--title",
        "-t",
        default="夜航",
        help="主标题 (默认: 夜航)",
    )
    parser.add_argument(
        "--latin",
        "-l",
        default="Night Voyage",
        help="西文大标 (默认: Night Voyage)",
    )
    parser.add_argument(
        "--slogan",
        default=None,
        help="文案副标 (默认根据各版式预设提供)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用的设计排版风格预设",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="静默模式，抑制控制台日志",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：遇到底图缺失或渲染异常时返回非零退出码 1",
    )
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.list:
        if not args.quiet:
            print("Agnes Studio 可用设计排版风格预设:")
            for s in list_layout_poster_styles():
                print(f"  - [{s['key']}] {s['name']} -> {s['default_file']}")
        return 0

    # 确定输入源
    resolved_src = None
    input_path_arg = args.src or args.input
    if input_path_arg:
        p = Path(input_path_arg)
        if not p.is_file():
            if not args.quiet:
                print(f"❌ 找不到输入底图: {input_path_arg}", file=sys.stderr)
            return 1 if (args.strict or args.input) else 0
        resolved_src = p
    else:
        candidates = [
            ROOT / "outputs" / "epic_compare" / "clean_base.png",
            ROOT / "public" / "assets" / "agnes_1789995698_9987.png",
            ROOT / "assets" / "agnes_1790006749_b2b755da.png",
            ROOT / "assets" / "agnes_1789995999_1670.png",
        ]
        for c in candidates:
            if c.is_file():
                resolved_src = c
                break

    if resolved_src is None:
        if not args.quiet:
            print("❌ 未指定底图且未发现默认候选底图资产", file=sys.stderr)
        return 1 if args.strict else 0

    target_styles = list(LAYOUT_POSTER_STYLES.keys()) if args.style == "all" else [args.style]

    try:
        default_out_dir = Path(args.out_dir) if args.out_dir else (ROOT / "outputs" / "layout_study")
        for st in target_styles:
            if args.out:
                out_path = Path(args.out)
                if args.style == "all":
                    out_path = out_path.with_name(f"{out_path.stem}_{st}{out_path.suffix or '.png'}")
            else:
                default_out_dir.mkdir(parents=True, exist_ok=True)
                out_path = default_out_dir / LAYOUT_POSTER_STYLES[st]["default_file"]

            render_layout_poster_style(
                style=st,
                image=resolved_src,
                out=out_path,
                title=args.title,
                latin=args.latin,
                slogan=args.slogan,
                quiet=args.quiet,
            )
        if not args.quiet:
            print("done")
        return 0
    except Exception as e:
        if not args.quiet:
            print(f"❌ 设计排版海报渲染失败: {e}", file=sys.stderr)
        return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
