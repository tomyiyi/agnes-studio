import re
import unittest
from pathlib import Path


class HifiAssetTests(unittest.TestCase):
    def test_all_p0_assets_referenced_by_ui_exist(self):
        html = Path('public/index.html').read_text(encoding='utf-8')
        refs = sorted(set(re.findall(r'assets/skill71_hifi_p0/[^\"\']+\.png', html)))
        self.assertEqual(len(refs), 8)
        for ref in refs:
            path = Path('public') / ref
            self.assertTrue(path.is_file(), ref)

    def test_all_p0_assets_are_nontrivial_pngs(self):
        root = Path('public/assets/skill71_hifi_p0')
        files = sorted(root.glob('*.png'))
        self.assertEqual(len(files), 8)
        for path in files:
            self.assertEqual(path.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')
            self.assertGreater(path.stat().st_size, 20_000, path.name)


if __name__ == '__main__':
    unittest.main()
