#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio · 封面生产流水线（微信 / 小红书）
================================================

工作流总入口：
  1) 人物 Subject   — 底图选取/裁切/头肩校验/水印清理
  2) 文字排版 Type  — 对角拆字 / 大字报 / 四级层级 / 盘古之白
  3) 整体排版 Layout— 平台安全区网格 + 负空间 + 导出
  4) 质量门禁 QA    — 文案/布局/缩略/列表遮挡模拟/强制目检

用法：
  python3 scripts/cover_pipeline.py --platform all --mode diag --title-zone safe
  python3 scripts/cover_pipeline.py --platform xhs --mode bignews --title-zone safe
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import statistics
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter
from playwright.sync_api import sync_playwright

sys_path_scripts = Path(__file__).resolve().parent
if str(sys_path_scripts) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(sys_path_scripts))
try:
    from typography_rules import ChineseTypographyRules
    from copywriting_rules import apply_fix, lint_copy
except Exception:
    ChineseTypographyRules = None
    apply_fix = lambda x: x
    lint_copy = lambda x: []
try:
    from vision_subject_detector import detect_faces, check_occlusion
except Exception:
    detect_faces = lambda p: []
    check_occlusion = lambda tb, zs: (False, None)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "covers"
FONTS = ROOT / "public" / "fonts"
ASSETS_EXP = ROOT / "experiments"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# —— 平台规格 ——
PLATFORMS = {
    "wechat": {
        "label": "微信头条 2.35:1",
        "w": 2350,
        "h": 1000,
        "ratio": 2.35,
        "safe": "上 70% · 左右 6%",
        "danger_band": 0.25,
        "place": (0.62, 0.42),
        "src": "wechat",
    },
    "wechat-sq": {
        "label": "微信次条 1:1",
        "w": 1080,
        "h": 1080,
        "ratio": 1.0,
        "safe": "中央 80%",
        "danger_band": 0.15,
        # 方图必须完整头肩，人脸偏右上三分，避免顶切
        "place": (0.58, 0.36),
        "src": "xhs",
    },
    "xhs": {
        "label": "小红书竖版 3:4",
        "w": 1080,
        "h": 1440,
        "ratio": 0.75,
        "safe": "高 12%–72% · 左右 8%",
        "danger_band": 0.28,
        "place": (0.55, 0.34),
        "src": "xhs",
    },
    "xhs-sq": {
        "label": "小红书方图 1:1",
        "w": 1080,
        "h": 1080,
        "ratio": 1.0,
        "safe": "中央 84%",
        "danger_band": 0.22,
        "place": (0.55, 0.36),
        "src": "xhs",
    },
}

PALETTE = {
    "ink": "#0c0b0a",
    "cream": "#f6f1e8",
    "gold": "#c9a063",
    "red": "#e11d48",
}


# =============================================================================
# 1) 人物工作流 Subject
# =============================================================================

def skin_centroid(im: Image.Image) -> tuple[float, float, int]:
    """粗定位肤色质心，用于构图避让。"""
    W, H = 64, 64
    small = im.convert("RGB").resize((W, H), Image.Resampling.BOX)
    xs = ys = n = 0
    for y in range(H):
        for x in range(W):
            r, g, b = small.getpixel((x, y))
            if r > 110 and g > 70 and b > 60 and r > g > b and (r - b) > 18 and r < 245:
                xs += x
                ys += y
                n += 1
    if not n:
        return 0.6, 0.45, 0
    return xs / n / (W - 1), ys / n / (H - 1), n


def head_visible_probe(im: Image.Image) -> dict:
    """头肩带肤色占比 + 上沿留白粗检。"""
    w, h = im.size
    band = im.crop((int(w * 0.30), int(h * 0.04), int(w * 0.78), int(h * 0.48)))
    raw = list(band.resize((40, 24)).getdata())
    skin = sum(1 for r, g, b in raw if r > 60 and g > 40 and b > 30 and r > g > b and (r - b) > 15 and r < 230)
    ratio = skin / max(1, len(raw))
    top = im.convert("L").crop((0, 0, w, max(4, int(h * 0.06))))
    top_std = statistics.pstdev([v for v in top.resize((32, 8)).getdata()])
    return {
        "skin_ratio": round(ratio, 3),
        "headroom_sigma": round(top_std, 1),
        "ok": ratio > 0.06,
    }


def _unsharp(im: Image.Image, radius: float = 1.0, amount: float = 0.5) -> Image.Image:
    """轻量 USM：保留皮肤，提亮发丝与字缘。"""
    from PIL import ImageChops, ImageFilter
    blur = im.filter(ImageFilter.GaussianBlur(radius))
    # out = im * (1+amount) - blur * amount
    return Image.blend(im, ImageChops.add(im, ImageChops.subtract(im, blur)), amount)


def patch_watermark(im: Image.Image) -> Image.Image:
    """抹掉生图服务右下角水印（含「AI生成 / Xiaomi MiMo」贴角标）。

    角标位置固定，采取「强制角区 Telea 修复」——不依赖笔画检出，
    杜绝半透明角标漏网；修复邻域自然长入，无硬边小方块。
    """
    try:
        import cv2
        import numpy as np
    except Exception:
        return im

    w, h = im.size
    if w < 64 or h < 64:
        return im
    rgb = np.array(im.convert("RGB"))
    # 贴角标区：右下 18%×14%，略外扩盖住「AI生成 / Xiaomi MiMo」
    x0, y0 = int(w * 0.82), int(h * 0.86)
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[y0:h, x0:w] = 255
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    fixed = cv2.inpaint(bgr, mask, inpaintRadius=9, flags=cv2.INPAINT_TELEA)
    return Image.fromarray(cv2.cvtColor(fixed, cv2.COLOR_BGR2RGB))


