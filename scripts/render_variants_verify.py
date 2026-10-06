#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量版式变体渲染器 — 不挡人物，少特效。统一用 clean_base，字只进负空间。

支持 8 大经典版式构图范式：
- V1 顶部标题 (v1_top_title): 字在天空，不碰人物主体
- V2 左上角字 (v2_topleft): 图右侧人物完整，左上块级排版
- V3 竖排右上 (v3_vertical_corner): 竖排字在右侧空场，左上极简西文
- V4 极简角标 (v4_bottom_left_min): 仅 micro 英文 + 左下小主标
- V5 负空间大留白 (v5_whisper): 年份标与留白，轻声细语
- V6 中轴顶部横排 (v6_center_top): 中轴横排巨字 + 下方西文短句
- V7 对角极简 (v7_diag_minimal): 左上西文 + 左下小主标，对角呼应
- V8 竖排书名与印章 (v8_vertical_seal): 纯粹竖排金石印章，零杂质
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


def get_base_css(extra: str = "") -> str:
    """跨平台解析字体路径并生成基础 CSS 定义。"""
    nsb = resolve_font_path("serif")
    phh = resolve_font_path("sans")
    phm = resolve_font_path("sans")
    return f"""
    @font-face{{font-family:'NSB';src:url('file://{nsb}') format('opentype'), url('file://{nsb}') format('truetype');}}
    @font-face{{font-family:'PHH';src:url('file://{phh}') format('truetype'), url('file://{phh}') format('opentype');}}
    @font-face{{font-family:'PHM';src:url('file://{phm}') format('truetype'), url('file://{phm}') format('opentype');}}
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{width:864px;height:1152px;overflow:hidden;background:#000}}
    .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
    .bg{{width:100%;height:100%;object-fit:cover}}
    .lat{{font-family:Didot,Futura,serif;letter-spacing:.5em;text-transform:uppercase;font-size:12px}}
    .ph{{font-family:'PHH',sans-serif}}
    .ns{{font-family:'NSB',serif}}
    .sup{{font-family:'PHM',sans-serif;letter-spacing:.28em;font-size:15px}}
    {extra}
    """


def shell(img: str, inner: str, extra: str = "") -> str:
    """将内部排版片段组装为完整 HTML 画布容器。"""
    clean_img = sanitize_img_uri(img)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{get_base_css(extra)}
    </style></head><body><div class="s"><img class="bg" src="{clean_img}">{inner}</div></body></html>"""


def shot(
    html: str,
    out: str | Path,
    size=(864, 1152),
    timeout_ms: int = 450,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    """使用 Playwright 渲染 HTML 为高清海报 PNG；dry_run 模式下仅预演输出路径。"""
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        if not quiet:
            print(f"DRY {out_path.name}")
        return out_path

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
    if not quiet:
        size_kb = out_path.stat().st_size // 1024 if out_path.exists() else 0
        print(f"OK {out_path.name} ({size_kb} KB)")
    return out_path


render_html = shot


# ---------- 8 大变体 HTML 构建器 ----------

def build_v1_top_title_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
) -> str:
    """V1 顶部标题 — 字在天空，不碰人"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "Night Voyage"))
    safe_slogan = escape(str(slogan if slogan is not None else "她把城市调成静音"))
    inner = f"""
      <div style="position:absolute;left:8%;right:8%;top:8%;text-align:center;color:#F4F0E8">
        <div class="lat" style="opacity:.75;margin-bottom:20px">{safe_latin}</div>
        <div class="ns" style="font-size:110px;letter-spacing:.24em;line-height:1">{safe_title}</div>
      </div>
      <div style="position:absolute;left:0;right:0;bottom:5%;text-align:center">
        <div class="sup" style="color:rgba(244,240,232,.85)">{safe_slogan}</div>
      </div>
    """
    return shell(image, inner, extra=extra_css)


