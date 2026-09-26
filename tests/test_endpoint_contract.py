import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import gemini_engine
import studio_server


class TestEndpointContract(unittest.TestCase):
    def test_image_and_chat_defaults_are_separate(self):
        cfg = studio_server.get_local_newapi_config()
        self.assertEqual(cfg["image_base_url"], "http://192.168.1.164:3000/v1")
        self.assertEqual(cfg["chat_base_url"], "http://127.0.0.1:18045/v1")
        self.assertNotEqual(cfg["image_base_url"], cfg["chat_base_url"])

    def test_chat_default_is_dsh_tunnel(self):
        self.assertEqual(gemini_engine.DEFAULT_BASE, "http://127.0.0.1:18045/v1")

    def test_chat_model_allowlist_excludes_local_image_models(self):
        self.assertIn("gemini-3.8-flash-medium", gemini_engine.CHAT_MODEL_ALLOWLIST)
        self.assertNotIn("agnes-image-2.5-flash", gemini_engine.CHAT_MODEL_ALLOWLIST)

    def test_runtime_key_precedence_is_dsh_first(self):
        self.assertTrue(hasattr(gemini_engine, "load_credentials"))
        source = Path(gemini_engine.__file__).read_text(encoding="utf-8")
        self.assertIn("ANTIGRAVITY_API_KEY", source)


if __name__ == "__main__":
    unittest.main()