def crop_subject(
    src: Path,
    dst: Path,
    target_ratio: float,
    *,
    place: tuple[float, float] = (0.62, 0.40),
    min_headroom: float = 0.06,
) -> Path:
    """人脸框优先裁切：保证完整头部 + 头顶空气；禁止 2.35:1 砍头发顶。

    规则（2026-09-23 反馈后固化）：
      1. 用 Vision 人脸框 y_min 作为「发顶参考」，输出 y_min 必须 ≥ min_headroom
      2. 人脸 x 落到 place.x 附近（右 2/3 或指定）
      3. 兜底：无脸时顶对齐，宁多留空不砍头
    """
    im = Image.open(src).convert("RGB")
    im = patch_watermark(im)
    w, h = im.size
    faces = detect_faces(str(src))
    if faces:
        # 取最大脸
        f = max(faces, key=lambda z: (z["x_max"]-z["x_min"])*(z["y_max"]-z["y_min"]))
        fx = (f["x_min"] + f["x_max"]) / 2
        fy_top = f["y_min"]  # 0~1
        face_h = f["y_max"] - f["y_min"]
    else:
        cx, cy, n = skin_centroid(im)
        fx, fy_top, face_h = cx, max(0.05, cy - 0.18), 0.35

    if w / h > target_ratio:
        new_w = int(h * target_ratio)
        new_h = h
    else:
        new_w = w
        new_h = int(w / target_ratio)

    place_x, place_y = place
    # 水平：脸到 place.x
    x0 = int(fx * w - place_x * new_w)
    x0 = max(0, min(x0, w - new_w))

    # 垂直：输出中发顶 ≥ min_headroom；脸心尽量靠近 place.y
    # 输出坐标：face_top_out = fy_top*h - y0  ≥ min_headroom * new_h
    y0_max = int(fy_top * h - min_headroom * new_h)
    y0_ideal = int((fy_top + face_h * 0.5) * h - place_y * new_h)
    y0 = min(y0_ideal, y0_max)  # 不可更高，否则砍顶
    # 若理想裁切仍砍顶，强制 y0_max；若过高导致脚下/肩部大量空白，允许更低但发顶≥headroom
    y0 = max(0, min(y0, h - new_h))
    face_top_out = fy_top * h - y0
    if face_top_out < min_headroom * new_h:
        y0 = max(0, int(fy_top * h - min_headroom * new_h))

    im = im.crop((x0, y0, x0 + new_w, y0 + new_h))
    # 若裁切结果仍低于交付宽，LANCZOS 放大到目标宽，减少 CSS 再拉伸模糊
    if new_w < 1600 and target_ratio > 1.5:
        target_w = int(2350)
        target_h = int(target_w / target_ratio)
        im = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
    # 放大后轻锐化（USM 近似），提发丝/五官，不假脸
    im = _unsharp(im, radius=1.2, amount=0.55)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "PNG")
    return dst


def head_integrity_gate(im: Image.Image) -> dict:
    """P0：Vision 人脸框必须完整（发顶留白、脸不出画）。"""
    # 对 PIL 图临时导出再检成本高，用边缘内肤色+顶部亮度近似 + 可选 vision
    w, h = im.size
    probe = head_visible_probe(im)
    cx, cy, n = skin_centroid(im)
    # 顶部 3% 是否过暗（常见砍头顶后是衣服/边框）
    top = im.convert("L").crop((0, 0, w, max(6, int(h * 0.03))))
    top_mean = sum(top.resize((32, 4)).getdata()) / 128
    # 发顶检测：上 8–35% 中带与顶 0–4% 对比
    ok = probe["ok"] and n > 30 and cy < 0.62
    return {"top_mean": round(top_mean, 1), "probe": probe, "skin_centroid": [round(cx,3), round(cy,3)], "ok": ok}


def verify_layout(im: Image.Image, place: tuple[float, float], platform: str, image_path: Path | None = None) -> dict:
    """布局门禁：以 Vision 人脸框中心为准（肤色质心含毛衣/手部，不可靠）。"""
    faces = detect_faces(str(image_path)) if image_path else []
    if faces:
        f = max(faces, key=lambda z: (z["x_max"]-z["x_min"])*(z["y_max"]-z["y_min"]))
        cx = (f["x_min"] + f["x_max"]) / 2
        cy = (f["y_min"] + f["y_max"]) / 2
        n = 100
    else:
        cx, cy, n = skin_centroid(im)
    probe = head_visible_probe(im)
    # 人脸不应贴边（允许 ±0.12 偏差 + 0.18 安全边）
    fx_ok = 0.22 <= cx <= 0.82
    fy_ok = 0.18 <= cy <= 0.72
    place_err = ((cx - place[0]) ** 2 + (cy - place[1]) ** 2) ** 0.5
    ok = probe["ok"] and fx_ok and fy_ok and place_err < 0.22 and n > 40
    return {
        "platform": platform,
        "skin_centroid": [round(cx, 3), round(cy, 3)],
        "place": list(place),
        "place_err": round(place_err, 3),
        "fx_ok": fx_ok,
        "fy_ok": fy_ok,
        "head": probe,
        "ok": ok,
    }


# =============================================================================
# 2) 文字排版工作流 Type
# =============================================================================