def build_v2_topleft_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
) -> str:
    """V2 左上角字 — 图右侧人物完整"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "Night Voyage"))
    safe_slogan = escape(str(slogan if slogan is not None else "她把城市调成静音"))
    inner = f"""
      <div style="position:absolute;left:7%;top:10%;width:38%;color:#F4F0E8">
        <div class="lat" style="opacity:.8;margin-bottom:18px">{safe_latin}</div>
        <div class="ns" style="font-size:96px;letter-spacing:.12em;line-height:.95">{safe_title}</div>
        <div class="sup" style="margin-top:18px;color:rgba(244,240,232,.8)">{safe_slogan}</div>
      </div>
    """
    return shell(image, inner, extra=extra_css)


def build_v3_vertical_corner_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    extra_css: str = "",
) -> str:
    """V3 竖排右上 — 字在空场，人完整"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "Night Voyage"))
    inner = f"""
      <div style="position:absolute;right:8%;top:9%;writing-mode:vertical-rl;color:#F4F0E8">
        <div class="ns" style="font-size:88px;letter-spacing:.22em;line-height:1">{safe_title}</div>
      </div>
      <div style="position:absolute;left:7%;top:10%;writing-mode:vertical-rl">
        <div class="lat" style="color:rgba(244,240,232,.75);letter-spacing:.45em">{safe_latin}</div>
      </div>
    """
    return shell(image, inner, extra=extra_css)


def build_v4_bottom_left_min_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    extra_css: str = "",
) -> str:
    """V4 极简角标 — 仅 micro + 小主标"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "Night Voyage"))
    inner = f"""
      <div style="position:absolute;left:7%;bottom:7%;color:#F4F0E8">
        <div class="ns" style="font-size:72px;letter-spacing:.18em">{safe_title}</div>
        <div class="lat" style="margin-top:12px;opacity:.7">{safe_latin}</div>
      </div>
    """
    return shell(image, inner, extra=extra_css)


def build_v5_whisper_html(
    image: str,
    title: str = "夜航",
    tag: str = "2026",
    extra_css: str = "",
) -> str:
    """V5 负空间大留白 — 字更小更少"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_tag = escape(str(tag if tag is not None else "2026"))
    inner = f"""
      <div style="position:absolute;left:10%;top:12%;color:#F4F0E8">
        <div class="lat" style="opacity:.7;margin-bottom:14px">{safe_tag}</div>
        <div class="ns" style="font-size:84px;letter-spacing:.2em">{safe_title}</div>
      </div>
    """
    return shell(image, inner, extra=extra_css)


def build_v6_center_top_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    extra_css: str = "",
) -> str:
    """V6 中轴顶部横排 + 下方短句（人物中下，不加暗角）"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "Night Voyage"))
    inner = f"""
      <div style="position:absolute;left:0;right:0;top:7%;text-align:center;color:#F4F0E8">
        <div class="ph" style="font-size:104px;letter-spacing:.22em;line-height:1;font-weight:900">{safe_title}</div>
        <div class="lat" style="margin-top:16px;opacity:.7">{safe_latin}</div>
      </div>
    """
    return shell(image, inner, extra=extra_css)


def build_v7_diag_minimal_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    extra_css: str = "",
) -> str:
    """V7 对角：左上西文 + 左下小字，中间人全露"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "Night Voyage"))
    inner = f"""
      <div style="position:absolute;left:8%;top:8%;color:#F4F0E8">
        <div class="lat" style="opacity:.8">{safe_latin}</div>
      </div>
      <div style="position:absolute;left:8%;bottom:8%;color:#F4F0E8">
        <div class="ns" style="font-size:64px;letter-spacing:.16em">{safe_title}</div>
      </div>
    """
    return shell(image, inner, extra=extra_css)


