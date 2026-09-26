import json
import os
import sys
import threading
import unittest
import urllib.request
from http.server import HTTPServer
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import gemini_engine
import studio_server


class TestEndpointContract(unittest.TestCase):
    def test_image_and_chat_defaults_are_separate(self):
        cfg = studio_server.get_local_newapi_config()
        self.assertEqual(cfg["image_base_url"], "http://192.168.1.164:3000/v1")
        self.assertEqual(cfg["chat_base_url"], "http://127.0.0.1:18045/v1")
        self.assertNotEqual(cfg["image_base_url"], cfg["chat_base_url"])

    def test_chat_default_is_dsh_tunnel(self):
        self.assertEqual(gemini_engine.DEFAULT_BASE, "http://127.0.0.1:18045/v1")

    def test_chat_model_allowlist_excludes_local_image_models(self):
        self.assertIn("gemini-3.8-flash-medium", gemini_engine.CHAT_MODEL_ALLOWLIST)
        self.assertNotIn("agnes-image-2.5-flash", gemini_engine.CHAT_MODEL_ALLOWLIST)

    def test_runtime_key_precedence_is_dsh_first(self):
        self.assertTrue(hasattr(gemini_engine, "load_credentials"))
        source = Path(gemini_engine.__file__).read_text(encoding="utf-8")
        self.assertIn("ANTIGRAVITY_API_KEY", source)

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

    def test_gemini_vision_and_inspect_default_models(self):
        import inspect
        sig_detect = inspect.signature(gemini_engine.detect_visual_subjects_gemini)
        self.assertIn("model", sig_detect.parameters)
        self.assertIsNone(sig_detect.parameters["model"].default)

        sig_inspect = inspect.signature(gemini_engine.vision_inspect_artwork)
        self.assertIn("model", sig_inspect.parameters)
        self.assertIsNone(sig_inspect.parameters["model"].default)

        source = Path(gemini_engine.__file__).read_text(encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
