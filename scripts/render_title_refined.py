#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高级中文海报标题字设（Refined Title Typography）——精工而非特效。

参照华语电影海报标题：端正、极简、字距/比例/材质说话。
涵盖 5 大经典院线级字设范式：
1. R1 东方院线居中 (r1_oriental_center): 大宋体居中偏下，西文极细，朱印，微暗角
2. R2 黑宋大标偏左 (r2_left_big): 黑宋大标靠左，极简西文，极度克制
3. R3 竖排书脊标题 (r3_vertical_spine): 竖排书脊标题，底部横向英文，画册扉页质感
4. R4 负空间天幕 (r4_sky_field): 嵌入天空负空间，黄金分割留白
5. R5 院线主从排布 (r5_film_bottom): 顶部独立西文，底部厚重中文主标与副标
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


def get_base_css(
    serif_path: str | None = None,
    bold_serif_path: str | None = None,
    medium_path: str | None = None,
    heavy_path: str | None = None,
) -> str:
    """跨平台解析字体路径并生成基础 CSS 定义。"""
    nsb = resolve_font_path(serif_path or "serif")
    nsbold = resolve_font_path(bold_serif_path or "serif")
    phm = resolve_font_path(medium_path or "wenkai")
    phh = resolve_font_path(heavy_path or "sans")

    return f"""
@font-face{{font-family:'NSB';src:url('file://{nsb}') format('opentype'), url('file://{nsb}') format('truetype');}}
@font-face{{font-family:'NSBO';src:url('file://{nsbold}') format('opentype'), url('file://{nsbold}') format('truetype');}}
@font-face{{font-family:'PHM';src:url('file://{phm}') format('truetype'), url('file://{phm}') format('opentype');}}
@font-face{{font-family:'PHH';src:url('file://{phh}') format('truetype'), url('file://{phh}') format('opentype');}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:864px;height:1152px;overflow:hidden;background:#0a0a0c}}
.s{{position:relative;width:864px;height:1152px;overflow:hidden}}
.bg{{width:100%;height:100%;object-fit:cover}}
.latin{{font-family:Didot,Baskerville,serif;letter-spacing:.48em;text-transform:uppercase}}
.sup{{font-family:'PHM','PingFang SC',sans-serif;letter-spacing:.36em}}
"""


# ---------- 5 大经典范式 HTML 构建器 ----------

