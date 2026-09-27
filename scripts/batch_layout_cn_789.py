#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agnes Studio · 7/8/9 版式精修渲染器 (中文高级字设真字体后期叠字).

三大经典构图：
- 07 杂志开窗 (compose_07 / window_spine): 大图窗居中偏上 + 左竖排中文书脊 + 窗下注脚
- 08 杂志开窗·b (compose_08 / offset_window): 偏心大窗 + 中文横题（字大、字距开）
- 09 独主体大空场 (compose_09 / solo_field): 人物居右下 + 左上中文巨字 + 留白羽化
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import env_config  # noqa: F401
from env_config import (
    PROJECT_ROOT,
    FONTS_DIR,
    resolve_font_path,
)

from PIL import Image, ImageDraw, ImageFilter, ImageFont

try:
    from agnes_gateway import generate, save_image  # noqa: E402
except ImportError:
    generate = None  # type: ignore
    save_image = None  # type: ignore

OUT = ROOT / "outputs" / "layout_variants" / "L2"
OUT.mkdir(parents=True, exist_ok=True)

FONTS = FONTS_DIR
SERIF_BLACK = FONTS / "NotoSerifCJKsc-Black.otf"
SERIF_BOLD = FONTS / "NotoSerifCJKsc-Bold.otf"
PUHUI_H = FONTS / "Alibaba-PuHuiTi-Heavy.ttf"
PUHUI_M = FONTS / "Alibaba-PuHuiTi-Medium.ttf"
SONGTI = FONTS / "Songti.ttc"
LATIN_DIDOT = Path("/System/Library/Fonts/Supplemental/Didot.ttc")
LATIN_BODONI = Path("/System/Library/Fonts/Supplemental/Bodoni 72.ttc")
LATIN_FUTURA = Path("/System/Library/Fonts/Supplemental/Futura.ttc")

# 人物占比刻意放大：近景/中景，脸可读，留出字槽
BASE_PORTRAIT = (
    "young Asian woman long black hair, elegant cream knit sweater, "
    "warm greige studio, soft fashion light, fashion editorial photography, "
    "subject LARGE in frame occupying 50-65% height, face clearly readable, "
    "three-quarter or frontal beauty portrait, quiet luxury mood, "
    "clean uncluttered background, no text, no letters, no watermark, no UI"
)

# 7/8 需要图窗用：主体稍收，但仍比原版大
BASE_WINDOW = (
    "young Asian woman long black hair cream knit sweater, warm greige studio, "
    "soft fashion light, elegant fashion portrait, subject medium-large 45-58% height, "
    "face readable, calm luxury, clean background, no text no letters no watermark"
)

BASE_SOLO = (
    "young Asian woman long black hair cream knit sweater, warm greige seamless studio, "
    "soft directional fashion light, full editorial figure medium shot, "
    "subject clearly present 42-55% of frame height, face readable, vast calm empty field around, "
    "premium minimalist, no text no letters no watermark no UI"
)

SHOTS = [
    # 7 系列人物
    ("07a_portrait", BASE_WINDOW),
    ("07b_portrait", BASE_WINDOW),
    # 8 系列
    ("08a_portrait", BASE_WINDOW),
    ("08b_portrait", BASE_WINDOW),
    # 9 系列
    ("09a_portrait", BASE_SOLO),
    ("09b_portrait", BASE_SOLO),
]


def resolve_layout_font(target: str | Path | None = None, size: int = 16) -> ImageFont.FreeTypeFont:
    """跨平台安全解析并加载 TrueType/OpenType 字体，若路径不存在则自动降级到可用字体或系统默认。"""
    # 1. 直接是有效文件路径
    if target:
        p = Path(target)
        if p.is_file():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                pass
        # 尝试通过 env_config 解析
        resolved = resolve_font_path(str(target))
        if resolved and Path(resolved).is_file():
            try:
                return ImageFont.truetype(resolved, size)
            except Exception:
                pass

    # 2. 依次尝试项目常见字体 (wenkai, smiley, sans, serif)
    for key in ("wenkai", "smiley", "songti", "sans"):
        fallback = resolve_font_path(key)
        if fallback and Path(fallback).is_file():
            try:
                return ImageFont.truetype(fallback, size)
            except Exception:
                continue

    # 3. 终极兜底
    try:
        return ImageFont.load_default()
    except Exception:
        raise OSError("Unable to load any usable font")


