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
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from env_config import resolve_chrome_path, ASSETS_DIR, FONTS_DIR
from agnes_engine import (
    load_credentials,
    call_gemini,
    generate_creative_brief,
    refine_prompt_for_agnes,
    detect_visual_subjects_gemini,
    vision_inspect_artwork,
)
from pro_poster_renderer import render_html_to_poster, get_base64_image
from vision_subject_detector import detect_faces, check_occlusion

try:
    from studio_server import generate_custom_poster_html
except ImportError:
    generate_custom_poster_html = None  # type: ignore

DEFAULT_TEST_STEPS = (1, 2, 3, 4, 5, 6, 7)
DEFAULT_BRIEF_TOPIC = "极简宋韵美学与雨过天青"
DEFAULT_BRIEF_PLATFORM = "wechat"
DEFAULT_BRIEF_TONE = "neo-chinese"
DEFAULT_OPTICAL_PROMPT = "a solitary celadon cup on stone table, dark background"
DEFAULT_ASPECT_RATIO = "2.35:1"
DEFAULT_NEGATIVE_SPACE = "left-half"
DEFAULT_POSTER_STYLE = "cinema_01"
DEFAULT_POSTER_FILENAME = "poster_test_automated.png"


def parse_steps(steps_arg: str | None) -> list[int]:
    """解析以逗号分隔的步骤字符串，默认执行全部 1-7。"""
    if not steps_arg:
        return list(DEFAULT_TEST_STEPS)
    result: list[int] = []
    for item in str(steps_arg).split(","):
        cleaned = item.strip()
        if cleaned.isdigit():
            val = int(cleaned)
            if 1 <= val <= 7 and val not in result:
                result.append(val)
    return result or list(DEFAULT_TEST_STEPS)


def test_step_1_chrome(
    chrome_path_override: str | None = None,
    resolve_fn: Callable[[], str | None] | None = None,
) -> dict[str, Any]:
    """[Test 1/7] 探测跨平台 Chromium 执行路径。"""
    t0 = time.time()
    try:
        if chrome_path_override:
            path = chrome_path_override
        else:
            fn = resolve_fn or resolve_chrome_path
            path = fn()
        exists = bool(path and os.path.exists(path))
        return {
            "step": 1,
            "name": "chrome_detection",
            "ok": exists,
            "path": path or "",
            "exists": exists,
            "cost_s": round(time.time() - t0, 3),
            "error": None if exists else f"Chrome 路径不存在或未检测到: {path}",
        }
    except Exception as exc:
        return {
            "step": 1,
            "name": "chrome_detection",
            "ok": False,
            "path": "",
            "exists": False,
            "cost_s": round(time.time() - t0, 3),
            "error": str(exc),
        }


def test_step_2_gateway(
    mock: bool = False,
    call_agnes_fn: Callable[..., dict[str, Any]] | None = None,
    load_creds_fn: Callable[[], tuple[str, str, str]] | None = None,
) -> dict[str, Any]:
    """[Test 2/7] 校验 New API 凭证与网关探活。"""
    t0 = time.time()
    try:
        creds_loader = load_creds_fn or load_credentials
        base, key, model = creds_loader()
        masked_key = f"{key[:6]}...{key[-4:]}" if key and len(key) > 10 else "***"
        if mock:
            return {
                "step": 2,
                "name": "gateway_ping",
                "ok": True,
                "mock": True,
                "base_url": base,
                "api_key": masked_key,
                "chat_model": model,
                "cost_s": round(time.time() - t0, 3),
                "error": None,
            }
        fn = call_agnes_fn or call_gemini
        test_res = fn([{"role": "user", "content": "ping"}], max_tokens=10)
        ok = bool(test_res.get("ok"))
        cost_s = test_res.get("cost_s", round(time.time() - t0, 3))
        err = None if ok else test_res.get("error", "Gemini 网关调用失败")
        return {
            "step": 2,
            "name": "gateway_ping",
            "ok": ok,
            "mock": False,
            "base_url": base,
            "api_key": masked_key,
            "chat_model": model,
            "cost_s": cost_s,
            "error": err,
        }
    except Exception as exc:
        return {
            "step": 2,
            "name": "gateway_ping",
            "ok": False,
            "mock": mock,
            "cost_s": round(time.time() - t0, 3),
            "error": str(exc),
        }


