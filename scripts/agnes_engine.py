#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio · Agnes 智能文案引擎 (Agnes Engine)
===============================================
通过 New API 网关调用 Agnes 模型，为 Agnes Studio 提供 AI 辅助能力：
  1. 智能海报文案与需求简报生成 (generate_creative_brief)
  2. 物理光学级 Agnes 生图提示词编译与增强 (refine_prompt_for_agnes)
  3. 视觉主体识别 (detect_visual_subjects) — 暂无可用视觉模型，优雅降级
  4. 视觉质量审查 (vision_inspect_artwork) — 暂无可用视觉模型，返回明确状态

迁移说明 (2026-09-30)：原 gemini_engine.py 已废弃，Gemini 已从 New API 下线
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
DEFAULT_BASE = "http://127.0.0.1:13000/v1"
DEFAULT_CHAT_MODEL = "agnes-3.0-flash"
CHAT_MODEL_ALLOWLIST = {
    "agnes-3.0-flash",
    "agnes-2.5-flash",
    "agnes-2.5-pro",
    "agnes-2.5-pro-alpha",
    "agnes-2.5-pro-beta",
    "agnes-2.0-flash",
}


def load_credentials() -> Tuple[str, str, str]:
    """读取网关配置，返回 (base_url, api_key, chat_model)"""
    env_base = os.getenv("AGNES_BASE_URL") or os.getenv("GEMINI_BASE_URL") or os.getenv("OPENAI_BASE_URL")
    env_key = os.getenv("AGNES_API_KEY") or os.getenv("ANTIGRAVITY_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    env_model = os.getenv("AGNES_CHAT_MODEL") or os.getenv("AGNES_MODEL") or os.getenv("GEMINI_CHAT_MODEL") or os.getenv("GEMINI_MODEL") or os.getenv("CHAT_MODEL")

    base = env_base or DEFAULT_BASE
    key = env_key
    model = env_model or DEFAULT_CHAT_MODEL

    if KEY_PATH.exists():
        try:
            with open(KEY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 优先使用 New API 网关配置
            if not env_base:
                base = data.get("chat_base_url") or DEFAULT_BASE
            # 使用本地 New API 密钥
            if not key:
                key = data.get("api_key") or key
            if not env_model:
                chat_models = (data.get("models") or {}).get("chat") or []
                allowed_models = [item for item in chat_models if item in CHAT_MODEL_ALLOWLIST]
                if allowed_models:
                    model = allowed_models[0]
        except Exception:
            pass
    return base.rstrip("/"), key, model


def encode_image_data_uri(image_path: Path) -> str:
    """读取图片并转换为带 MIME 的 Base64 Data URI"""
    ext = image_path.suffix.lower().lstrip(".")
    if ext == "png":
        mime = "image/png"
    elif ext == "webp":
        mime = "image/webp"
    elif ext == "gif":
        mime = "image/gif"
    elif ext in ("jpg", "jpeg"):
        mime = "image/jpeg"
    else:
        mime = "image/jpeg"
    b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def call_agnes(
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
    """通过 New API 网关调用 Agnes 聊天模型"""
    def_base, def_key, def_model = load_credentials()
    base = (base_url or def_base).rstrip("/")
    target_model = model or def_model

    if not (base.startswith("http://") or base.startswith("https://")):
        return {"ok": False, "error": f"Base URL 必须以 http:// 或 https:// 开头: {base}", "model": target_model}

    key = api_key or def_key

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
            "User-Agent": "AgnesStudio-AgnesEngine/2.0",
            **({"Authorization": f"Bearer {key}"} if key else {}),
        },
    )

    last_err = None
    max_retries = max(0, int(retries))
    for attempt in range(max_retries + 1):
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            cost_s = round(time.time() - t0, 2)
            if not isinstance(data, dict):
                last_err = "响应非有效 JSON 对象"
                if attempt < max_retries:
                    time.sleep(0.6 * (attempt + 1))
                continue
            if "error" in data:
                err_val = data["error"]
                err_msg = err_val.get("message") if isinstance(err_val, dict) else str(err_val)
                last_err = f"API Error: {err_msg}"
                if attempt < max_retries:
                    time.sleep(0.6 * (attempt + 1))
                continue

            choices = data.get("choices")
            if not choices or not isinstance(choices, list):
                last_err = "API 返回的 choices 列表为空"
                if attempt < max_retries:
                    time.sleep(0.6 * (attempt + 1))
                continue

            choice = choices[0] if isinstance(choices[0], dict) else {}
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

        if attempt < max_retries:
            time.sleep(0.6 * (attempt + 1))

    return {"ok": False, "error": last_err, "model": target_model}


# 向后兼容：旧代码调用 call_gemini 时自动转到 call_agnes
def call_gemini(*args, **kwargs) -> Dict[str, Any]:
    """已废弃：请使用 call_agnes"""
    return call_agnes(*args, **kwargs)


def _strip_markdown_codeblock(text: str) -> str:
    """提取 markdown 代码块内的原始内容"""
    if not isinstance(text, str):
        return ""
    text = text.strip()
    match = re.search(r"```(?:[a-zA-Z0-9_-]+)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
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
    if not topic or not str(topic).strip():
        return {"ok": False, "error": "主题内容不能为空"}

    clean_topic = str(topic).strip()
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

    user_prompt = f"创意主题: {clean_topic}\n目标平台: {platform} (尺寸: {'2350x1000' if platform=='wechat' else '1080x1440'})\n美学调性: {tone}\n设计目标: {goal}"

    res = call_agnes(
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
        if not isinstance(data, dict):
            return {"ok": False, "error": "简报格式非字典对象", "raw": raw_text}
        # 强制执行盘古之白与标点修整
        data["title"] = apply_fix(str(data.get("title", "")))
        data["subtitle"] = str(data.get("subtitle", "")).upper()
        data["body"] = apply_fix(str(data.get("body", "")))
        data["author"] = apply_fix(str(data.get("author", "AGNES STUDIO")))
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
    if not raw_prompt or not str(raw_prompt).strip():
        return {"ok": False, "error": "原始提示词不能为空"}

    clean_prompt = str(raw_prompt).strip()
    sys_prompt = """你是一位专门为 Agnes 图像扩散模型撰写 Prompt 的物理光学专家与电影摄影指导。
任务：将用户的原始想法扩展为极致专业的商业摄影/艺术生成 Prompt（英文）。
必须包含要素：
1. 核心主体精细材质、高光与阴影过渡；
2. 摄影器材与参数（例如 Hasselblad H6D-100c, 80mm f/2.8 lens, shallow depth of field）；
3. 精确照明方案（例如 soft volumetric light, cinematic chiaroscuro, dramatic rim light）；
4. 明确的留白与负空间指令（根据指定方位保留大面积干净、平滑的背景以供中文字体排版）；
5. 负面排除后缀：absolutely no text, no watermark, no logo, no blur, ultra clean seamless composition.

请直接输出优化后的纯英文 Prompt，不要包含额外解释或引号。"""

    user_prompt = f"原始提示词: {clean_prompt}\n画幅比例: {aspect_ratio}\n建议留白方位: {negative_space_zone}"

    res = call_agnes(
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


_VISION_UNAVAILABLE_MSG = (
    "当前 New API 网关无可用视觉理解模型（Agnes 全系文本模型不支持图像输入），"
    "视觉检测/审查功能暂不可用。"
)


def detect_visual_subjects(
    image_path: str,
    *,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Dict[str, float]]:
    """
    检测图片中的人脸与高显著性主体保护区。
    当前无可用视觉模型，返回空列表（调用方应视为"无保护区"继续流程）。
    """
    print(f"⚠️ [Agnes Vision] {_VISION_UNAVAILABLE_MSG}")
    return []


# 向后兼容
def detect_visual_subjects_gemini(*args, **kwargs) -> List[Dict[str, float]]:
    """已废弃：请使用 detect_visual_subjects"""
    return detect_visual_subjects(*args, **kwargs)


def vision_inspect_artwork(
    image_path: str,
    title: str = "",
    *,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    视觉与排印美学质量审查。
    当前无可用视觉模型，返回明确的不支持状态（而非静默失败）。
    """
    return {
        "ok": False,
        "error": _VISION_UNAVAILABLE_MSG,
        "vision_available": False,
        "image_path": image_path,
        "title": title,
    }
    print("简报结果:", json.dumps(brief_res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    print("=== 测试 Agnes 引擎基本能力 ===")
    brief_res = generate_creative_brief("江南雨季茶舍与空山新雨", platform="wechat", tone="neo-chinese")
    print("简报结果:", json.dumps(brief_res, ensure_ascii=False, indent=2)[:500])
