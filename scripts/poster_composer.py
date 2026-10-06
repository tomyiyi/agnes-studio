#!/usr/bin/env python3
"""
Agnes Studio - 商业海报排版与中文字体合成引擎
遵循 GitHub 高星排版标准（chinese-copywriting-guidelines / satori 盒模型思想）
支持 得意黑 (Smiley Sans)、霞鹜文楷 (LXGW WenKai)、经典宋体 (Songti) 矢量光影合成
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from env_config import FONTS_DIR, ASSETS_DIR, resolve_font_path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONTS_DIR = str(FONTS_DIR)
ASSETS_DIR = str(ASSETS_DIR)

FONT_STYLES: dict[str, dict[str, Any]] = {
    "wenkai": {
        "key": "wenkai",
        "name": "霞鹜文楷",
        "font_file": "LXGWWenKai-Regular.ttf",
        "description": "经典文楷书风，温润优雅，适用于人文、艺术与叙事商业海报",
    },
    "smiley": {
        "key": "smiley",
        "name": "得意黑",
        "font_file": "SmileySans-Oblique.ttf",
        "description": "现代窄体黑体，动感有力，适用于先锋、科技与运动潮牌海报",
    },
    "songti": {
        "key": "songti",
        "name": "经典宋体",
        "font_file": "SourceHanSerif-Regular.otf",
        "description": "高雅清秀宋体，庄重端庄，适用于典雅、文艺与高端品牌海报",
    },
}

THEME_COLORS: dict[str, dict[str, Any]] = {
    "amber_gold": {
        "key": "amber_gold",
        "name": "琥珀暖金",
        "title_rgb": [255, 228, 160],
        "description": "温暖复古金色调，适合人文、古典、蒸汽朋克海报",
    },
    "cyber_cyan": {
        "key": "cyber_cyan",
        "name": "赛博青蓝",
        "title_rgb": [0, 240, 255],
        "description": "冷色霓虹青蓝调，适合未来科幻、都市街头海报",
    },
    "pure_white": {
        "key": "pure_white",
        "name": "极简纯白",
        "title_rgb": [255, 255, 255],
        "description": "纯净高对比白灰色调，适合极简现代、黑白光影海报",
    },
}


def list_font_styles() -> list[dict[str, Any]]:
    """返回支持的字体风格元数据清单。"""
    return [dict(v) for v in FONT_STYLES.values()]


def list_theme_colors() -> list[dict[str, Any]]:
    """返回支持的配色主题元数据清单。"""
    return [dict(v) for v in THEME_COLORS.values()]


def _prepare_io(bg_image_path, output_path):
    if not bg_image_path:
        raise ValueError("Background image path cannot be empty")
    bg_p = Path(bg_image_path)
    if not bg_p.is_file():
        raise FileNotFoundError(f"Source background image not found: {bg_image_path}")
    if not output_path:
        raise ValueError("Output path cannot be empty")
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    return bg_p, out_p


def get_font(font_key, size):
    path = resolve_font_path(font_key)
    if path and os.path.exists(str(path)):
        try:
            return ImageFont.truetype(str(path), size)
        except Exception:
            pass
    # 兜底
    return ImageFont.load_default()

def compose_commercial_poster(
    bg_image_path,
    output_path,
    font_style="wenkai",       # "wenkai" (霞鹜文楷) | "smiley" (得意黑) | "songti" (宋体)
    main_title="铜钟与蒸汽城",
    sub_title="STEAM & CHIME",
    tagline="「 她修理时间，也修理人心 」",
    metadata_no="ARCHIVE NO. 2026-X89 // DIRECTED BY AGNES STUDIO",
    theme_color="amber_gold",   # "amber_gold" | "cyber_cyan" | "pure_white"
    quiet=False,
):
    bg_p, out_p = _prepare_io(bg_image_path, output_path)
    font_style = str(font_style or "wenkai").strip().lower()
    main_title = str(main_title or "")
    sub_title = str(sub_title or "")
    tagline = str(tagline or "")
    metadata_no = str(metadata_no or "")
    theme_color = str(theme_color or "amber_gold").strip().lower()

    if not quiet:
        print(f"🎨 [Poster Composer] 正在使用【{font_style}】字体合成商业级海报...")

    base_img = Image.open(bg_p).convert("RGBA")
    w, h = base_img.size

    # 创建透明文字层
    text_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    # 配色配置
    if theme_color == "amber_gold":
        c_title = (255, 228, 160, 255)
        c_sub = (240, 205, 130, 240)
        c_tagline = (235, 235, 245, 230)
        c_meta = (180, 185, 200, 180)
        shadow_tint = (35, 20, 10, 220)
    elif theme_color == "cyber_cyan":
        c_title = (0, 240, 255, 255)
        c_sub = (140, 245, 255, 230)
        c_tagline = (230, 240, 255, 230)
        c_meta = (150, 200, 220, 180)
        shadow_tint = (5, 25, 45, 220)
    else:  # pure_white or fallback
        c_title = (255, 255, 255, 255)
        c_sub = (220, 225, 235, 230)
        c_tagline = (200, 205, 215, 220)
        c_meta = (160, 165, 175, 180)
        shadow_tint = (10, 10, 15, 220)

    # 计算排版尺寸 (基准按 1024 宽等比自适应)
    scale = w / 1024.0
    size_title = int(48 * scale)
    size_sub = int(18 * scale)
    size_tagline = int(22 * scale)
    size_meta = int(12 * scale)

    f_title = get_font(font_style, size_title)
    f_sub = get_font("smiley" if font_style == "smiley" else "wenkai", size_sub)
    f_tagline = get_font(font_style, size_tagline)
    f_meta = get_font("smiley", size_meta)

    # 锚定在左上角预留的负空间 (符合电影与动画概念海报构图)
    margin_x = int(64 * scale)
    curr_y = int(60 * scale)

    # 绘制辅助装饰线 (Top Border Accent)
    draw.line([(margin_x, curr_y - 12), (margin_x + int(240 * scale), curr_y - 12)], fill=c_sub, width=max(1, int(1.5 * scale)))

    # 1. 绘制 Tier 1 主标题 (带柔和多层光晕阴影，避免脏黑)
    # 为增加通透与呼吸感，汉字字符之间加入字间距 (Tracking)
    if main_title:
        title_spaced = " ".join(list(main_title)) if font_style != "smiley" else main_title
        for ox, oy in [(-2, 2), (2, 2), (0, 3), (3, 3)]:
            draw.text((margin_x + ox, curr_y + oy), title_spaced, font=f_title, fill=shadow_tint)
        draw.text((margin_x, curr_y), title_spaced, font=f_title, fill=c_title)

    curr_y += int(62 * scale)

    # 2. 绘制 Tier 2 英文副标 (大幅拉开字间距)
    if sub_title:
        sub_spaced = "   ".join(sub_title.split())
        for ox, oy in [(0, 2), (1, 1)]:
            draw.text((margin_x + ox, curr_y + oy), sub_spaced, font=f_sub, fill=shadow_tint)
        draw.text((margin_x, curr_y), sub_spaced, font=f_sub, fill=c_sub)

    curr_y += int(38 * scale)

    # 3. 绘制 Tier 3 叙事 Slogan
    if tagline:
        for ox, oy in [(0, 1), (1, 1)]:
            draw.text((margin_x + ox, curr_y + oy), tagline, font=f_tagline, fill=shadow_tint)
        draw.text((margin_x, curr_y), tagline, font=f_tagline, fill=c_tagline)

    # 4. 绘制 Tier 4 底部商业元数据 (底部条形码 + 档案编号)
    bottom_y = h - int(48 * scale)
    # 模拟极客条形码
    bar_x = margin_x
    for i in range(16):
        b_w = int((2 if i % 3 == 0 else 1) * scale)
        draw.line([(bar_x, bottom_y), (bar_x, bottom_y + int(14 * scale))], fill=c_meta, width=b_w)
        bar_x += int((4 if i % 2 == 0 else 3) * scale)

    if metadata_no:
        draw.text((bar_x + int(12 * scale), bottom_y + int(2 * scale)), metadata_no, font=f_meta, fill=c_meta)

    # 合成与导出
    final_poster = Image.alpha_composite(base_img, text_layer)
    final_poster = final_poster.convert("RGB")
    final_poster.save(str(out_p), quality=95)
    if not quiet:
        print(f"✅ 商业海报渲染完成: {out_p}")
    return str(out_p)


def build_arg_parser() -> argparse.ArgumentParser:
    """构建商业海报排版与中文字体合成引擎命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="Agnes Studio · 商业海报排版与中文字体合成引擎 (Poster Composer)")
    parser.add_argument(
        "--bg",
        "-b",
        default=None,
        help="背景底图路径（未指定时将查找 public/assets 样张底图）",
    )
    parser.add_argument(
        "--out",
        "-o",
        default=None,
        help="输出海报图片路径（默认 outputs/posters/poster_<style>.png）",
    )
    parser.add_argument(
        "--font-style",
        "-f",
        default="wenkai",
        choices=["wenkai", "smiley", "songti"],
        help="排版字体风格: wenkai (霞鹜文楷) | smiley (得意黑) | songti (经典宋体)",
    )
    parser.add_argument(
        "--title",
        "-t",
        default="铜钟与蒸汽城",
        help="海报主标题文本",
    )
    parser.add_argument(
        "--sub",
        "-s",
        default="STEAM & CHIME",
        help="英文/拼音副标题文本",
    )
    parser.add_argument(
        "--tagline",
        default="「 她修理时间，也修理人心 」",
        help="海报叙事 Slogan / 金句文本",
    )
    parser.add_argument(
        "--metadata",
        default="ARCHIVE NO. 2026-X89 // DIRECTED BY AGNES STUDIO",
        help="底部商业档案元数据编号",
    )
    parser.add_argument(
        "--theme-color",
        "-c",
        default="amber_gold",
        choices=["amber_gold", "cyber_cyan", "pure_white"],
        help="配色主题: amber_gold | cyber_cyan | pure_white",
    )
    parser.add_argument(
        "--all-styles",
        action="store_true",
        help="一键渲染输出全部 3 款开源字体风格版本",
    )
    parser.add_argument(
        "--list-styles",
        "-l",
        action="store_true",
        help="列出支持的字体风格与配色主题清单",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出预设清单或渲染执行汇总报告",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="静默模式，抑制常规控制台日志",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：底图缺失或渲染异常时返回退出码 1",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    quiet = args.quiet or args.json

    try:
        if args.list_styles:
            styles = list_font_styles()
            colors = list_theme_colors()
            if args.json:
                print(json.dumps({
                    "font_styles": styles,
                    "theme_colors": colors,
                }, ensure_ascii=False, indent=2))
            elif not args.quiet:
                print("Agnes Studio · 支持字体风格清单:")
                for s in styles:
                    print(f"  [{s['key']:<8}] {s['name']:<8} ({s['font_file']:<26}) | {s['description']}")
                print("Agnes Studio · 支持配色主题清单:")
                for c in colors:
                    print(f"  [{c['key']:<12}] {c['name']:<8} | {c['description']}")
            return 0

        # 确定输入背景底图
        target_bg = None
        if args.bg:
            p = Path(args.bg).resolve()
            if p.is_file():
                target_bg = p
        else:
            default_candidate = Path(ASSETS_DIR) / "agnes_1790006749_b2b755da.png"
            if default_candidate.is_file():
                target_bg = default_candidate
            else:
                candidates = sorted(list(Path(ASSETS_DIR).glob("*.png")))
                if candidates:
                    target_bg = candidates[0]

        if not target_bg or not target_bg.is_file():
            err_msg = f"找不到可用背景底图: {args.bg or ASSETS_DIR}"
            if args.json:
                print(json.dumps({"ok": False, "error": err_msg}, ensure_ascii=False, indent=2))
            elif not args.quiet:
                print(f"❌ {err_msg}", file=sys.stderr)
            return 1

        styles_to_render = ["wenkai", "smiley", "songti"] if args.all_styles else [args.font_style]
        results: list[dict[str, Any]] = []

        for style in styles_to_render:
            if args.out:
                out_path = Path(args.out)
                if args.all_styles:
                    out_path = out_path.parent / f"{out_path.stem}_{style}{out_path.suffix or '.png'}"
            else:
                default_dir = SCRIPTS_DIR.parent / "outputs" / "posters"
                out_path = default_dir / f"poster_{style}.png"

            res_path = compose_commercial_poster(
                target_bg,
                out_path,
                font_style=style,
                main_title=args.title,
                sub_title=args.sub,
                tagline=args.tagline,
                metadata_no=args.metadata,
                theme_color=args.theme_color,
                quiet=quiet,
            )
            file_p = Path(res_path)
            results.append({
                "style": style,
                "file": str(file_p),
                "bytes": file_p.stat().st_size if file_p.exists() else 0,
                "ok": True,
            })

        if args.json:
            print(json.dumps({
                "ok": True,
                "total": len(results),
                "styles": styles_to_render,
                "bg": str(target_bg),
                "results": results,
            }, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False, indent=2))
        elif not args.quiet:
            if getattr(args, "list_styles", False):
                print(f"❌ 查询字体风格清单失败: {e}", file=sys.stderr)
            else:
                print(f"❌ 商业海报渲染失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
