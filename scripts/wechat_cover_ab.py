#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H1 标题位置 / H3 导出格式 · 微信头图 2350×1000 最小对照实验。

单变量：
  H1 — 仅改主标锚点（上安全区 vs 底部 25% 遮挡带）
  H3 — 同版式，仅导出 PNG-24 vs JPEG q90，并附模拟二次压缩结果

构图铁律（2026-09-23 用户反馈后固化）：
  - 去掉无信息量的色块/描边框（含粉红竖条、青色尺寸徽标框）
  - 人物必须是主体，头部完整可见（2.35:1 裁切禁止居中砍头）
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from env_config import FONTS_DIR, ASSETS_DIR, resolve_chrome_path
from PIL import Image

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None  # type: ignore

OUT = ROOT / "experiments"
FONTS = FONTS_DIR
ASSETS = ASSETS_DIR
CHROME = resolve_chrome_path()
W, H = 2350, 1000
RATIO = 2.35

BG_SRC = ASSETS / "agnes_1789995698_9987.png"

EXPERIMENT_MATRIX: list[dict[str, Any]] = [
    {
        "id": "H1_top",
        "group": "H1",
        "name": "主标安全区",
        "filename": "H1_title_top_safe.png",
        "format": "png",
        "title_top": True,
        "description": "主标落在安全区（上 70% 区域），避免公众号列表底栏遮挡",
    },
    {
        "id": "H1_bot",
        "group": "H1",
        "name": "主标底部遮挡带",
        "filename": "H1_title_bottom_risk.png",
        "format": "png",
        "title_top": False,
        "description": "主标落入底部 25% 遮挡带，模拟失败信号与基线遮挡",
    },
    {
        "id": "H3_png",
        "group": "H3",
        "name": "PNG-24 无损导出",
        "filename": "H3_export_png24.png",
        "format": "png",
        "title_top": True,
        "description": "PNG-24 高保真格式导出基准",
    },
    {
        "id": "H3_jpg",
        "group": "H3",
        "name": "JPEG q90 导出",
        "filename": "H3_export_jpeg_q90.jpg",
        "format": "jpeg",
        "title_top": True,
        "description": "JPEG quality 90 导出基准",
    },
    {
        "id": "H3_png_sim",
        "group": "H3",
        "name": "PNG-24 模拟微信二次压缩",
        "filename": "H3_png24_after_wechat_sim.jpg",
        "format": "sim_reencode",
        "source_ref": "H3_export_png24.png",
        "description": "PNG-24 经微信缩放下采样后二次有损压缩表现",
    },
    {
        "id": "H3_jpg_sim",
        "group": "H3",
        "name": "JPEG q90 模拟微信二次压缩",
        "filename": "H3_jpeg_q90_after_wechat_sim.jpg",
        "format": "sim_reencode",
        "source_ref": "H3_export_jpeg_q90.jpg",
        "description": "JPEG q90 经微信缩放下采样后二次有损压缩表现",
    },
]


def get_experiment_matrix() -> list[dict[str, Any]]:
    """返回 H1/H3 微信头图对照实验矩阵规格清单。"""
    return [dict(item) for item in EXPERIMENT_MATRIX]


def check_prerequisites(src_path: Path | str | None = None) -> dict[str, Any]:
    """检查实验所需前置依赖：底图源文件、SmileySans 字体、Chrome、Playwright。"""
    src = Path(src_path) if src_path else BG_SRC
    font_file = FONTS / "SmileySans-Oblique.ttf"
    has_playwright = sync_playwright is not None
    chrome_ok = bool(CHROME and os.path.exists(CHROME))

    res: dict[str, Any] = {
        "src_path": str(src),
        "src_exists": src.is_file(),
        "font_path": str(font_file),
        "font_exists": font_file.is_file(),
        "chrome_path": str(CHROME) if CHROME else None,
        "chrome_exists": chrome_ok,
        "playwright_available": has_playwright,
    }
    res["all_ok"] = bool(
        res["src_exists"]
        and res["font_exists"]
        and res["chrome_exists"]
        and res["playwright_available"]
    )
    return res


