import json
import sys
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from agnes_gateway import generate
from studio_server import is_configured_image_gateway, resolve_image_base_url, IMAGE_BASE_DEFAULT


class TestStudioServerImageRoute(unittest.TestCase):
    def test_image_base_url_precedes_legacy_base_url(self):
        cfg = {
            "detected": True,
            "image_base_url": "http://127.0.0.1:13000/v1",
            "base_url": "http://legacy.invalid:3000/v1",
        }
        self.assertEqual(resolve_image_base_url({}, cfg), "http://127.0.0.1:13000/v1")

    def test_explicit_base_url_overrides_local_config(self):
        cfg = {
            "detected": True,
            "image_base_url": "http://image.invalid/v1",
            "base_url": "http://legacy.invalid/v1",
        }
        self.assertEqual(resolve_image_base_url({"base_url": "http://override/v1/"}, cfg), "http://override/v1")

    def test_explicit_image_base_url_in_req_body(self):
        cfg = {
            "detected": True,
            "image_base_url": "http://image.invalid/v1",
            "base_url": "http://legacy.invalid/v1",
        }
        self.assertEqual(
            resolve_image_base_url({"image_base_url": "http://override-image.invalid/v1/"}, cfg),
            "http://override-image.invalid/v1",
        )

    def test_image_base_url_precedes_base_url_in_req_body(self):
        cfg = {"detected": True, "base_url": "http://legacy.invalid/v1"}
        self.assertEqual(
            resolve_image_base_url(
                {
                    "image_base_url": "http://priority-image.invalid/v1/",
                    "base_url": "http://fallback-base.invalid/v1/",
                },
                cfg,
            ),
            "http://priority-image.invalid/v1",
        )

    def test_base_url_is_legacy_compatibility_fallback(self):
        cfg = {"detected": True, "base_url": "http://legacy.invalid/v1"}
        self.assertEqual(resolve_image_base_url({}, cfg), "http://legacy.invalid/v1")

    def test_undetected_config_uses_active_local_image_gateway(self):
        self.assertEqual(resolve_image_base_url({}, {"detected": False}), IMAGE_BASE_DEFAULT.rstrip("/"))

    def test_resolve_image_base_url_none_and_non_dict_safe(self):
        self.assertEqual(resolve_image_base_url(None, None), IMAGE_BASE_DEFAULT.rstrip("/"))
        self.assertEqual(resolve_image_base_url("invalid", "invalid"), IMAGE_BASE_DEFAULT.rstrip("/"))


class TestIsConfiguredImageGateway(unittest.TestCase):
    def test_configured_image_gateway_exact_match(self):
        cfg = {"detected": True, "image_base_url": "http://127.0.0.1:13000/v1"}
        self.assertTrue(is_configured_image_gateway("http://127.0.0.1:13000/v1", cfg))
        self.assertFalse(is_configured_image_gateway("http://127.0.0.1:9999/v1", cfg))

    def test_configured_image_gateway_trailing_slash_normalization(self):
        cfg = {"detected": True, "image_base_url": "http://127.0.0.1:13000/v1"}
        self.assertTrue(is_configured_image_gateway("http://127.0.0.1:13000/v1/", cfg))

    def test_configured_image_gateway_undetected_defaults(self):
        self.assertTrue(is_configured_image_gateway(IMAGE_BASE_DEFAULT, {"detected": False}))
        self.assertTrue(is_configured_image_gateway(IMAGE_BASE_DEFAULT + "/", None))

    def test_configured_image_gateway_empty_or_non_matching(self):
        self.assertFalse(is_configured_image_gateway("", None))
        self.assertFalse(is_configured_image_gateway("http://evil.invalid", None))




class TestAgnesGatewayKeySentinel(unittest.TestCase):
    """第 18 轮：agnes_gateway.generate 的 "" 哨兵语义。

    与第 14 轮 call_agnes 的三态语义一致：None=回退服务端密钥，
    ""=明确无密钥（不发 Authorization 头）。旧 `key = api_key or key`
    会把显式 "" 吞掉并悄悄捡回服务端密钥。
    """

    def _capture_request(self, **kwargs):
        captured = {}
        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps(
            {"data": [{"url": "http://x/y.png"}]}).encode("utf-8")
        fake_resp.__enter__.return_value = fake_resp

        def fake_urlopen(req, timeout=None):
            captured["req"] = req
            return fake_resp

        with patch.object(urllib.request, "urlopen",
                          side_effect=fake_urlopen):
            with patch("agnes_gateway.load_gateway",
                       return_value=("http://127.0.0.1:13000/v1",
                                     "sk-server-secret", "m")):
                res = generate("hello", **kwargs)
        return res, captured["req"]

    def test_explicit_empty_key_sends_no_auth_header(self):
        res, req = self._capture_request(api_key="")
        self.assertTrue(res["ok"])
        self.assertIsNone(req.get_header("Authorization"))

    def test_none_key_falls_back_to_server_key(self):
        res, req = self._capture_request(api_key=None)
        self.assertTrue(res["ok"])
        self.assertEqual(req.get_header("Authorization"),
                         "Bearer sk-server-secret")

    def test_explicit_key_is_used(self):
        res, req = self._capture_request(api_key="sk-user")
        self.assertTrue(res["ok"])
        self.assertEqual(req.get_header("Authorization"), "Bearer sk-user")


if __name__ == "__main__":
    unittest.main()