def build_r1_oriental_center_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    seal_text: str = "航",
    extra_css: str = "",
) -> str:
    """R1 东方院线海报：大宋体居中偏下，西文极细，朱印标定。"""
    safe_img = sanitize_img_uri(image)
    safe_title = escape(title or "夜航")
    safe_latin = escape(latin or "Night Voyage")
    safe_slogan = escape(slogan or "她把城市调成静音")
    safe_seal = escape(seal_text or (title[-1] if title else "印"))
    base_css = get_base_css()

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css}
      .v{{position:absolute;inset:0;
        background: radial-gradient(ellipse at 50% 70%, rgba(0,0,0,.18), transparent 55%);
      }}
      .block{{position:absolute;left:0;right:0;top:58%;text-align:center;color:#F2EDE4}}
      .t1{{
        font-family:'NSB',serif;
        font-size:128px;letter-spacing:.22em;line-height:1;
        padding-left:.22em;
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
      {extra_css}
    </style></head><body><div class="s">
      <img class="bg" src="{safe_img}">
      <div class="v"></div>
      <div class="block">
        <div class="t1">{safe_title}</div>
        <div class="latin">{safe_latin}</div>
        <div class="rule"></div>
        <div class="sup">{safe_slogan}</div>
      </div>
      <div class="seal">{safe_seal}</div>
    </div></body></html>"""


def build_r2_left_big_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
) -> str:
    """R2 黑宋大标靠左：极简西文小号，无冗余装饰。"""
    safe_img = sanitize_img_uri(image)
    safe_title = escape(title or "夜航")
    safe_latin = escape(latin or "Night Voyage")
    safe_slogan = escape(slogan or "她把城市调成静音")
    base_css = get_base_css()

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css}
      .wrap{{position:absolute;left:9%;top:22%;color:#F2EDE4}}
      .t1{{
        font-family:'NSB',serif;
        font-size:156px;letter-spacing:.14em;line-height:.95;
        font-weight:900;
      }}
      .latin{{font-size:12px;opacity:.7;margin-top:32px}}
      .sup{{font-size:15px;opacity:.85;margin-top:18px}}
      {extra_css}
    </style></head><body><div class="s">
      <img class="bg" src="{safe_img}">
      <div class="wrap">
        <div class="t1">{safe_title}</div>
        <div class="latin">{safe_latin}</div>
        <div class="sup">{safe_slogan}</div>
      </div>
    </div></body></html>"""


def build_r3_vertical_spine_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage · Agnes",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
) -> str:
    """R3 竖排书脊标题 + 底部横向英文，画册扉页质感。"""
    safe_img = sanitize_img_uri(image)
    safe_title = escape(title or "夜航")
    safe_latin = escape(latin or "Night Voyage · Agnes")
    safe_slogan = escape(slogan or "她把城市调成静音")
    base_css = get_base_css()

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css}
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
      {extra_css}
    </style></head><body><div class="s">
      <img class="bg" src="{safe_img}">
      <div class="vtitle">{safe_title}</div>
      <div class="sup">{safe_slogan}</div>
      <div class="latin">{safe_latin}</div>
    </div></body></html>"""


def build_r4_sky_field_html(
    image: str,
    title: str = "夜 航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
) -> str:
    """R4 负空间天幕：标题嵌入天空负空间，黄金分割留白。"""
    safe_img = sanitize_img_uri(image)
    safe_title = escape(title or "夜 航")
    safe_latin = escape(latin or "Night Voyage")
    safe_slogan = escape(slogan or "她把城市调成静音")
    base_css = get_base_css()

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css}
      .wrap{{position:absolute;left:12%;top:18%;width:58%;color:#F2EDE4}}
      .t1{{
        font-family:'NSBO','NSB',serif;
        font-size:112px;letter-spacing:.18em;line-height:1.05;
        font-weight:900;
      }}
      .latin{{font-size:12px;opacity:.72;margin-top:26px;letter-spacing:.55em}}
      .sup{{font-size:14px;opacity:.8;margin-top:14px}}
      {extra_css}
    </style></head><body><div class="s">
      <img class="bg" src="{safe_img}">
      <div class="wrap">
        <div class="t1">{safe_title}</div>
        <div class="latin">{safe_latin}</div>
        <div class="sup">{safe_slogan}</div>
      </div>
    </div></body></html>"""


def build_r5_film_bottom_html(
    image: str,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
) -> str:
    """R5 院线主从排布：顶部独立西文，底部厚重中文主标与副标。"""
    safe_img = sanitize_img_uri(image)
    safe_title = escape(title or "夜航")
    safe_latin = escape(latin or "Night Voyage")
    safe_slogan = escape(slogan or "她把城市调成静音")
    base_css = get_base_css()

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{base_css}
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
      {extra_css}
    </style></head><body><div class="s">
      <img class="bg" src="{safe_img}">
      <div class="top"><div class="latin">{safe_latin}</div></div>
      <div class="bot">
        <div class="t1">{safe_title}</div>
        <div class="sup">{safe_slogan}</div>
      </div>
    </div></body></html>"""


# ---------- 渲染与对外输出接口 ----------

def render_html(
    html: str,
    out: str | Path,
    size=(864, 1152),
    timeout_ms: int = 550,
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
    timeout_ms: int = 550,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    """向下兼容别名，调用 render_html。"""
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_r1_oriental_center(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    seal_text: str = "航",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 550,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = sanitize_img_uri(b64(image))
    html = build_r1_oriental_center_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        seal_text=seal_text,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_r2_left_big(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 550,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = sanitize_img_uri(b64(image))
    html = build_r2_left_big_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_r3_vertical_spine(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage · Agnes",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 550,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = sanitize_img_uri(b64(image))
    html = build_r3_vertical_spine_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_r4_sky_field(
    image: str | Path,
    out: str | Path,
    title: str = "夜 航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 550,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = sanitize_img_uri(b64(image))
    html = build_r4_sky_field_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def render_r5_film_bottom(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 550,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    img = sanitize_img_uri(b64(image))
    html = build_r5_film_bottom_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


# =============================================================================
# 风格注册表与多风格派发器
# =============================================================================

REFINED_TITLE_STYLES = {
    "r1_oriental_center": {
        "name": "东方院线居中 (Oriental Center)",
        "func": render_r1_oriental_center,
        "default_file": "r1_oriental_center.png",
        "default_latin": "Night Voyage",
        "default_slogan": "她把城市调成静音",
        "description": "大宋体居中偏下，西文极细，朱印，微暗角",
    },
    "r2_left_big": {
        "name": "黑宋大标偏左 (Left Big Black Serif)",
        "func": render_r2_left_big,
        "default_file": "r2_left_big.png",
        "default_latin": "Night Voyage",
        "default_slogan": "她把城市调成静音",
        "description": "黑宋大标靠左，极简西文，极度克制",
    },
    "r3_vertical_spine": {
        "name": "竖排书脊标题 (Vertical Spine Book)",
        "func": render_r3_vertical_spine,
        "default_file": "r3_vertical_spine.png",
        "default_latin": "Night Voyage · Agnes",
        "default_slogan": "她把城市调成静音",
        "description": "竖排书脊标题，底部横向英文，画册扉页质感",
    },
    "r4_sky_field": {
        "name": "负空间天幕 (Sky Field Negative Space)",
        "func": render_r4_sky_field,
        "default_file": "r4_sky_field.png",
        "default_latin": "Night Voyage",
        "default_slogan": "她把城市调成静音",
        "description": "嵌入天空负空间，黄金分割留白",
    },
    "r5_film_bottom": {
        "name": "院线主从排布 (Film Bottom Hierarchy)",
        "func": render_r5_film_bottom,
        "default_file": "r5_film_bottom.png",
        "default_latin": "Night Voyage",
        "default_slogan": "她把城市调成静音",
        "description": "顶部独立西文，底部厚重中文主标与副标",
    },
}

REFINED_TITLE_REGISTRY = {k: v["func"] for k, v in REFINED_TITLE_STYLES.items()}


def normalize_refined_style_key(style: str) -> str:
    """标准化高级字设范式键名，支持别名与数字缩写。"""
    raw = str(style or "").strip().lower()
    mapping = {
        "1": "r1_oriental_center",
        "r1": "r1_oriental_center",
        "r1_oriental_center": "r1_oriental_center",
        "oriental_center": "r1_oriental_center",
        "oriental": "r1_oriental_center",
        "2": "r2_left_big",
        "r2": "r2_left_big",
        "r2_left_big": "r2_left_big",
        "left_big": "r2_left_big",
        "3": "r3_vertical_spine",
        "r3": "r3_vertical_spine",
        "r3_vertical_spine": "r3_vertical_spine",
        "vertical_spine": "r3_vertical_spine",
        "spine": "r3_vertical_spine",
        "4": "r4_sky_field",
        "r4": "r4_sky_field",
        "r4_sky_field": "r4_sky_field",
        "sky_field": "r4_sky_field",
        "sky": "r4_sky_field",
        "5": "r5_film_bottom",
        "r5": "r5_film_bottom",
        "r5_film_bottom": "r5_film_bottom",
        "film_bottom": "r5_film_bottom",
    }
    if raw in mapping:
        return mapping[raw]
    if raw in REFINED_TITLE_STYLES:
        return raw
    raise KeyError(f"Unknown refined title style: '{style}'. Available: {list(REFINED_TITLE_STYLES.keys())}")


def list_refined_title_styles() -> list[dict[str, str]]:
    """列出所有已注册的高级中文海报标题字设范式预设。"""
    return [
        {
            "key": k,
            "name": v["name"],
            "default_file": v["default_file"],
            "description": v.get("description", ""),
        }
        for k, v in REFINED_TITLE_STYLES.items()
    ]


def render_refined_title_style(
    style: str,
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str | None = None,
    slogan: str | None = None,
    seal_text: str = "航",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 550,
    quiet: bool = False,
    dry_run: bool = False,
    **kwargs,
) -> Path:
    """按高级字设范式名称派发渲染对应的海报。"""
    norm_key = normalize_refined_style_key(style)
    meta = REFINED_TITLE_STYLES[norm_key]
    func = meta["func"]
    eff_latin = latin if latin is not None else meta["default_latin"]
    eff_slogan = slogan if slogan is not None else meta["default_slogan"]

    if norm_key == "r1_oriental_center":
        return func(
            image=image,
            out=out,
            title=title,
            latin=eff_latin,
            slogan=eff_slogan,
            seal_text=seal_text,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
            dry_run=dry_run,
        )
    elif norm_key == "r4_sky_field":
        t = title
        if t == "夜航":
            t = "夜 航"
        return func(
            image=image,
            out=out,
            title=t,
            latin=eff_latin,
            slogan=eff_slogan,
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
            latin=eff_latin,
            slogan=eff_slogan,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
            dry_run=dry_run,
        )


def render_refined_variant(
    variant: str,
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    seal_text: str = "航",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 550,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    """根据变体名称渲染指定的精致字设海报（向后兼容）。"""
    raw_key = str(variant or "").strip().lower()
    try:
        norm_key = normalize_refined_style_key(raw_key)
    except KeyError:
        raise ValueError(f"Unknown refined title variant '{variant}'. Available: {list(REFINED_TITLE_REGISTRY.keys())}")

    return render_refined_title_style(
        style=norm_key,
        image=image,
        out=out,
        title=title,
        latin=latin,
        slogan=slogan,
        seal_text=seal_text,
        extra_css=extra_css,
        size=size,
        timeout_ms=timeout_ms,
        quiet=quiet,
        dry_run=dry_run,
    )


def render_all_refined_titles(
    image: str | Path,
    out_dir: str | Path | None = None,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    seal_text: str = "航",
    timeout_ms: int = 550,
    quiet: bool = False,
    dry_run: bool = False,
) -> dict[str, Path]:
    """批量渲染所有 5 大高级字设范式海报。"""
    target_dir = Path(out_dir) if out_dir else (ROOT / "outputs" / "title_refined")
    target_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    results["r1_oriental_center"] = render_r1_oriental_center(
        image, target_dir / "r1_oriental_center.png", title=title, latin=latin, slogan=slogan, seal_text=seal_text, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    results["r2_left_big"] = render_r2_left_big(
        image, target_dir / "r2_left_big.png", title=title, latin=latin, slogan=slogan, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    results["r3_vertical_spine"] = render_r3_vertical_spine(
        image, target_dir / "r3_vertical_spine.png", title=title, latin=f"{latin} · Agnes", slogan=slogan, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    results["r4_sky_field"] = render_r4_sky_field(
        image, target_dir / "r4_sky_field.png", title=f"{title[0]} {title[1:]}" if len(title) > 1 else title, latin=latin, slogan=slogan, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    results["r5_film_bottom"] = render_r5_film_bottom(
        image, target_dir / "r5_film_bottom.png", title=title, latin=latin, slogan=slogan, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run
    )
    return results


def build_arg_parser() -> argparse.ArgumentParser:
    """构建高级中文海报标题字设渲染命令行参数解析器"""
    parser = argparse.ArgumentParser(description="高级中文海报标题字设（Refined Title Typography）渲染引擎")
    parser.add_argument(
        "--variant",
        "--style",
        "-v",
        "-s",
        dest="style",
        type=str,
        default="all",
        help="指定字设范式（r1-r5 或 all，默认: all）",
    )
    parser.add_argument(
        "--src",
        "--image",
        type=str,
        default=None,
        help="输入底图路径",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=None,
        help="向下兼容底图输入路径",
    )
    parser.add_argument(
        "--out",
        "-o",
        type=str,
        default=None,
        help="输出海报路径（单风格或 all 附加后缀）",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="输出目录（未指定 --out 时默认保存至该目录）",
    )
    parser.add_argument(
        "--title",
        "-t",
        type=str,
        default="夜航",
        help="主标题 (默认: 夜航)",
    )
    parser.add_argument(
        "--latin",
        "-l",
        type=str,
        default=None,
        help="西文大标 (默认根据各版式预设提供)",
    )
    parser.add_argument(
        "--slogan",
        type=str,
        default="她把城市调成静音",
        help="文案副标 (默认: 她把城市调成静音)",
    )
    parser.add_argument(
        "--seal",
        type=str,
        default="航",
        help="印章字符 (默认: 航)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用的高级字设范式预设",
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
    """高级中文海报标题字设渲染引擎规范化 CLI 入口。"""
    parser = build_arg_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    suppress_log = args.quiet or args.json

    try:
        if args.list:
            if args.json:
                print(json.dumps(list_refined_title_styles(), ensure_ascii=False, indent=2))
            elif not args.quiet:
                print("Agnes Studio 可用高级字设范式预设:")
                for s in list_refined_title_styles():
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

        raw_style = (args.style or "all").strip().lower()
        if raw_style == "all":
            target_styles = list(REFINED_TITLE_STYLES.keys())
        else:
            try:
                target_styles = [normalize_refined_style_key(raw_style)]
            except KeyError as e:
                err_msg = str(e)
                if args.json:
                    print(json.dumps({"error": err_msg, "ok": False}, ensure_ascii=False))
                elif not args.quiet:
                    print(f"❌ {err_msg}", file=sys.stderr)
                return 1 if (args.strict or args.input) else 0

        quiet = suppress_log
        report_items = []
        default_out_dir = Path(args.out_dir) if args.out_dir else (ROOT / "outputs" / "title_refined")
        for st in target_styles:
            if args.out:
                out_path = Path(args.out)
                if raw_style == "all":
                    out_path = out_path.with_name(f"{out_path.stem}_{st}{out_path.suffix or '.png'}")
            else:
                default_out_dir.mkdir(parents=True, exist_ok=True)
                out_path = default_out_dir / REFINED_TITLE_STYLES[st]["default_file"]

            render_refined_title_style(
                style=st,
                image=resolved_src,
                out=out_path,
                title=args.title,
                latin=args.latin,
                slogan=args.slogan,
                seal_text=args.seal,
                quiet=quiet,
                dry_run=args.dry_run,
            )
            report_items.append({
                "style": st,
                "name": REFINED_TITLE_STYLES[st]["name"],
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
            print(f"❌ 高级字设海报渲染失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
