#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""反 slop 海报：一个巨型事件 + 三级字阶 + 最多一种表现手法。"""
from __future__ import annotations

import base64
from html import escape
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
NSB = resolve_font_path("serif")
PHH = resolve_font_path("sans")
PHM = resolve_font_path("sans")
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


def css(extra: str = "") -> str:
    nsb_font = resolve_font_path("serif")
    phh_font = resolve_font_path("sans")
    phm_font = resolve_font_path("sans")
    return f"""
    @font-face{{font-family:'NSB';src:url('file://{nsb_font}') format('opentype'), url('file://{nsb_font}') format('truetype');}}
    @font-face{{font-family:'PHH';src:url('file://{phh_font}') format('truetype');}}
    @font-face{{font-family:'PHM';src:url('file://{phm_font}') format('truetype');}}
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{width:864px;height:1152px;overflow:hidden;background:#000}}
    .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
    .bg{{width:100%;height:100%;object-fit:cover;filter:contrast(1.08) saturate(.9)}}
    .micro{{font-family:Futura,'Helvetica Neue','SmileySans',sans-serif;font-size:11px;letter-spacing:.42em;text-transform:uppercase}}
    .sup{{font-family:'PHM','SmileySans',sans-serif;font-size:16px;letter-spacing:.28em}}
    {extra}
    """


def build_mega_bleed_html(
    image: str,
    title: str = "夜航",
    subtitle_top: str = "Night Voyage",
    subtitle_bottom: str = "Agnes · 2026",
    extra_css: str = "",
) -> str:
    clean_img = sanitize_img_uri(image)
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_top = escape(str(subtitle_top if subtitle_top is not None else "Night Voyage"))
    safe_bottom = escape(str(subtitle_bottom if subtitle_bottom is not None else "Agnes · 2026"))
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css(extra_css)}
      .bg{{filter:contrast(1.12) saturate(.85) brightness(.92)}}
      .macro{{
        position:absolute;left:4%;right:-6%;bottom:18%;
        font-family:'PHH','SmileySans',sans-serif;font-size:176px;line-height:.82;
        letter-spacing:-.03em;color:#F2EEE6;font-weight:900;
        white-space:nowrap;
      }}
      .micro-t{{position:absolute;left:5%;top:8%;color:rgba(242,238,230,.85)}}
      .micro-b{{position:absolute;right:6%;bottom:8%;color:rgba(212,184,150,.95)}}
      .fade{{position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,rgba(0,0,0,.55) 100%)}}
    </style></head><body><div class="s">
      <img class="bg" src="{clean_img}"><div class="fade"></div>
      <div class="micro micro-t">{safe_top}</div>
      <div class="macro">{safe_title}</div>
      <div class="micro micro-b">{safe_bottom}</div>
    </div></body></html>"""


def mega_bleed(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    subtitle_top: str = "Night Voyage",
    subtitle_bottom: str = "Agnes · 2026",
) -> Path:
    """named move: mega-title-bleed — 巨字贴边裁切，仅 macro+micro。"""
    img = b64(image)
    html = build_mega_bleed_html(img, title=title, subtitle_top=subtitle_top, subtitle_bottom=subtitle_bottom)
    return shot(html, out)


def build_hard_field_html(
    image: str,
    title: str = "夜航",
    tagline: str = "她把城市调成静音",
    micro_text: str = "A Film Still",
    extra_css: str = "",
) -> str:
    clean_img = sanitize_img_uri(image)
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_tagline = escape(str(tagline if tagline is not None else "她把城市调成静音"))
    safe_micro = escape(str(micro_text if micro_text is not None else "A Film Still"))
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css(extra_css)}
      .field{{
        position:absolute;left:0;right:0;bottom:0;height:36%;
        background:#0A0A0C;
      }}
      .macro{{
        position:absolute;left:7%;bottom:16%;
        font-family:'NSB','LXGWWenKai','Songti SC',serif;font-size:128px;letter-spacing:.22em;
        color:#F2EEE6;line-height:1;
      }}
      .sup{{position:absolute;left:7%;bottom:9%;color:rgba(212,184,150,.92)}}
      .micro-t{{position:absolute;left:7%;top:7%;color:rgba(242,238,230,.8)}}
    </style></head><body><div class="s">
      <img class="bg" src="{clean_img}" style="height:68%">
      <div class="field"></div>
      <div class="micro micro-t">{safe_micro}</div>
      <div class="macro">{safe_title}</div>
      <div class="sup">{safe_tagline}</div>
    </div></body></html>"""