def test_step_3_brief(
    topic: str = DEFAULT_BRIEF_TOPIC,
    platform: str = DEFAULT_BRIEF_PLATFORM,
    tone: str = DEFAULT_BRIEF_TONE,
    mock: bool = False,
    gen_brief_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """[Test 3/7] 测试 Gemini 创意简报生成 (含盘古之白与对角拆字)。"""
    t0 = time.time()
    try:
        if mock:
            mock_brief = {
                "title": "天青过雨",
                "subtitle": "CELADON IN RAIN",
                "body": "雨过天青云破处，这般颜色做将来。",
                "author": "AGNES FILM TYPE",
                "style_preset": "cinema_01",
            }
            return {
                "step": 3,
                "name": "creative_brief",
                "ok": True,
                "mock": True,
                "brief": mock_brief,
                "cost_s": round(time.time() - t0, 3),
                "error": None,
            }
        fn = gen_brief_fn or generate_creative_brief
        res = fn(topic, platform=platform, tone=tone)
        ok = bool(res.get("ok"))
        brief = res.get("brief", {})
        return {
            "step": 3,
            "name": "creative_brief",
            "ok": ok,
            "mock": False,
            "brief": brief,
            "cost_s": round(time.time() - t0, 3),
            "error": None if ok else res.get("error", "简报生成失败"),
        }
    except Exception as exc:
        return {
            "step": 3,
            "name": "creative_brief",
            "ok": False,
            "mock": mock,
            "brief": {},
            "cost_s": round(time.time() - t0, 3),
            "error": str(exc),
        }


def test_step_4_prompt(
    prompt: str = DEFAULT_OPTICAL_PROMPT,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    negative_space_zone: str = DEFAULT_NEGATIVE_SPACE,
    mock: bool = False,
    refine_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """[Test 4/7] 测试 Gemini 物理光学级 Prompt 增强。"""
    t0 = time.time()
    try:
        if mock:
            mock_prompt = (
                f"{prompt}, 35mm optical lens, f/1.8 depth of field, negative space on {negative_space_zone}, "
                f"cinematic aspect ratio {aspect_ratio}, high fidelity commercial photography."
            )
            return {
                "step": 4,
                "name": "prompt_refine",
                "ok": True,
                "mock": True,
                "prompt": mock_prompt,
                "cost_s": round(time.time() - t0, 3),
                "error": None,
            }
        fn = refine_fn or refine_prompt_for_agnes
        res = fn(prompt, aspect_ratio=aspect_ratio, negative_space_zone=negative_space_zone)
        ok = bool(res.get("ok"))
        return {
            "step": 4,
            "name": "prompt_refine",
            "ok": ok,
            "mock": False,
            "prompt": res.get("prompt", ""),
            "cost_s": round(time.time() - t0, 3),
            "error": None if ok else res.get("error", "Prompt 增强失败"),
        }
    except Exception as exc:
        return {
            "step": 4,
            "name": "prompt_refine",
            "ok": False,
            "mock": mock,
            "prompt": "",
            "cost_s": round(time.time() - t0, 3),
            "error": str(exc),
        }


def test_step_5_detector(
    image_path: Path | str | None = None,
    detect_fn: Callable[..., list[Any]] | None = None,
    occlusion_fn: Callable[..., tuple[bool, Any]] | None = None,
    mock: bool = False,
) -> dict[str, Any]:
    """[Test 5/7] 测试多模态视觉主体识别 (Linux + Gemini 回退)。"""
    t0 = time.time()
    try:
        target_path: Path | None = None
        if image_path is not None:
            target_path = Path(image_path)
        else:
            hero = ASSETS_DIR / "poster_workshop_hero_1080.png"
            if hero.exists():
                target_path = hero
            else:
                candidates = list(ASSETS_DIR.glob("*.png"))
                target_path = candidates[0] if candidates else None

        if target_path is None or not target_path.exists():
            return {
                "step": 5,
                "name": "subject_detection",
                "ok": True,
                "skipped": True,
                "mock": mock,
                "target_image": None,
                "faces": [],
                "occlusion_overlap": False,
                "cost_s": round(time.time() - t0, 3),
                "message": "跳过主体识别测试 (未找到测试图片)",
                "error": None,
            }

        sample_textbox = (0.05, 0.05, 0.45, 0.25)
        if mock:
            mock_faces = [[0.2, 0.2, 0.4, 0.4]]
            return {
                "step": 5,
                "name": "subject_detection",
                "ok": True,
                "mock": True,
                "skipped": False,
                "target_image": str(target_path),
                "faces": mock_faces,
                "face_count": len(mock_faces),
                "sample_textbox": sample_textbox,
                "occlusion_overlap": False,
                "occlusion_zone": None,
                "cost_s": round(time.time() - t0, 3),
                "error": None,
            }

        dfn = detect_fn or detect_faces
        faces = dfn(str(target_path))
        ofn = occlusion_fn or check_occlusion
        has_overlap, zone = ofn(sample_textbox, faces)
        return {
            "step": 5,
            "name": "subject_detection",
            "ok": True,
            "mock": False,
            "skipped": False,
            "target_image": str(target_path),
            "faces": faces,
            "face_count": len(faces),
            "sample_textbox": sample_textbox,
            "occlusion_overlap": bool(has_overlap),
            "occlusion_zone": zone,
            "cost_s": round(time.time() - t0, 3),
            "error": None,
        }
    except Exception as exc:
        return {
            "step": 5,
            "name": "subject_detection",
            "ok": False,
            "mock": mock,
            "skipped": False,
            "target_image": str(image_path or ""),
            "faces": [],
            "cost_s": round(time.time() - t0, 3),
            "error": str(exc),
        }


def test_step_6_rasterizer(
    out_path: Path | str | None = None,
    brief: dict[str, Any] | None = None,
    bg_img: Path | str | None = None,
    render_fn: Callable[..., Any] | None = None,
    html_gen_fn: Callable[..., str] | None = None,
    dry_run: bool = False,
    poster_style: str = DEFAULT_POSTER_STYLE,
) -> dict[str, Any]:
    """[Test 6/7] 测试 Chromium 亚像素商业海报排印与光栅化渲染。"""
    t0 = time.time()
    try:
        target_out = Path(out_path) if out_path else (ASSETS_DIR / DEFAULT_POSTER_FILENAME)
        target_out.parent.mkdir(parents=True, exist_ok=True)
        b = brief or {
            "title": "天青过雨",
            "subtitle": "CELADON IN RAIN",
            "body": "雨过天青云破处，这般颜色做将来。",
            "author": "AGNES FILM TYPE",
        }

        # Resolve background image
        resolved_bg: Path | None = None
        if bg_img is not None:
            resolved_bg = Path(bg_img)
        else:
            hero = ASSETS_DIR / "poster_workshop_hero_1080.png"
            if hero.exists():
                resolved_bg = hero
            else:
                fallback = ASSETS_DIR / "agnes_1789995698_9987.png"
                if fallback.exists():
                    resolved_bg = fallback

        bg_uri = get_base64_image(str(resolved_bg)) if (resolved_bg and resolved_bg.exists()) else ""

        gen_html = html_gen_fn or generate_custom_poster_html
        if gen_html is None:
            raise RuntimeError("generate_custom_poster_html could not be imported from studio_server")

        html = gen_html(
            poster_style,
            b.get("title", "天青过雨"),
            b.get("subtitle", "CELADON IN RAIN"),
            b.get("body", "雨过天青云破处，这般颜色做将来。"),
            b.get("author", "AGNES FILM TYPE"),
            bg_uri,
        )

        if dry_run:
            return {
                "step": 6,
                "name": "html_rasterize",
                "ok": True,
                "dry_run": True,
                "out_path": str(target_out),
                "html_length": len(html),
                "cost_ms": int((time.time() - t0) * 1000),
                "size_kb": 0,
                "error": None,
            }

        rfn = render_fn or render_html_to_poster
        rfn(html, str(target_out))
        if not target_out.exists():
            return {
                "step": 6,
                "name": "html_rasterize",
                "ok": False,
                "dry_run": False,
                "out_path": str(target_out),
                "cost_ms": int((time.time() - t0) * 1000),
                "size_kb": 0,
                "error": f"海报文件未成功生成: {target_out}",
            }

        size_kb = target_out.stat().st_size // 1024
        cost_ms = int((time.time() - t0) * 1000)
        return {
            "step": 6,
            "name": "html_rasterize",
            "ok": True,
            "dry_run": False,
            "out_path": str(target_out),
            "cost_ms": cost_ms,
            "size_kb": size_kb,
            "error": None,
        }
    except Exception as exc:
        return {
            "step": 6,
            "name": "html_rasterize",
            "ok": False,
            "dry_run": dry_run,
            "out_path": str(out_path or ""),
            "cost_ms": int((time.time() - t0) * 1000),
            "size_kb": 0,
            "error": str(exc),
        }


def test_step_7_inspect(
    poster_path: Path | str | None = None,
    title: str = "天青过雨",
    mock: bool = False,
    inspect_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """[Test 7/7] 测试 Gemini 多模态视觉审美审查与质检报告。"""
    t0 = time.time()
    try:
        p = Path(poster_path) if poster_path else (ASSETS_DIR / DEFAULT_POSTER_FILENAME)
        if mock:
            mock_inspection = {
                "aesthetic_score": 93,
                "occlusion_risk": "low",
                "text_legibility": "excellent",
                "negative_space_quality": "balanced",
                "critique": "Mock visual QA passed: high contrast, balanced negative space.",
            }
            return {
                "step": 7,
                "name": "vision_inspection",
                "ok": True,
                "mock": True,
                "poster_path": str(p),
                "inspection": mock_inspection,
                "cost_s": round(time.time() - t0, 3),
                "error": None,
            }
        if not p.exists():
            return {
                "step": 7,
                "name": "vision_inspection",
                "ok": False,
                "mock": False,
                "poster_path": str(p),
                "cost_s": round(time.time() - t0, 3),
                "error": f"待审查海报不存在: {p}",
            }
        fn = inspect_fn or vision_inspect_artwork
        res = fn(str(p), title=title)
        ok = bool(res.get("ok"))
        return {
            "step": 7,
            "name": "vision_inspection",
            "ok": ok,
            "mock": False,
            "poster_path": str(p),
            "inspection": res.get("inspection", {}),
            "cost_s": res.get("cost_s", round(time.time() - t0, 3)),
            "error": None if ok else res.get("error", "视觉质检失败"),
        }
    except Exception as exc:
        return {
            "step": 7,
            "name": "vision_inspection",
            "ok": False,
            "mock": mock,
            "poster_path": str(poster_path or ""),
            "cost_s": round(time.time() - t0, 3),
            "error": str(exc),
        }


def run_integration_suite(
    steps: list[int] | None = None,
    out_dir: Path | str | None = None,
    mock: bool = False,
    skip_network: bool = False,
    dry_run: bool = False,
    verbose: bool = True,
    raise_on_error: bool = False,
    custom_runners: dict[str, Callable] | None = None,
) -> dict[str, Any]:
    """执行 Gemini 智能引擎与全链路排印管线自动化验证套件。"""
    runners = custom_runners or {}
    steps_to_run = parse_steps(",".join(map(str, steps)) if steps else None)
    target_out_dir = Path(out_dir) if out_dir else ASSETS_DIR
    target_out_dir.mkdir(parents=True, exist_ok=True)
    poster_out_file = target_out_dir / DEFAULT_POSTER_FILENAME

    if verbose:
        print("=" * 65)
        print("🚀 [Agnes Studio] 正在执行全链路自动化回归测试...")
        print("=" * 65)

    results: dict[str, Any] = {}
    current_brief: dict[str, Any] = {}
    sample_img_path: str | None = None

    # Step 1: Chrome detection
    if 1 in steps_to_run:
        if verbose:
            print("\n[Test 1/7] 探测跨平台 Chromium 执行路径...")
        r1 = runners.get("step_1", test_step_1_chrome)()
        results["step_1"] = r1
        if verbose:
            if r1.get("ok"):
                print(f"  ✓ 探测到 Chrome 执行文件: {r1.get('path')}")
            else:
                print(f"  ❌ {r1.get('error')}")
        if not r1.get("ok") and raise_on_error:
            raise AssertionError(r1.get("error"))

    # Step 2: Gateway ping
    if 2 in steps_to_run:
        if verbose:
            print("\n[Test 2/7] 校验 New API 凭证与网关探活...")
        use_mock_2 = mock or skip_network
        r2 = runners.get("step_2", test_step_2_gateway)(mock=use_mock_2)
        results["step_2"] = r2
        if verbose:
            print(f"  · Base URL: {r2.get('base_url')}")
            print(f"  · API Key:  {r2.get('api_key')}")
            print(f"  · Chat Model: {r2.get('chat_model')}")
            if r2.get("ok"):
                mode_tag = " (Mock)" if r2.get("mock") else ""
                print(f"  ✓ 网关响应正常!{mode_tag} 耗时: {r2.get('cost_s')}s")
            else:
                print(f"  ❌ 网关调用失败: {r2.get('error')}")
        if not r2.get("ok") and raise_on_error:
            raise AssertionError(r2.get("error"))

    # Step 3: Brief generation
    if 3 in steps_to_run:
        if verbose:
            print("\n[Test 3/7] 测试 Gemini 创意简报生成 (含盘古之白与对角拆字)...")
        use_mock_3 = mock or skip_network
        r3 = runners.get("step_3", test_step_3_brief)(mock=use_mock_3)
        results["step_3"] = r3
        if r3.get("ok"):
            current_brief = r3.get("brief", {})
            if verbose:
                mode_tag = " (Mock)" if r3.get("mock") else ""
                print(f"  ✓ 简报生成成功!{mode_tag} (耗时: {r3.get('cost_s')}s)")
                print(f"    · 主标 T1:    {current_brief.get('title')}")
                print(f"    · 副标 T2:    {current_brief.get('subtitle')}")
                print(f"    · Slogan T3:  {current_brief.get('body')}")
                print(f"    · 署名:       {current_brief.get('author')}")
                print(f"    · 推荐预设:   {current_brief.get('style_preset')}")
        else:
            if verbose:
                print(f"  ❌ 简报生成失败: {r3.get('error')}")
            if raise_on_error:
                raise AssertionError(r3.get("error"))

    # Step 4: Prompt refinement
    if 4 in steps_to_run:
        if verbose:
            print("\n[Test 4/7] 测试 Gemini 物理光学级 Prompt 增强...")
        use_mock_4 = mock or skip_network
        r4 = runners.get("step_4", test_step_4_prompt)(mock=use_mock_4)
        results["step_4"] = r4
        if r4.get("ok"):
            if verbose:
                p_text = r4.get("prompt", "")
                mode_tag = " (Mock)" if r4.get("mock") else ""
                print(f"  ✓ 编译后的 Optical Prompt{mode_tag}: {p_text[:100]}...")
        else:
            if verbose:
                print(f"  ❌ Prompt 增强失败: {r4.get('error')}")
            if raise_on_error:
                raise AssertionError(r4.get("error"))

    # Step 5: Visual subject detection
    if 5 in steps_to_run:
        if verbose:
            print("\n[Test 5/7] 测试多模态视觉主体识别 (Linux + Gemini 回退)...")
        use_mock_5 = mock or skip_network
        r5 = runners.get("step_5", test_step_5_detector)(mock=use_mock_5)
        results["step_5"] = r5
        if r5.get("skipped"):
            if verbose:
                print(f"  ⚠️ {r5.get('message')}")
        elif r5.get("ok"):
            sample_img_path = r5.get("target_image")
            if verbose:
                faces = r5.get("faces", [])
                mode_tag = " (Mock)" if r5.get("mock") else ""
                print(f"  ✓ 主体保护区识别成功{mode_tag}: 检测到 {len(faces)} 个保护区域: {faces}")
                print(f"    · 文本框避障测试: 坐标 {r5.get('sample_textbox')} -> 遮挡状态: {r5.get('occlusion_overlap')}")
        else:
            if verbose:
                print(f"  ❌ 主体识别失败: {r5.get('error')}")
            if raise_on_error:
                raise AssertionError(r5.get("error"))

    # Step 6: Poster rasterization
    if 6 in steps_to_run:
        if verbose:
            print("\n[Test 6/7] 测试 Chromium 亚像素商业海报排印与光栅化渲染...")
        bg_for_step_6 = sample_img_path or (ASSETS_DIR / "agnes_1789995698_9987.png")
        r6 = runners.get("step_6", test_step_6_rasterizer)(
            out_path=poster_out_file,
            brief=current_brief,
            bg_img=bg_for_step_6,
            dry_run=dry_run,
        )
        results["step_6"] = r6
        if r6.get("ok"):
            if verbose:
                if r6.get("dry_run"):
                    print(f"  ✓ [Dry Run] 商业海报 HTML 编译完成! 长度: {r6.get('html_length')} 字节")
                else:
                    print(f"  ✓ 1200x1200 商业海报渲染完成! 耗时: {r6.get('cost_ms')}ms · 大小: {r6.get('size_kb')} KB")
        else:
            if verbose:
                print(f"  ❌ 海报渲染失败: {r6.get('error')}")
            if raise_on_error:
                raise AssertionError(r6.get("error"))

    # Step 7: Vision inspection
    if 7 in steps_to_run:
        if verbose:
            print("\n[Test 7/7] 测试 Gemini 多模态视觉审美审查与质检报告...")
        use_mock_7 = mock or skip_network or dry_run
        insp_target = poster_out_file if poster_out_file.exists() else None
        r7 = runners.get("step_7", test_step_7_inspect)(
            poster_path=insp_target,
            title=current_brief.get("title", "天青过雨"),
            mock=use_mock_7,
        )
        results["step_7"] = r7
        if r7.get("ok"):
            insp = r7.get("inspection", {})
            if verbose:
                mode_tag = " (Mock)" if r7.get("mock") else ""
                print(f"  ✓ 视觉质检完成!{mode_tag} 耗时: {r7.get('cost_s')}s")
                print(f"    · 美学评分:     {insp.get('aesthetic_score')} / 100")
                print(f"    · 遮挡风险:     {insp.get('occlusion_risk')}")
                print(f"    · 文字易读性:   {insp.get('text_legibility')}")
                print(f"    · 留白负空间:   {insp.get('negative_space_quality')}")
                print(f"    · 审稿总监评语: {insp.get('critique')}")
        else:
            if verbose:
                print(f"  ❌ 视觉质检失败: {r7.get('error')}")
            if raise_on_error:
                raise AssertionError(r7.get("error"))

    # Final Summary
    passed_steps = [k for k, v in results.items() if v.get("ok")]
    failed_steps = [k for k, v in results.items() if not v.get("ok")]
    all_ok = len(failed_steps) == 0 and len(passed_steps) == len(steps_to_run)

    if verbose:
        print("\n" + "=" * 65)
        if all_ok:
            print(f"🎉 恭喜！Agnes Studio {len(passed_steps)} 项核心自动化测试全量通过！")
        else:
            print(f"⚠️ Agnes Studio 自动化回归套件完成: {len(passed_steps)} 项通过，{len(failed_steps)} 项失败。")
        print("=" * 65)

    return {
        "ok": all_ok,
        "total_steps": len(steps_to_run),
        "passed": len(passed_steps),
        "failed": len(failed_steps),
        "steps": results,
        "out_dir": str(target_out_dir),
    }


def run_tests(
    steps: list[int] | None = None,
    out_dir: Path | str | None = None,
    mock: bool = False,
    skip_network: bool = False,
    dry_run: bool = False,
    verbose: bool = True,
    raise_on_error: bool = True,
) -> dict[str, Any]:
    """向后兼容的回归测试入口函数。"""
    return run_integration_suite(
        steps=steps,
        out_dir=out_dir,
        mock=mock,
        skip_network=skip_network,
        dry_run=dry_run,
        verbose=verbose,
        raise_on_error=raise_on_error,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="Agnes Studio · Gemini 智能引擎与全链路排印管线自动化验证套件"
    )
    parser.add_argument(
        "--steps",
        type=str,
        default=None,
        help="指定执行的步骤编号，逗号分隔，如 1,2,5,6 (默认全部 1-7)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="启用 Mock 模拟网络与多模态 LLM 调用",
    )
    parser.add_argument(
        "--skip-network",
        action="store_true",
        help="跳过外部网络调用 (步骤 2,3,4,7 自动使用 Mock)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="无头排印渲染 Dry Run 模式 (不实际调用无头 Chrome)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="渲染生成物的输出目录",
    )
    parser.add_argument(
        "--json",
        nargs="?",
        const="-",
        default=None,
        help="以 JSON 格式输出测试结果 (输出至指定文件或 stdout '-')",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="静默模式，减少标准输出日志",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI 主入口函数，返回状态码 0 (成功) 或 1 (失败)。"""
    parser = build_arg_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    try:
        steps = parse_steps(args.steps)
        suite_res = run_integration_suite(
            steps=steps,
            out_dir=args.out_dir,
            mock=args.mock,
            skip_network=args.skip_network,
            dry_run=args.dry_run,
            verbose=not args.quiet,
            raise_on_error=False,
        )
        if args.json:
            json_str = json.dumps(suite_res, ensure_ascii=False, indent=2)
            if args.json == "-":
                print(json_str)
            else:
                p = Path(args.json)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json_str, encoding="utf-8")
        return 0 if suite_res.get("ok") else 1
    except Exception as e:
        if args.json:
            err_payload = {"ok": False, "error": str(e)}
            err_str = json.dumps(err_payload, ensure_ascii=False, indent=2)
            if args.json == "-":
                print(err_str)
            else:
                try:
                    p = Path(args.json)
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(err_str, encoding="utf-8")
                except Exception:
                    print(err_str)
        elif not args.quiet:
            print(f"❌ Gemini 集成验证套件执行失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