def build_v8_vertical_seal_html(
    image: str,
    title: str = "夜航",
    seal_char: str = "航",
    extra_css: str = "",
) -> str:
    """V8 仅竖排书名 + 印章，零渐变"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_seal = escape(str(seal_char if seal_char is not None else (title[-1] if title else "印")))
    inner = f"""
      <div style="position:absolute;right:7%;top:12%;writing-mode:vertical-rl">
        <div class="ns" style="font-size:92px;letter-spacing:.24em;color:#F4F0E8;line-height:1">{safe_title}</div>
      </div>
      <div style="position:absolute;right:7%;bottom:10%;width:42px;height:42px;border:1.5px solid #B4232A;color:#B4232A;display:flex;align-items:center;justify-content:center;font-family:'NSB',serif;font-size:16px">{safe_seal}</div>
    """
    return shell(image, inner, extra=extra_css)


# ---------- 8 大变体独立渲染接口 ----------

def render_v1_top_title(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = b64(image)
    html = build_v1_top_title_html(img, title=title, latin=latin, slogan=slogan, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_v2_topleft(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = b64(image)
    html = build_v2_topleft_html(img, title=title, latin=latin, slogan=slogan, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_v3_vertical_corner(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = b64(image)
    html = build_v3_vertical_corner_html(img, title=title, latin=latin, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_v4_bottom_left_min(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = b64(image)
    html = build_v4_bottom_left_min_html(img, title=title, latin=latin, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_v5_whisper(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    tag: str = "2026",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = b64(image)
    html = build_v5_whisper_html(img, title=title, tag=tag, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_v6_center_top(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = b64(image)
    html = build_v6_center_top_html(img, title=title, latin=latin, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_v7_diag_minimal(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = b64(image)
    html = build_v7_diag_minimal_html(img, title=title, latin=latin, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_v8_vertical_seal(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    seal_char: str = "航",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = b64(image)
    html = build_v8_vertical_seal_html(img, title=title, seal_char=seal_char, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


VARIANTS_REGISTRY = {
    "v1_top_title": {
        "name": "顶部标题 (V1 Top Title)",
        "builder": build_v1_top_title_html,
        "renderer": render_v1_top_title,
        "default_filename": "v1_top_title.png",
        "default_file": "v1_top_title.png",
    },
    "v2_topleft": {
        "name": "左上角字 (V2 Top Left)",
        "builder": build_v2_topleft_html,
        "renderer": render_v2_topleft,
        "default_filename": "v2_topleft.png",
        "default_file": "v2_topleft.png",
    },
    "v3_vertical_corner": {
        "name": "竖排右上 (V3 Vertical Corner)",
        "builder": build_v3_vertical_corner_html,
        "renderer": render_v3_vertical_corner,
        "default_filename": "v3_vertical_corner.png",
        "default_file": "v3_vertical_corner.png",
    },
    "v4_bottom_left_min": {
        "name": "极简角标 (V4 Bottom Left Minimal)",
        "builder": build_v4_bottom_left_min_html,
        "renderer": render_v4_bottom_left_min,
        "default_filename": "v4_bottom_left_min.png",
        "default_file": "v4_bottom_left_min.png",
    },
    "v5_whisper": {
        "name": "负空间大留白 (V5 Whisper)",
        "builder": build_v5_whisper_html,
        "renderer": render_v5_whisper,
        "default_filename": "v5_whisper.png",
        "default_file": "v5_whisper.png",
    },
    "v6_center_top": {
        "name": "中轴顶部横排 (V6 Center Top)",
        "builder": build_v6_center_top_html,
        "renderer": render_v6_center_top,
        "default_filename": "v6_center_top.png",
        "default_file": "v6_center_top.png",
    },
    "v7_diag_minimal": {
        "name": "对角极简 (V7 Diagonal Minimal)",
        "builder": build_v7_diag_minimal_html,
        "renderer": render_v7_diag_minimal,
        "default_filename": "v7_diag_minimal.png",
        "default_file": "v7_diag_minimal.png",
    },
    "v8_vertical_seal": {
        "name": "竖排书名与印章 (V8 Vertical Seal)",
        "builder": build_v8_vertical_seal_html,
        "renderer": render_v8_vertical_seal,
        "default_filename": "v8_vertical_seal.png",
        "default_file": "v8_vertical_seal.png",
    },
}


def normalize_variant_key(key: str) -> str:
    k = key.strip().lower()
    mapping = {
        "1": "v1_top_title", "v1": "v1_top_title", "top_title": "v1_top_title", "v1_top_title": "v1_top_title",
        "2": "v2_topleft", "v2": "v2_topleft", "topleft": "v2_topleft", "v2_topleft": "v2_topleft",
        "3": "v3_vertical_corner", "v3": "v3_vertical_corner", "vertical_corner": "v3_vertical_corner", "v3_vertical_corner": "v3_vertical_corner",
        "4": "v4_bottom_left_min", "v4": "v4_bottom_left_min", "bottom_left_min": "v4_bottom_left_min", "v4_bottom_left_min": "v4_bottom_left_min",
        "5": "v5_whisper", "v5": "v5_whisper", "whisper": "v5_whisper", "v5_whisper": "v5_whisper",
        "6": "v6_center_top", "v6": "v6_center_top", "center_top": "v6_center_top", "v6_center_top": "v6_center_top",
        "7": "v7_diag_minimal", "v7": "v7_diag_minimal", "diag_minimal": "v7_diag_minimal", "v7_diag_minimal": "v7_diag_minimal",
        "8": "v8_vertical_seal", "v8": "v8_vertical_seal", "vertical_seal": "v8_vertical_seal", "v8_vertical_seal": "v8_vertical_seal",
    }
    if k in mapping:
        return mapping[k]
    raise KeyError(f"Unknown variant key: '{key}'. Available: {list(VARIANTS_REGISTRY.keys())}")


def list_variants() -> list[dict[str, str]]:
    """列出所有已注册的版式变体预设"""
    return [
        {"key": k, "name": v["name"], "default_file": v["default_filename"]}
        for k, v in VARIANTS_REGISTRY.items()
    ]


def render_variant_style(
    variant: str,
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    tag: str = "2026",
    seal_char: str | None = None,
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
    quiet: bool = False,
    dry_run: bool = False,
    **kwargs,
) -> Path:
    """按版式变体名称派发渲染对应的海报"""
    norm_key = normalize_variant_key(variant)
    if norm_key == "v1_top_title":
        return render_v1_top_title(image, out, title=title, latin=latin, slogan=slogan, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)
    elif norm_key == "v2_topleft":
        return render_v2_topleft(image, out, title=title, latin=latin, slogan=slogan, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)
    elif norm_key == "v3_vertical_corner":
        return render_v3_vertical_corner(image, out, title=title, latin=latin, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)
    elif norm_key == "v4_bottom_left_min":
        return render_v4_bottom_left_min(image, out, title=title, latin=latin, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)
    elif norm_key == "v5_whisper":
        return render_v5_whisper(image, out, title=title, tag=tag, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)
    elif norm_key == "v6_center_top":
        return render_v6_center_top(image, out, title=title, latin=latin, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)
    elif norm_key == "v7_diag_minimal":
        return render_v7_diag_minimal(image, out, title=title, latin=latin, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)
    elif norm_key == "v8_vertical_seal":
        effective_seal = seal_char if seal_char is not None else (title[-1] if title else "航")
        return render_v8_vertical_seal(image, out, title=title, seal_char=effective_seal, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)
    else:
        func = VARIANTS_REGISTRY[norm_key]["renderer"]
        return func(image, out, title=title, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run, **kwargs)


def render_all_variants(
    image: str | Path,
    out_dir: str | Path | None = None,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
    quiet: bool = False,
    dry_run: bool = False,
) -> dict[str, Path]:
    """批量渲染全部 8 款版式变体并返回输出文件路径映射字典。"""
    dest = Path(out_dir) if out_dir else (ROOT / "outputs" / "verify_batch")
    dest.mkdir(parents=True, exist_ok=True)
    res: dict[str, Path] = {}

    res["v1_top_title"] = render_v1_top_title(
        image, dest / "v1_top_title.png", title=title, latin=latin, slogan=slogan, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    res["v2_topleft"] = render_v2_topleft(
        image, dest / "v2_topleft.png", title=title, latin=latin, slogan=slogan, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    res["v3_vertical_corner"] = render_v3_vertical_corner(
        image, dest / "v3_vertical_corner.png", title=title, latin=latin, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    res["v4_bottom_left_min"] = render_v4_bottom_left_min(
        image, dest / "v4_bottom_left_min.png", title=title, latin=latin, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    res["v5_whisper"] = render_v5_whisper(
        image, dest / "v5_whisper.png", title=title, tag="2026", extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    res["v6_center_top"] = render_v6_center_top(
        image, dest / "v6_center_top.png", title=title, latin=latin, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    res["v7_diag_minimal"] = render_v7_diag_minimal(
        image, dest / "v7_diag_minimal.png", title=title, latin=latin, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    seal_c = title[-1] if title else "航"
    res["v8_vertical_seal"] = render_v8_vertical_seal(
        image, dest / "v8_vertical_seal.png", title=title, seal_char=seal_c, extra_css=extra_css, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    return res


def build_arg_parser() -> argparse.ArgumentParser:
    """构建全量版式变体渲染引擎 CLI 参数解析器。"""
    parser = argparse.ArgumentParser(
        description="Agnes Studio · 全量版式变体渲染引擎 (Variants Verify Renderer)"
    )
    parser.add_argument(
        "--variant",
        "--style",
        "-v",
        "-s",
        default="all",
        help="指定渲染变体 (1-8, v1-v8, v1_top_title 等或 all, 默认: all)",
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
        help="输出海报路径（在 variant=all 时将自动附加变体后缀）",
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
        help="西文标题 (默认: Night Voyage)",
    )
    parser.add_argument(
        "--slogan",
        default="她把城市调成静音",
        help="副标语 (默认: 她把城市调成静音)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用的版式变体预设清单",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出结果 (版式清单或批处理报告)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="演练模式，验证流程而不实际光栅化生成海报",
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
    """全量版式变体渲染引擎规范化 CLI 入口。"""
    parser = build_arg_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    suppress_log = args.quiet or args.json

    try:
        if args.list:
            variants = list_variants()
            if args.json:
                print(json.dumps(variants, ensure_ascii=False, indent=2))
            elif not args.quiet:
                print("Agnes Studio 可用版式变体预设清单:")
                for s in variants:
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

        var_arg = (args.variant or "all").strip().lower()
        if var_arg == "all":
            target_keys = list(VARIANTS_REGISTRY.keys())
        else:
            try:
                target_keys = [normalize_variant_key(var_arg)]
            except KeyError as e:
                err_msg = str(e)
                if args.json:
                    print(json.dumps({"error": err_msg, "ok": False}, ensure_ascii=False))
                elif not args.quiet:
                    print(f"❌ {err_msg}", file=sys.stderr)
                return 1 if (args.strict or args.input) else 0

        quiet = suppress_log
        report_items = []
        default_out_dir = Path(args.out_dir) if args.out_dir else (ROOT / "outputs" / "verify_batch")
        for k in target_keys:
            if args.out:
                out_path = Path(args.out)
                if var_arg == "all":
                    out_path = out_path.with_name(f"{out_path.stem}_{k}{out_path.suffix or '.png'}")
            else:
                default_out_dir.mkdir(parents=True, exist_ok=True)
                out_path = default_out_dir / VARIANTS_REGISTRY[k]["default_filename"]

            render_variant_style(
                variant=k,
                image=resolved_src,
                out=out_path,
                title=args.title,
                latin=args.latin,
                slogan=args.slogan,
                quiet=quiet,
                dry_run=args.dry_run,
            )
            report_items.append({
                "variant": k,
                "name": VARIANTS_REGISTRY[k]["name"],
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
            print(f"❌ 版式变体海报渲染失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