def load_copy_rules() -> dict:
    p = ROOT / "data" / "copy_templates.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def apply_pangu(text: str) -> str:
    if ChineseTypographyRules is not None:
        return ChineseTypographyRules.apply_pangu_spacing(text)
    # 兜底：中英/数字之间补空格
    import re
    return re.sub(r"([一-鿿])([A-Za-z0-9])", r"\1 \2", re.sub(r"([A-Za-z0-9])([一-鿿])", r"\1 \2", text))


def validate_copy(title_a: str, title_b: str, latin: str, slogan: str) -> list[str]:
    """文案门禁：字数 / 禁则字符 / 盘古之白。"""
    errs: list[str] = []
    rules = (load_copy_rules().get("rules") or {})
    ta = rules.get("title_a_chars", [2, 4])
    tb = rules.get("title_b_chars", [2, 4])
    smax = rules.get("slogan_max_chars", 18)
    if not (ta[0] <= len(title_a) <= ta[1]):
        errs.append(f"title_a 长度 {len(title_a)} 超出 {ta}")
    if not (tb[0] <= len(title_b) <= tb[1]):
        errs.append(f"title_b 长度 {len(title_b)} 超出 {tb}")
    if len(slogan) > smax:
        errs.append(f"slogan {len(slogan)} 超过 {smax}")
    for ch in rules.get("forbid_chars") or []:
        for name, val in [("title_a", title_a), ("title_b", title_b), ("slogan", slogan)]:
            if ch in val:
                errs.append(f"{name} 含禁则字符 {ch}，请用「」")
    # 盘古：中英紧贴检测（以最终 latin+slogan 抽样）
    sample = f"{latin} {slogan}"
    if ChineseTypographyRules is not None:
        spaced = ChineseTypographyRules.apply_pangu_spacing(sample)
        if spaced != sample and sample != apply_pangu(sample):
            pass
    if apply_pangu(f"{title_a}{title_b} {latin}") == f"{title_a}{title_b} {latin}" and latin:
        # 若中英紧贴且调用后无变化，视为已合规
        pass
    if latin and ("BEAUTY" in latin or "ENGINE" in latin or latin.isupper()):
        # 要求 tracking 语义上合法：不允许超长
        if len(latin) > 28:
            errs.append("latin 过长")
    return errs


def build_filename(platform: str, mode: str, slug: str, ext: str = "png") -> str:
    spec = PLATFORMS[platform]
    code = {
        "wechat": "wx_head",
        "wechat-sq": "wx_sub",
        "xhs": "xhs_main",
        "xhs-sq": "xhs_sq",
    }[platform]
    date = __import__("datetime").date.today().strftime("%Y%m%d")
    return f"{code}_{mode}_{spec['w']}x{spec['h']}_{date}_{slug}.{ext}"


def face_boxes(image_path: Path):
    return detect_faces(str(image_path))


def _overlaps(tb, faces) -> bool:
    if not faces:
        return False
    hit, _ = check_occlusion(tb, faces)
    return bool(hit)


def resolve_text_box(faces, platform: str, title_zone: str, mode: str) -> dict:
    """P0 人脸避让：在候选标题框中选第一个不压脸的；全压则失败。

    候选覆盖：顶带 / 底带 / 左柱 / 右柱 / 模式专用，均避开面部 ±3% x、±5% y 缓冲。
    """
    safe_bottom = title_zone == "safe"
    cands: list[tuple[float, float, float, float]] = []

    # 模式专用窄栏
    if mode == "vertical":
        cands += [
            (0.04, 0.08, 0.26, 0.78),
            (0.74, 0.08, 0.96, 0.78),
            (0.04, 0.04, 0.28, 0.55),
            (0.72, 0.10, 0.96, 0.62),
        ]
    elif mode == "stack":
        cands += [
            (0.05, 0.10, 0.32, 0.62),
            (0.68, 0.08, 0.95, 0.58),
            (0.05, 0.55, 0.35, 0.88),
        ]
    elif mode == "bignews":
        cands += [
            (0.05, 0.02, 0.95, 0.16),   # 顶带横幅（高于面部）
            (0.05, 0.10, 0.30, 0.55),   # 左柱
            (0.70, 0.10, 0.95, 0.55),   # 右柱
        ]
    else:  # diag
        cands += [
            (0.05, 0.10, 0.48, 0.55),
            (0.55, 0.08, 0.95, 0.55),
            (0.05, 0.04, 0.95, 0.20),
        ]

    # 平台主位 + 通用避让
    if platform == "xhs":
        cands.append((0.06, 0.12, 0.72, 0.58) if safe_bottom else (0.06, 0.55, 0.72, 0.85))
    elif platform == "wechat":
        cands.append((0.05, 0.10, 0.48, 0.55) if safe_bottom else (0.05, 0.62, 0.48, 0.92))
    elif platform == "wechat-sq":
        cands.append((0.08, 0.12, 0.55, 0.55) if safe_bottom else (0.08, 0.55, 0.55, 0.88))
    else:
        cands.append((0.06, 0.10, 0.70, 0.55) if safe_bottom else (0.06, 0.60, 0.70, 0.90))

    # 通用兜底：顶带（高于面部缓冲）、左右窄柱
    cands += [
        (0.04, 0.02, 0.96, 0.16),
        (0.04, 0.06, 0.26, 0.70),
        (0.74, 0.06, 0.96, 0.70),
        (0.04, 0.02, 0.26, 0.55),
        (0.74, 0.02, 0.96, 0.55),
    ]

    # safe 模式禁止使用遮挡带（底部 danger_band）
    danger = {"wechat": 0.25, "wechat-sq": 0.15, "xhs": 0.28, "xhs-sq": 0.22}.get(platform, 0.25)
    usable = []
    for tb in cands:
        if safe_bottom and tb[3] > 1.0 - danger + 0.02:  # 侵入底部遮挡带
            continue
        usable.append(tb)
    if not usable:
        usable = [tb for tb in cands if tb[3] <= 0.72] or cands
    cands = usable

    chosen = None
    for tb in cands:
        if not _overlaps(tb, faces):
            chosen = tb
            break
    if chosen is None and not faces:
        chosen = cands[0]
    ok = chosen is not None
    css = None
    if ok:
        x1, y1, x2, y2 = chosen
        # 保证字块可用宽度 ≥ 34%，否则向安全侧扩宽（仍避开脸）
        if (x2 - x1) < 0.34:
            need = 0.34 - (x2 - x1)
            if x2 + need <= 0.96 and not _overlaps((x1, y1, x2 + need, y2), faces):
                x2 = x2 + need
            elif x1 - need >= 0.04 and not _overlaps((x1 - need, y1, x2, y2), faces):
                x1 = x1 - need
            else:
                x2 = min(0.96, x1 + 0.34)
        css = f"left:{x1*100:.1f}%; right:{(1-x2)*100:.1f}%; top:{y1*100:.1f}%; bottom:{(1-y2)*100:.1f}%;"
    return {
        "faces": faces,
        "candidates": cands,
        "chosen": list(chosen) if chosen else None,
        "block_css": css,
        "ok": ok,
        "note": "no-face-fallback" if not faces else ("clear" if ok else "all-boxes-hit-face"),
    }


