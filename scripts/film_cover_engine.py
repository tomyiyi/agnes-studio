#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio · 电影感封面排版引擎 (Cinematic Cover Engine)
深度汲取【书生·电影感封面六式】与【书生·色块封面八式】核心排版法则：
1. 样式 01 · 绿色刊头 (Capsule Green Banner): 顶部荧光绿横向圆角胶囊 + 双端排字避让头部 + 底部双色超粗黑体
2. 样式 02 · 红色错位 (Split Red Columns): 左字列(y29%)与右字列(y45%)错落夹击 + 纯红锐角大字 + 白描边黑副标
3. 样式 03 · 侧边明黄 (Side Yellow Ribbon): 紧贴左边缘 11% 贯穿黄色色带 + 纵向大英文 + 左下黄色 2:1 超窄特粗黑体
4. 样式 04 · 绿底上下 (Top Green 1/3 Split): 上 1/3 苹果绿大色块 + 深钴蓝剪纸美术字 + 4% 头部跨层微阴影
5. 样式 05 · 电影宽银幕 (Letterbox 2.35:1): 上下 12% 纯黑遮幅 + 居中大宋体 + 底部胶片微排版
"""

import os
from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = "/Users/tom/Desktop/agnes-studio/public/fonts"
ASSETS_DIR = "/Users/tom/Desktop/agnes-studio/public/assets"

FONT_SMILEY = os.path.join(FONTS_DIR, "SmileySans-Oblique.ttf")
FONT_WENKAI = os.path.join(FONTS_DIR, "LXGWWenKai-Regular.ttf")
FONT_SONGTI = "/System/Library/Fonts/Supplemental/Songti.ttc"
FONT_PINGFANG = "/System/Library/Fonts/PingFang.ttc"

def get_font(path, size):
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

# -------------------------------------------------------------
# 1. 书生六式之【绿色刊头】：荧光绿胶囊 + 双端排字 + 底部左对齐
# -------------------------------------------------------------
def render_shusheng_capsule_green(
    bg_image_path,
    output_path,
    title="电影感封面",
    sub_1="一张照片",
    sub_2="六种排法",
    author_en="AGNES DESIGN",
    author_cn="书生视觉"
):
    print(f"🎬 [Capsule Green] 正在渲染【绿色刊头胶囊排版】封面...")
    base_img = Image.open(bg_image_path).convert("RGBA")
    w, h = base_img.size
    scale = w / 1024.0

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. 顶部荧光绿 #00F05A 圆角横胶囊 (宽94%, 高13%, 左右各3%, 上留5%)
    cap_w = int(w * 0.94)
    cap_h = int(h * 0.13)
    cap_x = int(w * 0.03)
    cap_y = int(h * 0.05)
    radius = cap_h // 2
    c_green = (0, 240, 90, 255)

    draw.rounded_rectangle(
        [(cap_x, cap_y), (cap_x + cap_w, cap_y + cap_h)],
        radius=radius,
        fill=c_green
    )

    f_cap_main = get_font(FONT_SMILEY, int(22 * scale))
    f_cap_sub = get_font(FONT_SMILEY, int(15 * scale))

    # 胶囊左侧：两行黑色无衬线粗体 【署名英文】/【署名】
    pad_in = int(32 * scale)
    draw.text((cap_x + pad_in, cap_y + int(18 * scale)), author_en, font=f_cap_sub, fill=(10, 10, 10, 255))
    draw.text((cap_x + pad_in, cap_y + int(42 * scale)), author_cn, font=f_cap_main, fill=(10, 10, 10, 255))

    # 胶囊右侧：两行黑色无衬线粗体 DESIGN / 照片排版
    t_r1 = "DESIGN"
    t_r2 = "照片排版"
    bbox_r1 = draw.textbbox((0, 0), t_r1, font=f_cap_sub)
    bbox_r2 = draw.textbbox((0, 0), t_r2, font=f_cap_main)
    w_r1 = bbox_r1[2] - bbox_r1[0]
    w_r2 = bbox_r2[2] - bbox_r2[0]

    draw.text((cap_x + cap_w - pad_in - w_r1, cap_y + int(18 * scale)), t_r1, font=f_cap_sub, fill=(10, 10, 10, 255))
    draw.text((cap_x + cap_w - pad_in - w_r2, cap_y + int(42 * scale)), t_r2, font=f_cap_main, fill=(10, 10, 10, 255))

    # 2. 下部从 y64% 起叠两行超粗黑体中文 (左对齐 x=5%)
    f_title = get_font(FONT_SMILEY, int(64 * scale))
    f_sub = get_font(FONT_SMILEY, int(42 * scale))

    text_x = int(w * 0.05)
    title_y = int(h * 0.68)
    sub_y = title_y + int(85 * scale)

    # 第一行白色大标题 (带微弱黑色暗投影保障可读性)
    draw.text((text_x + 3, title_y + 3), title, font=f_title, fill=(0, 0, 0, 180))
    draw.text((text_x, title_y), title, font=f_title, fill=(255, 255, 255, 255))

    # 第二行连续排 【副一】【副二】(前段白色、后段荧光绿)
    bbox_s1 = draw.textbbox((text_x, sub_y), sub_1, font=f_sub)
    s1_end_x = bbox_s1[2]

    # 副一 (白色)
    draw.text((text_x + 2, sub_y + 2), sub_1, font=f_sub, fill=(0, 0, 0, 180))
    draw.text((text_x, sub_y), sub_1, font=f_sub, fill=(255, 255, 255, 255))

    # 副二 (荧光绿)
    spacing = int(12 * scale)
    draw.text((s1_end_x + spacing + 2, sub_y + 2), sub_2, font=f_sub, fill=(0, 0, 0, 180))
    draw.text((s1_end_x + spacing, sub_y), sub_2, font=f_sub, fill=c_green)

    final_img = Image.alpha_composite(base_img, overlay).convert("RGB")
    final_img.save(output_path, quality=95)
    print(f"✅ 绿色刊头胶囊封面生成成功: {output_path}")
    return output_path

# -------------------------------------------------------------
# 2. 书生六式之【红色错位】：左右竖排错位夹击 + 纯红锐角大字
# -------------------------------------------------------------
def render_shusheng_split_red(
    bg_image_path,
    output_path,
    chars_left="铜钟",    # 前二字
    chars_right="蒸汽",   # 后二字
    sub_1="一张人物自拍",
    sub_2="也能排成电影海报"
):
    print(f"🎬 [Split Red] 正在渲染【红色错位竖排夹击】封面...")
    base_img = Image.open(bg_image_path).convert("RGBA")
    w, h = base_img.size
    scale = w / 1024.0

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. 字体
    f_vert = get_font(FONT_SMILEY, int(96 * scale))   # 红色超粗锐角大字
    f_sub = get_font(FONT_PINGFANG, int(18 * scale))   # 思源黑体风格副标题
    f_quote = get_font(FONT_SMILEY, int(22 * scale))

    c_red = (235, 35, 45, 255)

    # 2. 左上角副标题 (带白描边黑色字心，保证浅墙/深窗都能读清)
    sub_x = int(w * 0.05)
    sub_y1 = int(h * 0.08)
    sub_y2 = sub_y1 + int(28 * scale)

    # 红色角标
    draw.rectangle([(sub_x, sub_y1 - int(12 * scale)), (sub_x + int(24 * scale), sub_y1 + int(12 * scale))], fill=c_red)
    draw.text((sub_x + int(4 * scale), sub_y1 - int(12 * scale)), "“", font=f_quote, fill=(255, 255, 255, 255))

    for offset in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)]:
        draw.text((sub_x + int(36 * scale) + offset[0], sub_y1 + offset[1]), sub_1, font=f_sub, fill=(255, 255, 255, 240))
        draw.text((sub_x + int(36 * scale) + offset[0], sub_y2 + offset[1]), sub_2, font=f_sub, fill=(255, 255, 255, 240))
    draw.text((sub_x + int(36 * scale), sub_y1), sub_1, font=f_sub, fill=(15, 18, 24, 255))
    draw.text((sub_x + int(36 * scale), sub_y2), sub_2, font=f_sub, fill=(15, 18, 24, 255))

    # 3. 左字列：限定 x3%—25%，依次竖排【前二字】，起点 y29%
    left_x = int(w * 0.05)
    left_y = int(h * 0.29)
    char_step = int(125 * scale)

    for i, ch in enumerate(chars_left):
        cy = left_y + i * char_step
        # 阴影与纯红大字
        draw.text((left_x + 3, cy + 3), ch, font=f_vert, fill=(0, 0, 0, 160))
        draw.text((left_x, cy), ch, font=f_vert, fill=c_red)

    # 4. 右字列：限定 x75%—97%，依次竖排【后二字】，起点 y45% (比左列低约一个字)
    right_x = int(w * 0.82)
    right_y = int(h * 0.45)

    for i, ch in enumerate(chars_right):
        cy = right_y + i * char_step
        draw.text((right_x + 3, cy + 3), ch, font=f_vert, fill=(0, 0, 0, 160))
        draw.text((right_x, cy), ch, font=f_vert, fill=c_red)

    # 右下角闭合红色引号框
    q_x = int(w * 0.88)
    q_y = right_y + len(chars_right) * char_step + int(10 * scale)
    draw.rectangle([(q_x, q_y), (q_x + int(24 * scale), q_y + int(24 * scale))], fill=c_red)
    draw.text((q_x + int(6 * scale), q_y - int(4 * scale)), "”", font=f_quote, fill=(255, 255, 255, 255))

    final_img = Image.alpha_composite(base_img, overlay).convert("RGB")
    final_img.save(output_path, quality=95)
    print(f"✅ 红色错位竖排封面生成成功: {output_path}")
    return output_path

# -------------------------------------------------------------
# 3. 书生八式之【侧边色块】：11% 贯穿黄色色带 + 2:1 超窄刊头黑体
# -------------------------------------------------------------
def render_shusheng_side_yellow(
    bg_image_path,
    output_path,
    title_top="电影感",
    title_bottom="封面",
    sub="一张照片 · 八种排法"
):
    print(f"🎬 [Side Yellow] 正在渲染【侧边黄色贯穿带】封面...")
    base_img = Image.open(bg_image_path).convert("RGBA")
    w, h = base_img.size
    scale = w / 1024.0

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. 明黄 #F9EF51 色带：紧贴最左边，宽 11% 画宽，贯穿顶底
    ribbon_w = int(w * 0.11)
    c_yellow = (249, 239, 81, 255)
    draw.rectangle([(0, 0), (ribbon_w, h)], fill=c_yellow)

    # 色带上半部：黑色窄长大写纵向排列
    f_vert_en = get_font(FONT_SMILEY, int(16 * scale))
    en_words = ["P", "H", "O", "T", "O", "·", "C", "O", "V", "E", "R", "·", "D", "E", "S", "I", "G", "N"]
    step_y = int(24 * scale)
    start_y = int(h * 0.08)
    for i, ch in enumerate(en_words):
        draw.text((int(ribbon_w * 0.32), start_y + i * step_y), ch, font=f_vert_en, fill=(15, 18, 24, 255))

    # 2. 文字区放左下 (左缘 x30%, 避开人物面部与手部)
    text_x = int(w * 0.28)

    # 上行：“电影感” 黄色粗美术宋体
    f_songti = get_font(FONT_SONGTI, int(48 * scale))
    draw.text((text_x + 2, int(h * 0.58) + 2), title_top, font=f_songti, fill=(0, 0, 0, 180))
    draw.text((text_x, int(h * 0.58)), title_top, font=f_songti, fill=c_yellow)

    # 下行：“封面” 黄色超窄特粗黑体 (高宽比 2:1)
    f_heavy_black = get_font(FONT_SMILEY, int(110 * scale))
    draw.text((text_x + 3, int(h * 0.67) + 3), title_bottom, font=f_heavy_black, fill=(0, 0, 0, 200))
    draw.text((text_x, int(h * 0.67)), title_bottom, font=f_heavy_black, fill=c_yellow)

    # 最底部：白色特粗黑体副标题
    f_sub = get_font(FONT_SMILEY, int(26 * scale))
    draw.text((text_x + 2, int(h * 0.90) + 2), sub, font=f_sub, fill=(0, 0, 0, 180))
    draw.text((text_x, int(h * 0.90)), sub, font=f_sub, fill=(255, 255, 255, 255))

    final_img = Image.alpha_composite(base_img, overlay).convert("RGB")
    final_img.save(output_path, quality=95)
    print(f"✅ 侧边黄色贯穿带封面生成成功: {output_path}")
    return output_path

# -------------------------------------------------------------
# 4. 书生八式之【绿底上下】：上 1/3 浅绿色块 + 深钴蓝剪纸美术字
# -------------------------------------------------------------
def render_shusheng_top_green(
    bg_image_path,
    output_path,
    title="电 影 感 封 面",
    sub="一张照片 · 八种排法",
    en_sub="ONE PHOTO · EIGHT MOODS"
):
    print(f"🎬 [Top Green] 正在渲染【绿底上下 1/3 分割】封面...")
    base_img = Image.open(bg_image_path).convert("RGBA")
    w, h = base_img.size
    scale = w / 1024.0

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. 上方占 30% 画高的苹果绿色块 #98C064
    block_h = int(h * 0.30)
    c_light_green = (152, 192, 100, 255)
    c_cobalt_blue = (6, 70, 154, 255)   # 深钴蓝 #06469A

    draw.rectangle([(0, 0), (w, block_h)], fill=c_light_green)

    # 在绿色块底边缘模拟一小片微弱阴影（4% 跨层立体感）
    shadow_band = Image.new("RGBA", (w, int(18 * scale)), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_band)
    for y in range(int(18 * scale)):
        alpha = int(45 * (1.0 - y / (18 * scale)))
        s_draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    overlay.paste(shadow_band, (0, block_h), shadow_band)

    # 2. 居中大主标题：深钴蓝剪纸美术大字
    f_main = get_font(FONT_SMILEY, int(54 * scale))
    bbox_m = draw.textbbox((0, 0), title, font=f_main)
    mw = bbox_m[2] - bbox_m[0]
    draw.text(((w - mw) // 2, int(h * 0.05)), title, font=f_main, fill=c_cobalt_blue)

    # 3. 中间细无衬线英文
    f_en = get_font(FONT_SMILEY, int(14 * scale))
    bbox_e = draw.textbbox((0, 0), en_sub, font=f_en)
    ew = bbox_e[2] - bbox_e[0]
    draw.text(((w - ew) // 2, int(h * 0.16)), en_sub, font=f_en, fill=c_cobalt_blue)

    # 4. 副标题居中：深蓝粗黑体
    f_sub = get_font(FONT_SMILEY, int(24 * scale))
    bbox_s = draw.textbbox((0, 0), sub, font=f_sub)
    sw = bbox_s[2] - bbox_s[0]
    draw.text(((w - sw) // 2, int(h * 0.22)), sub, font=f_sub, fill=c_cobalt_blue)

    # 5. 下方照片两侧电影标注
    f_tiny = get_font(FONT_WENKAI, int(12 * scale))
    draw.text((int(w * 0.05), block_h + int(24 * scale)), "SEE YOUR / PHOTO DIFFERENTLY", font=f_tiny, fill=(152, 192, 100, 230))
    draw.text((int(w * 0.65), block_h + int(24 * scale)), "COLOR / TELLS A STORY", font=f_tiny, fill=(152, 192, 100, 230))

    final_img = Image.alpha_composite(base_img, overlay).convert("RGB")
    final_img.save(output_path, quality=95)
    print(f"✅ 绿底上下 1/3 分割封面生成成功: {output_path}")
    return output_path

if __name__ == "__main__":
    src_anime = os.path.join(ASSETS_DIR, "agnes_1790006749_b2b755da.png")
    src_beauty = os.path.join(ASSETS_DIR, "agnes_1789995999_1670.png")
    src_macro = os.path.join(ASSETS_DIR, "macro_beauty_02.png")

    print("🚀 启动书生经典海报排版引擎...")

    # 1. 绿色刊头胶囊
    render_shusheng_capsule_green(
        src_anime,
        os.path.join(ASSETS_DIR, "cover_shusheng_capsule_green.png"),
        title="铜钟与蒸汽城",
        sub_1="她修时间",
        sub_2="也修人心",
        author_en="AGNES STUDIO // FILM",
        author_cn="书生视觉排版"
    )

    # 2. 红色错位夹击竖排
    render_shusheng_split_red(
        src_anime,
        os.path.join(ASSETS_DIR, "cover_shusheng_split_red.png"),
        chars_left="铜钟",
        chars_right="蒸汽",
        sub_1="普通自拍照",
        sub_2="也能排成电影大片"
    )

    # 3. 侧边黄色贯穿色带
    render_shusheng_side_yellow(
        src_beauty,
        os.path.join(ASSETS_DIR, "cover_shusheng_side_yellow.png"),
        title_top="电影感",
        title_bottom="封面",
        sub="一张自拍 · 八种排法"
    )

    # 4. 绿底上下 1/3 色块
    render_shusheng_top_green(
        src_macro,
        os.path.join(ASSETS_DIR, "cover_shusheng_top_green.png"),
        title="电影感人像写真",
        sub="高审美视觉 · 矢量排版",
        en_sub="AGNES STUDIO // SHU SHENG COVER 02"
    )
    print("✨ 全套书生经典封面已成功渲染并落地！")