def font(path: Path | str, size: int) -> ImageFont.FreeTypeFont:
    """兼容旧接口的字体加载器，内部使用 resolve_layout_font 提供跨平台容错。"""
    return resolve_layout_font(path, size)


def paste_rgba(base: Image.Image, overlay: Image.Image, xy: tuple[int, int]) -> None:
    """使用 RGBA 透明通道将图层贴入底图。"""
    base.paste(overlay, xy, overlay)


def measure(text: str, fnt: ImageFont.FreeTypeFont, tracking: int = 0) -> tuple[int, int]:
    """安全测量文字尺寸，支持字间距 (tracking)。"""
    if not text:
        return 1, 1
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    w = 0
    h = 0
    for ch in text:
        bbox = d.textbbox((0, 0), ch, font=fnt)
        w += (bbox[2] - bbox[0]) + tracking
        h = max(h, bbox[3] - bbox[1])
    return max(w - tracking, 1), max(h, 1)


def text_rgba(
    size: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    *,
    tracking: int = 0,
    vertical: bool = False,
) -> Image.Image:
    """将文字渲染至透明 RGBA 图层；支持横排/竖排及字间距。"""
    w, h = max(size[0], 1), max(size[1], 1)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if not text:
        return layer
    d = ImageDraw.Draw(layer)
    if vertical:
        y = 0
        fnt_size = getattr(fnt, "size", 16)
        for ch in text:
            bbox = d.textbbox((0, 0), ch, font=fnt)
            cw, chh = bbox[2] - bbox[0], bbox[3] - bbox[1]
            d.text(((w - cw) / 2 - bbox[0], y - bbox[1]), ch, font=fnt, fill=fill)
            y += chh + tracking + int(fnt_size * 0.12)
    else:
        x = 0
        for ch in text:
            bbox = d.textbbox((0, 0), ch, font=fnt)
            d.text((x - bbox[0], -bbox[1]), ch, font=fnt, fill=fill)
            x += (bbox[2] - bbox[0]) + tracking
    return layer


