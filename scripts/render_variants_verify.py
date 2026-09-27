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


def shot(html: str, out: str | Path, size=(864, 1152), timeout_ms: int = 450) -> Path:
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
        b = p.chromium.launch(**kw)
        page = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
        page.set_content(html)
        if timeout_ms > 0:
            page.wait_for_timeout(timeout_ms)
        page.screenshot(path=str(out_path), type="png")
        b.close()
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
) -> Path:
    img = b64(image)
    html = build_v1_top_title_html(img, title=title, latin=latin, slogan=slogan, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms)


def render_v2_topleft(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
) -> Path:
    img = b64(image)
    html = build_v2_topleft_html(img, title=title, latin=latin, slogan=slogan, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms)


def render_v3_vertical_corner(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
) -> Path:
    img = b64(image)
    html = build_v3_vertical_corner_html(img, title=title, latin=latin, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms)


def render_v4_bottom_left_min(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
) -> Path:
    img = b64(image)
    html = build_v4_bottom_left_min_html(img, title=title, latin=latin, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms)


def render_v5_whisper(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    tag: str = "2026",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
) -> Path:
    img = b64(image)
    html = build_v5_whisper_html(img, title=title, tag=tag, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms)


def render_v6_center_top(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
) -> Path:
    img = b64(image)
    html = build_v6_center_top_html(img, title=title, latin=latin, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms)


def render_v7_diag_minimal(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
) -> Path:
    img = b64(image)
    html = build_v7_diag_minimal_html(img, title=title, latin=latin, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms)


def render_v8_vertical_seal(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    seal_char: str = "航",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
) -> Path:
    img = b64(image)
    html = build_v8_vertical_seal_html(img, title=title, seal_char=seal_char, extra_css=extra_css)
    return shot(html, out, size=size, timeout_ms=timeout_ms)


VARIANTS_REGISTRY = {
    "v1_top_title": {
        "builder": build_v1_top_title_html,
        "renderer": render_v1_top_title,
        "default_filename": "v1_top_title.png",
    },
    "v2_topleft": {
        "builder": build_v2_topleft_html,
        "renderer": render_v2_topleft,
        "default_filename": "v2_topleft.png",
    },
    "v3_vertical_corner": {
        "builder": build_v3_vertical_corner_html,
        "renderer": render_v3_vertical_corner,
        "default_filename": "v3_vertical_corner.png",
    },
    "v4_bottom_left_min": {
        "builder": build_v4_bottom_left_min_html,
        "renderer": render_v4_bottom_left_min,
        "default_filename": "v4_bottom_left_min.png",
    },
    "v5_whisper": {
        "builder": build_v5_whisper_html,
        "renderer": render_v5_whisper,
        "default_filename": "v5_whisper.png",
    },
    "v6_center_top": {
        "builder": build_v6_center_top_html,
        "renderer": render_v6_center_top,
        "default_filename": "v6_center_top.png",
    },
    "v7_diag_minimal": {
        "builder": build_v7_diag_minimal_html,
        "renderer": render_v7_diag_minimal,
        "default_filename": "v7_diag_minimal.png",
    },
    "v8_vertical_seal": {
        "builder": build_v8_vertical_seal_html,
        "renderer": render_v8_vertical_seal,
        "default_filename": "v8_vertical_seal.png",
    },
}


