#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agnes Studio - 网关健康检查（/api/gateway/health）回归测试。

覆盖：
1. probe_gateway 成功 / HTTPError / 连接异常 三种路径的结构化结果
2. 无 key 时不发送 Authorization 头；有 key 时经 Bearer 头出站，
   但 key 绝不出现在返回结果中
3. 非法 base_url 直接判不可达
4. /api/gateway/health 路由在源码中存在且同时探活 chat 与 image
"""

import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import studio_server
from studio_server import probe_gateway


class FakeHTTPResponse:
    """最小的 urlopen 上下文管理器替身。"""

    def __init__(self, payload, status=200):
        self._payload = payload
        self.status = status

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


MODELS_PAYLOAD = {
    "data": [
        {"id": "agnes-3.0-flash"},
        {"id": "agnes-image-2.5-flash"},
        {"id": "dall-e-3"},
    ]
}


class TestProbeGateway(unittest.TestCase):
    def test_success_returns_structured_result(self):
        with patch.object(studio_server.urllib.request, "urlopen", return_value=FakeHTTPResponse(MODELS_PAYLOAD)):
            res = probe_gateway("http://gw.invalid:13000/v1/")
        self.assertTrue(res["reachable"])
        self.assertEqual(res["base_url"], "http://gw.invalid:13000/v1")  # 尾部斜杠去除
        self.assertEqual(res["model_count"], 3)
        self.assertIn("agnes-3.0-flash", res["chat_models"])
        self.assertIn("agnes-image-2.5-flash", res["image_models"])
        self.assertIn("latency_ms", res)
        # 结果中绝不能出现任何 key 字样
        self.assertNotIn("api_key", json.dumps(res))

    def test_no_authorization_header_sent(self):
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["headers"] = {k.lower(): v for k, v in req.header_items()}
            captured["url"] = req.full_url
            return FakeHTTPResponse(MODELS_PAYLOAD)

        with patch.object(studio_server.urllib.request, "urlopen", side_effect=fake_urlopen):
            probe_gateway("http://gw.invalid:13000/v1")
        self.assertNotIn("authorization", captured["headers"])
        self.assertTrue(captured["url"].endswith("/models"))

    def test_key_sent_as_bearer_header_but_never_in_result(self):
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["headers"] = {k.lower(): v for k, v in req.header_items()}
            return FakeHTTPResponse(MODELS_PAYLOAD)

        with patch.object(studio_server.urllib.request, "urlopen", side_effect=fake_urlopen):
            res = probe_gateway("http://gw.invalid:13000/v1", api_key="sk-real-key")
        self.assertEqual(captured["headers"].get("authorization"), "Bearer sk-real-key")
        self.assertNotIn("sk-real-key", json.dumps(res))
        self.assertTrue(res["reachable"])

    def test_http_error_converges_to_unreachable(self):
        err = urllib.error.HTTPError("http://gw.invalid/v1/models", 503, "Service Unavailable", {}, io.BytesIO(b"{}"))

        def fake_urlopen(req, timeout=None):
            raise err

        with patch.object(studio_server.urllib.request, "urlopen", side_effect=fake_urlopen):
            res = probe_gateway("http://gw.invalid/v1")
        self.assertFalse(res["reachable"])
        self.assertEqual(res["http_status"], 503)
        self.assertIn("503", res["error"])

    def test_connection_failure_converges_to_unreachable(self):
        def fake_urlopen(req, timeout=None):
            raise urllib.error.URLError("connection refused")

        with patch.object(studio_server.urllib.request, "urlopen", side_effect=fake_urlopen):
            res = probe_gateway("http://gw.invalid:1/v1")
        self.assertFalse(res["reachable"])
        self.assertIn("连接失败", res["error"])

    def test_invalid_base_url_is_unreachable(self):
        for bad in ("", "not-a-url", "ftp://gw.invalid/v1"):
            res = probe_gateway(bad)
            self.assertFalse(res["reachable"])
            self.assertEqual(res["error"], "base_url 非法")


class TestGatewayHealthRoute(unittest.TestCase):
    def test_health_route_probes_both_gateways(self):
        source = Path(studio_server.__file__).read_text(encoding="utf-8")
        self.assertIn('"/api/gateway/health"', source)
        self.assertIn("probe_gateway(chat_base, api_key=chat_key)", source)
        self.assertIn("probe_gateway(image_base, api_key=image_key)", source)


if __name__ == "__main__":
    unittest.main()
