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


def classify_generation_error(error: object) -> str:
    """将网关/认证/业务失败分层，避免报告把 502 误报成版式生图失败。"""
    text = str(error or "").lower()
    if "http 502" in text or "bad gateway" in text:
        return "gateway_502"
    if any(token in text for token in ("http 401", "http 403", "unauthorized", "forbidden", "token_rejected")):
        return "auth"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    return "generation_error"

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
    quiet: bool = False,
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
    if not quiet:
        print("OK compose", out_p.name)
    return out_p


def compose_08(
    src: Path | str,
    out: Path | str,
    title: str = "静物",
    latin: str = "STILL LIFE",
    caption: str = "安静是最好的滤镜",
    quiet: bool = False,
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
    if not quiet:
        print("OK compose", out_p.name)
    return out_p


def compose_09(
    src: Path | str,
    out: Path | str,
    title: str = "独白",
    latin: str = "MONOLOGUE",
    micro: str = "一个人的完整场",
    caption: str | None = None,
    quiet: bool = False,
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
    if not quiet:
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


def list_layout_cn_variants() -> list[dict[str, Any]]:
    """返回 7/8/9 版式规格清单列表。"""
    res = []
    for k, info in sorted(LAYOUT_CN_REGISTRY.items()):
        res.append({
            "key": k,
            "name": info["name"],
            "default_title": info["default_title"],
            "default_latin": info["default_latin"],
            "default_caption": info["default_caption"],
            "default_filename": info["default_filename"],
        })
    return res


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
    quiet: bool = False,
) -> Path:
    """按版式类型调度渲染器。"""
    k = normalize_variant_key(variant)
    info = LAYOUT_CN_REGISTRY[k]
    t = title or info["default_title"]
    l = latin or info["default_latin"]
    c = caption_or_micro or info["default_caption"]
    return info["func"](src=src, out=out, title=t, latin=l, caption=c, quiet=quiet)


def render_all_layouts(
    src: Path | str,
    out_dir: Path | str,
    title: str = "",
    latin: str = "",
    caption: str = "",
    quiet: bool = False,
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
            quiet=quiet,
        )
    return results


def generate_layout_shot(
    stem: str,
    prompt: str,
    out_dir: Path | str | None = None,
    size: str = "864x1152",
    model: str = "agnes-image-2.5-flash",
    retries: int = 3,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Any = None,
    save_image_fn: Any = None,
) -> dict[str, Any]:
    """生成单张版式底图人物摄影样张。"""
    if not stem or not str(stem).strip():
        err = "Stem cannot be empty"
        return {
            "stem": str(stem) if stem is not None else "",
            "ok": False,
            "err": err,
            "error_class": classify_generation_error(err),
        }
    if not prompt or not str(prompt).strip():
        err = "Prompt cannot be empty"
        return {
            "stem": str(stem),
            "ok": False,
            "err": err,
            "error_class": classify_generation_error(err),
        }

    stem_clean = str(stem).strip()
    target_dir = Path(out_dir) if out_dir else OUT
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{stem_clean}.png"

    if target_path.is_file() and not force:
        size_bytes = target_path.stat().st_size
        if size_bytes > 20_000:
            return {
                "stem": stem_clean,
                "ok": True,
                "skipped": True,
                "path": str(target_path),
                "size_kb": size_bytes // 1024,
            }

    if dry_run:
        return {
            "stem": stem_clean,
            "ok": True,
            "dry_run": True,
            "path": str(target_path),
            "size_kb": 0,
        }

    gen = generate_fn or generate
    saver = save_image_fn or save_image

    if not callable(gen):
        err = "agnes_gateway.generate is not available or not callable"
        return {
            "stem": stem_clean,
            "ok": False,
            "err": err,
            "error_class": classify_generation_error(err),
        }

    try:
        r = gen(prompt, size=size, model=model, retries=retries)
        if isinstance(r, dict) and r.get("ok"):
            if callable(saver):
                saver(r, target_path)
            size_kb = target_path.stat().st_size // 1024 if target_path.exists() else 0
            return {
                "stem": stem_clean,
                "ok": True,
                "path": str(target_path),
                "size_kb": size_kb,
            }
        else:
            err_msg = (
                r.get("error")
                if isinstance(r, dict) and r.get("error")
                else (str(r)[:200] if r is not None else "Empty response")
            )
            return {
                "stem": stem_clean,
                "ok": False,
                "err": err_msg or "Unknown generation error",
                "error_class": classify_generation_error(err_msg),
            }
    except Exception as exc:
        return {
            "stem": stem_clean,
            "ok": False,
            "err": str(exc),
            "error_class": classify_generation_error(exc),
        }


def run_batch_generate_shots(
    out_dir: Path | str | None = None,
    shots: list[tuple[str, str]] | None = None,
    size: str = "864x1152",
    model: str = "agnes-image-2.5-flash",
    retries: int = 3,
    force: bool = False,
    dry_run: bool = False,
    generate_fn: Any = None,
    save_image_fn: Any = None,
) -> list[dict[str, Any]]:
    """批量生成 7/8/9 版式人物摄影底图。"""
    target_dir = Path(out_dir) if out_dir else OUT
    target_dir.mkdir(parents=True, exist_ok=True)
    report: list[dict[str, Any]] = []
    target_shots = shots or SHOTS

    for stem, prompt in target_shots:
        res = generate_layout_shot(
            stem=stem,
            prompt=prompt,
            out_dir=target_dir,
            size=size,
            model=model,
            retries=retries,
            force=force,
            dry_run=dry_run,
            generate_fn=generate_fn,
            save_image_fn=save_image_fn,
        )
        report.append(res)
        if res.get("skipped"):
            print("SKIP gen", stem)
        elif res.get("ok"):
            sz = res.get("size_kb", 0)
            print("OK gen", stem, sz if sz else "(dry_run)" if dry_run else "")
        else:
            print("FAIL gen", stem, str(res.get("err", ""))[:120], file=sys.stderr)

    return report


def build_arg_parser() -> argparse.ArgumentParser:
    """构建 7/8/9 版式精修与中文排版渲染器命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="Agnes Studio 7/8/9 版式精修与中文排版渲染器 (Layout CN 07/08/09 Engine)"
    )
    parser.add_argument(
        "--variant",
        choices=["07", "08", "09", "all"],
        default="all",
        help="目标版式编号: 07 (杂志开窗), 08 (偏心大窗), 09 (独主体大空场), 或 all (全部)",
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
        "--list",
        "-l",
        action="store_true",
        help="列出所有可用的 7/8/9 版式规格及预设参数",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="调用网关自主生成人物原图 (需网关可用)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅演练生图流程，不发起实际网络请求",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新生成底图，即使已存在",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出版式规格清单或渲染结果报告",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="静默模式，抑制控制台标准输出",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：遇到底图缺失或执行异常时返回退出码 1",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # 1. 响应 --list
    if args.list:
        variants = list_layout_cn_variants()
        if args.json:
            print(json.dumps(variants, ensure_ascii=False, indent=2))
        elif not args.quiet:
            print("Agnes Studio · 7/8/9 经典中文版式清单:")
            for v in variants:
                print(
                    f"  [{v['key']}] {v['name']} -> "
                    f"默认: 《{v['default_title']}》/ {v['default_latin']} ({v['default_filename']})"
                )
        return 0

    try:
        # 2. 尝试网关生成
        report: list[dict] = []
        if args.generate:
            if not args.dry_run and (not generate or not save_image):
                if not args.quiet and not args.json:
                    print("⚠️ agnes_gateway 不可用，跳过生成步骤", file=sys.stderr)
            else:
                report = run_batch_generate_shots(
                    out_dir=OUT,
                    force=args.force,
                    dry_run=args.dry_run,
                )

        # 3. 底图定位
        src_path: Path | None = None
        if args.src:
            src_path = Path(args.src)
            if not src_path.is_file():
                if not args.quiet and not args.json:
                    print(f"❌ 找不到底图文件: {args.src}", file=sys.stderr)
                elif args.json:
                    print(json.dumps({"ok": False, "error": f"找不到底图文件: {args.src}"}, ensure_ascii=False))
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

        # 4. 执行排版合成
        inner_quiet = args.quiet or args.json
        if args.batch:
            jobs = [
                ("07a_portrait.png", "07A_CN_留白.png", "留白", "THE WHITE", "把空气留给呼吸"),
                ("07b_portrait.png", "07B_CN_观景.png", "观景", "THE VIEW", "窗里有风经过"),
                ("08a_portrait.png", "08A_CN_静物.png", "静物", "STILL LIFE", "安静是最好的滤镜"),
                ("08b_portrait.png", "08B_CN_见山.png", "见山", "SEE MOUNTAIN", "看见即抵达"),
                ("09a_portrait.png", "09A_CN_独白.png", "独白", "MONOLOGUE", "一个人的完整场"),
                ("09b_portrait.png", "09B_CN_自在.png", "自在", "AT EASE", "不必满，不必急"),
            ]
            rendered_jobs = []
            for src_name, dst_name, title, latin, caption in jobs:
                cur_src = (OUT / src_name) if (OUT / src_name).is_file() else src_path
                if not cur_src or not cur_src.is_file():
                    if not args.quiet and not args.json:
                        print("MISS src for", dst_name)
                    if args.strict:
                        if args.json:
                            print(json.dumps({"ok": False, "error": f"strict 模式下缺失底图: {src_name}"}, ensure_ascii=False))
                        return 1
                    continue
                dst = OUT / dst_name
                if dst_name.startswith("07"):
                    p = compose_07(cur_src, dst, title, latin, caption, quiet=inner_quiet)
                elif dst_name.startswith("08"):
                    p = compose_08(cur_src, dst, title, latin, caption, quiet=inner_quiet)
                else:
                    p = compose_09(cur_src, dst, title, latin, caption, quiet=inner_quiet)
                rendered_jobs.append(str(p))

            if args.strict and not rendered_jobs:
                if not args.quiet and not args.json:
                    print("❌ strict 模式下无任何底图可用，排版合成终止", file=sys.stderr)
                elif args.json:
                    print(json.dumps({"ok": False, "error": "strict 模式下无任何底图可用，排版合成终止"}, ensure_ascii=False))
                return 1

            (OUT / "batch_report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            if args.json:
                res_obj = {
                    "ok": True,
                    "batch": True,
                    "count": len(rendered_jobs),
                    "rendered": rendered_jobs,
                    "generation_report": report,
                }
                print(json.dumps(res_obj, ensure_ascii=False, indent=2))
            else:
                if not args.quiet:
                    print("DONE")
            return 0

        # 单项或全量渲染检查底图
        if not src_path or not src_path.is_file():
            if not args.quiet and not args.json:
                print("❌ 未提供底图且未检测到默认底图", file=sys.stderr)
            elif args.json:
                print(json.dumps({"ok": False, "error": "未提供底图且未检测到默认底图"}, ensure_ascii=False))
            return 1

        target_out_dir = Path(args.out) if args.out else OUT
        if args.variant == "all":
            all_rendered = render_all_layouts(
                src=src_path,
                out_dir=target_out_dir,
                title=args.title or "",
                latin=args.latin or "",
                caption=args.caption or "",
                quiet=inner_quiet,
            )
            if args.json:
                res_obj = {
                    "ok": True,
                    "variant": "all",
                    "src": str(src_path),
                    "results": {k: str(v) for k, v in all_rendered.items()},
                }
                print(json.dumps(res_obj, ensure_ascii=False, indent=2))
            return 0

        # 指定具体 variant
        k = normalize_variant_key(args.variant)
        out_target = (
            Path(args.out)
            if (args.out and not Path(args.out).is_dir())
            else (target_out_dir / LAYOUT_CN_REGISTRY[k]["default_filename"])
        )
        single_res = render_layout_cn(
            variant=k,
            src=src_path,
            out=out_target,
            title=args.title or "",
            latin=args.latin or "",
            caption_or_micro=args.caption or "",
            quiet=inner_quiet,
        )
        if args.json:
            res_obj = {
                "ok": True,
                "variant": k,
                "src": str(src_path),
                "output": str(single_res),
            }
            print(json.dumps(res_obj, ensure_ascii=False, indent=2))
        return 0

    except Exception as e:
        if not args.quiet and not args.json:
            print(f"❌ 执行失败: {e}", file=sys.stderr)
        elif args.json:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
