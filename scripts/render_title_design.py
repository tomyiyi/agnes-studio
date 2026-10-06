#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""海报标题字设计（Title Lettering Design）——字本身被设计，不是摆字。

涵盖 6 大标题字设计范式：
1. T1 切割字 (t1_cut_slash): 倾斜色块斜切汉字，打破常规字形
2. T2 双层错位字 (t2_double_offset): 描边与实心字层叠错位
3. T3 反白色块切割 (t3_color_split): 几何切片多重着色
4. T4 字内图窗 (t4_image_in_type): 画面纹理穿透作为文字填充
5. T5 几何锁字 (t5_geo_lock): 四角取景器标定，字标徽章化
6. T6 描边挤压 (t6_outline_stretch): 极粗描边配合横向挤压与发光
"""
from __future__ import annotations

import argparse
import base64
from html import escape
import json
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


def shell(
    img: str,
    title_html: str,
    extra_css: str = "",
    rest: str = "",
    serif_font: str | None = None,
    sans_font: str | None = None,
    medium_font: str | None = None,
    oblique_font: str | None = None,
) -> str:
    """构建海报外层 HTML 骨架并注入跨平台字体定义。"""
    serif_p = resolve_font_path(serif_font or "serif")
    sans_p = resolve_font_path(sans_font or "sans")
    medium_p = resolve_font_path(medium_font or "wenkai")
    smiley_p = resolve_font_path(oblique_font or "smiley")
    safe_img = sanitize_img_uri(img)

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    @font-face{{font-family:'NSB';src:url('file://{serif_p}') format('opentype'), url('file://{serif_p}') format('truetype');}}
    @font-face{{font-family:'PHH';src:url('file://{sans_p}') format('truetype'), url('file://{sans_p}') format('opentype');}}
    @font-face{{font-family:'PHM';src:url('file://{medium_p}') format('truetype'), url('file://{medium_p}') format('opentype');}}
    @font-face{{font-family:'SM';src:url('file://{smiley_p}') format('truetype'), url('file://{smiley_p}') format('opentype');}}
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{width:864px;height:1152px;overflow:hidden;background:#000}}
    .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
    .bg{{width:100%;height:100%;object-fit:cover}}
    .lat{{font-family:Didot,Futura,'Times New Roman',serif;letter-spacing:.5em;text-transform:uppercase;font-size:12px}}
    {extra_css}
    </style></head><body><div class="s"><img class="bg" src="{safe_img}">{title_html}{rest}</div></body></html>"""


# ---------- 6 套标题字设计 HTML 构建器 ----------

def build_t1_cut_slash_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    slash_color: str = "#C8102E",
    extra_css: str = "",
) -> str:
    """T1 切割字：倾角色块切开宋体大标，打破常规字形。"""
    safe_title = escape(title or "夜航")
    safe_latin = escape(latin or "Night Voyage")
    safe_slogan = escape(slogan or "她把城市调成静音")
    safe_slash_color = escape(slash_color or "#C8102E")
    content = f"""
      <div class="wrap" style="position:absolute;left:8%;top:12%">
        <div class="lat" style="color:rgba(244,240,232,.75);margin-bottom:16px">{safe_latin}</div>
        <div class="cut" style="position:relative;display:inline-block">
          <div class="ns" style="font-family:'NSB',serif;font-size:148px;letter-spacing:.08em;line-height:.9;color:#F4F0E8">{safe_title}</div>
          <div class="slash" style="position:absolute;left:42%;top:-8%;width:6px;height:116%;background:{safe_slash_color};transform:rotate(12deg);z-index:5"></div>
        </div>
        <div class="sub" style="margin-top:18px;font-family:'PHM',sans-serif;font-size:16px;letter-spacing:.35em;color:rgba(244,240,232,.8)">{safe_slogan}</div>
      </div>
    """
    css = ".wrap{filter:drop-shadow(0 8px 24px rgba(0,0,0,.35))}\n" + (extra_css or "")
    return shell(image, content, extra_css=css)


