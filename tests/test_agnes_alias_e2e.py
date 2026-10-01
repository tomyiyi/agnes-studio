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


if __name__ == "__main__":
    unittest.main()