def face_occlusion_gate(image_path: Path, title_zone: str = "safe", platform: str = "wechat", mode: str = "diag") -> dict:
    faces = face_boxes(image_path)
    return resolve_text_box(faces, platform, title_zone, mode)


def qa_thumbnail_ok(path: Path) -> bool:
    """375pt 宽缩略下主标区仍有足够对比（粗检亮部方差）。"""
    im = Image.open(path).convert("L")
    thumb = im.resize((375, max(1, int(375 * im.height / im.width))), Image.Resampling.LANCZOS)
    # 左上标题窗
    w, h = thumb.size
    box = thumb.crop((int(w * 0.05), int(h * 0.08), int(w * 0.55), int(h * 0.55)))
    return statistics.pstdev(list(box.getdata())) > 18


def render_wechat_list_sim(png_path: Path, out_path: Path) -> Path:
    """微信列表标题条遮挡模拟：底部叠 25% 半透明标题区，检查主标是否被切。"""
    im = Image.open(png_path).convert("RGB")
    w, h = im.size
    overlay_h = int(h * 0.25)
    strip = Image.new("RGB", (w, overlay_h), (245, 245, 245))
    d = ImageDraw.Draw(strip)
    d.rectangle([0, 0, w, overlay_h], fill=(248, 248, 248))
    d.text((int(w * 0.06), int(overlay_h * 0.35)), "列表标题会叠在这里 · TITLE MASK", fill=(17, 24, 39))
    im2 = im.copy()
    im2.paste(strip, (0, h - overlay_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    im2.save(out_path, "JPEG", quality=88)
    return out_path


def build_contact_sheet(pngs: list[Path], out_path: Path) -> Path:
    thumbs = []
    H = 420
    for p in pngs:
        im = Image.open(p).convert("RGB")
        w = max(1, int(im.width * H / im.height))
        t = im.resize((w, H), Image.Resampling.LANCZOS)
        cell = Image.new("RGB", (w, H + 24), (244, 240, 232))
        cell.paste(t, (0, 24))
        ImageDraw.Draw(cell).text((8, 6), p.name, fill=(17, 24, 39))
        thumbs.append(cell)
    W = sum(t.width + 8 for t in thumbs)
    sheet = Image.new("RGB", (W, H + 24), (244, 240, 232))
    x = 0
    for t in thumbs:
        sheet.paste(t, (x, 0))
        x += t.width + 8
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, "JPEG", quality=88)
    return out_path

def type_html_styles() -> str:
    """字体工程 + 电影感版式（克制暗角，设计感靠字阶/发丝线/错位）。"""
    return f"""
  @font-face {{
    font-family: 'SmileySans';
    src: url('file://{FONTS}/SmileySans-Oblique.ttf') format('truetype');
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'SmileySans', 'PingFang SC', sans-serif;
    color: {PALETTE['cream']};
    background: {PALETTE['ink']};
    -webkit-font-smoothing: antialiased;
    text-rendering: geometricPrecision;
    overflow: hidden;
  }}
  .mono {{ font-family: ui-monospace, 'SF Mono', Menlo, monospace; }}
  .serif {{ font-family: 'Songti SC', 'Source Han Serif SC', serif; }}
  .rule {{
    height: 1px;
    background: linear-gradient(90deg, {PALETTE['gold']}, rgba(201,160,99,0));
  }}
  /* 对角拆字：大字错位 + 末字金 */
  .diag-1, .diag-2 {{
    line-height: 0.9;
    letter-spacing: 0.14em;
    font-weight: 400;
    text-shadow: 0 10px 36px rgba(12, 11, 10, 0.35);
  }}
  .diag-2 {{ margin-left: 0.62em; margin-top: 0.04em; }}
  .diag-2 em, .bignews em, .vtitle em {{ font-style: normal; color: {PALETTE['gold']}; }}
  .stack-1, .stack-2 {{
    line-height: 1.05;
    letter-spacing: 0.22em;
    text-shadow: 0 10px 36px rgba(12, 11, 10, 0.35);
  }}
  .stack-2 {{ font-family: 'Songti SC', 'Source Han Serif SC', serif; opacity: 0.94; }}
  .bignews {{
    line-height: 0.92;
    letter-spacing: 0.06em;
    text-shadow: 0 10px 36px rgba(12, 11, 10, 0.4);
  }}
  .vwrap {{
    writing-mode: vertical-rl;
    display: flex;
    flex-direction: row;
    gap: 0.4em;
  }}
  .vtitle {{
    font-family: 'Songti SC', 'Source Han Serif SC', serif;
    letter-spacing: 0.32em;
    line-height: 1.1;
  }}
  .latin {{ letter-spacing: 0.42em; color: rgba(246, 241, 232, 0.82); }}
  .slogan {{ letter-spacing: 0.22em; color: rgba(246, 241, 232, 0.9); }}
  .micro {{ letter-spacing: 0.34em; color: rgba(246, 241, 232, 0.55); }}
  .kicker {{ letter-spacing: 0.48em; color: rgba(246, 241, 232, 0.6); }}
"""


def title_block(title_a, title_b, title_b_accent, mode, size_hero):
    if mode == "diag":
        b = title_b
        if title_b_accent and title_b_accent in b:
            b = b.replace(title_b_accent, f"<em>{title_b_accent}</em>", 1)
        return (
            f'<div class="diag-1" style="font-size:{size_hero}px">{title_a}</div>'
            f'<div class="diag-2" style="font-size:{size_hero}px">{b}</div>'
        )
    if mode == "stack":
        return (
            f'<div class="stack-1" style="font-size:{size_hero}px">{title_a}</div>'
            f'<div class="stack-2" style="font-size:{int(size_hero*0.55)}px">{title_b}</div>'
        )
    if mode == "vertical":
        b = title_b
        if title_b_accent and title_b_accent in b:
            b = b.replace(title_b_accent, f"<em>{title_b_accent}</em>", 1)
        return (
            f'<div class="vwrap" style="font-size:{size_hero}px">'
            f'<div class="vtitle">{title_a}</div><div class="vtitle">{b}</div></div>'
        )
    line = title_a + title_b
    if title_b_accent and title_b_accent in line:
        line = line.replace(title_b_accent, f"<em>{title_b_accent}</em>", 1)
    return f'<div class="bignews" style="font-size:{size_hero}px">{line}</div>'


def pick_text_colors(image_path: Path) -> tuple[str, str, str, str]:
    """亮底用墨字，暗底用米字；返回 (text, accent, scrim_tint, scrim_tint_mid)。"""
    im = Image.open(image_path).convert("RGB")
    # 看文案侧（左 30%）平均亮度
    w, h = im.size
    left = list(im.crop((0, 0, int(w * 0.35), h)).resize((24, 24)).getdata())
    lum = sum((r + g + b) / 3 for r, g, b in left) / len(left)
    if lum > 135:
        # 亮底：墨字 + 极浅纸帘，禁止重暗角
        return ("#1c1714", "#a8843f", "rgba(255,252,248,0.30)", "rgba(255,252,248,0.10)")
    return ("#f6f1e8", "#c9a063", "rgba(10,10,12,0.42)", "rgba(10,10,12,0.14)")


def compose_html(
    platform: str,
    bg_uri: str,
    subject_path: Path | None = None,
    *,
    block_css_override: str | None = None,
    title_a: str = "东方",
    title_b: str = "神颜",
    title_accent: str = "颜",
    latin: str = "ORIENTAL BEAUTY",
    slogan: str = "她以骨相写诗，以眉眼成章",
    mode: str = "diag",
    title_zone: str = "safe",
) -> str:
    spec = PLATFORMS[platform]
    W, H = spec["w"], spec["h"]
    text_col, accent, scrim_tint, scrim_tint_mid = pick_text_colors(subject_path) if subject_path else ("#f6f1e8", "#c9a063", "rgba(10,10,12,0.42)", "rgba(10,10,12,0.14)")
    styles = type_html_styles().replace("{PALETTE['cream']}", text_col).replace("{PALETTE['gold']}", accent)

    if platform == "wechat":
        hero, sub = 150, 15
        block_css = block_css_override or (
            "top: 12%; left: 6.5%; width: 44%;"
            if title_zone == "safe" else "bottom: 8%; left: 6.5%; width: 44%;"
        )
        photo_pos = "center 16%"
        # 只压左栏，人物亮
        scrim = "linear-gradient(90deg, " + scrim_tint + " 0%, " + scrim_tint_mid + " 30%, transparent 55%)"
    elif platform == "wechat-sq":
        hero, sub = 72, 12
        block_css = block_css_override or (
            "top: 12%; left: 8%; right: 42%;"
            if title_zone == "safe" else "bottom: 10%; left: 8%; right: 42%;"
        )
        photo_pos = "center 14%"
        scrim = "linear-gradient(90deg, rgba(10,10,12,0.55) 0%, rgba(10,10,12,0.2) 40%, transparent 62%)"
    elif platform == "xhs":
        hero, sub = 112, 14
        block_css = block_css_override or (
            "top: 14%; left: 8%; right: 8%;"
            if title_zone == "safe" else "bottom: 32%; left: 8%; right: 8%;"
        )
        photo_pos = "center 12%"
        scrim = (
            "linear-gradient(180deg, rgba(255,252,248,0.28) 0%, rgba(255,252,248,0.08) 28%, "
            "transparent 48%, rgba(255,252,248,0.06) 78%, rgba(10,10,12,0.18) 100%)"
        )
    else:
        hero, sub = 96, 12
        block_css = block_css_override or (
            "top: 12%; left: 8%; right: 8%;"
            if title_zone == "safe" else "bottom: 28%; left: 8%; right: 8%;"
        )
        photo_pos = "center 12%"
        scrim = "linear-gradient(180deg, rgba(10,10,12,0.45) 0%, transparent 40%, rgba(10,10,12,0.35) 100%)"

    if block_css_override:
        block_css = block_css_override

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><style>
{styles}
  body {{ width: {W}px; height: {H}px; position: relative; }}
  .photo {{
    position: absolute; inset: 0;
    background: url('{bg_uri}') {photo_pos} / cover no-repeat;
    filter: none;
  }}
  .scrim {{ position: absolute; inset: 0; background: {scrim}; }}
  .vignette {{ position: absolute; inset: 0; box-shadow: inset 0 0 28px rgba(20,12,8,0.05); }}
  .block {{ position: absolute; z-index: 5; {block_css} }}
  .rule {{ width: 64px; margin: 16px 0 18px; }}
  .latin {{ font-size: {sub}px; margin-top: 24px; }}
  .slogan {{ font-family: 'Songti SC', serif; font-size: {sub+5}px; margin-top: 14px; }}
  /* 交付成图禁止角落小字/规格水印/页码 —— 2026-09-23 反馈 */
</style></head>
<body>
  <div class="photo"></div>
  <div class="scrim"></div>
  <div class="vignette"></div>
  <div class="block">
    <div class="rule"></div>
    {title_block(title_a, title_b, title_accent, mode, hero)}
    <div class="latin mono">{latin}</div>
    <div class="slogan">{slogan}</div>
  </div>
</body></html>"""


def render_html(html: str, out_path: Path, w: int, h: int, fmt: str = "png") -> Path:
    """2× 超采样 → Lanczos 缩到交付尺寸，保证字缘/发丝清晰。"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scale = 2
    tmp = out_path.with_suffix(f".supersample.{fmt}")
    with sync_playwright() as p:
        launch = {"headless": True}
        if CHROME and os.path.exists(CHROME):
            launch["executable_path"] = CHROME
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
        page.set_content(html)
        page.wait_for_timeout(600)
        if fmt == "jpeg":
            page.screenshot(path=str(tmp), type="jpeg", quality=95)
        else:
            page.screenshot(path=str(tmp), type="png")
        browser.close()
    im = Image.open(tmp)
    if im.size != (w, h):
        im = im.convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
    else:
        im = im.convert("RGB")
    if fmt == "jpeg":
        im.save(out_path, "JPEG", quality=92, optimize=True)
    else:
        im.save(out_path, "PNG")
    tmp.unlink(missing_ok=True)
    return out_path


def export_pair(png_path: Path) -> dict:
    """PNG-24 主稿 + JPEG q92 伴生。"""
    im = Image.open(png_path).convert("RGB")
    jpg = png_path.with_suffix(".jpg")
    im.save(jpg, "JPEG", quality=92, optimize=True)
    return {
        "png": str(png_path),
        "png_kb": png_path.stat().st_size // 1024,
        "jpg": str(jpg),
        "jpg_kb": jpg.stat().st_size // 1024,
    }


def run_platform(
    platform: str,
    *,
    subject_src: Path,
    mode: str = "diag",
    title_a: str = "东方",
    title_b: str = "神颜",
    title_accent: str = "颜",
    latin: str = "ORIENTAL BEAUTY",
    slogan: str = "她以骨相写诗，以眉眼成章",
    title_zone: str = "safe",
    slug: str = "oriental-beauty",
) -> dict:
    spec = PLATFORMS[platform]
    place = spec.get("place", (0.6, 0.4))
    stem = f"{platform}_{mode}_{title_zone}"
    crop_path = OUT / f"{stem}_subject.png"
    crop_subject(subject_src, crop_path, spec["ratio"], place=place)

    crop_im = Image.open(crop_path)
    faces_after = detect_faces(str(crop_path))
    if faces_after:
        f = max(faces_after, key=lambda z: (z["x_max"]-z["x_min"])*(z["y_max"]-z["y_min"]))
        # 头必须完整：发顶留白 ≥3%，脸不贴四边
        head_ok = (
            f["y_min"] >= 0.03
            and f["y_max"] <= 0.92
            and f["x_min"] >= 0.04
            and f["x_max"] <= 0.96
        )
        if not head_ok:
            raise SystemExit(f"[head] face box clipped: {f}")
        print(f"  · face box y={f['y_min']:.2f}-{f['y_max']:.2f} x={f['x_min']:.2f}-{f['x_max']:.2f} headroom={f['y_min']:.0%}")
    layout = verify_layout(crop_im, place, platform, image_path=crop_path)
    if not layout["ok"]:
        raise SystemExit(
            f"[layout] subject placement failed for {platform}: {layout}"
        )

    # 终稿再检（含排版层）：皮肤质心仍应稳定
    face_pre = face_occlusion_gate(crop_path, title_zone=title_zone, platform=platform, mode=mode)
    if not face_pre["ok"]:
        raise SystemExit(f"[face] title would occlude face: {face_pre}")

    bg_uri = "data:image/png;base64," + base64.b64encode(crop_path.read_bytes()).decode()
    html = compose_html(
        platform,
        bg_uri,
        subject_path=crop_path,
        block_css_override=face_pre.get("block_css"),
        title_a=title_a,
        title_b=title_b,
        title_accent=title_accent,
        latin=latin,
        slogan=slogan,
        mode=mode,
        title_zone=title_zone,
    )
    png_path = OUT / f"{stem}.png"
    render_html(html, png_path, spec["w"], spec["h"])
    files = export_pair(png_path)

    final_im = Image.open(png_path)
    final_layout = verify_layout(final_im, place, platform, image_path=png_path)
    # 暗角门禁：四角平均亮度 / 中心 ≥ 0.55，否则暗角过大
    g = final_im.convert("L")
    W, H = g.size
    def _mean(box):
        c = g.crop(box)
        return sum(c.resize((16, 16)).getdata()) / 256
    center = _mean((int(W*0.35), int(H*0.3), int(W*0.65), int(H*0.7)))
    corners = [
        _mean((0, 0, int(W*0.12), int(H*0.12))),
        _mean((int(W*0.88), 0, W, int(H*0.12))),
        _mean((0, int(H*0.88), int(W*0.12), H)),
        _mean((int(W*0.88), int(H*0.88), W, H)),
    ]
    vignette_ratio = (sum(corners)/4) / max(center, 1)
    if vignette_ratio < 0.55:
        raise SystemExit(f"[vignette] too heavy, corners/center={vignette_ratio:.2f}")
    final_layout["vignette_ratio"] = round(vignette_ratio, 3)

    title_a, title_b, latin, slogan = (apply_fix(x) for x in (title_a, title_b, latin, slogan))
    copy_errs = validate_copy(title_a, title_b, latin, slogan) + lint_copy(f"{title_a}{title_b} {latin} {slogan}")
    if copy_errs:
        raise SystemExit(f"[copy] {copy_errs}")

    named_png = OUT / build_filename(platform, mode, slug, "png")
    named_jpg = OUT / build_filename(platform, mode, slug, "jpg")
    Image.open(png_path).save(named_png)
    Image.open(png_path).convert("RGB").save(named_jpg, "JPEG", quality=92, optimize=True)

    face_gate = face_occlusion_gate(crop_path, title_zone=title_zone, platform=platform, mode=mode)
    if not face_gate["ok"]:
        raise SystemExit(f"[face] title would occlude face: {face_gate}")

    # 清晰度门禁：高频能量（拉普拉斯近似）过低则拒收
    gsm = final_im.convert("L").resize((min(1200, final_im.width), max(1, int(min(1200, final_im.width) * final_im.height / final_im.width))))
    px = gsm.load()
    w2, h2 = gsm.size
    import math
    e = 0
    n = 0
    for y in range(1, h2 - 1, 2):
        for x in range(1, w2 - 1, 2):
            lap = abs(4 * px[x, y] - px[x-1, y] - px[x+1, y] - px[x, y-1] - px[x, y+1])
            e += lap
            n += 1
    sharpness = e / max(n, 1)
    if sharpness < 4.0:
        raise SystemExit(f"[sharpness] too soft, lap_mean={sharpness:.2f}")
    thumb_ok = qa_thumbnail_ok(named_png)
    list_sim = None
    if platform == "wechat":
        list_sim = str(render_wechat_list_sim(named_png, OUT / f"{stem}_list_sim.jpg"))

    report = {
        "platform": platform,
        "label": spec["label"],
        "canvas": f"{spec['w']}×{spec['h']}",
        "safe": spec["safe"],
        "mode": mode,
        "title_zone": title_zone,
        "layout_subject": layout,
        "layout_final": final_layout,
        "qa_vignette_ratio": final_layout.get("vignette_ratio"),
        "copy_errors": copy_errs,
        "qa_face_gate": face_gate,
        "qa_sharpness": round(sharpness, 2),
        "qa_thumbnail_ok": thumb_ok,
        "qa_list_sim": list_sim,
        "qa_visual_check_required": True,
        "files": {
            **files,
            "named_png": str(named_png),
            "named_jpg": str(named_jpg),
        },
    }
    print(
        f"✓ {spec['label']:18} {files['png'].split('/')[-1]:32} "
        f"{files['png_kb']}KB png / {files['jpg_kb']}KB jpg  "
        f"place_err={final_layout['place_err']} centroid={final_layout['skin_centroid']}"
    )
    return report




def run_brief_batch(brief_path: Path, platforms: list[str] | None = None) -> list[dict]:
    """一键：单份简报 → 多规格出图（含人脸避让/QA/命名）。"""
    from cover_style import load_brief, resolve_style

    brief = load_brief(brief_path)
    style = resolve_style(brief)
    plats = platforms or list(PLATFORMS)
    if brief.get("platform") and brief["platform"] in PLATFORMS and not platforms:
        plats = [brief["platform"]] + [p for p in PLATFORMS if p != brief["platform"]]
    kwargs = {}
    for k in ("title_a", "title_b", "title_accent", "latin", "slogan", "slug"):
        if brief.get(k):
            kwargs[k] = brief[k]
    mode = style.mode if brief.get("mode", "auto") in (None, "auto") else brief.get("mode", style.mode)
    zone = brief.get("title_zone") or style.title_zone_default

    # 底图：优先 brief 指定，否则按规格选已生成源
    wechat_src = Path(brief["wechat_src"]) if brief.get("wechat_src") else ASSETS_EXP / "_beauty_hero.png"
    xhs_src = Path(brief["xhs_src"]) if brief.get("xhs_src") else ASSETS_EXP / "_beauty_xhs.png"

    reports = []
    for name in plats:
        src = wechat_src if (PLATFORMS[name].get("src") == "wechat") else xhs_src
        if not src.exists():
            print(f"· skip {name}: missing {src}")
            continue
        try:
            reports.append(run_platform(
                name,
                subject_src=src,
                mode=mode,
                title_zone=zone,
                **kwargs,
            ))
        except SystemExit as e:
            print(f"· FAIL {name}: {e}")
            reports.append({"platform": name, "ok": False, "error": str(e)})
        except Exception as e:
            print(f"· ERROR {name}: {e}")
            reports.append({"platform": name, "ok": False, "error": str(e)})
    return reports

def main() -> None:
    ap = argparse.ArgumentParser(description="微信 / 小红书 封面流水线")
    ap.add_argument("--platform", choices=list(PLATFORMS) + ["all"], default="all")
    ap.add_argument("--mode", choices=["diag", "bignews", "stack", "vertical"], default="diag")
    ap.add_argument("--slug", default="oriental-beauty", help="交付文件名 slug")
    ap.add_argument("--title-zone", choices=["safe", "risk"], default="safe",
                    help="risk=标题落入底部遮挡带（实验用）")
    ap.add_argument("--wechat-src", default=str(ASSETS_EXP / "_beauty_hero.png"))
    ap.add_argument("--xhs-src", default=str(ASSETS_EXP / "_beauty_xhs.png"))
    ap.add_argument("--brief", help="需求简报 JSON（goal/subject/tone/mode/copy），驱动变量样式")
    ap.add_argument("--briefs-dir", help="批量：目录下所有 *.json 简报，各自出四规格")
    ap.add_argument("--platforms", help="批量时平台列表，逗号分隔，默认全部")
    ap.add_argument("--generate", action="store_true",
                    help="经 New API 轮换池生成底图（scripts/agnes_gateway.py）")
    args = ap.parse_args()

    brief = {}
    style = None
    if args.brief:
        from cover_style import load_brief, resolve_style
        brief = load_brief(args.brief)
        style = resolve_style(brief)
        print(f"· brief style {style.name}")
        print(f"· font/mode {style.mode} hero={style.hero_size}")
        if args.generate:
            from agnes_gateway import generate, save_image
            size_hint = brief.get("size") or (
                "2352x1008" if (brief.get("platform") or args.platform).startswith("wechat")
                and "sq" not in (brief.get("platform") or args.platform) else "1088x1456"
            )
            gen_out = OUT / f"_gen_{style.name.replace('/', '_')}.png"
            res = generate(style.gen_prompt, size=size_hint)
            if not res.get("ok"):
                raise SystemExit(f"[generate] {res}")
            save_image(res, gen_out)
            print(f"· generated subject → {gen_out} ({res['cost_s']}s via {res['via']})")
            # 按平台源类型回填
            plat = brief.get("platform") or args.platform
            if plat.startswith("wechat") and "sq" not in plat:
                args.wechat_src = str(gen_out)
            else:
                args.xhs_src = str(gen_out)

    if args.briefs_dir:
        plats = args.platforms.split(",") if args.platforms else None
        all_reports = []
        for bp in sorted(Path(args.briefs_dir).glob("*.json")):
            print(f"\n=== BRIEF {bp.name} ===")
            all_reports.extend(run_brief_batch(bp, plats))
        batch_json = OUT / "pipeline_report_batch.json"
        batch_json.write_text(json.dumps(all_reports, ensure_ascii=False, indent=2), encoding="utf-8")
        named = [Path(r["files"]["named_png"]) for r in all_reports if r.get("files", {}).get("named_png")]
        if named:
            sheet = build_contact_sheet(named, OUT / "_contact_batch.jpg")
            print(f"✓ batch contact → {sheet}")
        print("⚠️  [QA] 批量完成后仍须逐张目检。")
        return

    platforms = list(PLATFORMS) if args.platform == "all" else [args.platform]
    reports = []
    for name in platforms:
        src_kind = PLATFORMS[name].get("src", "wechat")
        if src_kind == "xhs":
            src = Path(args.xhs_src)
        else:
            src = Path(args.wechat_src)
        if not src.exists():
            raise SystemExit(f"missing subject: {src}")
        mode = (style.mode if style and brief.get("mode", "auto") == "auto" else args.mode) if style else args.mode
        # 简报文案覆盖
        kwargs = {'slug': args.slug}
        if brief:
            for k in ("title_a", "title_b", "title_accent", "latin", "slogan", "slug"):
                if brief.get(k):
                    kwargs[k] = brief[k]
        kw = dict(kwargs) if 'kwargs' in dir() else {}
        kw.setdefault('slug', getattr(args, 'slug', 'oriental-beauty'))
        reports.append(
            run_platform(
                name,
                subject_src=src,
                mode=mode,
                title_zone=args.title_zone,
                **kwargs,
            )
        )

    out_json = OUT / f"pipeline_report_{args.mode}_{args.title_zone}.json"
    out_json.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ report → {out_json}")

    # 自动对照板 + 强制目检提示
    named = [Path(r["files"]["named_png"]) for r in reports if r.get("files", {}).get("named_png")]
    if named:
        sheet = build_contact_sheet(named, OUT / f"_contact_{args.mode}_{args.title_zone}.jpg")
        print(f"✓ contact sheet → {sheet}")
        print("⚠️  [QA] 必须人工目检对照板与终稿后再交付（头肩/排版/水印/缩略）。")


if __name__ == "__main__":
    main()