def build_t2_double_offset_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage · 2026",
    stroke_color: str = "rgba(244,240,232,.55)",
    text_color: str = "#F4F0E8",
    extra_css: str = "",
) -> str:
    """T2 双层错位字：描边字 + 实心字错位叠放，层次分明。"""
    safe_title = escape(title or "夜航")
    safe_latin = escape(latin or "Night Voyage · 2026")
    safe_stroke = escape(stroke_color or "rgba(244,240,232,.55)")
    safe_text = escape(text_color or "#F4F0E8")
    content = f"""
      <div style="position:absolute;left:10%;top:14%">
        <div class="lat" style="color:#D4B896;margin-bottom:20px">{safe_latin}</div>
        <div style="position:relative;height:170px">
          <div style="position:absolute;left:18px;top:18px;font-family:'PHH',sans-serif;font-size:128px;letter-spacing:.06em;color:transparent;-webkit-text-stroke:1.5px {safe_stroke};line-height:1">{safe_title}</div>
          <div style="position:absolute;left:0;top:0;font-family:'PHH',sans-serif;font-size:128px;letter-spacing:.06em;color:{safe_text};line-height:1">{safe_title}</div>
        </div>
      </div>
    """
    return shell(image, content, extra_css=extra_css or "")


def build_t3_color_split_html(
    image: str,
    title: str = "夜航",
    latin: str = "A Film Still",
    slogan: str = "她把城市调成静音",
    split_color: str = "#C8102E",
    extra_css: str = "",
) -> str:
    """T3 反白色块切割：色块切入字，字被几何裁切多重着色。"""
    safe_title = escape(title or "夜航")
    safe_latin = escape(latin or "A Film Still")
    safe_slogan = escape(slogan or "她把城市调成静音")
    safe_split = escape(split_color or "#C8102E")
    content = f"""
      <div style="position:absolute;left:7%;top:18%">
        <div class="lat" style="color:rgba(244,240,232,.7);margin-bottom:14px">{safe_latin}</div>
        <div style="position:relative;display:inline-block;overflow:hidden;padding:8px 0">
          <div style="font-family:'NSB',serif;font-size:132px;letter-spacing:.16em;line-height:1;color:#F4F0E8;clip-path:polygon(0 0,100% 0,100% 58%,0 48%)">{safe_title}</div>
          <div style="position:absolute;left:0;top:48%;font-family:'NSB',serif;font-size:132px;letter-spacing:.16em;line-height:1;color:{safe_split};clip-path:polygon(0 12%,100% 0,100% 100%,0 100%)">{safe_title}</div>
        </div>
        <div style="margin-top:12px;font-family:'PHM',sans-serif;font-size:15px;letter-spacing:.32em;color:rgba(244,240,232,.85)">{safe_slogan}</div>
      </div>
    """
    return shell(image, content, extra_css=extra_css or "")


def build_t4_image_in_type_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    bar_color: str = "#C8102E",
    extra_css: str = "",
) -> str:
    """T4 字内图窗：标题字被底图照片填充，文字与环境融为一体。"""
    safe_img = sanitize_img_uri(image)
    safe_title = escape(title or "夜航")
    safe_latin = escape(latin or "Night Voyage")
    safe_slogan = escape(slogan or "她把城市调成静音")
    safe_bar = escape(bar_color or "#C8102E")
    content = f"""
      <div style="position:absolute;left:8%;top:16%;width:80%">
        <div class="lat" style="color:rgba(244,240,232,.8);margin-bottom:22px">{safe_latin}</div>
        <div style="font-family:'PHH',sans-serif;font-size:150px;line-height:.92;letter-spacing:.04em;
          background-image:url('{safe_img}');background-size:120% auto;background-position:30% 20%;
          -webkit-background-clip:text;background-clip:text;color:transparent;
          -webkit-text-stroke:1px rgba(244,240,232,.25);">{safe_title}</div>
        <div style="margin-top:20px;width:48px;height:2px;background:{safe_bar}"></div>
        <div style="margin-top:14px;font-family:'PHM',sans-serif;font-size:15px;letter-spacing:.38em;color:rgba(244,240,232,.8)">{safe_slogan}</div>
      </div>
    """
    return shell(image, content, extra_css=extra_css or "")


