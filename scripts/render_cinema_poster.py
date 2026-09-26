#!/usr/bin/env python3
"""电影级极简海报：去掉一切教材腔，只留图 + 极少字 + 真负空间。"""
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

F = FONTS_DIR
NS_BLACK = resolve_font_path("serif")
PH_H = resolve_font_path("sans")
PH_M = resolve_font_path("sans")
DIDOT = resolve_font_path("didot")
FUTURA = resolve_font_path("futura")


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


def shot(html: str, out: str | Path, size=(864, 1152), timeout_ms: int = 500) -> Path:
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright

    chrome_path = resolve_chrome_path()
    kw = {"headless": True}
    if chrome_path:
        kw["executable_path"] = chrome_path

    w, h = size
    with sync_playwright() as p:
        b = p.chromium.launch(**kw)
        page = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
        page.set_content(html)
        if timeout_ms > 0:
            page.wait_for_timeout(timeout_ms)
        page.screenshot(path=str(out_path), type="png")
        b.close()
    size_kb = out_path.stat().st_size // 1024 if out_path.exists() else 0
    print(f" ✓ {out_path.name} {size_kb} KB")
    return out_path


def wrap(img: str, inner: str, extra_css: str = "") -> str:
    ns_font = resolve_font_path("serif")
    ph_font = resolve_font_path("sans")
    clean_img = sanitize_img_uri(img)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      @font-face{{font-family:'NSB';src:url('file://{ns_font}') format('opentype'), url('file://{ns_font}') format('truetype');}}
      @font-face{{font-family:'PHH';src:url('file://{ph_font}') format('truetype');}}
      @font-face{{font-family:'PHM';src:url('file://{ph_font}') format('truetype');}}
      *{{margin:0;padding:0;box-sizing:border-box}}
      body{{width:864px;height:1152px;overflow:hidden;background:#000}}
      .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
      .bg{{width:100%;height:100%;object-fit:cover;filter:contrast(1.05) saturate(.92)}}
      .cream{{color:#F3EFE6}}
      .lat{{font-family:Didot,Futura,'SmileySans','Times New Roman',serif;letter-spacing:.55em;text-transform:uppercase;font-size:12px}}
      .ph{{font-family:'PHH','PHM','SmileySans',-apple-system,sans-serif;font-weight:900}}
      .ns{{font-family:'NSB','LXGWWenKai','Songti SC','Source Han Serif SC',serif}}
      {extra_css}
    </style></head><body><div class="s"><img class="bg" src="{clean_img}">{inner}</div></body></html>"""


def build_film_bottom_html(
    img_uri: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    tagline: str = "A FILM STILL · AGNES",
    extra_css: str = "",
) -> str:
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "Night Voyage"))
    safe_tagline = escape(str(tagline if tagline is not None else "A FILM STILL · AGNES"))
    inner = f"""
      <div style="position:absolute;inset:0;background:linear-gradient(180deg,transparent 42%,rgba(0,0,0,.25) 62%,rgba(0,0,0,.88) 100%)"></div>
      <div style="position:absolute;left:0;right:0;bottom:14%;text-align:center">
        <div class="lat cream" style="opacity:.75;margin-bottom:22px">{safe_latin}</div>
        <div class="ph cream" style="font-size:132px;letter-spacing:.18em;line-height:1">{safe_title}</div>
        <div class="lat cream" style="opacity:.55;margin-top:26px;letter-spacing:.35em;font-family:Futura,sans-serif;font-size:11px">{safe_tagline}</div>
      </div>"""
    return wrap(img_uri, inner, extra_css=extra_css)


def film_bottom(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    tagline: str = "A FILM STILL · AGNES",
) -> Path:
    """经典电影海报：巨标压底，西文其上，几乎无装饰。"""
    img = b64(image)
    html = build_film_bottom_html(img, title=title, latin=latin, tagline=tagline)
    return shot(html, out)


def build_film_top_html(
    img_uri: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    tagline: str = "她把城市调成静音",
    extra_css: str = "",
) -> str:
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "Night Voyage"))
    safe_tagline = escape(str(tagline if tagline is not None else "她把城市调成静音"))
    inner = f"""
      <div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.72) 0%,rgba(0,0,0,.15) 28%,transparent 48%)"></div>
      <div style="position:absolute;left:0;right:0;top:9%;text-align:center">
        <div class="lat cream" style="opacity:.7;margin-bottom:28px">{safe_latin}</div>
        <div class="ns cream" style="font-size:118px;letter-spacing:.28em;line-height:1">{safe_title}</div>
      </div>
      <div style="position:absolute;left:0;right:0;bottom:7%;text-align:center">
        <div class="lat cream" style="opacity:.5;font-family:Futura,sans-serif;letter-spacing:.4em;font-size:11px">{safe_tagline}</div>
      </div>"""
    return wrap(img_uri, inner, extra_css=extra_css)


def film_top(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    tagline: str = "她把城市调成静音",
) -> Path:
    """上标下图：字在天空/空场，主体完整。"""
    img = b64(image)
    html = build_film_top_html(img, title=title, latin=latin, tagline=tagline)
    return shot(html, out)


def build_side_rail_html(
    img_uri: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    tagline: str = "她把城市调成静音",
    extra_css: str = "",
) -> str:
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "Night Voyage"))
    safe_tagline = escape(str(tagline if tagline is not None else "她把城市调成静音"))
    inner = f"""
      <div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.55) 0%,rgba(0,0,0,.1) 32%,transparent 55%)"></div>
      <div style="position:absolute;left:8%;top:12%;bottom:12%;display:flex;flex-direction:column;justify-content:space-between">
        <div>
          <div class="lat cream" style="opacity:.75;writing-mode:vertical-rl;letter-spacing:.45em;height:180px">{safe_latin}</div>
        </div>
        <div>
          <div class="ns cream" style="writing-mode:vertical-rl;font-size:96px;letter-spacing:.22em;line-height:1">{safe_title}</div>
          <div style="width:1px;height:48px;background:rgba(243,239,230,.45);margin:24px 0 0 8px"></div>
          <div class="ph cream" style="font-size:13px;letter-spacing:.32em;opacity:.7;margin-top:20px">{safe_tagline}</div>
        </div>
      </div>"""
    return wrap(img_uri, inner, extra_css=extra_css)


def side_rail(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    tagline: str = "她把城市调成静音",
) -> Path:
    """极简左轴：竖排大标 + 一条细线，其余全给图。"""
    img = b64(image)
    html = build_side_rail_html(img, title=title, latin=latin, tagline=tagline)
    return shot(html, out)


def main():
    base = ROOT / "outputs" / "epic_compare" / "clean_base.png"
    if not base.exists():
        base = ROOT / "public" / "assets" / "agnes_1789995698_9987.png"
    out = ROOT / "outputs" / "cinema_study"
    out.mkdir(parents=True, exist_ok=True)
    film_bottom(base, out / "cine_01_bottom.png")
    film_top(base, out / "cine_02_top.png")
    side_rail(base, out / "cine_03_rail.png")
    print("done")


if __name__ == "__main__":
    main()
