#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio - Core Engine & Typography & Data Integrity Test Suite
===================================================================
Automated regression tests covering:
1. Chinese copywriting rules (sparanoid / pangu guidelines)
2. Professional Chinese typography & punctuation normalization
3. Modular Scale hierarchy & geometric progression
4. Swiss international grid system & layout zones
5. Environment configuration & cross-platform path resolution
6. Data integrity & JSON syntax across all configuration files
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from copywriting_rules import apply_fix, lint_copy, apply_pangu_spacing, normalize_punctuation
from typography_rules import (
    ChineseTypographyRules,
    ModularScale,
    SwissGridSystem,
    SmartPosterComposer,
    PosterTypeSystem,
)
from env_config import (
    PROJECT_ROOT,
    PUBLIC_DIR,
    ASSETS_DIR,
    FONTS_DIR,
    DATA_DIR,
    resolve_chrome_path,
    resolve_font_path,
)


class TestCopywritingRules(unittest.TestCase):
    """测试中文文案排版规范及盘古之白"""

    def test_pangu_spacing(self):
        self.assertEqual(apply_pangu_spacing("Agnes模型发布"), "Agnes 模型发布")
        self.assertEqual(apply_pangu_spacing("模型发布2.5版本"), "模型发布 2.5 版本")
        self.assertEqual(apply_pangu_spacing("模型震撼发布99%超越"), "模型震撼发布 99% 超越")
        self.assertEqual(apply_pangu_spacing(""), "")

    def test_normalize_punctuation(self):
        text = '“东方美学”：高级感'
        normalized = normalize_punctuation(text)
        self.assertIn("「东方美学」", normalized)
        self.assertNotIn("“", normalized)
        self.assertNotIn("”", normalized)

    def test_apply_fix_and_lint(self):
        raw = '东方BEAUTY的“高级感”来自10:1字阶'
        fixed = apply_fix(raw)
        self.assertIn("东方 BEAUTY", fixed)
        self.assertIn("「高级感」", fixed)
        issues = lint_copy(fixed)
        self.assertEqual(issues, [])


class TestChineseTypographyRules(unittest.TestCase):
    """测试海报级中文排印与标点挤压规则"""

    def test_apply_pangu_spacing(self):
        raw = "Agnes 2.5模型震撼发布，首创\"混元矢量\"排版！"
        formatted = ChineseTypographyRules.format_poster_copy(raw)
        self.assertIn("Agnes 2.5 模型", formatted)
        self.assertIn("「混元矢量」", formatted)

    def test_normalize_quotes_and_brackets(self):
        text = '电影“一代宗师”经典台词：‘念念不忘’'
        result = ChineseTypographyRules.normalize_quotes_and_brackets(text)
        self.assertIn("「一代宗师」", result)
        self.assertIn("『念念不忘』", result)

    def test_squeeze_punctuation(self):
        text = "天地有大美， 」静水流深"
        squeezed = ChineseTypographyRules.squeeze_punctuation(text)
        self.assertEqual(squeezed, "天地有大美，」静水流深")


class TestModularScale(unittest.TestCase):
    """测试模块化字阶系统"""

    def test_scale_monotonicity_golden(self):
        ms = ModularScale(16.0, "golden")
        h = ms.get_poster_hierarchy()
        self.assertGreaterEqual(h["mega"], h["h1"])
        self.assertGreaterEqual(h["h1"], h["h2"])
        self.assertGreaterEqual(h["h2"], h["h3"])
        self.assertGreaterEqual(h["h3"], h["body"])
        self.assertGreaterEqual(h["body"], h["tag"])
        self.assertGreaterEqual(h["tag"], h["micro"])
        self.assertGreaterEqual(h["micro"], 9)

    def test_scale_monotonicity_balanced(self):
        ms = ModularScale(16.0, "perfect_fourth")
        h = ms.get_poster_hierarchy()
        self.assertGreaterEqual(h["mega"], h["h1"])
        self.assertGreaterEqual(h["h1"], h["h2"])
        self.assertGreaterEqual(h["h2"], h["h3"])
        self.assertGreaterEqual(h["h3"], h["body"])
        self.assertGreaterEqual(h["body"], h["tag"])
        self.assertGreaterEqual(h["tag"], h["micro"])
        self.assertGreaterEqual(h["micro"], 9)


