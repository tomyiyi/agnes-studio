#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第8轮测试：/api/generate-image 接入网关故障转移 + trace_id。

mock studio_server.post_with_failover（不发起真实生图调用），验证：
  - 成功路径：响应 success/trace_id/endpoint_used/file_path，图片真实落盘
  - 请求体 trace_id 透传到响应；缺省时自动生成 agnes-<12hex>
  - first_endpoint=显式解析的 image base_url（请求级覆盖排首位）
  - 400（缺 prompt）；AllGatewaysFailed -> 500；网关 4xx -> 500；
    无图片数据 -> 500
"""

import base64
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

# 1x1 PNG
PNG_B64 = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8"
           "BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
EP_IMG = "http://127.0.0.1:13000/v1"


def _ok_result(**kw):
    d = {"ok": True, "status": 200,
         "data": {"data": [{"b64_json": PNG_B64}]},
         "endpoint_used": EP_IMG, "attempts": []}
    d.update(kw)
    return d


def _post(port, path, body):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:%d%s" % (port, path), data=data, method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")


class TestGenerateImageFailover(unittest.TestCase):
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

    def post(self, body):
        return _post(self.port, "/api/generate-image", body)

    def _saved_path(self, file_path):
        # file_path 约定为相对路径 assets/generated/<name>；实际落盘在 GENERATED_DIR
        return studio_server.GENERATED_DIR / Path(file_path).name

    def _cleanup(self, file_path):
        if file_path:
            p = self._saved_path(file_path)
            if p.is_file():
                p.unlink()

    def test_ok_saves_file_and_echoes_trace(self):
        mock = MagicMock(return_value=_ok_result())
        with patch.object(studio_server, "post_with_failover", mock):
            st, body = self.post({"prompt": "a cat", "trace_id": "img-t1"})
            self.addCleanup(self._cleanup, body.get("file_path", ""))
            self.assertEqual(st, 200)
            self.assertTrue(body["success"])
            self.assertEqual(body["trace_id"], "img-t1")
            self.assertEqual(body["endpoint_used"], EP_IMG)
            # 图片真实落盘且为有效 PNG
            p = self._saved_path(body["file_path"])
            self.assertTrue(p.is_file())
            self.assertEqual(p.read_bytes()[:8], base64.b64decode(PNG_B64)[:8])
        # first_endpoint = 请求级解析地址（排首位）
        self.assertEqual(mock.call_args.kwargs["first_endpoint"], EP_IMG)
        self.assertEqual(mock.call_args.kwargs["kind"], "image")
        self.assertEqual(mock.call_args.args[0], "/images/generations")

    def test_trace_id_generated_when_missing(self):
        mock = MagicMock(return_value=_ok_result())
        with patch.object(studio_server, "post_with_failover", mock):
            st, body = self.post({"prompt": "a cat"})
            self.addCleanup(self._cleanup, body.get("file_path", ""))
            self.assertEqual(st, 200)
            self.assertTrue(body["trace_id"].startswith("agnes-"))

    def test_400_missing_prompt(self):
        mock = MagicMock()
        with patch.object(studio_server, "post_with_failover", mock):
            st, body = self.post({"prompt": "  "})
            self.assertEqual(st, 400)
            self.assertFalse(body["success"])
            mock.assert_not_called()

    def test_all_gateways_failed_500(self):
        mock = MagicMock(side_effect=studio_server.AllGatewaysFailed("all down"))
        with patch.object(studio_server, "post_with_failover", mock):
            st, body = self.post({"prompt": "a cat", "trace_id": "img-t2"})
            self.assertEqual(st, 500)
            self.assertFalse(body["success"])
            self.assertEqual(body["trace_id"], "img-t2")
            self.assertIn("全部故障", body["error"])

    def test_gateway_4xx_no_retry_500(self):
        mock = MagicMock(return_value={
            "ok": False, "status": 401, "data": {"error": {"message": "bad key"}},
            "endpoint_used": EP_IMG, "attempts": []})
        with patch.object(studio_server, "post_with_failover", mock):
            st, body = self.post({"prompt": "a cat", "trace_id": "img-t3"})
            self.assertEqual(st, 500)
            self.assertEqual(body["trace_id"], "img-t3")
            self.assertIn("401", body["error"])

    def test_no_image_data_500(self):
        mock = MagicMock(return_value=_ok_result(data={"data": []}))
        with patch.object(studio_server, "post_with_failover", mock):
            st, body = self.post({"prompt": "a cat"})
            self.assertEqual(st, 500)
            self.assertIn("未能从模型响应中提取", body["error"])

    def test_400_paths_echo_trace_id(self):
        # 第 13 轮：400 校验路径与 500 路径保持 trace 回显一致
        mock = MagicMock()
        with patch.object(studio_server, "post_with_failover", mock):
            st, body = self.post({"prompt": "  ", "trace_id": "img-t400a"})
            self.assertEqual(st, 400)
            self.assertEqual(body["trace_id"], "img-t400a")
            st, body = self.post({"prompt": "a cat", "base_url": "ftp://x",
                                  "trace_id": "img-t400b"})
            self.assertEqual(st, 400)
            self.assertEqual(body["trace_id"], "img-t400b")
            mock.assert_not_called()

    def test_success_logs_failover_attempts(self):
        # 第 13 轮：发生切换时成功日志打印故障转移明细
        attempts = [
            {"endpoint": "http://127.0.0.1:59999/v1", "ok": False,
             "error": "ConnectionRefusedError: [Errno 111]"},
            {"endpoint": EP_IMG, "ok": True, "status": 200},
        ]
        mock = MagicMock(return_value=_ok_result(attempts=attempts))
        with patch.object(studio_server, "post_with_failover", mock), \
                patch("builtins.print") as mock_print:
            st, body = self.post({"prompt": "a cat", "trace_id": "img-tlog"})
            self.addCleanup(self._cleanup, body.get("file_path", ""))
            self.assertEqual(st, 200)
            self.assertTrue(body["success"])
        logged = " ".join(str(c.args[0]) for c in mock_print.call_args_list)
        self.assertIn("img-tlog", logged)
        self.assertIn("故障转移", logged)
        self.assertIn("59999", logged)
        self.assertIn("ConnectionRefusedError", logged)

    def test_success_log_no_failover_note_without_switch(self):
        # 未发生切换时日志保持原样（无多余后缀）
        mock = MagicMock(return_value=_ok_result(attempts=[
            {"endpoint": EP_IMG, "ok": True, "status": 200}]))
        with patch.object(studio_server, "post_with_failover", mock), \
                patch("builtins.print") as mock_print:
            st, body = self.post({"prompt": "a cat", "trace_id": "img-tlog2"})
            self.addCleanup(self._cleanup, body.get("file_path", ""))
            self.assertEqual(st, 200)
        logged = " ".join(str(c.args[0]) for c in mock_print.call_args_list)
        self.assertIn("img-tlog2", logged)
        self.assertNotIn("故障转移", logged)

    def test_first_endpoint_prefers_explicit(self):
        mock = MagicMock(return_value=_ok_result(endpoint_used="http://x:1/v1"))
        with patch.object(studio_server, "post_with_failover", mock):
            st, body = self.post({"prompt": "a cat",
                                  "base_url": "http://x:1/v1"})
            self.addCleanup(self._cleanup, body.get("file_path", ""))
            self.assertEqual(st, 200)
        self.assertEqual(mock.call_args.kwargs["first_endpoint"], "http://x:1/v1")


    def test_explicit_foreign_base_without_key_sends_no_key(self):
        """第 14 轮：显式指向非配置网关且未自带 key → api_key=""（明确无密钥，
        阻止 post_with_failover 重新解析服务端默认 key），防 SSRF 密钥外泄。"""
        mock = MagicMock(return_value=_ok_result(endpoint_used="http://evil:9/v1"))
        with patch.object(studio_server, "post_with_failover", mock):
            st, body = self.post({"prompt": "a cat", "base_url": "http://evil:9/v1"})
            self.addCleanup(self._cleanup, body.get("file_path", ""))
            self.assertEqual(st, 200)
        self.assertEqual(mock.call_args.kwargs["api_key"], "")

    def test_explicit_foreign_base_with_own_key_uses_it(self):
        """指向自定义网关 + 自带 key → 使用调用方自己的 key。"""
        mock = MagicMock(return_value=_ok_result(endpoint_used="http://x:1/v1"))
        with patch.object(studio_server, "post_with_failover", mock):
            st, body = self.post({"prompt": "a cat", "base_url": "http://x:1/v1",
                                  "api_key": "sk-user-own"})
            self.addCleanup(self._cleanup, body.get("file_path", ""))
            self.assertEqual(st, 200)
        self.assertEqual(mock.call_args.kwargs["api_key"], "sk-user-own")

    def test_default_path_key_binding(self):
        """无显式 base_url → 目标为服务端配置网关：注入本地 key；
        无本地配置时传 None（下游按旧链解析，保持回退行为）。"""
        mock = MagicMock(return_value=_ok_result())
        with patch.object(studio_server, "post_with_failover", mock):
            st, body = self.post({"prompt": "a cat"})
            self.addCleanup(self._cleanup, body.get("file_path", ""))
            self.assertEqual(st, 200)
        local_cfg = studio_server.get_local_newapi_config()
        expected = (local_cfg.get("api_key") or "").strip() or None
        self.assertEqual(mock.call_args.kwargs["api_key"], expected)


class TestPostWithFailoverFirstEndpoint(unittest.TestCase):
    """gateway_failover.first_endpoint 参数单元测试（mock http_post）。"""

    def test_first_endpoint_goes_first_and_dedups(self):
        import gateway_failover as gf
        calls = []

        def fake_post(url, payload, key, timeout):
            calls.append(url)
            if "dead" in url:
                raise urllib.error.URLError("refused")
            return 200, {"data": []}

        with patch.dict("os.environ", {"AGNES_IMAGE_BASE_URLS":
                                       "http://dead:1/v1,http://live:2/v1"}):
            res = gf.post_with_failover(
                "/images/generations", {}, kind="image",
                first_endpoint="http://live:2/v1",  # 与环境链重复 -> 去重后仍首位
                http_post=fake_post, api_key="k")
        self.assertTrue(res["ok"])
        self.assertEqual(res["endpoint_used"], "http://live:2/v1")
        self.assertEqual(len(calls), 1)  # 首端点即成功，无需切换

    def test_first_endpoint_fails_over_to_chain(self):
        import gateway_failover as gf
        calls = []

        def fake_post(url, payload, key, timeout):
            calls.append(url)
            if "explicit" in url:
                raise urllib.error.URLError("refused")
            return 200, {"data": []}

        with patch.dict("os.environ", {"AGNES_IMAGE_BASE_URLS":
                                       "http://live:2/v1"}):
            res = gf.post_with_failover(
                "/images/generations", {}, kind="image",
                first_endpoint="http://explicit:9/v1",
                http_post=fake_post, api_key="k")
        self.assertTrue(res["ok"])
        self.assertEqual(res["endpoint_used"], "http://live:2/v1")
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0].startswith("http://explicit:9/v1"))


if __name__ == "__main__":
    unittest.main()
