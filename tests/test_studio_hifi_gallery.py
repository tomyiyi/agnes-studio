import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "public" / "index.html"
EXPECTED = {
    "S05": "skill-poster",
    "S07": "skill-poster",
    "S09": "skill-poster",
    "S15": "skill-poster",
    "S02": "skill-poster",
    "S11": "skill-atmosphere",
    "N01": "skill-atmosphere",
    "S04": "skill-atmosphere",
}


class TestStudioHifiGallery(unittest.TestCase):
    def setUp(self):
        self.source = INDEX.read_text(encoding="utf-8")

    def test_all_hifi_assets_are_gallery_records(self):
        block = self.source.split("const SKILL71_GALLERY = [", 1)[1].split("\n    ];", 1)[0]
        for skill_id, category in EXPECTED.items():
            self.assertIn(f"id:'skill71_hifi_{skill_id}'", block)
            self.assertIn(f"category_id:'{category}'", block)
            self.assertIn(f"skill71_hifi_p0/", block)
        self.assertEqual(block.count("id:'skill71_hifi_"), 8)

    def test_gallery_categories_and_count_include_hifi_records(self):
        self.assertIn("id:'skill-poster',name:'Skill 视觉海报',count:5", self.source)
        self.assertIn("id:'skill-atmosphere',name:'Skill 氛围实验',count:3", self.source)
        self.assertIn("MASTER_CATEGORIES[0].count += SKILL71_GALLERY.length", self.source)

    def test_every_hifi_image_reference_exists_and_is_png(self):
        refs = re.findall(r"skill71_hifi_p0/[^'\"]+\.png", self.source)
        self.assertEqual(len(set(refs)), 8)
        for ref in set(refs):
            path = ROOT / "public" / "assets" / ref
            self.assertTrue(path.is_file(), ref)
            self.assertTrue(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), ref)


if __name__ == "__main__":
    unittest.main()
