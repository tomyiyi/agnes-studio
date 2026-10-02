#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第4轮测试：/api/agnes/* 别名路由端到端实测。

真实启动 HTTPServer(127.0.0.1, 随机端口)，mock studio_server 模块级的三个
引擎函数（不发起真实 New API 调用），用 urllib 真实走 HTTP 验证：
  - /api/agnes/* 与 /api/gemini/* 别名行为一致（同一处理器）
  - 成功响应回显 trace_id；请求体 trace_id 透传到引擎层 kwargs
  - 400/404/500 错误路径；未知路径 404
"""

import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import studio_server

PNG_REL = "assets/agnes_1789997358_1867.png"


def _post(port, path, body):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:%d%s" % (port, path), data=data, method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        with e:
            raw = e.read().decode("utf-8") or "{}"
            return e.code, json.loads(raw)


class TestAgnesAliasE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = HTTPServer(("127.0.0.1", 0),
                               studio_server.StudioHTTPRequestHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(
            target=cls.httpd.serve_forever,
            kwargs={"poll_interval": 0.05}, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.thread.join()
        cls.httpd.server_close()

    def post(self, path, body):
        return _post(self.port, path, body)

    # ---- generate-brief ----

    def test_agnes_generate_brief_ok_echoes_trace(self):
        mock = MagicMock(return_value={
            "ok": True, "brief": "B", "cost_s": 1.2, "trace_id": "t-9"})
        with patch.object(studio_server, "generate_creative_brief", mock):
            for alias in ("/api/agnes/generate-brief",
                          "/api/gemini/generate-brief"):
                with self.subTest(alias=alias):
                    st, body = self.post(alias, {"topic": "秋冬",
                                                "trace_id": "t-9"})
                    self.assertEqual(st, 200)
                    self.assertTrue(body["success"])
                    self.assertEqual(body["brief"], "B")
                    self.assertEqual(body["trace_id"], "t-9")
        # 引擎层收到透传的 trace_id
        self.assertEqual(mock.call_args.kwargs["trace_id"], "t-9")

    def test_agnes_generate_brief_400_missing_topic(self):
        mock = MagicMock()
        with patch.object(studio_server, "generate_creative_brief", mock):
            st, body = self.post("/api/agnes/generate-brief", {"topic": "  "})
            self.assertEqual(st, 400)
            self.assertFalse(body["success"])
            mock.assert_not_called()

    def test_agnes_generate_brief_engine_failure_500(self):
        mock = MagicMock(return_value={"ok": False, "error": "boom"})
        with patch.object(studio_server, "generate_creative_brief", mock):
            st, body = self.post("/api/agnes/generate-brief", {"topic": "x"})
            self.assertEqual(st, 500)
            self.assertIn("boom", body["error"])

    # ---- refine-prompt ----

    def test_agnes_refine_prompt_alias_parity(self):
        mock = MagicMock(return_value={
            "ok": True, "prompt": "P", "cost_s": 0.5, "trace_id": "t-r"})
        with patch.object(studio_server, "refine_prompt_for_agnes", mock):
            for alias in ("/api/agnes/refine-prompt",
                          "/api/gemini/refine-prompt"):
                with self.subTest(alias=alias):
                    st, body = self.post(alias, {"prompt": "a cat",
                                                "trace_id": "t-r"})
                    self.assertEqual(st, 200)
                    self.assertTrue(body["success"])
                    self.assertEqual(body["prompt"], "P")
                    self.assertEqual(body["trace_id"], "t-r")

    def test_agnes_refine_prompt_400_missing_prompt(self):
        mock = MagicMock()
        with patch.object(studio_server, "refine_prompt_for_agnes", mock):
            st, _ = self.post("/api/agnes/refine-prompt", {})
            self.assertEqual(st, 400)
            mock.assert_not_called()

    # ---- vision-inspect ----

    def test_agnes_vision_inspect_ok(self):
        mock = MagicMock(return_value={
            "ok": True, "inspection": "fine", "cost_s": 2.0,
            "trace_id": "t-v"})
        with patch.object(studio_server, "vision_inspect_artwork", mock):
            st, body = self.post("/api/agnes/vision-inspect",
                                 {"image_path": PNG_REL, "title": "t",
                                  "trace_id": "t-v"})
            self.assertEqual(st, 200)
            self.assertTrue(body["success"])
            self.assertEqual(body["inspection"], "fine")
            self.assertEqual(body["trace_id"], "t-v")
            # 引擎收到的是 public 下的绝对路径
            self.assertTrue(str(mock.call_args.args[0]).endswith(PNG_REL))

    def test_agnes_vision_inspect_400_404(self):
        mock = MagicMock()
        with patch.object(studio_server, "vision_inspect_artwork", mock):
            st, _ = self.post("/api/agnes/vision-inspect", {})
            self.assertEqual(st, 400)  # 缺 image_path
            st, _ = self.post("/api/agnes/vision-inspect",
                              {"image_path": "x.txt"})
            self.assertEqual(st, 400)  # 非法扩展
            st, body = self.post("/api/agnes/vision-inspect",
                                 {"image_path": "assets/nope.png"})
            self.assertEqual(st, 404)  # 文件不存在
            self.assertFalse(body["success"])
            mock.assert_not_called()

    def test_unknown_path_404(self):
        st, body = self.post("/api/agnes/nope", {})
        self.assertEqual(st, 404)
        self.assertFalse(body["success"])




class TestChatRoutesTraceEcho(unittest.TestCase):
    """第 15 轮：三条 chat 路由 + /api/test-connection 的 400/404/500 路径
    必须回显 trace_id（与第 13 轮 image 路由的统一口径一致）。"""

    @classmethod
    def setUpClass(cls):
        cls.httpd = HTTPServer(("127.0.0.1", 0),
                               studio_server.StudioHTTPRequestHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(
            target=cls.httpd.serve_forever,
            kwargs={"poll_interval": 0.05}, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.thread.join()
        cls.httpd.server_close()

    def post(self, path, body):
        return _post(self.port, path, body)

    # ---- generate-brief ----

    def test_brief_400_missing_topic_echoes_trace(self):
        mock = MagicMock()
        with patch.object(studio_server, "generate_creative_brief", mock):
            st, body = self.post("/api/agnes/generate-brief",
                                 {"topic": "  ", "trace_id": "t-br-400"})
            self.assertEqual(st, 400)
            self.assertEqual(body["trace_id"], "t-br-400")
            mock.assert_not_called()
            # 缺省 trace_id 时自动生成
            st, body = self.post("/api/agnes/generate-brief", {"topic": ""})
            self.assertEqual(st, 400)
            self.assertTrue(body["trace_id"].startswith("agnes-"))

    def test_brief_400_bad_base_url_echoes_trace(self):
        mock = MagicMock()
        with patch.object(studio_server, "generate_creative_brief", mock):
            st, body = self.post("/api/agnes/generate-brief",
                                 {"topic": "x", "base_url": "ftp://evil",
                                  "trace_id": "t-br-url"})
            self.assertEqual(st, 400)
            self.assertEqual(body["trace_id"], "t-br-url")
            mock.assert_not_called()

    def test_brief_500_engine_not_ready_echoes_trace(self):
        with patch.object(studio_server, "generate_creative_brief", None):
            st, body = self.post("/api/agnes/generate-brief",
                                 {"topic": "x", "trace_id": "t-br-500"})
            self.assertEqual(st, 500)
            self.assertEqual(body["trace_id"], "t-br-500")

    def test_brief_500_engine_error_echoes_engine_trace(self):
        mock = MagicMock(return_value={"ok": False, "error": "boom",
                                       "trace_id": "t-eng-1"})
        with patch.object(studio_server, "generate_creative_brief", mock):
            st, body = self.post("/api/agnes/generate-brief",
                                 {"topic": "x", "trace_id": "t-eng-1"})
            self.assertEqual(st, 500)
            self.assertEqual(body["trace_id"], "t-eng-1")

    # ---- refine-prompt ----

    def test_refine_400_and_500_echo_trace(self):
        mock = MagicMock()
        with patch.object(studio_server, "refine_prompt_for_agnes", mock):
            st, body = self.post("/api/agnes/refine-prompt",
                                 {"prompt": "", "trace_id": "t-rf-400"})
            self.assertEqual(st, 400)
            self.assertEqual(body["trace_id"], "t-rf-400")
            mock.assert_not_called()
        with patch.object(studio_server, "refine_prompt_for_agnes", None):
            st, body = self.post("/api/agnes/refine-prompt",
                                 {"prompt": "x", "trace_id": "t-rf-500"})
            self.assertEqual(st, 500)
            self.assertEqual(body["trace_id"], "t-rf-500")
        mock_err = MagicMock(return_value={"ok": False, "error": "boom",
                                           "trace_id": "t-eng-2"})
        with patch.object(studio_server, "refine_prompt_for_agnes", mock_err):
            st, body = self.post("/api/agnes/refine-prompt",
                                 {"prompt": "x", "trace_id": "t-eng-2"})
            self.assertEqual(st, 500)
            self.assertEqual(body["trace_id"], "t-eng-2")

    # ---- vision-inspect ----

    def test_vision_400_404_500_echo_trace(self):
        mock = MagicMock()
        with patch.object(studio_server, "vision_inspect_artwork", mock):
            st, body = self.post("/api/agnes/vision-inspect",
                                 {"image_path": "", "trace_id": "t-vi-400"})
            self.assertEqual(st, 400)
            self.assertEqual(body["trace_id"], "t-vi-400")
            st, body = self.post("/api/agnes/vision-inspect",
                                 {"image_path": "x.txt", "trace_id": "t-vi-ext"})
            self.assertEqual(st, 400)
            self.assertEqual(body["trace_id"], "t-vi-ext")
            st, body = self.post("/api/agnes/vision-inspect",
                                 {"image_path": "no-such-file-xyz.png",
                                  "trace_id": "t-vi-404"})
            self.assertEqual(st, 404)
            self.assertEqual(body["trace_id"], "t-vi-404")
            mock.assert_not_called()
        with patch.object(studio_server, "vision_inspect_artwork", None):
            st, body = self.post("/api/agnes/vision-inspect",
                                 {"image_path": PNG_REL,
                                  "trace_id": "t-vi-500"})
            # PNG_REL 真实存在 → 走到引擎未就绪 500
            self.assertEqual(st, 500)
            self.assertEqual(body["trace_id"], "t-vi-500")

    # ---- test-connection ----

    def test_brief_auto_generates_and_propagates_trace(self):
        def side_effect(*args, **kwargs):
            return {"ok": True, "brief": "B", "cost_s": 0.1, "trace_id": kwargs.get("trace_id")}
        mock = MagicMock(side_effect=side_effect)
        with patch.object(studio_server, "generate_creative_brief", mock):
            st, body = self.post("/api/agnes/generate-brief", {"topic": "tea"})
            self.assertEqual(st, 200)
            self.assertTrue(body["success"])
            passed_trace = mock.call_args.kwargs.get("trace_id")
            self.assertTrue(passed_trace and passed_trace.startswith("agnes-"))
            self.assertEqual(body["trace_id"], passed_trace)

    def test_refine_auto_generates_and_propagates_trace(self):
        def side_effect(*args, **kwargs):
            return {"ok": True, "prompt": "P", "cost_s": 0.1, "trace_id": kwargs.get("trace_id")}
        mock = MagicMock(side_effect=side_effect)
        with patch.object(studio_server, "refine_prompt_for_agnes", mock):
            st, body = self.post("/api/agnes/refine-prompt", {"prompt": "tea cup"})
            self.assertEqual(st, 200)
            self.assertTrue(body["success"])
            passed_trace = mock.call_args.kwargs.get("trace_id")
            self.assertTrue(passed_trace and passed_trace.startswith("agnes-"))
            self.assertEqual(body["trace_id"], passed_trace)

    def test_vision_auto_generates_and_propagates_trace(self):
        def side_effect(*args, **kwargs):
            return {"ok": True, "inspection": "fine", "cost_s": 0.1, "trace_id": kwargs.get("trace_id")}
        mock = MagicMock(side_effect=side_effect)
        with patch.object(studio_server, "vision_inspect_artwork", mock):
            st, body = self.post("/api/agnes/vision-inspect", {"image_path": PNG_REL})
            self.assertEqual(st, 200)
            self.assertTrue(body["success"])
            passed_trace = mock.call_args.kwargs.get("trace_id")
            self.assertTrue(passed_trace and passed_trace.startswith("agnes-"))
            self.assertEqual(body["trace_id"], passed_trace)

    def test_chat_routes_fallback_trace_when_engine_omits_trace_id(self):
        with patch.object(studio_server, "generate_creative_brief",
                          MagicMock(return_value={"ok": True, "brief": "B", "cost_s": 0.1})):
            st, body = self.post("/api/agnes/generate-brief", {"topic": "tea", "trace_id": "explicit-trace"})
            self.assertEqual(st, 200)
            self.assertEqual(body["trace_id"], "explicit-trace")

    def test_test_connection_400_echoes_trace(self):
        st, body = self.post("/api/test-connection",
                             {"base_url": "", "trace_id": "t-tc-400"})
        self.assertEqual(st, 400)
        self.assertEqual(body["trace_id"], "t-tc-400")
        st, body = self.post("/api/test-connection",
                             {"base_url": "ftp://x", "trace_id": "t-tc-url"})
        self.assertEqual(st, 400)
        self.assertEqual(body["trace_id"], "t-tc-url")




class TestVisionPathTraversal(unittest.TestCase):
    """第 16 轮：`str.startswith` 前缀碰撞穿越回归测试。

    `public_backup/probe.png` 真实存在，但位于允许目录（public/、
    experiments/、outputs/）之外；旧代码用字符串前缀判定会误放行
    （"public_backup".startswith("public")），修复后必须 404 且引擎
    未被调用。
    """

    COLLIDE_DIR = Path(__file__).resolve().parent.parent / "public_backup"

    @classmethod
    def setUpClass(cls):
        cls.httpd = HTTPServer(("127.0.0.1", 0),
                               studio_server.StudioHTTPRequestHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(
            target=cls.httpd.serve_forever,
            kwargs={"poll_interval": 0.05}, daemon=True)
        cls.thread.start()
        cls.COLLIDE_DIR.mkdir(exist_ok=True)
        import base64 as _b64
        (cls.COLLIDE_DIR / "probe.png").write_bytes(_b64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8"
            "BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="))

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.thread.join()
        cls.httpd.server_close()
        import shutil as _sh
        _sh.rmtree(cls.COLLIDE_DIR, ignore_errors=True)

    def post(self, path, body):
        return _post(self.port, path, body)

    def test_prefix_collision_blocked(self):
        mock = MagicMock()
        with patch.object(studio_server, "vision_inspect_artwork", mock):
            st, body = self.post(
                "/api/agnes/vision-inspect",
                {"image_path": "../public_backup/probe.png",
                 "trace_id": "t-tr-1"})
            self.assertEqual(st, 404)
            self.assertEqual(body["trace_id"], "t-tr-1")
            mock.assert_not_called()

    def test_prefix_collision_alt_path_blocked(self):
        # 不带 public/ 前缀的相对穿越同样被拦
        mock = MagicMock()
        with patch.object(studio_server, "vision_inspect_artwork", mock):
            st, body = self.post(
                "/api/agnes/vision-inspect",
                {"image_path": "public/../public_backup/probe.png",
                 "trace_id": "t-tr-3"})
            self.assertEqual(st, 404)
            mock.assert_not_called()

    def test_legit_subdir_still_allowed(self):
        mock = MagicMock(return_value={"ok": True, "inspection": "I",
                                       "cost_s": 0.1, "trace_id": "t-tr-2"})
        with patch.object(studio_server, "vision_inspect_artwork", mock):
            st, body = self.post("/api/agnes/vision-inspect",
                                 {"image_path": PNG_REL,
                                  "trace_id": "t-tr-2"})
            self.assertEqual(st, 200)
            self.assertTrue(body["success"])
            called_path = mock.call_args.args[0]
            self.assertTrue(Path(called_path).is_relative_to(
                Path(studio_server.PUBLIC_DIR).resolve()))




class TestConfigKeyMasking(unittest.TestCase):
    """第 17 轮：/api/config 的 masked_api_key 只保留末 4 位。"""

    @classmethod
    def setUpClass(cls):
        cls.httpd = HTTPServer(("127.0.0.1", 0),
                               studio_server.StudioHTTPRequestHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(
            target=cls.httpd.serve_forever,
            kwargs={"poll_interval": 0.05}, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.thread.join()
        cls.httpd.server_close()

    def get_config(self, fake_key):
        fake_cfg = {"detected": True,
                    "base_url": "http://127.0.0.1:13000",
                    "image_base_url": "http://127.0.0.1:13000",
                    "chat_base_url": "http://127.0.0.1:13000",
                    "api_key": fake_key,
                    "default_model": "agnes-3.0-flash",
                    "models": [], "chat_models": []}
        with patch.object(studio_server, "get_local_newapi_config",
                          return_value=fake_cfg):
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{self.port}/api/config",
                    timeout=10) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_masked_key_last4_only(self):
        key = "sk-testfakekey1234567890abcdef"
        st, body = self.get_config(key)
        self.assertEqual(st, 200)
        self.assertEqual(body["masked_api_key"], "..." + key[-4:])
        self.assertNotIn(key[:6], body["masked_api_key"])
        self.assertEqual(body["api_key"], "")

    def test_short_key_fully_masked(self):
        st, body = self.get_config("short")
        self.assertEqual(st, 200)
        self.assertEqual(body["masked_api_key"], "***")




class TestConnectionTraceEcho(unittest.TestCase):
    """第 20 轮：/api/test-connection 剩余三条路径的 trace 回显。

    第 15 轮只覆盖了该路由的两个参数校验 400；成功、HTTPError、
    连接失败三条路径漏网。本类用 urlopen 分流 mock（仅拦截发往
    /models 的探活请求，测试客户端自身的 HTTP 不受影响）。

    注意：不能把 urllib.request.urlopen 存为 TestCase 类属性再经
    self 取用——函数作为类属性会被描述符协议绑定成 bound method，
    导致 self 被当成 url 参数传入（本轮真实踩坑）。
    """

    @classmethod
    def setUpClass(cls):
        cls.httpd = HTTPServer(("127.0.0.1", 0),
                               studio_server.StudioHTTPRequestHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(
            target=cls.httpd.serve_forever,
            kwargs={"poll_interval": 0.05}, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.thread.join()
        cls.httpd.server_close()

    def _post_with_probe(self, body, probe_handler):
        real_urlopen = urllib.request.urlopen  # 局部变量，不经描述符绑定

        def fake_urlopen(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else ""
            if url.endswith("/models"):
                return probe_handler(req)
            return real_urlopen(req, timeout=timeout)

        with patch.object(urllib.request, "urlopen",
                          side_effect=fake_urlopen):
            return _post(self.port, "/api/test-connection", body)

    @staticmethod
    def _ok_probe(req):
        m = MagicMock()
        m.read.return_value = json.dumps(
            {"data": [{"id": "agnes-3.0-flash"}]}).encode("utf-8")
        m.__enter__.return_value = m
        m.__exit__.return_value = False
        return m

    @staticmethod
    def _http401_probe(req):
        raise urllib.error.HTTPError(
            url=req.full_url, code=401, msg="Unauthorized", hdrs={}, fp=None)

    @staticmethod
    def _refused_probe(req):
        raise urllib.error.URLError("Connection refused")

    def test_success_echoes_trace(self):
        st, body = self._post_with_probe(
            {"base_url": "http://probe.invalid/v1", "trace_id": "t-tc-1"},
            self._ok_probe)
        self.assertEqual(st, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["trace_id"], "t-tc-1")

    def test_http_error_echoes_trace(self):
        st, body = self._post_with_probe(
            {"base_url": "http://probe.invalid/v1", "trace_id": "t-tc-2"},
            self._http401_probe)
        self.assertEqual(st, 200)
        self.assertFalse(body["success"])
        self.assertEqual(body["trace_id"], "t-tc-2")
        self.assertEqual(body["code"], 401)

    def test_connection_failure_echoes_trace(self):
        st, body = self._post_with_probe(
            {"base_url": "http://probe.invalid/v1"},
            self._refused_probe)
        self.assertEqual(st, 200)
        self.assertFalse(body["success"])
        self.assertTrue(body["trace_id"].startswith("agnes-"))
        self.assertIn("连接失败", body["error"])


if __name__ == "__main__":
    unittest.main()
