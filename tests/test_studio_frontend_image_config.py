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


class StudioFrontendPort3000FossilContractTest(unittest.TestCase):
    """第 23 轮：清除前端与后端预设中遗留的 3000 化石端口。

    在迁移至 13000 网关后，前端快速预设按钮、输入框 placeholder、
    生态看板与 testConnection 回退值中仍残留 127.0.0.1:3000，
    导致前端快速预设和探活默认指向无法连通的端口。
    """

    @classmethod
    def setUpClass(cls):
        cls.source = INDEX.read_text(encoding="utf-8")

    def test_no_fossil_port_3000_in_frontend(self):
        self.assertNotIn("127.0.0.1:3000", self.source)

    def test_apply_preset_uses_active_13000_port(self):
        self.assertIn("applyEndpointPreset('http://127.0.0.1:13000/v1')", self.source)

    def test_test_connection_fallback_uses_13000(self):
        self.assertIn("elBase.value.trim() : 'http://127.0.0.1:13000/v1'", self.source)

    def test_setting_base_url_placeholder_uses_13000(self):
        self.assertIn('placeholder="http://127.0.0.1:13000/v1"', self.source)

    def test_ecosystem_gateway_endpoint_uses_13000(self):
        self.assertIn('"id": "new_api_gateway"', self.source)
        self.assertIn('"endpoint": "http://127.0.0.1:13000"', self.source)


class StudioServerPresetEndpointsContractTest(unittest.TestCase):
    """验证后端预设端点已对齐活跃网关端口 13000，无 3000 化石残留。"""

    def test_preset_endpoints_no_fossil_port_3000(self):
        server_py = Path(__file__).parents[1] / "scripts" / "studio_server.py"
        source = server_py.read_text(encoding="utf-8")
        self.assertNotIn("127.0.0.1:3000", source)
        self.assertIn('"url": "http://127.0.0.1:13000/v1"', source)


if __name__ == "__main__": unittest.main()