def build_t5_geo_lock_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    frame_color: str = "#D4B896",
    extra_css: str = "",
) -> str:
    """T5 几何锁字：四角取景器线框锁字，标定 logo 化。"""
    safe_title = escape(title or "夜航")
    safe_latin = escape(latin or "Night Voyage")
    safe_slogan = escape(slogan or "她把城市调成静音")
    safe_frame = escape(frame_color or "#D4B896")
    content = f"""
      <div style="position:absolute;left:50%;top:16%;transform:translateX(-50%);text-align:center">
        <div class="lat" style="color:rgba(244,240,232,.75);margin-bottom:18px">{safe_latin}</div>
        <div style="position:relative;display:inline-block;padding:28px 40px">
          <div style="position:absolute;left:0;top:0;width:28px;height:28px;border-left:2px solid {safe_frame};border-top:2px solid {safe_frame}"></div>
          <div style="position:absolute;right:0;top:0;width:28px;height:28px;border-right:2px solid {safe_frame};border-top:2px solid {safe_frame}"></div>
          <div style="position:absolute;left:0;bottom:0;width:28px;height:28px;border-left:2px solid {safe_frame};border-bottom:2px solid {safe_frame}"></div>
          <div style="position:absolute;right:0;bottom:0;width:28px;height:28px;border-right:2px solid {safe_frame};border-bottom:2px solid {safe_frame}"></div>
          <div style="font-family:'NSB',serif;font-size:118px;letter-spacing:.28em;line-height:1;color:#F4F0E8;padding-left:.28em">{safe_title}</div>
        </div>
        <div style="margin-top:20px;font-family:'PHM',sans-serif;font-size:14px;letter-spacing:.42em;color:rgba(244,240,232,.8)">{safe_slogan}</div>
      </div>
    """
    return shell(image, content, extra_css=extra_css or "")


def build_t6_outline_stretch_html(
    image: str,
    title: str = "夜航",
    latin: str = "2026 / NIGHT",
    slogan: str = "她把城市调成静音",
    stroke_color: str = "#F4F0E8",
    extra_css: str = "",
) -> str:
    """T6 渐变描边大字 + 侧向挤压：强张力先锋现代感。"""
    safe_title = escape(title or "夜航")
    safe_latin = escape(latin or "2026 / NIGHT")
    safe_slogan = escape(slogan or "她把城市调成静音")
    safe_stroke = escape(stroke_color or "#F4F0E8")
    content = f"""
      <div style="position:absolute;left:6%;top:20%">
        <div class="lat" style="color:#D4B896;margin-bottom:12px">{safe_latin}</div>
        <div style="font-family:'PHH',sans-serif;font-size:160px;line-height:.86;letter-spacing:-.02em;
          color:transparent;-webkit-text-stroke:2.5px {safe_stroke};
          text-shadow: 0 0 40px rgba(244,240,232,.15);
          transform:scaleX(0.92);transform-origin:left center;">{safe_title}</div>
        <div style="margin-top:22px;display:flex;align-items:center;gap:16px">
          <div style="width:64px;height:1px;background:rgba(244,240,232,.5)"></div>
          <div style="font-family:'PHM',sans-serif;font-size:15px;letter-spacing:.34em;color:rgba(244,240,232,.85)">{safe_slogan}</div>
        </div>
      </div>
    """
    return shell(image, content, extra_css=extra_css or "")


# ---------- 渲染与对外输出接口 ----------

