#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio - 统一轻量服务中枢 (Studio Server & Model Gateway)
================================================================
兼具静态资源托管与轻量 API 网关：
1. 托管 public/ 静态资产（HTML/CSS/JS/Fonts/Assets）；
2. GET  /api/config          -> 自动探测本地 New API 配置与默认模型；
3. POST /api/test-connection -> 实时探测 Agnes / New API 端点连通性与延迟；
4. POST /api/generate-image  -> 调用 Agnes 生图模型生成高审美留白底图并持久化；
5. POST /api/render-poster   -> 调用 Chrome 无头渲染管线生成自定义 1200x1200 商业海报。

零额外依赖：完全基于 Python 原生 http.server 与 urllib 构建，开箱即用。
"""

import os
import sys
import json
import time
import base64
import urllib.request
import urllib.error
import urllib.parse
from html import escape
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Optional, Tuple

DIR = Path(__file__).resolve().parent.parent

def ensure_venv():
    """在直接运行服务时，自动自提至项目 .venv 环境（如存在且当前非虚拟环境）"""
    venv_py = DIR / ".venv" / "bin" / "python"
    if venv_py.exists() and sys.executable != str(venv_py) and os.environ.get("AGNES_VENV_SWITCHED") != "1":
        os.environ["AGNES_VENV_SWITCHED"] = "1"
        os.execv(str(venv_py), [str(venv_py)] + sys.argv)

PUBLIC_DIR = DIR / "public"
ASSETS_DIR = PUBLIC_DIR / "assets"

SKILLS_71_PATH = DIR / "data" / "skills_71_index.json"
SKILLS_DATA_PATH = DIR / "data" / "skills.json"

def load_skills_catalog():
    with SKILLS_71_PATH.open(encoding="utf-8") as handle:
        skills = json.load(handle)
    with SKILLS_DATA_PATH.open(encoding="utf-8") as handle:
        categories = json.load(handle)
    normalized = []
    for item in skills.get("skills", []):
        normalized.append({
            "id": item["id"],
            "name": item.get("display_name") or item["id"],
            "call": item.get("declared_skill_name") or item.get("repo_name") or item["id"],
            "group": item.get("group") or "未分类",
            "style": item.get("style") or "",
            "scope": item.get("scope") or "",
            "thumb": None,
            "hifi": False,
        })
    return {"success": True, "skills71": normalized, "categories": categories.get("categories", [])}

def list_rendered_posters(root=ASSETS_DIR, limit=20):
    items = []
    root = Path(root)
    if not root.is_dir():
        return items
    for path in root.glob("poster_custom_*.png"):
        if not path.is_file():
            continue
        stat = path.stat()
        items.append({"name": path.name, "poster_url": f"assets/{path.name}", "full_url": f"/assets/{path.name}", "size_bytes": stat.st_size, "mtime": stat.st_mtime})
    items.sort(key=lambda item: item["mtime"], reverse=True)
    return items[:limit]
GENERATED_DIR = ASSETS_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

FONTS_DIR = DIR / "public" / "fonts"
render_html_to_poster = None

def get_base64_image(image_path):
    """读取本地图片并转为 base64 data URI，确保无头浏览器 100% 离线秒级加载"""
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        ext = os.path.splitext(str(image_path))[1].lower().lstrip(".")
        if ext == "png":
            mime = "image/png"
        elif ext == "webp":
            mime = "image/webp"
        else:
            mime = "image/jpeg"
        return f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"
    except Exception as e:
        print(f"⚠️ [Base64 Error] 读取图片失败 {image_path}: {e}")
        return ""

# 尝试引入海报排版引擎与 Gemini 智能引擎
sys.path.insert(0, str(DIR / "scripts"))
try:
    import env_config
    from pro_poster_renderer import render_html_to_poster as _renderer, FONTS_DIR as _FONTS_DIR
    render_html_to_poster = _renderer
    FONTS_DIR = _FONTS_DIR
except Exception as e:
    print(f"⚠️ [Warning] 排版引擎导入提示: {e}")

try:
    from agnes_engine import (
        generate_creative_brief,
        refine_prompt_for_agnes,
        vision_inspect_artwork,
        load_credentials,
        new_trace_id,
    )
except Exception as e:
    print(f"⚠️ [Warning] Agnes 引擎导入提示: {e}")
    generate_creative_brief = None
    refine_prompt_for_agnes = None
    vision_inspect_artwork = None
    load_credentials = None
    new_trace_id = None

try:
    from gateway_failover import post_with_failover, AllGatewaysFailed, doctor as gateway_doctor
except Exception as e:
    print(f"⚠️ [Warning] 网关故障转移模块导入提示: {e}")
    post_with_failover = None
    AllGatewaysFailed = Exception
    gateway_doctor = None

LOCAL_KEY_PATH = Path.home() / ".new-api" / "local_key.json"
# 网关地址：环境变量优先，默认走本机 New API
# AGNES_IMAGE_BASE_URL: 图像生成网关；AGNES_CHAT_BASE_URL: 文本/视觉网关
# AGNES_BASE_URL / NEW_API_BASE_URL: 通用网关基地址回退
IMAGE_BASE_DEFAULT = (
    os.environ.get("AGNES_IMAGE_BASE_URL")
    or os.environ.get("AGNES_BASE_URL")
    or os.environ.get("NEW_API_BASE_URL")
    or "http://127.0.0.1:13000/v1"
)
CHAT_BASE_DEFAULT = (
    os.environ.get("AGNES_CHAT_BASE_URL")
    or os.environ.get("AGNES_BASE_URL")
    or os.environ.get("NEW_API_BASE_URL")
    or "http://127.0.0.1:13000/v1"
)

def get_default_image_base() -> str:
    """动态获取当前图像生成网关默认地址，支持环境变量优先覆盖。"""
    return (
        os.environ.get("AGNES_IMAGE_BASE_URL")
        or os.environ.get("AGNES_BASE_URL")
        or os.environ.get("NEW_API_BASE_URL")
        or IMAGE_BASE_DEFAULT
    )

def get_default_chat_base() -> str:
    """动态获取当前文本/视觉网关默认地址，支持环境变量优先覆盖。"""
    return (
        os.environ.get("AGNES_CHAT_BASE_URL")
        or os.environ.get("AGNES_BASE_URL")
        or os.environ.get("NEW_API_BASE_URL")
        or CHAT_BASE_DEFAULT
    )

def get_local_newapi_config(key_path: Path | str | None = None) -> dict:
    """读取本地 New API 配置文件（如果存在）"""
    target_path = Path(key_path) if key_path is not None else LOCAL_KEY_PATH
    default_img = get_default_image_base()
    default_chat = get_default_chat_base()
    if target_path.exists():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "detected": True,
                "type": "local_new_api",
                "base_url": data.get("base_url", default_img),
                "image_base_url": data.get("image_base_url", data.get("base_url", default_img)),
                "chat_base_url": data.get("chat_base_url", default_chat),
                "api_key": data.get("api_key", ""),
                "default_model": "agnes-image-2.5-flash",
                "models": data.get("models", {}).get("image_generation", [
                    "agnes-image-2.5-flash",
                    "agnes-image-2.1-flash",
                    "dall-e-3"
                ]),
                "chat_models": data.get("models", {}).get("chat", [
                    "agnes-2.5-flash",
                    "agnes-2.5-pro",
                    "agnes-3.0-flash"
                ])
            }
        except Exception as e:
            print(f"读取本地 New API 配置失败: {e}")
    return {
        "detected": False,
        "type": "none",
        "base_url": default_img,
        "image_base_url": default_img,
        "chat_base_url": default_chat,
        "api_key": "",
        "default_model": "agnes-image-2.5-flash",
        "models": [
            "agnes-image-2.5-flash",
            "agnes-image-2.1-flash",
            "dall-e-3"
        ],
        "chat_models": [
            "agnes-2.5-flash",
            "agnes-2.5-pro",
            "agnes-3.0-flash"
        ]
    }

def resolve_image_base_url(req_body: dict | None = None, local_cfg: dict | None = None) -> str:
    """Resolve the image-generation endpoint without falling back to chat routing."""
    req = req_body if isinstance(req_body, dict) else {}
    cfg = local_cfg if isinstance(local_cfg, dict) else {}
    explicit = str(req.get("image_base_url") or req.get("base_url") or "").strip()
    if explicit:
        return explicit.rstrip("/")

    if cfg.get("detected"):
        configured = cfg.get("image_base_url") or cfg.get("base_url")
        if configured:
            return str(configured).strip().rstrip("/")

    return get_default_image_base().rstrip("/")


def _server_default_chat_base(local_cfg: dict) -> str:
    """无请求覆盖时的服务端默认文本网关地址（密钥绑定的锚点）。"""
    if callable(load_credentials):
        try:
            sb, _, _ = load_credentials()
            if sb:
                return str(sb).strip().rstrip("/")
        except Exception:
            pass
    if local_cfg.get("detected") and local_cfg.get("chat_base_url"):
        return str(local_cfg["chat_base_url"]).strip().rstrip("/")
    return get_default_chat_base().rstrip("/")


def _server_default_key(local_cfg: dict) -> Optional[str]:
    """服务端密钥回退链：load_credentials > AGNES_* 环境变量 > 本地配置 > 通用环境变量。"""
    if callable(load_credentials):
        try:
            _, def_key, _ = load_credentials()
            if def_key:
                return str(def_key).strip()
        except Exception:
            pass
    env_agnes_key = (
        os.getenv("AGNES_API_KEY")
        or os.getenv("AGNES_GATEWAY_KEY")
        or os.getenv("NEW_API_KEY")
    )
    if env_agnes_key:
        return env_agnes_key.strip()
    if local_cfg.get("detected") and local_cfg.get("api_key"):
        return str(local_cfg["api_key"]).strip()
    fallback = os.getenv("ANTIGRAVITY_API_KEY") or os.getenv("OPENAI_API_KEY")
    if fallback:
        return fallback.strip()
    return None


def is_configured_image_gateway(target_base: str, local_cfg: dict | None = None) -> bool:
    """目标是否为服务端配置的图像网关（无请求覆盖时的解析结果）。"""
    cfg = local_cfg if isinstance(local_cfg, dict) else {}
    if cfg.get("detected"):
        configured = (cfg.get("image_base_url")
                      or cfg.get("base_url") or "").strip().rstrip("/")
    else:
        configured = get_default_image_base().rstrip("/")
    target = str(target_base or "").strip().rstrip("/")
    return bool(configured) and target == configured


def is_configured_gateway(target_base: str, local_cfg: dict | None = None) -> bool:
    """目标是否属于服务端配置的合法网关地址（base_url / chat_base_url / image_base_url）。"""
    cfg = local_cfg if isinstance(local_cfg, dict) else {}
    target = str(target_base or "").strip().rstrip("/")
    if not target:
        return False
    if cfg.get("detected"):
        configured_urls = {
            str(cfg.get(k) or "").strip().rstrip("/")
            for k in ("base_url", "chat_base_url", "image_base_url")
        }
    else:
        configured_urls = {
            get_default_image_base().rstrip("/"),
            get_default_chat_base().rstrip("/"),
        }
    configured_urls.discard("")
    return target in configured_urls


def resolve_chat_credentials(req_body: dict | None = None) -> Tuple[str, Optional[str]]:
    """解析用于文本/视觉调用的网关地址与密钥。

    密钥绑定规则（第 12/14 轮安全收紧）：
    1. 请求体显式 api_key 优先；
    2. 请求显式 base_url 与服务端默认网关**精确一致**时，可用服务端密钥回退链；
    3. 请求显式指向其他地址且未自带 key 时，返回 ""（明确无密钥——下游
       不再回退解析、不发送 Authorization 头），防止服务端密钥被 SSRF
       带往任意地址。指向自定义网关的调用方必须自带 api_key。
    """
    req = req_body if isinstance(req_body, dict) else {}
    base_url = req.get("chat_base_url") or req.get("base_url")
    api_key = req.get("api_key")

    explicit_base = str(base_url).strip().rstrip("/") if base_url else ""
    explicit_key = str(api_key).strip() if api_key else ""

    local_cfg = get_local_newapi_config()
    server_base = _server_default_chat_base(local_cfg)
    final_base = explicit_base or server_base

    if explicit_key:
        return final_base, explicit_key
    if explicit_base and explicit_base != server_base:
        return final_base, ""
    return final_base, _server_default_key(local_cfg)


def probe_gateway(base_url: str, timeout: int = 5, api_key: str | None = None) -> dict:
    """轻量探活网关：GET <base>/models。

    设计约束：
    - 本机 New API 的 /models 需要鉴权：服务端如已解析出 key，可经 api_key 参数
      注入到 Authorization 头（仅出站请求头，绝不进入返回结果/日志/前端）；
    - 只做可达性与模型清单探测，不触发任何模型推理调用；
    - 所有异常收敛为 reachable=False 的结构化结果，不抛异常。
    职责划分：本函数是被动探活（面向人/UI 的健康展示）；调用时的主动容错
    由 agnes_engine.call_agnes 内置的网关故障转移负责（基于
    gateway_failover.resolve_endpoints 的端点链），两者不重叠。
    """
    base = str(base_url or "").strip().rstrip("/")
    if not base or not (base.startswith("http://") or base.startswith("https://")):
        return {"base_url": base, "reachable": False, "error": "base_url 非法"}

    models_url = f"{base}/models"
    req = urllib.request.Request(models_url, method="GET")
    req.add_header("User-Agent", "AgnesStudio/1.0")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    start_t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            latency_ms = int((time.time() - start_t) * 1000)
            res_json = json.loads(raw)
            model_list = []
            if isinstance(res_json, dict):
                data = res_json.get("data")
                if isinstance(data, list):
                    model_list = [str(m["id"]) for m in data if isinstance(m, dict) and m.get("id")]
            chat_models = [m for m in model_list if "agnes-3" in m.lower() or "chat" in m.lower()]
            image_models = [m for m in model_list if "image" in m.lower() or "dall-e" in m.lower()]
            return {
                "base_url": base,
                "reachable": True,
                "latency_ms": latency_ms,
                "http_status": getattr(response, "status", 200),
                "model_count": len(model_list),
                "chat_models": chat_models[:8],
                "image_models": image_models[:8],
            }
    except urllib.error.HTTPError as e:
        try:
            e.close()
        except Exception:
            pass
        return {"base_url": base, "reachable": False, "http_status": e.code,
                "error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"base_url": base, "reachable": False, "error": f"连接失败: {e}"}


def list_generated_images(root=GENERATED_DIR, limit=24):
    """Return safe, newest-first generated image metadata for the Studio UI."""
    allowed = {".png", ".jpg", ".jpeg", ".webp"}
    root = Path(root)
    if not root.is_dir():
        return []
    files = [p for p in root.iterdir() if p.is_file() and p.suffix.lower() in allowed]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    items = []
    for path in files[:max(0, int(limit))]:
        stat = path.stat()
        rel = f"assets/generated/{path.name}"
        items.append({
            "name": path.name,
            "file_path": rel,
            "full_url": f"/assets/generated/{path.name}",
            "size_bytes": stat.st_size,
            "mtime": stat.st_mtime,
        })
    return items


class StudioHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path).path.rstrip("/")
        if parsed_path == "/api/generated-images":
            self._send_json({"success": True, "items": list_generated_images()})
            return

        if parsed_path == "/api/rendered-posters":
            self._send_json({"success": True, "items": list_rendered_posters()})
            return

        if parsed_path == "/api/skills-catalog":
            try:
                self._send_json(load_skills_catalog())
            except (OSError, KeyError, TypeError, ValueError) as exc:
                self._send_json({"success": False, "error": f"技能目录读取失败: {exc}"}, status=500)
            return
        if parsed_path == "/api/gateway/health":
            # 网关健康检查：分别探活文本(chat)与图像(image)网关的 /models。
            # 轻量 GET、不触发模型推理调用；服务端解析的 key 仅注入出站请求头，
            # 绝不回显给前端；前端可定时轮询做状态灯。
            # 职责划分收尾（第 10 轮）：主端点（chat/image，带鉴权 + 模型清单）
            # 之外，另经 gateway_failover.doctor 探活故障转移全链（主 + fallback），
            # 使健康展示与 post_with_failover 的实际可用能力一致；链探活不带 key
            #（401/403 记 warn：可达但需认证），doctor 本身永不抛异常。
            chat_base, chat_key = resolve_chat_credentials({})
            local_cfg = get_local_newapi_config()
            image_base = resolve_image_base_url({}, local_cfg)
            image_key = local_cfg.get("api_key") if local_cfg.get("detected") else None
            chat_chain = gateway_doctor("chat") if callable(gateway_doctor) else {"_error": "故障转移模块未就绪"}
            image_chain = gateway_doctor("image") if callable(gateway_doctor) else {"_error": "故障转移模块未就绪"}
            self._send_json({
                "success": True,
                "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "chat": probe_gateway(chat_base, api_key=chat_key),
                "image": probe_gateway(image_base, api_key=image_key),
                "chat_chain": chat_chain,
                "image_chain": image_chain,
            })
            return

        if parsed_path == "/api/config":
            cfg = get_local_newapi_config()
            # 为前端提供脱敏显示的 key 和全量配置（本地配置优先，环境变量密钥回退）
            effective_key = str(cfg.get("api_key") or _server_default_key(cfg) or "").strip()
            masked_key = ""
            if effective_key:
                # 第 17 轮收紧：只保留末 4 位用于识别（业界惯例，
                # Stripe/GitHub 均只展示末 4 位），不再暴露前 6 位——
                # /api/config 无鉴权（局域网可达），前 6 位对识别无增益，
                # 却扩大了密钥已知明文前缀。前端仅作输入框 placeholder。
                masked_key = "..." + effective_key[-4:] if len(effective_key) > 10 else "***"
            
            preset_endpoints = []
            if cfg["detected"] and cfg.get("base_url"):
                preset_endpoints.append({
                    "name": f"探测到的网关 ({cfg['base_url']}) [推荐]",
                    "url": cfg["base_url"]
                })
            preset_endpoints.extend([
                {"name": "本地 New API 负载均衡 (127.0.0.1:13000)", "url": "http://127.0.0.1:13000/v1"},
                {"name": "Agnes AI 官方端点", "url": "https://apihub.agnes-ai.com/v1"},
                {"name": "自定义 / OneAPI 聚合网关", "url": ""}
            ])
            
            resp = {
                "success": True,
                "detected": cfg["detected"],
                "local_key_detected": cfg["detected"],
                "base_url": cfg["base_url"],
                "image_base_url": cfg["image_base_url"],
                "chat_base_url": cfg["chat_base_url"],
                "masked_api_key": masked_key,
                "has_api_key": bool(effective_key),
                # 不向前端回传明文密钥；调用时由服务端按需注入本地密钥
                "api_key": "",
                "default_model": cfg["default_model"],
                "available_models": cfg["models"],
                "chat_models": cfg.get("chat_models", []),
                "preset_endpoints": preset_endpoints
            }
            self._send_json(resp)
            return

        if parsed_path.startswith("/api/") or parsed_path == "/api":
            self._send_json({"success": False, "error": f"Endpoint not found: {parsed_path}"}, status=404)
            return

        super().do_GET()

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path).path.rstrip("/")
        try:
            content_len = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            content_len = 0
        post_data = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            req_body = json.loads(post_data.decode("utf-8"))
            if not isinstance(req_body, dict):
                req_body = {}
        except Exception:
            req_body = {}

        # 1. 连通性测试 API
        if parsed_path == "/api/test-connection":
            base_url = str(
                req_body.get("base_url")
                or req_body.get("chat_base_url")
                or req_body.get("image_base_url")
                or ""
            ).strip().rstrip("/")
            api_key = str(req_body.get("api_key") or "").strip()
            trace = new_trace_id(req_body.get("trace_id")) if new_trace_id else (
                str(req_body.get("trace_id") or "").strip()[:64] or "agnes-noengine")
            if not api_key:
                local_cfg = get_local_newapi_config()
                if local_cfg.get("detected") and is_configured_gateway(base_url, local_cfg):
                    # 安全收紧（第 12/27 轮）：仅当请求地址与本地配置的网关地址之一
                    # 精确一致时才注入服务端密钥。防止 SSRF 密钥外泄。
                    if local_cfg.get("api_key"):
                        api_key = str(local_cfg["api_key"]).strip()

            if not base_url:
                self._send_json({"success": False, "error": "请提供有效的 Base URL", "trace_id": trace}, status=400)
                return

            if not (base_url.startswith("http://") or base_url.startswith("https://")):
                self._send_json({"success": False, "error": "Base URL 必须以 http:// 或 https:// 开头", "trace_id": trace}, status=400)
                return

            models_url = f"{base_url}/models"
            req = urllib.request.Request(models_url, method="GET")
            req.add_header("User-Agent", "AgnesStudio/1.0")
            if api_key:
                req.add_header("Authorization", f"Bearer {api_key}")

            start_t = time.time()
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    raw = response.read().decode("utf-8", errors="replace")
                    latency_ms = int((time.time() - start_t) * 1000)
                    res_json = json.loads(raw)
                    model_list = []
                    if isinstance(res_json, dict) and isinstance(res_json.get("data"), list):
                        model_list = [str(m["id"]) for m in res_json["data"] if isinstance(m, dict) and m.get("id")]
                    
                    # 过滤生图与对话相关模型
                    image_models = [m for m in model_list if "image" in m.lower() or "dall-e" in m.lower()]
                    chat_models = [m for m in model_list if "agnes-3" in m.lower() or "chat" in m.lower()]
                    self._send_json({
                        "success": True,
                        "latency_ms": latency_ms,
                        "model_count": len(model_list),
                        "image_models": image_models or ["agnes-image-2.5-flash", "dall-e-3"],
                        "chat_models": chat_models or ["agnes-2.5-flash", "agnes-3.0-flash"],
                        "all_models": model_list[:15],
                        "trace_id": trace,
                    })
                    return
            except urllib.error.HTTPError as e:
                err_msg = f"HTTP {e.code}: {e.reason}"
                try:
                    err_body = e.read().decode("utf-8")
                    err_json = json.loads(err_body)
                    if "error" in err_json:
                        err_msg = str(err_json["error"])
                except Exception:
                    pass
                finally:
                    try:
                        e.close()
                    except Exception:
                        pass
                self._send_json({"success": False, "error": err_msg,
                                 "code": e.code, "trace_id": trace},
                                status=200)
                return
            except Exception as e:
                self._send_json({"success": False,
                                 "error": f"连接失败: {str(e)}",
                                 "trace_id": trace},
                                status=200)
                return

        # 2. 调用 Agnes 生成留白底图
        # 2. AI 生图（Agnes 图像生成网关：故障转移 + trace）
        if parsed_path == "/api/generate-image":
            local_cfg = get_local_newapi_config()
            base_url = resolve_image_base_url(req_body, local_cfg)
            # 第 14 轮安全收紧：服务端密钥绑定服务端配置的图像网关。
            # 请求显式指向其他地址且未自带 key 时传 ""（明确无密钥——阻止
            # post_with_failover 重新解析默认 key、不发送 Authorization 头）。
            explicit_img_base = str(req_body.get("image_base_url") or req_body.get("base_url") or "").strip().rstrip("/")
            explicit_img_key = str(req_body.get("api_key") or "").strip()
            if explicit_img_key:
                api_key = explicit_img_key
            elif is_configured_image_gateway(base_url, local_cfg):
                api_key = str(local_cfg.get("api_key") or "").strip() or None
            else:
                api_key = ""
            model = str(req_body.get("model") or "agnes-image-2.5-flash").strip()
            prompt = str(req_body.get("prompt") or "").strip()
            size = str(req_body.get("size") or "1024x1024")
            trace = new_trace_id(req_body.get("trace_id")) if new_trace_id else (
                str(req_body.get("trace_id") or "").strip()[:64] or "agnes-noengine")

            if not prompt:
                self._send_json({"success": False, "error": "提示词不能为空",
                                 "trace_id": trace}, status=400)
                return

            if not (base_url.startswith("http://") or base_url.startswith("https://")):
                self._send_json({"success": False, "error": "Base URL 必须以 http:// 或 https:// 开头",
                                 "trace_id": trace}, status=400)
                return

            if post_with_failover is None:
                self._send_json({"success": False, "error": "网关故障转移模块未就绪",
                                 "trace_id": trace}, status=500)
                return

            payload = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "n": 1
            }
            start_t = time.time()
            try:
                res = post_with_failover(
                    "/images/generations", payload, kind="image",
                    timeout=90, api_key=api_key,
                    first_endpoint=base_url,
                )
            except AllGatewaysFailed as e:
                print(f"[Agnes][{trace}] 生图网关全部故障: {e}", flush=True)
                self._send_json({"success": False, "error": f"生图网关全部故障: {e}", "trace_id": trace}, status=500)
                return
            except Exception as e:
                print(f"[Agnes][{trace}] 生图异常: {type(e).__name__}: {e}", flush=True)
                self._send_json({"success": False, "error": f"生图失败: {e}", "trace_id": trace}, status=500)
                return
            cost_s = round(time.time() - start_t, 2)
            if not res.get("ok"):
                err_detail = (res.get("data") or {}).get("error", {})
                err_msg = err_detail.get("message") if isinstance(err_detail, dict) else err_detail
                print(f"[Agnes][{trace}] 生图网关返回错误 HTTP {res.get('status')}: {err_msg}", flush=True)
                self._send_json({"success": False, "error": f"生图网关错误 HTTP {res.get('status')}: {err_msg}",
                                 "trace_id": trace, "endpoint_used": res.get("endpoint_used")}, status=500)
                return
            attempts = res.get("attempts") or []
            failover_note = ""
            if len(attempts) > 1:
                failed = [a for a in attempts if not a.get("ok")]
                if failed:
                    failover_note = " [故障转移: %s]" % ", ".join(
                        "%s→%s" % (a.get("endpoint"), a.get("error") or a.get("status"))
                        for a in failed)
            print(f"[Agnes][{trace}] 生图 OK {res.get('endpoint_used')} {cost_s}s{failover_note}", flush=True)
            res_data = res.get("data") or {}

            remote_url = None
            b64_data = None
            if "data" in res_data and len(res_data["data"]) > 0:
                item = res_data["data"][0]
                remote_url = item.get("url")
                b64_data = item.get("b64_json")

            timestamp = int(time.time())
            out_filename = f"agnes_{timestamp}.png"
            out_path = GENERATED_DIR / out_filename

            # 保存图片到本地 assets/generated（urlretrieve 已废弃，改用 urlopen）
            try:
                if b64_data:
                    import base64
                    with open(out_path, "wb") as img_f:
                        img_f.write(base64.b64decode(b64_data))
                elif remote_url and (remote_url.startswith("http://") or remote_url.startswith("https://")):
                    dl_req = urllib.request.Request(remote_url, headers={"User-Agent": "AgnesStudio/1.0"})
                    with urllib.request.urlopen(dl_req, timeout=60) as dl_resp:
                        with open(out_path, "wb") as img_f:
                            img_f.write(dl_resp.read())
                else:
                    self._send_json({"success": False, "error": "未能从模型响应中提取有效的图片数据", "trace_id": trace}, status=500)
                    return
            except Exception as e:
                self._send_json({"success": False, "error": f"图片落盘失败: {e}", "trace_id": trace}, status=500)
                return

            self._send_json({
                "success": True,
                "cost_seconds": cost_s,
                "file_path": f"assets/generated/{out_filename}",
                "full_url": f"/assets/generated/{out_filename}",
                "model": model,
                "prompt": prompt,
                "trace_id": trace,
                "endpoint_used": res.get("endpoint_used"),
            })
            return

        # 3. 动态渲染自定义商业海报 (Render Poster)
        if parsed_path == "/api/render-poster":
            if not render_html_to_poster:
                self._send_json({"success": False, "error": "排版引擎不可用，请确保已安装 playwright 及其浏览器依赖"}, status=500)
                return

            style = str(req_body.get("style") or "swiss_01")
            title = str(req_body.get("title") or "苏黎世秩序")
            subtitle = str(req_body.get("subtitle") or "STRUCTURE & ESSENCE")
            body = str(req_body.get("body") or "设计不是情绪的宣泄，而是对客观秩序的精确度量。让字符锚定在理性的基准线上。")
            author = str(req_body.get("author") or "TOM // AGNES STUDIO")

            # 兼容前端 background_img 与历史 bg_image 两种字段名
            bg_image_rel = str(req_body.get("bg_image") or req_body.get("background_img") or "assets/poster_pro_swiss_01.png").strip()

            if bg_image_rel.startswith("data:image/"):
                bg_uri = bg_image_rel
            else:
                # 定位底图绝对路径（限制在 public/、experiments/、outputs/ 内，防止路径穿越；支持 public/ 前缀与 query 参数）
                clean_rel = bg_image_rel.split("?")[0].split("#")[0].strip()
                rel_clean = clean_rel.lstrip("/")
                if rel_clean.startswith("public/"):
                    rel_clean = rel_clean[len("public/"):].lstrip("/")
                bg_abs_path = (PUBLIC_DIR / rel_clean).resolve()

                allowed_dirs = [
                    PUBLIC_DIR.resolve(),
                    (DIR / "experiments").resolve(),
                    (DIR / "outputs").resolve(),
                ]
                def is_under_allowed_dir(candidate: Path) -> bool:
                    if not candidate.is_file():
                        return False
                    return any(candidate.is_relative_to(allowed_dir) for allowed_dir in allowed_dirs)

                is_valid = is_under_allowed_dir(bg_abs_path)
                if not is_valid:
                    alt_abs = (DIR / clean_rel.lstrip("/")).resolve()
                    if is_under_allowed_dir(alt_abs):
                        bg_abs_path = alt_abs
                    else:
                        bg_abs_path = ASSETS_DIR / "agnes_1789995698_9987.png"
                bg_uri = get_base64_image(str(bg_abs_path))

            timestamp = int(time.time())
            out_filename = f"poster_custom_{timestamp}.png"
            out_abs_path = str(ASSETS_DIR / out_filename)

            # 根据流派生成 HTML 并光栅化
            html = generate_custom_poster_html(style, title, subtitle, body, author, bg_uri)
            try:
                t0 = time.time()
                render_html_to_poster(html, out_abs_path)
                duration_ms = int((time.time() - t0) * 1000)
                self._send_json({
                    "success": True,
                    "poster_url": f"assets/{out_filename}",
                    "style": style,
                    "timestamp": timestamp,
                    "duration_ms": duration_ms
                })
            except Exception as e:
                self._send_json({"success": False, "error": f"渲染失败: {str(e)}"}, status=500)
            return

        # 4. Gemini / Agnes 智能简报与文案生成
        if parsed_path in ("/api/gemini/generate-brief", "/api/agnes/generate-brief"):
            topic = str(req_body.get("topic") or "").strip()
            platform = str(req_body.get("platform") or "wechat")
            tone = str(req_body.get("tone") or "luxury")
            goal = str(req_body.get("goal") or "editorial")
            trace = new_trace_id(req_body.get("trace_id")) if new_trace_id else (
                str(req_body.get("trace_id") or "").strip()[:64] or "agnes-noengine")

            if not topic:
                self._send_json({"success": False, "error": "请输入创意主题", "trace_id": trace}, status=400)
                return

            base_url, api_key = resolve_chat_credentials(req_body)

            if base_url:
                if not (base_url.startswith("http://") or base_url.startswith("https://")):
                    self._send_json({"success": False, "error": "Base URL 必须以 http:// 或 https:// 开头", "trace_id": trace}, status=400)
                    return

            if not generate_creative_brief:
                self._send_json({"success": False, "error": "Gemini 引擎未就绪", "trace_id": trace}, status=500)
                return

            res = generate_creative_brief(topic, platform=platform, tone=tone, goal=goal, base_url=base_url, api_key=api_key, trace_id=trace)
            if res.get("ok"):
                self._send_json({"success": True, "brief": res["brief"], "cost_s": res.get("cost_s"), "trace_id": res.get("trace_id") or trace})
            else:
                self._send_json({"success": False, "error": res.get("error"), "trace_id": res.get("trace_id") or trace}, status=500)
            return

        # 5. Gemini / Agnes 物理光学 Prompt 编译与增强
        if parsed_path in ("/api/gemini/refine-prompt", "/api/agnes/refine-prompt"):
            raw_prompt = str(req_body.get("prompt") or "").strip()
            aspect_ratio = str(req_body.get("aspect_ratio") or "1:1")
            negative_space_zone = str(req_body.get("negative_space") or "top-left")
            trace = new_trace_id(req_body.get("trace_id")) if new_trace_id else (
                str(req_body.get("trace_id") or "").strip()[:64] or "agnes-noengine")

            if not raw_prompt:
                self._send_json({"success": False, "error": "请输入原始提示词", "trace_id": trace}, status=400)
                return

            base_url, api_key = resolve_chat_credentials(req_body)

            if base_url:
                if not (base_url.startswith("http://") or base_url.startswith("https://")):
                    self._send_json({"success": False, "error": "Base URL 必须以 http:// 或 https:// 开头", "trace_id": trace}, status=400)
                    return

            if not refine_prompt_for_agnes:
                self._send_json({"success": False, "error": "Gemini 引擎未就绪", "trace_id": trace}, status=500)
                return

            res = refine_prompt_for_agnes(raw_prompt, aspect_ratio=aspect_ratio, negative_space_zone=negative_space_zone, base_url=base_url, api_key=api_key, trace_id=trace)
            if res.get("ok"):
                self._send_json({"success": True, "prompt": res["prompt"], "cost_s": res.get("cost_s"), "trace_id": res.get("trace_id") or trace})
            else:
                self._send_json({"success": False, "error": res.get("error"), "trace_id": res.get("trace_id") or trace}, status=500)
            return

        # 6. Gemini / Agnes 视觉多模态审美与排版审查
        if parsed_path in ("/api/gemini/vision-inspect", "/api/agnes/vision-inspect"):
            image_rel = str(req_body.get("image_path") or "").strip()
            title = str(req_body.get("title") or "")
            trace = new_trace_id(req_body.get("trace_id")) if new_trace_id else (
                str(req_body.get("trace_id") or "").strip()[:64] or "agnes-noengine")

            if not image_rel:
                self._send_json({"success": False, "error": "请提供待质检图片路径", "trace_id": trace}, status=400)
                return

            ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
            clean_rel = image_rel.split("?")[0].split("#")[0].strip()
            ext = os.path.splitext(clean_rel)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTS:
                self._send_json({"success": False, "error": "只支持 PNG、JPG、JPEG、WEBP 格式的图片文件", "trace_id": trace}, status=400)
                return

            base_url, api_key = resolve_chat_credentials(req_body)

            if base_url:
                if not (base_url.startswith("http://") or base_url.startswith("https://")):
                    self._send_json({"success": False, "error": "Base URL 必须以 http:// 或 https:// 开头", "trace_id": trace}, status=400)
                    return

            rel_clean = clean_rel.lstrip("/")
            if rel_clean.startswith("public/"):
                rel_clean = rel_clean[len("public/"):].lstrip("/")
            img_abs = (PUBLIC_DIR / rel_clean).resolve()

            allowed_dirs = [
                PUBLIC_DIR.resolve(),
                (DIR / "experiments").resolve(),
                (DIR / "outputs").resolve(),
            ]
            # 第 16 轮安全修复：str.startswith 有前缀碰撞漏洞
            # （如 public_backup 会被误判为 public 的子目录），改用
            # Path.is_relative_to 做带分隔符边界的归属判定。
            is_in_allowed_dir = any(img_abs.is_relative_to(d) for d in allowed_dirs)
            if not is_in_allowed_dir or not img_abs.exists() or not img_abs.is_file():
                alt_abs = (DIR / clean_rel.lstrip("/")).resolve()
                if any(alt_abs.is_relative_to(d) for d in allowed_dirs) and alt_abs.is_file():
                    img_abs = alt_abs
                else:
                    self._send_json({"success": False, "error": f"找不到图片文件: {image_rel}", "trace_id": trace}, status=404)
                    return

            if not vision_inspect_artwork:
                self._send_json({"success": False, "error": "Gemini 引擎未就绪", "trace_id": trace}, status=500)
                return

            res = vision_inspect_artwork(str(img_abs), title=title, base_url=base_url, api_key=api_key, trace_id=trace)
            if res.get("ok"):
                self._send_json({"success": True, "inspection": res["inspection"], "cost_s": res.get("cost_s"), "trace_id": res.get("trace_id") or trace})
            else:
                self._send_json({"success": False, "error": res.get("error"), "trace_id": res.get("trace_id") or trace}, status=500)
            return

        self._send_json({"success": False, "error": f"Endpoint not found: {parsed_path}"}, status=404)

def generate_custom_poster_html(style, title, subtitle, body, author, bg_uri):
    """根据自定义参数生成对应流派的高保真 HTML 排印代码"""
    s = (style or "swiss_01").lower()
    title = escape(str(title or ""), quote=True)
    subtitle = escape(str(subtitle or ""), quote=True)
    body = escape(str(body or ""), quote=True)
    author = escape(str(author or ""), quote=True)
    bg_uri = (
        str(bg_uri or "")
        .replace("\r", "")
        .replace("\n", "")
        .replace("'", "%27")
        .replace('"', "%22")
        .replace("<", "%3C")
        .replace(">", "%3E")
    )

    if "cyber" in s:
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  @font-face {{ font-family: 'SmileySans'; src: url('file://{FONTS_DIR}/SmileySans-Oblique.ttf') format('truetype'); }}
  @font-face {{ font-family: 'LXGWWenKai'; src: url('file://{FONTS_DIR}/LXGWWenKai-Regular.ttf') format('truetype'); }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 1200px; background: #06080d; color: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    position: relative; overflow: hidden; -webkit-font-smoothing: antialiased;
  }}
  .bg-layer {{ position: absolute; inset: 0; background-image: url('{bg_uri}'); background-size: cover; background-position: center; }}
  .corner-l {{ position: absolute; width: 36px; height: 36px; border: 2px solid #00f0ff; pointer-events: none; }}
  .top-left {{ top: 40px; left: 40px; border-right: none; border-bottom: none; }}
  .top-right {{ top: 40px; right: 40px; border-left: none; border-bottom: none; }}
  .bottom-left {{ bottom: 40px; left: 40px; border-right: none; border-top: none; }}
  .bottom-right {{ bottom: 40px; right: 40px; border-left: none; border-top: none; }}
  .hanging-card {{
    position: absolute; top: 60px; left: 60px; width: 580px;
    background: rgba(6, 8, 13, 0.84); backdrop-filter: blur(20px);
    border: 1px solid rgba(0, 240, 255, 0.35); border-radius: 12px; padding: 36px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8); z-index: 10;
  }}
  .badge-tag {{
    display: inline-flex; align-items: center; gap: 8px; font-family: monospace; font-size: 11px;
    color: #00f0ff; background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0, 240, 255, 0.4);
    padding: 3px 10px; border-radius: 4px; letter-spacing: 2px; text-transform: uppercase;
  }}
  .h1-title {{
    font-family: 'SmileySans', sans-serif; font-size: 68px; letter-spacing: 4px; line-height: 1.05;
    margin: 16px 0 10px 0; background: linear-gradient(135deg, #ffffff 0%, #00f0ff 60%, #3b82f6 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .sub-en-title {{ font-family: 'SmileySans', sans-serif; font-size: 14px; letter-spacing: 5px; color: rgba(255,255,255,0.75); margin-bottom: 20px; }}
  .body-poem {{ font-family: 'LXGWWenKai', sans-serif; font-size: 16px; line-height: 1.65; color: #cbd5e1; border-top: 1px solid rgba(255,255,255,0.12); padding-top: 18px; }}
  .bottom-hud {{ position: absolute; bottom: 60px; right: 60px; display: flex; flex-direction: column; align-items: flex-end; gap: 8px; z-index: 10; }}
  .barcode {{ height: 28px; width: 140px; background: repeating-linear-gradient(to right, #fff 0px, #fff 2px, transparent 2px, transparent 4px, #fff 4px, #fff 7px, transparent 7px, transparent 9px); opacity: 0.8; }}
  .serial-num {{ font-family: monospace; font-size: 11px; color: #94a3b8; letter-spacing: 2px; }}
</style></head><body>
  <div class="bg-layer"></div>
  <div class="corner-l top-left"></div><div class="corner-l top-right"></div>
  <div class="corner-l bottom-left"></div><div class="corner-l bottom-right"></div>
  <div class="hanging-card">
    <div class="badge-tag">● TACTICAL HUD // LIVE GENERATED</div>
    <div class="h1-title">{title}</div>
    <div class="sub-en-title">{subtitle}</div>
    <div class="body-poem">{body}</div>
  </div>
  <div class="bottom-hud">
    <div class="barcode"></div>
    <div class="serial-num">AUTHOR: {author} // 2026 SPEC</div>
  </div>
</body></html>"""
    
    elif "chinese" in s:
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  @font-face {{ font-family: 'LXGWWenKai'; src: url('file://{FONTS_DIR}/LXGWWenKai-Regular.ttf') format('truetype'); }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 1200px; background: #080b0f; color: #ffffff;
    font-family: "Songti SC", "Source Han Serif SC", "STSong", serif;
    position: relative; overflow: hidden; -webkit-font-smoothing: antialiased;
  }}
  .bg-layer {{ position: absolute; inset: 0; background-image: url('{bg_uri}'); background-size: cover; background-position: center; }}
  .title-left {{
    position: absolute; top: 120px; left: 100px; writing-mode: vertical-rl;
    font-size: 84px; font-weight: 900; letter-spacing: 28px; color: #ffffff;
    text-shadow: 0 4px 24px rgba(0,0,0,0.85); z-index: 10;
  }}
  .poem-block {{
    position: absolute; top: 130px; left: 240px; writing-mode: vertical-rl;
    font-family: 'LXGWWenKai', sans-serif; font-size: 18px; line-height: 2.2;
    letter-spacing: 6px; color: rgba(255,255,255,0.85);
    text-shadow: 0 2px 10px rgba(0,0,0,0.8); z-index: 10;
  }}
  .seal-red {{
    display: none;
  }}
  .footer-caption {{
    position: absolute; bottom: 50px; left: 100px; font-size: 12px;
    letter-spacing: 4px; color: rgba(255,255,255,0.7); font-family: monospace; z-index: 10;
  }}
