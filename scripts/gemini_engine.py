#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
已废弃 (2026-09-30)：Gemini 模型已从 New API 下线，请使用 agnes_engine。
此文件仅为向后兼容保留，所有调用自动转发到 agnes_engine。
"""
from agnes_engine import (
    call_agnes,
    call_gemini,
    generate_creative_brief,
    refine_prompt_for_agnes,
    detect_visual_subjects,
    detect_visual_subjects_gemini,
    vision_inspect_artwork,
    load_credentials,
    encode_image_data_uri,
    DEFAULT_BASE,
    DEFAULT_CHAT_MODEL,
    CHAT_MODEL_ALLOWLIST,
)

__all__ = [
    "call_agnes", "call_gemini", "generate_creative_brief",
    "refine_prompt_for_agnes", "detect_visual_subjects",
    "detect_visual_subjects_gemini", "vision_inspect_artwork",
    "load_credentials", "encode_image_data_uri",
    "DEFAULT_BASE", "DEFAULT_CHAT_MODEL", "CHAT_MODEL_ALLOWLIST",
]
