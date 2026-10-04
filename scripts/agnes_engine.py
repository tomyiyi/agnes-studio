#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio · Agnes 智能文案引擎 (Agnes Engine)
===============================================
通过 New API 网关调用 Agnes 模型，为 Agnes Studio 提供 AI 辅助能力：
  1. 智能海报文案与需求简报生成 (generate_creative_brief)
  2. 物理光学级 Agnes 生图提示词编译与增强 (refine_prompt_for_agnes)
  3. 视觉主体识别 (detect_visual_subjects) — Agnes 多模态视觉
  4. 视觉质量审查 (vision_inspect_artwork) — Agnes 多模态视觉审美质检

迁移说明 (2026-09-30)：原 gemini_engine.py 已废弃，Gemini 已从 New API 下线
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import threading
import time
import uuid
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

# ═══════════════════════════════════════════════════
# Agnes API 全局限速器（令牌桶算法）
# 学习自 github.com/prabakannan/agnes-video-generator/core/api/rate_limiter.py
# 所有 Agnes API 调用共享同一个令牌桶，确保总调用频率不超过限制。
# ═══════════════════════════════════════════════════

# Agnes API 每分钟调用上限（可通过环境变量 AGNES_RATE_LIMIT 覆盖）
_AGNES_RATE_LIMIT = int(os.environ.get("AGNES_RATE_LIMIT", "20"))
# 预留 20% 余量：实际允许 80% 的配额
_SAFETY_FACTOR = 0.8
_EFFECTIVE_RATE = _AGNES_RATE_LIMIT * _SAFETY_FACTOR  # 16 次/分钟 ≈ 3.75 秒/次

# 重试配置（学习自 agnes-video-generator/core/api/agnes_chat.py）
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 15  # 秒，指数退避基数：15s → 30s → 45s


class AgnesRateLimiter:
    """令牌桶限速器（线程安全）。当令牌不足时，acquire() 会阻塞直到令牌可用。"""

    def __init__(self, rate_per_minute: float = _EFFECTIVE_RATE, max_burst: int = 4):
        self.max_tokens = min(max_burst, rate_per_minute)
        self.refill_rate = rate_per_minute / 60.0  # tokens per second
        self.tokens = float(self.max_tokens)
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()
        self._total_waits = 0
        self._total_wait_seconds = 0.0

    def acquire(self) -> None:
        """阻塞式获取一个令牌。桶中有令牌则立即消耗返回，否则等待。"""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return
            wait_time = (1.0 - self.tokens) / self.refill_rate
            self.tokens = 0.0
            self.last_refill = now + wait_time
            if wait_time > 0.05:
                self._total_waits += 1
            self._total_wait_seconds += wait_time
        if wait_time > 0.05:
            print(f"[RateLimiter] 限速等待 {wait_time:.1f}s", flush=True)
        time.sleep(wait_time)

    @property
    def stats(self) -> dict:
        return {
            "total_waits": self._total_waits,
            "total_wait_seconds": round(self._total_wait_seconds, 1),
            "effective_rate_per_min": round(self.refill_rate * 60.0, 1),
            "max_burst": self.max_tokens,
        }


_rate_limiter_instance = None
_rate_limiter_lock = threading.Lock()


def get_rate_limiter() -> "AgnesRateLimiter":
    """获取全局速率限制器实例（线程安全单例）。"""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        with _rate_limiter_lock:
            if _rate_limiter_instance is None:
                _rate_limiter_instance = AgnesRateLimiter()
    return _rate_limiter_instance


def reset_rate_limiter() -> None:
    """重置全局限速器（仅用于测试）。"""
    global _rate_limiter_instance
    with _rate_limiter_lock:
        _rate_limiter_instance = None




