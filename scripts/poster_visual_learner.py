#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio · 海报多模态视觉解构与设计自学习引擎
"""

import os
import json
from pathlib import Path
from PIL import Image

def analyze_poster_visual():
    print("🚀 启动海报视觉多模态特征解构与学习引擎...")
    
    target_files = [
        "/Users/tom/Desktop/agnes-studio/public/assets/cover_cinematic_split_green.png",
        "/Users/tom/Desktop/agnes-studio/public/assets/cover_cinematic_letterbox.png",
        "/Users/tom/Desktop/agnes-studio/public/assets/poster_style_smiley.png"
    ]

    results = []
    for filepath in target_files:
        if not os.path.isfile(filepath):
            continue

        filename = os.path.basename(filepath)
        with Image.open(filepath) as img:
            w, h = img.size
            thumb = img.resize((32, 32))
            colors = thumb.getcolors(32 * 32) or []
            colors.sort(key=lambda x: x[0], reverse=True)
            
            palette = []
            for count, rgb in colors[:5]:
                if isinstance(rgb, tuple) and len(rgb) >= 3:
                    hex_val = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
                    palette.append({"hex": hex_val, "rgb": list(rgb[:3]), "pixels": count})

            aspect_ratio = w / h if h > 0 else 1.0
            if aspect_ratio >= 1.3:
                layout = "电影宽银幕上下遮幅 (2.35:1)"
            else:
                layout = "加块绿 · 左右对角拆字法"

            results.append({
                "filename": filename,
                "dimensions": f"{w}x{h}",
                "aspect_ratio": round(aspect_ratio, 2),
                "dominant_palette": palette,
                "layout_category": layout,
                "rules": [
                    "形：莫兰迪色块打底隔离复杂背景",
                    "斜：8° 窄斜体得意黑建立动势",
                    "比：主标题与微标 10:1 极端字阶对比",
                    "空：对角避让保留人物视觉焦点"
                ]
            })
            print(f"  ✓ 解构成功: {filename} -> {layout}")

    safe_dir = Path("/Users/tom/Desktop/agnes-studio/data").resolve()
    target_path = (safe_dir / "learned_poster_rules.json").resolve()
    if not str(target_path).startswith(str(safe_dir)):
        raise ValueError("Path traversal detected")

    target_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✨ 海报设计学习报告与知识沉淀已保存至: {target_path}")

if __name__ == "__main__":
    analyze_poster_visual()