def compose_07(
    src: Path | str,
    out: Path | str,
    title: str = "留白",
    latin: str = "THE WHITE",
    caption: str = "把空气留给呼吸",
) -> Path:
    """杂志开窗：大图窗居中偏上 + 左竖排中文书脊 + 窗下 caption。"""
    src_p = Path(src)
    if not src_p.is_file():
        raise FileNotFoundError(f"Source image not found: {src}")

    W, H = 864, 1152
    canvas = Image.new("RGBA", (W, H), (242, 236, 226, 255))  # ivory paper
    win_w, win_h = int(W * 0.72), int(H * 0.52)
    win_x, win_y = int(W * 0.18), int(H * 0.16)

    photo = Image.open(src_p).convert("RGB")
    pw, ph = photo.size
    scale = max(win_w / pw, win_h / ph)
    photo = photo.resize((int(pw * scale), int(ph * scale)), Image.LANCZOS)
    left = (photo.width - win_w) // 2
    top = max(0, (photo.height - win_h) // 2 - int(photo.height * 0.06))
    photo = photo.crop((left, top, left + win_w, top + win_h))
    canvas.paste(photo, (win_x, win_y))

    # thin window rule
    d = ImageDraw.Draw(canvas)
    d.rectangle([win_x, win_y, win_x + win_w, win_y + win_h], outline=(40, 36, 32, 90), width=1)

    # left vertical Chinese spine title — monumental serif
    f_title = resolve_layout_font("serif", 64)
    ty = int(H * 0.20)
    for ch in title:
        layer = Image.new("RGBA", (80, 90), (0, 0, 0, 0))
        dd = ImageDraw.Draw(layer)
        bbox = dd.textbbox((0, 0), ch, font=f_title)
        dd.text(((80 - (bbox[2] - bbox[0])) / 2 - bbox[0], 0 - bbox[1]), ch, font=f_title, fill=(28, 24, 20, 255))
        paste_rgba(canvas, layer, (int(W * 0.055), ty))
        ty += 78

    # tiny latin vertical-ish label under spine
    f_lat = resolve_layout_font("didot", 13)
    d.text((int(W * 0.065), ty + 12), latin, font=f_lat, fill=(90, 80, 70, 220))

    # caption under window
    f_cap = resolve_layout_font("sans", 15)
    d.text((win_x, win_y + win_h + 18), caption, font=f_cap, fill=(70, 62, 54, 230))
    # micro index
    f_micro = resolve_layout_font("sans", 12)
    d.text((win_x + win_w - 40, win_y + win_h + 20), "07", font=f_micro, fill=(120, 108, 96, 200))
    # one hairline
    d.line([win_x, win_y + win_h + 48, win_x + win_w, win_y + win_h + 48], fill=(90, 80, 70, 120), width=1)

    out_p = Path(out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_p, quality=93)
    print("OK compose", out_p.name)
    return out_p


def compose_08(
    src: Path | str,
    out: Path | str,
    title: str = "静物",
    latin: str = "STILL LIFE",
    caption: str = "安静是最好的滤镜",
) -> Path:
    """杂志开窗·b：偏心大窗 + 中文横题（字大、字距开）。"""
    src_p = Path(src)
    if not src_p.is_file():
        raise FileNotFoundError(f"Source image not found: {src}")

    W, H = 864, 1152
    canvas = Image.new("RGBA", (W, H), (236, 228, 216, 255))
    d = ImageDraw.Draw(canvas)

    win_w, win_h = int(W * 0.78), int(H * 0.58)
    win_x, win_y = int(W * 0.14), int(H * 0.28)
    photo = Image.open(src_p).convert("RGB")
    pw, ph = photo.size
    scale = max(win_w / pw, win_h / ph)
    photo = photo.resize((int(pw * scale), int(ph * scale)), Image.LANCZOS)
    left = (photo.width - win_w) // 2
    top = max(0, (photo.height - win_h) // 2 - int(photo.height * 0.05))
    photo = photo.crop((left, top, left + win_w, top + win_h))
    canvas.paste(photo, (win_x, win_y))
    d.rectangle([win_x, win_y, win_x + win_w, win_y + win_h], outline=(50, 42, 36, 80), width=1)

    # horizontal Chinese title — large, wide tracking, top left
    f_title = resolve_layout_font("serif", 92)
    tracking = 18
    tw, th = measure(title, f_title, tracking)
    layer = text_rgba((tw + 20, th + 20), title, f_title, (32, 28, 24, 255), tracking=tracking)
    paste_rgba(canvas, layer, (int(W * 0.10), int(H * 0.10)))

    # latin subline
    f_lat = resolve_layout_font("didot", 16)
    d.text((int(W * 0.11), int(H * 0.10) + th + 28), latin, font=f_lat, fill=(96, 84, 72, 220))

    # caption under window
    f_cap = resolve_layout_font("sans", 15)
    d.text((win_x, win_y + win_h + 20), caption, font=f_cap, fill=(70, 62, 54, 230))
    f_micro = resolve_layout_font("sans", 12)
    d.text((win_x + win_w - 36, win_y + win_h + 22), "08", font=f_micro, fill=(120, 108, 96, 200))

    # hairline under title
    d.line([int(W * 0.11), int(H * 0.10) + th + 56, int(W * 0.55), int(H * 0.10) + th + 56], fill=(90, 80, 70, 130), width=1)

    out_p = Path(out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_p, quality=93)
    print("OK compose", out_p.name)
    return out_p


def compose_09(
    src: Path | str,
    out: Path | str,
    title: str = "独白",
    latin: str = "MONOLOGUE",
    micro: str = "一个人的完整场",
    caption: str | None = None,
) -> Path:
    """独主体大空场：人物放大占右下，左上中文巨字 + 留白。"""
    src_p = Path(src)
    if not src_p.is_file():
        raise FileNotFoundError(f"Source image not found: {src}")

    if caption is not None:
        micro = caption

    W, H = 864, 1152
    canvas = Image.new("RGBA", (W, H), (232, 224, 212, 255))
    d = ImageDraw.Draw(canvas)

    win_w, win_h = int(W * 0.55), int(H * 0.62)
    win_x, win_y = int(W * 0.38), int(H * 0.30)
    photo = Image.open(src_p).convert("RGB")
    pw, ph = photo.size
    scale = max(win_w / pw, win_h / ph)
    photo = photo.resize((int(pw * scale), int(ph * scale)), Image.LANCZOS)
    left = (photo.width - win_w) // 2
    top = max(0, (photo.height - win_h) // 2 - int(photo.height * 0.04))
    photo = photo.crop((left, top, left + win_w, top + win_h))

    # soft feather edge so person sits in field (no hard sticker frame)
    mask = Image.new("L", (win_w, win_h), 0)
    md = ImageDraw.Draw(mask)
    md.rectangle([8, 8, win_w - 8, win_h - 8], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(6))
    canvas.paste(photo, (win_x, win_y), mask)

    # monumental Chinese title upper-left — 2 chars huge
    f_title = resolve_layout_font("serif", 150)
    tracking = 12
    tw, th = measure(title, f_title, tracking)
    layer = text_rgba((tw + 30, th + 30), title, f_title, (28, 24, 20, 255), tracking=tracking)
    paste_rgba(canvas, layer, (int(W * 0.08), int(H * 0.10)))

    # thin latin
    f_lat = resolve_layout_font("didot", 15)
    d.text((int(W * 0.09), int(H * 0.10) + th + 24), latin, font=f_lat, fill=(88, 76, 64, 210))

    # tiny micro line bottom-left
    f_cap = resolve_layout_font("sans", 13)
    d.text((int(W * 0.09), int(H * 0.88)), micro, font=f_cap, fill=(100, 90, 80, 210))
    f_micro = resolve_layout_font("sans", 12)
    d.text((int(W * 0.09), int(H * 0.91)), "09", font=f_micro, fill=(130, 118, 104, 180))
    # one vertical hairline
    d.line([int(W * 0.09), int(H * 0.82), int(W * 0.09), int(H * 0.86)], fill=(90, 80, 70, 140), width=1)

    out_p = Path(out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_p, quality=93)
    print("OK compose", out_p.name)
    return out_p


LAYOUT_CN_REGISTRY = {
    "07": {
        "name": "杂志开窗 (大图窗 + 左竖排书脊)",
        "func": compose_07,
        "default_title": "留白",
        "default_latin": "THE WHITE",
        "default_caption": "把空气留给呼吸",
        "default_filename": "07_magazine_window.png",
    },
    "08": {
        "name": "偏心大窗 (偏心大窗 + 中文横题)",
        "func": compose_08,
        "default_title": "静物",
        "default_latin": "STILL LIFE",
        "default_caption": "安静是最好的滤镜",
        "default_filename": "08_offset_window.png",
    },
    "09": {
        "name": "独主体大空场 (人物居右下 + 巨字留白)",
        "func": compose_09,
        "default_title": "独白",
        "default_latin": "MONOLOGUE",
        "default_caption": "一个人的完整场",
        "default_filename": "09_solo_space.png",
    },
}


def normalize_variant_key(key: str) -> str:
    """标准化版式键名：'07', '7', '07a', 'window' -> '07'。"""
    k = str(key or "").strip().lower()
    if "7" in k or "window" in k and "offset" not in k:
        return "07"
    if "8" in k or "offset" in k:
        return "08"
    if "9" in k or "solo" in k:
        return "09"
    raise KeyError(f"Unknown layout variant: '{key}'. Supported: '07', '08', '09'")


def render_layout_cn(
    variant: str,
    src: Path | str,
    out: Path | str,
    title: str = "",
    latin: str = "",
    caption_or_micro: str = "",
) -> Path:
    """按版式类型调度渲染器。"""
    k = normalize_variant_key(variant)
    info = LAYOUT_CN_REGISTRY[k]
    t = title or info["default_title"]
    l = latin or info["default_latin"]
    c = caption_or_micro or info["default_caption"]
    return info["func"](src=src, out=out, title=t, latin=l, caption=c)


def render_all_layouts(
    src: Path | str,
    out_dir: Path | str,
    title: str = "",
    latin: str = "",
    caption: str = "",
) -> dict[str, Path]:
    """批量渲染全部三种版式到指定目录。"""
    out_d = Path(out_dir)
    out_d.mkdir(parents=True, exist_ok=True)
    results: dict[str, Path] = {}
    for k, info in LAYOUT_CN_REGISTRY.items():
        dst = out_d / info["default_filename"]
        results[k] = info["func"](
            src=src,
            out=dst,
            title=title or info["default_title"],
            latin=latin or info["default_latin"],
            caption=caption or info["default_caption"],
        )
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Agnes Studio 7/8/9 版式精修与中文排版渲染器"
    )
    parser.add_argument(
        "--variant",
        choices=["07", "08", "09", "all"],
        default="all",
        help="目标版式编号 (07, 08, 09 或 all)",
    )
    parser.add_argument(
        "--src",
        "--input",
        dest="src",
        type=str,
        default=None,
        help="底图文件路径",
    )
    parser.add_argument(
        "--out",
        "--output",
        dest="out",
        type=str,
        default=None,
        help="输出图片路径或目录",
    )
    parser.add_argument("--title", type=str, default=None, help="自定义中文标题")
    parser.add_argument("--latin", type=str, default=None, help="自定义西文副标")
    parser.add_argument("--caption", type=str, default=None, help="自定义注脚/微文案")
    parser.add_argument(
        "--batch",
        action="store_true",
        help="运行完整批处理流程 (含默认配图与预设文案)",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="调用网关自主生成人物原图 (需网关可用)",
    )

    args = parser.parse_args(argv)

    try:
        # 1. 尝试网关生成
        report: list[dict] = []
        if args.generate:
            if not generate or not save_image:
                print("⚠️ agnes_gateway 不可用，跳过生成步骤", file=sys.stderr)
            else:
                for stem, prompt in SHOTS:
                    fp = OUT / f"{stem}.png"
                    if fp.exists() and fp.stat().st_size > 20_000:
                        print("SKIP gen", stem)
                        report.append({"stem": stem, "ok": True, "skipped": True})
                        continue
                    r = generate(prompt, size="864x1152", model="agnes-image-2.5-flash", retries=3)
                    if r.get("ok"):
                        save_image(r, fp)
                        print("OK gen", stem, fp.stat().st_size // 1024)
                        report.append({"stem": stem, "ok": True})
                    else:
                        print("FAIL gen", stem, str(r)[:120], file=sys.stderr)
                        report.append({"stem": stem, "ok": False, "err": str(r)[:200]})

        # 2. 底图定位
        src_path: Path | None = None
        if args.src:
            src_path = Path(args.src)
            if not src_path.is_file():
                print(f"❌ 找不到底图文件: {args.src}", file=sys.stderr)
                return 1
        else:
            candidates = [
                OUT / "07a_portrait.png",
                ROOT / "public" / "assets" / "poster_style_wenkai.png",
                ROOT / "public" / "assets" / "macro_beauty_02.png",
            ]
            for c in candidates:
                if c.is_file():
                    src_path = c
                    break

        # 3. 执行排版合成
        if args.batch:
            jobs = [
                ("07a_portrait.png", "07A_CN_留白.png", "留白", "THE WHITE", "把空气留给呼吸"),
                ("07b_portrait.png", "07B_CN_观景.png", "观景", "THE VIEW", "窗里有风经过"),
                ("08a_portrait.png", "08A_CN_静物.png", "静物", "STILL LIFE", "安静是最好的滤镜"),
                ("08b_portrait.png", "08B_CN_见山.png", "见山", "SEE MOUNTAIN", "看见即抵达"),
                ("09a_portrait.png", "09A_CN_独白.png", "独白", "MONOLOGUE", "一个人的完整场"),
                ("09b_portrait.png", "09B_CN_自在.png", "自在", "AT EASE", "不必满，不必急"),
            ]
            for src_name, dst_name, title, latin, caption in jobs:
                cur_src = (OUT / src_name) if (OUT / src_name).is_file() else src_path
                if not cur_src or not cur_src.is_file():
                    print("MISS src for", dst_name)
                    continue
                dst = OUT / dst_name
                if dst_name.startswith("07"):
                    compose_07(cur_src, dst, title, latin, caption)
                elif dst_name.startswith("08"):
                    compose_08(cur_src, dst, title, latin, caption)
                else:
                    compose_09(cur_src, dst, title, latin, caption)

            (OUT / "batch_report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print("DONE")
            return 0

        # 单项或全量渲染
        if not src_path or not src_path.is_file():
            print("❌ 未提供底图且未检测到默认底图", file=sys.stderr)
            return 1

        target_out_dir = Path(args.out) if args.out else OUT
        if args.variant == "all":
            render_all_layouts(
                src=src_path,
                out_dir=target_out_dir,
                title=args.title or "",
                latin=args.latin or "",
                caption=args.caption or "",
            )
            return 0

        # 指定具体 variant
        k = normalize_variant_key(args.variant)
        out_target = (
            Path(args.out)
            if (args.out and not Path(args.out).is_dir())
            else (target_out_dir / LAYOUT_CN_REGISTRY[k]["default_filename"])
        )
        render_layout_cn(
            variant=k,
            src=src_path,
            out=out_target,
            title=args.title or "",
            latin=args.latin or "",
            caption_or_micro=args.caption or "",
        )
        return 0

    except Exception as e:
        print(f"❌ 执行失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
