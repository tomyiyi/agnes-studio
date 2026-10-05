#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""反 slop 海报：一个巨型事件 + 三级字阶 + 最多一种表现手法。"""
from __future__ import annotations

import argparse
import base64
from html import escape
import json
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


def shot(
    html: str,
    out: str | Path,
    size=(864, 1152),
    timeout_ms: int = 500,
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        if not quiet:
            print(f" ✓ {out_path.name} (dry_run)")
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
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    """named move: mega-title-bleed — 巨字贴边裁切，仅 macro+micro。"""
    img = b64(image)
    html = build_mega_bleed_html(img, title=title, subtitle_top=subtitle_top, subtitle_bottom=subtitle_bottom)
    return shot(html, out, quiet=quiet, dry_run=dry_run)


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
    quiet: bool = False,
    dry_run: bool = False,
) -> Path:
    """named move: hard-field-inversion — 底部硬色场反转，标题可读通道。"""
    img = b64(image)
    html = build_hard_field_html(img, title=title, tagline=tagline, micro_text=micro_text)
    return shot(html, out, quiet=quiet, dry_run=dry_run)


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
    quiet: bool = False,
    dry_run: bool = False,
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
    return shot(html, out, quiet=quiet, dry_run=dry_run)


# =============================================================================
# 风格注册表与多风格派发器
# =============================================================================

DRAMA_POSTER_STYLES = {
    "mega_bleed": {
        "name": "巨字贴边裁切 (Mega Title Bleed)",
        "func": mega_bleed,
        "default_file": "drama_01_mega_bleed.png",
        "description": "巨字贴边裁切：只保留 macro 主标题与微型标签，破格出血冲击力",
    },
    "hard_field": {
        "name": "硬色场反转 (Hard Field Inversion)",
        "func": hard_field,
        "default_file": "drama_02_hard_field.png",
        "description": "硬色场反转：底部 36% 纯黑硬色场反转，确保主标题极致可读与视觉重心",
    },
    "chinese_corner": {
        "name": "边角式计白当黑 (Chinese Corner)",
        "func": chinese_corner,
        "default_file": "drama_03_corner.png",
        "description": "边角式计白当黑：右上竖排主标题与右下朱红印章，大面积留白让位于画面",
    },
}


def list_drama_poster_styles() -> list[dict[str, str]]:
    """列出所有已注册的反 slop 戏剧性海报版式预设"""
    return [
        {
            "key": k,
            "name": v["name"],
            "default_file": v["default_file"],
            "description": v.get("description", ""),
        }
        for k, v in DRAMA_POSTER_STYLES.items()
    ]


def render_drama_poster_style(
    style: str,
    image: str | Path,
    out: str | Path,
    title: str = "夜航",
    subtitle: str | None = None,
    tagline: str | None = None,
    seal: str | None = None,
    quiet: bool = False,
    dry_run: bool = False,
    **kwargs,
) -> Path:
    """按风格名称派发渲染对应的反 slop 戏剧性海报"""
    key = style.strip().lower()
    if key not in DRAMA_POSTER_STYLES:
        raise KeyError(f"Unknown drama poster style: '{style}'. Available: {list(DRAMA_POSTER_STYLES.keys())}")
    style_meta = DRAMA_POSTER_STYLES[key]
    func = style_meta["func"]

    if key == "mega_bleed":
        sub_top = subtitle if subtitle is not None else "Night Voyage"
        sub_bot = tagline if tagline is not None else "Agnes · 2026"
        return func(
            image=image,
            out=out,
            title=title,
            subtitle_top=sub_top,
            subtitle_bottom=sub_bot,
            quiet=quiet,
            dry_run=dry_run,
        )
    elif key == "hard_field":
        tline = tagline if tagline is not None else "她把城市调成静音"
        micro = subtitle if subtitle is not None else "A Film Still"
        return func(
            image=image,
            out=out,
            title=title,
            tagline=tline,
            micro_text=micro,
            quiet=quiet,
            dry_run=dry_run,
        )
    elif key == "chinese_corner":
        sub = subtitle if subtitle is not None else "Night Voyage"
        bot_label = tagline if tagline is not None else "Agnes Studio"
        seal_c = seal if seal is not None else (title[-1] if title else "航")
        return func(
            image=image,
            out=out,
            title=title,
            subtitle=sub,
            bottom_label=bot_label,
            seal_char=seal_c,
            quiet=quiet,
            dry_run=dry_run,
        )
    else:
        return func(
            image=image,
            out=out,
            title=title,
            quiet=quiet,
            dry_run=dry_run,
            **kwargs,
        )


