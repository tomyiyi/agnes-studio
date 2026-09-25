#!/usr/bin/env python3
"""7/8/9 版式精修：人物放大 + 中文高级字设（真字体后期叠字）。

- 7 杂志开窗：大图窗 + 左竖排中文书脊
- 8 杂志开窗·b：偏心大窗 + 中文题
- 9 独主体大空场：人物放大 + 中文巨字留白
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from agnes_gateway import generate, save_image  # noqa: E402

OUT = ROOT / "outputs" / "layout_variants" / "L2"
OUT.mkdir(parents=True, exist_ok=True)

FONTS = ROOT / "public" / "fonts"
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


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def paste_rgba(base: Image.Image, overlay: Image.Image, xy: tuple[int, int]) -> None:
    base.paste(overlay, xy, overlay)


def text_rgba(
    size: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
    *,
    tracking: int = 0,
    vertical: bool = False,
) -> Image.Image:
    """Render text to transparent layer; optional letter-spacing / vertical CJK."""
    w, h = size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if vertical:
        y = 0
        for ch in text:
            bbox = d.textbbox((0, 0), ch, font=fnt)
            cw, chh = bbox[2] - bbox[0], bbox[3] - bbox[1]
            d.text(((w - cw) / 2 - bbox[0], y - bbox[1]), ch, font=fnt, fill=fill)
            y += chh + tracking + int(fnt.size * 0.12)
    else:
        x = 0
        for ch in text:
            bbox = d.textbbox((0, 0), ch, font=fnt)
            d.text((x - bbox[0], -bbox[1]), ch, font=fnt, fill=fill)
            x += bbox[2] - bbox[0] + tracking
    return layer


def measure(text: str, fnt: ImageFont.FreeTypeFont, tracking: int = 0) -> tuple[int, int]:
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    w = 0
    h = 0
    for ch in text:
        bbox = d.textbbox((0, 0), ch, font=fnt)
        w += bbox[2] - bbox[0] + tracking
        h = max(h, bbox[3] - bbox[1])
    return max(w - tracking, 1), max(h, 1)


def compose_07(src: Path, out: Path, title: str, latin: str, caption: str) -> None:
    """杂志开窗：大图窗居中偏上 + 左竖排中文书脊 + 窗下 caption。"""
    W, H = 864, 1152
    # paper field
    canvas = Image.new("RGBA", (W, H), (242, 236, 226, 255))  # ivory paper
    # photo window: LARGER than L1 (was ~mid). now 72% width, 52% height
    win_w, win_h = int(W * 0.72), int(H * 0.52)
    win_x, win_y = int(W * 0.18), int(H * 0.16)  # leave left spine + bottom caption
    photo = Image.open(src).convert("RGB")
    # cover crop
    pw, ph = photo.size
    scale = max(win_w / pw, win_h / ph)
    photo = photo.resize((int(pw * scale), int(ph * scale)), Image.LANCZOS)
    # center crop
    left = (photo.width - win_w) // 2
    # bias slightly up for face
    top = max(0, (photo.height - win_h) // 2 - int(photo.height * 0.06))
    photo = photo.crop((left, top, left + win_w, top + win_h))
    canvas.paste(photo, (win_x, win_y))

    # thin window rule
    d = ImageDraw.Draw(canvas)
    d.rectangle([win_x, win_y, win_x + win_w, win_y + win_h], outline=(40, 36, 32, 90), width=1)

    # left vertical Chinese spine title — monumental serif
    f_title = font(SERIF_BLACK, 64)
    # vertical stack
    ty = int(H * 0.20)
    for ch in title:
        layer = Image.new("RGBA", (80, 90), (0, 0, 0, 0))
        dd = ImageDraw.Draw(layer)
        bbox = dd.textbbox((0, 0), ch, font=f_title)
        dd.text(((80 - (bbox[2] - bbox[0])) / 2 - bbox[0], 0 - bbox[1]), ch, font=f_title, fill=(28, 24, 20, 255))
        paste_rgba(canvas, layer, (int(W * 0.055), ty))
        ty += 78

    # tiny latin vertical-ish label under spine
    f_lat = font(LATIN_DIDOT if LATIN_DIDOT.exists() else LATIN_BODONI, 13)
    d.text((int(W * 0.065), ty + 12), latin, font=f_lat, fill=(90, 80, 70, 220))

    # caption under window
    f_cap = font(PUHUI_M, 15)
    d.text((win_x, win_y + win_h + 18), caption, font=f_cap, fill=(70, 62, 54, 230))
    # micro index
    f_micro = font(LATIN_FUTURA if LATIN_FUTURA.exists() else f_cap, 12)
    d.text((win_x + win_w - 40, win_y + win_h + 20), "07", font=f_micro, fill=(120, 108, 96, 200))
    # one hairline
    d.line([win_x, win_y + win_h + 48, win_x + win_w, win_y + win_h + 48], fill=(90, 80, 70, 120), width=1)

    canvas.convert("RGB").save(out, quality=93)
    print("OK compose", out.name)


def compose_08(src: Path, out: Path, title: str, latin: str, caption: str) -> None:
    """杂志开窗·b：偏心大窗 + 中文横题（字大、字距开）。"""
    W, H = 864, 1152
    canvas = Image.new("RGBA", (W, H), (236, 228, 216, 255))
    d = ImageDraw.Draw(canvas)

    # big off-center window — even larger person crop
    win_w, win_h = int(W * 0.78), int(H * 0.58)
    win_x, win_y = int(W * 0.14), int(H * 0.28)
    photo = Image.open(src).convert("RGB")
    pw, ph = photo.size
    scale = max(win_w / pw, win_h / ph)
    photo = photo.resize((int(pw * scale), int(ph * scale)), Image.LANCZOS)
    left = (photo.width - win_w) // 2
    top = max(0, (photo.height - win_h) // 2 - int(photo.height * 0.05))
    photo = photo.crop((left, top, left + win_w, top + win_h))
    canvas.paste(photo, (win_x, win_y))
    d.rectangle([win_x, win_y, win_x + win_w, win_y + win_h], outline=(50, 42, 36, 80), width=1)

    # horizontal Chinese title — large, wide tracking, top left
    f_title = font(SERIF_BLACK, 92)
    tracking = 18
    tw, th = measure(title, f_title, tracking)
    layer = text_rgba((tw + 20, th + 20), title, f_title, (32, 28, 24, 255), tracking=tracking)
    paste_rgba(canvas, layer, (int(W * 0.10), int(H * 0.10)))

    # latin subline
    f_lat = font(LATIN_DIDOT if LATIN_DIDOT.exists() else LATIN_BODONI, 16)
    d.text((int(W * 0.11), int(H * 0.10) + th + 28), latin, font=f_lat, fill=(96, 84, 72, 220))

    # caption under window
    f_cap = font(PUHUI_M, 15)
    d.text((win_x, win_y + win_h + 20), caption, font=f_cap, fill=(70, 62, 54, 230))
    f_micro = font(LATIN_FUTURA if LATIN_FUTURA.exists() else f_cap, 12)
    d.text((win_x + win_w - 36, win_y + win_h + 22), "08", font=f_micro, fill=(120, 108, 96, 200))

    # hairline under title
    d.line([int(W * 0.11), int(H * 0.10) + th + 56, int(W * 0.55), int(H * 0.10) + th + 56], fill=(90, 80, 70, 130), width=1)

    canvas.convert("RGB").save(out, quality=93)
    print("OK compose", out.name)


def compose_09(src: Path, out: Path, title: str, latin: str, micro: str) -> None:
    """独主体大空场：人物放大占右下，左上中文巨字 + 留白。"""
    W, H = 864, 1152
    canvas = Image.new("RGBA", (W, H), (232, 224, 212, 255))
    d = ImageDraw.Draw(canvas)

    # person block larger: 55% width, 62% height, lower-right third
    win_w, win_h = int(W * 0.55), int(H * 0.62)
    win_x, win_y = int(W * 0.38), int(H * 0.30)
    photo = Image.open(src).convert("RGB")
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
    # gaussian blur mask edges slightly
    from PIL import ImageFilter
    mask = mask.filter(ImageFilter.GaussianBlur(6))
    canvas.paste(photo, (win_x, win_y), mask)

    # monumental Chinese title upper-left — 2 chars huge
    f_title = font(SERIF_BLACK, 150)
    tracking = 12
    tw, th = measure(title, f_title, tracking)
    layer = text_rgba((tw + 30, th + 30), title, f_title, (28, 24, 20, 255), tracking=tracking)
    paste_rgba(canvas, layer, (int(W * 0.08), int(H * 0.10)))

    # thin latin
    f_lat = font(LATIN_DIDOT if LATIN_DIDOT.exists() else LATIN_BODONI, 15)
    d.text((int(W * 0.09), int(H * 0.10) + th + 24), latin, font=f_lat, fill=(88, 76, 64, 210))

    # tiny micro line bottom-left
    f_cap = font(PUHUI_M, 13)
    d.text((int(W * 0.09), int(H * 0.88)), micro, font=f_cap, fill=(100, 90, 80, 210))
    f_micro = font(LATIN_FUTURA if LATIN_FUTURA.exists() else f_cap, 12)
    d.text((int(W * 0.09), int(H * 0.91)), "09", font=f_micro, fill=(130, 118, 104, 180))
    # one vertical hairline
    d.line([int(W * 0.09), int(H * 0.82), int(W * 0.09), int(H * 0.86)], fill=(90, 80, 70, 140), width=1)

    canvas.convert("RGB").save(out, quality=93)
    print("OK compose", out.name)


def main() -> None:
    report = []
    # 1) generate larger-person portraits
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
            print("FAIL gen", stem, str(r)[:120])
            report.append({"stem": stem, "ok": False, "err": str(r)[:200]})

    # 2) compose Chinese typography
    jobs = [
        ("07a_portrait.png", "07A_CN_留白.png", "留白", "THE WHITE", "把空气留给呼吸"),
        ("07b_portrait.png", "07B_CN_观景.png", "观景", "THE VIEW", "窗里有风经过"),
        ("08a_portrait.png", "08A_CN_静物.png", "静物", "STILL LIFE", "安静是最好的滤镜"),
        ("08b_portrait.png", "08B_CN_见山.png", "见山", "SEE MOUNTAIN", "看见即抵达"),
        ("09a_portrait.png", "09A_CN_独白.png", "独白", "MONOLOGUE", "一个人的完整场"),
        ("09b_portrait.png", "09B_CN_自在.png", "自在", "AT EASE", "不必满，不必急"),
    ]
    for src_name, dst_name, title, latin, caption in jobs:
        src = OUT / src_name
        dst = OUT / dst_name
        if not src.exists():
            print("MISS", src_name)
            continue
        if dst.exists() and dst.stat().st_size > 20_000:
            print("SKIP compose", dst_name)
            continue
        if dst_name.startswith("07"):
            compose_07(src, dst, title, latin, caption)
        elif dst_name.startswith("08"):
            compose_08(src, dst, title, latin, caption)
        else:
            compose_09(src, dst, title, latin, caption)

    (OUT / "batch_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DONE")


if __name__ == "__main__":
    main()