def hard_field(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    tagline: str = "她把城市调成静音",
    micro_text: str = "A Film Still",
) -> Path:
    """named move: hard-field-inversion — 底部硬色场反转，标题可读通道。"""
    img = b64(image)
    html = build_hard_field_html(img, title=title, tagline=tagline, micro_text=micro_text)
    return shot(html, out)


def build_chinese_corner_html(
    image: str,
    title: str = "夜航",
    subtitle: str = "Night Voyage",
    bottom_label: str = "Agnes Studio",
    seal_char: str = "航",
    extra_css: str = "",
) -> str:
    clean_img = sanitize_img_uri(image)
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_sub = escape(str(subtitle if subtitle is not None else "Night Voyage"))
    safe_bottom = escape(str(bottom_label if bottom_label is not None else "Agnes Studio"))
    safe_seal = escape(str(seal_char if seal_char is not None else "航"))
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css(extra_css)}
      .veil{{position:absolute;inset:0;background:linear-gradient(215deg,rgba(0,0,0,.62) 0%,transparent 42%)}}
      .macro{{
        position:absolute;right:8%;top:10%;
        writing-mode:vertical-rl;
        font-family:'NSB','LXGWWenKai','Songti SC',serif;font-size:108px;letter-spacing:.2em;
        color:#F2EEE6;line-height:1;
      }}
      .sup{{
        position:absolute;right:calc(8% + 130px);top:12%;
        writing-mode:vertical-rl;
        font-family:'PHM','SmileySans',sans-serif;font-size:13px;letter-spacing:.35em;
        color:rgba(242,238,230,.7);
      }}
      .micro-b{{position:absolute;left:7%;bottom:7%;color:rgba(212,184,150,.9)}}
      .seal{{
        position:absolute;right:8%;bottom:10%;
        width:40px;height:40px;border:1.5px solid #B4232A;color:#B4232A;
        display:flex;align-items:center;justify-content:center;
        font-family:'NSB','LXGWWenKai','Songti SC',serif;font-size:16px;
      }}
    </style></head><body><div class="s">
      <img class="bg" src="{clean_img}"><div class="veil"></div>
      <div class="macro">{safe_title}</div>
      <div class="sup">{safe_sub}</div>
      <div class="micro micro-b">{safe_bottom}</div>
      <div class="seal">{safe_seal}</div>
    </div></body></html>"""


def chinese_corner(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    subtitle: str = "Night Voyage",
    bottom_label: str = "Agnes Studio",
    seal_char: str = "航",
) -> Path:
    """named move: 边角式 + 计白当黑 — 字藏一角，中间全给图。"""
    img = b64(image)
    html = build_chinese_corner_html(
        img,
        title=title,
        subtitle=subtitle,
        bottom_label=bottom_label,
        seal_char=seal_char,
    )
    return shot(html, out)


def main():
    base = ROOT / "outputs" / "epic_compare" / "clean_base.png"
    if not base.exists():
        base = ROOT / "public" / "assets" / "agnes_1789995698_9987.png"
    out = ROOT / "outputs" / "drama_study"
    out.mkdir(parents=True, exist_ok=True)
    mega_bleed(base, out / "drama_01_mega_bleed.png")
    hard_field(base, out / "drama_02_hard_field.png")
    chinese_corner(base, out / "drama_03_corner.png")
    print("done")


if __name__ == "__main__":
    main()
