#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纪念碑式高级字排：思源宋/黑 Black + 阿里普惠 Heavy + 真西文。

字当建筑，不只当标签。
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


def render_html(
    html: str,
    out: str | Path,
    size=(864, 1152),
    timeout_ms: int = 600,
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


# ---------- 三套「大气」构图 HTML 构建器 ----------

def build_monument_html(
    image: str,
    title: str = "夜航",
    latin: str = "NIGHT VOYAGE",
    sub: str = "一部还没写完的电影",
    year: str = "2026",
    meta: str = "Agnes Studio · Monument",
    extra_css: str = "",
) -> str:
    """构建【电影纪念碑】海报 HTML。"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "NIGHT VOYAGE"))
    safe_sub = escape(str(sub if sub is not None else "一部还没写完的电影"))
    safe_year = escape(str(year if year is not None else "2026"))
    safe_meta = escape(str(meta if meta is not None else "Agnes Studio · Monument"))

    ns_font = resolve_font_path("serif")
    pb_font = resolve_font_path("sans")

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      @font-face{{font-family:'NS';src:url('file://{ns_font}') format('opentype'), url('file://{ns_font}') format('truetype');}}
      @font-face{{font-family:'PB';src:url('file://{pb_font}') format('truetype'), url('file://{pb_font}') format('opentype');}}
      *{{margin:0;padding:0;box-sizing:border-box}}
      body{{width:864px;height:1152px;overflow:hidden;background:#0B0B0E}}
      .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
      .bg{{width:100%;height:100%;object-fit:cover;filter:contrast(1.1) saturate(.88)}}
      .veil{{position:absolute;inset:0;background:
        linear-gradient(180deg,rgba(11,11,14,.55) 0%,rgba(11,11,14,.05) 38%,rgba(11,11,14,.15) 62%,rgba(11,11,14,.72) 100%)}}
      .latin{{
        position:absolute;left:8%;top:7%;
        font-family:Didot,Bodoni 72,Baskerville,serif;
        font-size:15px;letter-spacing:.55em;color:rgba(244,240,232,.85);
        text-transform:uppercase;font-weight:400;
      }}
      .title{{
        position:absolute;left:7%;right:7%;top:12%;
        font-family:'NS','Songti SC',serif;
        font-size:148px;line-height:.92;font-weight:900;
        letter-spacing:.06em;color:#F4F0E8;
        text-shadow:0 8px 40px rgba(0,0,0,.25);
      }}
      .bar{{position:absolute;left:8%;bottom:22%;width:1px;height:72px;background:rgba(244,240,232,.45)}}
      .sub{{
        position:absolute;left:calc(8% + 28px);bottom:23%;
        font-family:'PB','Noto Sans SC',sans-serif;
        font-size:20px;letter-spacing:.28em;color:rgba(244,240,232,.78);font-weight:500;
      }}
      .meta{{
        position:absolute;left:8%;bottom:8%;
        font-family:Futura,Helvetica Neue,sans-serif;
        font-size:11px;letter-spacing:.42em;color:rgba(244,240,232,.45);text-transform:uppercase;
      }}
      .year{{position:absolute;right:8%;bottom:8%;font-family:Didot,serif;font-size:28px;letter-spacing:.12em;color:rgba(212,184,150,.9)}}
      {extra_css}
    </style></head><body><div class="s">
      <img class="bg" src="{image}"><div class="veil"></div>
      <div class="latin">{safe_latin}</div>
      <div class="title">{safe_title}</div>
      <div class="bar"></div>
      <div class="sub">{safe_sub}</div>
      <div class="meta">{safe_meta}</div>
      <div class="year">{safe_year}</div>
    </div></body></html>"""


def build_puhui_mega_html(
    image: str,
    title: str = "夜航",
    latin: str = "NIGHT VOYAGE",
    en_bottom: str | None = None,
    extra_css: str = "",
) -> str:
    """构建【巨字建筑】海报 HTML。"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "NIGHT VOYAGE"))
    if en_bottom is None:
        safe_en = safe_latin
    else:
        safe_en = escape(str(en_bottom))

    ph_font = resolve_font_path("sans")

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      @font-face{{font-family:'PH';src:url('file://{ph_font}') format('truetype'), url('file://{ph_font}') format('opentype');}}
      *{{margin:0;padding:0;box-sizing:border-box}}
      body{{width:864px;height:1152px;overflow:hidden;background:#0A0A0C}}
      .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
      .bg{{width:100%;height:100%;object-fit:cover;filter:contrast(1.08) saturate(.9)}}
      .fade{{position:absolute;left:0;right:0;bottom:0;height:48%;
        background:linear-gradient(180deg,transparent,rgba(10,10,12,.92) 55%)}}
      .latin{{
        position:absolute;right:8%;top:8%;
        writing-mode:vertical-rl;
        font-family:Futura,Helvetica Neue,sans-serif;
        font-size:13px;letter-spacing:.48em;color:rgba(244,240,232,.7);
        text-transform:uppercase;
      }}
      .title{{
        position:absolute;left:5%;right:5%;bottom:14%;
        font-family:'PH','PingFang SC',sans-serif;
        font-size:168px;line-height:.86;font-weight:900;
        letter-spacing:-.02em;color:#F4F0E8;
      }}
      .en{{
        position:absolute;left:5.5%;bottom:8%;
        font-family:Futura,Avenir,sans-serif;
        font-size:14px;letter-spacing:.52em;color:rgba(212,184,150,.95);text-transform:uppercase;
      }}
      {extra_css}
    </style></head><body><div class="s">
      <img class="bg" src="{image}"><div class="fade"></div>
      <div class="latin">{safe_latin}</div>
      <div class="title">{safe_title}</div>
      <div class="en">{safe_en}</div>
    </div></body></html>"""


def build_vertical_epic_html(
    image: str,
    title: str = "夜航",
    latin: str = "NIGHT VOYAGE",
    slogan: str = "她把城市调成静音",
    seal_char: str = "航",
    extra_css: str = "",
) -> str:
    """构建【中轴竖排东方史诗】海报 HTML。"""
    safe_title = escape(str(title if title is not None else "夜航"))
    safe_latin = escape(str(latin if latin is not None else "NIGHT VOYAGE"))
    safe_slogan = escape(str(slogan if slogan is not None else "她把城市调成静音"))
    safe_seal = escape(str(seal_char if seal_char is not None else "航"))

    ns_font = resolve_font_path("serif")
    ph_font = resolve_font_path("sans")

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      @font-face{{font-family:'NS';src:url('file://{ns_font}') format('opentype'), url('file://{ns_font}') format('truetype');}}
      @font-face{{font-family:'PH';src:url('file://{ph_font}') format('truetype'), url('file://{ph_font}') format('opentype');}}
      *{{margin:0;padding:0;box-sizing:border-box}}
      body{{width:864px;height:1152px;overflow:hidden;background:#0A0A0C}}
      .s{{position:relative;width:864px;height:1152px;overflow:hidden}}
      .bg{{width:100%;height:100%;object-fit:cover;filter:contrast(1.06) saturate(.85)}}
      .veil{{position:absolute;inset:0;background:
        radial-gradient(ellipse at 70% 40%, transparent 20%, rgba(10,10,12,.55) 100%),
        linear-gradient(90deg,rgba(10,10,12,.55),transparent 40%)}}
      .vtitle{{
        position:absolute;right:10%;top:10%;
        writing-mode:vertical-rl;
        font-family:'NS','Songti SC',serif;
        font-size:96px;letter-spacing:.22em;font-weight:900;color:#F4F0E8;line-height:1;
      }}
      .lat{{
        position:absolute;left:9%;top:12%;
        font-family:Didot,Bodoni,serif;font-size:14px;letter-spacing:.5em;
        color:rgba(244,240,232,.8);text-transform:uppercase;
      }}
      .sl{{
        position:absolute;left:9%;bottom:16%;
        font-family:'PH','PingFang SC',sans-serif;
        font-size:18px;letter-spacing:.32em;color:rgba(244,240,232,.82);font-weight:500;
      }}
      .line{{position:absolute;left:9%;bottom:13%;width:64px;height:1px;background:rgba(212,184,150,.7)}}
      .seal{{
        position:absolute;right:10%;bottom:12%;
        width:48px;height:48px;border:1.5px solid rgba(180,35,42,.88);color:rgba(180,35,42,.92);
        display:flex;align-items:center;justify-content:center;
        font-family:'NS','Songti SC',serif;font-size:20px;
      }}
      {extra_css}
    </style></head><body><div class="s">
      <img class="bg" src="{image}"><div class="veil"></div>
      <div class="lat">{safe_latin}</div>
      <div class="vtitle">{safe_title}</div>
      <div class="sl">{safe_slogan}</div>
      <div class="line"></div>
      <div class="seal">{safe_seal}</div>
    </div></body></html>"""


# ---------- 三套「大气」构图渲染对外接口 ----------

def style_monument(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "NIGHT VOYAGE",
    sub: str = "一部还没写完的电影",
    year: str = "2026",
    meta: str = "Agnes Studio · Monument",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 600,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    """思源宋 Black · 电影纪念碑：巨字顶满宽度，西文细带，竖线分隔。"""
    img = sanitize_img_uri(b64(image))
    html = build_monument_html(
        img,
        title=title,
        latin=latin,
        sub=sub,
        year=year,
        meta=meta,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def style_puhui_mega(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "NIGHT VOYAGE",
    en_bottom: str | None = None,
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 600,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    """阿里普惠 Heavy · 巨字建筑：字占下半屏当图形。"""
    img = sanitize_img_uri(b64(image))
    html = build_puhui_mega_html(
        img,
        title=title,
        latin=latin,
        en_bottom=en_bottom,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


def style_vertical_epic(
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "NIGHT VOYAGE",
    slogan: str = "她把城市调成静音",
    seal_char: str = "航",
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 600,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    """思源宋 · 中轴竖排东方史诗。"""
    img = sanitize_img_uri(b64(image))
    html = build_vertical_epic_html(
        img,
        title=title,
        latin=latin,
        slogan=slogan,
        seal_char=seal_char,
        extra_css=extra_css,
    )
    return render_html(html, out, size=size, timeout_ms=timeout_ms, quiet=quiet, dry_run=dry_run)


# =============================================================================
# 风格注册表与多风格派发器
# =============================================================================

CN_TYPE_POSTER_STYLES = {
    "monument": {
        "name": "思源宋 Black 电影纪念碑 (Monument)",
        "func": style_monument,
        "default_file": "type_monument_song.png",
        "description": "思源宋 Black 电影纪念碑：巨字顶满宽度，西文细带，竖线分隔",
    },
    "puhui_mega": {
        "name": "阿里普惠 Heavy 巨字建筑 (Puhui Mega)",
        "func": style_puhui_mega,
        "default_file": "type_puhui_mega.png",
        "description": "阿里普惠 Heavy 巨字建筑：字占下半屏当图形，粗黑厚重建筑感",
    },
    "vertical_epic": {
        "name": "思源宋 中轴竖排东方史诗 (Vertical Epic)",
        "func": style_vertical_epic,
        "default_file": "type_vertical_epic.png",
        "description": "思源宋 中轴竖排东方史诗：右侧大标竖排搭配金石印章与暗部微光",
    },
}


def list_cn_type_poster_styles() -> list[dict[str, str]]:
    """列出所有已注册的纪念碑式高级字排风格预设"""
    return [
        {
            "key": k,
            "name": v["name"],
            "default_file": v["default_file"],
            "description": v.get("description", ""),
        }
        for k, v in CN_TYPE_POSTER_STYLES.items()
    ]


def render_cn_type_poster_style(
    style: str,
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    latin: str = "NIGHT VOYAGE",
    sub: str | None = None,
    slogan: str | None = None,
    seal: str | None = None,
    year: str = "2026",
    meta: str = "Agnes Studio · Monument",
    en_bottom: str | None = None,
    extra_css: str = "",
    size=(864, 1152),
    timeout_ms: int = 600,
    quiet: bool = False,
    dry_run: bool = False,
    **kwargs,
) -> Path:
    """按风格名称派发渲染对应的纪念碑式高级字排海报"""
    key = style.strip().lower()
    if key not in CN_TYPE_POSTER_STYLES:
        raise KeyError(f"Unknown cn type poster style: '{style}'. Available: {list(CN_TYPE_POSTER_STYLES.keys())}")
    style_meta = CN_TYPE_POSTER_STYLES[key]
    func = style_meta["func"]

    if key == "monument":
        sub_text = sub if sub is not None else "一部还没写完的电影"
        return func(
            image=image,
            out=out,
            title=title,
            latin=latin,
            sub=sub_text,
            year=year,
            meta=meta,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
            dry_run=dry_run,
        )
    elif key == "puhui_mega":
        return func(
            image=image,
            out=out,
            title=title,
            latin=latin,
            en_bottom=en_bottom,
            extra_css=extra_css,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
            dry_run=dry_run,
        )
    elif key == "vertical_epic":
        slogan_text = slogan if slogan is not None else "她把城市调成静音"
        seal_c = seal if seal is not None else (title[-1] if title else "航")
        return func(
            image=image,
            out=out,
            title=title,
            latin=latin,
            slogan=slogan_text,
            seal_char=seal_c,
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
            latin=latin,
            size=size,
            timeout_ms=timeout_ms,
            quiet=quiet,
            dry_run=dry_run,
            **kwargs,
        )


def build_arg_parser() -> argparse.ArgumentParser:
    """构建纪念碑式高级字排渲染命令行参数解析器"""
    parser = argparse.ArgumentParser(description="Agnes Studio · 纪念碑式高级字排渲染引擎 (Monumental CN Typography Poster)")
    parser.add_argument(
        "--style",
        "-s",
        default="all",
        choices=["monument", "puhui_mega", "vertical_epic", "all"],
        help="海报版式风格: monument | puhui_mega | vertical_epic | all (默认: all)",
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
        default="NIGHT VOYAGE",
        help="西文大标 (默认: NIGHT VOYAGE)",
    )
    parser.add_argument(
        "--sub",
        default=None,
        help="副标题 (用于 monument 风格)",
    )
    parser.add_argument(
        "--slogan",
        default=None,
        help="标语/说明文本 (用于 vertical_epic 风格)",
    )
    parser.add_argument(
        "--seal",
        default=None,
        help="印章文字 (仅 vertical_epic 风格使用，默认从标题取末字)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用的纪念碑式字排风格预设",
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
            if args.json:
                print(json.dumps(list_cn_type_poster_styles(), ensure_ascii=False, indent=2))
            elif not args.quiet:
                print("Agnes Studio 可用纪念碑字排风格预设:")
                for s in list_cn_type_poster_styles():
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
            return 1 if args.strict else 0

        target_styles = list(CN_TYPE_POSTER_STYLES.keys()) if args.style == "all" else [args.style]

        quiet = suppress_log
        report_items = []
        default_out_dir = Path(args.out_dir) if args.out_dir else (ROOT / "outputs" / "epic_compare")
        for st in target_styles:
            if args.out:
                out_path = Path(args.out)
                if args.style == "all":
                    out_path = out_path.with_name(f"{out_path.stem}_{st}{out_path.suffix or '.png'}")
            else:
                default_out_dir.mkdir(parents=True, exist_ok=True)
                out_path = default_out_dir / CN_TYPE_POSTER_STYLES[st]["default_file"]

            render_cn_type_poster_style(
                style=st,
                image=resolved_src,
                out=out_path,
                title=args.title,
                latin=args.latin,
                sub=args.sub,
                slogan=args.slogan,
                seal=args.seal,
                quiet=quiet,
                dry_run=args.dry_run,
            )
            report_items.append({
                "style": st,
                "name": CN_TYPE_POSTER_STYLES[st]["name"],
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
            print(f"❌ 纪念碑式海报渲染失败: {e}", file=sys.stderr)
        return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
