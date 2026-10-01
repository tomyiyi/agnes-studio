import re
import unittest
from pathlib import Path
INDEX = Path(__file__).parents[1] / "public" / "index.html"
class StudioFrontendImageConfigContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = INDEX.read_text(encoding="utf-8")
        start = cls.source.index("async function generateBackgroundWithAgnes()")
        end = cls.source.index("async function inspectPosterWithGemini()", start)
        cls.generate_block = cls.source[start:end]
    def test_default_config_has_active_image_endpoint(self):
        self.assertIn("const DEFAULT_IMAGE_BASE_URL = 'http://127.0.0.1:13000/v1';", self.source)
        self.assertIn("image_base_url: DEFAULT_IMAGE_BASE_URL", self.source)
    def test_server_image_endpoint_precedes_legacy_base_url(self):
        resolver = self.source[self.source.index("function resolveFrontendImageBase"):self.source.index("function openSettingsModal")]
        self.assertLess(resolver.index("serverConfig.image_base_url"), resolver.index("serverConfig.base_url"))
    def test_generate_uses_image_endpoint(self):
        self.assertIn("studioConfig.image_base_url || studioConfig.base_url || DEFAULT_IMAGE_BASE_URL", self.generate_block)
        self.assertNotIn("192.168.1.164:3000", self.generate_block)
    def test_no_old_endpoint_in_active_config_contract(self):
        active = re.search(r"const DEFAULT_IMAGE_BASE_URL.*?async function testConnection", self.source, re.S).group(0)
        self.assertNotIn("192.168.1.164:3000", active)


class StudioFrontendChatEndpointContractTest(unittest.TestCase):
    """第 19 轮：前端 chat_base_url 化石端口回归。

    第 8 轮把后端的 CHAT_BASE_DEFAULT 从 18045 修正为 13000，
    但 public/index.html 里 4 处 chat 地址漏网（默认配置、|| 回退、
    generate-brief 与 vision-inspect 请求体）。后端恒返回 chat_base_url，
    化石回退仅在字段为空时触发——平时不炸，边缘即坑。
    """

    @classmethod
    def setUpClass(cls):
        cls.source = INDEX.read_text(encoding="utf-8")

    def test_no_fossil_chat_port_in_frontend(self):
        self.assertNotIn("18045", self.source)

    def test_chat_default_matches_backend_chat_default(self):
        self.assertIn("chat_base_url: 'http://127.0.0.1:13000/v1'",
                      self.source)


if __name__ == "__main__": unittest.main()