class TestSwissGridSystem(unittest.TestCase):
    """测试瑞士 12 栏网格与基线计算"""

    def setUp(self):
        self.canvas_w = 1200
        self.canvas_h = 1600
        self.grid = SwissGridSystem(self.canvas_w, self.canvas_h, columns=12)

    def test_grid_boundaries(self):
        x, w = self.grid.get_column_rect(0, 4)
        self.assertGreaterEqual(x, self.grid.margin_x)
        self.assertLessEqual(x + w, self.canvas_w - self.grid.margin_x)

        x_end, w_end = self.grid.get_column_rect(8, 4)
        self.assertGreater(x_end, x)
        self.assertLessEqual(x_end + w_end, self.canvas_w)

    def test_baseline_snapping(self):
        y = 123
        snapped = self.grid.snap_to_baseline(y)
        self.assertEqual(snapped % self.grid.baseline_unit, 0)

    def test_layout_zones(self):
        zones = self.grid.get_layout_zones()
        expected_zones = ["top_banner", "left_col", "right_col", "center_corridor", "bottom_credits"]
        for zone in expected_zones:
            self.assertIn(zone, zones)
            x, y, w, h = zones[zone]
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertGreater(w, 0)
            self.assertGreater(h, 0)
            self.assertLessEqual(x + w, self.canvas_w)
            self.assertLessEqual(y + h, self.canvas_h)


class TestEnvConfig(unittest.TestCase):
    """测试跨平台路径与环境探测"""

    def test_directories_exist(self):
        self.assertTrue(PROJECT_ROOT.exists(), f"PROJECT_ROOT missing: {PROJECT_ROOT}")
        self.assertTrue(PUBLIC_DIR.exists(), f"PUBLIC_DIR missing: {PUBLIC_DIR}")
        self.assertTrue(ASSETS_DIR.exists(), f"ASSETS_DIR missing: {ASSETS_DIR}")
        self.assertTrue(FONTS_DIR.exists(), f"FONTS_DIR missing: {FONTS_DIR}")
        self.assertTrue(DATA_DIR.exists(), f"DATA_DIR missing: {DATA_DIR}")

    def test_chrome_resolution(self):
        chrome_path = resolve_chrome_path()
        self.assertIsInstance(chrome_path, str)
        self.assertTrue(len(chrome_path) > 0)

    def test_font_resolution(self):
        font_keys = ["smiley", "wenkai", "songti", "pingfang", "serif", "sans"]
        for key in font_keys:
            with self.subTest(font_key=key):
                font_path = resolve_font_path(key)
                self.assertIsInstance(font_path, str)
                self.assertTrue(len(font_path) > 0, f"未能为 {key} 解析字体路径")
                self.assertTrue(Path(font_path).exists(), f"解析出的字体路径不存在: {font_path}")

    def test_font_resolution_fallback(self):
        fallback_path = resolve_font_path("non_existent_random_font_xyz")
        self.assertIsInstance(fallback_path, str)
        self.assertTrue(len(fallback_path) > 0)
        self.assertTrue(Path(fallback_path).exists(), f"兜底字体路径不存在: {fallback_path}")


class TestSmartPosterComposer(unittest.TestCase):
    """测试智能避障与对角拆字海报排版推导器"""

    def test_plan_layout_collision_avoidance_split(self):
        face_zone = [{"x_min": 0.45, "y_min": 0.08, "x_max": 0.55, "y_max": 0.22, "type": "face"}]
        plan = SmartPosterComposer.plan_layout(
            image_w=1200,
            image_h=1600,
            exclusion_zones=face_zone,
            title="苏园惊鸿",
            subtitle="园林清韵",
            en_title="Suzhou Classic"
        )
        self.assertEqual(plan["layout_style"], "bilateral_split_vertical")
        roles = {el["role"]: el for el in plan["elements"]}
        self.assertIn("title_part_1", roles)
        self.assertIn("title_part_2", roles)
        self.assertIn("en_subtitle", roles)
        self.assertIn("footer_metadata", roles)

        part1 = roles["title_part_1"]
        part2 = roles["title_part_2"]
        self.assertEqual(part1["orientation"], "vertical")
        self.assertEqual(part2["orientation"], "vertical")
        self.assertGreater(part2["y"], part1["y"])
        self.assertEqual(part1["font_size"], plan["hierarchy_sizes"]["h1"])

    def test_plan_layout_horizontal_magazine(self):
        plan = SmartPosterComposer.plan_layout(
            image_w=1200,
            image_h=1600,
            exclusion_zones=[],
            title="铜钟与蒸汽城",
            subtitle="蒸汽纪元",
            en_title="Steam & Chime"
        )
        self.assertEqual(plan["layout_style"], "top_horizontal_magazine")
        roles = {el["role"]: el for el in plan["elements"]}
        self.assertIn("title", roles)
        self.assertIn("en_subtitle", roles)
        self.assertIn("footer_metadata", roles)
        self.assertEqual(roles["title"]["orientation"], "horizontal")


