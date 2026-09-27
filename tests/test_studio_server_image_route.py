import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from studio_server import resolve_image_base_url


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

    def test_base_url_is_legacy_compatibility_fallback(self):
        cfg = {"detected": True, "base_url": "http://legacy.invalid/v1"}
        self.assertEqual(resolve_image_base_url({}, cfg), "http://legacy.invalid/v1")

    def test_undetected_config_uses_active_local_image_gateway(self):
        self.assertEqual(resolve_image_base_url({}, {"detected": False}), "http://127.0.0.1:13000/v1")


if __name__ == "__main__":
    unittest.main()