</style></head><body>
  <div class="bg-layer"></div>
  <div class="title-left">{title}</div>
  <div class="poem-block">{body}</div>
  <div class="footer-caption">{subtitle} // {author}</div>
</body></html>"""

    elif "cinema" in s:
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  @font-face {{ font-family: 'SmileySans'; src: url('file://{FONTS_DIR}/SmileySans-Oblique.ttf') format('truetype'); }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 1200px; background: #000000; color: #ffffff;
    font-family: "Songti SC", "Source Han Serif SC", "STSong", serif;
    position: relative; overflow: hidden; -webkit-font-smoothing: antialiased;
  }}
  .top-letterbox {{
    position: absolute; top: 0; left: 0; right: 0; height: 140px; background: #000000;
    display: flex; justify-content: space-between; align-items: center; padding: 0 60px;
    font-family: 'SmileySans', sans-serif; font-size: 13px; letter-spacing: 4px;
    color: rgba(255,255,255,0.5); z-index: 20;
  }}
  .screen-container {{
    position: absolute; top: 140px; bottom: 140px; left: 0; right: 0;
    background-image: url('{bg_uri}'); background-size: cover; background-position: center;
  }}
  .center-title-box {{ position: absolute; bottom: 50px; left: 0; right: 0; text-align: center; z-index: 10; }}
  .main-film-title {{ font-size: 68px; font-weight: 900; letter-spacing: 24px; color: #ffffff; text-shadow: 0 4px 20px rgba(0,0,0,0.8); padding-left: 24px; }}
  .sub-film-title {{ font-family: 'SmileySans', sans-serif; font-size: 14px; letter-spacing: 12px; color: #e2e8f0; margin-top: 12px; padding-left: 12px; }}
  .bottom-letterbox {{
    position: absolute; bottom: 0; left: 0; right: 0; height: 140px; background: #000000;
    display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 8px;
    padding: 0 80px; z-index: 20;
  }}
  .billing-block {{ font-family: monospace; font-size: 10px; line-height: 1.4; text-align: center; color: rgba(255, 255, 255, 0.5); letter-spacing: 1.5px; text-transform: uppercase; }}
</style></head><body>
  <div class="top-letterbox">
    <span>AGNES CINEMATIC MASTERWORKS // 2.35:1 WIDESCREEN</span>
    <span>PRESENTED BY {author}</span>
  </div>
  <div class="screen-container">
    <div class="center-title-box">
      <div class="main-film-title">{title}</div>
      <div class="sub-film-title">{subtitle}</div>
    </div>
  </div>
  <div class="bottom-letterbox">
    <div class="billing-block">
      AN AI PRODUCTION "{title}" DIRECTED AND CRAFTED BY {author}<br>
      {body}
    </div>
  </div>
</body></html>"""

    # 默认瑞士网格风格
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  @font-face {{ font-family: 'SmileySans'; src: url('file://{FONTS_DIR}/SmileySans-Oblique.ttf') format('truetype'); }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 1200px; background: #f4f4f0; color: #111827;
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
    position: relative; overflow: hidden; -webkit-font-smoothing: antialiased;
  }}
  .artwork-cutout {{
    position: absolute; right: 50px; bottom: 50px; width: 620px; height: 740px;
    background-image: url('{bg_uri}'); background-size: cover; background-position: center;
    z-index: 2; border: 1px solid #111827; box-shadow: 20px 20px 0px #e11d48;
  }}
  .header-tag {{ position: absolute; top: 50px; left: 50px; font-family: 'SmileySans', sans-serif; font-size: 16px; letter-spacing: 3px; border-bottom: 2px solid #111827; padding-bottom: 8px; width: 440px; }}
  .main-title-block {{ position: absolute; top: 180px; left: 50px; width: 1100px; z-index: 5; }}
  .main-hero-title {{ font-size: 110px; font-weight: 900; letter-spacing: -3px; line-height: 0.9; text-transform: uppercase; color: #111827; }}
  .main-hero-title span {{ color: #e11d48; }}
  .cn-display-title {{ font-size: 40px; font-weight: 800; letter-spacing: 10px; margin-top: 18px; color: #111827; }}
  .manifesto-block {{
    position: absolute; bottom: 120px; left: 50px; width: 440px; z-index: 5;
    background: rgba(244, 244, 240, 0.96); padding: 24px; border-left: 4px solid #111827;
  }}
  .manifesto-text {{ font-size: 14px; line-height: 1.6; color: #374151; }}
  .badge-red {{ display: inline-block; background: #e11d48; color: #ffffff; font-size: 11px; font-weight: 700; padding: 4px 10px; margin-bottom: 12px; letter-spacing: 1px; }}
  .footer-specs {{ position: absolute; bottom: 50px; left: 50px; width: 440px; font-size: 11px; font-family: monospace; color: #6b7280; letter-spacing: 1px; }}
</style></head><body>
  <div class="artwork-cutout"></div>
  <div class="header-tag">KUNSTGEWERBEMUSEUM ZÜRICH // {author}</div>
  <div class="main-title-block">
    <div class="main-hero-title">{subtitle}<span>.</span></div>
    <div class="cn-display-title">{title}</div>
  </div>
  <div class="manifesto-block">
    <div class="badge-red">SWISS INTERNATIONAL STYLE</div>
    <p class="manifesto-text">{body}</p>
  </div>
  <div class="footer-specs">GRID: 12-COLUMN // RATIO: 1.618 // SYSTEM: HELVETICA ACCURACY</div>
</body></html>"""

def run(port=8088):
    server_address = ("", port)
    httpd = HTTPServer(server_address, StudioHTTPRequestHandler)
    print(f"🚀 [Agnes Studio Server] 统一智能服务已就绪！")
    print(f"🌐 服务端口: http://localhost:{port}/#poster-studio")
    print(f"⚙️  模型网关: http://localhost:{port}/api/config")
    httpd.serve_forever()

if __name__ == "__main__":
    ensure_venv()
    p = 8088
    if len(sys.argv) > 1:
        try:
            p = int(sys.argv[1])
        except ValueError:
            pass
    run(p)