def build_arg_parser() -> argparse.ArgumentParser:
    """构建反 slop 巨幅戏剧性海报渲染命令行参数解析器"""
    parser = argparse.ArgumentParser(description="Agnes Studio · 反 slop 巨幅戏剧性海报渲染引擎 (Drama Poster Renderer)")
    parser.add_argument(
        "--style",
        "-s",
        default="all",
        choices=["mega_bleed", "hard_field", "chinese_corner", "all"],
        help="海报版式风格: mega_bleed | hard_field | chinese_corner | all (默认: all)",
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
        "--out-dir",
        default=None,
        help="输出海报目录（当未指定 --out 时覆盖默认输出目录）",
    )
    parser.add_argument(
        "--title",
        "-t",
        default="夜航",
        help="海报中文主标题 (默认: 夜航)",
    )
    parser.add_argument(
        "--subtitle",
        default=None,
        help="海报副标题/说明文本 (默认根据风格预设自动提供)",
    )
    parser.add_argument(
        "--tagline",
        default=None,
        help="海报标语/底部标签 (默认根据风格预设自动提供)",
    )
    parser.add_argument(
        "--seal",
        default=None,
        help="印章文字 (仅 chinese_corner 风格使用，默认从标题取末字)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用的戏剧性海报风格预设",
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
    args = parser.parse_args(argv if argv is not None else [])

    suppress_log = args.quiet or args.json

    try:
        if args.list:
            if args.json:
                print(json.dumps(list_drama_poster_styles(), ensure_ascii=False, indent=2))
            elif not args.quiet:
                print("Agnes Studio 可用戏剧性海报风格预设:")
                for s in list_drama_poster_styles():
                    print(f"  - [{s['key']}] {s['name']} -> {s['default_file']}")
            return 0

        # 确定输入源
        resolved_src = None
        input_path_arg = args.src
        if input_path_arg:
            p = Path(input_path_arg)
            if not p.is_file():
                err_msg = f"找不到输入底图: {input_path_arg}"
                if args.json:
                    print(json.dumps({"error": err_msg, "ok": False}, ensure_ascii=False))
                elif not args.quiet:
                    print(f"❌ {err_msg}", file=sys.stderr)
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
            err_msg = "未指定 --src 且未发现默认候选底图资产"
            if args.json:
                print(json.dumps({"error": err_msg, "ok": False}, ensure_ascii=False))
            elif not args.quiet:
                print(f"❌ {err_msg}", file=sys.stderr)
            return 1 if args.strict else 0

        target_styles = list(DRAMA_POSTER_STYLES.keys()) if args.style == "all" else [args.style]

        quiet = suppress_log
        report_items = []
        default_out_dir = Path(args.out_dir) if args.out_dir else (ROOT / "outputs" / "drama_study")
        for st in target_styles:
            if args.out:
                out_path = Path(args.out)
                if args.style == "all":
                    out_path = out_path.with_name(f"{out_path.stem}_{st}{out_path.suffix or '.png'}")
            else:
                default_out_dir.mkdir(parents=True, exist_ok=True)
                out_path = default_out_dir / DRAMA_POSTER_STYLES[st]["default_file"]

            render_drama_poster_style(
                style=st,
                image=resolved_src,
                out=out_path,
                title=args.title,
                subtitle=args.subtitle,
                tagline=args.tagline,
                seal=args.seal,
                quiet=quiet,
                dry_run=args.dry_run,
            )
            report_items.append({
                "style": st,
                "name": DRAMA_POSTER_STYLES[st]["name"],
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
            print(f"❌ 戏剧性海报渲染失败: {e}", file=sys.stderr)
        return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
