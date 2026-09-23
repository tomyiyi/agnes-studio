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
import urllib.request
import urllib.error
import urllib.parse
from html import escape
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = DIR / "public"
ASSETS_DIR = PUBLIC_DIR / "assets"
GENERATED_DIR = ASSETS_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

# 尝试引入海报排版引擎
sys.path.insert(0, str(DIR / "scripts"))
try:
    from pro_poster_renderer import render_html_to_poster, get_base64_image, FONTS_DIR
except Exception as e:
    print(f"⚠️ [Warning] 排版引擎导入提示: {e}")

LOCAL_KEY_PATH = Path.home() / ".new-api" / "local_key.json"

def get_local_newapi_config():
    """读取本地 New API 配置文件（如果存在）"""
    if LOCAL_KEY_PATH.exists():
        try:
            with open(LOCAL_KEY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "detected": True,
                "type": "local_new_api",
                "base_url": data.get("base_url", "http://127.0.0.1:3000/v1"),
                "api_key": data.get("api_key", ""),
                "default_model": "agnes-image-2.5-flash",
                "models": data.get("models", {}).get("image_generation", [
                    "agnes-image-2.5-flash",
                    "agnes-image-2.1-flash",
                    "dall-e-3"
                ])
            }
        except Exception as e:
            print(f"读取本地 New API 配置失败: {e}")
    return {
        "detected": False,
        "type": "none",
        "base_url": "https://apihub.agnes-ai.com/v1",
        "api_key": "",
        "default_model": "agnes-image-2.5-flash",
        "models": [
            "agnes-image-2.5-flash",
            "agnes-image-2.1-flash",
            "dall-e-3"
        ]
    }

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
        if self.path == "/api/config":
            cfg = get_local_newapi_config()
            # 为前端提供脱敏显示的 key 和全量配置
            masked_key = ""
            if cfg["api_key"]:
                key = cfg["api_key"]
                masked_key = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
            
            resp = {
                "success": True,
                "detected": cfg["detected"],
                "local_key_detected": cfg["detected"],
                "base_url": cfg["base_url"],
                "masked_api_key": masked_key,
                "has_api_key": bool(cfg["api_key"]),
                # 不向前端回传明文密钥；调用时由服务端按需注入本地密钥
                "api_key": "",
                "default_model": cfg["default_model"],
                "available_models": cfg["models"],
                "preset_endpoints": [
                    {"name": "本地 New API 负载均衡 (推荐)", "url": "http://127.0.0.1:3000/v1"},
                    {"name": "Agnes AI 官方端点", "url": "https://apihub.agnes-ai.com/v1"},
                    {"name": "自定义 / OneAPI 聚合网关", "url": ""}
                ]
            }
            self._send_json(resp)
            return

        super().do_GET()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            req_body = json.loads(post_data.decode("utf-8"))
        except Exception:
            req_body = {}

        # 1. 连通性测试 API
        if self.path == "/api/test-connection":
            base_url = req_body.get("base_url", "").strip().rstrip("/")
            api_key = req_body.get("api_key", "").strip()
            if not api_key:
                local_cfg = get_local_newapi_config()
                if local_cfg["detected"] and base_url.startswith("http://127.0.0.1"):
                    api_key = local_cfg["api_key"]

            if not base_url:
                self._send_json({"success": False, "error": "请提供有效的 Base URL"}, status=400)
                return

            models_url = f"{base_url}/models"
            req = urllib.request.Request(models_url, method="GET")
            req.add_header("User-Agent", "AgnesStudio/1.0")
            if api_key:
                req.add_header("Authorization", f"Bearer {api_key}")

            start_t = time.time()
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    raw = response.read().decode("utf-8")
                    latency_ms = int((time.time() - start_t) * 1000)
                    res_json = json.loads(raw)
                    model_list = []
                    if "data" in res_json and isinstance(res_json["data"], list):
                        model_list = [m.get("id") for m in res_json["data"] if isinstance(m, dict) and "id" in m]
                    
                    # 过滤生图相关模型
                    image_models = [m for m in model_list if "image" in m.lower() or "dall-e" in m.lower()]
                    self._send_json({
                        "success": True,
                        "latency_ms": latency_ms,
                        "model_count": len(model_list),
                        "image_models": image_models or ["agnes-image-2.5-flash", "dall-e-3"],
                        "all_models": model_list[:15]
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
                self._send_json({"success": False, "error": err_msg, "code": e.code}, status=200)
                return
            except Exception as e:
                self._send_json({"success": False, "error": f"连接失败: {str(e)}"}, status=200)
                return

        # 2. 调用 Agnes 生成留白底图
        if self.path == "/api/generate-image":
            base_url = req_body.get("base_url", "http://127.0.0.1:3000/v1").strip().rstrip("/")
            api_key = req_body.get("api_key", "").strip()
            model = req_body.get("model", "agnes-image-2.5-flash").strip()
            prompt = req_body.get("prompt", "").strip()
            size = req_body.get("size", "1024x1024")

            # 如果未提供 key，尝试从本地读取
            if not api_key:
                local_cfg = get_local_newapi_config()
                if local_cfg["detected"]:
                    api_key = local_cfg["api_key"]

            if not prompt:
                self._send_json({"success": False, "error": "提示词不能为空"}, status=400)
                return

            gen_url = f"{base_url}/images/generations"
            payload = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "n": 1
            }
            body_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(gen_url, data=body_bytes, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("User-Agent", "AgnesStudio/1.0")
            if api_key:
                req.add_header("Authorization", f"Bearer {api_key}")

            start_t = time.time()
            try:
                with urllib.request.urlopen(req, timeout=90) as response:
                    res_raw = response.read().decode("utf-8")
                    cost_s = round(time.time() - start_t, 2)
                    res_data = json.loads(res_raw)
                    
                    remote_url = None
                    b64_data = None
                    if "data" in res_data and len(res_data["data"]) > 0:
                        item = res_data["data"][0]
                        remote_url = item.get("url")
                        b64_data = item.get("b64_json")

                    timestamp = int(time.time())
                    out_filename = f"agnes_{timestamp}.png"
                    out_path = GENERATED_DIR / out_filename

                    # 保存图片到本地 assets/generated
                    if b64_data:
                        import base64
                        with open(out_path, "wb") as img_f:
                            img_f.write(base64.b64decode(b64_data))
                    elif remote_url:
                        urllib.request.urlretrieve(remote_url, str(out_path))
                    else:
                        self._send_json({"success": False, "error": "未能从模型响应中提取图片数据"}, status=500)
                        return

                    self._send_json({
                        "success": True,
                        "cost_seconds": cost_s,
                        "file_path": f"assets/generated/{out_filename}",
                        "full_url": f"/assets/generated/{out_filename}",
                        "model": model,
                        "prompt": prompt
                    })
                    return
            except Exception as e:
                self._send_json({"success": False, "error": f"生图失败: {str(e)}"}, status=500)
                return

        # 3. 动态渲染自定义商业海报 (Render Poster)
        if self.path == "/api/render-poster":
            style = req_body.get("style", "swiss_01")
            title = req_body.get("title", "苏黎世秩序")
            subtitle = req_body.get("subtitle", "STRUCTURE & ESSENCE")
            body = req_body.get("body", "设计不是情绪的宣泄，而是对客观秩序的精确度量。让字符锚定在理性的基准线上。")
            author = req_body.get("author", "TOM // AGNES STUDIO")
            title = escape(title, quote=True)
            subtitle = escape(subtitle, quote=True)
            body = escape(body, quote=True)
            author = escape(author, quote=True)

            # 兼容前端 background_img 与历史 bg_image 两种字段名
            bg_image_rel = req_body.get("bg_image") or req_body.get("background_img") or "assets/poster_pro_swiss_01.png"

            # 定位底图绝对路径（限制在 public/ 内，防止路径穿越）
            bg_abs_path = (PUBLIC_DIR / bg_image_rel.lstrip("/")).resolve()
            if not str(bg_abs_path).startswith(str(PUBLIC_DIR.resolve())) or not bg_abs_path.exists():
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

        super().do_POST()

def generate_custom_poster_html(style, title, subtitle, body, author, bg_uri):
    """根据自定义参数生成对应流派的高保真 HTML 排印代码"""
    if "cyber" in style:
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
    
    elif "chinese" in style:
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
    width: 44px; height: 44px; background: #b91c1c; border: 2px solid #ef4444; border-radius: 4px;
    display: flex; align-items: center; justify-content: center; color: #ffffff;
    font-size: 13px; font-weight: bold; writing-mode: vertical-rl; letter-spacing: 2px;
    position: absolute; top: 380px; left: 120px; z-index: 10;
  }}
  .footer-caption {{
    position: absolute; bottom: 50px; left: 100px; font-size: 12px;
    letter-spacing: 4px; color: rgba(255,255,255,0.7); font-family: monospace; z-index: 10;
  }}
</style></head><body>
  <div class="bg-layer"></div>
  <div class="title-left">{title}</div>
  <div class="seal-red">雅集</div>
  <div class="poem-block">{body}</div>
  <div class="footer-caption">{subtitle} // {author}</div>
</body></html>"""

    elif "cinema" in style:
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
    p = 8088
    if len(sys.argv) > 1:
        try:
            p = int(sys.argv[1])
        except ValueError:
            pass
    run(p)