def make_subject_crop(src: Path | str, dst: Path | str) -> Path:
    """1:1 人像 → 2.35:1，顶对齐裁切保住完整头部；人像为画面主体。"""
    src = Path(src)
    dst = Path(dst)
    if not src.is_file():
        raise FileNotFoundError(f"Source background image not found: {src}")
    im = Image.open(src).convert("RGB")
    w, h = im.size
    crop_h = int(round(w / RATIO))
    # 头部在上 1/3：从 y=0 起裁，保证发顶完整
    y0 = 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.crop((0, y0, w, y0 + crop_h)).save(dst, "PNG")
    return dst


def cover_html(bg_uri: str, title_top: bool) -> str:
    # 左侧文案栏，不压人脸（人头偏画面中右）
    if title_top:
        title_style = "top:20%; left:6%;"
        sub_style = "top:54%; left:6%;"
    else:
        # 刻意落入底部 25% 遮挡带（H1 失败信号）；脚注上移避免与主标叠字
        title_style = "bottom:8%; left:6%;"
        sub_style = "bottom:28%; left:6%;"
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family:'SmileySans'; src:url('file://{FONTS}/SmileySans-Oblique.ttf') format('truetype'); }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  width:{W}px; height:{H}px; overflow:hidden; background:#0A0B10; color:#F9FAFB;
  position:relative; font-family:'SmileySans','PingFang SC',sans-serif;
  -webkit-font-smoothing:antialiased;
}}
.bg {{
  position:absolute; inset:0;
  background-image:url('{bg_uri}');
  background-size:cover; background-position:center top;
}}
/* 只压左侧文案区，右侧人物保持明亮，确保人脸是主体 */
.veil {{
  position:absolute; inset:0;
  background:linear-gradient(90deg,
    rgba(10,11,16,0.88) 0%,
    rgba(10,11,16,0.72) 34%,
    rgba(10,11,16,0.18) 52%,
    rgba(10,11,16,0) 68%);
}}
.kicker {{
  position:absolute; top:7%; left:6%; z-index:5;
  font-family:ui-monospace,Menlo,monospace;
  font-size:26px; letter-spacing:8px; color:rgba(249,250,251,0.7);
}}
.title {{
  position:absolute; {title_style} z-index:5;
  font-size:120px; line-height:1.05; letter-spacing:10px;
  text-shadow:0 8px 40px rgba(0,0,0,0.45);
}}
.title .dot {{ color:#E11D48; }}
.sub {{
  position:absolute; {sub_style} z-index:5;
  font-family:ui-monospace,Menlo,monospace; font-size:28px; letter-spacing:7px;
  color:rgba(249,250,251,0.82);
  text-shadow:0 4px 20px rgba(0,0,0,0.4);
}}
</style></head><body>
  <div class="bg"></div>
  <div class="veil"></div>
  <div class="kicker">AGNES STUDIO // 2.35:1</div>
  <div class="title">苏黎世秩序<span class="dot">.</span></div>
  <div class="sub">STRUCTURE &amp; ESSENCE</div>
</body></html>"""


README_TEXT = """# H1 / H3 微信头图对照实验（2350×1000）

## 构图约束（已按反馈修正）

- **人物是主体**：2.35:1 采用**顶对齐**裁切，完整保留头部与肩部；禁止居中裁切砍头。
- **去掉装饰框**：不使用粉红竖条、青色尺寸徽标框等无信息色块/描边。
- **文案不压脸**：文字靠左，veil 只压文案区，右侧人脸保持可辨。

## H1 · 标题位置（单变量：主标锚点）

| 文件 | 变量 | 预期 |
| --- | --- | --- |
| `H1_title_top_safe.png` | 主标落在安全区 | 列表标题条遮挡下主标仍完整 |
| `H1_title_bottom_risk.png` | 主标落入底部 25% 遮挡带 | 失败信号：主标被切断 |

**判读**：真机订阅号列表截图，看主标是否被切。
**数据**：不可读像素占比、可读性 1–5、遮挡线与基线重叠。

## H3 · 导出格式（版式与 H1-top 相同）

| 文件 | 变量 |
| --- | --- |
| `H3_export_png24.png` | PNG-24 |
| `H3_export_jpeg_q90.jpg` | JPEG q90 |
| `H3_png24_after_wechat_sim.jpg` | PNG → 模拟二次压缩 |
| `H3_jpeg_q90_after_wechat_sim.jpg` | JPEG q90 → 模拟二次压缩 |

**判读**：200% 看字缘/发丝毛刺。
**成功信号**：PNG 链路毛刺显著更少。

## 常量

2350×1000 · sRGB · Smiley Sans · `#0A0B10`/`#E11D48`/`#F9FAFB` · 仅动所标单变量
"""


def render(html: str, out_path: Path | str, fmt: str = "png") -> Path:
    if sync_playwright is None:
        raise RuntimeError("Playwright is not installed or available")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        launch = {"headless": True}
        if CHROME and os.path.exists(CHROME):
            launch["executable_path"] = CHROME
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.set_content(html)
        page.wait_for_timeout(450)
        if fmt == "jpeg":
            page.screenshot(path=str(out_path), type="jpeg", quality=90)
        else:
            page.screenshot(path=str(out_path), type="png")
        browser.close()
    return out_path


def save_q90_copy(src: Path | str, dst: Path | str) -> Path:
    src = Path(src)
    dst = Path(dst)
    if not src.is_file():
        raise FileNotFoundError(f"Source image not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    Image.open(src).convert("RGB").save(dst, "JPEG", quality=90, optimize=True)
    return dst


def simulate_wechat_reencode(src: Path | str, dst: Path | str) -> Path:
    src = Path(src)
    dst = Path(dst)
    if not src.is_file():
        raise FileNotFoundError(f"Source image not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    small = im.resize((int(im.width * 0.92), int(im.height * 0.92)), Image.Resampling.LANCZOS)
    small.resize(im.size, Image.Resampling.BICUBIC).save(dst, "JPEG", quality=65, optimize=True)
    return dst


def head_visible_probe(path: Path | str) -> str:
    """粗检：画面上部 8–38% 中带是否有足够肤色/亮度结构（头应在框内）。"""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    im = Image.open(path).convert("RGB")
    w, h = im.size
    band = im.crop((int(w * 0.35), int(h * 0.05), int(w * 0.72), int(h * 0.42)))
    resized = band.resize((40, 24))
    if hasattr(resized, "get_flattened_data"):
        px = list(resized.get_flattened_data())
    else:
        px = list(resized.getdata())
    skin = 0
    for r, g, b in px:
        if r > 60 and g > 40 and b > 30 and r > g > b and (r - b) > 15 and r < 230:
            skin += 1
    ratio = skin / len(px)
    return f"head-band skin≈{ratio:.0%} ({'OK' if ratio > 0.08 else 'REVIEW'})"


def run_wechat_cover_ab(
    src: Path | str | None = None,
    out_dir: Path | str | None = None,
    dry_run: bool = False,
    write_readme: bool = True,
    render_fn: Callable[..., Path] | None = None,
    quiet: bool = False,
) -> dict[str, Any]:
    """执行 H1 / H3 微信头图对照实验管线。"""
    src_path = Path(src) if src else BG_SRC
    if not src_path.is_file():
        raise FileNotFoundError(f"Source background image not found: {src_path}")

    target_dir = Path(out_dir) if out_dir else OUT
    target_dir.mkdir(parents=True, exist_ok=True)

    subject_crop = target_dir / "_bg_subject_235x100.png"
    make_subject_crop(src_path, subject_crop)
    probe_subject = head_visible_probe(subject_crop)

    if not quiet:
        print("▶ 裁切：顶对齐 2.35:1 人像主体…", probe_subject)

    bg_uri = f"data:image/png;base64,{base64.b64encode(subject_crop.read_bytes()).decode()}"

    h1_top = target_dir / "H1_title_top_safe.png"
    h1_bot = target_dir / "H1_title_bottom_risk.png"
    h3_png = target_dir / "H3_export_png24.png"
    h3_jpg = target_dir / "H3_export_jpeg_q90.jpg"
    h3_png_x = target_dir / "H3_png24_after_wechat_sim.jpg"
    h3_jpg_x = target_dir / "H3_jpeg_q90_after_wechat_sim.jpg"

    artifacts: list[dict[str, Any]] = []
    actual_render = render_fn or render

    if dry_run:
        if not quiet:
            print("▶ [DRY-RUN] 跳过无头浏览器光栅化渲染，生成预演记录…")
        for item in EXPERIMENT_MATRIX:
            p = target_dir / item["filename"]
            artifacts.append({
                "id": item["id"],
                "file": str(p),
                "name": p.name,
                "format": item["format"],
                "dry_run": True,
                "size_kb": 0,
            })
    else:
        if not quiet:
            print("▶ H1 title position…")
        actual_render(cover_html(bg_uri, True), h1_top, "png")
        actual_render(cover_html(bg_uri, False), h1_bot, "png")

        probe_h1_top = head_visible_probe(h1_top)
        probe_h1_bot = head_visible_probe(h1_bot)
        if not quiet:
            print("  ", h1_top.name, probe_h1_top)
            print("  ", h1_bot.name, probe_h1_bot)

        if not quiet:
            print("▶ H3 export format…")
        actual_render(cover_html(bg_uri, True), h3_png, "png")
        save_q90_copy(h3_png, h3_jpg)

        if not quiet:
            print("▶ H3 simulated re-encode…")
        simulate_wechat_reencode(h3_png, h3_png_x)
        simulate_wechat_reencode(h3_jpg, h3_jpg_x)

        for p in (h1_top, h1_bot, h3_png, h3_jpg, h3_png_x, h3_jpg_x):
            with Image.open(p) as im:
                fmt_str = str(im.format)
                w_val, h_val = im.size[0], im.size[1]
            sz_kb = p.stat().st_size // 1024
            if not quiet:
                print(f"  ✓ {p.name:44} {fmt_str:4} {w_val}×{h_val} {sz_kb} KB")
            artifacts.append({
                "file": str(p),
                "name": p.name,
                "format": fmt_str,
                "size": [w_val, h_val],
                "size_kb": sz_kb,
            })

    if write_readme and not dry_run:
        (target_dir / "README.md").write_text(README_TEXT, encoding="utf-8")
        if not quiet:
            print("✓ README.md")

    return {
        "ok": True,
        "src": str(src_path),
        "out_dir": str(target_dir),
        "dry_run": dry_run,
        "subject_probe": probe_subject,
        "artifacts_count": len(artifacts),
        "artifacts": artifacts,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="Agnes Studio · H1/H3 微信头图 2350×1000 最小对照实验引擎 (WeChat Cover A/B Suite)"
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="列出所有 6 项 H1/H3 对照实验规格清单",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="检查实验运行前置条件（底图文件、字体、Chrome 与 Playwright 环境）",
    )
    parser.add_argument(
        "--src",
        type=str,
        default=None,
        help="指定自定义输入底图路径（默认使用官方资产库底图）",
    )
    parser.add_argument(
        "-o",
        "--out",
        "--out-dir",
        dest="out_dir",
        type=str,
        default=None,
        help="指定生成物输出目录（默认输出到 experiments/）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预演模式：执行前置检查并生成任务规划，不启动浏览器光栅化渲染",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出结果 (规格清单、环境探活或实验执行报告)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="静默模式，抑制控制台标准输出",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：前置依赖缺失或执行异常时返回非零退出码 1",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """命令行主执行入口。"""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    quiet = args.quiet or args.json

    if args.list:
        matrix = get_experiment_matrix()
        if args.json:
            print(json.dumps(matrix, ensure_ascii=False, indent=2))
        elif not args.quiet:
            print("Agnes Studio · H1/H3 微信头图对照实验清单:")
            for item in matrix:
                print(f"  [{item['id']:<10}] {item['name']:<18} | {item['format']:<12} | {item['description']}")
        return 0

    if args.check:
        prereqs = check_prerequisites(args.src)
        if args.json:
            print(json.dumps(prereqs, ensure_ascii=False, indent=2))
        elif not args.quiet:
            print("Agnes Studio · H1/H3 对照实验前置条件巡检:")
            print(f"  底图源文件: {'✓ 存在' if prereqs['src_exists'] else '❌ 缺失'} ({prereqs['src_path']})")
            print(f"  SmileySans: {'✓ 存在' if prereqs['font_exists'] else '❌ 缺失'} ({prereqs['font_path']})")
            print(f"  Chrome内核: {'✓ 存在' if prereqs['chrome_exists'] else '❌ 缺失'} ({prereqs['chrome_path']})")
            print(f"  Playwright: {'✓ 就绪' if prereqs['playwright_available'] else '❌ 缺失'}")
            print(f"  总体就绪度: {'✓ PASS' if prereqs['all_ok'] else '⚠️ WARNING'}")

        if args.strict and not prereqs["all_ok"]:
            return 1
        return 0

    try:
        report = run_wechat_cover_ab(
            src=args.src,
            out_dir=args.out_dir,
            dry_run=args.dry_run,
            quiet=quiet,
        )
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        if not quiet:
            print(f"❌ 运行失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
