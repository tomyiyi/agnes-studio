import tempfile
import time
import unittest
from pathlib import Path
from scripts.studio_server import list_rendered_posters

class RenderedPosterHistoryTests(unittest.TestCase):
    def test_only_custom_pngs_newest_first(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'poster_custom_old.png').write_bytes(b'old')
            time.sleep(0.02)
            (root / 'poster_custom_new.png').write_bytes(b'new')
            (root / 'ordinary.png').write_bytes(b'x')
            (root / 'poster_custom.json').write_text('{}')
            (root / 'poster_custom_dir.png').mkdir()
            self.assertEqual([x['name'] for x in list_rendered_posters(root)], ['poster_custom_new.png', 'poster_custom_old.png'])

    def test_limit_and_safe_paths(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(25):
                (root / f'poster_custom_{i}.png').write_bytes(b'x')
            items = list_rendered_posters(root)
            self.assertEqual(len(items), 20)
            for item in items:
                self.assertTrue(item['poster_url'].startswith('assets/'))
                self.assertNotIn(str(root), repr(item))

    def test_frontend_contract(self):
        source = Path('public/index.html').read_text()
        for token in ['/api/rendered-posters', 'loadRenderedPosterHistory', 'restoreRenderedPoster', "tabId === 'poster-studio'", 'latestRenderedPosterPath = posterPath']:
            self.assertIn(token, source)
