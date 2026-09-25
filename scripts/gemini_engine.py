#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio · Gemini 智能多模态与文案引擎 (Gemini Engine)
=========================================================
通过 New API 网关调用稳定的 Gemini 2.5 Flash / Pro 模型，
为 Agnes Studio 提供全链路 AI 视觉辅助能力：
  1. 智能海报文案与需求简报生成 (generate_creative_brief)
  2. 物理光学级 Agnes 生图提示词编译与增强 (refine_prompt_for_agnes)
  3. 多模态视觉主体识别与避障检测 (detect_visual_subjects)
  4. 视觉与排印美学多模态质量审查 (vision_inspect_artwork)
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from copywriting_rules import apply_fix, lint_copy
except Exception:
    apply_fix = lambda x: x
    lint_copy = lambda x: []

ROOT = SCRIPTS_DIR.parent
KEY_PATH = Path.home() / ".new-api" / "local_key.json"
DEFAULT_BASE = "http://127.0.0.1:3000/v1"
DEFAULT_CHAT_MODEL = "agnes-2.5-flash"


def load_credentials() -> Tuple[str, str, str]:
    """读取网关配置，返回 (base_url, api_key, chat_model)"""
    base, key, model = DEFAULT_BASE, "", DEFAULT_CHAT_MODEL
    if KEY_PATH.exists():
        try:
            with open(KEY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            base = data.get("base_url") or base
            key = data.get("api_key") or key
            chat_models = (data.get("models") or {}).get("chat") or []
            if chat_models:
                model = chat_models[0]
        except Exception:
            pass
    return base.rstrip("/"), key, model


def call_gemini(
    messages: List[Dict[str, Any]],
    *,
    model: Optional[str] = None,
    temperature: float = 0.6,
    max_tokens: int = 1500,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: int = 45,
    retries: int = 2,
) -> Dict[str, Any]:
    """通过 New API 统一网关调用 Gemini 聊天与多模态端点"""
    def_base, def_key, def_model = load_credentials()
    base = (base_url or def_base).rstrip("/")
    key = api_key or def_key
    target_model = model or def_model

    payload = {
        "model": target_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "AgnesStudio-GeminiEngine/1.0",
            **({"Authorization": f"Bearer {key}"} if key else {}),
        },
    )

    last_err = None
    for attempt in range(retries + 1):
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            cost_s = round(time.time() - t0, 2)
            choice = (data.get("choices") or [{}])[0]
            msg = choice.get("message") or {}
            content = msg.get("content", "")
            return {
                "ok": True,
                "content": content,
                "model": target_model,
                "cost_s": cost_s,
                "usage": data.get("usage", {}),
            }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", "ignore")[:300]
            last_err = f"HTTP {e.code}: {err_body}"
        except Exception as e:
            last_err = str(e)
        time.sleep(0.6 * (attempt + 1))

    return {"ok": False, "error": last_err, "model": target_model}


def _strip_markdown_codeblock(text: str) -> str:
    """提取 markdown 代码块内的原始内容"""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text


