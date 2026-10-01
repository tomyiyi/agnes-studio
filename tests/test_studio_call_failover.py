#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第3轮测试：call_agnes 故障转移接入 + 调用层统一 trace id。

全部 mock urllib.request.urlopen / time.sleep，不发起真实网络请求。
覆盖：
  - 单端点零行为变更（旧重试语义不变）
  - 多端点：连接拒绝/5xx 立即切换（不 sleep）；4xx 不切换不重试
  - 全部端点故障 -> ok=False（不抛异常，保持 call_agnes 旧契约）
  - trace_id 透传 / 自动生成；日志带 trace；返回带 trace_id/endpoint_used
  - failover=False 逃生开关；显式 base_url 排首位；端点去重
"""

import io
import json
import os
import sys
import unittest
import urllib.error
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import agnes_engine as E

EP_LIVE = "http://127.0.0.1:13000/v1"
EP_DEAD = "http://127.0.0.1:19999/v1"
EP_DEAD2 = "http://127.0.0.1:19998/v1"

_FAILOVER_KEYS = ("AGNES_CHAT_BASE_URLS", "AGNES_CHAT_BASE_URL",
                  "AGNES_CHAT_FALLBACK_URLS")


@contextmanager
def failover_env(**kv):
    """临时设置 failover 环境变量，退出后恢复（默认先清空三者）。"""
    old = {k: os.environ.get(k) for k in _FAILOVER_KEYS}
    try:
        for k in _FAILOVER_KEYS:
            os.environ.pop(k, None)
        os.environ.update(kv)
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _ok_resp(text="hello"):
    m = MagicMock()
    m.read.return_value = json.dumps(
        {"choices": [{"message": {"content": text}}], "usage": {}}).encode("utf-8")
    m.__enter__.return_value = m
    return m


def _http_error(code):
    return urllib.error.HTTPError(
        url="http://x/", code=code, msg="boom", hdrs={},
        fp=io.BytesIO(b'{"error": {"message": "boom"}}'))


def _refused():
    return urllib.error.URLError("Connection refused")


class TestCallAgnesFailover(unittest.TestCase):
    def _patch_common(self):
        """限速器 mock + sleep mock（避免 15s 真实退避）。"""
        p1 = patch("agnes_engine.get_rate_limiter")
        p2 = patch("time.sleep")
        self.addCleanup(p1.stop)
        self.addCleanup(p2.stop)
        limiter = p1.start()
        limiter.return_value = MagicMock()
        return p2.start()

    # ---- 单端点：零行为变更 ----

    def test_single_endpoint_retry_unchanged(self):
        mock_sleep = self._patch_common()
        with failover_env():
            with patch("urllib.request.urlopen") as mu:
                mu.side_effect = [_http_error(429), _ok_resp("hi")]
                res = E.call_agnes([{"role": "user", "content": "hi"}], retries=1)
        self.assertTrue(res["ok"])
        self.assertEqual(res["content"], "hi")
        self.assertEqual(mu.call_count, 2)
        # 同一端点重试：两次调用 URL 相同
        urls = [c.args[0].full_url for c in mu.call_args_list]
        self.assertEqual(urls[0], urls[1])
        mock_sleep.assert_called_once()  # 429 退避一次（旧语义）
        self.assertTrue(res["trace_id"].startswith("agnes-"))
        self.assertEqual(res["endpoint_used"], urls[0].rsplit("/chat/completions", 1)[0])

    def test_single_endpoint_4xx_no_retry(self):
        mock_sleep = self._patch_common()
        with failover_env():
            with patch("urllib.request.urlopen") as mu:
                mu.side_effect = _http_error(401)
                res = E.call_agnes([], retries=2)
        self.assertFalse(res["ok"])
        self.assertIn("HTTP 401", res["error"])
        self.assertEqual(mu.call_count, 1)
        mock_sleep.assert_not_called()
        self.assertTrue(res["trace_id"].startswith("agnes-"))

    # ---- 多端点：故障转移 ----

    def test_failover_on_connection_refused(self):
        mock_sleep = self._patch_common()
        with failover_env(AGNES_CHAT_BASE_URLS=f"{EP_DEAD},{EP_LIVE}"):
            def fake(req, *a, **k):
                if "19999" in req.full_url:
                    raise _refused()
                return _ok_resp("via-fallback")
            with patch("urllib.request.urlopen", side_effect=fake) as mu:
                res = E.call_agnes([{"role": "user", "content": "hi"}], retries=0)
        self.assertTrue(res["ok"])
        self.assertEqual(res["content"], "via-fallback")
        self.assertEqual(res["endpoint_used"], EP_LIVE)
        self.assertEqual(mu.call_count, 2)
        mock_sleep.assert_not_called()  # 切换不 sleep

    def test_failover_on_500(self):
        mock_sleep = self._patch_common()
        with failover_env(AGNES_CHAT_BASE_URLS=f"{EP_DEAD},{EP_LIVE}"):
            def fake(req, *a, **k):
                if "19999" in req.full_url:
                    raise _http_error(500)
                return _ok_resp("via-fallback")
            with patch("urllib.request.urlopen", side_effect=fake) as mu:
                res = E.call_agnes([], retries=2)
        self.assertTrue(res["ok"])
        self.assertEqual(res["endpoint_used"], EP_LIVE)
        self.assertEqual(mu.call_count, 2)
        mock_sleep.assert_not_called()

    def test_4xx_does_not_failover(self):
        mock_sleep = self._patch_common()
        with failover_env(AGNES_CHAT_BASE_URLS=f"{EP_DEAD},{EP_LIVE}"):
            with patch("urllib.request.urlopen") as mu:
                mu.side_effect = _http_error(400)
                res = E.call_agnes([], retries=2)
        self.assertFalse(res["ok"])
        self.assertIn("HTTP 400", res["error"])
        self.assertEqual(mu.call_count, 1)  # 请求本身问题：不切换
        mock_sleep.assert_not_called()

    def test_all_endpoints_fail_returns_error_not_raise(self):
        mock_sleep = self._patch_common()
        with failover_env(AGNES_CHAT_BASE_URLS=f"{EP_DEAD},{EP_DEAD2}"):
            with patch("urllib.request.urlopen") as mu:
                mu.side_effect = _refused()
                res = E.call_agnes([], retries=0)
        self.assertFalse(res["ok"])
        self.assertIn("Connection refused", res["error"])
        self.assertEqual(mu.call_count, 2)  # 每个端点各试 1 次
        self.assertTrue(res["trace_id"].startswith("agnes-"))
        mock_sleep.assert_not_called()

    def test_failover_disabled_escape_hatch(self):
        self._patch_common()
        with failover_env(AGNES_CHAT_BASE_URLS=f"{EP_DEAD},{EP_LIVE}"):
            with patch("urllib.request.urlopen") as mu:
                mu.side_effect = _refused()
                res = E.call_agnes([], base_url=EP_DEAD, retries=0, failover=False)
        self.assertFalse(res["ok"])
        self.assertEqual(mu.call_count, 1)  # 只打显式端点，不切换

    def test_explicit_base_url_goes_first(self):
        self._patch_common()
        explicit = "http://explicit:13000/v1"
        with failover_env(AGNES_CHAT_BASE_URLS="http://a:1/v1,http://b:2/v1"):
            with patch("urllib.request.urlopen") as mu:
                mu.side_effect = _refused()
                E.call_agnes([], base_url=explicit, retries=0)
        urls = [c.args[0].full_url for c in mu.call_args_list]
        self.assertTrue(urls[0].startswith(explicit))
        self.assertEqual(len(urls), 3)  # explicit + a + b

    # ---- 端点解析 ----

    def test_chat_endpoints_dedup(self):
        with failover_env(
                AGNES_CHAT_BASE_URLS=f"{EP_LIVE},http://100.84.255.7:13000/v1"):
            eps = E._chat_endpoints(EP_LIVE)
        self.assertEqual(eps, [EP_LIVE, "http://100.84.255.7:13000/v1"])

    def test_chat_endpoints_default_single(self):
        with failover_env():
            eps = E._chat_endpoints(None)
        self.assertEqual(len(eps), 1)
        self.assertTrue(eps[0].startswith("http"))

    # ---- trace id ----

    def test_trace_id_passthrough(self):
        self._patch_common()
        with failover_env():
            with patch("urllib.request.urlopen") as mu:
                mu.return_value = _ok_resp()
                res = E.call_agnes([], trace_id="req-42", retries=0)
        self.assertEqual(res["trace_id"], "req-42")

    def test_trace_id_generated_when_blank(self):
        self._patch_common()
        with failover_env():
            with patch("urllib.request.urlopen") as mu:
                mu.return_value = _ok_resp()
                res = E.call_agnes([], trace_id="   ", retries=0)
        self.assertTrue(res["trace_id"].startswith("agnes-"))
        self.assertEqual(len(res["trace_id"]), len("agnes-") + 12)

    def test_trace_id_in_logs(self):
        import contextlib
        buf = io.StringIO()
        self._patch_common()
        with failover_env():
            with contextlib.redirect_stdout(buf):
                with patch("urllib.request.urlopen") as mu:
                    mu.side_effect = _refused()
                    res = E.call_agnes([], retries=1)
        trace = res["trace_id"]
        # 重试日志行必须携带同一 trace id
        self.assertIn(f"[{trace}]", buf.getvalue())

    def test_wrapper_trace_passthrough(self):
        self._patch_common()
        with patch("agnes_engine.call_agnes") as mc:
            mc.return_value = {"ok": False, "error": "x"}
            E.generate_creative_brief("主题", trace_id="t-1")
            self.assertEqual(mc.call_args.kwargs["trace_id"], "t-1")
            E.refine_prompt_for_agnes("prompt", trace_id="t-2")
            self.assertEqual(mc.call_args.kwargs["trace_id"], "t-2")


if __name__ == "__main__":
    unittest.main()
