#!/usr/bin/env python3
"""
Agnes Studio - 商业海报排版与中文字体合成引擎
遵循 GitHub 高星排版标准（chinese-copywriting-guidelines / satori 盒模型思想）
支持 得意黑 (Smiley Sans)、霞鹜文楷 (LXGW WenKai)、经典宋体 (Songti) 矢量光影合成
"""

import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from env_config import FONTS_DIR, ASSETS_DIR, resolve_font_path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONTS_DIR = str(FONTS_DIR)
ASSETS_DIR = str(ASSETS_DIR)


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
    theme_color="amber_gold"   # "amber_gold" | "cyber_cyan" | "pure_white"
):
    bg_p, out_p = _prepare_io(bg_image_path, output_path)
    font_style = str(font_style or "wenkai").strip().lower()
    main_title = str(main_title or "")
    sub_title = str(sub_title or "")
    tagline = str(tagline or "")
    metadata_no = str(metadata_no or "")
    theme_color = str(theme_color or "amber_gold").strip().lower()

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
    print(f"✅ 商业海报渲染完成: {out_p}")
    return str(out_p)

if __name__ == "__main__":
    # 使用纯净底图分别生成三种顶级开源字体版本
    src_img = os.path.join(ASSETS_DIR, "agnes_1790006749_b2b755da.png")
    if os.path.exists(src_img):
        # 1. 霞鹜文楷版 (日漫温润诗意)
        compose_commercial_poster(
            src_img,
            os.path.join(ASSETS_DIR, "poster_style_wenkai.png"),
            font_style="wenkai",
            main_title="铜 钟 与 蒸 汽 城",
            sub_title="STEAM & CHIME",
            tagline="「 她修理时间，也修理人心 」",
            theme_color="amber_gold"
        )

        # 2. 得意黑版 (现代先锋窄斜体)
        compose_commercial_poster(
            src_img,
            os.path.join(ASSETS_DIR, "poster_style_smiley.png"),
            font_style="smiley",
            main_title="铜钟与蒸汽城",
            sub_title="STEAM & CHIME",
            tagline="「 她修理时间，也修理人心 」",
            theme_color="cyber_cyan"
        )

        # 3. 经典宋体版 (严肃大片衬线)
        compose_commercial_poster(
            src_img,
            os.path.join(ASSETS_DIR, "poster_style_songti.png"),
            font_style="songti",
            main_title="铜 钟 与 蒸 汽 城",
            sub_title="STEAM & CHIME",
            tagline="「 她修理时间，也修理人心 」",
            theme_color="amber_gold"
        )