def render_html(
    html: str,
    out: str | Path,
    size=(864, 1152),
    timeout_ms: int = 500,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    """使用 Playwright 渲染 HTML 为高清海报 PNG。"""
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        if not quiet:
            print(f"  ✓ {out_path.name} (dry_run)")
        return out_path
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


def shot(
    html: str,
    out: str | Path,
    size=(864, 1152),
    timeout_ms: int = 500,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    """向下兼容别名，调用 render_html。"""
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_t1_cut_slash(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    slash_color: str = "#C8102E",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 500,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = sanitize_img_uri(b64(image))
    html = build_t1_cut_slash_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        slash_color=slash_color,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_t2_double_offset(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage · 2026",
    stroke_color: str = "rgba(244,240,232,.55)",
    text_color: str = "#F4F0E8",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 500,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = sanitize_img_uri(b64(image))
    html = build_t2_double_offset_html(
        img,
        title=title,
        latin=latin,
        stroke_color=stroke_color,
        text_color=text_color,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_t3_color_split(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "A Film Still",
    slogan: str = "她把城市调成静音",
    split_color: str = "#C8102E",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 500,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = sanitize_img_uri(b64(image))
    html = build_t3_color_split_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        split_color=split_color,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_t4_image_in_type(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    bar_color: str = "#C8102E",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 500,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = sanitize_img_uri(b64(image))
    html = build_t4_image_in_type_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        bar_color=bar_color,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_t5_geo_lock(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    frame_color: str = "#D4B896",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 500,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = sanitize_img_uri(b64(image))
    html = build_t5_geo_lock_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        frame_color=frame_color,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_t6_outline_stretch(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "2026 / NIGHT",
    slogan: str = "她把城市调成静音",
    stroke_color: str = "#F4F0E8",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 500,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = sanitize_img_uri(b64(image))
    html = build_t6_outline_stretch_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        stroke_color=stroke_color,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


TITLE_DESIGN_REGISTRY = {
    "t1_cut_slash": render_t1_cut_slash,
    "t2_double_offset": render_t2_double_offset,
    "t3_color_split": render_t3_color_split,
    "t4_image_in_type": render_t4_image_in_type,
    "t5_geo_lock": render_t5_geo_lock,
    "t6_outline_stretch": render_t6_outline_stretch,
}


# =============================================================================
# 风格注册表与多风格派发器
# =============================================================================

TITLE_DESIGN_STYLES = {
    "t1_cut_slash": {
        "name": "斜切刀锋 (Slanted Cut Slash)",
        "func": render_t1_cut_slash,
        "default_file": "t1_cut_slash.png",
        "default_latin": "Night Voyage",
        "description": "倾斜色块斜切汉字，打破常规字形，高冲击力几何刀锋",
    },
    "t2_double_offset": {
        "name": "叠字双影 / 描边错位 (Double Offset Stroke)",
        "func": render_t2_double_offset,
        "default_file": "t2_double_offset.png",
        "default_latin": "Night Voyage · 2026",
        "description": "描边与实心字层叠错位，双影层次与先锋视觉张力",
    },
    "t3_color_split": {
        "name": "色块反相切割 (Color Split Inversion)",
        "func": render_t3_color_split,
        "default_file": "t3_color_split.png",
        "default_latin": "A Film Still",
        "description": "色块反相几何切片，多重撞色与结构分割",
    },
    "t4_image_in_type": {
        "name": "镂空透图 (Image in Type)",
        "func": render_t4_image_in_type,
        "default_file": "t4_image_in_type.png",
        "default_latin": "Night Voyage",
        "description": "底图纹理穿透文字镂空填充，字景合一",
    },
    "t5_geo_lock": {
        "name": "几何框定 (Geometric Lock Frame)",
        "func": render_t5_geo_lock,
        "default_file": "t5_geo_lock.png",
        "default_latin": "Night Voyage",
        "description": "四角取景器标定，字标徽章化与建筑级秩序稳定感",
    },
    "t6_outline_stretch": {
        "name": "渐变描边拉伸 (Outline Stretch)",
        "func": render_t6_outline_stretch,
        "default_file": "t6_outline_stretch.png",
        "default_latin": "2026 / NIGHT",
        "description": "渐变描边配合横向挤压拉伸，强张力现代先锋",
    },
}


def list_title_design_styles() -> list[dict[str, str]]:
    """列出所有已注册的标题字设计范式预设"""
    return [
        {
            "key": k,
            "name": v["name"],
            "default_file": v["default_file"],
            "description": v.get("description", ""),
        }
        for k, v in TITLE_DESIGN_STYLES.items()
    ]


def render_title_design_style(
    style: str,
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str | None = None,
    slogan: str | None = None,
    color: str | None = None,
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 500,
    quiet: bool = False,
    dry_run: bool = False,
    **kwargs,
) -> Path:
    """按标题字设范式名称派发渲染对应的海报"""
    key = style.strip().lower()
    if key not in TITLE_DESIGN_STYLES:
        raise KeyError(f"Unknown title design style: '{style}'. Available: {list(TITLE_DESIGN_STYLES.keys())}")
    style_meta = TITLE_DESIGN_STYLES[key]
    func = style_meta["func"]
    effective_latin = latin if latin is not None else style_meta["default_latin"]
    effective_slogan = slogan if slogan is not None else "她把城市调成静音"

    if key == "t1_cut_slash":
        slash_c = color if color is not None else "#C8102E"
        return func(
            image=image,
            out=out,
            title=title,
            latin=effective_latin,
            slogan=effective_slogan,
            slash_color=slash_c,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
            dry_run=dry_run,
        )
    elif key == "t2_double_offset":
        return func(
            image=image,
            out=out,
            title=title,
            latin=effective_latin,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
            dry_run=dry_run,
        )
    elif key == "t3_color_split":
        split_c = color if color is not None else "#C8102E"
        return func(
            image=image,
            out=out,
            title=title,
            latin=effective_latin,
            slogan=effective_slogan,
            split_color=split_c,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
            dry_run=dry_run,
        )
    elif key == "t4_image_in_type":
        bar_c = color if color is not None else "#C8102E"
        return func(
            image=image,
            out=out,
            title=title,
            latin=effective_latin,
            slogan=effective_slogan,
            bar_color=bar_c,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
            dry_run=dry_run,
        )
    elif key == "t5_geo_lock":
        frame_c = color if color is not None else "#D4B896"
        return func(
            image=image,
            out=out,
            title=title,
            latin=effective_latin,
            slogan=effective_slogan,
            frame_color=frame_c,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
            dry_run=dry_run,
        )
    elif key == "t6_outline_stretch":
        stroke_c = color if color is not None else "#F4F0E8"
        return func(
            image=image,
            out=out,
            title=title,
            latin=effective_latin,
            slogan=effective_slogan,
            stroke_color=stroke_c,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
            dry_run=dry_run,
        )
    else:
        return func(
            image=image,
            out=out,
            title=title,
            latin=effective_latin,
            slogan=effective_slogan,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
            dry_run=dry_run,
            **kwargs,
        )


def render_all_title_designs(
    image: str | Path,
    out_dir: str | Path | None = None,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    timeout_ms: int = 500,
    quiet: bool = False,
    dry_run: bool = False,
) -> dict[str, Path]:
    """批量渲染所有 6 大标题字设范式海报。"""
    target_dir = Path(out_dir) if out_dir else (ROOT / "outputs" / "title_design")
    target_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    results["t1_cut_slash"] = render_t1_cut_slash(
        image, target_dir / "t1_cut_slash.png", title=title, latin=latin, slogan=slogan, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    results["t2_double_offset"] = render_t2_double_offset(
        image, target_dir / "t2_double_offset.png", title=title, latin=f"{latin} · 2026", timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    results["t3_color_split"] = render_t3_color_split(
        image, target_dir / "t3_color_split.png", title=title, latin="A Film Still", slogan=slogan, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    results["t4_image_in_type"] = render_t4_image_in_type(
        image, target_dir / "t4_image_in_type.png", title=title, latin=latin, slogan=slogan, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    results["t5_geo_lock"] = render_t5_geo_lock(
        image, target_dir / "t5_geo_lock.png", title=title, latin=latin, slogan=slogan, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    results["t6_outline_stretch"] = render_t6_outline_stretch(
        image, target_dir / "t6_outline_stretch.png", title=title, latin="2026 / NIGHT", slogan=slogan, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    return results


def build_arg_parser() -> argparse.ArgumentParser:
    """构建海报标题字设计范式库渲染命令行参数解析器"""
    parser = argparse.ArgumentParser(description="Agnes Studio · 海报标题字设计范式库渲染引擎 (Title Design Renderer)")
    parser.add_argument(
        "--style",
        "-s",
        default="all",
        choices=["t1_cut_slash", "t2_double_offset", "t3_color_split", "t4_image_in_type", "t5_geo_lock", "t6_outline_stretch", "all"],
        help="标题字设范式: t1_cut_slash | t2_double_offset | t3_color_split | t4_image_in_type | t5_geo_lock | t6_outline_stretch | all (默认: all)",
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
        default=None,
        help="西文大标 (默认根据各版式预设提供)",
    )
    parser.add_argument(
        "--slogan",
        default="她把城市调成静音",
        help="文案副标 (默认: 她把城市调成静音)",
    )
    parser.add_argument(
        "--color",
        default=None,
        help="强调色 / 边框色 / 切割条色（十六进制色彩，默认依范式预设）",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用的标题字设范式预设",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出风格列表或批量执行结果报告",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预演模式：仅校验参数与规划输出路径，不唤起浏览器真实光栅化",
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    suppress_log = args.quiet or args.json

    try:
        if args.list:
            styles = list_title_design_styles()
            if args.json:
                print(json.dumps(styles, ensure_ascii=False, indent=2))
            elif not args.quiet:
                print("Agnes Studio 可用标题字设范式预设:")
                for s in styles:
                    print(f"  - [{s['key']}] {s['name']} -> {s['default_file']}")
            return 0

        # 确定输入源
        resolved_src = None
        input_path_arg = args.src or args.input
        if input_path_arg:
            p = Path(input_path_arg)
            if not p.is_file():
                err_msg = f"找不到输入底图: {input_path_arg}"
                if args.json:
                    print(json.dumps({"error": err_msg, "ok": False}, ensure_ascii=False))
                elif not args.quiet:
                    print(f"❌ {err_msg}", file=sys.stderr)
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
            err_msg = "未指定底图且未发现默认候选底图资产"
            if args.json:
                print(json.dumps({"error": err_msg, "ok": False}, ensure_ascii=False))
            elif not args.quiet:
                print(f"❌ {err_msg}", file=sys.stderr)
            return 1 if (args.strict or args.input) else 0

        target_styles = list(TITLE_DESIGN_STYLES.keys()) if args.style == "all" else [args.style]

        quiet = suppress_log
        report_items = []
        default_out_dir = Path(args.out_dir) if args.out_dir else (ROOT / "outputs" / "title_design")
        for st in target_styles:
            if args.out:
                out_path = Path(args.out)
                if args.style == "all":
                    out_path = out_path.with_name(f"{out_path.stem}_{st}{out_path.suffix or '.png'}")
            else:
                default_out_dir.mkdir(parents=True, exist_ok=True)
                out_path = default_out_dir / TITLE_DESIGN_STYLES[st]["default_file"]

            render_title_design_style(
                style=st,
                image=resolved_src,
                out=out_path,
                title=args.title,
                latin=args.latin,
                slogan=args.slogan,
                color=args.color,
                quiet=quiet,
                dry_run=args.dry_run,
            )
            report_items.append({
                "style": st,
                "name": TITLE_DESIGN_STYLES[st]["name"],
                "output": str(out_path),
                "dry_run": args.dry_run,
                "status": "ok",
            })
        if args.json:
            print(json.dumps(report_items, ensure_ascii=False, indent=2))
        elif not args.quiet:
            print("done")
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e), "ok": False}, ensure_ascii=False))
        elif not args.quiet:
            if getattr(args, "list", False):
                print(f"❌ 查询标题字设范式预设失败: {e}", file=sys.stderr)
            else:
                print(f"❌ 标题字设计海报渲染失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
