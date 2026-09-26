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
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import env_config  # noqa: F401
from PIL import Image

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
from cover_style import resolve_style, load_catalog, CoverStyle
from cover_pipeline import (
    validate_copy,
    build_filename,
    resolve_text_box,
    compose_html,
    PLATFORMS,
    export_pair,
    render_wechat_list_sim,
    build_contact_sheet,
    qa_thumbnail_ok,
)
import wechat_cover_ab
from expert_poster_designer import analyze_safe_zone
from vision_subject_detector import detect_faces, check_occlusion


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
        font_keys = ["smiley", "wenkai", "songti", "pingfang", "serif", "sans", "lxgwwenkai", "didot", "hei", "futura", "kai"]
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

    def test_venv_site_packages_registered(self):
        venv_dir = PROJECT_ROOT / ".venv"
        if venv_dir.exists():
            site_packages = list(venv_dir.glob("lib/python*/site-packages"))
            if site_packages:
                for sp in site_packages:
                    self.assertIn(str(sp), sys.path)


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


class TestCoverStyleResolver(unittest.TestCase):
    """测试封面需求简报至样式推导引擎 (CoverStyle & StyleCatalog)"""

    def setUp(self):
        self.catalog = load_catalog()

    def test_default_resolution(self):
        st = resolve_style({})
        self.assertIsInstance(st, CoverStyle)
        self.assertEqual(st.mode, "diag")
        self.assertEqual(st.hero_size, 148)
        self.assertEqual(st.sub_size, 22)
        self.assertEqual(st.title_zone_default, "safe")
        self.assertTrue(len(st.gen_prompt) > 0)
        self.assertIn("ultra sharp", st.gen_prompt)

    def test_platform_tuning_and_type_scales(self):
        st_wechat = resolve_style({"platform": "wechat", "tone": "luxury"})
        self.assertEqual(st_wechat.hero_size, 148)
        self.assertEqual(st_wechat.sub_size, 22)

        st_xhs = resolve_style({"platform": "xhs", "tone": "minimal"})
        # xhs base: hero=110, sub=16; minimal scale=0.92
        self.assertEqual(st_xhs.hero_size, int(110 * 0.92))
        self.assertEqual(st_xhs.sub_size, int(16 * 0.92))

        st_wechat_sq = resolve_style({"platform": "wechat-sq", "tone": "epic"})
        # wechat-sq base: hero=92, sub=14; epic scale=1.08
        self.assertEqual(st_wechat_sq.hero_size, int(92 * 1.08))
        self.assertEqual(st_wechat_sq.sub_size, int(14 * 1.08))

    def test_goal_mode_mapping(self):
        self.assertEqual(resolve_style({"goal": "ctr"}).mode, "bignews")
        self.assertEqual(resolve_style({"goal": "editorial"}).mode, "diag")
        self.assertEqual(resolve_style({"goal": "story"}).mode, "stack")
        self.assertEqual(resolve_style({"goal": "vertical"}).mode, "vertical")

    def test_subject_serif_override(self):
        st_scenery = resolve_style({"subject": "scenery", "tone": "luxury"})
        self.assertEqual(st_scenery.font_css, self.catalog["font_stacks"]["serif_east"])

        st_product = resolve_style({"subject": "product", "tone": "luxury"})
        self.assertEqual(st_product.font_css, self.catalog["font_stacks"]["serif_east"])

        st_cyber_product = resolve_style({"subject": "product", "tone": "cyber"})
        self.assertNotEqual(st_cyber_product.font_css, self.catalog["font_stacks"]["serif_east"])

    def test_skill_style_injection_and_fallback(self):
        st_s05 = resolve_style({"style_skill": "S05"})
        self.assertEqual(st_s05.style_skill, "S05")
        self.assertTrue(len(st_s05.skill_call_name) > 0)
        self.assertIn("S05", st_s05.notes)

        # 未知或非法 skill 不抛出异常，优雅降级
        st_unknown = resolve_style({"style_skill": "NON_EXISTENT_SKILL_XYZ"})
        self.assertEqual(st_unknown.style_skill, "")

    def test_cover_style_to_dict_and_serialization(self):
        st = resolve_style({"goal": "editorial", "platform": "xhs", "tone": "warm"})
        d = st.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("hero_size", d)
        self.assertIn("sub_size", d)
        self.assertIn("palette", d)
        self.assertIn("gen_prompt", d)
        serialized = json.dumps(d, ensure_ascii=False)
        self.assertTrue(len(serialized) > 0)


