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


def shot(html: str, out: str | Path, size=(864, 1152), timeout_ms: int = 500, quiet: bool = False) -> Path:
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
    if not quiet:
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
    quiet: bool = False,
) -> Path:
    """经典电影海报：巨标压底，西文其上，几乎无装饰。"""
    img = b64(image)
    html = build_film_bottom_html(img, title=title, latin=latin, tagline=tagline)
    return shot(html, out, quiet=quiet)


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
    quiet: bool = False,
) -> Path:
    """上标下图：字在天空/空场，主体完整。"""
    img = b64(image)
    html = build_film_top_html(img, title=title, latin=latin, tagline=tagline)
    return shot(html, out, quiet=quiet)


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
    quiet: bool = False,
) -> Path:
    """极简左轴：竖排大标 + 一条细线，其余全给图。"""
    img = b64(image)
    html = build_side_rail_html(img, title=title, latin=latin, tagline=tagline)
    return shot(html, out, quiet=quiet)


# =============================================================================
# 风格注册表与多风格派发器
# =============================================================================

CINEMA_POSTER_STYLES = {
    "bottom": {
        "name": "经典巨标压底 (Classic Film Bottom)",
        "func": film_bottom,
        "default_file": "cine_01_bottom.png",
        "default_tagline": "A FILM STILL · AGNES",
    },
    "top": {
        "name": "上标空场构图 (Film Top)",
        "func": film_top,
        "default_file": "cine_02_top.png",
        "default_tagline": "她把城市调成静音",
    },
    "rail": {
        "name": "极简左轴竖排 (Minimal Side Rail)",
        "func": side_rail,
        "default_file": "cine_03_rail.png",
        "default_tagline": "她把城市调成静音",
    },
}


def list_cinema_poster_styles() -> list[dict[str, str]]:
    """列出所有已注册的电影级极简海报版式"""
    return [
        {"key": k, "name": v["name"], "default_file": v["default_file"]}
        for k, v in CINEMA_POSTER_STYLES.items()
    ]


def render_cinema_poster_style(
    style: str,
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "Night Voyage",
    tagline: str | None = None,
    quiet: bool = False,
) -> Path:
    """按风格名称派发渲染电影级海报"""
    key = style.strip().lower()
    if key not in CINEMA_POSTER_STYLES:
        raise KeyError(f"Unknown cinema poster style: '{style}'. Available: {list(CINEMA_POSTER_STYLES.keys())}")
    style_meta = CINEMA_POSTER_STYLES[key]
    func = style_meta["func"]
    effective_tagline = tagline if tagline is not None else style_meta["default_tagline"]
    return func(
        image=image,
        out=out,
        title=title,
        latin=latin,
        tagline=effective_tagline,
        quiet=quiet,
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Agnes Studio · 电影级极简海报渲染引擎 (Cinema Poster Renderer)")
    parser.add_argument(
        "--style",
        "-s",
        default="all",
        choices=["bottom", "top", "rail", "all"],
        help="海报版式风格: bottom | top | rail | all (默认: all)",
    )
    parser.add_argument(
        "--src",
        "--image",
        "-i",
        default=None,
        help="输入背景底图路径（未指定时探查默认底图）",
    )
    parser.add_argument(
        "--out",
        "-o",
        default=None,
        help="输出海报路径（在 style=all 时将自动附加风格后缀）",
    )
    parser.add_argument(
        "--title",
        "-t",
        default="夜航",
        help="海报中文主标题 (默认: 夜航)",
    )
    parser.add_argument(
        "--latin",
        "-l",
        default="Night Voyage",
        help="海报西文副标题 (默认: Night Voyage)",
    )
    parser.add_argument(
        "--tagline",
        default=None,
        help="海报底部/侧边标语 (默认根据风格预设自动提供)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用的电影级海报风格预设",
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
    args = parser.parse_args(argv if argv is not None else [])

    if args.list:
        if not args.quiet:
            print("Agnes Studio 可用电影级海报风格预设:")
            for s in list_cinema_poster_styles():
                print(f"  - [{s['key']}] {s['name']} -> {s['default_file']}")
        return 0

    # 确定输入源
    resolved_src = None
    if args.src:
        p = Path(args.src)
        if not p.is_file():
            if not args.quiet:
                print(f"❌ 找不到输入底图: {args.src}", file=sys.stderr)
            return 1 if args.strict else 0
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
            print("❌ 未指定 --src 且未发现默认候选底图资产", file=sys.stderr)
        return 1 if args.strict else 0

    target_styles = list(CINEMA_POSTER_STYLES.keys()) if args.style == "all" else [args.style]

    try:
        default_out_dir = ROOT / "outputs" / "cinema_study"
        for st in target_styles:
            if args.out:
                out_path = Path(args.out)
                if args.style == "all":
                    out_path = out_path.with_name(f"{out_path.stem}_{st}{out_path.suffix or '.png'}")
            else:
                default_out_dir.mkdir(parents=True, exist_ok=True)
                out_path = default_out_dir / CINEMA_POSTER_STYLES[st]["default_file"]

            render_cinema_poster_style(
                style=st,
                image=resolved_src,
                out=out_path,
                title=args.title,
                latin=args.latin,
                tagline=args.tagline,
                quiet=args.quiet,
            )
        if not args.quiet:
            print("done")
        return 0
    except Exception as e:
        if not args.quiet:
            print(f"❌ 电影级海报渲染失败: {e}", file=sys.stderr)
        return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
