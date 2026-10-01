import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import HTTPServer
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import agnes_engine
import pro_poster_renderer
import studio_server


class TestEndpointContract(unittest.TestCase):
    def test_image_and_chat_defaults_are_configurable(self):
        # 默认都走本机 New API (13000)，可通过环境变量分别覆盖
        # AGNES_IMAGE_BASE_URL / AGNES_CHAT_BASE_URL
        self.assertEqual(studio_server.IMAGE_BASE_DEFAULT, "http://127.0.0.1:13000/v1")
        self.assertEqual(studio_server.CHAT_BASE_DEFAULT, "http://127.0.0.1:13000/v1")

        # 确保无本地配置文件回退时，get_local_newapi_config 提供的默认值正确
        cfg = studio_server.get_local_newapi_config(key_path="/non_existent/path/local_key.json")
        self.assertFalse(cfg["detected"])
        self.assertEqual(cfg["image_base_url"], "http://127.0.0.1:13000/v1")
        self.assertEqual(cfg["chat_base_url"], "http://127.0.0.1:13000/v1")

    def test_get_local_newapi_config_custom_key_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_file = Path(tmpdir) / "custom_key.json"
            cfg_file.write_text(json.dumps({
                "base_url": "http://10.0.0.1:3000/v1",
                "image_base_url": "http://10.0.0.2:3000/v1",
                "chat_base_url": "http://10.0.0.3:18045/v1",
                "api_key": "sk-test-12345",
            }), encoding="utf-8")
            cfg = studio_server.get_local_newapi_config(key_path=cfg_file)
            self.assertTrue(cfg["detected"])
            self.assertEqual(cfg["base_url"], "http://10.0.0.1:3000/v1")
            self.assertEqual(cfg["image_base_url"], "http://10.0.0.2:3000/v1")
            self.assertEqual(cfg["chat_base_url"], "http://10.0.0.3:18045/v1")
            self.assertEqual(cfg["api_key"], "sk-test-12345")

    def test_chat_default_is_newapi(self):
        self.assertEqual(agnes_engine.DEFAULT_BASE, "http://127.0.0.1:13000/v1")

    def test_chat_model_allowlist_excludes_local_image_models(self):
        self.assertIn("agnes-3.0-flash", agnes_engine.CHAT_MODEL_ALLOWLIST)
        self.assertNotIn("agnes-image-2.5-flash", agnes_engine.CHAT_MODEL_ALLOWLIST)

    def test_runtime_key_precedence_is_agnes_first(self):
        self.assertTrue(hasattr(agnes_engine, "load_credentials"))
        source = Path(agnes_engine.__file__).read_text(encoding="utf-8")
        self.assertIn("AGNES_API_KEY", source)

    def test_studio_server_safe_import(self):
        self.assertTrue(callable(getattr(studio_server, "ensure_venv", None)))
        self.assertTrue(callable(getattr(studio_server, "get_local_newapi_config", None)))

    def test_generate_custom_poster_html_all_styles(self):
        styles = {
            "cyber_01": "TACTICAL HUD",
            "chinese_01": "vertical-rl",
            "cinema_01": "2.35:1 WIDESCREEN",
            "swiss_01": "SWISS INTERNATIONAL STYLE",
        }
        for style_name, marker in styles.items():
            with self.subTest(style=style_name):
                html = studio_server.generate_custom_poster_html(
                    style_name,
                    "测试标题",
                    "SUBTITLE",
                    "文案内容",
                    "AGNES TEST",
                    "data:image/png;base64,abc",
                )
                self.assertIn(marker, html)
                self.assertIn("测试标题", html)
                self.assertIn("SUBTITLE", html)
                self.assertIn("文案内容", html)
                self.assertIn("AGNES TEST", html)

    def test_generate_custom_poster_html_case_and_none_robustness(self):
        # None inputs shouldn't raise TypeError
        html_none = studio_server.generate_custom_poster_html(None, None, None, None, None, None)
        self.assertIn("<!DOCTYPE html>", html_none)
        self.assertIn("SWISS INTERNATIONAL STYLE", html_none)

        # Case-insensitivity support
        html_cyber_upper = studio_server.generate_custom_poster_html("CYBER_02", "赛博", "SUB", "BODY", "AUT", "")
        self.assertIn("TACTICAL HUD", html_cyber_upper)
        html_cinema_upper = studio_server.generate_custom_poster_html("CINEMA_PRO", "大片", "SUB", "BODY", "AUT", "")
        self.assertIn("2.35:1 WIDESCREEN", html_cinema_upper)

    def test_generate_custom_poster_html_xss_escaping(self):
        html_xss = studio_server.generate_custom_poster_html(
            "swiss_01",
            "<script>alert('xss')</script>",
            'Sub "Title"',
            "Line1 & Line2",
            "Author <Admin>",
            "",
        )
        self.assertNotIn("<script>", html_xss)
        self.assertIn("&lt;script&gt;", html_xss)
        self.assertIn("&quot;Title&quot;", html_xss)
        self.assertIn("Line1 &amp; Line2", html_xss)
        self.assertIn("Author &lt;Admin&gt;", html_xss)

        html_bg_xss = studio_server.generate_custom_poster_html(
            "swiss_01",
            "Title",
            "Sub",
            "Body",
            "Author",
            "https://example.com/a.png');}</style><script>alert('bg_xss')</script>",
        )
        self.assertNotIn("<script>", html_bg_xss)
        self.assertIn("%3Cscript%3E", html_bg_xss)

    def test_api_config_endpoint_with_query_params(self):
        server = HTTPServer(("127.0.0.1", 0), studio_server.StudioHTTPRequestHandler)
        port = server.server_port
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            # Query param cache-busting should not produce 404
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/config?t=123456", timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(data.get("success"))
                self.assertIn("image_base_url", data)
                self.assertIn("chat_base_url", data)

            # Trailing slash should also route correctly
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/config/", timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(data.get("success"))
        finally:
            server.shutdown()
            server.server_close()

    def test_post_unknown_endpoint_returns_404_json(self):
        server = HTTPServer(("127.0.0.1", 0), studio_server.StudioHTTPRequestHandler)
        port = server.server_port
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/non_existent_route",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=5)
            self.assertEqual(ctx.exception.code, 404)
            with ctx.exception:
                resp_data = json.loads(ctx.exception.read().decode("utf-8"))
            self.assertFalse(resp_data.get("success"))
            self.assertIn("Endpoint not found", resp_data.get("error", ""))
        finally:
            server.shutdown()
            server.server_close()

    def test_post_non_dict_payload_handled_gracefully(self):
        server = HTTPServer(("127.0.0.1", 0), studio_server.StudioHTTPRequestHandler)
        port = server.server_port
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            # Send non-dict JSON body to /api/test-connection
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/test-connection",
                data=b"123",
                headers={"Content-Type": "application/json", "Content-Length": "3"},
                method="POST",
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=5)
            self.assertEqual(ctx.exception.code, 400)
            with ctx.exception:
                resp_data = json.loads(ctx.exception.read().decode("utf-8"))
            self.assertFalse(resp_data.get("success"))
            self.assertIn("请提供有效的 Base URL", resp_data.get("error", ""))
        finally:
            server.shutdown()
            server.server_close()

    def test_get_unknown_api_endpoint_returns_404_json(self):
        server = HTTPServer(("127.0.0.1", 0), studio_server.StudioHTTPRequestHandler)
        port = server.server_port
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/non_existent_endpoint",
                method="GET",
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=5)
            self.assertEqual(ctx.exception.code, 404)
            with ctx.exception:
                resp_data = json.loads(ctx.exception.read().decode("utf-8"))
            self.assertFalse(resp_data.get("success"))
            self.assertIn("Endpoint not found", resp_data.get("error", ""))
        finally:
            server.shutdown()
            server.server_close()

    def test_agnes_vision_and_inspect_default_models(self):
        import inspect
        sig_detect = inspect.signature(agnes_engine.detect_visual_subjects)
        self.assertIn("model", sig_detect.parameters)
        self.assertIsNone(sig_detect.parameters["model"].default)

        sig_inspect = inspect.signature(agnes_engine.vision_inspect_artwork)
        self.assertIn("model", sig_inspect.parameters)
        self.assertIsNone(sig_inspect.parameters["model"].default)

        source = Path(agnes_engine.__file__).read_text(encoding="utf-8")
        self.assertNotIn('model="agnes-2.5-flash"', source)

    def test_post_endpoints_validation_contract(self):
        server = HTTPServer(("127.0.0.1", 0), studio_server.StudioHTTPRequestHandler)
        port = server.server_port
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            endpoints = [
                ("/api/generate-image", {}, 400, "提示词不能为空"),
                ("/api/gemini/generate-brief", {}, 400, "请输入创意主题"),
                ("/api/gemini/refine-prompt", {}, 400, "请输入原始提示词"),
                ("/api/gemini/vision-inspect", {}, 400, "请提供待质检图片路径"),
                ("/api/gemini/vision-inspect", {"image_path": "non_existent_file.png"}, 404, "找不到图片文件"),
            ]
            for path, payload, expected_code, expected_err in endpoints:
                with self.subTest(path=path, payload=payload):
                    data = json.dumps(payload).encode("utf-8")
                    req = urllib.request.Request(
                        f"http://127.0.0.1:{port}{path}",
                        data=data,
                        headers={"Content-Type": "application/json", "Content-Length": str(len(data))},
                        method="POST",
                    )
                    with self.assertRaises(urllib.error.HTTPError) as ctx:
                        urllib.request.urlopen(req, timeout=5)
                    self.assertEqual(ctx.exception.code, expected_code)
                    with ctx.exception:
                        resp_data = json.loads(ctx.exception.read().decode("utf-8"))
                    self.assertFalse(resp_data.get("success"))
                    self.assertIn(expected_err, resp_data.get("error", ""))
        finally:
            server.shutdown()
            server.server_close()


    def test_post_render_poster_endpoint_contract(self):
        server = HTTPServer(("127.0.0.1", 0), studio_server.StudioHTTPRequestHandler)
        port = server.server_port
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            rendered_payloads = []

            def fake_renderer(html_content, out_path):
                rendered_payloads.append((html_content, out_path))
                return out_path

            orig_renderer = studio_server.render_html_to_poster
            studio_server.render_html_to_poster = fake_renderer
            try:
                # 1. 成功渲染，支持 data URI
                data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                req_data = json.dumps({
                    "style": "cyber_01",
                    "title": "赛博之夜",
                    "subtitle": "CYBER NIGHT",
                    "bg_image": data_uri,
                }).encode("utf-8")
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/render-poster",
                    data=req_data,
                    headers={"Content-Type": "application/json", "Content-Length": str(len(req_data))},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                    res_json = json.loads(resp.read().decode("utf-8"))
                    self.assertTrue(res_json.get("success"))
                    self.assertTrue(res_json.get("poster_url", "").startswith("assets/poster_custom_"))
                    self.assertEqual(res_json.get("style"), "cyber_01")
                    self.assertIn("duration_ms", res_json)

                self.assertEqual(len(rendered_payloads), 1)
                html_passed, out_passed = rendered_payloads[0]
                self.assertIn(data_uri, html_passed)
                self.assertIn("赛博之夜", html_passed)

                # 2. 渲染器异常时返回 500
                def failing_renderer(html_content, out_path):
                    raise RuntimeError("Chromium launch timeout")

                studio_server.render_html_to_poster = failing_renderer
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(req, timeout=5)
                self.assertEqual(ctx.exception.code, 500)
                with ctx.exception:
                    err_resp = json.loads(ctx.exception.read().decode("utf-8"))
                self.assertFalse(err_resp.get("success"))
                self.assertIn("Chromium launch timeout", err_resp.get("error", ""))

                # 3. 渲染器不可用时返回 500
                studio_server.render_html_to_poster = None
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(req, timeout=5)
                self.assertEqual(ctx.exception.code, 500)
                with ctx.exception:
                    err_resp2 = json.loads(ctx.exception.read().decode("utf-8"))
                self.assertFalse(err_resp2.get("success"))
                self.assertIn("排版引擎不可用", err_resp2.get("error", ""))
            finally:
                studio_server.render_html_to_poster = orig_renderer
        finally:
            server.shutdown()
            server.server_close()

    def test_options_request_and_cors_headers(self):
        server = HTTPServer(("127.0.0.1", 0), studio_server.StudioHTTPRequestHandler)
        port = server.server_port
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            for path in ("/api/config", "/api/render-poster", "/api/generate-image"):
                with self.subTest(path=path):
                    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method="OPTIONS")
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        self.assertEqual(resp.status, 204)
                        self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")
                        self.assertIn("POST", resp.headers.get("Access-Control-Allow-Methods", ""))
                        self.assertIn("OPTIONS", resp.headers.get("Access-Control-Allow-Methods", ""))
        finally:
            server.shutdown()
            server.server_close()

    def test_url_scheme_validation(self):
        server = HTTPServer(("127.0.0.1", 0), studio_server.StudioHTTPRequestHandler)
        port = server.server_port
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            # 1. test-connection with non-http/https URL
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/test-connection",
                data=json.dumps({"base_url": "file:///etc"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=5)
            self.assertEqual(ctx.exception.code, 400)
            with ctx.exception:
                resp = json.loads(ctx.exception.read().decode("utf-8"))
            self.assertFalse(resp.get("success"))
            self.assertIn("Base URL 必须以 http:// 或 https:// 开头", resp.get("error", ""))

            # 2. generate-image with non-http/https URL
            req_img = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/generate-image",
                data=json.dumps({"prompt": "A test poster", "base_url": "ftp://example.com"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req_img, timeout=5)
            self.assertEqual(ctx.exception.code, 400)
            with ctx.exception:
                resp_img = json.loads(ctx.exception.read().decode("utf-8"))
            self.assertFalse(resp_img.get("success"))
            self.assertIn("Base URL 必须以 http:// 或 https:// 开头", resp_img.get("error", ""))

            # 3. gemini endpoints with non-http/https URL
            gemini_endpoints = [
                ("/api/gemini/generate-brief", {"topic": "艺术设计", "chat_base_url": "ftp://example.com"}),
                ("/api/gemini/refine-prompt", {"prompt": "A sunset view", "base_url": "file:///etc"}),
                ("/api/gemini/vision-inspect", {"image_path": "assets/sample.png", "chat_base_url": "bad://url"}),
            ]
            for ep_path, ep_payload in gemini_endpoints:
                with self.subTest(endpoint=ep_path):
                    req_ep = urllib.request.Request(
                        f"http://127.0.0.1:{port}{ep_path}",
                        data=json.dumps(ep_payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with self.assertRaises(urllib.error.HTTPError) as ctx:
                        urllib.request.urlopen(req_ep, timeout=5)
                    self.assertEqual(ctx.exception.code, 400)
                    with ctx.exception:
                        resp_ep = json.loads(ctx.exception.read().decode("utf-8"))
                    self.assertFalse(resp_ep.get("success"))
                    self.assertIn("Base URL 必须以 http:// 或 https:// 开头", resp_ep.get("error", ""))
        finally:
            server.shutdown()
            server.server_close()

    def test_vision_inspect_file_validation(self):
        server = HTTPServer(("127.0.0.1", 0), studio_server.StudioHTTPRequestHandler)
        port = server.server_port
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            # 1. 非图片文件扩展名应返回 400
            for invalid_file in ("package.json", "scripts/studio_server.py", "readme.txt"):
                with self.subTest(file=invalid_file):
                    req = urllib.request.Request(
                        f"http://127.0.0.1:{port}/api/gemini/vision-inspect",
                        data=json.dumps({"image_path": invalid_file}).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with self.assertRaises(urllib.error.HTTPError) as ctx:
                        urllib.request.urlopen(req, timeout=5)
                    self.assertEqual(ctx.exception.code, 400)
                    with ctx.exception:
                        resp = json.loads(ctx.exception.read().decode("utf-8"))
                    self.assertFalse(resp.get("success"))
                    self.assertIn("只支持 PNG、JPG、JPEG、WEBP 格式的图片文件", resp.get("error", ""))

            # 2. 路径穿越或在允许目录之外的文件应返回 404
            for invalid_path in ("../../etc/passwd.png", "../outside.png"):
                with self.subTest(path=invalid_path):
                    req = urllib.request.Request(
                        f"http://127.0.0.1:{port}/api/gemini/vision-inspect",
                        data=json.dumps({"image_path": invalid_path}).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with self.assertRaises(urllib.error.HTTPError) as ctx:
                        urllib.request.urlopen(req, timeout=5)
                    self.assertEqual(ctx.exception.code, 404)
                    with ctx.exception:
                        resp = json.loads(ctx.exception.read().decode("utf-8"))
                    self.assertFalse(resp.get("success"))
                    self.assertIn("找不到图片文件", resp.get("error", ""))
        finally:
            server.shutdown()
            server.server_close()

    def test_post_render_poster_with_public_prefix_path(self):
        server = HTTPServer(("127.0.0.1", 0), studio_server.StudioHTTPRequestHandler)
        port = server.server_port
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            captured_html = []

            def fake_renderer(html_content, out_path):
                captured_html.append(html_content)
                return out_path

            orig_renderer = studio_server.render_html_to_poster
            studio_server.render_html_to_poster = fake_renderer
            try:
                # 传入带 public/ 前缀的路径
                req_data = json.dumps({
                    "style": "swiss_01",
                    "title": "前缀路径测试",
                    "subtitle": "PUBLIC PREFIX TEST",
                    "bg_image": "public/assets/poster_workshop_hero_1080.png",
                }).encode("utf-8")
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/render-poster",
                    data=req_data,
                    headers={"Content-Type": "application/json", "Content-Length": str(len(req_data))},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                    res_json = json.loads(resp.read().decode("utf-8"))
                    self.assertTrue(res_json.get("success"))

                self.assertEqual(len(captured_html), 1)
                # 确认背景图片已被读取为 base64 data URI 并注入
                self.assertIn("data:image/png;base64,", captured_html[0])
                self.assertIn("前缀路径测试", captured_html[0])
            finally:
                studio_server.render_html_to_poster = orig_renderer
        finally:
            server.shutdown()
            server.server_close()

    def test_agnes_engine_contract_and_image_handling(self):
        # 1. 验证 markdown 代码块去除（含大小写兼容与去空白）
        self.assertEqual(agnes_engine._strip_markdown_codeblock('```json\n{"a": 1}\n```'), '{"a": 1}')
        self.assertEqual(agnes_engine._strip_markdown_codeblock('```JSON\n{"b": 2}\n```'), '{"b": 2}')
        self.assertEqual(agnes_engine._strip_markdown_codeblock('```\n{"c": 3}\n```'), '{"c": 3}')
        self.assertEqual(agnes_engine._strip_markdown_codeblock('{"d": 4}'), '{"d": 4}')

        # 2. 验证 call_gemini 对非 http/https scheme 的快速拦截
        bad_schemes = ["ftp://example.com/v1", "file:///etc/passwd", "gopher://bad"]
        for bad_url in bad_schemes:
            with self.subTest(bad_url=bad_url):
                res = agnes_engine.call_gemini([], base_url=bad_url)
                self.assertFalse(res["ok"])
                self.assertIn("Base URL 必须以 http:// 或 https:// 开头", res.get("error", ""))

        # 3. 验证缺失文件时多模态函数的安全优雅退出
        missing_file = "non_existent_img_xyz.png"
        self.assertEqual(agnes_engine.detect_visual_subjects(missing_file), [])
        inspect_res = agnes_engine.vision_inspect_artwork(missing_file)
        self.assertFalse(inspect_res["ok"])
        self.assertIn("文件不存在", inspect_res.get("error", ""))

        # 4. 验证 WebP / PNG / JPEG base64 MIME 正确性
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            webp_f = tmp_path / "sample.webp"
            png_f = tmp_path / "sample.png"
            jpg_f = tmp_path / "sample.jpg"

            webp_f.write_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8 ")
            png_f.write_bytes(b"\x89PNG\r\n\x1a\n")
            jpg_f.write_bytes(b"\xff\xd8\xff\xe0")

            # studio_server.get_base64_image
            self.assertTrue(studio_server.get_base64_image(webp_f).startswith("data:image/webp;base64,"))
            self.assertTrue(studio_server.get_base64_image(png_f).startswith("data:image/png;base64,"))
            self.assertTrue(studio_server.get_base64_image(jpg_f).startswith("data:image/jpeg;base64,"))
            self.assertEqual(studio_server.get_base64_image(tmp_path / "not_found.png"), "")

            # pro_poster_renderer.get_base64_image
            self.assertTrue(pro_poster_renderer.get_base64_image(webp_f).startswith("data:image/webp;base64,"))
            self.assertTrue(pro_poster_renderer.get_base64_image(png_f).startswith("data:image/png;base64,"))
            self.assertTrue(pro_poster_renderer.get_base64_image(jpg_f).startswith("data:image/jpeg;base64,"))
            self.assertEqual(pro_poster_renderer.get_base64_image(tmp_path / "not_found.png"), "")

    def test_post_render_poster_bg_path_resolution(self):
        server = HTTPServer(("127.0.0.1", 0), studio_server.StudioHTTPRequestHandler)
        port = server.server_port
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            rendered_payloads = []

            def fake_renderer(html_content, out_path):
                rendered_payloads.append((html_content, out_path))
                return out_path

            orig_renderer = studio_server.render_html_to_poster
            studio_server.render_html_to_poster = fake_renderer
            try:
                expected_swiss = studio_server.get_base64_image(str(studio_server.PUBLIC_DIR / "assets" / "poster_pro_swiss_01.png"))
                default_bg = studio_server.get_base64_image(str(studio_server.ASSETS_DIR / "agnes_1789995698_9987.png"))
                self.assertTrue(len(expected_swiss) > 0)
                self.assertTrue(len(default_bg) > 0)
                self.assertNotEqual(expected_swiss, default_bg)

                # 1. 验证带 query 字符串（如前端防缓存 ?t=...）能够正确解析并使用目标图片
                req_data = json.dumps({
                    "style": "swiss_01",
                    "title": "测试瑞士",
                    "bg_image": "assets/poster_pro_swiss_01.png?t=1672345678#preview",
                }).encode("utf-8")
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/render-poster",
                    data=req_data,
                    headers={"Content-Type": "application/json", "Content-Length": str(len(req_data))},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                self.assertIn(expected_swiss, rendered_payloads[-1][0])

                # 2. 验证带 public/ 前缀能够正确解析
                req_data2 = json.dumps({
                    "style": "swiss_01",
                    "title": "测试前缀",
                    "bg_image": "public/assets/poster_pro_swiss_01.png",
                }).encode("utf-8")
                req2 = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/render-poster",
                    data=req_data2,
                    headers={"Content-Type": "application/json", "Content-Length": str(len(req_data2))},
                    method="POST",
                )
                with urllib.request.urlopen(req2, timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                self.assertIn(expected_swiss, rendered_payloads[-1][0])

                # 3. 验证目录穿越被安全拦截并回退至默认底图
                req_data3 = json.dumps({
                    "style": "swiss_01",
                    "title": "测试穿越",
                    "bg_image": "../../../etc/shadow",
                }).encode("utf-8")
                req3 = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/render-poster",
                    data=req_data3,
                    headers={"Content-Type": "application/json", "Content-Length": str(len(req_data3))},
                    method="POST",
                )
                with urllib.request.urlopen(req3, timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                self.assertIn(default_bg, rendered_payloads[-1][0])
            finally:
                studio_server.render_html_to_poster = orig_renderer
        finally:
            server.shutdown()
            server.server_close()

    def test_gateway_readiness_ui_contract(self):
        """确保前端 index.html 的网关状态逻辑符合真实探活规范，不展示伪假绿色就绪状态"""
        html_path = studio_server.PUBLIC_DIR / "index.html"
        self.assertTrue(html_path.exists())
        html_content = html_path.read_text(encoding="utf-8")

        # 1. 确保必要的 DOM 节点 ID 存在
        self.assertIn('id="btn-model-gateway"', html_content)
        self.assertIn('id="header-gateway-dot"', html_content)
        self.assertIn('id="header-gateway-status"', html_content)
        self.assertIn('id="header-gateway-badge"', html_content)

        # 2. 初始静态 HTML 不得硬编码未探测的虚假就绪文本
        self.assertNotIn("网关就绪 (6 Keys · 32ms)", html_content)
        self.assertIn("配置待探测", html_content)

        # 3. updateHeaderStatus 函数必须能根据 isReady 动态切换 emerald / amber 样式与指示点
        self.assertIn("function updateHeaderStatus(isReady, labelText)", html_content)
        self.assertIn("bg-emerald-50", html_content)
        self.assertIn("bg-amber-50", html_content)
        self.assertIn("header-gateway-dot", html_content)
        self.assertIn("header-gateway-badge", html_content)

        # 4. testConnection 探活成功时必须激活就绪状态，探活失败或异常时必须置为未就绪
        self.assertIn('updateHeaderStatus(true, "网关就绪 · "', html_content)
        self.assertIn('updateHeaderStatus(false, "网关未就绪 · 握手失败")', html_content)
        self.assertIn('updateHeaderStatus(false, "网关离线 · 请求异常")', html_content)


class TestConnectionKeyInjectionTightening(unittest.TestCase):
    """第 12 轮：/api/test-connection 服务端密钥注入收紧。

    用本地监听器捕获 Authorization 头，验证：
    - base_url 精确等于配置网关 → 注入服务端密钥（合法便利流不断）；
    - base_url 为其他 127.0.0.1 端口/路径 → 不注入；
    - base_url 含 192.168. 前缀 → 不注入（旧逻辑会泄漏）。
    """

    def _run_case(self, base_url):
        from http.server import BaseHTTPRequestHandler
        from unittest.mock import patch

        captured = {}

        class Listener(BaseHTTPRequestHandler):
            def do_GET(self):
                captured["auth"] = self.headers.get("Authorization")
                body = b'{"data": []}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        # 监听 0.0.0.0：既服务 127.0.0.1，也服务本机局域网 IP
        #（模拟攻击者在局域网/回环起的收割监听器）
        listener = HTTPServer(("0.0.0.0", 0), Listener)
        lport = listener.server_address[1]
        lt = threading.Thread(target=listener.serve_forever, daemon=True)
        lt.start()

        fake_cfg = {
            "detected": True,
            "base_url": "http://127.0.0.1:%d/v1" % lport,
            "api_key": "sk-secret-configured-key",
        }
        # base_url 中的占位端口替换为真实监听端口
        target = base_url.replace("LISTEN_PORT", str(lport))

        server = HTTPServer(("127.0.0.1", 0), studio_server.StudioHTTPRequestHandler)
        sport = server.server_port
        st = threading.Thread(target=server.serve_forever, daemon=True)
        st.start()
        try:
            with patch.object(studio_server, "get_local_newapi_config",
                              return_value=fake_cfg):
                req = urllib.request.Request(
                    "http://127.0.0.1:%d/api/test-connection" % sport,
                    data=json.dumps({"base_url": target}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    body = json.loads(r.read().decode("utf-8"))
                self.assertTrue(body["success"])
        finally:
            server.shutdown()
            server.server_close()
            listener.shutdown()
            listener.server_close()
        return captured.get("auth")

    def test_key_injected_only_for_exact_configured_base(self):
        auth = self._run_case("http://127.0.0.1:LISTEN_PORT/v1")
        self.assertEqual(auth, "Bearer sk-secret-configured-key")

    def test_no_key_for_other_localhost_port(self):
        auth = self._run_case("http://127.0.0.1:LISTEN_PORT/evil")
        self.assertIsNone(auth)

    def test_no_key_for_lan_prefix(self):
        # 本机真实局域网 IP（omarchy: 192.168.1.133），动态探测兜底
        import socket
        lan_ip = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("192.168.1.1", 80))
            lan_ip = s.getsockname()[0]
            s.close()
        except Exception:
            lan_ip = None
        if not lan_ip or not lan_ip.startswith("192.168."):
            self.skipTest("无 192.168.x 局域网地址，跳过")
        # 注意：本机 http_proxy 指向 192.168.1.164:7897，且 no_proxy 用了
        # CIDR 写法（192.168.1.0/24）——Python urllib 的 proxy_bypass 不认
        # CIDR，字面 IP 会被送进代理导致超时。这里把字面 IP 追加进 no_proxy，
        # studio_server 与测试同进程，urlopen 会实时读取环境变量。
        from unittest.mock import patch as _patch
        import os as _os
        extra = ",".join(filter(None, [_os.environ.get("no_proxy"), lan_ip]))
        with _patch.dict(_os.environ, {"no_proxy": extra, "NO_PROXY": extra}):
            auth = self._run_case("http://%s:LISTEN_PORT/x" % lan_ip)
        self.assertIsNone(auth)


if __name__ == "__main__":
    unittest.main()
