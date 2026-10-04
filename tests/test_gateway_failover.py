#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gateway_failover.py 测试：故障转移语义、端点解析、doctor 隔离。

http_post 全部 mock，不发起真实网络请求。
"""

import os
import socket
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import gateway_failover as G

EP1 = "http://127.0.0.1:13000/v1"
EP2 = "http://100.84.255.7:13000/v1"


def fake_post_factory(script):
    """script: list of ("ok", status, data) | ("raise", exc)。返回 (post, calls)。"""
    calls = []

    def post(url, payload, key, timeout):
        calls.append({"url": url, "key": key, "timeout": timeout})
        action = script[len(calls) - 1]
        if action[0] == "raise":
            raise action[1]
        return action[1], action[2]

    return post, calls


class ResolveEndpointsTest(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def _clean_gateway_env(self):
        for k in list(os.environ):
            if k.startswith("AGNES_") or k.startswith("NEW_API_") or k.startswith("OPENAI_"):
                del os.environ[k]

    def test_full_override_urls(self):
        self._clean_gateway_env()
        os.environ["AGNES_CHAT_BASE_URLS"] = EP2 + " , " + EP1 + "," + EP2
        eps = G.resolve_endpoints("chat")
        self.assertEqual(eps, [EP2, EP1])  # 去重保序

    def test_primary_plus_fallbacks(self):
        self._clean_gateway_env()
        os.environ["AGNES_CHAT_BASE_URL"] = EP1 + "/"
        os.environ["AGNES_CHAT_FALLBACK_URLS"] = EP2 + "," + EP1
        eps = G.resolve_endpoints("chat")
        self.assertEqual(eps, [EP1, EP2])

    def test_generic_agnes_base_url_fallback(self):
        self._clean_gateway_env()
        os.environ["AGNES_BASE_URL"] = "http://general.api:13000/v1"
        self.assertEqual(G.resolve_endpoints("chat"), ["http://general.api:13000/v1"])
        self.assertEqual(G.resolve_endpoints("image"), ["http://general.api:13000/v1"])

    def test_generic_new_api_base_url_fallback(self):
        self._clean_gateway_env()
        os.environ["NEW_API_BASE_URL"] = "http://newapi.base:13000/v1"
        self.assertEqual(G.resolve_endpoints("chat"), ["http://newapi.base:13000/v1"])
        self.assertEqual(G.resolve_endpoints("image"), ["http://newapi.base:13000/v1"])

    def test_chat_and_image_endpoint_isolation(self):
        self._clean_gateway_env()
        os.environ["AGNES_CHAT_BASE_URL"] = "http://chat.only:13000/v1"
        # image 不应受 AGNES_CHAT_BASE_URL 污染
        img_eps = G.resolve_endpoints("image")
        self.assertNotIn("http://chat.only:13000/v1", img_eps)

    def test_image_uses_own_prefix(self):
        self._clean_gateway_env()
        os.environ["AGNES_IMAGE_BASE_URLS"] = EP2
        self.assertEqual(G.resolve_endpoints("image"), [EP2])
        # chat 不受 image 配置影响（回退到 load_credentials/默认，至少非空合法）
        chat_eps = G.resolve_endpoints("chat")
        self.assertTrue(chat_eps)
        self.assertTrue(all(e.startswith("http") for e in chat_eps))

    def test_bad_kind(self):
        with self.assertRaises(ValueError):
            G.resolve_endpoints("nope")

    def test_default_when_nothing_configured(self):
        self._clean_gateway_env()
        eps = G.resolve_endpoints("chat")
        self.assertTrue(len(eps) >= 1)
        self.assertTrue(eps[0].startswith("http"))

    def test_resolve_endpoints_chat_with_custom_key_path(self):
        self._clean_gateway_env()
        with patch("gateway_failover.load_credentials", return_value=("http://custom-chat:13000/v1", "KEY")) as mock_load:
            eps = G.resolve_endpoints("chat", key_path="/path/to/custom_key.json")
            mock_load.assert_called_once_with(key_path="/path/to/custom_key.json")
            self.assertEqual(eps[0], "http://custom-chat:13000/v1")

    def test_resolve_endpoints_image_with_custom_key_path(self):
        self._clean_gateway_env()
        with patch("gateway_failover.load_gateway", return_value=("http://custom-img:13000/v1", "KEY", "m")) as mock_load:
            eps = G.resolve_endpoints("image", key_path="/path/to/custom_key.json")
            mock_load.assert_called_once_with(key_path="/path/to/custom_key.json")
            self.assertEqual(eps[0], "http://custom-img:13000/v1")


class FailoverTest(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)
        for k in list(os.environ):
            if k.startswith("AGNES_"):
                del os.environ[k]
        os.environ["AGNES_CHAT_BASE_URLS"] = EP1 + "," + EP2

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_first_success_short_circuits(self):
        post, calls = fake_post_factory([("ok", 200, {"x": 1})])
        res = G.post_with_failover("/chat/completions", {"m": "hi"},
                                   http_post=post, api_key="K")
        self.assertTrue(res["ok"])
        self.assertEqual(res["endpoint_used"], EP1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["key"], "K")
        self.assertTrue(calls[0]["url"].startswith(EP1))

    def test_connection_error_fails_over(self):
        post, calls = fake_post_factory([
            ("raise", urllib.error.URLError("refused")),
            ("ok", 200, {"x": 2}),
        ])
        res = G.post_with_failover("/chat/completions", {}, http_post=post)
        self.assertTrue(res["ok"])
        self.assertEqual(res["endpoint_used"], EP2)
        self.assertEqual(len(calls), 2)
        self.assertFalse(res["attempts"][0]["ok"])
        self.assertIn("URLError", res["attempts"][0]["error"])

    def test_timeout_fails_over(self):
        post, calls = fake_post_factory([
            ("raise", socket.timeout("timed out")),
            ("ok", 200, {}),
        ])
        res = G.post_with_failover("/x", {}, http_post=post)
        self.assertEqual(res["endpoint_used"], EP2)

    def test_502_503_504_fail_over(self):
        for code in (502, 503, 504):
            post, calls = fake_post_factory([
                ("ok", code, {"error": "bad"}),
                ("ok", 200, {"good": True}),
            ])
            res = G.post_with_failover("/x", {}, http_post=post)
            self.assertEqual(res["endpoint_used"], EP2, "HTTP %s 应切换" % code)
            self.assertEqual(len(calls), 2)

    def test_429_fails_over(self):
        post, calls = fake_post_factory([
            ("ok", 429, {"error": "rate limited"}),
            ("ok", 200, {}),
        ])
        res = G.post_with_failover("/x", {}, http_post=post)
        self.assertEqual(res["endpoint_used"], EP2)

    def test_4xx_does_not_fail_over(self):
        post, calls = fake_post_factory([("ok", 401, {"error": "bad key"})])
        res = G.post_with_failover("/x", {}, http_post=post)
        self.assertFalse(res["ok"])
        self.assertEqual(res["status"], 401)
        self.assertEqual(len(calls), 1)  # 401 是请求问题，不切换
        self.assertEqual(res["endpoint_used"], EP1)

    def test_all_fail_raises_aggregated(self):
        post, calls = fake_post_factory([
            ("raise", urllib.error.URLError("down1")),
            ("ok", 503, {}),
        ])
        with self.assertRaises(G.AllGatewaysFailed) as ctx:
            G.post_with_failover("/x", {}, http_post=post)
        msg = str(ctx.exception)
        self.assertIn(EP1, msg)
        self.assertIn(EP2, msg)

    def test_key_from_resolver(self):
        post, calls = fake_post_factory([("ok", 200, {})])
        G.post_with_failover("/x", {}, http_post=post,
                             key_resolver=lambda: ("base", "SECRETKEY", "m"))
        self.assertEqual(calls[0]["key"], "SECRETKEY")

    def test_explicit_key_wins_over_resolver(self):
        post, calls = fake_post_factory([("ok", 200, {})])
        resolver = MagicMock(return_value=("b", "FROM_RESOLVER", "m"))
        G.post_with_failover("/x", {}, http_post=post, api_key="EXPLICIT",
                             key_resolver=resolver)
        self.assertEqual(calls[0]["key"], "EXPLICIT")
        resolver.assert_not_called()

    def test_image_key_resolved_via_load_gateway(self):
        post, calls = fake_post_factory([("ok", 200, {})])
        with patch("gateway_failover.load_gateway", return_value=("http://base", "IMAGE_KEY", "model")):
            G.post_with_failover("/images/generations", {}, kind="image", http_post=post)
        self.assertEqual(calls[0]["key"], "IMAGE_KEY")

    def test_chat_key_resolved_via_load_credentials(self):
        post, calls = fake_post_factory([("ok", 200, {})])
        with patch("gateway_failover.load_credentials", return_value=("http://base", "CHAT_KEY")):
            G.post_with_failover("/chat/completions", {}, kind="chat", http_post=post)
        self.assertEqual(calls[0]["key"], "CHAT_KEY")

    def test_key_path_forwarded_to_resolver(self):
        post, calls = fake_post_factory([("ok", 200, {})])
        mock_resolver = MagicMock(return_value=("base", "CUSTOM_KEY"))
        G.post_with_failover("/x", {}, http_post=post,
                             key_resolver=mock_resolver,
                             key_path="/path/to/key.json")
        mock_resolver.assert_called_once_with(key_path="/path/to/key.json")
        self.assertEqual(calls[0]["key"], "CUSTOM_KEY")

    def test_key_path_forwarded_to_resolve_endpoints(self):
        post, calls = fake_post_factory([("ok", 200, {})])
        with patch("gateway_failover.resolve_endpoints", return_value=[EP1]) as mock_resolve:
            G.post_with_failover("/x", {}, http_post=post, api_key="K",
                                 key_path="/path/to/key.json")
            mock_resolve.assert_called_once_with("chat", key_path="/path/to/key.json")


class DoctorTest(unittest.TestCase):
    def test_doctor_401_is_warn_not_error(self):
        import urllib.request

        orig_urlopen = urllib.request.urlopen
        orig_resolve = G.resolve_endpoints

        def fake_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(
                req.full_url, 401, "Unauthorized", {}, None)

        urllib.request.urlopen = fake_urlopen
        G.resolve_endpoints = lambda kind="chat", key_path=None: [EP1]
        try:
            rep = G.doctor("chat")
        finally:
            urllib.request.urlopen = orig_urlopen
            G.resolve_endpoints = orig_resolve
        # 401 说明网关活着：warn（需认证），不是 error（不可达）
        self.assertEqual(rep[EP1]["status"], "warn")
        self.assertIn("401", rep[EP1]["message"])

    def test_doctor_survives_broken_endpoint(self):
        import urllib.request

        orig_urlopen = urllib.request.urlopen
        orig_resolve = G.resolve_endpoints

        def fake_urlopen(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            if "badhost" in url:
                raise urllib.error.URLError("no route")
            m = MagicMock()
            m.status = 200
            m.__enter__ = MagicMock(return_value=m)
            m.__exit__ = MagicMock(return_value=False)
            return m

        urllib.request.urlopen = fake_urlopen
        G.resolve_endpoints = lambda kind="chat", key_path=None: ["http://badhost:1/v1", EP1]
        try:
            rep = G.doctor("chat")
        finally:
            urllib.request.urlopen = orig_urlopen
            G.resolve_endpoints = orig_resolve
        self.assertEqual(rep["http://badhost:1/v1"]["status"], "error")
        self.assertEqual(rep[EP1]["status"], "ok")

    def test_doctor_forwards_key_path(self):
        with patch("gateway_failover.resolve_endpoints", return_value=[EP1]) as mock_resolve:
            with patch("urllib.request.urlopen") as mock_url:
                resp = MagicMock()
                resp.status = 200
                resp.read.return_value = b"{}"
                mock_url.return_value.__enter__.return_value = resp
                res = G.doctor("chat", key_path="/path/to/key.json")
                mock_resolve.assert_called_once_with("chat", key_path="/path/to/key.json")
                self.assertIn(EP1, res)


class CliTest(unittest.TestCase):
    def test_cli_main_endpoints_with_key_path(self):
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            with patch("gateway_failover.resolve_endpoints", return_value=[EP1]) as mock_resolve:
                G.main(["--kind", "image", "--key-path", "/path/to/custom_key.json"])
                mock_resolve.assert_called_once_with("image", key_path="/path/to/custom_key.json")
        self.assertIn(EP1, buf.getvalue())

    def test_cli_main_doctor_with_key_path(self):
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            with patch("gateway_failover.doctor", return_value={EP1: {"status": "ok"}}) as mock_doctor:
                G.main(["--kind", "chat", "--doctor", "--key-path", "/path/to/custom_key.json"])
                mock_doctor.assert_called_once_with("chat", key_path="/path/to/custom_key.json")
        self.assertIn("ok", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