class TestSafeZoneAnalyzer(unittest.TestCase):
    """测试多模态空间方差与负空间避障探测器"""

    def test_analyze_safe_zone_sample(self):
        sample_img = ASSETS_DIR / "agnes_1790006749_b2b755da.png"
        self.assertTrue(sample_img.exists(), "样本图片缺失")
        res = analyze_safe_zone(str(sample_img))
        self.assertIsInstance(res, dict)
        self.assertEqual(res["width"], 1024)
        self.assertEqual(res["height"], 1024)
        self.assertIn("best_grid", res)
        self.assertIn("min_variance", res)
        self.assertIsInstance(res["bg_rgb"], tuple)
        self.assertEqual(len(res["bg_rgb"]), 3)
        self.assertGreater(res["safe_x"], 0)
        self.assertGreater(res["safe_y"], 0)


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


class TestCoverPipeline(unittest.TestCase):
    """测试封面流水线文案门禁、动态命名、防遮挡与 HTML 渲染安全规范"""

    def test_validate_copy_length_and_forbid_chars(self):
        # 1. 正常文案通过
        errs = validate_copy("东方", "神颜", "ORIENTAL BEAUTY", "她以骨相写诗，以眉眼成章")
        self.assertEqual(errs, [])

        # 2. title_a / title_b 长度超限
        errs_short = validate_copy("东", "神颜", "ORIENTAL BEAUTY", "短标题测试")
        self.assertTrue(any("title_a" in e for e in errs_short))

        errs_long = validate_copy("超级长的大标题", "神颜", "ORIENTAL BEAUTY", "长标题测试")
        self.assertTrue(any("title_a" in e for e in errs_long))

        errs_tb_long = validate_copy("东方", "超级长副标", "ORIENTAL BEAUTY", "长副标测试")
        self.assertTrue(any("title_b" in e for e in errs_tb_long))

        # 3. slogan 超限 (>18 字)
        errs_slogan = validate_copy("东方", "神颜", "BEAUTY", "这是一段非常非常长的毫无节制的超过十八个字的长标语句子测试")
        self.assertTrue(any("slogan" in e for e in errs_slogan))

        # 4. 禁则弯引号
        errs_quote = validate_copy("“东方", "神颜”", "BEAUTY", "‘高级感’")
        self.assertTrue(any("禁则字符" in e for e in errs_quote))

        # 5. 盘古之白空格缺失
        errs_pangu = validate_copy("东方", "神颜", "BEAUTY", "体验Agnes模型发布")
        self.assertTrue(any("盘古之白" in e for e in errs_pangu))

        # 6. latin 过长 (>28 字符)
        errs_latin = validate_copy("东方", "神颜", "VERY LONG LATIN SUBTITLE THAT EXCEEDS LIMIT", "测试标语")
        self.assertTrue(any("latin 过长" in e for e in errs_latin))

    def test_build_filename_and_platforms(self):
        date_today = __import__("datetime").date.today().strftime("%Y%m%d")
        expected_codes = {
            "wechat": ("wx_head", 2350, 1000),
            "wechat-sq": ("wx_sub", 1080, 1080),
            "xhs": ("xhs_main", 1080, 1440),
            "xhs-sq": ("xhs_sq", 1080, 1080),
        }
        for plat, (code, w, h) in expected_codes.items():
            with self.subTest(platform=plat):
                fn = build_filename(plat, "diag", "sample-slug", "png")
                self.assertEqual(fn, f"{code}_diag_{w}x{h}_{date_today}_sample-slug.png")

        # 针对以点开头的扩展名
        fn_dot = build_filename("wechat", "diag", "sample-slug", ".png")
        self.assertNotIn("..png", fn_dot)
        self.assertTrue(fn_dot.endswith(".png"))

        # 不支持的平台抛出 ValueError
        with self.assertRaises(ValueError):
            build_filename("unknown_platform_xyz", "diag", "sample-slug")

    def test_resolve_text_box(self):
        # 1. 无人脸时成功回退兜底候选框
        res_noface = resolve_text_box([], "wechat", "safe", "diag")
        self.assertTrue(res_noface["ok"])
        self.assertIsNotNone(res_noface["chosen"])
        self.assertIn("left:", res_noface["block_css"])
        self.assertEqual(res_noface["note"], "no-face-fallback")

        # 2. 有人脸且未完全覆盖时成功避让人脸
        faces = [{"x_min": 0.50, "y_min": 0.10, "x_max": 0.70, "y_max": 0.40}]
        res_face = resolve_text_box(faces, "wechat", "safe", "diag")
        self.assertTrue(res_face["ok"])
        self.assertEqual(res_face["note"], "clear")
        x1, y1, x2, y2 = res_face["chosen"]
        # 避让逻辑应保证文本框与人脸不重叠
        has_overlap = not (x2 < 0.47 or x1 > 0.73 or y2 < 0.05 or y1 > 0.43)
        self.assertFalse(has_overlap)

        # 3. 极度遮挡：人脸覆盖整个画面导致所有候选框均被命中
        giant_face = [{"x_min": 0.0, "y_min": 0.0, "x_max": 1.0, "y_max": 1.0}]
        res_blocked = resolve_text_box(giant_face, "wechat", "safe", "diag")
        self.assertFalse(res_blocked["ok"])
        self.assertIsNone(res_blocked["chosen"])
        self.assertEqual(res_blocked["note"], "all-boxes-hit-face")

    def test_compose_html_escaping_and_sanitization(self):
        html_xss = compose_html(
            "wechat",
            "data:image/png;base64,sample');}</style><script>alert('xss')</script>",
            title_a="<script>alert(1)</script>",
            title_b="大片",
            title_accent="片",
            latin="ORIENTAL BEAUTY & LUXURY",
            slogan="<style>body{display:none}</style>",
            mode="diag",
        )
        self.assertNotIn("<script>alert(1)</script>", html_xss)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html_xss)
        self.assertNotIn("<style>body{display:none}</style>", html_xss)
        self.assertIn("&lt;style&gt;body{display:none}&lt;/style&gt;", html_xss)
        self.assertNotIn("<script>alert('xss')</script>", html_xss)
        self.assertIn("%3Cscript%3E", html_xss)
        self.assertIn("<em>片</em>", html_xss)

    def test_export_pair_and_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            png_file = tmp_path / "test_cover.png"
            Image.new("RGB", (200, 100), color=(20, 30, 40)).save(png_file, "PNG")

            # 1. 传 Path 对象调用
            res_path = export_pair(png_file)
            self.assertEqual(res_path["png"], str(png_file))
            self.assertTrue(Path(res_path["jpg"]).exists())
            self.assertEqual(res_path["jpg"], str(tmp_path / "test_cover.jpg"))
            self.assertIn("png_kb", res_path)
            self.assertIn("jpg_kb", res_path)

            # 2. 传 str 字符串路径调用
            res_str = export_pair(str(png_file))
            self.assertEqual(res_str["png"], str(png_file))
            self.assertEqual(res_str["jpg"], str(tmp_path / "test_cover.jpg"))

            # 3. 不存在文件抛出 FileNotFoundError
            with self.assertRaises(FileNotFoundError):
                export_pair(tmp_path / "non_existent.png")

    def test_render_wechat_list_sim(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            src_png = tmp_path / "wx_head.png"
            Image.new("RGB", (400, 200), color=(100, 120, 150)).save(src_png, "PNG")
            out_sim = tmp_path / "sim" / "wx_sim.jpg"

            # 1. 正常模拟微信遮挡带输出
            ret = render_wechat_list_sim(src_png, out_sim)
            self.assertEqual(ret, out_sim)
            self.assertTrue(out_sim.exists())
            with Image.open(out_sim) as sim_im:
                self.assertEqual(sim_im.size, (400, 200))

            # 2. 字符串入参兼容
            out_sim_str = tmp_path / "sim" / "wx_sim_2.jpg"
            render_wechat_list_sim(str(src_png), str(out_sim_str))
            self.assertTrue(out_sim_str.exists())

            # 3. 源文件不存在抛出 FileNotFoundError
            with self.assertRaises(FileNotFoundError):
                render_wechat_list_sim(tmp_path / "not_found.png", out_sim)

    def test_build_contact_sheet_and_edge_cases(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            img1 = tmp_path / "img1.png"
            img2 = tmp_path / "img2.png"
            Image.new("RGB", (200, 300), color=(255, 0, 0)).save(img1, "PNG")
            Image.new("RGB", (200, 300), color=(0, 255, 0)).save(img2, "PNG")
            out_sheet = tmp_path / "contact_sheet.jpg"

            # 1. 混合 Path 与 str 列表生成接触印相图
            build_contact_sheet([img1, str(img2)], out_sheet)
            self.assertTrue(out_sheet.exists())
            with Image.open(out_sheet) as sheet_im:
                self.assertEqual(sheet_im.height, 420 + 24)
                self.assertGreater(sheet_im.width, 200)

            # 2. 空列表边界防护：抛出 ValueError
            with self.assertRaises(ValueError):
                build_contact_sheet([], tmp_path / "empty.jpg")

            # 3. 包含不存在文件抛出 FileNotFoundError
            with self.assertRaises(FileNotFoundError):
                build_contact_sheet([img1, tmp_path / "missing.png"], tmp_path / "sheet.jpg")

    def test_qa_thumbnail_ok(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # 1. 纯色背景无对比度：pstdev 接近 0，不达标
            plain_img = tmp_path / "plain.png"
            Image.new("RGB", (400, 400), color=(128, 128, 128)).save(plain_img, "PNG")
            self.assertFalse(qa_thumbnail_ok(plain_img))

            # 2. 高对比黑白图：方差显著，达标
            high_contrast = tmp_path / "high_contrast.png"
            hc_im = Image.new("RGB", (400, 400), color=(0, 0, 0))
            for x in range(10, 200):
                for y in range(10, 200):
                    hc_im.putpixel((x, y), (255, 255, 255))
            hc_im.save(high_contrast, "PNG")
            self.assertTrue(qa_thumbnail_ok(str(high_contrast)))

            # 3. 不存在文件抛出 FileNotFoundError
            with self.assertRaises(FileNotFoundError):
                qa_thumbnail_ok(tmp_path / "not_found.png")

    def test_wechat_cover_ab_env_resolution(self):
        # 验证 wechat_cover_ab 已对齐 cross-platform 环境，杜绝 hardcoded macOS 路径
        self.assertEqual(wechat_cover_ab.CHROME, resolve_chrome_path())
        self.assertEqual(wechat_cover_ab.FONTS, FONTS_DIR)
        self.assertEqual(wechat_cover_ab.ASSETS, ASSETS_DIR)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            dummy_src = tmp_path / "dummy_bg.png"
            dummy_dst = tmp_path / "dummy_crop.png"
            Image.new("RGB", (1000, 1000), color=(50, 50, 50)).save(dummy_src, "PNG")
            wechat_cover_ab.make_subject_crop(str(dummy_src), str(dummy_dst))
            self.assertTrue(dummy_dst.exists())
            with Image.open(dummy_dst) as im:
                self.assertEqual(im.size[0], 1000)
                self.assertEqual(im.size[1], int(round(1000 / 2.35)))


class TestVisionSubjectDetector(unittest.TestCase):
    """测试多模态视觉主体检测与文字避障碰撞检测"""

    def setUp(self):
        self.sample_zone = {
            "x_min": 0.40,
            "x_max": 0.60,
            "y_min": 0.40,
            "y_max": 0.60,
        }

    def test_check_occlusion_positive_hit(self):
        # 明显与主体区域重叠
        text_box = (0.35, 0.38, 0.55, 0.55)
        hit, zone = check_occlusion(text_box, [self.sample_zone])
        self.assertTrue(hit)
        self.assertEqual(zone, self.sample_zone)

    def test_check_occlusion_clear_separation(self):
        # 位于左上角完全无重叠区域
        text_box = (0.05, 0.05, 0.25, 0.25)
        hit, zone = check_occlusion(text_box, [self.sample_zone])
        self.assertFalse(hit)
        self.assertIsNone(zone)

    def test_check_occlusion_margin_buffer(self):
        # 保护区自带发饰/眼神缓冲区 (y_min 外扩 0.05，两侧外扩 0.03)
        # y_min=0.40，外扩后为 0.35；文字框底部处于 0.37 时未进入主体本身但进入缓冲保护区
        buffered_box = (0.42, 0.20, 0.58, 0.37)
        hit, zone = check_occlusion(buffered_box, [self.sample_zone])
        self.assertTrue(hit, "应该命中头部上方 5% 发饰眼神呼吸缓冲区")
        self.assertEqual(zone, self.sample_zone)

    def test_check_occlusion_robustness(self):
        # 空值、格式非法及类型防御
        self.assertEqual(check_occlusion(None, [self.sample_zone]), (False, None))
        self.assertEqual(check_occlusion((0.1, 0.1), [self.sample_zone]), (False, None))
        self.assertEqual(check_occlusion((0.1, 0.1, 0.5, 0.5), None), (False, None))
        self.assertEqual(check_occlusion((0.1, 0.1, 0.5, 0.5), []), (False, None))
        self.assertEqual(check_occlusion((0.1, 0.1, 0.5, 0.5), ["not_a_dict"]), (False, None))
        self.assertEqual(check_occlusion((0.1, 0.1, 0.5, 0.5), [{"bad_key": 1}]), (False, None))
        # 字符串数字坐标兼容
        hit, zone = check_occlusion(("0.35", "0.38", "0.55", "0.55"), [self.sample_zone])
        self.assertTrue(hit)
        self.assertEqual(zone, self.sample_zone)

    def test_detect_faces_input_guards(self):
        # 非法或不存在输入安全返回空列表
        self.assertEqual(detect_faces(None), [])
        self.assertEqual(detect_faces(""), [])
        self.assertEqual(detect_faces("non_existent_file_path.png"), [])

    def test_detect_faces_fallback_flow(self):
        # 验证 Linux / 无 swift 环境下的回退机制
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_img = Path(tmpdir) / "face_test.png"
            Image.new("RGB", (200, 200), color=(100, 100, 100)).save(tmp_img, "PNG")

            mock_boxes = [{"x_min": 0.2, "x_max": 0.8, "y_min": 0.1, "y_max": 0.7}]
            with patch("shutil.which", return_value=None), \
                 patch("gemini_engine.detect_visual_subjects_gemini", return_value=mock_boxes):
                detected = detect_faces(str(tmp_img))
                self.assertEqual(detected, mock_boxes)


if __name__ == "__main__":
    unittest.main()
