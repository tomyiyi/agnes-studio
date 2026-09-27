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

def render_html(html: str, out: str | Path, size=(864, 1152), timeout_ms: int = 500) -> Path:
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


def shot(html: str, out: str | Path, size=(864, 1152), timeout_ms: int = 500) -> Path:
    """向下兼容别名，调用 render_html。"""
    return render_html(html, out, size=size, timeout_ms=timeout_ms)


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
    return render_html(html, out, size=size, timeout_ms=timeout_ms)


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
    return render_html(html, out, size=size, timeout_ms=timeout_ms)


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
    return render_html(html, out, size=size, timeout_ms=timeout_ms)


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
    return render_html(html, out, size=size, timeout_ms=timeout_ms)


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
    return render_html(html, out, size=size, timeout_ms=timeout_ms)


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
    return render_html(html, out, size=size, timeout_ms=timeout_ms)


TITLE_DESIGN_REGISTRY = {
    "t1_cut_slash": render_t1_cut_slash,
    "t2_double_offset": render_t2_double_offset,
    "t3_color_split": render_t3_color_split,
    "t4_image_in_type": render_t4_image_in_type,
    "t5_geo_lock": render_t5_geo_lock,
    "t6_outline_stretch": render_t6_outline_stretch,
}


def render_all_title_designs(
    image: str | Path,
    out_dir: str | Path | None = None,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    timeout_ms: int = 500,
) -> dict[str, Path]:
    """批量渲染所有 6 大标题字设范式海报。"""
    target_dir = Path(out_dir) if out_dir else (ROOT / "outputs" / "title_design")
    target_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    results["t1_cut_slash"] = render_t1_cut_slash(
        image, target_dir / "t1_cut_slash.png", title=title, latin=latin, slogan=slogan, timeout_ms=timeout_ms
    )
    results["t2_double_offset"] = render_t2_double_offset(
        image, target_dir / "t2_double_offset.png", title=title, latin=f"{latin} · 2026", timeout_ms=timeout_ms
    )
    results["t3_color_split"] = render_t3_color_split(
        image, target_dir / "t3_color_split.png", title=title, latin="A Film Still", slogan=slogan, timeout_ms=timeout_ms
    )
    results["t4_image_in_type"] = render_t4_image_in_type(
        image, target_dir / "t4_image_in_type.png", title=title, latin=latin, slogan=slogan, timeout_ms=timeout_ms
    )
    results["t5_geo_lock"] = render_t5_geo_lock(
        image, target_dir / "t5_geo_lock.png", title=title, latin=latin, slogan=slogan, timeout_ms=timeout_ms
    )
    results["t6_outline_stretch"] = render_t6_outline_stretch(
        image, target_dir / "t6_outline_stretch.png", title=title, latin="2026 / NIGHT", slogan=slogan, timeout_ms=timeout_ms
    )
    return results


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="海报标题字设计（Title Lettering Design）渲染器")
    parser.add_argument("--input", "-i", type=str, default=None, help="底图路径")
    parser.add_argument("--out-dir", "-o", type=str, default=None, help="输出目录")
    parser.add_argument("--title", type=str, default="夜航", help="主标题")
    parser.add_argument("--latin", type=str, default="Night Voyage", help="西文大标")
    parser.add_argument("--slogan", type=str, default="她把城市调成静音", help="文案副标")
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

    out_dir = Path(args.out_dir) if args.out_dir else (ROOT / "outputs" / "title_design")
    render_all_title_designs(base, out_dir=out_dir, title=args.title, latin=args.latin, slogan=args.slogan)
    print("done", out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