def generate_creative_brief(
    topic: str,
    *,
    platform: str = "wechat",
    tone: str = "luxury",
    goal: str = "editorial",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    智能生成商业级海报简报与排版文案
    遵循中文排印规范、10:1字阶、盘古之白与对角拆字美学
    """
    sys_prompt = """你是一位国际顶尖视觉创意总监兼中文字体排版大师（熟谙 Muller-Brockmann 瑞士网格系统、中国古典金石碑版与现代院线电影排印）。
请根据用户提供的主题、平台、调性与商业目标，输出一份高水准的海报简报。

排版与文案严苛准则：
1. 主标题（title）：凝练有力（4-10字），富有哲思与视觉张力，适合对角拆字或大字报排布；
2. 英文/辅标题（subtitle）：高审美大写英文或拼音短语，具有国际杂志感；
3. 正文文案（body）：1-2句诗意或格言文案（25-50字），严禁俗套营销辞藻；
4. 标点禁则：必须遵循中文排印规范，中英文之间自动加空格（盘古之白），使用直角引号「」，严禁弯引号“”，逗号句号全角；
5. 生图提示词（gen_prompt）：必须为 Agnes 物理扩散模型量身定制，包含专业摄影用光（如 chiaroscuro, rembrandt lighting）、大师级色彩、超清微距或大景别，且显式指定留白区域（如 negative space on left/top），并添加：no text, no watermark, ultra clean frame；
6. 推荐样式（style_preset）：从 ['cinema_01', 'swiss_01', 'chinese_01', 'cyber_01'] 中选择最契合的一项。

请严格仅输出如下 JSON 格式，不要包含任何多余解释：
{
  "title": "中文主标题",
  "subtitle": "ENGLISH SUBTITLE",
  "body": "正文诗意文案...",
  "author": "创作者/品牌署名",
  "style_preset": "cinema_01",
  "gen_prompt": "English optical prompt for Agnes...",
  "negative_space_focus": "留白方位描述 (如: 画面左上预留60%纯净留白)",
  "design_rationale": "排版与视觉设计阐述 (一句话)"
}"""

    user_prompt = f"创意主题: {topic}\n目标平台: {platform} (尺寸: {'2350x1000' if platform=='wechat' else '1080x1440'})\n美学调性: {tone}\n设计目标: {goal}"

    res = call_gemini(
        [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.6,
        base_url=base_url,
        api_key=api_key,
    )

    if not res.get("ok"):
        return {"ok": False, "error": res.get("error")}

    raw_text = res.get("content", "")
    json_str = _strip_markdown_codeblock(raw_text)

    try:
        data = json.loads(json_str)
        # 强制执行盘古之白与标点修整
        data["title"] = apply_fix(data.get("title", ""))
        data["subtitle"] = data.get("subtitle", "").upper()
        data["body"] = apply_fix(data.get("body", ""))
        data["author"] = apply_fix(data.get("author", "AGNES STUDIO"))
        return {"ok": True, "brief": data, "cost_s": res.get("cost_s")}
    except Exception as e:
        return {
            "ok": False,
            "error": f"JSON解析失败: {e}",
            "raw": raw_text,
        }


def refine_prompt_for_agnes(
    raw_prompt: str,
    *,
    aspect_ratio: str = "1:1",
    negative_space_zone: str = "top-left",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    将普通的自然语言提示词编译为 Agnes 物理光学级专业 Prompt
    注入相机镜头、打光方案、粒子质感与文字预留负空间
    """
    sys_prompt = """你是一位专门为 Agnes 图像扩散模型撰写 Prompt 的物理光学专家与电影摄影指导。
任务：将用户的原始想法扩展为极致专业的商业摄影/艺术生成 Prompt（英文）。
必须包含要素：
1. 核心主体精细材质、高光与阴影过渡；
2. 摄影器材与参数（例如 Hasselblad H6D-100c, 80mm f/2.8 lens, shallow depth of field）；
3. 精确照明方案（例如 soft volumetric light, cinematic chiaroscuro, dramatic rim light）；
4. 明确的留白与负空间指令（根据指定方位保留大面积干净、平滑的背景以供中文字体排版）；
5. 负面排除后缀：absolutely no text, no watermark, no logo, no blur, ultra clean seamless composition.

请直接输出优化后的纯英文 Prompt，不要包含额外解释或引号。"""

    user_prompt = f"原始提示词: {raw_prompt}\n画幅比例: {aspect_ratio}\n建议留白方位: {negative_space_zone}"

    res = call_gemini(
        [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
        base_url=base_url,
        api_key=api_key,
    )

    if not res.get("ok"):
        return {"ok": False, "error": res.get("error")}

    enhanced = res.get("content", "").strip().strip('"').strip("'")
    return {"ok": True, "prompt": enhanced, "cost_s": res.get("cost_s")}


def detect_visual_subjects_gemini(
    image_path: str,
    *,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Dict[str, float]]:
    """
    使用 Gemini 2.5 Flash 多模态视觉能力检测图片中的人脸与高显著性主体保护区。
    返回标准化的 0.0 ~ 1.0 浮点坐标列表：[{"x_min": ..., "x_max": ..., "y_min": ..., "y_max": ...}]
    """
    img_file = Path(image_path).resolve()
    if not img_file.is_file():
        return []

    try:
        data_bytes = img_file.read_bytes()
        ext = img_file.suffix.lower().replace(".", "")
        mime = "image/png" if ext == "png" else "image/jpeg"
        b64 = base64.b64encode(data_bytes).decode("utf-8")
        data_uri = f"data:{mime};base64,{b64}"

        prompt = (
            "Analyze this image and identify all human faces, key figures, or primary focal subject regions that MUST NOT be covered by poster text. "
            "Return strictly a JSON array of objects with normalized coordinates (range 0.0 to 1.0): "
            "[{\"x_min\": float, \"x_max\": float, \"y_min\": float, \"y_max\": float}]. "
            "Coordinate origin (0, 0) is top-left, and (1.0, 1.0) is bottom-right. "
            "If no human faces or focal subjects are present, return []. Output ONLY the JSON array."
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            }
        ]

        res = call_gemini(
            messages,
            model="agnes-2.5-flash",
            temperature=0.1,
            max_tokens=400,
            base_url=base_url,
            api_key=api_key,
        )

        if not res.get("ok"):
            return []

        raw = _strip_markdown_codeblock(res.get("content", ""))
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            valid_boxes = []
            for b in parsed:
                if isinstance(b, dict) and all(k in b for k in ("x_min", "x_max", "y_min", "y_max")):
                    valid_boxes.append({
                        "x_min": max(0.0, min(1.0, float(b["x_min"]))),
                        "x_max": max(0.0, min(1.0, float(b["x_max"]))),
                        "y_min": max(0.0, min(1.0, float(b["y_min"]))),
                        "y_max": max(0.0, min(1.0, float(b["y_max"]))),
                    })
            return valid_boxes
    except Exception as e:
        print(f"⚠️ [Gemini Vision] 主体识别异常: {e}")
    return []


def vision_inspect_artwork(
    image_path: str,
    title: str = "",
    *,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    对生成的排版海报或留白底图进行 Gemini 多模态视觉审美质检与安全区评估
    """
    img_file = Path(image_path).resolve()
    if not img_file.is_file():
        return {"ok": False, "error": f"文件不存在: {image_path}"}

    try:
        data_bytes = img_file.read_bytes()
        ext = img_file.suffix.lower().replace(".", "")
        mime = "image/png" if ext == "png" else "image/jpeg"
        b64 = base64.b64encode(data_bytes).decode("utf-8")
        data_uri = f"data:{mime};base64,{b64}"

        prompt = f"""请作为资深平面设计审稿总监与视觉质检员，对这张商业海报作品进行多模态审美审查。
当前标题内容: 「{title}」

审查维度：
1. 主体与排版避障（Face & Subject Occlusion）：文字是否压住五官或关键主体；
2. 负空间留白（Negative Space & Breathing）：是否有充分的呼吸感；
3. 字体层级与排印（Typography Hierarchy）：字阶对比、可读性与字距美感；
4. 综合美学评分（0 - 100 分）；
5. 明确的修改建议与改进点。

请严格仅输出如下 JSON 格式：
{{
  "aesthetic_score": 92,
  "occlusion_risk": "low" | "medium" | "high",
  "text_legibility": "excellent" | "good" | "poor",
  "negative_space_quality": "balanced" | "crowded" | "empty",
  "critique": "简明扼要的专业评语（50字内）",
  "suggestions": ["修改建议1", "修改建议2"]
}}"""

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            }
        ]

        res = call_gemini(
            messages,
            model="agnes-2.5-flash",
            temperature=0.3,
            max_tokens=600,
            base_url=base_url,
            api_key=api_key,
        )

        if not res.get("ok"):
            return {"ok": False, "error": res.get("error")}

        raw = _strip_markdown_codeblock(res.get("content", ""))
        parsed = json.loads(raw)
        return {"ok": True, "inspection": parsed, "cost_s": res.get("cost_s")}
    except Exception as e:
        return {"ok": False, "error": f"质检执行失败: {e}"}


if __name__ == "__main__":
    print("=== 测试 Gemini 引擎基本能力 ===")
    brief_res = generate_creative_brief("江南雨季茶舍与空山新雨", platform="wechat", tone="neo-chinese")
    print("简报结果:", json.dumps(brief_res, ensure_ascii=False, indent=2))