def load_credentials() -> Tuple[str, Optional[str], str]:
    """读取网关配置，返回 (base_url, api_key, chat_model)
    
    优先级：
    1. AGNES_* 专用环境变量（最高优先级）
    2. local_key.json 本地配置文件（开发机配置，优先于通用环境变量，避免被旧环境劫持）
    3. GEMINI_* / OPENAI_* 通用环境变量（回退）
    4. 默认常量
    """
    # 1. Agnes 专用环境变量
    agnes_base = (
        os.getenv("AGNES_CHAT_BASE_URL")
        or os.getenv("AGNES_BASE_URL")
        or os.getenv("AGNES_GATEWAY_URL")
    )
    agnes_key = (
        os.getenv("AGNES_API_KEY")
        or os.getenv("AGNES_GATEWAY_KEY")
        or os.getenv("NEW_API_KEY")
    )
    env_model = (
        os.getenv("AGNES_CHAT_MODEL")
        or os.getenv("AGNES_MODEL")
        or os.getenv("GEMINI_CHAT_MODEL")
        or os.getenv("GEMINI_MODEL")
        or os.getenv("CHAT_MODEL")
    )

    # 2. 本地配置文件
    file_base = None
    file_key = None
    file_model = None
    if KEY_PATH.exists():
        try:
            with open(KEY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            file_base = data.get("chat_base_url") or data.get("base_url")
            file_key = data.get("api_key")
            if not env_model:
                chat_models = (data.get("models") or {}).get("chat") or []
                allowed_models = [item for item in chat_models if item in CHAT_MODEL_ALLOWLIST]
                if allowed_models:
                    file_model = allowed_models[0]
        except Exception:
            pass

    # 3. 通用环境变量回退（过滤已知的环境化石，避免劫持默认网关）
    _FOSSIL_BASE_MARKERS = (":18045", ":8045", ":3000")
    fallback_base = (
        os.getenv("NEW_API_BASE_URL")
        or os.getenv("GEMINI_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENAI_API_BASE")
    )
    if fallback_base and any(m in fallback_base for m in _FOSSIL_BASE_MARKERS):
        fallback_base = None
    fallback_key = (
        os.getenv("NEW_API_KEY")
        or os.getenv("ANTIGRAVITY_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )

    base = agnes_base or file_base or fallback_base or DEFAULT_BASE
    key = agnes_key or file_key or fallback_key or None
    model = env_model or file_model or DEFAULT_CHAT_MODEL

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


def _should_retry_http(status_code: int) -> bool:
    """判断 HTTP 状态码是否应重试：5xx 和 429 重试，4xx 不重试。"""
    return status_code >= 500 or status_code == 429


def _chat_endpoints(explicit_base: Optional[str] = None) -> List[str]:
    """解析聊天网关端点链：请求显式地址排首位，其次走 failover 环境配置。

    延迟导入 gateway_failover（函数内 import）：该模块顶部有
    ``from agnes_engine import load_credentials``，顶层互引会形成循环导入。
    """
    chain: List[str] = []
    if explicit_base:
        chain.append(explicit_base.rstrip("/"))
    try:
        from gateway_failover import resolve_endpoints
        for u in resolve_endpoints("chat"):
            if u and u not in chain:
                chain.append(u)
    except Exception:
        pass
    if not chain:
        try:
            base, _, _ = load_credentials()
            if base:
                chain.append(base.rstrip("/"))
        except Exception:
            pass
    return chain or [DEFAULT_BASE]


def _new_trace_id(provided: Optional[str] = None) -> str:
    """调用层统一 trace id：调用方透传优先，否则生成 agnes-<12hex>。"""
    if provided is not None and str(provided).strip():
        return str(provided).strip()[:64]
    return "agnes-" + uuid.uuid4().hex[:12]


# 公开别名：供 studio_server 等调用方复用同一 trace 生成规则
new_trace_id = _new_trace_id


def call_agnes(
    messages: List[Dict[str, Any]],
    *,
    model: Optional[str] = None,
    temperature: float = 0.6,
    max_tokens: int = 1500,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    trace_id: Optional[str] = None,
    failover: bool = True,
    timeout: int = 45,
    retries: int = 2,
) -> Dict[str, Any]:
    """通过 New API 网关调用 Agnes 聊天模型（令牌桶限速 + 指数退避重试 + 网关故障转移）。

    故障转移语义（端点链 = 请求显式 base_url 排首位 + gateway_failover 环境链去重）：
      - 单端点时行为与旧版完全一致（同端点重试 + 退避）。
      - 多端点时：非末端点遇到端点级故障（连接失败/超时/5xx/429）立即切换
        到下一个端点（不 sleep）；末端点保留旧版重试 + 退避语义。
      - 其他 4xx 视为请求本身问题，直接返回，不切换、不重试。
    职责划分：本函数负责调用时的主动容错；/api/gateway/health（probe_gateway）
    只做被动探活（GET /models，不触发模型推理），两者不重叠。
    """
    trace = _new_trace_id(trace_id)
    def_base, def_key, def_model = load_credentials()
    base = (base_url or def_base).rstrip("/")
    target_model = model or def_model

    if not (base.startswith("http://") or base.startswith("https://")):
        return {"ok": False,
                "error": f"Base URL 必须以 http:// 或 https:// 开头: {base}",
                "model": target_model, "trace_id": trace}

    # 第 14 轮安全收紧：api_key="" 表示调用方明确"无密钥"
    # （如目标为非配置网关），此时不再回退 def_key，防止服务端密钥被 SSRF
    # 带往任意地址；只有 None 才走默认密钥解析（保持旧调用方行为）。
    key = def_key if api_key is None else api_key
    endpoints = _chat_endpoints(base_url) if failover else [base]

    payload = {
        "model": target_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    body = json.dumps(payload).encode("utf-8")

    last_err = None
    max_retries = max(0, int(retries))
    for ep_idx, ep in enumerate(endpoints):
        is_last = ep_idx == len(endpoints) - 1
        # 非末端点只试 1 次：故障立即切换；末端点保留旧版重试语义
        tries = (max_retries + 1) if is_last else 1
        req = urllib.request.Request(
            f"{ep}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "AgnesStudio-AgnesEngine/2.0",
                **({"Authorization": f"Bearer {key}"} if key else {}),
            },
        )
        for t in range(tries):
            get_rate_limiter().acquire()
            t0 = time.time()
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                cost_s = round(time.time() - t0, 2)
                if not isinstance(data, dict):
                    last_err = "响应非有效 JSON 对象"
                else:
                    err_val = data.get("error")
                    if err_val is not None:
                        err_msg = (err_val.get("message") if isinstance(err_val, dict)
                                   else str(err_val))
                        last_err = f"API Error: {err_msg}"
                    elif not data.get("choices") or not isinstance(data.get("choices"), list):
                        last_err = "API 返回的 choices 列表为空"
                    else:
                        choice = data["choices"][0] if isinstance(data["choices"][0], dict) else {}
                        msg = choice.get("message") or {}
                        content = msg.get("content", "")
                        print(f"[Agnes][{trace}] OK {ep} {cost_s}s", flush=True)
                        return {
                            "ok": True,
                            "content": content,
                            "model": target_model,
                            "cost_s": cost_s,
                            "usage": data.get("usage", {}),
                            "trace_id": trace,
                            "endpoint_used": ep,
                        }
            except urllib.error.HTTPError as e:
                try:
                    err_body = e.read().decode("utf-8", "ignore")[:300]
                except Exception:
                    err_body = str(e)
                finally:
                    try:
                        e.close()
                    except Exception:
                        pass
                last_err = f"HTTP {e.code}: {err_body}"
                if not _should_retry_http(e.code):
                    print(f"[Agnes][{trace}] 致命错误，直接返回: {last_err}", flush=True)
                    return {"ok": False, "error": last_err,
                            "model": target_model, "trace_id": trace}
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
            # —— 可重试故障：非末端点立即切换；末端点按旧语义退避重试
            if not is_last:
                nxt = endpoints[ep_idx + 1]
                print(f"[Agnes][{trace}] 端点故障切换 {ep} -> {nxt}: {last_err}",
                      flush=True)
                break
            if t < tries - 1:
                delay = _RETRY_BASE_DELAY * (t + 1)
                print(f"[Agnes][{trace}] 重试 {t + 1}/{max_retries}，{delay}s 后: {last_err}",
                      flush=True)
                time.sleep(delay)
    return {"ok": False, "error": last_err, "model": target_model,
            "trace_id": trace}


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
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    智能生成商业级海报简报与排版文案
    遵循中文排印规范、10:1字阶、盘古之白与对角拆字美学
    """
    trace = _new_trace_id(trace_id)
    if not topic or not str(topic).strip():
        return {"ok": False, "error": "主题内容不能为空", "trace_id": trace}

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
        trace_id=trace,
    )

    if not res.get("ok"):
        return {"ok": False, "error": res.get("error"), "trace_id": res.get("trace_id")}

    raw_text = res.get("content", "")
    json_str = _strip_markdown_codeblock(raw_text)

    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            return {"ok": False, "error": "简报格式非字典对象", "raw": raw_text, "trace_id": trace}
        # 强制执行盘古之白与标点修整
        data["title"] = apply_fix(str(data.get("title", "")))
        data["subtitle"] = str(data.get("subtitle", "")).upper()
        data["body"] = apply_fix(str(data.get("body", "")))
        data["author"] = apply_fix(str(data.get("author", "AGNES STUDIO")))
        return {"ok": True, "brief": data, "cost_s": res.get("cost_s"), "trace_id": res.get("trace_id")}
    except Exception as e:
        return {
            "ok": False,
            "error": f"JSON解析失败: {e}",
            "raw": raw_text,
            "trace_id": trace,
        }


def refine_prompt_for_agnes(
    raw_prompt: str,
    *,
    aspect_ratio: str = "1:1",
    negative_space_zone: str = "top-left",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    将普通的自然语言提示词编译为 Agnes 物理光学级专业 Prompt
    注入相机镜头、打光方案、粒子质感与文字预留负空间
    """
    trace = _new_trace_id(trace_id)
    if not raw_prompt or not str(raw_prompt).strip():
        return {"ok": False, "error": "原始提示词不能为空", "trace_id": trace}

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
        trace_id=trace,
    )

    if not res.get("ok"):
        return {"ok": False, "error": res.get("error"), "trace_id": res.get("trace_id")}

    enhanced = res.get("content", "").strip().strip('"').strip("'")
    return {"ok": True, "prompt": enhanced, "cost_s": res.get("cost_s"), "trace_id": res.get("trace_id")}


def detect_visual_subjects(
    image_path: str,
    *,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> List[Dict[str, float]]:
    """
    使用 Agnes 多模态视觉能力检测图片中的人脸与高显著性主体保护区。
    返回标准化的 0.0 ~ 1.0 浮点坐标列表：[{"x_min": ..., "x_max": ..., "y_min": ..., "y_max": ...}]
    """
    if not image_path:
        return []

    try:
        img_file = Path(image_path).resolve()
        if not img_file.is_file():
            return []
        data_uri = encode_image_data_uri(img_file)
    except Exception as e:
        print(f"⚠️ [Agnes Vision] 准备图片异常: {e}")
        return []

    try:
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

        res = call_agnes(
            messages,
            model=model,
            temperature=0.1,
            max_tokens=400,
            base_url=base_url,
            api_key=api_key,
        trace_id=trace_id,
        )

        if not res.get("ok"):
            return []

        raw = _strip_markdown_codeblock(res.get("content", ""))
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            valid_boxes = []
            for b in parsed:
                if isinstance(b, dict) and all(k in b for k in ("x_min", "x_max", "y_min", "y_max")):
                    try:
                        x0 = max(0.0, min(1.0, float(b["x_min"])))
                        x1 = max(0.0, min(1.0, float(b["x_max"])))
                        y0 = max(0.0, min(1.0, float(b["y_min"])))
                        y1 = max(0.0, min(1.0, float(b["y_max"])))
                        valid_boxes.append({
                            "x_min": min(x0, x1),
                            "x_max": max(x0, x1),
                            "y_min": min(y0, y1),
                            "y_max": max(y0, y1),
                        })
                    except (ValueError, TypeError):
                        continue
            return valid_boxes
    except Exception as e:
        print(f"⚠️ [Agnes Vision] 主体识别异常: {e}")
    return []


def vision_inspect_artwork(
    image_path: str,
    title: str = "",
    *,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    对生成的排版海报或留白底图进行 Agnes 多模态视觉审美质检与安全区评估
    """
    trace = _new_trace_id(trace_id)
    if not image_path:
        return {"ok": False, "error": "图片路径不能为空", "trace_id": trace}

    try:
        img_file = Path(image_path).resolve()
        if not img_file.is_file():
            return {"ok": False, "error": f"文件不存在: {image_path}", "trace_id": trace}
        data_uri = encode_image_data_uri(img_file)
    except Exception as e:
        return {"ok": False, "error": f"读取文件异常: {e}", "trace_id": trace}

    try:
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

        res = call_agnes(
            messages,
            model=model,
            temperature=0.3,
            max_tokens=600,
            base_url=base_url,
            api_key=api_key,
        trace_id=trace,
        )

        if not res.get("ok"):
            return {"ok": False, "error": res.get("error"), "trace_id": res.get("trace_id")}

        raw = _strip_markdown_codeblock(res.get("content", ""))
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            return {"ok": False, "error": "质检结果格式非字典对象", "raw": raw, "trace_id": trace}
        return {"ok": True, "inspection": parsed, "cost_s": res.get("cost_s"), "trace_id": res.get("trace_id")}
    except Exception as e:
        return {"ok": False, "error": f"质检执行失败: {e}", "trace_id": trace}



# 向后兼容
def detect_visual_subjects_gemini(*args, **kwargs) -> List[Dict[str, float]]:
    """已废弃：请使用 detect_visual_subjects"""
    return detect_visual_subjects(*args, **kwargs)

if __name__ == "__main__":
    print("=== 测试 Agnes 引擎基本能力 ===")
    brief_res = generate_creative_brief("江南雨季茶舍与空山新雨", platform="wechat", tone="neo-chinese")
    print("简报结果:", json.dumps(brief_res, ensure_ascii=False, indent=2)[:500])
