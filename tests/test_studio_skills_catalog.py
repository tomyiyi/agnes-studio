import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import studio_server


class SkillsCatalogTests(unittest.TestCase):
    def test_loads_and_normalizes_repository_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'skills_71_index.json').write_text(json.dumps({
                'skills': [{'id': 'S01', 'display_name': '示例', 'group': '组', 'declared_skill_name': 'demo'}]
            }), encoding='utf-8')
            (root / 'skills.json').write_text(json.dumps({
                'categories': [{'name': '分类', 'skill_count': 1, 'desc': '说明', 'templates': []}]
            }), encoding='utf-8')
            with patch.object(studio_server, 'SKILLS_71_PATH', root / 'skills_71_index.json'), patch.object(studio_server, 'SKILLS_DATA_PATH', root / 'skills.json'):
                result = studio_server.load_skills_catalog()
        self.assertTrue(result['success'])
        self.assertEqual(len(result['skills71']), 1)
        self.assertEqual(result['skills71'][0]['call'], 'demo')
        self.assertEqual(result['categories'][0]['name'], '分类')
        self.assertNotIn('path', result['skills71'][0])
        self.assertNotIn('install_root', result)

    def test_frontend_loads_catalog_before_rendering(self):
        source = Path('public/index.html').read_text()
        for token in ['let SKILLS71 = [];', 'let SKILLS_DATA = [];', 'loadSkillsCatalog', "'/api/skills-catalog'", 'loadSkillsCatalog().catch']:
            self.assertIn(token, source)
        self.assertNotIn('      renderSkills();\n      renderEcosystem();', source)

    def test_server_sources_are_explicit(self):
        source = Path('scripts/studio_server.py').read_text()
        self.assertIn('SKILLS_71_PATH = DIR / "data" / "skills_71_index.json"', source)
        self.assertIn('SKILLS_DATA_PATH = DIR / "data" / "skills.json"', source)
        self.assertIn('parsed_path == "/api/skills-catalog"', source)


if __name__ == '__main__':
    unittest.main()