def render_all_variants(
    image: str | Path,
    out_dir: str | Path | None = None,
    title: str = "夜航",
    latin: str = "Night Voyage",
    slogan: str = "她把城市调成静音",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 450,
) -> dict[str, Path]:
    """批量渲染全部 8 款版式变体并返回输出文件路径映射字典。"""
    dest = Path(out_dir) if out_dir else (ROOT / "outputs" / "verify_batch")
    dest.mkdir(parents=True, exist_ok=True)
    res: dict[str, Path] = {}

    res["v1_top_title"] = render_v1_top_title(
        image, dest / "v1_top_title.png", title=title, latin=latin, slogan=slogan, extra_css=extra_css, size=size, timeout_ms=timeout_ms
    )
    res["v2_topleft"] = render_v2_topleft(
        image, dest / "v2_topleft.png", title=title, latin=latin, slogan=slogan, extra_css=extra_css, size=size, timeout_ms=timeout_ms
    )
    res["v3_vertical_corner"] = render_v3_vertical_corner(
        image, dest / "v3_vertical_corner.png", title=title, latin=latin, extra_css=extra_css, size=size, timeout_ms=timeout_ms
    )
    res["v4_bottom_left_min"] = render_v4_bottom_left_min(
        image, dest / "v4_bottom_left_min.png", title=title, latin=latin, extra_css=extra_css, size=size, timeout_ms=timeout_ms
    )
    res["v5_whisper"] = render_v5_whisper(
        image, dest / "v5_whisper.png", title=title, tag="2026", extra_css=extra_css, size=size, timeout_ms=timeout_ms
    )
    res["v6_center_top"] = render_v6_center_top(
        image, dest / "v6_center_top.png", title=title, latin=latin, extra_css=extra_css, size=size, timeout_ms=timeout_ms
    )
    res["v7_diag_minimal"] = render_v7_diag_minimal(
        image, dest / "v7_diag_minimal.png", title=title, latin=latin, extra_css=extra_css, size=size, timeout_ms=timeout_ms
    )
    seal_c = title[-1] if title else "航"
    res["v8_vertical_seal"] = render_v8_vertical_seal(
        image, dest / "v8_vertical_seal.png", title=title, seal_char=seal_c, extra_css=extra_css, size=size, timeout_ms=timeout_ms
    )
    return res


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="全量版式变体渲染器")
    parser.add_argument("--input", "-i", type=str, default=None, help="底图路径")
    parser.add_argument("--out-dir", "-o", type=str, default=None, help="输出目录")
    parser.add_argument("--title", type=str, default="夜航", help="主标题")
    parser.add_argument("--latin", type=str, default="Night Voyage", help="西文标题")
    parser.add_argument("--slogan", type=str, default="她把城市调成静音", help="副标语")
    parser.add_argument("--variant", "-v", type=str, default="all", help="指定渲染变体 (1-8, v1-v8 或 all)")
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

    out_dir = Path(args.out_dir) if args.out_dir else (ROOT / "outputs" / "verify_batch")
    out_dir.mkdir(parents=True, exist_ok=True)

    variant = args.variant.lower().strip()
    if variant in ("all", "1", "v1"):
        render_v1_top_title(base, out_dir / "v1_top_title.png", title=args.title, latin=args.latin, slogan=args.slogan)
    if variant in ("all", "2", "v2"):
        render_v2_topleft(base, out_dir / "v2_topleft.png", title=args.title, latin=args.latin, slogan=args.slogan)
    if variant in ("all", "3", "v3"):
        render_v3_vertical_corner(base, out_dir / "v3_vertical_corner.png", title=args.title, latin=args.latin)
    if variant in ("all", "4", "v4"):
        render_v4_bottom_left_min(base, out_dir / "v4_bottom_left_min.png", title=args.title, latin=args.latin)
    if variant in ("all", "5", "v5"):
        render_v5_whisper(base, out_dir / "v5_whisper.png", title=args.title)
    if variant in ("all", "6", "v6"):
        render_v6_center_top(base, out_dir / "v6_center_top.png", title=args.title, latin=args.latin)
    if variant in ("all", "7", "v7"):
        render_v7_diag_minimal(base, out_dir / "v7_diag_minimal.png", title=args.title, latin=args.latin)
    if variant in ("all", "8", "v8"):
        seal_c = args.title[-1] if args.title else "航"
        render_v8_vertical_seal(base, out_dir / "v8_vertical_seal.png", title=args.title, seal_char=seal_c)

    print("done", out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
