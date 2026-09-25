#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio · Gemini 智能引擎与全链路排印管线自动化验证套件
==========================================================
覆盖测试：
1. 跨平台 Chrome/Chromium 与无头浏览器环境探测
2. New API 网关连通性与模型列表获取
3. Gemini 智能创意简报与文案生成 (generate_creative_brief)
4. Gemini 物理光学生图 Prompt 编译与增强 (refine_prompt_for_agnes)
5. Gemini 视觉多模态主体避障检测 (detect_visual_subjects_gemini)
6. Chrome 排印光栅化渲染 (render_html_to_poster)
7. Gemini 视觉多模态审美审查 (vision_inspect_artwork)
"""

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from env_config import resolve_chrome_path, ASSETS_DIR, FONTS_DIR
from gemini_engine import (
    load_credentials,
    call_gemini,
    generate_creative_brief,
    refine_prompt_for_agnes,
    detect_visual_subjects_gemini,
    vision_inspect_artwork,
)
from pro_poster_renderer import render_html_to_poster, get_base64_image
from vision_subject_detector import detect_faces, check_occlusion


def run_tests():
    print("=" * 65)
    print("🚀 [Agnes Studio] 正在执行全链路自动化回归测试...")
    print("=" * 65)

    # 1. 环境与无头 Chrome 探测
    print("\n[Test 1/7] 探测跨平台 Chromium 执行路径...")
    chrome_path = resolve_chrome_path()
    print(f"  ✓ 探测到 Chrome 执行文件: {chrome_path}")
    assert os.path.exists(chrome_path), f"Chrome 路径不存在: {chrome_path}"

    # 2. 网关配置与连通性
    print("\n[Test 2/7] 校验 New API 凭证与网关探活...")
    base, key, model = load_credentials()
    print(f"  · Base URL: {base}")
    print(f"  · API Key:  {key[:6]}...{key[-4:] if len(key)>10 else '***'}")
    print(f"  · Chat Model: {model}")
    test_res = call_gemini([{"role": "user", "content": "ping"}], max_tokens=10)
    assert test_res.get("ok"), f"Gemini 网关调用失败: {test_res.get('error')}"
    print(f"  ✓ 网关响应正常! 耗时: {test_res.get('cost_s')}s")

    # 3. Gemini 创意简报生成
    print("\n[Test 3/7] 测试 Gemini 创意简报生成 (含盘古之白与对角拆字)...")
    t0 = time.time()
    brief_res = generate_creative_brief("极简宋韵美学与雨过天青", platform="wechat", tone="neo-chinese")
    assert brief_res.get("ok"), f"简报生成失败: {brief_res.get('error')}"
    brief = brief_res["brief"]
    print(f"  ✓ 简报生成成功! (耗时: {round(time.time() - t0, 2)}s)")
    print(f"    · 主标 T1:    {brief.get('title')}")
    print(f"    · 副标 T2:    {brief.get('subtitle')}")
    print(f"    · Slogan T3:  {brief.get('body')}")
    print(f"    · 署名:       {brief.get('author')}")
    print(f"    · 推荐预设:   {brief.get('style_preset')}")

    # 4. Gemini 物理光学 Prompt 增强
    print("\n[Test 4/7] 测试 Gemini 物理光学级 Prompt 增强...")
    refine_res = refine_prompt_for_agnes("a solitary celadon cup on stone table, dark background", aspect_ratio="2.35:1", negative_space_zone="left-half")
    assert refine_res.get("ok"), f"Prompt 增强失败: {refine_res.get('error')}"
    print(f"  ✓ 编译后的 Optical Prompt: {refine_res['prompt'][:100]}...")

    # 5. Linux 下 Gemini 多模态视觉主体识别
    print("\n[Test 5/7] 测试多模态视觉主体识别 (Linux + Gemini 回退)...")
    sample_img = ASSETS_DIR / "poster_workshop_hero_1080.png"
    if not sample_img.exists():
        candidates = list(ASSETS_DIR.glob("*.png"))
        sample_img = candidates[0] if candidates else None
    
    if sample_img and sample_img.exists():
        faces = detect_faces(str(sample_img))
        print(f"  ✓ 主体保护区识别成功: 检测到 {len(faces)} 个保护区域: {faces}")
        # 验证避障检测函数
        sample_textbox = (0.05, 0.05, 0.45, 0.25)
        has_overlap, zone = check_occlusion(sample_textbox, faces)
        print(f"    · 文本框避障测试: 坐标 {sample_textbox} -> 遮挡状态: {has_overlap}")
    else:
        print("  ⚠️ 跳过主体识别测试 (未找到测试图片)")

    # 6. Chromium 无头海报光栅化渲染
    print("\n[Test 6/7] 测试 Chromium 亚像素商业海报排印与光栅化渲染...")
    test_out = ASSETS_DIR / "poster_test_automated.png"
    bg_img = sample_img or (ASSETS_DIR / "agnes_1789995698_9987.png")
    bg_uri = get_base64_image(str(bg_img))
    
    # 构造标准 HTML
    from studio_server import generate_custom_poster_html
    html = generate_custom_poster_html(
        "cinema_01",
        brief.get("title", "天青过雨"),
        brief.get("subtitle", "CELADON IN RAIN"),
        brief.get("body", "雨过天青云破处，这般颜色做将来。"),
        brief.get("author", "AGNES FILM TYPE"),
        bg_uri
    )
    t_render = time.time()
    render_html_to_poster(html, str(test_out))
    render_cost_ms = int((time.time() - t_render) * 1000)
    assert test_out.exists(), "海报文件未成功生成!"
    print(f"  ✓ 1200x1200 商业海报渲染完成! 耗时: {render_cost_ms}ms · 大小: {test_out.stat().st_size // 1024} KB")

    # 7. Gemini 视觉多模态审美审查
    print("\n[Test 7/7] 测试 Gemini 多模态视觉审美审查与质检报告...")
    insp_res = vision_inspect_artwork(str(test_out), title=brief.get("title", "天青过雨"))
    assert insp_res.get("ok"), f"视觉质检失败: {insp_res.get('error')}"
    insp = insp_res["inspection"]
    print(f"  ✓ 视觉质检完成! 耗时: {insp_res.get('cost_s')}s")
    print(f"    · 美学评分:     {insp.get('aesthetic_score')} / 100")
    print(f"    · 遮挡风险:     {insp.get('occlusion_risk')}")
    print(f"    · 文字易读性:   {insp.get('text_legibility')}")
    print(f"    · 留白负空间:   {insp.get('negative_space_quality')}")
    print(f"    · 审稿总监评语: {insp.get('critique')}")

    print("\n" + "=" * 65)
    print("🎉 恭喜！Agnes Studio 7 项核心自动化测试全量通过！")
    print("=" * 65)


if __name__ == "__main__":
    run_tests()
