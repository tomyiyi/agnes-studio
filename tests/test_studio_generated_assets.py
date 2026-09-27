import tempfile
import time
import unittest
from pathlib import Path

from scripts.studio_server import list_generated_images


class StudioGeneratedAssetsTest(unittest.TestCase):
    def test_only_images_newest_first_and_safe_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = root / 'old.png'
            new = root / 'new.webp'
            old.write_bytes(b'old')
            time.sleep(0.01)
            new.write_bytes(b'new')
            (root / 'ignored.json').write_text('{}')
            (root / 'nested').mkdir()

            items = list_generated_images(root)

        self.assertEqual([item['name'] for item in items], ['new.webp', 'old.png'])
        self.assertEqual([item['file_path'] for item in items], ['assets/generated/new.webp', 'assets/generated/old.png'])
        self.assertTrue(all(td not in str(item) for item in items))

    def test_limit_is_24(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(30):
                (root / f'{i}.png').write_bytes(b'x')
                time.sleep(0.001)
            self.assertEqual(len(list_generated_images(root)), 24)

    def test_missing_directory_is_empty(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(list_generated_images(Path(td) / 'missing'), [])

    def test_frontend_contract(self):
        source = (Path(__file__).parents[1] / 'public' / 'index.html').read_text(encoding='utf-8')
        self.assertIn("/api/generated-images", source)
        self.assertIn('loadGeneratedBackgrounds', source)
        self.assertIn('upsertGeneratedBackgroundOption', source)
        self.assertIn('loadGeneratedBackgrounds();', source)


if __name__ == '__main__':
    unittest.main()
