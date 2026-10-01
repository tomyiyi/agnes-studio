#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agnes Studio - chat 凭证解析与配置漂移防护回归测试。

覆盖：
1. scripts/studio_server.py::resolve_chat_credentials 的优先级与规范化
2. 环境化石端口（8045/18045）硬编码漂移防护——未来若有人重新引入
   Gemini 时代遗留网关地址，测试必须变红
3. /api/agnes/* 别名路由与 /api/gemini/* 配对存在（合同式断言）
"""

import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import studio_server
from studio_server import resolve_chat_credentials


FAKE_KEY = "sk-test-fake-key-not-real"
FAKE_BASE = "http://test-gateway.invalid:9999/v1"


class TestResolveChatCredentials(unittest.TestCase):
    def test_explicit_request_body_wins(self):
        with patch.object(studio_server, "load_credentials", return_value=("http://should-not-win/v1", "sk-should-not-win", "m")):
            base, key = resolve_chat_credentials({"chat_base_url": FAKE_BASE + "/", "api_key": "  " + FAKE_KEY + "  "})
        self.assertEqual(base, FAKE_BASE)  # 尾部斜杠被去除
        self.assertEqual(key, FAKE_KEY)    # 前后空白被去除

    def test_legacy_base_url_alias_still_works(self):
        base, key = resolve_chat_credentials({"base_url": FAKE_BASE, "api_key": FAKE_KEY})
        self.assertEqual((base, key), (FAKE_BASE, FAKE_KEY))

    def test_explicit_base_matching_default_fills_key(self):
        # 第 14 轮：显式地址 == 服务端默认网关 → 可用服务端密钥（前端常规流程）
        with patch.object(studio_server, "load_credentials", return_value=("http://from-env/v1", FAKE_KEY, "m")):
            base, key = resolve_chat_credentials({"chat_base_url": "http://from-env/v1/"})
        self.assertEqual(base, "http://from-env/v1")  # 尾部斜杠被去除
        self.assertEqual(key, FAKE_KEY)

    def test_explicit_foreign_base_without_key_yields_empty(self):
        # 第 14 轮安全收紧：显式指向其他地址且未自带 key → ""（明确无密钥，
        # 下游不再回退解析、不发送 Authorization 头），防 SSRF 密钥外泄
        with patch.object(studio_server, "load_credentials", return_value=("http://from-env/v1", FAKE_KEY, "m")):
            base, key = resolve_chat_credentials({"chat_base_url": FAKE_BASE})
        self.assertEqual(base, FAKE_BASE)
        self.assertEqual(key, "")

    def test_explicit_foreign_base_with_own_key_honored(self):
        # 指向自定义网关 + 自带 key → 使用调用方自己的 key
        with patch.object(studio_server, "load_credentials", return_value=("http://from-env/v1", FAKE_KEY, "m")):
            base, key = resolve_chat_credentials({"base_url": FAKE_BASE, "api_key": "sk-user-own"})
        self.assertEqual((base, key), (FAKE_BASE, "sk-user-own"))

    def test_load_credentials_provides_both_when_body_empty(self):
        with patch.object(studio_server, "load_credentials", return_value=("http://from-env/v1", FAKE_KEY, "m")):
            base, key = resolve_chat_credentials({})
        self.assertEqual((base, key), ("http://from-env/v1", FAKE_KEY))

    def test_load_credentials_exception_falls_through(self):
        def boom():
            raise RuntimeError("boom")
        clean_env = {k: v for k, v in __import__("os").environ.items()
                     if k not in ("AGNES_API_KEY", "AGNES_GATEWAY_KEY", "ANTIGRAVITY_API_KEY", "OPENAI_API_KEY")}
        with patch.object(studio_server, "load_credentials", boom), \
             patch.object(studio_server, "get_local_newapi_config", return_value={"detected": False}), \
             patch.dict("os.environ", clean_env, clear=True):
            base, key = resolve_chat_credentials({})
        self.assertEqual(base, studio_server.CHAT_BASE_DEFAULT.rstrip("/"))
        self.assertIsNone(key)

    def test_engine_missing_falls_back_to_local_config(self):
        local_cfg = {"detected": True, "chat_base_url": "http://local-cfg/v1", "api_key": "sk-local-cfg"}
        with patch.object(studio_server, "load_credentials", None), \
             patch.object(studio_server, "get_local_newapi_config", return_value=local_cfg), \
             patch.dict("os.environ", {}, clear=False):
            base, key = resolve_chat_credentials(None)
        self.assertEqual((base, key), ("http://local-cfg/v1", "sk-local-cfg"))

    def test_non_dict_body_treated_as_empty(self):
        with patch.object(studio_server, "load_credentials", return_value=("http://from-env/v1", FAKE_KEY, "m")):
            base, key = resolve_chat_credentials("not-a-dict")
        self.assertEqual((base, key), ("http://from-env/v1", FAKE_KEY))

    def test_default_base_has_no_fossil_port(self):
        self.assertNotIn(":18045", studio_server.CHAT_BASE_DEFAULT)
        self.assertNotIn(":8045", studio_server.CHAT_BASE_DEFAULT)


class TestConfigFossilDriftGuard(unittest.TestCase):
    """防止 Gemini 时代遗留网关地址（18045/8045）以硬编码形式复发。"""

    FOSSIL_URL_RE = re.compile(r"https?://[^\s\"']*:(?:18045|8045)\b")

    def test_no_hardcoded_fossil_gateway_urls_in_scripts(self):
        scripts_dir = ROOT / "scripts"
        offenders = []
        for path in sorted(scripts_dir.glob("*.py")):
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if self.FOSSIL_URL_RE.search(line):
                    offenders.append("%s:%d: %s" % (path.name, lineno, line.strip()[:100]))
        self.assertEqual(offenders, [], "发现环境化石网关地址硬编码")


class TestAgnesAliasRoutes(unittest.TestCase):
    """三大 AI 路由的 /api/agnes/* 别名必须与 /api/gemini/* 配对存在。"""

    PAIRS = [
        ("/api/gemini/generate-brief", "/api/agnes/generate-brief"),
        ("/api/gemini/refine-prompt", "/api/agnes/refine-prompt"),
        ("/api/gemini/vision-inspect", "/api/agnes/vision-inspect"),
    ]

    def test_alias_pairs_exist_in_source(self):
        source = Path(studio_server.__file__).read_text(encoding="utf-8")
        for gemini_route, agnes_route in self.PAIRS:
            with self.subTest(route=agnes_route):
                self.assertIn('"%s"' % gemini_route, source)
                self.assertIn('"%s"' % agnes_route, source)


if __name__ == "__main__":
    unittest.main()