class TestPosterTypeSystem(unittest.TestCase):
    """测试海报字排规格与主题呈现规范"""

    def setUp(self):
        self.pts = PosterTypeSystem()

    def test_sizes_scaling(self):
        sizes_base = self.pts.sizes(canvas_w=1080)
        self.assertIn("T1", sizes_base)
        self.assertIn("T2", sizes_base)
        self.assertIn("T3", sizes_base)
        self.assertIn("T4", sizes_base)
        self.assertGreater(sizes_base["T1"]["size"], sizes_base["T2"]["size"])
        self.assertGreater(sizes_base["T2"]["size"], sizes_base["T3"]["size"])
        self.assertGreater(sizes_base["T3"]["size"], sizes_base["T4"]["size"])

        sizes_2x = self.pts.sizes(canvas_w=2160)
        self.assertEqual(sizes_2x["T1"]["size"], sizes_base["T1"]["size"] * 2)

    def test_theme_mode_mapping(self):
        self.assertEqual(self.pts.theme_mode("ctr"), "压图巨字")
        self.assertEqual(self.pts.theme_mode("editorial"), "负空间一角")
        self.assertEqual(self.pts.theme_mode("brand"), "中轴竖排或负空间一角")
        self.assertEqual(self.pts.theme_mode("story"), "对角拆字")
        self.assertEqual(self.pts.theme_mode("vertical"), "中轴竖排")
        self.assertEqual(self.pts.theme_mode("unknown_mode"), "负空间一角")

    def test_validate_copy_pair(self):
        valid_issues = self.pts.validate_copy_pair(
            title="山河盛宴",
            latin="FESTIVAL OF MOUNTAINS",
            slogan="千里江山一日还"
        )
        self.assertEqual(valid_issues, [])

        long_title_issues = self.pts.validate_copy_pair(
            title="超级长的大气海报主标题完全超出限制",
            latin="VALID LATIN",
            slogan="合规短标语"
        )
        self.assertTrue(any("主标过长" in msg for msg in long_title_issues))

        lowercase_latin_issues = self.pts.validate_copy_pair(
            title="山河盛宴",
            latin="Festival of mountains",
            slogan="千里江山一日还"
        )
        self.assertTrue(any("全大写" in msg for msg in lowercase_latin_issues))

        long_slogan_issues = self.pts.validate_copy_pair(
            title="山河盛宴",
            latin="FESTIVAL",
            slogan="这是一个超级长毫无节制完全不适合海报金句排版的超长超长标语金句文本"
        )
        self.assertTrue(any("slogan >18 字" in msg for msg in long_slogan_issues))


class TestDataIntegrity(unittest.TestCase):
    """测试 data 目录下所有 JSON 语法与数据完整性"""

    def test_json_data_validity(self):
        json_files = list(DATA_DIR.glob("**/*.json"))
        self.assertGreater(len(json_files), 10, "data 目录缺少预期的 JSON 数据文件")
        for path in json_files:
            with self.subTest(file=path.name):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.assertTrue(isinstance(data, (dict, list)), f"{path.name} 结构不是字典或列表")

    def test_core_rule_files_exist(self):
        core_files = [
            "learned_poster_rules.json",
            "style_catalog.json",
            "poster_grand_rules.json",
            "poster_layout_system.json",
            "copy_templates.json",
        ]
        for name in core_files:
            target = DATA_DIR / name
            self.assertTrue(target.exists(), f"核心配置缺失: {name}")


if __name__ == "__main__":
    unittest.main()
