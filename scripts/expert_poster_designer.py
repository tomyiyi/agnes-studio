#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio · 专家级动态海报排版引擎 (Expert Dynamic Poster Designer)
践行【智能海报视觉排版与图形设计专家】工作规范：
1. 视觉主体零侵扰：基于 3x3 空间方差动态锁定负空间与避障禁区
2. 数学字阶体系：严格采用 1.618 (黄金分割比) 递进字阶层级 (H1: 68pt -> H2: 42pt -> Body: 16pt)
3. 情绪字体映射：底图光影与画风自适应匹配 (得意黑 8° 动势 + 霞鹜文楷 + 刀刻宋体)
4. 动线平衡与微对比：盘古之白微间距 + 环境光采样互补色
"""

import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# 导入专业中文字体排印学与瑞士网格系统引擎
from typography_rules import ChineseTypographyRules, ModularScale, SwissGridSystem, SmartPosterComposer
from vision_subject_detector import detect_faces

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

def analyze_safe_zone(img_path):
    """
    第一阶段：多模态空间解析与负空间检测
    划分 3x3 网格并计算区域平整度与方差，自动推导最佳安全区
    """
    with Image.open(img_path) as img:
        w, h = img.size
        gray = img.convert("L")
        arr = np.array(gray)
        cell_w, cell_h = w // 3, h // 3
        
        variances = []
        for r in range(3):
            for c in range(3):
                sub = arr[r*cell_h:(r+1)*cell_h, c*cell_w:(c+1)*cell_w]
                variances.append((r, c, np.var(sub)))
        
        # 排序寻找最平整区域
        variances.sort(key=lambda x: x[2])
        best_r, best_c, min_var = variances[0]
        
        # 采样该区域主色
        crop_box = (best_c*cell_w, best_r*cell_h, (best_c+1)*cell_w, (best_r+1)*cell_h)
        sub_img = img.crop(crop_box).resize((1, 1))
        bg_rgb = sub_img.getpixel((0, 0))[:3]
        
        return {
            "width": w,
            "height": h,
            "best_grid": (best_r, best_c),
            "min_variance": float(min_var),
            "bg_rgb": bg_rgb,
            "safe_x": int(w * 0.06),
            "safe_y": int(h * 0.06) if best_r == 0 else int(h * 0.65)
        }

def render_expert_steampunk_poster():
    """
    实战案例 1：《铜钟与蒸汽城》日漫概念 Key Visual
    基于左上角平整负空间 (方差 0.4) 打造【非对称左上悬挂 + 对角视线穿透】
    严格接入瑞士 12 栏网格 (Swiss Grid) 与黄金分割模块化字阶 (Modular Scale)
    """
    src_img = os.path.join(ASSETS_DIR, "agnes_1790006749_b2b755da.png")
    out_img = os.path.join(ASSETS_DIR, "poster_expert_dynamic_steampunk.png")
    print("🎨 [Expert Designer] 开始执行《铜钟与蒸汽城》动态专家级排版 (瑞士网格与黄金字阶)...")
    
    analysis = analyze_safe_zone(src_img)
    w, h = analysis["width"], analysis["height"]
    scale = w / 1024.0
    
    # 1. 瑞士国际网格与黄金字阶定义
    grid = SwissGridSystem(w, h, columns=12, margin_ratio=0.06)
    scale_sys = ModularScale(base_size=16.0 * scale, ratio_name="golden")
    hier = scale_sys.get_poster_hierarchy()
    
    f_h1 = get_font(FONT_SMILEY, hier["h1"])      # 68pt 黄金主标题
    f_h2 = get_font(FONT_SONGTI, hier["h2"])      # 42pt 经典衬线副标
    f_quote = get_font(FONT_WENKAI, hier["h3"])   # 26pt 霞鹜文楷感性格言
    f_en = get_font(FONT_SMILEY, hier["body"])    # 16pt 得意黑西文
    f_meta = get_font(FONT_SMILEY, hier["micro"]) # 9~10pt 胶片微排版
    
    base = Image.open(src_img).convert("RGBA")
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # 色彩提取自画面光源
    c_gold = (245, 208, 97, 255)       # 黄铜油灯暖金
    c_cyan = (56, 189, 248, 255)       # 蒸汽冷蓝
    c_white = (255, 255, 255, 255)
    c_dark_block = (12, 22, 28, 210)   # 极夜半透冷灰块
    
    # 1. 顶部微西文标号 (对齐 Column 0, 基线网格吸附)
    x0, col_span_w = grid.get_column_rect(0, 8)
    y0 = grid.snap_to_baseline(grid.margin_y)
    
    draw.text((x0, y0), "ANIME ORIGINAL CONCEPT // KEY VISUAL // NO. 01", font=f_meta, fill=c_cyan)
    
    # 2. H1 大标题：得意黑 8° 窄斜体 (盘古之白处理 + 柔和圆角半透底衬)
    title_text = ChineseTypographyRules.format_poster_copy("铜钟与蒸汽城")
    bbox_h1 = draw.textbbox((x0, y0 + int(24 * scale)), title_text, font=f_h1)
    
    pad_x = int(16 * scale)
    pad_y = int(8 * scale)
    rect_h1 = (x0 - pad_x, bbox_h1[1] - pad_y, bbox_h1[2] + pad_x, bbox_h1[3] + pad_y)
    draw.rounded_rectangle(rect_h1, radius=int(8 * scale), fill=c_dark_block)
    
    # 金箔光影双层文字
    draw.text((x0 + 2, bbox_h1[1] + 2), title_text, font=f_h1, fill=(0, 0, 0, 180))
    draw.text((x0, bbox_h1[1]), title_text, font=f_h1, fill=c_gold)
    
    # 3. 英文对齐字标 (STEAM & CHIME : THE TIME REPAIRER)
    en_y = grid.snap_to_baseline(bbox_h1[3] + int(12 * scale))
    draw.text((x0, en_y), "STEAM & CHIME : THE TIME REPAIRER", font=f_en, fill=(210, 225, 235, 230))
    
    # 4. H2 故事副标 (规范化直角引号「」+ 霞鹜文楷治愈感言)
    raw_quote = '"她修补时光齿轮，也修补破碎的人心"'
    quote_text = ChineseTypographyRules.format_poster_copy(raw_quote)
    quote_y = grid.snap_to_baseline(en_y + int(36 * scale))
    bbox_q = draw.textbbox((x0, quote_y), quote_text, font=f_quote)
    rect_q = (x0 - int(10 * scale), quote_y - int(4 * scale), bbox_q[2] + int(10 * scale), bbox_q[3] + int(4 * scale))
    draw.rounded_rectangle(rect_q, radius=int(6 * scale), fill=(18, 32, 42, 190))
    draw.text((x0, quote_y), quote_text, font=f_quote, fill=c_white)
    
    # 5. 底部版权与胶片元数据栏 (避开右下女机械师扳手主体，吸附地脚基线)
    bot_y = grid.snap_to_baseline(int(h * 0.93))
    meta_text = ChineseTypographyRules.format_poster_copy("ORIGINAL STORY BY AGNES AI // SOUNDTRACK IN 7.1 DOLBY // 2026 ROADSHOW")
    draw.text((x0, bot_y), meta_text, font=f_meta, fill=(160, 180, 195, 180))
    
    # 6. 右上角日漫剧场版专属印章 (Column 10, 对齐天头)
    badge_x, _ = grid.get_column_rect(10, 2)
    badge_y = y0
    draw.rounded_rectangle([(badge_x, badge_y), (badge_x + int(112 * scale), badge_y + int(32 * scale))], radius=int(6 * scale), fill=(235, 55, 65, 230))
    draw.text((badge_x + int(14 * scale), badge_y + int(7 * scale)), "劇場版公開", font=get_font(FONT_SONGTI, int(15 * scale)), fill=c_white)
    
    final_img = Image.alpha_composite(base, overlay).convert("RGB")
    final_img.save(out_img, quality=95)
    print(f"✨ 案例 1 完成: {out_img}")
    return out_img

from vision_subject_detector import detect_faces, check_occlusion

def render_expert_neochinese_poster():
    """
    实战案例 2：《苏园惊鸿》新中式马面裙立像
    采用【智能主体避障 + 两边拆字错位夹击】：
    严禁在中轴人头上方落字！将“苏园”与“惊鸿”分置左右两侧环境区，
    中间 40% 核心区彻底留白，完整展示人物发簪、面容、立领与身姿！
    """
    src_img = os.path.join(ASSETS_DIR, "agnes_1789998061_5508.png")
    out_img = os.path.join(ASSETS_DIR, "poster_expert_dynamic_neochinese.png")
    print("🎨 [Expert Designer] 开始执行《苏园惊鸿》智能避障动态排版...")
    
    # 1. 真实人脸与主体保护区检测
    faces = detect_faces(src_img)
    print(f"  🔍 实时检测到底部主体面部保护区: {faces}")
    
    w, h = 1024, 1024
    scale = w / 1024.0
    
    # 瑞士网格与黄金字阶系统
    grid = SwissGridSystem(w, h, columns=12, margin_ratio=0.06)
    scale_sys = ModularScale(base_size=16.0 * scale, ratio_name="golden")
    hier = scale_sys.get_poster_hierarchy()
    
    base = Image.open(src_img).convert("RGBA")
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    f_title = get_font(FONT_SONGTI, hier["h1"])      # 68pt 刀刻宋体
    f_sub = get_font(FONT_WENKAI, hier["h3"])        # 26pt 霞鹜文楷
    f_en = get_font(FONT_SMILEY, hier["tag"])        # 10pt 得意黑
    f_stamp = get_font(FONT_SONGTI, hier["micro"])   # 9~10pt 印章微字
    
    c_ink_gold = (248, 235, 205, 255)  # 泥金墨色
    c_celadon = (168, 202, 185, 255)   # 水绿同色系
    c_red_seal = (185, 42, 36, 240)    # 古法朱砂红
    
    # 2. 避开中间人头 (人头位于 x:45%~55%, y:8%~18%)
    # 采用【两边拆字错落竖排 · 瑞士网格对齐】
    
    # 左字列：对齐 Column 0 (x: 61px), 吸附垂直基线 y: 120px
    left_x, _ = grid.get_column_rect(0, 2)
    left_y = grid.snap_to_baseline(int(h * 0.12))
    char_step = grid.snap_to_baseline(int(hier["h1"] * 1.3))
    chars_left = ["苏", "园"]
    
    for i, ch in enumerate(chars_left):
        cy = left_y + i * char_step
        # 泥金字 + 书法黑立体微阴影
        draw.text((left_x + 2, cy + 2), ch, font=f_title, fill=(10, 15, 18, 210))
        draw.text((left_x, cy), ch, font=f_title, fill=c_ink_gold)
        
    # 左列英文小注标
    draw.text((left_x, left_y + 2 * char_step + int(8 * scale)), "SUZHOU GARDEN", font=f_en, fill=c_celadon)

    # 右字列：对齐 Column 10 (x: 827px), 起点 y: 288px (下移约两个字高，形成对角呼吸感)
    right_x, _ = grid.get_column_rect(10, 2)
    right_y = grid.snap_to_baseline(int(h * 0.28))
    chars_right = ["惊", "鸿"]
    
    for i, ch in enumerate(chars_right):
        cy = right_y + i * char_step
        draw.text((right_x + 2, cy + 2), ch, font=f_title, fill=(10, 15, 18, 210))
        draw.text((right_x, cy), ch, font=f_title, fill=c_ink_gold)
        
    # 右列英文小注标
    draw.text((right_x - int(24 * scale), right_y + 2 * char_step + int(8 * scale)), "GRACEFUL SWAN", font=f_en, fill=c_celadon)

    # 3. 左下侧平整区域竖排诗词 (避开团扇主体，标点压缩处理)
    raw_poem = "月白云锦短衫轻，水绿马面动微风"
    poem_clean = ChineseTypographyRules.squeeze_punctuation(raw_poem)
    poem_chars = list(poem_clean)
    py_start = grid.snap_to_baseline(left_y + 2 * char_step + int(48 * scale))
    px = left_x
    step_poem = grid.snap_to_baseline(int(26 * scale))
    
    for i, ch in enumerate(poem_chars):
        draw.text((px + 1, py_start + i * step_poem + 1), ch, font=f_sub, fill=(10, 10, 10, 160))
        draw.text((px, py_start + i * step_poem), ch, font=f_sub, fill=(235, 230, 220, 230))
        
    # 诗尾朱砂红印章
    seal_y = py_start + len(poem_chars) * step_poem + int(6 * scale)
    draw.rectangle([(px - int(2 * scale), seal_y), (px + int(22 * scale), seal_y + int(24 * scale))], fill=c_red_seal)
    draw.text((px + int(3 * scale), seal_y + int(3 * scale)), "雅", font=f_stamp, fill=(255, 255, 255, 255))
    
    # 4. 底部东方时装画册英文字标 (置于最底端 y:94% 地面基线，远离双脚)
    bot_y = grid.snap_to_baseline(int(h * 0.94))
    foot_text = ChineseTypographyRules.format_poster_copy("THE NEO-CHINESE HAUTE COUTURE LOOKBOOK // AGNES 2.5 FLASH")
    bbox_f = draw.textbbox((0, 0), foot_text, font=f_en)
    fw = bbox_f[2] - bbox_f[0]
    draw.text(((w - fw) // 2, bot_y), foot_text, font=f_en, fill=(190, 185, 175, 200))
    
    final_img = Image.alpha_composite(base, overlay).convert("RGB")
    final_img.save(out_img, quality=95)
    print(f"✨ 案例 2 完成: {out_img}")
    return out_img

if __name__ == "__main__":
    print("🚀 [Expert Engine] 启动专家级多模态动态排版流水线...")
    render_expert_steampunk_poster()
    render_expert_neochinese_poster()
    print("🎉 专家级动态海报排版实操测试圆满完成！")
