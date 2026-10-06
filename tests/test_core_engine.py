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

import argparse
import datetime
import io
import json
import sys
import tempfile
import unittest
import urllib.error
import tarfile
import zipfile
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "experiments"))
import env_config  # noqa: F401
from PIL import Image

from copywriting_rules import (
    apply_fix,
    lint_copy,
    apply_pangu_spacing,
    normalize_punctuation,
    main as copy_rules_main,
    build_arg_parser as build_copy_rules_parser,
)
from typography_rules import (
    ChineseTypographyRules,
    ModularScale,
    SwissGridSystem,
    SmartPosterComposer,
    PosterTypeSystem,
    build_arg_parser as build_typography_parser,
    main as typography_main,
    parse_exclusion_zones,
    plan_to_serializable,
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
from cover_style import (
    resolve_style,
    load_catalog,
    CoverStyle,
    list_catalog_options,
    list_skill_styles,
    main as cover_style_main,
    build_arg_parser as build_cover_style_parser,
)
import cover_pipeline
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
    classify_generation_error as cover_classify_error,
    classify_pipeline_error as cover_pipeline_classify_error,
    generate_cover_subject,
    preflight_source_asset,
    preflight_source_assets,
    resolve_source_asset_for_platform,
    resolve_required_source_assets,
    run_brief_batch,
    run_platform,
)
import check_upstream_updates
from check_upstream_updates import (
    get_local_auth_key,
    get_local_base_url,
    check_new_api_health,
    check_github_repo,
    run_lifecycle_monitor,
    main as monitor_main,
    build_arg_parser as sentinel_build_arg_parser,
)
import wechat_cover_ab
import agnes_gateway
from agnes_gateway import load_gateway, generate, save_image, classify_generation_error as gateway_classify_error
from expert_poster_designer import (
    analyze_safe_zone,
    render_expert_steampunk_poster,
    render_expert_neochinese_poster,
    main as expert_designer_main,
    build_arg_parser as expert_designer_build_arg_parser,
    list_expert_modes as expert_designer_list_modes,
    EXPERT_MODES as EXPERT_DESIGNER_MODES,
)
from poster_composer import (
    compose_commercial_poster,
    main as poster_composer_main,
    build_arg_parser as poster_composer_build_arg_parser,
    list_font_styles as poster_composer_list_font_styles,
    list_theme_colors as poster_composer_list_theme_colors,
    FONT_STYLES as POSTER_COMPOSER_FONT_STYLES,
    THEME_COLORS as POSTER_COMPOSER_THEME_COLORS,
)
from vision_subject_detector import (
    detect_faces,
    check_occlusion,
    build_arg_parser as vision_detector_build_arg_parser,
    main as vision_detector_main,
)
from film_cover_engine import (
    render_shusheng_capsule_green,
    render_shusheng_split_red,
    render_shusheng_side_yellow,
    render_shusheng_top_green,
    render_shusheng_letterbox,
    FILM_COVER_STYLES,
    list_film_cover_styles,
    render_film_cover_style,
    build_arg_parser as build_film_cover_arg_parser,
    main as film_cover_main,
)
from poster_visual_learner import (
    extract_poster_features,
    analyze_poster_visual,
    DEFAULT_TARGET_FILES,
    DEFAULT_OUTPUT_PATH,
    build_arg_parser as poster_learner_build_arg_parser,
    main as poster_learner_main,
)
import autonomous_followup
from autonomous_followup import (
    log as followup_log,
    post_event,
    check_and_sync_git,
    check_and_heal_server,
    run_creative_pipeline_cycle,
    generate_morning_report,
    build_arg_parser as followup_build_arg_parser,
    main as followup_main,
)
import pro_poster_renderer
from pro_poster_renderer import (
    get_base64_image,
    render_html_to_poster,
    build_swiss_01_html,
    build_swiss_02_html,
    build_article_01_html,
    build_article_02_html,
    build_cyber_01_html,
    build_cyber_02_html,
    build_chinese_01_html,
    build_chinese_02_html,
    build_cinema_01_html,
    build_cinema_02_html,
    render_swiss_01,
    render_swiss_02,
    render_article_01,
    render_article_02,
    render_cyber_01,
    render_cyber_02,
    render_chinese_01,
    render_chinese_02,
    render_cinema_01,
    render_cinema_02,
    POSTER_REGISTRY,
    list_poster_presets,
    get_poster_preset,
    render_preset,
    run_all as run_all_posters,
    main as pro_poster_main,
    build_arg_parser as pro_poster_build_arg_parser,
    list_poster_categories as pro_poster_list_categories,
    POSTER_CATEGORIES as PRO_POSTER_CATEGORIES,
)
import agnes_engine
from agnes_engine import (
    load_credentials,
    encode_image_data_uri,
    call_agnes,
    _strip_markdown_codeblock,
    generate_creative_brief,
    refine_prompt_for_agnes,
    detect_visual_subjects,
    vision_inspect_artwork,
    DEFAULT_BASE,
    DEFAULT_CHAT_MODEL,
    CHAT_MODEL_ALLOWLIST,
    AgnesRateLimiter,
    get_rate_limiter,
    reset_rate_limiter,
    _should_retry_http,
)
import render_cinema_poster
from render_cinema_poster import (
    b64 as cinema_b64,
    sanitize_img_uri as cinema_sanitize_img_uri,
    wrap as cinema_wrap,
    build_film_bottom_html,
    build_film_top_html,
    build_side_rail_html,
    film_bottom,
    film_top,
    side_rail,
    shot as cinema_shot,
    CINEMA_POSTER_STYLES,
    list_cinema_poster_styles,
    render_cinema_poster_style,
    build_arg_parser as cinema_build_arg_parser,
    main as cinema_poster_main,
)
import render_drama_poster
from render_drama_poster import (
    b64 as drama_b64,
    sanitize_img_uri as drama_sanitize_img_uri,
    shot as drama_shot,
    css as drama_css,
    build_mega_bleed_html,
    mega_bleed,
    build_hard_field_html,
    hard_field,
    build_chinese_corner_html,
    chinese_corner,
    DRAMA_POSTER_STYLES,
    list_drama_poster_styles,
    render_drama_poster_style,
    build_arg_parser as drama_build_arg_parser,
    main as drama_poster_main,
)
import render_cn_type_poster
from render_cn_type_poster import (
    b64 as cn_b64,
    sanitize_img_uri as cn_sanitize_img_uri,
    render_html as cn_render_html,
    build_monument_html,
    style_monument,
    build_puhui_mega_html,
    style_puhui_mega,
    build_vertical_epic_html,
    style_vertical_epic,
    CN_TYPE_POSTER_STYLES,
    list_cn_type_poster_styles,
    render_cn_type_poster_style,
    build_arg_parser as cn_build_arg_parser,
    main as cn_type_poster_main,
)
import render_layout_poster
from render_layout_poster import (
    b64 as layout_b64,
    sanitize_img_uri as layout_sanitize_img_uri,
    render_html as layout_render_html,
    build_swiss_asym_html,
    layout_swiss_asym,
    build_type_band_html,
    layout_type_band,
    build_axis_tension_html,
    layout_axis_tension,
    build_window_editorial_html,
    layout_window_editorial,
    LAYOUT_POSTER_STYLES,
    list_layout_poster_styles,
    render_layout_poster_style,
    build_arg_parser as layout_build_arg_parser,
    main as layout_poster_main,
)
import render_title_design
from render_title_design import (
    b64 as title_b64,
    sanitize_img_uri as title_sanitize_img_uri,
    shell as title_shell,
    render_html as title_render_html,
    shot as title_shot,
    build_t1_cut_slash_html,
    render_t1_cut_slash,
    build_t2_double_offset_html,
    render_t2_double_offset,
    build_t3_color_split_html,
    render_t3_color_split,
    build_t4_image_in_type_html,
    render_t4_image_in_type,
    build_t5_geo_lock_html,
    render_t5_geo_lock,
    build_t6_outline_stretch_html,
    render_t6_outline_stretch,
    TITLE_DESIGN_REGISTRY,
    render_all_title_designs,
    TITLE_DESIGN_STYLES,
    list_title_design_styles,
    render_title_design_style,
    build_arg_parser as title_build_arg_parser,
    main as title_design_main,
)
import render_title_refined
from render_title_refined import (
    b64 as refined_b64,
    sanitize_img_uri as refined_sanitize_img_uri,
    get_base_css as refined_get_base_css,
    render_html as refined_render_html,
    shot as refined_shot,
    build_r1_oriental_center_html,
    render_r1_oriental_center,
    build_r2_left_big_html,
    render_r2_left_big,
    build_r3_vertical_spine_html,
    render_r3_vertical_spine,
    build_r4_sky_field_html,
    render_r4_sky_field,
    build_r5_film_bottom_html,
    render_r5_film_bottom,
    REFINED_TITLE_REGISTRY,
    render_refined_variant,
    render_all_refined_titles,
    REFINED_TITLE_STYLES,
    normalize_refined_style_key,
    list_refined_title_styles,
    render_refined_title_style,
    build_arg_parser as refined_title_build_arg_parser,
    main as refined_title_main,
)
import render_variants_verify
from render_variants_verify import (
    b64 as verify_b64,
    sanitize_img_uri as verify_sanitize_img_uri,
    get_base_css as verify_get_base_css,
    shell as verify_shell,
    shot as verify_shot,
    render_html as verify_render_html,
    build_v1_top_title_html,
    render_v1_top_title,
    build_v2_topleft_html,
    render_v2_topleft,
    build_v3_vertical_corner_html,
    render_v3_vertical_corner,
    build_v4_bottom_left_min_html,
    render_v4_bottom_left_min,
    build_v5_whisper_html,
    render_v5_whisper,
    build_v6_center_top_html,
    render_v6_center_top,
    build_v7_diag_minimal_html,
    render_v7_diag_minimal,
    build_v8_vertical_seal_html,
    render_v8_vertical_seal,
    VARIANTS_REGISTRY as VERIFY_VARIANTS_REGISTRY,
    render_all_variants as verify_render_all_variants,
    normalize_variant_key as verify_normalize_variant_key,
    list_variants as verify_list_variants,
    render_variant_style as verify_render_variant_style,
    build_arg_parser as verify_build_arg_parser,
    main as verify_variants_main,
)
import batch_layout_cn_789
from batch_layout_cn_789 import (
    resolve_layout_font,
    font as layout_cn_font,
    measure as layout_cn_measure,
    text_rgba as layout_cn_text_rgba,
    paste_rgba as layout_cn_paste_rgba,
    compose_07,
    compose_08,
    compose_09,
    normalize_variant_key as normalize_layout_cn_key,
    render_layout_cn,
    render_all_layouts as render_all_layout_cn,
    LAYOUT_CN_REGISTRY,
    SHOTS as LAYOUT_CN_SHOTS,
    classify_generation_error as layout_cn_classify_error,
    generate_layout_shot,
    run_batch_generate_shots,
    list_layout_cn_variants,
    build_arg_parser as build_layout_cn_arg_parser,
)
import batch_layout_variants
from batch_layout_variants import (
    LAYOUT_VARIANTS,
    LAYOUTS as BATCH_LAYOUTS,
    get_layout_variants_catalog,
    find_layout_variant,
    build_layout_prompt,
    generate_layout_variant,
    run_batch_layout_variants,
    classify_generation_error as layout_variants_classify_error,
    build_arg_parser as build_layout_variants_arg_parser,
)
import batch_type_behind
from batch_type_behind import (
    PRESET_WORDS as TYPE_BEHIND_PRESETS,
    get_preset_words as get_type_behind_presets,
    detect_language as detect_type_behind_lang,
    build_type_behind_prompt,
    prompt as type_behind_prompt,
    generate_type_behind,
    run_batch_type_behind,
    classify_generation_error as type_behind_classify_error,
    build_arg_parser as build_type_behind_arg_parser,
)
import batch_type_behind_v154
from batch_type_behind_v154 import (
    EXPERIMENTS as TYPE_BEHIND_V154_EXPERIMENTS,
    VERSION_METADATA as TYPE_BEHIND_V154_METADATA,
    list_versions as list_type_behind_v154_versions,
    list_experiments as list_type_behind_v154_experiments,
    get_experiment_by_stem as get_type_behind_v154_experiment_by_stem,
    generate_single_experiment as generate_type_behind_v154_single,
    run_batch_v154 as run_batch_type_behind_v154,
    classify_generation_error as type_behind_v154_classify_error,
    build_arg_parser as build_type_behind_v154_arg_parser,
)
import batch_skill71_hifi_p0
from batch_skill71_hifi_p0 import (
    PROMPTS as SKILL71_HIFI_P0_PROMPTS,
    list_hifi_presets,
    get_hifi_preset,
    render_single_hifi,
    run_batch_hifi,
    classify_generation_error as hifi_classify_error,
    build_arg_parser as build_skill71_hifi_p0_arg_parser,
)
import batch_skill71_samples
from batch_skill71_samples import (
    DEFAULT_INDEX_PATH as SKILL71_DEFAULT_INDEX,
    BASE_SUBJECT as SKILL71_BASE_SUBJECT,
    CLEAN as SKILL71_CLEAN,
    slugify as skill71_slugify,
    load_skills_index as skill71_load_index,
    build_prompt as skill71_build_prompt,
    render_single_skill_sample as skill71_render_single,
    filter_skills as skill71_filter_skills,
    run_batch_skill_samples as skill71_run_batch,
    list_skills as skill71_list_skills,
    one as skill71_one,
    classify_generation_error as skill71_classify_error,
    build_arg_parser as build_skill71_samples_arg_parser,
)
import merge_skill71_gallery
from merge_skill71_gallery import (
    GROUP_META as MERGE_GROUP_META,
    DEFAULT_CATEGORY_ORDER as MERGE_DEFAULT_CATEGORY_ORDER,
    build_gallery_item as merge_build_gallery_item,
    load_skills_index as merge_load_skills_index,
    load_batch_report as merge_load_batch_report,
    collect_gallery_items as merge_collect_gallery_items,
    update_index_html as merge_update_index_html,
    merge_gallery,
    build_arg_parser as merge_build_arg_parser,
    main as merge_main,
)
import batch_agnes_samples
from batch_agnes_samples import (
    DEFAULT_LIB_PATH as AGNES_SAMPLES_DEFAULT_LIB,
    DEFAULT_OUT_DIR as AGNES_SAMPLES_DEFAULT_OUT,
    slugify as agnes_samples_slugify,
    load_prompts_library as agnes_samples_load_lib,
    build_item_prompt as agnes_samples_build_prompt,
    render_single_sample as agnes_samples_render_single,
    filter_items as agnes_samples_filter_items,
    run_batch_agnes_samples as agnes_samples_run_batch,
    list_items as agnes_samples_list_items,
    one as agnes_samples_one,
    main as agnes_samples_main,
    classify_generation_error as agnes_samples_classify_error,
    build_arg_parser as build_agnes_samples_arg_parser,
)
import install_skills_71
from install_skills_71 import (
    LICENSE_NOTES as SKILLS_71_LICENSE_NOTES,
    sha256_bytes as skills_71_sha256_bytes,
    sha256_file as skills_71_sha256_file,
    repo_tarball_url as skills_71_repo_tarball_url,
    raw_url_from_blob as skills_71_raw_url_from_blob,
    safe_extract_tar as skills_71_safe_extract_tar,
    safe_extract_zip as skills_71_safe_extract_zip,
    copy_skill_tree as skills_71_copy_skill_tree,
    write_meta as skills_71_write_meta,
    verify_skill_md as skills_71_verify_skill_md,
    load_manifest as skills_71_load_manifest,
    filter_entries as skills_71_filter_entries,
    install_one as skills_71_install_one,
    run_install as skills_71_run_install,
    build_arg_parser as skills_71_build_arg_parser,
    list_skills as skills_71_list_skills,
    main as skills_71_main,
)
import gen_agnes_samples
from gen_agnes_samples import (
    DEFAULT_LIB_PATH as GEN_AGNES_DEFAULT_LIB,
    DEFAULT_OUT_DIR as GEN_AGNES_DEFAULT_OUT,
    DEFAULT_REPORT_NAME as GEN_AGNES_DEFAULT_REPORT_NAME,
    slugify as gen_agnes_slugify,
    load_prompts_library as gen_agnes_load_lib,
    build_item_prompt as gen_agnes_build_prompt,
    run_one as gen_agnes_run_one,
    filter_items as gen_agnes_filter_items,
    run_batch_gen as gen_agnes_run_batch,
    list_items as gen_agnes_list_items,
    build_arg_parser as gen_agnes_build_arg_parser,
    main as gen_agnes_main,
    classify_generation_error as gen_agnes_classify_error,
)
import test_gemini_integration
from test_gemini_integration import (
    DEFAULT_TEST_STEPS as GEMINI_DEFAULT_TEST_STEPS,
    parse_steps as gemini_parse_steps,
    test_step_1_chrome as gemini_step_1_chrome,
    test_step_2_gateway as gemini_step_2_gateway,
    test_step_3_brief as gemini_step_3_brief,
    test_step_4_prompt as gemini_step_4_prompt,
    test_step_5_detector as gemini_step_5_detector,
    test_step_6_rasterizer as gemini_step_6_rasterizer,
    test_step_7_inspect as gemini_step_7_inspect,
    run_integration_suite as gemini_run_integration_suite,
    run_tests as gemini_run_tests,
    build_arg_parser as gemini_build_arg_parser,
    main as gemini_main,
)
import compose_beauty_covers
from compose_beauty_covers import (
    resolve_source_image as beauty_resolve_source,
    image_to_base64_uri as beauty_image_to_b64,
    cover_html as beauty_cover_html,
    render as beauty_render,
    run_beauty_experiment as beauty_run_experiment,
    build_arg_parser as beauty_build_arg_parser,
    main as beauty_main,
    W as BEAUTY_W,
    H as BEAUTY_H,
    OUT as BEAUTY_OUT,
    FALLBACK_SRCS as BEAUTY_FALLBACK_SRCS,
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

    def test_cli_main_demo_mode(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            code = copy_rules_main([])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("in ", out)
        self.assertIn("fix", out)
        self.assertIn("lint", out)

    def test_cli_main_explicit_text_and_fix(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            code = copy_rules_main(["Agnes模型发布"])
        self.assertEqual(code, 0)
        self.assertIn("Agnes 模型发布", buf.getvalue())

        buf_opt = io.StringIO()
        with patch("sys.stdout", buf_opt):
            code_opt = copy_rules_main(["-t", "海报BEAUTY“高级感”设计"])
        self.assertEqual(code_opt, 0)
        self.assertIn("海报 BEAUTY「高级感」设计", buf_opt.getvalue())

    def test_cli_main_check_mode_clean_and_issue(self):
        # 干净文本检查
        buf_clean = io.StringIO()
        with patch("sys.stdout", buf_clean):
            code_clean = copy_rules_main(["--check", "Agnes 模型发布", "--strict"])
        self.assertEqual(code_clean, 0)
        self.assertIn("文案排版规范检查通过", buf_clean.getvalue())

        # 存在排版问题的文本：宽松模式返回 0
        buf_issue = io.StringIO()
        with patch("sys.stdout", buf_issue):
            code_issue = copy_rules_main(["--check", "Agnes模型发布"])
        self.assertEqual(code_issue, 0)
        self.assertIn("⚠️", buf_issue.getvalue())

        # 存在排版问题的文本：严格模式返回 1
        code_strict = copy_rules_main(["--check", "Agnes模型发布", "--strict", "-q"])
        self.assertEqual(code_strict, 1)

    def test_cli_main_json_mode(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            code = copy_rules_main(["--json", "Agnes模型"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertIn("clean", data)
        self.assertIn("issues", data)
        self.assertIn("original", data)
        self.assertIn("fixed", data)
        self.assertFalse(data["clean"])
        self.assertEqual(data["fixed"], "Agnes 模型")

        buf_check = io.StringIO()
        with patch("sys.stdout", buf_check):
            code_check = copy_rules_main(["--check", "--json", "Agnes 模型"])
        self.assertEqual(code_check, 0)
        data_check = json.loads(buf_check.getvalue())
        self.assertTrue(data_check["clean"])
        self.assertEqual(data_check["issues"], [])

    def test_cli_main_file_out_and_in_place(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_p = Path(tmp_dir)
            in_file = tmp_p / "dirty_copy.txt"
            out_file = tmp_p / "fixed_copy.txt"
            in_file.write_text("Agnes模型“商业”设计", encoding="utf-8")

            # 测试写入 --out
            code_out = copy_rules_main([
                "-f", str(in_file),
                "-o", str(out_file),
                "--quiet",
            ])
            self.assertEqual(code_out, 0)
            self.assertTrue(out_file.exists())
            self.assertEqual(out_file.read_text(encoding="utf-8"), "Agnes 模型「商业」设计")

            # 测试 --in-place
            code_inplace = copy_rules_main([
                "-f", str(in_file),
                "-i",
                "--quiet",
            ])
            self.assertEqual(code_inplace, 0)
            self.assertEqual(in_file.read_text(encoding="utf-8"), "Agnes 模型「商业」设计")

    def test_cli_main_file_error_handling(self):
        err_buf = io.StringIO()
        with patch("sys.stderr", err_buf):
            code = copy_rules_main(["-f", "/tmp/path/to/nonexistent_copywriting_file.txt"])
        self.assertEqual(code, 1)

    def test_cli_main_file_error_quiet_mode(self):
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with redirect_stderr(err_buf), redirect_stdout(out_buf):
            code = copy_rules_main(["-f", "/tmp/path/to/nonexistent_copywriting_file.txt", "-q"])
        self.assertEqual(code, 1)
        self.assertEqual(err_buf.getvalue(), "")
        self.assertEqual(out_buf.getvalue(), "")

    def test_cli_main_file_error_json_output(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = copy_rules_main(["-f", "/tmp/path/to/nonexistent_copywriting_file.txt", "--json"])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data["ok"])
        self.assertIn("error", data)

    def test_cli_main_exception_stderr_output(self):
        err_buf = io.StringIO()
        with patch("copywriting_rules.lint_copy", side_effect=RuntimeError("Lint crash")), \
             redirect_stderr(err_buf):
            code = copy_rules_main(["Agnes 测试文案"])
        self.assertEqual(code, 1)
        self.assertIn("❌ 文案排版处理异常: Lint crash", err_buf.getvalue())

    def test_cli_main_exception_quiet_mode(self):
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("copywriting_rules.lint_copy", side_effect=RuntimeError("Silent crash")), \
             redirect_stderr(err_buf), redirect_stdout(out_buf):
            code = copy_rules_main(["Agnes 测试文案", "-q"])
        self.assertEqual(code, 1)
        self.assertEqual(err_buf.getvalue(), "")
        self.assertEqual(out_buf.getvalue(), "")

    def test_cli_main_exception_json_output(self):
        buf = io.StringIO()
        with patch("copywriting_rules.lint_copy", side_effect=RuntimeError("JSON crash")), \
             redirect_stdout(buf):
            code = copy_rules_main(["Agnes 测试文案", "--json"])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"], "JSON crash")


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

    def test_font_resolution_none_and_empty(self):
        for empty_val in [None, "", "   ", "\t\n"]:
            with self.subTest(empty_val=empty_val):
                resolved = resolve_font_path(empty_val)
                self.assertIsInstance(resolved, str)
                self.assertTrue(len(resolved) > 0)
                self.assertTrue(Path(resolved).exists(), f"空值/None 解析字体路径不存在: {resolved}")

    def test_font_resolution_path_object(self):
        sample_path = FONTS_DIR / "SmileySans-Oblique.ttf"
        if sample_path.exists():
            resolved = resolve_font_path(sample_path)
            self.assertIsInstance(resolved, str)
            self.assertEqual(resolved, str(sample_path.resolve()))

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


class TestTypographyRulesCLI(unittest.TestCase):
    """测试字体排印与网格系统 CLI 规范化、字阶内省、网格推导与严格质检模式"""

    def test_cli_parser_defaults(self):
        parser = build_typography_parser()
        args = parser.parse_args([])
        self.assertEqual(args.width, 1024)
        self.assertEqual(args.height, 1024)
        self.assertEqual(args.columns, 12)
        self.assertEqual(args.ratio_name, "golden")
        self.assertEqual(args.base_size, 16.0)
        self.assertFalse(args.json)
        self.assertFalse(args.strict)

    def test_parse_exclusion_zones(self):
        # 1. 空输入
        self.assertEqual(parse_exclusion_zones(None), [])
        self.assertEqual(parse_exclusion_zones(""), [])

        # 2. 逗号分隔四元组
        zones_csv = parse_exclusion_zones("0.45,0.08,0.55,0.22")
        self.assertEqual(len(zones_csv), 1)
        self.assertAlmostEqual(zones_csv[0]["x_min"], 0.45)
        self.assertAlmostEqual(zones_csv[0]["y_min"], 0.08)
        self.assertAlmostEqual(zones_csv[0]["x_max"], 0.55)
        self.assertAlmostEqual(zones_csv[0]["y_max"], 0.22)
        self.assertEqual(zones_csv[0]["type"], "face")

        # 3. JSON 数组
        json_str = '[{"x_min": 0.1, "y_min": 0.2, "x_max": 0.3, "y_max": 0.4, "type": "subject"}]'
        zones_json = parse_exclusion_zones(json_str)
        self.assertEqual(len(zones_json), 1)
        self.assertAlmostEqual(zones_json[0]["x_min"], 0.1)

        # 4. JSON 单个字典对象
        dict_str = '{"x_min": 0.2, "y_min": 0.3, "x_max": 0.4, "y_max": 0.5}'
        zones_dict = parse_exclusion_zones(dict_str)
        self.assertEqual(len(zones_dict), 1)
        self.assertAlmostEqual(zones_dict[0]["x_min"], 0.2)

        # 5. 非法输入
        self.assertEqual(parse_exclusion_zones("invalid,data"), [])

    def test_plan_to_serializable(self):
        plan = SmartPosterComposer.plan_layout(1024, 1024, [], "测试标题")
        self.assertIsInstance(plan["grid"], SwissGridSystem)
        serializable = plan_to_serializable(plan)
        self.assertIsInstance(serializable["grid"], dict)
        self.assertEqual(serializable["grid"]["width"], 1024)
        dumped = json.dumps(serializable)
        self.assertIn("title_formatted", dumped)

    def test_cli_main_demo_mode(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            code = typography_main([])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Typography Engine", out)
        self.assertIn("文案规范输出", out)
        self.assertIn("黄金字阶层级", out)

        buf_json = io.StringIO()
        with patch("sys.stdout", buf_json):
            code_json = typography_main(["--json"])
        self.assertEqual(code_json, 0)
        data = json.loads(buf_json.getvalue())
        self.assertIn("demo_copy_formatted", data)
        self.assertIn("demo_hierarchy", data)
        self.assertIn("demo_plan", data)

    def test_cli_main_list_ratios(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            code = typography_main(["--list-ratios"])
        self.assertEqual(code, 0)
        self.assertIn("golden", buf.getvalue())
        self.assertIn("perfect_fifth", buf.getvalue())

        buf_json = io.StringIO()
        with patch("sys.stdout", buf_json):
            code_json = typography_main(["--list-ratios", "--json"])
        self.assertEqual(code_json, 0)
        data = json.loads(buf_json.getvalue())
        self.assertIn("golden", data)
        self.assertEqual(data["golden"], 1.618)

    def test_cli_main_hierarchy(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            code = typography_main(["--hierarchy", "--base-size", "20", "--ratio-name", "perfect_fourth"])
        self.assertEqual(code, 0)
        self.assertIn("perfect_fourth", buf.getvalue())

        buf_json = io.StringIO()
        with patch("sys.stdout", buf_json):
            code_json = typography_main(["--hierarchy", "--base-size", "16", "--ratio-name", "golden", "--json"])
        self.assertEqual(code_json, 0)
        data = json.loads(buf_json.getvalue())
        self.assertEqual(data["ratio_name"], "golden")
        self.assertEqual(data["hierarchy"]["h1"], 68)

    def test_cli_main_grid(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            code = typography_main(["--grid", "-W", "1200", "-H", "1600", "--columns", "12"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("瑞士 12 栏网格计算", out)
        self.assertIn("top_banner", out)

        buf_json = io.StringIO()
        with patch("sys.stdout", buf_json):
            code_json = typography_main(["--grid", "-W", "1200", "-H", "1600", "--json"])
        self.assertEqual(code_json, 0)
        data = json.loads(buf_json.getvalue())
        self.assertEqual(data["width"], 1200)
        self.assertEqual(data["height"], 1600)
        self.assertIn("layout_zones", data)

    def test_cli_main_format_copy(self):
        raw = 'Agnes 2.5模型震撼发布，首创"混元矢量"排版！'
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            code = typography_main(["--format-copy", raw])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Agnes 2.5 模型", out)
        self.assertIn("「混元矢量」", out)

        buf_json = io.StringIO()
        with patch("sys.stdout", buf_json):
            code_json = typography_main(["--format-copy", raw, "--json"])
        self.assertEqual(code_json, 0)
        data = json.loads(buf_json.getvalue())
        self.assertIn("Agnes 2.5 模型", data["formatted"])
        self.assertIn("「混元矢量」", data["formatted"])

    def test_cli_main_theme_mode_and_sizes(self):
        buf_mode = io.StringIO()
        with patch("sys.stdout", buf_mode):
            code_mode = typography_main(["--theme-mode", "ctr", "--json"])
        self.assertEqual(code_mode, 0)
        data_mode = json.loads(buf_mode.getvalue())
        self.assertEqual(data_mode["theme_mode"], "压图巨字")

        buf_sizes = io.StringIO()
        with patch("sys.stdout", buf_sizes):
            code_sizes = typography_main(["--sizes", "-W", "1080", "--json"])
        self.assertEqual(code_sizes, 0)
        data_sizes = json.loads(buf_sizes.getvalue())
        self.assertIn("T1", data_sizes)
        self.assertEqual(data_sizes["T1"]["size"], 120)

    def test_cli_main_validate_copy_clean_and_strict(self):
        # 正常文案通过
        buf_valid = io.StringIO()
        with patch("sys.stdout", buf_valid):
            code_valid = typography_main([
                "--validate-copy",
                "-t", "山河盛宴",
                "--en-title", "FESTIVAL",
                "--slogan", "千里江山一日还",
                "--strict"
            ])
        self.assertEqual(code_valid, 0)
        self.assertIn("校验通过", buf_valid.getvalue())

        # 违规文案：非 strict 返回 0
        buf_issue = io.StringIO()
        with patch("sys.stdout", buf_issue):
            code_issue = typography_main([
                "--validate-copy",
                "-t", "超级长的大气海报主标题完全超出限制",
                "--json"
            ])
        self.assertEqual(code_issue, 0)
        data_issue = json.loads(buf_issue.getvalue())
        self.assertFalse(data_issue["valid"])
        self.assertTrue(len(data_issue["issues"]) > 0)

        # 违规文案：--strict 返回 1
        code_strict = typography_main([
            "--validate-copy",
            "-t", "超级长的大气海报主标题完全超出限制",
            "--strict",
            "-q"
        ])
        self.assertEqual(code_strict, 1)

    def test_cli_main_plan_layout_normal_and_face_avoidance(self):
        # 1. 经典横向排版
        buf_mag = io.StringIO()
        with patch("sys.stdout", buf_mag):
            code_mag = typography_main([
                "--plan",
                "-t", "铜钟与蒸汽城",
                "--subtitle", "蒸汽纪元",
                "--en-title", "Steam & Chime",
                "--json"
            ])
        self.assertEqual(code_mag, 0)
        data_mag = json.loads(buf_mag.getvalue())
        self.assertEqual(data_mag["layout_style"], "top_horizontal_magazine")
        self.assertEqual(data_mag["title_formatted"], "铜钟与蒸汽城")

        # 2. 面部避障双向拆字错位竖排
        buf_split = io.StringIO()
        with patch("sys.stdout", buf_split):
            code_split = typography_main([
                "--plan",
                "-t", "苏园惊鸿",
                "--en-title", "Suzhou Classic",
                "--exclusion-zones", "0.45,0.08,0.55,0.22",
                "--json"
            ])
        self.assertEqual(code_split, 0)
        data_split = json.loads(buf_split.getvalue())
        self.assertEqual(data_split["layout_style"], "bilateral_split_vertical")
        roles = {el["role"]: el for el in data_split["elements"]}
        self.assertIn("title_part_1", roles)
        self.assertIn("title_part_2", roles)
        self.assertEqual(roles["title_part_1"]["orientation"], "vertical")
        self.assertEqual(roles["title_part_2"]["orientation"], "vertical")

    def test_cli_main_exception_stderr_output(self):
        err_buf = io.StringIO()
        with patch("typography_rules._run", side_effect=RuntimeError("Typography crash")), \
             redirect_stderr(err_buf):
            code = typography_main([])
        self.assertEqual(code, 1)
        self.assertIn("❌ 字体排印处理异常: Typography crash", err_buf.getvalue())

    def test_cli_main_exception_quiet_mode(self):
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("typography_rules._run", side_effect=RuntimeError("Silent crash")), \
             redirect_stderr(err_buf), redirect_stdout(out_buf):
            code = typography_main(["-q"])
        self.assertEqual(code, 1)
        self.assertEqual(err_buf.getvalue(), "")
        self.assertEqual(out_buf.getvalue(), "")

    def test_cli_main_exception_json_mode(self):
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("typography_rules._run", side_effect=RuntimeError("JSON crash")), \
             redirect_stderr(err_buf), redirect_stdout(out_buf):
            code = typography_main(["--json"])
        self.assertEqual(code, 1)
        self.assertEqual(err_buf.getvalue(), "")
        data = json.loads(out_buf.getvalue())
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"], "JSON crash")



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

    def test_list_catalog_options(self):
        opts = list_catalog_options()
        self.assertIsInstance(opts, dict)
        self.assertIn("subjects", opts)
        self.assertIn("tones", opts)
        self.assertIn("goals", opts)
        self.assertIn("platforms", opts)
        self.assertIn("modes", opts)
        self.assertIn("beauty", opts["subjects"])
        self.assertIn("luxury", opts["tones"])
        self.assertIn("wechat", opts["platforms"])
        self.assertIn("diag", opts["modes"])

    def test_list_skill_styles(self):
        skills = list_skill_styles()
        self.assertIsInstance(skills, list)
        self.assertGreater(len(skills), 0)
        first = skills[0]
        self.assertIn("id", first)
        self.assertIn("call_name", first)
        self.assertIn("tone", first)
        self.assertIn("mode", first)
        ids = [s["id"] for s in skills]
        self.assertIn("S05", ids)

    def test_resolve_style_kwargs_and_empty_brief(self):
        st = resolve_style(subject="product", tone="cyber", platform="xhs")
        self.assertEqual(st.mode, "diag")
        self.assertEqual(st.name, "cyber/product/editorial/diag")
        self.assertIn("cyber", st.notes)
        self.assertIn("product", st.notes)

    def test_cover_style_cli_main_default_and_flags(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            code = cover_style_main([])
        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["mode"], "diag")

        buf_custom = io.StringIO()
        with patch("sys.stdout", buf_custom):
            code_custom = cover_style_main([
                "--subject", "product",
                "--tone", "cyber",
                "--platform", "xhs",
                "--goal", "brand",
            ])
        self.assertEqual(code_custom, 0)
        output_custom = json.loads(buf_custom.getvalue())
        self.assertEqual(output_custom["name"], "cyber/product/brand/diag")

    def test_cover_style_cli_main_json_inline(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            code = cover_style_main(["--json", '{"subject": "scenery", "tone": "minimal"}'])
        self.assertEqual(code, 0)
        output = json.loads(buf.getvalue())
        self.assertIn("minimal", output["name"])

        # 非法 JSON 字符串返回退出码 1
        err_buf = io.StringIO()
        with patch("sys.stderr", err_buf):
            code_invalid = cover_style_main(["--json", 'invalid-json-string'])
        self.assertEqual(code_invalid, 1)

        # 根对象非字典返回退出码 1
        with patch("sys.stderr", err_buf):
            code_array = cover_style_main(["--json", '["a", "b"]'])
        self.assertEqual(code_array, 1)

    def test_cover_style_cli_main_brief_file_and_out(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            brief_file = tmp_path / "test_brief.json"
            out_file = tmp_path / "out_style.json"
            brief_file.write_text(json.dumps({"subject": "character", "tone": "warm"}), encoding="utf-8")

            buf = io.StringIO()
            with patch("sys.stdout", buf):
                code = cover_style_main([
                    str(brief_file),
                    "--out", str(out_file),
                    "--quiet",
                ])
            self.assertEqual(code, 0)
            self.assertEqual(buf.getvalue(), "")  # --quiet 抑制输出
            self.assertTrue(out_file.exists())
            loaded = json.loads(out_file.read_text(encoding="utf-8"))
            self.assertIn("warm", loaded["name"])

    def test_cover_style_cli_main_list_modes(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            code_list = cover_style_main(["--list"])
        self.assertEqual(code_list, 0)
        self.assertIn("Agnes Studio · 封面样式目录预设选项", buf.getvalue())

        buf_skills = io.StringIO()
        with patch("sys.stdout", buf_skills):
            code_skills = cover_style_main(["--list-skills"])
        self.assertEqual(code_skills, 0)
        self.assertIn("Agnes Studio · 封面预设 Skill 样式映射", buf_skills.getvalue())

    def test_cover_style_cli_main_error_handling(self):
        err_buf = io.StringIO()
        with patch("sys.stderr", err_buf):
            code_missing = cover_style_main(["/tmp/path/to/definitely_not_existing_brief.json"])
        self.assertEqual(code_missing, 1)

    def test_cover_style_cli_main_missing_brief_quiet_mode(self):
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with redirect_stderr(err_buf), redirect_stdout(out_buf):
            code_missing = cover_style_main(["/tmp/path/to/definitely_not_existing_brief.json", "-q"])
        self.assertEqual(code_missing, 1)
        self.assertEqual(err_buf.getvalue(), "")
        self.assertEqual(out_buf.getvalue(), "")

    def test_cover_style_cli_main_exception_stderr_output(self):
        err_buf = io.StringIO()
        with patch("cover_style.resolve_style", side_effect=RuntimeError("Resolve crash")), \
             redirect_stderr(err_buf):
            code = cover_style_main([])
        self.assertEqual(code, 1)
        self.assertIn("❌ 封面样式推导异常: Resolve crash", err_buf.getvalue())

    def test_cover_style_cli_main_exception_quiet_mode(self):
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("cover_style.resolve_style", side_effect=RuntimeError("Silent crash")), \
             redirect_stderr(err_buf), redirect_stdout(out_buf):
            code = cover_style_main(["-q"])
        self.assertEqual(code, 1)
        self.assertEqual(err_buf.getvalue(), "")
        self.assertEqual(out_buf.getvalue(), "")


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

    def test_safe_zone_analyzer_guards(self):
        with self.assertRaises(ValueError):
            analyze_safe_zone("")
        with self.assertRaises(ValueError):
            analyze_safe_zone(None)
        with self.assertRaises(FileNotFoundError):
            analyze_safe_zone("non_existent_image_for_analysis.png")


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

    def test_classify_generation_error(self):
        self.assertEqual(cover_classify_error("HTTP 502: Bad Gateway"), "gateway_502")
        self.assertEqual(cover_classify_error("HTTP 401: Unauthorized"), "auth")
        self.assertEqual(cover_classify_error("HTTP 403: Forbidden"), "auth")
        self.assertEqual(cover_classify_error("Connection timed out"), "timeout")
        self.assertEqual(cover_classify_error("some prompt error"), "generation_error")
        self.assertEqual(cover_classify_error("MISSING_SOURCE_ASSET: missing.png"), "MISSING_SOURCE_ASSET")

    def test_classify_pipeline_error(self):
        self.assertEqual(cover_pipeline_classify_error("MISSING_SOURCE_ASSET: no file"), "MISSING_SOURCE_ASSET")
        self.assertEqual(cover_pipeline_classify_error("MISSING_BRIEF: no brief"), "MISSING_BRIEF")
        self.assertEqual(cover_pipeline_classify_error("INVALID_BRIEF: broken json"), "INVALID_BRIEF")
        self.assertEqual(cover_pipeline_classify_error("[head] face box clipped: {...}"), "QA_HEAD")
        self.assertEqual(cover_pipeline_classify_error("[layout] subject placement failed"), "QA_LAYOUT")
        self.assertEqual(cover_pipeline_classify_error("[face] title would occlude face"), "QA_FACE")
        self.assertEqual(cover_pipeline_classify_error("[vignette] too heavy, corners/center=0.42"), "QA_VIGNETTE")
        self.assertEqual(cover_pipeline_classify_error("[copy] ['forbidden keyword']"), "QA_COPY")
        self.assertEqual(cover_pipeline_classify_error("[sharpness] too soft, lap_mean=1.8"), "QA_SHARPNESS")
        self.assertEqual(cover_pipeline_classify_error("HTTP 502: Bad Gateway"), "gateway_502")
        self.assertEqual(cover_pipeline_classify_error("HTTP 401: Unauthorized"), "auth")
        self.assertEqual(cover_pipeline_classify_error("Connection timed out"), "timeout")
        self.assertEqual(cover_pipeline_classify_error("Unexpected renderer crash"), "pipeline_error")

    def test_generate_cover_subject_validation_and_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_target = tmp_path / "subject.png"

            # 1. 验证空 prompt 防护
            res_no_prompt = generate_cover_subject("", out_target)
            self.assertFalse(res_no_prompt["ok"])
            self.assertEqual(res_no_prompt["error_class"], "generation_error")

            # 2. 验证空 out_path 防护
            res_no_out = generate_cover_subject("fashion portrait", "")
            self.assertFalse(res_no_out["ok"])
            self.assertEqual(res_no_out["error_class"], "generation_error")

            # 3. 验证 dry_run 演练模式
            res_dry = generate_cover_subject("fashion portrait", out_target, dry_run=True)
            self.assertTrue(res_dry["ok"])
            self.assertTrue(res_dry["dry_run"])
            self.assertEqual(res_dry["size_kb"], 0)
            self.assertFalse(out_target.exists())

            # 4. 验证已存在大文件跳过逻辑 (>20KB)
            out_target.write_bytes(b"x" * 25_000)
            res_skip = generate_cover_subject("fashion portrait", out_target)
            self.assertTrue(res_skip["ok"])
            self.assertTrue(res_skip["skipped"])
            self.assertEqual(res_skip["size_kb"], 24)

            # 5. force=True 覆盖已存在跳过
            def mock_gen_force(prompt, **kwargs):
                return {"ok": True, "cost_s": 1.2, "via": "mock"}

            def mock_save_force(res, target):
                Path(target).write_bytes(b"y" * 26_000)

            res_force = generate_cover_subject(
                "fashion portrait",
                out_target,
                force=True,
                generate_fn=mock_gen_force,
                save_image_fn=mock_save_force,
            )
            self.assertTrue(res_force["ok"])
            self.assertFalse(res_force.get("skipped", False))

            # 6. 未提供可调用生成函数且 gateway 为空
            res_no_gen = generate_cover_subject(
                "fashion portrait",
                tmp_path / "another.png",
                generate_fn=None,
            )
            if cover_pipeline.generate is None:
                self.assertFalse(res_no_gen["ok"])
                self.assertEqual(res_no_gen["error_class"], "generation_error")

    def test_generate_cover_subject_gateway_classification_and_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_target = tmp_path / "gen_subject.png"

            # 1. 成功生成
            def mock_gen_success(prompt, **kwargs):
                return {"ok": True, "cost_s": 2.5, "via": "mock_engine"}

            def mock_save(res, target):
                Path(target).write_bytes(b"z" * 22_000)

            res_ok = generate_cover_subject(
                "portrait prompt",
                out_target,
                generate_fn=mock_gen_success,
                save_image_fn=mock_save,
            )
            self.assertTrue(res_ok["ok"])
            self.assertEqual(res_ok["cost_s"], 2.5)
            self.assertEqual(res_ok["via"], "mock_engine")
            self.assertTrue(out_target.exists())

            # 2. 502 错误分类
            target_502 = tmp_path / "subject_502.png"
            def mock_gen_502(prompt, **kwargs):
                return {"ok": False, "error": "HTTP 502: Bad Gateway upstream unavailable"}

            res_502 = generate_cover_subject(
                "portrait prompt",
                target_502,
                generate_fn=mock_gen_502,
            )
            self.assertFalse(res_502["ok"])
            self.assertEqual(res_502["error_class"], "gateway_502")

            # 3. 403 认证错误分类
            target_403 = tmp_path / "subject_403.png"
            def mock_gen_403(prompt, **kwargs):
                return {"ok": False, "error": "HTTP 403: Forbidden - token_rejected"}

            res_403 = generate_cover_subject(
                "portrait prompt",
                target_403,
                generate_fn=mock_gen_403,
            )
            self.assertFalse(res_403["ok"])
            self.assertEqual(res_403["error_class"], "auth")

            # 4. 超时错误分类
            target_timeout = tmp_path / "subject_timeout.png"
            def mock_gen_timeout(prompt, **kwargs):
                raise TimeoutError("Request timed out after 30s")

            res_timeout = generate_cover_subject(
                "portrait prompt",
                target_timeout,
                generate_fn=mock_gen_timeout,
            )
            self.assertFalse(res_timeout["ok"])
            self.assertEqual(res_timeout["error_class"], "timeout")

    def test_cover_pipeline_main_generate_cli(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            brief_file = tmp_path / "test_brief.json"
            brief_file.write_text(
                json.dumps({
                    "goal": "时尚杂志封面",
                    "subject": "东方面孔",
                    "tone": "高级冷艳",
                    "mode": "diag",
                    "platform": "xhs",
                }, ensure_ascii=False),
                encoding="utf-8",
            )
            # 缺少平台源素材时，dry-run 也必须在生成前稳定失败
            with self.assertRaisesRegex(SystemExit, "MISSING_SOURCE_ASSET"):
                cover_pipeline.main(["--brief", str(brief_file), "--generate", "--dry-run"])

            # 提供可读源素材后，dry-run 才能正常完成且不创建目标
            source_file = tmp_path / "source.png"
            source_file.write_bytes(b"source")
            cover_pipeline.main([
                "--brief", str(brief_file), "--xhs-src", str(source_file),
                "--generate", "--dry-run",
            ])

            # 测试 --generate 失败时干净退出
            def mock_failing_gen(*args, **kwargs):
                return {"ok": False, "err": "HTTP 502 Bad Gateway", "error_class": "gateway_502"}

            with patch("cover_pipeline.generate_cover_subject", side_effect=mock_failing_gen):
                with self.assertRaises(SystemExit):
                    cover_pipeline.main(["--brief", str(brief_file), "--generate"])

    def test_preflight_source_asset_checks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # 1. 空路径防护
            self.assertFalse(preflight_source_asset(None)["ok"])
            self.assertEqual(preflight_source_asset("")["error_class"], "MISSING_SOURCE_ASSET")
            self.assertEqual(preflight_source_asset("   ")["error_class"], "MISSING_SOURCE_ASSET")

            # 2. 文件不存在防护
            non_existent = tmp_path / "absent.png"
            res_absent = preflight_source_asset(non_existent)
            self.assertFalse(res_absent["ok"])
            self.assertEqual(res_absent["error_class"], "MISSING_SOURCE_ASSET")
            self.assertIn("does not exist", res_absent["err"])

            # 3. 目录路径防护（非普通文件）
            a_dir = tmp_path / "subdir"
            a_dir.mkdir()
            res_dir = preflight_source_asset(a_dir)
            self.assertFalse(res_dir["ok"])
            self.assertEqual(res_dir["error_class"], "MISSING_SOURCE_ASSET")
            self.assertIn("not a regular file", res_dir["err"])

            # 4. 正常文件通过
            real_file = tmp_path / "valid.png"
            real_file.write_bytes(b"image-data")
            res_ok = preflight_source_asset(real_file)
            self.assertTrue(res_ok["ok"])
            self.assertEqual(res_ok["path"], str(real_file))

            # 5. 不可读权限防护
            with patch("os.access", return_value=False):
                res_unreadable = preflight_source_asset(real_file)
                self.assertFalse(res_unreadable["ok"])
                self.assertEqual(res_unreadable["error_class"], "MISSING_SOURCE_ASSET")
                self.assertIn("not readable", res_unreadable["err"])

            # 6. 批量 preflight_source_assets
            valid_file2 = tmp_path / "valid2.png"
            valid_file2.write_bytes(b"image-data-2")
            self.assertTrue(preflight_source_assets([real_file, valid_file2])["ok"])
            self.assertFalse(preflight_source_assets([real_file, non_existent])["ok"])

    def test_resolve_source_asset_for_platform(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            custom_src = tmp_path / "universal.png"
            brief_with_source_asset = {"source_asset": str(custom_src)}
            self.assertEqual(resolve_source_asset_for_platform("wechat", brief=brief_with_source_asset), custom_src)
            self.assertEqual(resolve_source_asset_for_platform("xhs", brief=brief_with_source_asset), custom_src)

            brief_with_subj = {"subject_src": str(custom_src)}
            self.assertEqual(resolve_source_asset_for_platform("xhs", brief=brief_with_subj), custom_src)

            brief_with_src = {"src": str(custom_src)}
            self.assertEqual(resolve_source_asset_for_platform("wechat", brief=brief_with_src), custom_src)

            # platform 规格差异化解析
            xhs_custom = tmp_path / "xhs_pic.png"
            wechat_custom = tmp_path / "wechat_pic.png"
            brief_split = {"xhs_src": str(xhs_custom), "wechat_src": str(wechat_custom)}
            self.assertEqual(resolve_source_asset_for_platform("xhs", brief=brief_split), xhs_custom)
            self.assertEqual(resolve_source_asset_for_platform("xhs-sq", brief=brief_split), xhs_custom)
            # wechat (2.35:1) 引用 wechat_src；而 wechat-sq (1:1) 在规格表定义中使用 portrait/xhs 源
            self.assertEqual(resolve_source_asset_for_platform("wechat", brief=brief_split), wechat_custom)
            self.assertEqual(resolve_source_asset_for_platform("wechat-sq", brief=brief_split), xhs_custom)

            # 检查 resolve_required_source_assets
            all_assets = resolve_required_source_assets(brief=brief_split, platform="all")
            self.assertEqual(set(all_assets), {xhs_custom, wechat_custom})
            single_assets = resolve_required_source_assets(brief=brief_split, platform="xhs")
            self.assertEqual(single_assets, [xhs_custom])
            fixed_assets = resolve_required_source_assets(brief=brief_with_source_asset, platform="all")
            self.assertEqual(fixed_assets, [custom_src])

    def test_resolve_source_asset_contract_1_xhs_default_missing(self):
        """契约 1: XHS 无显式 source 仍解析到 experiments/_beauty_xhs.png 且缺失由 preflight 返回 MISSING_SOURCE_ASSET。"""
        expected_default = cover_pipeline.ASSETS_EXP / "_beauty_xhs.png"
        self.assertFalse(expected_default.exists(), f"Default asset {expected_default} must not exist")

        for brief_input in (None, {}, {"mode": "diag"}, {"title_a": "东方"}):
            with self.subTest(brief=brief_input):
                resolved = resolve_source_asset_for_platform("xhs", brief=brief_input)
                self.assertEqual(resolved, expected_default)
                self.assertTrue(str(resolved).endswith("experiments/_beauty_xhs.png"))

                pf = preflight_source_asset(resolved)
                self.assertFalse(pf["ok"])
                self.assertEqual(pf["error_class"], "MISSING_SOURCE_ASSET")
                self.assertEqual(pf["missing_path"], str(expected_default))
                self.assertIn("does not exist", pf["err"])

        # xhs-sq 同样遵循 XHS 默认源
        resolved_sq = resolve_source_asset_for_platform("xhs-sq")
        self.assertEqual(resolved_sq, expected_default)
        pf_sq = preflight_source_asset(resolved_sq)
        self.assertFalse(pf_sq["ok"])
        self.assertEqual(pf_sq["error_class"], "MISSING_SOURCE_ASSET")

    def test_resolve_source_asset_contract_2_explicit_precedence(self):
        """契约 2: 显式存在 source 优先于平台默认。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            valid_src = tmp_path / "explicit_valid.png"
            Image.new("RGB", (64, 64), color=(200, 100, 50)).save(valid_src, "PNG")
            default_xhs = cover_pipeline.ASSETS_EXP / "_beauty_xhs.png"

            # 2.1 brief 中的各种显式覆盖键
            for key in ("source_asset", "subject_src", "src", "xhs_src"):
                with self.subTest(key=key):
                    brief = {key: str(valid_src)}
                    resolved = resolve_source_asset_for_platform("xhs", brief=brief)
                    self.assertEqual(resolved, valid_src)
                    self.assertNotEqual(resolved, default_xhs)
                    pf = preflight_source_asset(resolved)
                    self.assertTrue(pf["ok"])
                    self.assertEqual(pf["path"], str(valid_src))

            # 2.2 CLI / 参数传参 xhs_src 显式优先
            resolved_kw = resolve_source_asset_for_platform("xhs", xhs_src=str(valid_src))
            self.assertEqual(resolved_kw, valid_src)
            self.assertNotEqual(resolved_kw, default_xhs)
            self.assertTrue(preflight_source_asset(resolved_kw)["ok"])

            # 2.3 brief 显式通用 source_asset 优先于 xhs_src 参数
            other_src = tmp_path / "other.png"
            Image.new("RGB", (64, 64)).save(other_src)
            resolved_pri = resolve_source_asset_for_platform(
                "xhs", brief={"source_asset": str(valid_src)}, xhs_src=str(other_src)
            )
            self.assertEqual(resolved_pri, valid_src)

    def test_resolve_source_asset_contract_3_explicit_missing_reports_explicit_path(self):
        """契约 3: 显式 source 缺失时错误指向显式路径。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            missing_src = tmp_path / "missing_explicit_source.png"
            default_xhs = cover_pipeline.ASSETS_EXP / "_beauty_xhs.png"

            for key in ("source_asset", "subject_src", "src", "xhs_src"):
                with self.subTest(key=key):
                    brief = {key: str(missing_src)}
                    resolved = resolve_source_asset_for_platform("xhs", brief=brief)
                    self.assertEqual(resolved, missing_src)
                    pf = preflight_source_asset(resolved)
                    self.assertFalse(pf["ok"])
                    self.assertEqual(pf["error_class"], "MISSING_SOURCE_ASSET")
                    self.assertEqual(pf["missing_path"], str(missing_src))
                    self.assertIn(str(missing_src), pf["err"])
                    self.assertNotIn(str(default_xhs), pf["err"])

            # 参数显式传递缺失路径
            resolved_param = resolve_source_asset_for_platform("xhs", xhs_src=str(missing_src))
            self.assertEqual(resolved_param, missing_src)
            pf_param = preflight_source_asset(resolved_param)
            self.assertFalse(pf_param["ok"])
            self.assertEqual(pf_param["missing_path"], str(missing_src))
            self.assertIn(str(missing_src), pf_param["err"])
            self.assertNotIn(str(default_xhs), pf_param["err"])

    def test_resolve_source_asset_contract_4_non_xhs_does_not_fallback_to_xhs_default(self):
        """契约 4: 非 XHS 不错误落到 XHS 默认。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            default_xhs = cover_pipeline.ASSETS_EXP / "_beauty_xhs.png"
            default_hero = cover_pipeline.ASSETS_EXP / "_beauty_hero.png"

            # 4.1 wechat 在无显式 source 时，应落到 _beauty_hero.png，决不能落到 _beauty_xhs.png
            resolved_wx = resolve_source_asset_for_platform("wechat")
            self.assertEqual(resolved_wx, default_hero)
            self.assertNotEqual(resolved_wx, default_xhs)
            self.assertFalse(str(resolved_wx).endswith("_beauty_xhs.png"))
            self.assertTrue(str(resolved_wx).endswith("_beauty_hero.png"))

            # 4.2 即使有 xhs_src 参数，非 XHS 平台（wechat）也不得使用 xhs_src 或 XHS 默认
            xhs_file = tmp_path / "custom_xhs.png"
            xhs_file.write_bytes(b"xhs")
            resolved_wx_with_xhs = resolve_source_asset_for_platform("wechat", xhs_src=str(xhs_file))
            self.assertEqual(resolved_wx_with_xhs, default_hero)
            self.assertNotEqual(resolved_wx_with_xhs, xhs_file)

            # 4.3 即使 brief 中有 xhs_src，wechat 也不得落到 xhs_src 或 XHS 默认
            resolved_wx_brief = resolve_source_asset_for_platform("wechat", brief={"xhs_src": str(xhs_file)})
            self.assertEqual(resolved_wx_brief, default_hero)
            self.assertNotEqual(resolved_wx_brief, xhs_file)

            # 4.4 平台 "all" 默认兜底为 wechat 源，不错误落到 XHS
            resolved_all = resolve_source_asset_for_platform("all")
            self.assertEqual(resolved_all, default_hero)
            self.assertNotEqual(resolved_all, default_xhs)

    def test_resolve_source_asset_contract_5_dry_run_with_valid_source_no_output(self):
        """契约 5: 显式有效 source 的 dry-run 不因缺失默认素材失败且不创建最终输出。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            valid_source = tmp_path / "valid_subject.png"
            Image.new("RGB", (64, 64), color=(10, 20, 30)).save(valid_source, "PNG")

            # 确认平台默认素材不存在
            self.assertFalse((cover_pipeline.ASSETS_EXP / "_beauty_xhs.png").exists())

            # 5.1 generate_cover_subject 单元级演练：有效显式源顺利通过且不创建输出文件
            out_gen = tmp_path / "gen_dry_output.png"
            res = generate_cover_subject(
                prompt="test prompt for dry run",
                out_path=out_gen,
                dry_run=True,
                source_asset=valid_source,
            )
            self.assertTrue(res["ok"])
            self.assertTrue(res.get("dry_run"))
            self.assertEqual(res.get("size_kb"), 0)
            self.assertFalse(out_gen.exists())

            # 反向对照：未提供显式源且使用缺失的 XHS 默认素材时，dry-run 必然被 preflight 拦截
            res_fail = generate_cover_subject(
                prompt="test prompt for dry run",
                out_path=out_gen,
                dry_run=True,
                source_asset=resolve_source_asset_for_platform("xhs"),
            )
            self.assertFalse(res_fail["ok"])
            self.assertEqual(res_fail.get("error_class"), "MISSING_SOURCE_ASSET")
            self.assertFalse(out_gen.exists())

            # 5.2 真实 CLI dry-run 演练：brief 带有显式有效 source_asset
            brief_file = tmp_path / "brief_explicit.json"
            brief_file.write_text(json.dumps({
                "goal": "合约验证目标",
                "subject": "合约验证主体",
                "tone": "高雅",
                "mode": "diag",
                "platform": "xhs",
                "source_asset": str(valid_source),
            }, ensure_ascii=False), encoding="utf-8")
            target_out = cover_pipeline.OUT / "_gen_高雅_合约验证主体_合约验证目标_diag.png"
            target_out.unlink(missing_ok=True)
            try:
                cover_pipeline.main([
                    "--brief", str(brief_file), "--generate", "--dry-run",
                ])
                self.assertFalse(target_out.exists(), "Dry-run must not create the target output file")
            finally:
                target_out.unlink(missing_ok=True)

            # 5.3 真实 CLI dry-run 演练：通过 --xhs-src 传入显式有效 source
            brief_file_no_src = tmp_path / "brief_no_src.json"
            brief_file_no_src.write_text(json.dumps({
                "goal": "参数验证目标",
                "subject": "参数验证主体",
                "tone": "清丽",
                "mode": "diag",
                "platform": "xhs",
            }, ensure_ascii=False), encoding="utf-8")
            target_out_param = cover_pipeline.OUT / "_gen_清丽_参数验证主体_参数验证目标_diag.png"
            target_out_param.unlink(missing_ok=True)
            try:
                cover_pipeline.main([
                    "--brief", str(brief_file_no_src), "--xhs-src", str(valid_source),
                    "--generate", "--dry-run",
                ])
                self.assertFalse(target_out_param.exists(), "Dry-run with --xhs-src must not create output file")
            finally:
                target_out_param.unlink(missing_ok=True)

    def test_source_override_missing_path_reports_override_not_default(self):
        """显式 source 缺失时，错误必须指向显式路径而不是平台默认路径。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            explicit_missing = tmp_path / "provided-but-missing.png"
            resolved = resolve_source_asset_for_platform(
                "xhs", brief={"source_asset": str(explicit_missing)}
            )
            self.assertEqual(resolved, explicit_missing)
            result = preflight_source_asset(resolved)
            self.assertFalse(result["ok"])
            self.assertEqual(result["error_class"], "MISSING_SOURCE_ASSET")
            self.assertIn(str(explicit_missing), result["err"])
            self.assertNotIn("_beauty_xhs.png", result["err"])

    def test_source_override_dry_run_does_not_use_missing_xhs_default(self):
        """显式有效 source 的 dry-run 不应被缺失的 XHS 默认素材阻断。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            brief_file = tmp_path / "explicit_source.json"
            source_file = tmp_path / "source.png"
            Image.new("RGB", (32, 32), (255, 255, 255)).save(source_file)
            brief_file.write_text(json.dumps({
                "goal": "测试显式素材覆盖",
                "subject": "测试主体",
                "tone": "清晰",
                "mode": "diag",
                "platform": "xhs",
                "source_asset": str(source_file),
            }, ensure_ascii=False), encoding="utf-8")
            cover_pipeline.main([
                "--brief", str(brief_file), "--generate", "--dry-run",
            ])
            self.assertFalse((cover_pipeline.OUT / "_gen_清晰_测试主体_测试显式素材覆盖_diag.png").exists())

    def test_run_brief_batch_and_platform_preflight(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # 1. run_platform 入口前置校验
            non_existent = tmp_path / "does_not_exist.png"
            with self.assertRaisesRegex(SystemExit, "MISSING_SOURCE_ASSET"):
                run_platform("xhs", subject_src=non_existent)

            # 2. run_brief_batch 遇到缺失源素材时记录结构化报告而不是崩溃
            brief_file = tmp_path / "brief_missing.json"
            brief_file.write_text(
                json.dumps({
                    "goal": "时尚封面",
                    "subject": "东方面孔",
                    "tone": "冷艳",
                    "mode": "diag",
                    "source_asset": str(non_existent),
                }, ensure_ascii=False),
                encoding="utf-8",
            )
            reports = run_brief_batch(brief_file, platforms=["xhs", "wechat"])
            self.assertEqual(len(reports), 2)
            for r in reports:
                self.assertFalse(r["ok"])
                self.assertEqual(r["error_class"], "MISSING_SOURCE_ASSET")
                self.assertIn("does not exist", r["error"])

            # 3. run_brief_batch 遇到不存在的 brief 文件
            reports_no_brief = run_brief_batch(tmp_path / "non_existent_brief.json")
            self.assertEqual(len(reports_no_brief), 1)
            self.assertFalse(reports_no_brief[0]["ok"])
            self.assertEqual(reports_no_brief[0]["error_class"], "MISSING_BRIEF")
            self.assertIn("MISSING_BRIEF", reports_no_brief[0]["error"])

            # 4. run_brief_batch 遇到非法 json 的 brief 文件
            bad_brief = tmp_path / "corrupt_brief.json"
            bad_brief.write_text("{broken-json", encoding="utf-8")
            reports_bad_brief = run_brief_batch(bad_brief)
            self.assertEqual(len(reports_bad_brief), 1)
            self.assertFalse(reports_bad_brief[0]["ok"])
            self.assertEqual(reports_bad_brief[0]["error_class"], "INVALID_BRIEF")

            # 5. run_brief_batch 捕获 run_platform 门禁异常并结构化分类
            valid_src = tmp_path / "valid_subj.png"
            Image.new("RGB", (100, 100)).save(valid_src)
            brief_valid = tmp_path / "brief_valid.json"
            brief_valid.write_text(
                json.dumps({
                    "goal": "时尚封面",
                    "source_asset": str(valid_src),
                }, ensure_ascii=False),
                encoding="utf-8",
            )
            with patch("cover_pipeline.run_platform", side_effect=SystemExit("[head] face box clipped: {'y_min': 0.01}")):
                reports_head_fail = run_brief_batch(brief_valid, platforms=["xhs"])
                self.assertEqual(len(reports_head_fail), 1)
                self.assertFalse(reports_head_fail[0]["ok"])
                self.assertEqual(reports_head_fail[0]["error_class"], "QA_HEAD")
                self.assertIn("face box clipped", reports_head_fail[0]["error"])

            with patch("cover_pipeline.run_platform", side_effect=SystemExit("[sharpness] too soft, lap_mean=1.5")):
                reports_sharp_fail = run_brief_batch(brief_valid, platforms=["xhs"])
                self.assertEqual(len(reports_sharp_fail), 1)
                self.assertFalse(reports_sharp_fail[0]["ok"])
                self.assertEqual(reports_sharp_fail[0]["error_class"], "QA_SHARPNESS")

            with patch("cover_pipeline.run_platform", side_effect=RuntimeError("unexpected canvas crash")):
                reports_err = run_brief_batch(brief_valid, platforms=["xhs"])
                self.assertEqual(len(reports_err), 1)
                self.assertFalse(reports_err[0]["ok"])
                self.assertEqual(reports_err[0]["error_class"], "pipeline_error")

            # 6. run_platform 成功返回值必须具备 ok: True 结构化契约
            fake_success_report = {"platform": "xhs", "label": "小红书", "ok": True}
            with patch("cover_pipeline.run_platform", return_value=fake_success_report):
                reports_ok = run_brief_batch(brief_valid, platforms=["xhs"])
                self.assertEqual(len(reports_ok), 1)
                self.assertTrue(reports_ok[0]["ok"])
                self.assertEqual(reports_ok[0]["platform"], "xhs")


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

    def test_check_occlusion_inverted_box_coordinates(self):
        # 颠倒的左/右或上/下坐标自动规整
        inverted_box = (0.55, 0.55, 0.35, 0.38)
        hit, zone = check_occlusion(inverted_box, [self.sample_zone])
        self.assertTrue(hit)
        self.assertEqual(zone, self.sample_zone)

    def test_check_occlusion_sequence_zone(self):
        # 支持元组或列表格式的保护区
        tuple_zone = (0.40, 0.40, 0.60, 0.60)
        text_box = (0.35, 0.38, 0.55, 0.55)
        hit, zone = check_occlusion(text_box, [tuple_zone])
        self.assertTrue(hit)
        self.assertEqual(zone, tuple_zone)

    def test_check_occlusion_custom_padding(self):
        # 原本在默认缓冲区内 (y_min 0.40 - 0.05 = 0.35, 文字框底部 0.37)
        buffered_box = (0.42, 0.20, 0.58, 0.37)
        # 零 padding 时不触发碰撞
        hit_zero, _ = check_occlusion(buffered_box, [self.sample_zone], padding=0.0)
        self.assertFalse(hit_zero)
        # 字典自定义 top padding 扩大保护范围
        hit_custom, zone_custom = check_occlusion(buffered_box, [self.sample_zone], padding={"top": 0.08})
        self.assertTrue(hit_custom)
        self.assertEqual(zone_custom, self.sample_zone)

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
                 patch("agnes_engine.detect_visual_subjects", return_value=mock_boxes):
                detected = detect_faces(str(tmp_img))
                self.assertEqual(detected, mock_boxes)

    def test_detect_faces_fallback_forwards_options(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_img = Path(tmpdir) / "face_opts.png"
            Image.new("RGB", (100, 100), color=(50, 50, 50)).save(tmp_img, "PNG")

            with patch("shutil.which", return_value=None), \
                 patch("agnes_engine.detect_visual_subjects", return_value=[{"x_min": 0.1}]) as mock_detect:
                res = detect_faces(
                    str(tmp_img),
                    base_url="http://custom.example.com/v1",
                    api_key="sk-test-vis",
                    trace_id="vis-trace-123",
                    key_path="/path/to/key.json",
                )
                self.assertEqual(len(res), 1)
                mock_detect.assert_called_once_with(
                    str(tmp_img.resolve()),
                    base_url="http://custom.example.com/v1",
                    api_key="sk-test-vis",
                    trace_id="vis-trace-123",
                    key_path="/path/to/key.json",
                )

    def test_detect_faces_fallback_handles_exception_gracefully(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_img = Path(tmpdir) / "face_err.png"
            Image.new("RGB", (100, 100), color=(50, 50, 50)).save(tmp_img, "PNG")

            with patch("shutil.which", return_value=None), \
                 patch("agnes_engine.detect_visual_subjects", side_effect=RuntimeError("gateway unavailable")):
                res = detect_faces(str(tmp_img))
                self.assertEqual(res, [])

    def test_cli_main_default_target(self):
        with patch("vision_subject_detector.detect_faces", return_value=[{"x_min": 0.2}]) as mock_detect:
            with patch("pathlib.Path.is_file", return_value=True):
                code = vision_detector_main(["--quiet"])
                self.assertEqual(code, 0)
                mock_detect.assert_called_once()

    def test_cli_main_missing_image_returns_error_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_img = Path(tmpdir) / "not_there.png"
            code = vision_detector_main(["--image", str(missing_img), "--quiet"])
            self.assertEqual(code, 1)

    def test_cli_main_with_out_and_json(self):
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_img = Path(tmpdir) / "face.png"
            Image.new("RGB", (100, 100), color=(10, 10, 10)).save(tmp_img, "PNG")
            out_json = Path(tmpdir) / "sub" / "report.json"
            mock_faces = [{"x_min": 0.4, "x_max": 0.6, "y_min": 0.4, "y_max": 0.6}]

            buf = io.StringIO()
            with patch("vision_subject_detector.detect_faces", return_value=mock_faces), \
                 redirect_stdout(buf):
                code = vision_detector_main([
                    "--image", str(tmp_img),
                    "--out", str(out_json),
                    "--json",
                    "--quiet",
                ])

            self.assertEqual(code, 0)
            self.assertTrue(out_json.exists())
            data = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertTrue(data["exists"])
            self.assertEqual(data["subjects_count"], 1)
            self.assertEqual(data["subjects"], mock_faces)

            # verify json was also printed to stdout
            stdout_data = json.loads(buf.getvalue().strip())
            self.assertEqual(stdout_data["subjects_count"], 1)

    def test_cli_main_with_box_no_occlusion(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_img = Path(tmpdir) / "face.png"
            Image.new("RGB", (100, 100), color=(10, 10, 10)).save(tmp_img, "PNG")
            out_json = Path(tmpdir) / "report.json"
            mock_faces = [{"x_min": 0.4, "x_max": 0.6, "y_min": 0.4, "y_max": 0.6}]

            with patch("vision_subject_detector.detect_faces", return_value=mock_faces):
                code = vision_detector_main([
                    "--image", str(tmp_img),
                    "--out", str(out_json),
                    "--box", "0.05", "0.05", "0.25", "0.25",
                    "--strict",
                    "--quiet",
                ])

            self.assertEqual(code, 0)
            data = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertIn("occlusion", data)
            self.assertFalse(data["occlusion"]["has_occlusion"])
            self.assertIsNone(data["occlusion"]["conflicting_zone"])

    def test_cli_main_strict_occlusion_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_img = Path(tmpdir) / "face.png"
            Image.new("RGB", (100, 100), color=(10, 10, 10)).save(tmp_img, "PNG")
            mock_faces = [{"x_min": 0.4, "x_max": 0.6, "y_min": 0.4, "y_max": 0.6}]

            with patch("vision_subject_detector.detect_faces", return_value=mock_faces):
                # non-strict mode: warns but returns 0
                code_non_strict = vision_detector_main([
                    "--image", str(tmp_img),
                    "--box", "0.35", "0.38", "0.55", "0.55",
                    "--quiet",
                ])
                self.assertEqual(code_non_strict, 0)

                # strict mode: occlusion causes exit code 1
                code_strict = vision_detector_main([
                    "--image", str(tmp_img),
                    "--box", "0.35", "0.38", "0.55", "0.55",
                    "--strict",
                    "--quiet",
                ])
                self.assertEqual(code_strict, 1)

    def test_cli_main_require_subject(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_img = Path(tmpdir) / "face.png"
            Image.new("RGB", (100, 100), color=(10, 10, 10)).save(tmp_img, "PNG")

            # 0 faces with require-subject returns 1
            with patch("vision_subject_detector.detect_faces", return_value=[]):
                code_empty = vision_detector_main([
                    "--image", str(tmp_img),
                    "--require-subject",
                    "--quiet",
                ])
                self.assertEqual(code_empty, 1)

            # 1 face with require-subject returns 0
            with patch("vision_subject_detector.detect_faces", return_value=[{"x_min": 0.5}]):
                code_ok = vision_detector_main([
                    "--image", str(tmp_img),
                    "--require-subject",
                    "--quiet",
                ])
                self.assertEqual(code_ok, 0)

    def test_cli_main_quiet_mode_suppresses_stdout(self):
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_img = Path(tmpdir) / "face.png"
            Image.new("RGB", (100, 100), color=(10, 10, 10)).save(tmp_img, "PNG")

            buf = io.StringIO()
            with patch("vision_subject_detector.detect_faces", return_value=[]), \
                 redirect_stdout(buf):
                code = vision_detector_main(["--image", str(tmp_img), "--quiet"])

            self.assertEqual(code, 0)
            self.assertEqual(buf.getvalue().strip(), "")

    def test_vision_detector_build_arg_parser(self):
        parser = vision_detector_build_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        args = parser.parse_args([
            "--image", "test.png",
            "--out", "out.json",
            "--box", "0.1", "0.2", "0.3", "0.4",
            "--padding", "0.05",
            "--json",
            "--quiet",
            "--require-subject",
            "--strict",
            "--base-url", "https://api.example.com",
            "--api-key", "sk-123",
            "--trace-id", "trace-abc",
            "--key-path", "keys/test.key",
        ])
        self.assertEqual(args.image, "test.png")
        self.assertEqual(args.out, "out.json")
        self.assertEqual(args.box, [0.1, 0.2, 0.3, 0.4])
        self.assertEqual(args.padding, 0.05)
        self.assertTrue(args.json)
        self.assertTrue(args.quiet)
        self.assertTrue(args.require_subject)
        self.assertTrue(args.strict)
        self.assertEqual(args.base_url, "https://api.example.com")
        self.assertEqual(args.api_key, "sk-123")
        self.assertEqual(args.trace_id, "trace-abc")
        self.assertEqual(args.key_path, "keys/test.key")

    def test_cli_main_missing_image_json_output(self):
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_img = Path(tmpdir) / "not_there.png"
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = vision_detector_main(["--image", str(missing_img), "--json"])
            self.assertEqual(code, 1)
            raw = buf.getvalue().strip()
            data = json.loads(raw)
            self.assertFalse(data["ok"])
            self.assertFalse(data["exists"])
            self.assertIn("error", data)
            self.assertEqual(data["image"], str(missing_img.resolve()))

    def test_cli_main_out_and_json_without_quiet_no_pollution(self):
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_img = Path(tmpdir) / "face.png"
            Image.new("RGB", (100, 100), color=(10, 10, 10)).save(tmp_img, "PNG")
            out_json = Path(tmpdir) / "sub" / "report.json"
            mock_faces = [{"x_min": 0.4, "x_max": 0.6, "y_min": 0.4, "y_max": 0.6}]

            buf = io.StringIO()
            with patch("vision_subject_detector.detect_faces", return_value=mock_faces), \
                 redirect_stdout(buf):
                # Notice: --quiet is NOT passed, but stdout must remain pure JSON
                code = vision_detector_main([
                    "--image", str(tmp_img),
                    "--out", str(out_json),
                    "--json",
                ])

            self.assertEqual(code, 0)
            self.assertTrue(out_json.exists())
            raw = buf.getvalue().strip()
            # Must parse as valid JSON without extra text lines
            data = json.loads(raw)
            self.assertTrue(data["ok"])
            self.assertTrue(data["exists"])
            self.assertEqual(data["subjects_count"], 1)

    def test_cli_main_success_json_has_ok_flag(self):
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_img = Path(tmpdir) / "face.png"
            Image.new("RGB", (100, 100), color=(10, 10, 10)).save(tmp_img, "PNG")
            mock_faces = [{"x_min": 0.3, "x_max": 0.7, "y_min": 0.2, "y_max": 0.8}]

            buf = io.StringIO()
            with patch("vision_subject_detector.detect_faces", return_value=mock_faces), \
                 redirect_stdout(buf):
                code = vision_detector_main(["--image", str(tmp_img), "--json"])

            self.assertEqual(code, 0)
            data = json.loads(buf.getvalue().strip())
            self.assertTrue(data["ok"])
            self.assertEqual(data["subjects_count"], 1)

    def test_cli_main_runtime_exception_json_output(self):
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_img = Path(tmpdir) / "face.png"
            Image.new("RGB", (100, 100), color=(10, 10, 10)).save(tmp_img, "PNG")

            buf = io.StringIO()
            with patch("vision_subject_detector.detect_faces", side_effect=RuntimeError("GPU memory explosion")), \
                 redirect_stdout(buf):
                code = vision_detector_main(["--image", str(tmp_img), "--json"])

            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue().strip())
            self.assertFalse(data["ok"])
            self.assertIn("GPU memory explosion", data["error"])

    def test_cli_main_missing_image_stderr_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_img = Path(tmpdir) / "not_there.png"
            buf = io.StringIO()
            with redirect_stderr(buf):
                code = vision_detector_main(["--image", str(missing_img)])
            self.assertEqual(code, 1)
            self.assertIn(f"❌ 找不到目标图片文件: {missing_img}", buf.getvalue())

    def test_cli_main_missing_image_quiet_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_img = Path(tmpdir) / "not_there.png"
            err_buf = io.StringIO()
            out_buf = io.StringIO()
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = vision_detector_main(["--image", str(missing_img), "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")

    def test_cli_main_runtime_exception_stderr_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_img = Path(tmpdir) / "face.png"
            Image.new("RGB", (100, 100), color=(10, 10, 10)).save(tmp_img, "PNG")

            buf = io.StringIO()
            with patch("vision_subject_detector.detect_faces", side_effect=RuntimeError("Detector engine failure")), \
                 redirect_stderr(buf):
                code = vision_detector_main(["--image", str(tmp_img)])

            self.assertEqual(code, 1)
            self.assertIn("❌ 视觉主体与避障检测异常: Detector engine failure", buf.getvalue())

    def test_cli_main_runtime_exception_quiet_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_img = Path(tmpdir) / "face.png"
            Image.new("RGB", (100, 100), color=(10, 10, 10)).save(tmp_img, "PNG")

            err_buf = io.StringIO()
            out_buf = io.StringIO()
            with patch("vision_subject_detector.detect_faces", side_effect=RuntimeError("Silent failure")), \
                 redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = vision_detector_main(["--image", str(tmp_img), "--quiet"])

            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")



class TestFilmCoverEngine(unittest.TestCase):
    """测试电影感封面排版引擎 (Cinematic Cover Engine)"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.dummy_bg = self.tmp_path / "dummy_bg.png"
        Image.new("RGB", (600, 600), color=(30, 45, 60)).save(self.dummy_bg, "PNG")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_render_all_five_styles(self):
        styles = [
            ("capsule_green.png", render_shusheng_capsule_green),
            ("split_red.png", render_shusheng_split_red),
            ("side_yellow.png", render_shusheng_side_yellow),
            ("top_green.png", render_shusheng_top_green),
            ("letterbox.png", render_shusheng_letterbox),
        ]
        for filename, render_fn in styles:
            out_file = self.tmp_path / filename
            ret = render_fn(self.dummy_bg, out_file)
            self.assertEqual(ret, str(out_file))
            self.assertTrue(out_file.exists())
            with Image.open(out_file) as im:
                self.assertEqual(im.size, (600, 600))
                self.assertEqual(im.mode, "RGB")

    def test_input_guards(self):
        out_file = self.tmp_path / "out.png"

        # 背景图为空或不存在
        with self.assertRaises(ValueError):
            render_shusheng_capsule_green("", out_file)
        with self.assertRaises(ValueError):
            render_shusheng_capsule_green(None, out_file)
        with self.assertRaises(FileNotFoundError):
            render_shusheng_capsule_green(self.tmp_path / "non_existent.png", out_file)

        # 输出路径为空
        with self.assertRaises(ValueError):
            render_shusheng_capsule_green(self.dummy_bg, "")
        with self.assertRaises(ValueError):
            render_shusheng_capsule_green(self.dummy_bg, None)

    def test_auto_create_output_directory(self):
        nested_out = self.tmp_path / "sub" / "deep" / "letterbox_test.png"
        ret = render_shusheng_letterbox(self.dummy_bg, nested_out)
        self.assertEqual(ret, str(nested_out))
        self.assertTrue(nested_out.exists())

    def test_none_string_fallbacks(self):
        # 传递 None 文本不会触发 TypeError，安全回退为空文本
        out_file = self.tmp_path / "none_strings.png"
        ret = render_shusheng_capsule_green(
            self.dummy_bg,
            out_file,
            title=None,
            sub_1=None,
            sub_2=None,
            author_en=None,
            author_cn=None,
        )
        self.assertTrue(Path(ret).exists())

    def test_render_styles_quiet_mode(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret1 = render_shusheng_capsule_green(self.dummy_bg, self.tmp_path / "q1.png", quiet=True)
            ret2 = render_shusheng_split_red(self.dummy_bg, self.tmp_path / "q2.png", quiet=True)
            ret3 = render_shusheng_side_yellow(self.dummy_bg, self.tmp_path / "q3.png", quiet=True)
            ret4 = render_shusheng_top_green(self.dummy_bg, self.tmp_path / "q4.png", quiet=True)
            ret5 = render_shusheng_letterbox(self.dummy_bg, self.tmp_path / "q5.png", quiet=True)
        self.assertEqual(buf.getvalue().strip(), "")
        for ret in (ret1, ret2, ret3, ret4, ret5):
            self.assertTrue(Path(ret).exists())

    def test_list_and_render_film_cover_style(self):
        styles = list_film_cover_styles()
        self.assertEqual(len(styles), 5)
        keys = {s["key"] for s in styles}
        self.assertEqual(keys, {"capsule_green", "split_red", "side_yellow", "top_green", "letterbox"})

        out_path = self.tmp_path / "dispatch_test.png"
        res = render_film_cover_style(
            style="split_red",
            bg_image_path=self.dummy_bg,
            output_path=out_path,
            title="铜钟蒸汽",
            quiet=True,
        )
        self.assertEqual(res, str(out_path))
        self.assertTrue(out_path.exists())

        with self.assertRaises(KeyError):
            render_film_cover_style("unknown_style", self.dummy_bg, out_path)

    def test_cli_main_list_mode(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = film_cover_main(["--list"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Agnes Studio 可用电影感封面版式:", out)
        self.assertIn("capsule_green", out)
        self.assertIn("letterbox", out)

    def test_cli_main_single_style_with_custom_src_and_out(self):
        out_file = self.tmp_path / "cli_single.png"
        code = film_cover_main([
            "--style", "top_green",
            "--src", str(self.dummy_bg),
            "--out", str(out_file),
            "--title", "测试电影感标题",
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertTrue(out_file.exists())

    def test_cli_main_all_mode(self):
        out_base = self.tmp_path / "bundle.png"
        code = film_cover_main([
            "--style", "all",
            "--src", str(self.dummy_bg),
            "--out", str(out_base),
            "--quiet",
        ])
        self.assertEqual(code, 0)
        for st in FILM_COVER_STYLES.keys():
            expected_file = self.tmp_path / f"bundle_{st}.png"
            self.assertTrue(expected_file.exists(), f"Missing output: {expected_file}")

    def test_cli_main_missing_src_strict_mode(self):
        missing_src = self.tmp_path / "does_not_exist.png"
        code = film_cover_main([
            "--style", "letterbox",
            "--src", str(missing_src),
            "--strict",
            "--quiet",
        ])
        self.assertEqual(code, 1)

        code_lenient = film_cover_main([
            "--style", "letterbox",
            "--src", str(missing_src),
            "--quiet",
        ])
        self.assertEqual(code_lenient, 0)

    def test_cli_main_quiet_mode_suppresses_stdout(self):
        from contextlib import redirect_stdout

        out_file = self.tmp_path / "quiet_cli.png"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = film_cover_main([
                "--style", "side_yellow",
                "--src", str(self.dummy_bg),
                "--out", str(out_file),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertTrue(out_file.exists())
        self.assertEqual(buf.getvalue().strip(), "")

    def test_build_arg_parser(self):
        parser = build_film_cover_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        parsed = parser.parse_args(["--style", "capsule_green", "--json", "-q", "--strict"])
        self.assertEqual(parsed.style, "capsule_green")
        self.assertTrue(parsed.json)
        self.assertTrue(parsed.quiet)
        self.assertTrue(parsed.strict)

    def test_cli_main_list_json(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = film_cover_main(["--list", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue().strip())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 5)
        keys = [item["key"] for item in data]
        self.assertEqual(keys, ["capsule_green", "split_red", "side_yellow", "top_green", "letterbox"])
        for item in data:
            self.assertIn("name", item)
            self.assertIn("default_file", item)

    def test_cli_main_single_style_json(self):
        from contextlib import redirect_stdout

        out_file = self.tmp_path / "cli_json_single.png"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = film_cover_main([
                "--style", "capsule_green",
                "--src", str(self.dummy_bg),
                "--out", str(out_file),
                "--json",
            ])
        self.assertEqual(code, 0)
        self.assertTrue(out_file.exists())
        report = json.loads(buf.getvalue().strip())
        self.assertTrue(report.get("ok"))
        self.assertEqual(report.get("total"), 1)
        self.assertEqual(report.get("styles"), ["capsule_green"])
        self.assertEqual(report.get("src"), str(self.dummy_bg))
        self.assertEqual(len(report.get("results", [])), 1)
        self.assertEqual(report["results"][0]["style"], "capsule_green")
        self.assertEqual(report["results"][0]["output"], str(out_file))

    def test_cli_main_all_mode_json(self):
        from contextlib import redirect_stdout

        out_base = self.tmp_path / "bundle_json.png"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = film_cover_main([
                "--style", "all",
                "--src", str(self.dummy_bg),
                "--out", str(out_base),
                "--json",
            ])
        self.assertEqual(code, 0)
        report = json.loads(buf.getvalue().strip())
        self.assertTrue(report.get("ok"))
        self.assertEqual(report.get("total"), 5)
        self.assertEqual(len(report.get("results", [])), 5)
        for st in FILM_COVER_STYLES.keys():
            expected = self.tmp_path / f"bundle_json_{st}.png"
            self.assertTrue(expected.exists())

    def test_cli_main_missing_src_json_error(self):
        from contextlib import redirect_stdout

        missing_src = self.tmp_path / "non_existent_img.png"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = film_cover_main([
                "--src", str(missing_src),
                "--json",
                "--strict",
            ])
        self.assertEqual(code, 1)
        err_report = json.loads(buf.getvalue().strip())
        self.assertFalse(err_report.get("ok"))
        self.assertIn("error", err_report)
        self.assertIn("找不到输入底图", err_report["error"])

    def test_cli_main_exception_json_error(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with patch("film_cover_engine.render_film_cover_style", side_effect=RuntimeError("Simulated cover render crash")):
            with redirect_stdout(buf):
                code = film_cover_main([
                    "--style", "top_green",
                    "--src", str(self.dummy_bg),
                    "--json",
                ])
        self.assertEqual(code, 1)
        err_report = json.loads(buf.getvalue().strip())
        self.assertFalse(err_report.get("ok"))
        self.assertIn("error", err_report)
        self.assertIn("Simulated cover render crash", err_report["error"])

    @patch("film_cover_engine.render_film_cover_style", side_effect=RuntimeError("Cover disk render error"))
    def test_main_cli_exception_stderr_output(self, mock_render):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = film_cover_main([
                "--style", "top_green",
                "--src", str(self.dummy_bg),
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 电影感封面排版失败: Cover disk render error", buf.getvalue())

    @patch("film_cover_engine.render_film_cover_style", side_effect=RuntimeError("Cover quiet render error"))
    def test_main_cli_exception_quiet_mode(self, mock_render):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            code = film_cover_main([
                "--style", "top_green",
                "--src", str(self.dummy_bg),
                "-q",
            ])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_main_cli_missing_src_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        missing_src = self.tmp_path / "non_existent_film_bg.png"
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = film_cover_main([
                "--style", "top_green",
                "--src", str(missing_src),
                "--strict",
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 找不到输入底图", buf.getvalue())

    def test_cli_list_exception_json_output(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("film_cover_engine.list_film_cover_styles", side_effect=RuntimeError("Film styles index corrupted")):
            with redirect_stdout(buf):
                code = film_cover_main(["--list", "--json"])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "Film styles index corrupted")

    def test_cli_list_exception_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("film_cover_engine.list_film_cover_styles", side_effect=RuntimeError("Film styles index corrupted")):
            with redirect_stderr(buf):
                code = film_cover_main(["--list"])
        self.assertEqual(code, 1)
        self.assertIn("❌ 电影感封面排版失败: Film styles index corrupted", buf.getvalue())

    def test_cli_list_exception_quiet_mode(self):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with patch("film_cover_engine.list_film_cover_styles", side_effect=RuntimeError("Film styles index corrupted")):
            with redirect_stdout(out_buf), redirect_stderr(err_buf):
                code = film_cover_main(["--list", "-q"])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")


class TestPosterComposer(unittest.TestCase):
    """测试商业海报合成引擎 (Poster Composer)"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.dummy_bg = self.tmp_path / "dummy_poster_bg.png"
        Image.new("RGB", (512, 512), color=(20, 30, 40)).save(self.dummy_bg, "PNG")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_render_all_font_styles(self):
        styles = ["wenkai", "smiley", "songti"]
        for style in styles:
            out_file = self.tmp_path / f"poster_{style}.png"
            ret = compose_commercial_poster(
                self.dummy_bg,
                out_file,
                font_style=style,
                main_title="测试标题",
                sub_title="TEST SUBTITLE",
                tagline="「 测试副标 」",
            )
            self.assertEqual(ret, str(out_file))
            self.assertTrue(out_file.exists())
            with Image.open(out_file) as im:
                self.assertEqual(im.size, (512, 512))
                self.assertEqual(im.mode, "RGB")

    def test_render_all_theme_colors(self):
        colors = ["amber_gold", "cyber_cyan", "pure_white", "unknown_fallback"]
        for color in colors:
            out_file = self.tmp_path / f"poster_{color}.png"
            ret = compose_commercial_poster(
                self.dummy_bg,
                out_file,
                theme_color=color,
                main_title="色彩测试",
            )
            self.assertEqual(ret, str(out_file))
            self.assertTrue(out_file.exists())

    def test_input_guards(self):
        out_file = self.tmp_path / "out.png"

        # 背景图为空或不存在
        with self.assertRaises(ValueError):
            compose_commercial_poster("", out_file)
        with self.assertRaises(ValueError):
            compose_commercial_poster(None, out_file)
        with self.assertRaises(FileNotFoundError):
            compose_commercial_poster(self.tmp_path / "non_existent.png", out_file)

        # 输出路径为空
        with self.assertRaises(ValueError):
            compose_commercial_poster(self.dummy_bg, "")
        with self.assertRaises(ValueError):
            compose_commercial_poster(self.dummy_bg, None)

    def test_auto_create_output_directory(self):
        nested_out = self.tmp_path / "deep" / "nested" / "poster.png"
        ret = compose_commercial_poster(self.dummy_bg, nested_out)
        self.assertEqual(ret, str(nested_out))
        self.assertTrue(nested_out.exists())

    def test_none_string_fallbacks(self):
        # 传递 None 字符串安全回退，不崩溃
        out_file = self.tmp_path / "none_strings_poster.png"
        ret = compose_commercial_poster(
            self.dummy_bg,
            out_file,
            font_style=None,
            main_title=None,
            sub_title=None,
            tagline=None,
            metadata_no=None,
            theme_color=None,
        )
        self.assertTrue(Path(ret).exists())

    def test_compose_commercial_poster_quiet_mode(self):
        import io
        from contextlib import redirect_stdout
        out_file = self.tmp_path / "quiet_poster.png"
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = compose_commercial_poster(self.dummy_bg, out_file, quiet=True)
        self.assertEqual(ret, str(out_file))
        self.assertTrue(out_file.exists())
        self.assertEqual(buf.getvalue().strip(), "")

    def test_cli_main_default_execution(self):
        out_file = self.tmp_path / "default_cli_poster.png"
        code = poster_composer_main([
            "--bg", str(self.dummy_bg),
            "--out", str(out_file),
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertTrue(out_file.exists())

    def test_cli_main_custom_arguments(self):
        out_file = self.tmp_path / "custom_cli_poster.png"
        code = poster_composer_main([
            "--bg", str(self.dummy_bg),
            "--out", str(out_file),
            "--font-style", "smiley",
            "--title", "极速测试",
            "--sub", "SPEED TEST",
            "--tagline", "「 追求极致性能与优雅美学 」",
            "--metadata", "ID-9999",
            "--theme-color", "cyber_cyan",
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertTrue(out_file.exists())
        with Image.open(out_file) as im:
            self.assertEqual(im.size, (512, 512))

    def test_cli_main_missing_bg_returns_error_code(self):
        missing_bg = self.tmp_path / "not_there.png"
        code = poster_composer_main([
            "--bg", str(missing_bg),
            "--out", str(self.tmp_path / "out.png"),
            "--quiet",
            "--strict",
        ])
        self.assertEqual(code, 1)

    def test_cli_main_all_styles_mode(self):
        out_base = self.tmp_path / "suite.png"
        code = poster_composer_main([
            "--bg", str(self.dummy_bg),
            "--out", str(out_base),
            "--all-styles",
            "--quiet",
        ])
        self.assertEqual(code, 0)
        for s in ["wenkai", "smiley", "songti"]:
            expected_file = self.tmp_path / f"suite_{s}.png"
            self.assertTrue(expected_file.exists(), f"Expected {expected_file} to exist")

    def test_cli_main_quiet_mode_suppresses_stdout(self):
        import io
        from contextlib import redirect_stdout
        out_file = self.tmp_path / "quiet_cli.png"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = poster_composer_main([
                "--bg", str(self.dummy_bg),
                "--out", str(out_file),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_build_arg_parser(self):
        parser = poster_composer_build_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("bg", actions)
        self.assertIn("out", actions)
        self.assertIn("font_style", actions)
        self.assertIn("title", actions)
        self.assertIn("sub", actions)
        self.assertIn("tagline", actions)
        self.assertIn("metadata", actions)
        self.assertIn("theme_color", actions)
        self.assertIn("all_styles", actions)
        self.assertIn("list_styles", actions)
        self.assertIn("json", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_list_font_styles_and_colors(self):
        styles = poster_composer_list_font_styles()
        self.assertIsInstance(styles, list)
        self.assertEqual(len(styles), 3)
        for s in styles:
            self.assertIn("key", s)
            self.assertIn("name", s)
            self.assertIn("font_file", s)
            self.assertIn("description", s)

        colors = poster_composer_list_theme_colors()
        self.assertIsInstance(colors, list)
        self.assertEqual(len(colors), 3)
        for c in colors:
            self.assertIn("key", c)
            self.assertIn("name", c)
            self.assertIn("title_rgb", c)
            self.assertIn("description", c)

    def test_cli_list_styles_plain(self):
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = poster_composer_main(["--list-styles"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Agnes Studio · 支持字体风格清单:", out)
        self.assertIn("wenkai", out)
        self.assertIn("smiley", out)
        self.assertIn("songti", out)
        self.assertIn("Agnes Studio · 支持配色主题清单:", out)
        self.assertIn("amber_gold", out)

    def test_cli_list_styles_json(self):
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = poster_composer_main(["--list-styles", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue().strip())
        self.assertIn("font_styles", data)
        self.assertIn("theme_colors", data)
        self.assertEqual(len(data["font_styles"]), 3)
        self.assertEqual(len(data["theme_colors"]), 3)

    def test_cli_main_json_output_single_style(self):
        import io
        from contextlib import redirect_stdout

        out_file = self.tmp_path / "cli_json_single.png"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = poster_composer_main([
                "--bg", str(self.dummy_bg),
                "--out", str(out_file),
                "--font-style", "wenkai",
                "--json",
            ])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue().strip())
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("total"), 1)
        self.assertEqual(data.get("styles"), ["wenkai"])
        self.assertEqual(len(data.get("results", [])), 1)
        res0 = data["results"][0]
        self.assertEqual(res0["style"], "wenkai")
        self.assertTrue(res0["ok"])
        self.assertTrue(out_file.exists())
        self.assertGreater(res0["bytes"], 0)

    def test_cli_main_json_output_all_styles(self):
        import io
        from contextlib import redirect_stdout

        out_base = self.tmp_path / "cli_json_all.png"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = poster_composer_main([
                "--bg", str(self.dummy_bg),
                "--out", str(out_base),
                "--all-styles",
                "--json",
            ])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue().strip())
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("total"), 3)
        self.assertEqual(data.get("styles"), ["wenkai", "smiley", "songti"])
        self.assertEqual(len(data.get("results", [])), 3)
        for r in data["results"]:
            self.assertTrue(r["ok"])
            self.assertTrue(Path(r["file"]).exists())
            self.assertGreater(r["bytes"], 0)

    def test_cli_main_missing_bg_json_error(self):
        import io
        from contextlib import redirect_stdout

        missing_bg = self.tmp_path / "non_existent_bg.png"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = poster_composer_main([
                "--bg", str(missing_bg),
                "--out", str(self.tmp_path / "out.png"),
                "--json",
            ])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertIn("error", data)
        self.assertIn("找不到可用背景底图", data["error"])

    def test_cli_main_render_exception_json_error(self):
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with patch("poster_composer.compose_commercial_poster", side_effect=RuntimeError("simulated render failure")):
            with redirect_stdout(buf):
                code = poster_composer_main([
                    "--bg", str(self.dummy_bg),
                    "--out", str(self.tmp_path / "out.png"),
                    "--json",
                ])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertIn("error", data)
        self.assertIn("simulated render failure", data["error"])

    @patch("poster_composer.compose_commercial_poster", side_effect=RuntimeError("Poster disk render error"))
    def test_main_cli_exception_stderr_output(self, mock_render):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = poster_composer_main([
                "--bg", str(self.dummy_bg),
                "--out", str(self.tmp_path / "out.png"),
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 商业海报渲染失败: Poster disk render error", buf.getvalue())

    @patch("poster_composer.compose_commercial_poster", side_effect=RuntimeError("Poster quiet render error"))
    def test_main_cli_exception_quiet_mode(self, mock_render):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            code = poster_composer_main([
                "--bg", str(self.dummy_bg),
                "--out", str(self.tmp_path / "out.png"),
                "-q",
            ])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_main_cli_missing_bg_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        missing_bg = self.tmp_path / "non_existent_poster_bg.png"
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = poster_composer_main([
                "--bg", str(missing_bg),
                "--out", str(self.tmp_path / "out.png"),
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 找不到可用背景底图", buf.getvalue())

    def test_cli_list_styles_exception_json_output(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("poster_composer.list_font_styles", side_effect=RuntimeError("Font styles index corrupted")):
            with redirect_stdout(buf):
                code = poster_composer_main(["--list-styles", "--json"])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "Font styles index corrupted")

    def test_cli_list_styles_exception_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("poster_composer.list_font_styles", side_effect=RuntimeError("Font styles index corrupted")):
            with redirect_stderr(buf):
                code = poster_composer_main(["--list-styles"])
        self.assertEqual(code, 1)
        self.assertIn("❌ 商业海报渲染失败: Font styles index corrupted", buf.getvalue())

    def test_cli_list_styles_exception_quiet_mode(self):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with patch("poster_composer.list_font_styles", side_effect=RuntimeError("Font styles index corrupted")):
            with redirect_stdout(out_buf), redirect_stderr(err_buf):
                code = poster_composer_main(["--list-styles", "-q"])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")


class TestExpertPosterDesigner(unittest.TestCase):
    """测试专家级动态海报排版引擎 (Expert Dynamic Poster Designer)"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.dummy_bg = self.tmp_path / "dummy_expert_bg.png"
        Image.new("RGB", (600, 600), color=(40, 50, 60)).save(self.dummy_bg, "PNG")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_render_steampunk_custom_paths(self):
        out_file = self.tmp_path / "steampunk_custom.png"
        ret = render_expert_steampunk_poster(self.dummy_bg, out_file)
        self.assertEqual(ret, str(out_file))
        self.assertTrue(out_file.exists())
        with Image.open(out_file) as im:
            self.assertEqual(im.size, (600, 600))
            self.assertEqual(im.mode, "RGB")

    def test_render_neochinese_custom_paths(self):
        out_file = self.tmp_path / "neochinese_custom.png"
        ret = render_expert_neochinese_poster(self.dummy_bg, out_file)
        self.assertEqual(ret, str(out_file))
        self.assertTrue(out_file.exists())
        with Image.open(out_file) as im:
            self.assertEqual(im.size, (600, 600))
            self.assertEqual(im.mode, "RGB")

    def test_missing_source_image(self):
        out_file = self.tmp_path / "out.png"
        with self.assertRaises(FileNotFoundError):
            render_expert_steampunk_poster(self.tmp_path / "missing.png", out_file)
        with self.assertRaises(FileNotFoundError):
            render_expert_neochinese_poster(self.tmp_path / "missing.png", out_file)

    def test_render_steampunk_and_neochinese_quiet_mode(self):
        import io
        from contextlib import redirect_stdout
        out_steam = self.tmp_path / "quiet_steam.png"
        out_neo = self.tmp_path / "quiet_neo.png"

        buf = io.StringIO()
        with patch("expert_poster_designer.detect_faces", return_value=[]), \
             redirect_stdout(buf):
            render_expert_steampunk_poster(self.dummy_bg, out_steam, quiet=True)
            render_expert_neochinese_poster(self.dummy_bg, out_neo, quiet=True)

        self.assertTrue(out_steam.exists())
        self.assertTrue(out_neo.exists())
        self.assertEqual(buf.getvalue().strip(), "")

    def test_cli_main_steampunk_mode(self):
        out_file = self.tmp_path / "cli_steampunk.png"
        code = expert_designer_main([
            "--mode", "steampunk",
            "--src", str(self.dummy_bg),
            "--out", str(out_file),
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertTrue(out_file.exists())

    def test_cli_main_neochinese_mode(self):
        out_file = self.tmp_path / "cli_neochinese.png"
        code = expert_designer_main([
            "--mode", "neochinese",
            "--src", str(self.dummy_bg),
            "--out", str(out_file),
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertTrue(out_file.exists())

    def test_cli_main_all_mode(self):
        out_base = self.tmp_path / "bundle.png"
        code = expert_designer_main([
            "--mode", "all",
            "--src", str(self.dummy_bg),
            "--out", str(out_base),
            "--quiet",
        ])
        self.assertEqual(code, 0)
        steam_path = self.tmp_path / "bundle_steampunk.png"
        neo_path = self.tmp_path / "bundle_neochinese.png"
        self.assertTrue(steam_path.exists())
        self.assertTrue(neo_path.exists())

    def test_cli_main_missing_src_returns_error_code(self):
        missing_src = self.tmp_path / "missing_source.png"
        code = expert_designer_main([
            "--mode", "steampunk",
            "--src", str(missing_src),
            "--quiet",
            "--strict",
        ])
        self.assertEqual(code, 1)

    def test_cli_main_quiet_mode_suppresses_stdout(self):
        import io
        from contextlib import redirect_stdout
        out_file = self.tmp_path / "quiet_cli_steam.png"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = expert_designer_main([
                "--mode", "steampunk",
                "--src", str(self.dummy_bg),
                "--out", str(out_file),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_build_arg_parser(self):
        parser = expert_designer_build_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("mode", actions)
        self.assertIn("src", actions)
        self.assertIn("out", actions)
        self.assertIn("list_modes", actions)
        self.assertIn("json", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_list_expert_modes(self):
        modes = expert_designer_list_modes()
        self.assertIsInstance(modes, list)
        self.assertEqual(len(modes), 2)
        mode_keys = [m["mode"] for m in modes]
        self.assertIn("steampunk", mode_keys)
        self.assertIn("neochinese", mode_keys)
        for m in modes:
            self.assertIn("mode", m)
            self.assertIn("name", m)
            self.assertIn("description", m)
            self.assertIn("default_asset", m)
            self.assertIn("default_out", m)

    def test_cli_list_modes_plain(self):
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = expert_designer_main(["--list-modes"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Agnes Studio · 专家级动态海报排版模式清单:", out)
        self.assertIn("steampunk", out)
        self.assertIn("neochinese", out)

    def test_cli_list_modes_json(self):
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = expert_designer_main(["--list-modes", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue().strip())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        keys = [d["mode"] for d in data]
        self.assertIn("steampunk", keys)
        self.assertIn("neochinese", keys)

    def test_cli_main_json_output_single_mode(self):
        import io
        from contextlib import redirect_stdout

        out_file = self.tmp_path / "cli_json_steam.png"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = expert_designer_main([
                "--mode", "steampunk",
                "--src", str(self.dummy_bg),
                "--out", str(out_file),
                "--json",
            ])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue().strip())
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("total"), 1)
        self.assertEqual(data.get("mode"), "steampunk")
        self.assertEqual(len(data.get("results", [])), 1)
        r0 = data["results"][0]
        self.assertEqual(r0["mode"], "steampunk")
        self.assertTrue(r0["ok"])
        self.assertTrue(out_file.exists())
        self.assertGreater(r0["bytes"], 0)

    def test_cli_main_json_output_all_mode(self):
        import io
        from contextlib import redirect_stdout

        out_base = self.tmp_path / "cli_json_bundle.png"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = expert_designer_main([
                "--mode", "all",
                "--src", str(self.dummy_bg),
                "--out", str(out_base),
                "--json",
            ])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue().strip())
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("total"), 2)
        self.assertEqual(data.get("mode"), "all")
        self.assertEqual(len(data.get("results", [])), 2)
        for r in data["results"]:
            self.assertTrue(r["ok"])
            self.assertTrue(Path(r["out"]).exists())
            self.assertGreater(r["bytes"], 0)

    def test_cli_main_missing_src_json_error(self):
        import io
        from contextlib import redirect_stdout

        missing_src = self.tmp_path / "non_existent_source.png"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = expert_designer_main([
                "--mode", "steampunk",
                "--src", str(missing_src),
                "--out", str(self.tmp_path / "out.png"),
                "--json",
            ])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertIn("error", data)
        self.assertIn("找不到可用背景底图", data["error"])

    def test_cli_main_render_exception_json_error(self):
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with patch("expert_poster_designer.render_expert_steampunk_poster", side_effect=RuntimeError("simulated expert failure")):
            with redirect_stdout(buf):
                code = expert_designer_main([
                    "--mode", "steampunk",
                    "--src", str(self.dummy_bg),
                    "--out", str(self.tmp_path / "out.png"),
                    "--json",
                    "--strict",
                ])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertIn("error", data)
        self.assertIn("simulated expert failure", data["error"])

    @patch("expert_poster_designer.render_expert_steampunk_poster", side_effect=RuntimeError("Expert disk render error"))
    def test_main_cli_exception_stderr_output(self, mock_render):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = expert_designer_main([
                "--mode", "steampunk",
                "--src", str(self.dummy_bg),
                "--out", str(self.tmp_path / "out.png"),
                "--strict",
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 专家级排版渲染异常 (steampunk): Expert disk render error", buf.getvalue())

    @patch("expert_poster_designer.render_expert_steampunk_poster", side_effect=RuntimeError("Expert quiet render error"))
    def test_main_cli_exception_quiet_mode(self, mock_render):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            code = expert_designer_main([
                "--mode", "steampunk",
                "--src", str(self.dummy_bg),
                "--out", str(self.tmp_path / "out.png"),
                "-q",
                "--strict",
            ])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_main_cli_missing_src_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        missing_src = self.tmp_path / "non_existent_expert_bg.png"
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = expert_designer_main([
                "--mode", "steampunk",
                "--src", str(missing_src),
                "--out", str(self.tmp_path / "out.png"),
                "--strict",
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 找不到可用背景底图", buf.getvalue())

    def test_cli_list_modes_exception_json_output(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("expert_poster_designer.list_expert_modes", side_effect=RuntimeError("Modes index corrupted")):
            with redirect_stdout(buf):
                code = expert_designer_main(["--list-modes", "--json"])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "Modes index corrupted")

    def test_cli_list_modes_exception_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("expert_poster_designer.list_expert_modes", side_effect=RuntimeError("Modes index corrupted")):
            with redirect_stderr(buf):
                code = expert_designer_main(["--list-modes"])
        self.assertEqual(code, 1)
        self.assertIn("❌ 专家级排版异常: Modes index corrupted", buf.getvalue())

    def test_cli_list_modes_exception_quiet_mode(self):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with patch("expert_poster_designer.list_expert_modes", side_effect=RuntimeError("Modes index corrupted")):
            with redirect_stdout(out_buf), redirect_stderr(err_buf):
                code = expert_designer_main(["--list-modes", "-q"])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")


class TestPosterVisualLearner(unittest.TestCase):
    """测试海报多模态视觉解构与设计自学习引擎 (Poster Visual Learner Engine)"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

        # 构造纯红色 400x400 方图
        self.square_img = self.tmp_path / "square_red.png"
        Image.new("RGB", (400, 400), color=(255, 0, 0)).save(self.square_img, "PNG")

        # 构造 1000x400 宽银幕图 (2.5:1)
        self.wide_img = self.tmp_path / "wide_blue.png"
        Image.new("RGB", (1000, 400), color=(0, 0, 255)).save(self.wide_img, "PNG")

        # 构造 RGBA 含 Alpha 通道图
        self.rgba_img = self.tmp_path / "rgba_sample.png"
        Image.new("RGBA", (300, 300), color=(0, 255, 0, 200)).save(self.rgba_img, "PNG")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_extract_missing_file_returns_none(self):
        missing = self.tmp_path / "non_existent.png"
        self.assertIsNone(extract_poster_features(missing))

    def test_extract_square_poster_features(self):
        feat = extract_poster_features(self.square_img)
        self.assertIsNotNone(feat)
        self.assertEqual(feat["filename"], "square_red.png")
        self.assertEqual(feat["dimensions"], "400x400")
        self.assertEqual(feat["aspect_ratio"], 1.0)
        self.assertEqual(feat["layout_category"], "加块绿 · 左右对角拆字法")
        self.assertTrue(len(feat["dominant_palette"]) >= 1)
        self.assertEqual(feat["dominant_palette"][0]["hex"], "#ff0000")
        self.assertEqual(feat["dominant_palette"][0]["rgb"], [255, 0, 0])
        self.assertEqual(len(feat["rules"]), 4)

    def test_extract_wide_poster_features(self):
        feat = extract_poster_features(self.wide_img)
        self.assertIsNotNone(feat)
        self.assertEqual(feat["filename"], "wide_blue.png")
        self.assertEqual(feat["dimensions"], "1000x400")
        self.assertEqual(feat["aspect_ratio"], 2.5)
        self.assertEqual(feat["layout_category"], "电影宽银幕上下遮幅 (2.35:1)")
        self.assertEqual(feat["dominant_palette"][0]["hex"], "#0000ff")

    def test_extract_rgba_poster_features_handles_alpha(self):
        feat = extract_poster_features(self.rgba_img)
        self.assertIsNotNone(feat)
        self.assertEqual(feat["filename"], "rgba_sample.png")
        self.assertEqual(feat["dimensions"], "300x300")
        self.assertEqual(feat["aspect_ratio"], 1.0)
        self.assertEqual(feat["dominant_palette"][0]["hex"], "#00ff00")

    def test_analyze_poster_visual_custom_destination(self):
        out_json = self.tmp_path / "sub" / "output_rules.json"
        results = analyze_poster_visual(
            target_files=[self.square_img, self.wide_img],
            output_path=out_json,
        )
        self.assertEqual(len(results), 2)
        self.assertTrue(out_json.is_file())
        loaded = json.loads(out_json.read_text(encoding="utf-8"))
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["filename"], "square_red.png")
        self.assertEqual(loaded[1]["filename"], "wide_blue.png")

    def test_analyze_poster_visual_preserves_curated_rules(self):
        out_json = self.tmp_path / "curated_rules.json"
        existing_data = [
            {
                "id": "grand-space-rule",
                "rule": "留白≥35%",
            },
            {
                "filename": "square_red.png",
                "dominant_palette": [{"hex": "#000000", "rgb": [0, 0, 0], "pixels": 1}],
            },
        ]
        out_json.write_text(json.dumps(existing_data, ensure_ascii=False, indent=2), encoding="utf-8")

        results = analyze_poster_visual(
            target_files=[self.square_img, self.wide_img],
            output_path=out_json,
        )
        self.assertEqual(len(results), 2)

        loaded = json.loads(out_json.read_text(encoding="utf-8"))
        self.assertEqual(loaded[0]["id"], "grand-space-rule")
        self.assertEqual(loaded[1]["filename"], "square_red.png")
        self.assertEqual(loaded[1]["dominant_palette"][0]["hex"], "#ff0000")
        self.assertEqual(loaded[2]["filename"], "wide_blue.png")

    def test_analyze_poster_visual_quiet_mode(self):
        import io
        from contextlib import redirect_stdout

        out_json = self.tmp_path / "quiet_rules.json"
        buf = io.StringIO()
        with redirect_stdout(buf):
            results = analyze_poster_visual(
                target_files=[self.square_img],
                output_path=out_json,
                quiet=True,
            )
        self.assertEqual(len(results), 1)
        self.assertEqual(buf.getvalue(), "")

    def test_cli_main_with_files_out_and_quiet(self):
        import io
        from contextlib import redirect_stdout

        out_json = self.tmp_path / "cli_rules.json"
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = poster_learner_main([
                "--files", str(self.square_img), str(self.wide_img),
                "--out", str(out_json),
                "--quiet",
            ])
        self.assertEqual(rc, 0)
        self.assertEqual(buf.getvalue(), "")
        self.assertTrue(out_json.is_file())
        loaded = json.loads(out_json.read_text(encoding="utf-8"))
        self.assertEqual(len(loaded), 2)

    def test_cli_main_strict_success(self):
        out_json = self.tmp_path / "strict_success.json"
        rc = poster_learner_main([
            "--files", str(self.square_img),
            "--out", str(out_json),
            "--strict",
            "--quiet",
        ])
        self.assertEqual(rc, 0)
        self.assertTrue(out_json.is_file())

    def test_cli_main_strict_failure_on_missing_file(self):
        missing = self.tmp_path / "not_there.png"
        out_json = self.tmp_path / "strict_fail.json"
        rc = poster_learner_main([
            "--files", str(self.square_img), str(missing),
            "--out", str(out_json),
            "--strict",
            "--quiet",
        ])
        self.assertEqual(rc, 1)

    def test_poster_learner_build_arg_parser(self):
        parser = poster_learner_build_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        args = parser.parse_args([
            "--files", "a.png", "b.png",
            "--out", "rules.json",
            "--quiet",
            "--json",
            "--strict",
        ])
        self.assertEqual(args.files, ["a.png", "b.png"])
        self.assertEqual(args.out, "rules.json")
        self.assertTrue(args.quiet)
        self.assertTrue(args.json)
        self.assertTrue(args.strict)

    def test_extract_poster_features_corrupted_file_returns_none(self):
        corrupt_file = self.tmp_path / "corrupt.png"
        corrupt_file.write_bytes(b"NOT_A_VALID_IMAGE_HEADER_DATA")
        res = extract_poster_features(corrupt_file)
        self.assertIsNone(res)

    def test_cli_main_json_mode_output(self):
        import io
        from contextlib import redirect_stdout

        out_json = self.tmp_path / "out_json_mode.json"
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = poster_learner_main([
                "--files", str(self.square_img), str(self.wide_img),
                "--out", str(out_json),
                "--json",
            ])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue().strip())
        self.assertTrue(data["ok"])
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["expected"], 2)
        self.assertEqual(len(data["results"]), 2)
        self.assertEqual(data["results"][0]["filename"], "square_red.png")

    def test_cli_main_json_mode_strict_failure(self):
        import io
        from contextlib import redirect_stdout

        missing = self.tmp_path / "missing_poster.png"
        out_json = self.tmp_path / "out_json_fail.json"
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = poster_learner_main([
                "--files", str(self.square_img), str(missing),
                "--out", str(out_json),
                "--json",
                "--strict",
            ])
        self.assertEqual(rc, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data["ok"])
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["expected"], 2)
        self.assertIn("error", data)
        self.assertIn("部分文件解构失败", data["error"])

    @patch("poster_visual_learner.analyze_poster_visual", side_effect=RuntimeError("Learner crash disk error"))
    def test_cli_main_exception_stderr_output(self, mock_analyze):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with redirect_stderr(buf):
            rc = poster_learner_main(["--files", str(self.square_img)])
        self.assertEqual(rc, 1)
        self.assertIn("❌ 海报视觉解构与学习失败: Learner crash disk error", buf.getvalue())

    @patch("poster_visual_learner.analyze_poster_visual", side_effect=RuntimeError("Learner json failure"))
    def test_cli_main_exception_json_output(self, mock_analyze):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = poster_learner_main(["--files", str(self.square_img), "--json"])
        self.assertEqual(rc, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"], "Learner json failure")

    @patch("poster_visual_learner.analyze_poster_visual", side_effect=RuntimeError("Quiet failure"))
    def test_cli_main_exception_quiet_mode(self, mock_analyze):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = poster_learner_main(["--files", str(self.square_img), "-q"])
        self.assertEqual(rc, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")


class TestWechatCoverAB(unittest.TestCase):
    """测试微信头图 2.35:1 对照实验与光栅化组件 (WeChat Cover A/B Suite)"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.dummy_src = self.tmp_path / "dummy_bg.png"
        Image.new("RGB", (1000, 1000), color=(50, 50, 50)).save(self.dummy_src, "PNG")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_env_constants(self):
        self.assertEqual(wechat_cover_ab.CHROME, resolve_chrome_path())
        self.assertEqual(wechat_cover_ab.FONTS, FONTS_DIR)
        self.assertEqual(wechat_cover_ab.ASSETS, ASSETS_DIR)
        self.assertEqual(wechat_cover_ab.W, 2350)
        self.assertEqual(wechat_cover_ab.H, 1000)
        self.assertEqual(wechat_cover_ab.RATIO, 2.35)

    def test_make_subject_crop_success_and_missing(self):
        dst = self.tmp_path / "nested" / "crop.png"
        res = wechat_cover_ab.make_subject_crop(self.dummy_src, dst)
        self.assertEqual(res, dst)
        self.assertTrue(dst.exists())
        with Image.open(dst) as im:
            self.assertEqual(im.size, (1000, int(round(1000 / 2.35))))

        missing = self.tmp_path / "missing.png"
        with self.assertRaises(FileNotFoundError):
            wechat_cover_ab.make_subject_crop(missing, dst)

    def test_save_q90_copy_success_and_missing(self):
        dst_jpg = self.tmp_path / "nested" / "export.jpg"
        res = wechat_cover_ab.save_q90_copy(self.dummy_src, dst_jpg)
        self.assertEqual(res, dst_jpg)
        self.assertTrue(dst_jpg.exists())
        with Image.open(dst_jpg) as im:
            self.assertEqual(im.format, "JPEG")
            self.assertEqual(im.size, (1000, 1000))

        missing = self.tmp_path / "missing.png"
        with self.assertRaises(FileNotFoundError):
            wechat_cover_ab.save_q90_copy(missing, dst_jpg)

    def test_simulate_wechat_reencode_success_and_missing(self):
        dst_reencode = self.tmp_path / "nested" / "sim.jpg"
        res = wechat_cover_ab.simulate_wechat_reencode(self.dummy_src, dst_reencode)
        self.assertEqual(res, dst_reencode)
        self.assertTrue(dst_reencode.exists())
        with Image.open(dst_reencode) as im:
            self.assertEqual(im.format, "JPEG")
            self.assertEqual(im.size, (1000, 1000))

        missing = self.tmp_path / "missing.png"
        with self.assertRaises(FileNotFoundError):
            wechat_cover_ab.simulate_wechat_reencode(missing, dst_reencode)

    def test_head_visible_probe_cases(self):
        # 1. 肤色充足测试图
        skin_img = self.tmp_path / "skin.png"
        Image.new("RGB", (500, 500), color=(180, 110, 80)).save(skin_img, "PNG")
        res_skin = wechat_cover_ab.head_visible_probe(skin_img)
        self.assertTrue(res_skin.endswith("(OK)"))

        # 2. 无肤色暗色测试图
        dark_img = self.tmp_path / "dark.png"
        Image.new("RGB", (500, 500), color=(10, 10, 10)).save(dark_img, "PNG")
        res_dark = wechat_cover_ab.head_visible_probe(dark_img)
        self.assertTrue(res_dark.endswith("(REVIEW)"))

        # 3. 不存在文件触发异常
        missing = self.tmp_path / "missing.png"
        with self.assertRaises(FileNotFoundError):
            wechat_cover_ab.head_visible_probe(missing)

    def test_cover_html_templates(self):
        html_top = wechat_cover_ab.cover_html("data:image/png;base64,TEST_DATA", title_top=True)
        self.assertIn("top:20%; left:6%;", html_top)
        self.assertIn("top:54%; left:6%;", html_top)
        self.assertIn("data:image/png;base64,TEST_DATA", html_top)
        self.assertIn("SmileySans", html_top)

        html_bot = wechat_cover_ab.cover_html("data:image/png;base64,TEST_DATA", title_top=False)
        self.assertIn("bottom:8%; left:6%;", html_bot)
        self.assertIn("bottom:28%; left:6%;", html_bot)

    def test_get_experiment_matrix(self):
        matrix = wechat_cover_ab.get_experiment_matrix()
        self.assertEqual(len(matrix), 6)
        ids = [item["id"] for item in matrix]
        self.assertIn("H1_top", ids)
        self.assertIn("H1_bot", ids)
        self.assertIn("H3_png", ids)
        self.assertIn("H3_jpg", ids)
        self.assertIn("H3_png_sim", ids)
        self.assertIn("H3_jpg_sim", ids)
        for item in matrix:
            self.assertIn("group", item)
            self.assertIn("name", item)
            self.assertIn("filename", item)
            self.assertIn("format", item)
            self.assertIn("description", item)

    def test_check_prerequisites(self):
        prereqs = wechat_cover_ab.check_prerequisites(self.dummy_src)
        self.assertTrue(prereqs["src_exists"])
        self.assertEqual(prereqs["src_path"], str(self.dummy_src))
        self.assertIn("font_exists", prereqs)
        self.assertIn("chrome_exists", prereqs)
        self.assertIn("playwright_available", prereqs)

        missing = self.tmp_path / "missing.png"
        missing_prereqs = wechat_cover_ab.check_prerequisites(missing)
        self.assertFalse(missing_prereqs["src_exists"])
        self.assertFalse(missing_prereqs["all_ok"])

    def test_build_arg_parser(self):
        parser = wechat_cover_ab.build_arg_parser()
        self.assertIsNotNone(parser)
        parsed_list = parser.parse_args(["--list"])
        self.assertTrue(parsed_list.list)
        parsed_check = parser.parse_args(["--check", "--strict"])
        self.assertTrue(parsed_check.check)
        self.assertTrue(parsed_check.strict)
        parsed_custom = parser.parse_args(["--src", "a.png", "-o", "/tmp/out", "--dry-run", "--json", "-q"])
        self.assertEqual(parsed_custom.src, "a.png")
        self.assertEqual(parsed_custom.out_dir, "/tmp/out")
        self.assertTrue(parsed_custom.dry_run)
        self.assertTrue(parsed_custom.json)
        self.assertTrue(parsed_custom.quiet)

    def test_run_wechat_cover_ab_dry_run(self):
        out_target = self.tmp_path / "dry_out"
        report = wechat_cover_ab.run_wechat_cover_ab(
            src=self.dummy_src,
            out_dir=out_target,
            dry_run=True,
            quiet=True,
        )
        self.assertTrue(report["ok"])
        self.assertTrue(report["dry_run"])
        self.assertEqual(report["artifacts_count"], 6)
        self.assertEqual(len(report["artifacts"]), 6)
        self.assertTrue((out_target / "_bg_subject_235x100.png").exists())
        # 在 dry-run 下不生成真实的 HTML 渲染海报或 README
        self.assertFalse((out_target / "README.md").exists())

    def test_run_wechat_cover_ab_custom_render_fn(self):
        out_target = self.tmp_path / "custom_render_out"

        def mock_render(html: str, out_p: Path | str, fmt: str = "png") -> Path:
            p = Path(out_p)
            p.parent.mkdir(parents=True, exist_ok=True)
            img = Image.new("RGB", (2350, 1000), color=(120, 60, 40))
            if fmt == "jpeg":
                img.save(p, "JPEG")
            else:
                img.save(p, "PNG")
            return p

        report = wechat_cover_ab.run_wechat_cover_ab(
            src=self.dummy_src,
            out_dir=out_target,
            dry_run=False,
            write_readme=True,
            render_fn=mock_render,
            quiet=True,
        )
        self.assertTrue(report["ok"])
        self.assertFalse(report["dry_run"])
        self.assertEqual(report["artifacts_count"], 6)
        self.assertTrue((out_target / "H1_title_top_safe.png").exists())
        self.assertTrue((out_target / "H1_title_bottom_risk.png").exists())
        self.assertTrue((out_target / "H3_export_png24.png").exists())
        self.assertTrue((out_target / "H3_export_jpeg_q90.jpg").exists())
        self.assertTrue((out_target / "H3_png24_after_wechat_sim.jpg").exists())
        self.assertTrue((out_target / "H3_jpeg_q90_after_wechat_sim.jpg").exists())
        self.assertTrue((out_target / "README.md").exists())

    def test_run_wechat_cover_ab_missing_src(self):
        missing = self.tmp_path / "not_found.png"
        with self.assertRaises(FileNotFoundError):
            wechat_cover_ab.run_wechat_cover_ab(src=missing, out_dir=self.tmp_path)

    def test_main_cli_list(self):
        with io.StringIO() as buf, redirect_stdout(buf):
            code = wechat_cover_ab.main(["--list"])
            self.assertEqual(code, 0)
            output = buf.getvalue()
            self.assertIn("H1/H3 微信头图对照实验清单", output)
            self.assertIn("H1_top", output)

        with io.StringIO() as buf, redirect_stdout(buf):
            code = wechat_cover_ab.main(["--list", "--json"])
            self.assertEqual(code, 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(len(data), 6)

    def test_main_cli_check(self):
        with io.StringIO() as buf, redirect_stdout(buf):
            code = wechat_cover_ab.main(["--check", "--src", str(self.dummy_src)])
            self.assertEqual(code, 0)
            self.assertIn("H1/H3 对照实验前置条件巡检", buf.getvalue())

        with io.StringIO() as buf, redirect_stdout(buf):
            code = wechat_cover_ab.main(["--check", "--src", str(self.dummy_src), "--json"])
            self.assertEqual(code, 0)
            data = json.loads(buf.getvalue())
            self.assertTrue(data["src_exists"])

        missing = self.tmp_path / "missing_bg.png"
        code_strict = wechat_cover_ab.main(["--check", "--src", str(missing), "--strict", "-q"])
        self.assertEqual(code_strict, 1)

    def test_main_cli_dry_run(self):
        target = self.tmp_path / "cli_dry_out"
        with io.StringIO() as buf, redirect_stdout(buf):
            code = wechat_cover_ab.main([
                "--dry-run",
                "--src", str(self.dummy_src),
                "--out-dir", str(target),
                "--json",
            ])
            self.assertEqual(code, 0)
            res = json.loads(buf.getvalue())
            self.assertTrue(res["ok"])
            self.assertTrue(res["dry_run"])
            self.assertEqual(res["artifacts_count"], 6)

    def test_main_cli_missing_src(self):
        missing = self.tmp_path / "missing_bg.png"
        code = wechat_cover_ab.main(["--src", str(missing), "--out-dir", str(self.tmp_path), "-q"])
        self.assertEqual(code, 1)

    @patch("wechat_cover_ab.run_wechat_cover_ab", side_effect=RuntimeError("Cover crash disk error"))
    def test_main_cli_exception_stderr_output(self, mock_run):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = wechat_cover_ab.main(["--src", str(self.dummy_src)])
        self.assertEqual(code, 1)
        self.assertIn("❌ 运行失败: Cover crash disk error", buf.getvalue())

    @patch("wechat_cover_ab.run_wechat_cover_ab", side_effect=RuntimeError("Cover json error"))
    def test_main_cli_exception_json_output(self, mock_run):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = wechat_cover_ab.main(["--src", str(self.dummy_src), "--json"])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"], "Cover json error")

    @patch("wechat_cover_ab.run_wechat_cover_ab", side_effect=RuntimeError("Cover quiet error"))
    def test_main_cli_exception_quiet_mode(self, mock_run):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            code = wechat_cover_ab.main(["--src", str(self.dummy_src), "-q"])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_cli_list_exception_json_output(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("wechat_cover_ab.get_experiment_matrix", side_effect=RuntimeError("Matrix index corrupted")):
            with redirect_stdout(buf):
                code = wechat_cover_ab.main(["--list", "--json"])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "Matrix index corrupted")

    def test_cli_list_exception_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("wechat_cover_ab.get_experiment_matrix", side_effect=RuntimeError("Matrix index corrupted")):
            with redirect_stderr(buf):
                code = wechat_cover_ab.main(["--list"])
        self.assertEqual(code, 1)
        self.assertIn("❌ 运行失败: Matrix index corrupted", buf.getvalue())

    def test_cli_list_exception_quiet_mode(self):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with patch("wechat_cover_ab.get_experiment_matrix", side_effect=RuntimeError("Matrix index corrupted")):
            with redirect_stdout(out_buf), redirect_stderr(err_buf):
                code = wechat_cover_ab.main(["--list", "-q"])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")


class TestAgnesGateway(unittest.TestCase):
    """测试 Agnes 生图网关与本地轮换机制 (Agnes Gateway Suite)"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_generate_image_route_prefers_image_base_url(self):
        cfg = {"base_url": "http://old-base/v1", "image_base_url": "http://image-base/v1"}
        default_base = cfg.get("image_base_url") or cfg.get("base_url") or "http://127.0.0.1:13000/v1"
        self.assertEqual(default_base, "http://image-base/v1")

    def test_generate_image_route_accepts_explicit_base_url(self):
        cfg = {"base_url": "http://old-base/v1", "image_base_url": "http://image-base/v1"}
        request_base = "http://override/v1"
        default_base = cfg.get("image_base_url") or cfg.get("base_url") or "http://127.0.0.1:13000/v1"
        self.assertEqual(request_base or default_base, "http://override/v1")

    def test_generate_image_route_falls_back_to_base_url(self):
        cfg = {"base_url": "http://legacy-base/v1"}
        default_base = cfg.get("image_base_url") or cfg.get("base_url") or "http://127.0.0.1:13000/v1"
        self.assertEqual(default_base, "http://legacy-base/v1")

    def test_gateway_constants(self):
        self.assertEqual(agnes_gateway.DEFAULT_BASE, "http://127.0.0.1:13000/v1")
        self.assertEqual(agnes_gateway.DEFAULT_MODEL, "agnes-image-2.5-flash")

    def test_load_gateway_defaults(self):
        non_existent_key = self.tmp_path / "no_key.json"
        with patch.dict("os.environ", {}, clear=True):
            base, key, model = load_gateway(key_path=non_existent_key)
            self.assertEqual(base, "http://127.0.0.1:13000/v1")
            self.assertEqual(key, "")
            self.assertEqual(model, "agnes-image-2.5-flash")

    def test_load_gateway_prefers_image_base_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_file = Path(tmpdir) / "local_key.json"
            cfg_file.write_text(json.dumps({
                "base_url": "http://old.example/v1",
                "image_base_url": "http://image.example/v1",
                "api_key": "sk-test",
            }), encoding="utf-8")
            base, _, _ = load_gateway(key_path=cfg_file)
            self.assertEqual(base, "http://image.example/v1")

    def test_load_gateway_falls_back_to_base_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_file = Path(tmpdir) / "local_key.json"
            cfg_file.write_text(json.dumps({
                "base_url": "http://legacy.example/v1",
                "api_key": "sk-test",
            }), encoding="utf-8")
            base, _, _ = load_gateway(key_path=cfg_file)
            self.assertEqual(base, "http://legacy.example/v1")

    def test_load_gateway_from_json(self):
        cfg_file = self.tmp_path / "local_key.json"
        cfg_data = {
            "base_url": "http://192.168.1.100:3000/v1",
            "api_key": "sk-custom-token-12345",
            "models": {
                "image_generation": ["custom-flux-pro", "custom-agnes-2.5"]
            }
        }
        cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

        with patch.dict("os.environ", {}, clear=True):
            base, key, model = load_gateway(key_path=cfg_file)
            self.assertEqual(base, "http://192.168.1.100:3000/v1")
            self.assertEqual(key, "sk-custom-token-12345")
            self.assertEqual(model, "custom-flux-pro")

    def test_load_gateway_env_overrides(self):
        cfg_file = self.tmp_path / "local_key.json"
        cfg_file.write_text(json.dumps({"base_url": "http://10.0.0.1/v1", "api_key": "old-key"}), encoding="utf-8")

        env_vars = {
            "NEW_API_BASE_URL": "http://override-gateway:3000/v1",
            "NEW_API_KEY": "env-secret-key-999",
            "AGNES_IMAGE_MODEL": "agnes-ultra-hd",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            base, key, model = load_gateway(key_path=cfg_file)
            self.assertEqual(base, "http://override-gateway:3000/v1")
            self.assertEqual(key, "env-secret-key-999")
            self.assertEqual(model, "agnes-ultra-hd")

    def test_load_gateway_with_agnes_image_base_url(self):
        cfg_file = self.tmp_path / "local_key.json"
        cfg_file.write_text(json.dumps({"base_url": "http://10.0.0.1/v1"}), encoding="utf-8")
        env_vars = {
            "AGNES_IMAGE_BASE_URL": "http://image-priority.example/v1",
            "AGNES_BASE_URL": "http://agnes-base.example/v1",
            "NEW_API_BASE_URL": "http://new-api-base.example/v1",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            base, _, _ = load_gateway(key_path=cfg_file)
            self.assertEqual(base, "http://image-priority.example/v1")

    def test_load_gateway_with_agnes_gateway_key(self):
        cfg_file = self.tmp_path / "local_key.json"
        cfg_file.write_text(json.dumps({"api_key": "file-key"}), encoding="utf-8")
        # 1. 验证 AGNES_GATEWAY_KEY 优先于 NEW_API_KEY
        env_vars = {
            "AGNES_GATEWAY_KEY": "sk-gateway-key-priority",
            "NEW_API_KEY": "sk-new-api-key-lower",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            _, key, _ = load_gateway(key_path=cfg_file)
            self.assertEqual(key, "sk-gateway-key-priority")

        # 2. 验证 AGNES_API_KEY 具备最高优先级
        env_vars_top = {
            "AGNES_API_KEY": "sk-agnes-api-key-top",
            "AGNES_GATEWAY_KEY": "sk-gateway-key-priority",
            "NEW_API_KEY": "sk-new-api-key-lower",
        }
        with patch.dict("os.environ", env_vars_top, clear=True):
            _, key, _ = load_gateway(key_path=cfg_file)
            self.assertEqual(key, "sk-agnes-api-key-top")

    def test_classify_generation_error(self):
        self.assertEqual(gateway_classify_error("HTTP 502: Bad Gateway"), "gateway_502")
        self.assertEqual(gateway_classify_error("HTTP 401: Unauthorized"), "auth")
        self.assertEqual(gateway_classify_error("HTTP 403: Forbidden"), "auth")
        self.assertEqual(gateway_classify_error("token_rejected"), "auth")
        self.assertEqual(gateway_classify_error("Connection timed out"), "timeout")
        self.assertEqual(gateway_classify_error("generic prompt error"), "generation_error")

    def test_generate_invalid_prompt(self):
        res1 = generate("")
        self.assertFalse(res1["ok"])
        self.assertIn("non-empty string", res1["error"])
        self.assertEqual(res1.get("error_class"), "generation_error")

        res2 = generate("   \n\t  ")
        self.assertFalse(res2["ok"])
        self.assertEqual(res2.get("error_class"), "generation_error")

    def test_generate_dry_run(self):
        res = generate("Cyberpunk neon rain street", dry_run=True)
        self.assertTrue(res["ok"])
        self.assertTrue(res.get("dry_run"))
        self.assertEqual(res["cost_s"], 0.0)
        self.assertEqual(res["via"], "dry-run")
        self.assertIsNone(res["url"])
        self.assertIsNone(res["b64_json"])

    @patch("urllib.request.urlopen")
    def test_generate_success(self, mock_urlopen):
        fake_resp_data = {
            "data": [
                {
                    "url": "https://example.com/generated_artwork.png",
                    "b64_json": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                }
            ]
        }
        mock_resp = unittest.mock.MagicMock()
        mock_resp.read.return_value = json.dumps(fake_resp_data).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = generate("Cyberpunk neon rain street", retries=0)
        self.assertTrue(res["ok"])
        self.assertEqual(res["url"], "https://example.com/generated_artwork.png")
        self.assertEqual(res["attempt"], 1)
        self.assertEqual(res["via"], "new-api-rotation-pool")
        self.assertIn("b64_json", res)
        self.assertGreaterEqual(res["cost_s"], 0)

    @patch("time.sleep", return_value=None)
    @patch("urllib.request.urlopen")
    def test_generate_http_error_retry(self, mock_urlopen, mock_sleep):
        err = urllib.error.HTTPError(
            url="http://127.0.0.1:3000/v1/images/generations",
            code=502,
            msg="Bad Gateway",
            hdrs={},
            fp=io.BytesIO(b"gateway upstream timeout"),
        )
        mock_urlopen.side_effect = err

        res = generate("Test retry prompt", retries=1)
        self.assertFalse(res["ok"])
        self.assertIn("HTTP 502", res["error"])
        self.assertEqual(res.get("error_class"), "gateway_502")
        self.assertEqual(mock_urlopen.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("time.sleep", return_value=None)
    @patch("urllib.request.urlopen")
    def test_generate_auth_and_timeout_error_class(self, mock_urlopen, mock_sleep):
        err_auth = urllib.error.HTTPError(
            url="http://127.0.0.1:3000/v1/images/generations",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=io.BytesIO(b"token_rejected"),
        )
        mock_urlopen.side_effect = err_auth
        res_auth = generate("Test auth prompt", retries=0)
        self.assertFalse(res_auth["ok"])
        self.assertEqual(res_auth.get("error_class"), "auth")
        self.assertTrue(err_auth.fp.closed)

        mock_urlopen.side_effect = TimeoutError("Gateway request timed out")
        res_timeout = generate("Test timeout prompt", retries=0)
        self.assertFalse(res_timeout["ok"])
        self.assertEqual(res_timeout.get("error_class"), "timeout")

    def test_gateway_main_cli(self):
        out_file = self.tmp_path / "cli_test.png"
        # 1. 验证 --dry-run
        agnes_gateway.main(["--prompt", "test dry run", "--out", str(out_file), "--dry-run"])
        self.assertFalse(out_file.exists())

        # 2. 缺少 prompt 或 brief 时退出
        with self.assertRaises(SystemExit):
            agnes_gateway.main(["--out", str(out_file)])

        # 3. 失败时以 SystemExit 干净退出并打印分类错误
        with patch.object(agnes_gateway, "generate", return_value={"ok": False, "error": "HTTP 502 Bad Gateway", "error_class": "gateway_502"}):
            with self.assertRaises(SystemExit):
                agnes_gateway.main(["--prompt", "failing prompt", "--out", str(out_file)])

    def test_save_image_b64(self):
        out_file = self.tmp_path / "deep" / "folder" / "sample.png"
        raw_bytes = b"FAKE_PNG_BINARY_CONTENT_12345"
        import base64
        b64_payload = base64.b64encode(raw_bytes).decode("utf-8")

        res_dict = {"b64_json": b64_payload}
        saved_path = save_image(res_dict, out_file)

        self.assertEqual(saved_path, out_file)
        self.assertTrue(out_file.exists())
        self.assertEqual(out_file.read_bytes(), raw_bytes)

    def test_save_image_str_path(self):
        out_file_str = str(self.tmp_path / "str_path_test.png")
        raw_bytes = b"STR_PATH_CONTENT"
        import base64
        b64_payload = base64.b64encode(raw_bytes).decode("utf-8")

        saved_path = save_image({"b64_json": b64_payload}, out_file_str)
        self.assertEqual(saved_path, Path(out_file_str))
        self.assertEqual(Path(out_file_str).read_bytes(), raw_bytes)

    def test_save_image_corrupt_b64(self):
        out_file = self.tmp_path / "corrupt.png"
        with self.assertRaises(ValueError) as ctx:
            save_image({"b64_json": "!!!INVALID_BASE64_BYTES!!!"}, out_file)
        self.assertIn("invalid base64", str(ctx.exception).lower())

    def test_save_image_no_payload(self):
        out_file = self.tmp_path / "empty.png"
        with self.assertRaises(ValueError) as ctx:
            save_image({"status": "unknown"}, out_file)
        self.assertIn("no image payload", str(ctx.exception))

    @patch("urllib.request.urlretrieve")
    def test_save_image_url(self, mock_urlretrieve):
        out_file = self.tmp_path / "from_url.png"
        res_dict = {"url": "https://cdn.example.com/asset.png"}
        saved_path = save_image(res_dict, out_file)
        self.assertEqual(saved_path, out_file)
        mock_urlretrieve.assert_called_once_with("https://cdn.example.com/asset.png", str(out_file))


class TestUpstreamSentinel(unittest.TestCase):
    """测试生命周期巡检与上游依赖健康监控 (scripts/check_upstream_updates.py)"""

    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._temp_dir.name)

    def tearDown(self):
        self._temp_dir.cleanup()

    def test_get_local_auth_key_from_env(self):
        with patch.dict("os.environ", {"NEW_API_KEY": "sk-env-secret-123"}):
            self.assertEqual(get_local_auth_key(), "sk-env-secret-123")
        with patch.dict("os.environ", {"NEW_API_KEY": "", "AGNES_API_KEY": "sk-agnes-key-456"}):
            self.assertEqual(get_local_auth_key(), "sk-agnes-key-456")
        with patch.dict("os.environ", {"NEW_API_KEY": "", "AGNES_API_KEY": "", "AGNES_GATEWAY_KEY": "sk-gateway-789"}):
            self.assertEqual(get_local_auth_key(), "sk-gateway-789")

    def test_get_local_base_url_env_priority(self):
        env_vars = {
            "AGNES_IMAGE_BASE_URL": "http://img-sentinel.example/v1",
            "AGNES_BASE_URL": "http://agnes-sentinel.example/v1",
            "NEW_API_BASE_URL": "http://newapi-sentinel.example/v1",
            "AGNES_API_BASE": "http://agnes-legacy.example/v1",
            "NEW_API_BASE": "http://newapi-legacy.example/v1",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            self.assertEqual(get_local_base_url(), "http://img-sentinel.example/v1")
        with patch.dict("os.environ", {"AGNES_BASE_URL": "http://agnes-sentinel.example/v1"}, clear=True):
            self.assertEqual(get_local_base_url(), "http://agnes-sentinel.example/v1")
        with patch.dict("os.environ", {"AGNES_API_BASE": "http://agnes-legacy.example/v1"}, clear=True):
            self.assertEqual(get_local_base_url(), "http://agnes-legacy.example/v1")
        with patch.dict("os.environ", {"NEW_API_BASE": "http://newapi-legacy.example/v1"}, clear=True):
            self.assertEqual(get_local_base_url(), "http://newapi-legacy.example/v1")

    def test_get_local_base_url_from_file(self):
        key_file = self.tmp_path / "custom_base.json"
        key_file.write_text(json.dumps({"image_base_url": "http://file-img.example/v1"}), encoding="utf-8")
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(get_local_base_url(key_path=key_file), "http://file-img.example/v1")

    def test_get_local_auth_key_from_file(self):
        key_file = self.tmp_path / "test_key.json"
        key_file.write_text(json.dumps({"api_key": "sk-file-key-789"}), encoding="utf-8")
        with patch.dict("os.environ", {"NEW_API_KEY": "", "AGNES_API_KEY": ""}, clear=True):
            self.assertEqual(get_local_auth_key(key_path=key_file), "sk-file-key-789")

    def test_get_local_auth_key_fallback(self):
        invalid_file = self.tmp_path / "invalid.json"
        invalid_file.write_text("invalid json content", encoding="utf-8")
        with patch.dict("os.environ", {"NEW_API_KEY": "", "AGNES_API_KEY": ""}, clear=True):
            self.assertEqual(get_local_auth_key(key_path=invalid_file), "")
            self.assertEqual(get_local_auth_key(key_path=self.tmp_path / "missing.json"), "")

    @patch("urllib.request.urlopen")
    def test_check_new_api_health_success(self, mock_urlopen):
        mock_resp = unittest.mock.MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "data": [
                {"id": "agnes-image-2.5-flash"},
                {"id": "dall-e-3"},
                {"id": "gemini-2.5-flash"},
                {"id": "text-embedding-3-small"},
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = check_new_api_health(base_url="http://mock.gateway/v1", api_key="sk-test", timeout=3.0)
        self.assertEqual(res["status"], "healthy")
        self.assertEqual(res["available_models_count"], 4)
        self.assertIn("agnes-image-2.5-flash", res["image_models"])
        self.assertIn("dall-e-3", res["image_models"])
        self.assertNotIn("text-embedding-3-small", res["image_models"])
        self.assertIn("latency_ms", res)

    @patch("urllib.request.urlopen")
    def test_check_new_api_health_non_200(self, mock_urlopen):
        mock_resp = unittest.mock.MagicMock()
        mock_resp.status = 503
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = check_new_api_health(base_url="http://mock.gateway/v1", timeout=1.0)
        self.assertEqual(res["status"], "unhealthy")
        self.assertIn("HTTP 503", res["error"])

    @patch("urllib.request.urlopen")
    def test_check_new_api_health_http_error(self, mock_urlopen):
        err = urllib.error.HTTPError(
            url="http://mock.gateway/v1/models",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(b"unauthorized"),
        )
        mock_urlopen.side_effect = err
        res = check_new_api_health(base_url="http://mock.gateway/v1", timeout=1.0)
        self.assertEqual(res["status"], "unhealthy")
        self.assertIn("401", res["error"])
        self.assertTrue(err.fp.closed)

    @patch("urllib.request.urlopen")
    def test_check_new_api_health_invalid_json(self, mock_urlopen):
        mock_resp = unittest.mock.MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"<html>502 Bad Gateway</html>"
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = check_new_api_health(base_url="http://mock.gateway/v1", timeout=1.0)
        self.assertEqual(res["status"], "unhealthy")
        self.assertIn("Invalid JSON", res["error"])

    @patch("urllib.request.urlopen")
    def test_check_new_api_health_forwards_key_path(self, mock_urlopen):
        mock_resp = unittest.mock.MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"data": [{"id": "agnes-image-2.5-flash"}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        key_file = self.tmp_path / "custom_forward.json"
        key_file.write_text(json.dumps({
            "image_base_url": "http://10.99.0.1:13000/v1",
            "api_key": "sk-forward-key",
        }), encoding="utf-8")

        with patch.dict("os.environ", {}, clear=True):
            res = check_new_api_health(key_path=key_file, timeout=1.0)

        self.assertEqual(res["status"], "healthy")
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.full_url, "http://10.99.0.1:13000/v1/models")
        self.assertEqual(req.headers.get("Authorization"), "Bearer sk-forward-key")

    @patch("urllib.request.urlopen")
    def test_check_new_api_health_base_url_with_models(self, mock_urlopen):
        mock_resp = unittest.mock.MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"data": [{"id": "agnes-image-2.5-flash"}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = check_new_api_health(base_url="http://explicit.gateway/v1/models", api_key="sk-test", timeout=1.0)
        self.assertEqual(res["status"], "healthy")
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.full_url, "http://explicit.gateway/v1/models")

    @patch("urllib.request.urlopen")
    def test_check_github_repo_success(self, mock_urlopen):
        mock_resp = unittest.mock.MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "sha": "123456789abcdef",
            "commit": {
                "message": "feat: harden sentinel monitoring\n\nDetailed body",
                "author": {"date": "2026-09-26T21:00:00Z"},
            }
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = check_github_repo("owner/repo-name", timeout=3.0)
        self.assertEqual(res["status"], "synchronized")
        self.assertEqual(res["repo"], "owner/repo-name")
        self.assertEqual(res["latest_commit"], "1234567")
        self.assertEqual(res["message"], "feat: harden sentinel monitoring")
        self.assertEqual(res["date"], "2026-09-26T21:00:00Z")

    def test_check_github_repo_invalid_spec(self):
        res = check_github_repo("")
        self.assertEqual(res["status"], "invalid_repo")
        res2 = check_github_repo("invalid-no-slash")
        self.assertEqual(res2["status"], "invalid_repo")

    @patch("urllib.request.urlopen")
    def test_check_github_repo_fallback(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        res = check_github_repo("owner/repo")
        self.assertEqual(res["status"], "cached")
        self.assertIn("Connection refused", res["note"])

    @patch("check_upstream_updates.check_new_api_health")
    @patch("check_upstream_updates.check_github_repo")
    def test_run_lifecycle_monitor_save_and_structure(self, mock_github, mock_gateway):
        mock_gateway.return_value = {
            "status": "healthy",
            "latency_ms": 15,
            "available_models_count": 12,
            "image_models": ["agnes-image-2.5-flash"],
        }
        mock_github.return_value = {
            "repo": "custom/repo",
            "status": "synchronized",
            "latest_commit": "abcdef1",
        }

        out_file = self.tmp_path / "updates_test.json"
        summary = run_lifecycle_monitor(
            output_path=out_file,
            repos=["custom/repo"],
            save=True,
        )

        self.assertIn("last_checked_at", summary)
        self.assertEqual(summary["gateway"]["status"], "healthy")
        self.assertEqual(summary["upstream_repositories"][0]["repo"], "custom/repo")
        self.assertEqual(summary["upstream_repositories"][1]["repo"], "QuantumNous/new-api")
        self.assertTrue(out_file.exists())

        loaded = json.loads(out_file.read_text(encoding="utf-8"))
        self.assertEqual(loaded["gateway"]["status"], "healthy")
        self.assertEqual(len(loaded["cron_jobs"]), 1)
        self.assertTrue(loaded["cron_jobs"][0]["target"].endswith(".new-api/backups"))

    @patch("check_upstream_updates.check_new_api_health")
    def test_run_lifecycle_monitor_no_save(self, mock_gateway):
        mock_gateway.return_value = {"status": "unhealthy", "error": "mocked error"}
        out_file = self.tmp_path / "should_not_exist.json"
        summary = run_lifecycle_monitor(
            output_path=out_file,
            repos=[],
            save=False,
        )
        self.assertFalse(out_file.exists())
        self.assertEqual(summary["gateway"]["status"], "unhealthy")

    @patch("check_upstream_updates.check_new_api_health")
    def test_run_lifecycle_monitor_forwards_key_path(self, mock_gateway):
        mock_gateway.return_value = {"status": "healthy", "latency_ms": 10}
        custom_key = self.tmp_path / "custom_key.json"
        summary = run_lifecycle_monitor(
            repos=[],
            save=False,
            key_path=custom_key,
        )
        self.assertEqual(summary["gateway"]["status"], "healthy")
        mock_gateway.assert_called_once_with(
            base_url=None,
            api_key=None,
            timeout=5.0,
            key_path=custom_key,
        )

    @patch("check_upstream_updates.run_lifecycle_monitor")
    def test_cli_main_with_argv_and_repos(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        exit_code = monitor_main(["--no-save", "--repo", "custom/repo-a", "custom/repo-b"])
        self.assertEqual(exit_code, 0)
        mock_run.assert_called_once_with(
            output_path=check_upstream_updates.UPDATES_PATH,
            base_url=None,
            api_key=None,
            repos=["custom/repo-a", "custom/repo-b"],
            timeout=5.0,
            save=False,
            key_path=None,
        )

    @patch("check_upstream_updates.run_lifecycle_monitor")
    def test_cli_main_forwards_key_path_and_options(self, mock_run):
        mock_run.return_value = {"status": "ok"}
        custom_key = str(self.tmp_path / "key.json")
        exit_code = monitor_main([
            "--no-save",
            "--key-path", custom_key,
            "--base-url", "http://127.0.0.1:9999/v1",
            "--api-key", "sk-custom-test",
            "--timeout", "10.0",
        ])
        self.assertEqual(exit_code, 0)
        mock_run.assert_called_once_with(
            output_path=check_upstream_updates.UPDATES_PATH,
            base_url="http://127.0.0.1:9999/v1",
            api_key="sk-custom-test",
            repos=None,
            timeout=10.0,
            save=False,
            key_path=custom_key,
        )

    @patch("urllib.request.urlopen")
    def test_check_github_repo_custom_branch_syntax(self, mock_urlopen):
        mock_resp = unittest.mock.MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "sha": "fedcba987654321",
            "commit": {
                "message": "chore: branch commit",
                "author": {"date": "2026-10-04T18:00:00Z"},
            }
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        # 测试 @ 分支解析
        res_at = check_github_repo("owner/custom-repo@dev")
        self.assertEqual(res_at["status"], "synchronized")
        self.assertEqual(res_at["repo"], "owner/custom-repo")
        self.assertEqual(res_at["branch"], "dev")
        req_at = mock_urlopen.call_args[0][0]
        self.assertIn("/repos/owner/custom-repo/commits/dev", req_at.full_url)

        # 测试 # 分支解析
        res_hash = check_github_repo("owner/custom-repo#feature-x")
        self.assertEqual(res_hash["status"], "synchronized")
        self.assertEqual(res_hash["repo"], "owner/custom-repo")
        self.assertEqual(res_hash["branch"], "feature-x")
        req_hash = mock_urlopen.call_args[0][0]
        self.assertIn("/repos/owner/custom-repo/commits/feature-x", req_hash.full_url)

    @patch("check_upstream_updates.check_new_api_health")
    def test_run_lifecycle_monitor_quiet_mode(self, mock_gateway):
        mock_gateway.return_value = {"status": "healthy", "latency_ms": 5}
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            summary = run_lifecycle_monitor(
                repos=[],
                save=False,
                quiet=True,
            )
        self.assertEqual(summary["gateway"]["status"], "healthy")
        self.assertEqual(buf.getvalue(), "")

    @patch("check_upstream_updates.run_lifecycle_monitor")
    def test_cli_main_strict_mode(self, mock_run):
        # 1. 严格模式：网关与仓库健康 -> 退出码 0
        mock_run.return_value = {
            "gateway": {"status": "healthy"},
            "upstream_repositories": [{"repo": "owner/repo", "status": "synchronized"}],
        }
        self.assertEqual(monitor_main(["--strict", "--no-save"]), 0)

        # 2. 严格模式：网关不健康 -> 退出码 1
        mock_run.return_value = {
            "gateway": {"status": "unhealthy"},
            "upstream_repositories": [{"repo": "owner/repo", "status": "synchronized"}],
        }
        self.assertEqual(monitor_main(["--strict", "--no-save"]), 1)

        # 3. 严格模式：网关健康但存在 invalid_repo -> 退出码 1
        mock_run.return_value = {
            "gateway": {"status": "healthy"},
            "upstream_repositories": [
                {"repo": "owner/repo", "status": "synchronized"},
                {"repo": "bad_repo_spec", "status": "invalid_repo"},
            ],
        }
        self.assertEqual(monitor_main(["--strict", "--no-save"]), 1)

    @patch("check_upstream_updates.run_lifecycle_monitor")
    def test_cli_main_quiet_flag_forwarding(self, mock_run):
        mock_run.return_value = {"gateway": {"status": "healthy"}}
        exit_code = monitor_main(["-q", "--no-save"])
        self.assertEqual(exit_code, 0)
        mock_run.assert_called_once_with(
            output_path=check_upstream_updates.UPDATES_PATH,
            base_url=None,
            api_key=None,
            repos=None,
            timeout=5.0,
            save=False,
            key_path=None,
            quiet=True,
        )

    def test_sentinel_build_arg_parser(self):
        parser = sentinel_build_arg_parser()
        self.assertIsNotNone(parser)
        parsed = parser.parse_args(["--json", "--strict", "--no-save", "-q"])
        self.assertTrue(parsed.json)
        self.assertTrue(parsed.strict)
        self.assertTrue(parsed.no_save)
        self.assertTrue(parsed.quiet)

    @patch("check_upstream_updates.run_lifecycle_monitor")
    def test_cli_main_json_mode_output(self, mock_run):
        import io
        import contextlib
        mock_run.return_value = {
            "gateway": {"status": "healthy", "latency_ms": 12},
            "upstream_repositories": [{"repo": "owner/repo", "status": "synchronized"}],
        }
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = monitor_main(["--json", "--no-save"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["gateway"]["status"], "healthy")
        self.assertEqual(data["upstream_repositories"][0]["status"], "synchronized")

    @patch("check_upstream_updates.run_lifecycle_monitor")
    def test_cli_main_json_mode_with_strict_failure(self, mock_run):
        import io
        import contextlib
        mock_run.return_value = {
            "gateway": {"status": "unhealthy", "error": "Connection failed"},
            "upstream_repositories": [],
        }
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = monitor_main(["--json", "--strict", "--no-save"])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["gateway"]["status"], "unhealthy")

    @patch("check_upstream_updates.run_lifecycle_monitor", side_effect=RuntimeError("Lifecycle monitor crash"))
    def test_cli_exception_stderr_output(self, mock_run):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = monitor_main(["--no-save"])
        self.assertEqual(code, 1)
        self.assertIn("❌ 上游生命周期与网关监控运行失败: Lifecycle monitor crash", buf.getvalue())

    @patch("check_upstream_updates.run_lifecycle_monitor", side_effect=RuntimeError("Silent monitor crash"))
    def test_cli_exception_quiet_mode(self, mock_run):
        import io
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with redirect_stderr(err_buf), redirect_stdout(out_buf):
            code = monitor_main(["-q", "--no-save"])
        self.assertEqual(code, 1)
        self.assertEqual(err_buf.getvalue(), "")
        self.assertEqual(out_buf.getvalue(), "")

    @patch("check_upstream_updates.run_lifecycle_monitor", side_effect=RuntimeError("JSON monitor crash"))
    def test_cli_exception_json_output(self, mock_run):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = monitor_main(["--json", "--no-save"])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue())
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"], "JSON monitor crash")


class TestAutonomousFollowup(unittest.TestCase):
    """测试 24/7 自主跟进守护与晨报生成引擎"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_log_creates_file_and_directory(self):
        target_log = self.tmp_path / "sub" / "test_followup.log"
        followup_log("系统启动探测", kind="TEST", log_file=target_log)
        self.assertTrue(target_log.exists())
        content = target_log.read_text(encoding="utf-8")
        self.assertIn("[TEST] 系统启动探测", content)

    def test_post_event_writes_valid_ndjson(self):
        inbox = self.tmp_path / "inbox" / "events.ndjson"
        success = post_event("test_event", {"metric": 42}, inbox_file=inbox)
        self.assertTrue(success)
        self.assertTrue(inbox.exists())

        lines = inbox.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["source"], "agnes-followup-daemon")
        self.assertEqual(record["kind"], "test_event")
        self.assertEqual(record["payload"]["metric"], 42)
        self.assertIn("timestamp", record)
        self.assertIn("time_str", record)

    def test_post_event_handles_write_failure(self):
        invalid_path = self.tmp_path / "a_dir"
        invalid_path.mkdir(parents=True, exist_ok=True)
        res = post_event("test_fail", {}, inbox_file=invalid_path)
        self.assertFalse(res)

    def test_generate_morning_report_structure_and_metrics(self):
        report_file = self.tmp_path / "reports" / "MORNING_REPORT_TEST.md"
        fixed_dt = datetime.datetime(2026, 9, 26, 8, 0, 0)
        history = [
            {
                "title": "晨光留白",
                "subtitle": "MORNING LIGHT",
                "poster_url": "assets/poster_1.png",
                "score": 92,
            },
            {
                "title": "秩序之境",
                "subtitle": "ORDER STUDY",
                "poster_url": "assets/poster_2.png",
                "score": "88",
            },
            {
                "title": "未完成草稿",
                "subtitle": "DRAFT",
                "poster_url": "",
                "score": 50,
            },
        ]
        out_path = generate_morning_report(history, report_file=report_file, now=fixed_dt)
        self.assertEqual(out_path, str(report_file))
        self.assertTrue(report_file.exists())

        content = report_file.read_text(encoding="utf-8")
        self.assertIn("# Agnes Studio 自主演进晨报 (2026-09-26)", content)
        self.assertIn("新增自主生成海报**: 2 张", content)
        self.assertIn("90.0 / 100 分", content)
        self.assertIn("《晨光留白》", content)
        self.assertIn("《秩序之境》", content)
        self.assertNotIn("《未完成草稿》", content)

    def test_generate_morning_report_empty_and_zero_scores(self):
        report_file = self.tmp_path / "reports" / "MORNING_EMPTY.md"
        fixed_dt = datetime.datetime(2026, 9, 27, 8, 0, 0)
        out_path = generate_morning_report([], report_file=report_file, now=fixed_dt)
        self.assertTrue(Path(out_path).exists())
        content = Path(out_path).read_text(encoding="utf-8")
        self.assertIn("新增自主生成海报**: 0 张", content)
        self.assertIn("0.0 / 100 分", content)

    @patch("urllib.request.urlopen")
    def test_check_and_heal_server_uses_image_gateway_from_config(self, mock_urlopen):
        config_resp = MagicMock()
        config_resp.status = 200
        config_resp.read.return_value = json.dumps({
            "image_base_url": "http://127.0.0.1:13000/v1",
        }).encode("utf-8")
        models_resp = MagicMock()
        models_resp.status = 200
        config_resp.__enter__.return_value = config_resp
        models_resp.__enter__.return_value = models_resp
        mock_urlopen.side_effect = [config_resp, models_resp]

        server_alive, new_api_alive = check_and_heal_server(
            server_url="http://127.0.0.1:8088/api/config",
            api_key="test_key",
            auto_heal=False,
        )

        self.assertTrue(server_alive)
        self.assertTrue(new_api_alive)
        models_request = mock_urlopen.call_args_list[1].args[0]
        self.assertEqual(models_request.full_url, "http://127.0.0.1:13000/v1/models")

    @patch("autonomous_followup.get_local_auth_key", return_value="")
    @patch("urllib.request.urlopen")
    def test_check_and_heal_server_does_not_use_embedded_api_key(self, mock_urlopen, _mock_local_auth):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"{}"
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with patch.dict("os.environ", {"AGNES_API_KEY": "", "AGNES_GATEWAY_KEY": "", "NEW_API_KEY": ""}, clear=False):
            check_and_heal_server(
                server_url="http://127.0.0.1:8088/api/config",
                api_base="http://127.0.0.1:13000/v1",
                auto_heal=False,
            )

        models_request = mock_urlopen.call_args_list[1].args[0]
        self.assertNotIn("Authorization", models_request.headers)

    @patch("autonomous_followup.get_local_auth_key", return_value="")
    @patch("urllib.request.urlopen")
    def test_check_and_heal_server_uses_agnes_gateway_key_from_env(self, mock_urlopen, _mock_local_auth):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"{}"
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with patch.dict("os.environ", {"AGNES_API_KEY": "", "AGNES_GATEWAY_KEY": "gw_key_123", "NEW_API_KEY": ""}, clear=False):
            check_and_heal_server(
                server_url="http://127.0.0.1:8088/api/config",
                api_base="http://127.0.0.1:13000/v1",
                auto_heal=False,
            )

        models_request = mock_urlopen.call_args_list[1].args[0]
        self.assertEqual(models_request.headers.get("Authorization"), "Bearer gw_key_123")

    @patch("autonomous_followup.get_local_auth_key", return_value="")
    @patch("urllib.request.urlopen")
    def test_check_and_heal_server_uses_agnes_base_url_from_env(self, mock_urlopen, _mock_local_auth):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"{}"
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with patch.dict("os.environ", {"AGNES_BASE_URL": "http://10.0.0.1:13000/v1", "NEW_API_BASE_URL": "", "AGNES_API_BASE": ""}, clear=False):
            check_and_heal_server(
                server_url="http://127.0.0.1:8088/api/config",
                auto_heal=False,
            )

        models_request = mock_urlopen.call_args_list[1].args[0]
        self.assertEqual(models_request.full_url, "http://10.0.0.1:13000/v1/models")

    @patch("autonomous_followup.get_local_auth_key", return_value="")
    @patch("urllib.request.urlopen")
    def test_check_and_heal_server_uses_new_api_base_url_from_env(self, mock_urlopen, _mock_local_auth):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b"{}"
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with patch.dict("os.environ", {"AGNES_BASE_URL": "", "NEW_API_BASE_URL": "http://10.0.0.2:13000/v1", "AGNES_API_BASE": ""}, clear=False):
            check_and_heal_server(
                server_url="http://127.0.0.1:8088/api/config",
                auto_heal=False,
            )

        models_request = mock_urlopen.call_args_list[1].args[0]
        self.assertEqual(models_request.full_url, "http://10.0.0.2:13000/v1/models")

    @patch("urllib.request.urlopen")
    def test_check_and_heal_server_healthy(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        server_alive, new_api_alive = check_and_heal_server(
            server_url="http://127.0.0.1:8088/api/config",
            api_base="http://127.0.0.1:3000",
            api_key="test_key",
            auto_heal=False,
        )
        self.assertTrue(server_alive)
        self.assertTrue(new_api_alive)

    @patch("urllib.request.urlopen")
    def test_check_and_heal_server_unhealthy_no_heal(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        server_alive, new_api_alive = check_and_heal_server(
            server_url="http://127.0.0.1:8088/api/config",
            api_base="http://127.0.0.1:3000",
            api_key="test_key",
            auto_heal=False,
        )
        self.assertFalse(server_alive)
        self.assertFalse(new_api_alive)

    @patch("subprocess.Popen")
    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_check_and_heal_server_triggers_auto_heal(self, mock_urlopen, mock_sleep, mock_popen):
        def urlopen_side_effect(req, *args, **kwargs):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            if "8088" in url:
                raise urllib.error.URLError("Connection refused")
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.__enter__.return_value = mock_resp
            return mock_resp

        mock_urlopen.side_effect = urlopen_side_effect
        server_alive, new_api_alive = check_and_heal_server(
            server_url="http://127.0.0.1:8088/api/config",
            api_base="http://127.0.0.1:3000",
            api_key="test_key",
            auto_heal=True,
        )
        self.assertFalse(server_alive)
        self.assertTrue(new_api_alive)
        self.assertTrue(mock_popen.called)

    @patch("subprocess.check_output")
    @patch("subprocess.run")
    def test_check_and_sync_git_up_to_date(self, mock_run, mock_check_output):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_check_output.side_effect = ["rev_abc", "rev_abc"]

        synced, status = check_and_sync_git(cwd=self.tmp_path, proxy="")
        self.assertFalse(synced)
        self.assertEqual(status, "up_to_date")

    @patch("subprocess.run")
    def test_check_and_sync_git_fetch_failed(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="fatal: remote error")

        synced, status = check_and_sync_git(cwd=self.tmp_path, proxy="")
        self.assertFalse(synced)
        self.assertEqual(status, "fetch_failed")

    @patch("subprocess.check_output")
    @patch("subprocess.run")
    def test_check_and_sync_git_behind_and_rebase_success(self, mock_run, mock_check_output):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_check_output.side_effect = [
            "local_rev_1",
            "remote_rev_2",
            "3",
            "abc1234 feat(poster): latest commit",
        ]

        synced, commit = check_and_sync_git(cwd=self.tmp_path, proxy="http://127.0.0.1:7890")
        self.assertTrue(synced)
        self.assertEqual(commit, "abc1234 feat(poster): latest commit")

    @patch("subprocess.check_output")
    @patch("subprocess.run")
    def test_check_and_sync_git_rebase_conflict(self, mock_run, mock_check_output):
        mock_fetch_res = MagicMock(returncode=0, stderr="")
        mock_pull_res = MagicMock(returncode=1, stderr="CONFLICT (content)")
        mock_run.side_effect = [mock_fetch_res, mock_pull_res, MagicMock(returncode=0)]
        mock_check_output.side_effect = [
            "local_rev_1",
            "remote_rev_2",
            "1",
        ]

        synced, status = check_and_sync_git(cwd=self.tmp_path, proxy="")
        self.assertFalse(synced)
        self.assertEqual(status, "rebase_conflict")

    @patch("subprocess.run")
    def test_check_and_sync_git_exception_handled(self, mock_run):
        mock_run.side_effect = RuntimeError("Process timeout")
        synced, status = check_and_sync_git(cwd=self.tmp_path, proxy="")
        self.assertFalse(synced)
        self.assertIn("Process timeout", status)

    @patch("urllib.request.urlopen")
    def test_run_creative_pipeline_cycle_success(self, mock_urlopen):
        responses = [
            {"success": True, "brief": {"title": "极简秩序", "subtitle": "ORDER", "style_preset": "swiss_01", "gen_prompt": "concrete wall"}},
            {"success": True, "file_path": "/tmp/test_bg.png"},
            {"success": True, "poster_url": "assets/test_poster.png", "duration_ms": 350},
            {"success": True, "inspection": {"aesthetic_score": 93, "occlusion_risk": "low", "text_legibility": "excellent"}},
        ]

        class MockHttpResponse:
            def __init__(self, data):
                self._data = json.dumps(data).encode("utf-8")
            def read(self):
                return self._data
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        mock_urlopen.side_effect = [MockHttpResponse(r) for r in responses]

        result = run_creative_pipeline_cycle(0, server_base="http://127.0.0.1:8088", timeout=10)
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "极简秩序")
        self.assertEqual(result["subtitle"], "ORDER")
        self.assertEqual(result["poster_url"], "assets/test_poster.png")
        self.assertEqual(result["score"], 93)

    @patch("urllib.request.urlopen")
    def test_run_creative_pipeline_cycle_brief_fail(self, mock_urlopen):
        class MockHttpResponse:
            def __init__(self, data):
                self._data = json.dumps(data).encode("utf-8")
            def read(self):
                return self._data
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass

        mock_urlopen.return_value = MockHttpResponse({"success": False, "error": "gemini quota exhausted"})
        result = run_creative_pipeline_cycle(1, server_base="http://127.0.0.1:8088", timeout=10)
        self.assertIsNone(result)

    @patch("urllib.request.urlopen")
    def test_run_creative_pipeline_cycle_exception(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")
        result = run_creative_pipeline_cycle(2, server_base="http://127.0.0.1:8088", timeout=10)
        self.assertIsNone(result)

    def test_cli_main_report_now(self):
        report_file = self.tmp_path / "cli_report_now.md"
        exit_code = followup_main(["--report-now", "--out-report", str(report_file)])
        self.assertEqual(exit_code, 0)
        self.assertTrue(report_file.exists())
        content = report_file.read_text(encoding="utf-8")
        self.assertIn("# Agnes Studio 自主演进晨报", content)

    @patch("autonomous_followup.run_creative_pipeline_cycle")
    @patch("autonomous_followup.check_and_heal_server")
    @patch("autonomous_followup.check_and_sync_git")
    def test_cli_main_once_mode(self, mock_sync, mock_heal, mock_pipeline):
        mock_sync.return_value = (False, "up_to_date")
        mock_heal.return_value = (True, True)

        exit_code = followup_main(["--once", "--no-pipeline"])
        self.assertEqual(exit_code, 0)
        mock_sync.assert_called_once()
        mock_heal.assert_called_once_with(auto_heal=True)
        mock_pipeline.assert_not_called()

    @patch("autonomous_followup.run_creative_pipeline_cycle")
    @patch("autonomous_followup.check_and_heal_server")
    @patch("autonomous_followup.check_and_sync_git")
    def test_cli_main_once_with_pipeline_and_flags(self, mock_sync, mock_heal, mock_pipeline):
        mock_heal.return_value = (True, True)
        mock_pipeline.return_value = {"title": "T", "score": 90}

        exit_code = followup_main(["--once", "--no-sync", "--no-heal"])
        self.assertEqual(exit_code, 0)
        mock_sync.assert_not_called()
        mock_heal.assert_called_once_with(auto_heal=False)
        mock_pipeline.assert_called_once_with(1)

    def test_cli_build_arg_parser_options(self):
        parser = followup_build_arg_parser()
        actions = {opt for a in parser._actions for opt in a.option_strings}
        self.assertIn("--quiet", actions)
        self.assertIn("-q", actions)
        self.assertIn("--json", actions)
        self.assertIn("--once", actions)
        self.assertIn("--report-now", actions)
        self.assertIn("--no-heal", actions)
        self.assertIn("--no-sync", actions)
        self.assertIn("--no-pipeline", actions)
        self.assertIn("--out-report", actions)

    def test_cli_main_report_now_json_mode(self):
        import io
        from contextlib import redirect_stdout
        report_file = self.tmp_path / "cli_report_now.md"
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = followup_main(["--report-now", "--out-report", str(report_file), "--json"])
        self.assertEqual(exit_code, 0)
        data = json.loads(buf.getvalue())
        self.assertTrue(data["ok"])
        self.assertEqual(data["action"], "report_now")
        self.assertEqual(data["report_path"], str(report_file))

    @patch("autonomous_followup.run_creative_pipeline_cycle")
    @patch("autonomous_followup.check_and_heal_server")
    @patch("autonomous_followup.check_and_sync_git")
    def test_cli_main_once_json_mode(self, mock_sync, mock_heal, mock_pipeline):
        import io
        from contextlib import redirect_stdout
        mock_sync.return_value = (False, "up_to_date")
        mock_heal.return_value = (True, True)
        mock_pipeline.return_value = {"title": "T", "score": 90}

        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = followup_main(["--once", "--json"])
        self.assertEqual(exit_code, 0)
        data = json.loads(buf.getvalue())
        self.assertTrue(data["ok"])
        self.assertEqual(data["action"], "once_cycle")
        self.assertEqual(data["cycle"], 1)
        self.assertEqual(data["pipeline_results_count"], 1)

    @patch("autonomous_followup.run_creative_pipeline_cycle")
    @patch("autonomous_followup.check_and_heal_server")
    @patch("autonomous_followup.check_and_sync_git")
    def test_cli_main_quiet_mode(self, mock_sync, mock_heal, mock_pipeline):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        mock_sync.return_value = (False, "up_to_date")
        mock_heal.return_value = (True, True)

        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            exit_code = followup_main(["--once", "--no-pipeline", "-q"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    @patch("autonomous_followup.generate_morning_report", side_effect=RuntimeError("Report write error"))
    def test_cli_main_exception_stderr_output(self, mock_report):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with redirect_stderr(buf):
            exit_code = followup_main(["--report-now"])
        self.assertEqual(exit_code, 1)
        self.assertIn("❌ 24/7 自主守护引擎运行失败: Report write error", buf.getvalue())

    @patch("autonomous_followup.generate_morning_report", side_effect=RuntimeError("Report json failure"))
    def test_cli_main_exception_json_output(self, mock_report):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = followup_main(["--report-now", "--json"])
        self.assertEqual(exit_code, 1)
        data = json.loads(buf.getvalue())
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"], "Report json failure")

    @patch("autonomous_followup.generate_morning_report", side_effect=RuntimeError("Quiet failure"))
    def test_cli_main_exception_quiet_mode(self, mock_report):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            exit_code = followup_main(["--report-now", "-q"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")


class TestProPosterRenderer(unittest.TestCase):
    """测试专业商业海报排版引擎 pro_poster_renderer"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_base64_image_empty_and_passthrough(self):
        self.assertEqual(get_base64_image(""), "")
        self.assertEqual(get_base64_image(None), "")
        data_uri = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        self.assertEqual(get_base64_image(data_uri), data_uri)
        jpeg_data_uri = "data:image/jpeg;base64,/9j/4AAQSkZJRg=="
        self.assertEqual(get_base64_image(jpeg_data_uri), jpeg_data_uri)

    def test_get_base64_image_file_types_and_missing(self):
        img_png = self.tmp_path / "test.png"
        img_png.write_bytes(b"\x89PNG\r\n\x1a\nfake_png_data")
        res_png = get_base64_image(str(img_png))
        self.assertTrue(res_png.startswith("data:image/png;base64,"))

        img_jpg = self.tmp_path / "test.jpg"
        img_jpg.write_bytes(b"\xff\xd8\xfffake_jpg_data")
        res_jpg = get_base64_image(str(img_jpg))
        self.assertTrue(res_jpg.startswith("data:image/jpeg;base64,"))

        img_webp = self.tmp_path / "test.webp"
        img_webp.write_bytes(b"RIFFfake_webp_dataWEBP")
        res_webp = get_base64_image(str(img_webp))
        self.assertTrue(res_webp.startswith("data:image/webp;base64,"))

        missing_res = get_base64_image(str(self.tmp_path / "missing_file.png"))
        self.assertEqual(missing_res, "")

    def test_html_builders_structure_and_interpolation(self):
        test_bg = "data:image/png;base64,placeholder_bg_data"
        builders = [
            (build_swiss_01_html, ["ORDNUNG", "SWISS INTERNATIONAL STYLE"]),
            (build_swiss_02_html, ["musica", "viva.", "tonhalle zürich"]),
            (build_article_01_html, ["NEURAL REVIEW", "COVER STORY", "机械黄昏"]),
            (build_article_02_html, ["极简生活志", "在喧嚣时代", "确定性"]),
            (build_cyber_01_html, ["TACTICAL HUD", "零界觉醒", "CYBERPUNK"]),
            (build_cyber_02_html, ["Y2K ACID BRUTALISM", "重构视界", "RECONSTRUCT"]),
            (build_chinese_01_html, ["苏园", "惊鸿", "vertical-rl"]),
            (build_chinese_02_html, ["山海微澜", "清怀", "南宋马远夏圭遗意"]),
            (build_cinema_01_html, ["最后的地平线", "THE LAST HORIZON", "IMAX 70MM"]),
            (build_cinema_02_html, ["深渊回响", "VOICES IN THE MIST", "CANNES FILM FESTIVAL"]),
        ]
        for builder_fn, expected_keywords in builders:
            with self.subTest(builder=builder_fn.__name__):
                html = builder_fn(test_bg)
                self.assertIn("<!DOCTYPE html>", html)
                self.assertIn("</html>", html)
                self.assertIn(test_bg, html)
                for kw in expected_keywords:
                    self.assertIn(kw, html)

    def test_poster_registry_integrity(self):
        expected_keys = {
            "swiss_01", "swiss_02", "article_01", "article_02",
            "cyber_01", "cyber_02", "chinese_01", "chinese_02",
            "cinema_01", "cinema_02"
        }
        self.assertEqual(set(POSTER_REGISTRY.keys()), expected_keys)
        for key, item in POSTER_REGISTRY.items():
            with self.subTest(preset=key):
                self.assertIn("name", item)
                self.assertIn("func", item)
                self.assertIn("html_func", item)
                self.assertIn("file", item)
                self.assertIn("category", item)
                self.assertTrue(callable(item["func"]))
                self.assertTrue(callable(item["html_func"]))
                self.assertTrue(item["file"].endswith(".png"))

    def test_list_and_get_poster_preset(self):
        presets = list_poster_presets()
        self.assertEqual(len(presets), 10)
        keys = [p["key"] for p in presets]
        self.assertIn("swiss_01", keys)
        self.assertIn("chinese_01", keys)

        # get_poster_preset
        preset = get_poster_preset("cyber_01")
        self.assertIsNotNone(preset)
        self.assertEqual(preset["category"], "cyber")

        # case insensitivity
        self.assertEqual(get_poster_preset("CYBER_01"), preset)
        self.assertEqual(get_poster_preset("  cyber_01  "), preset)

        # invalid / empty
        self.assertIsNone(get_poster_preset("non_existent"))
        self.assertIsNone(get_poster_preset(""))
        self.assertIsNone(get_poster_preset(None))

    def test_render_preset_invalid_key_raises(self):
        with self.assertRaises(KeyError):
            render_preset("invalid_preset_key")

    def test_render_html_to_poster_validation(self):
        with self.assertRaises(ValueError):
            render_html_to_poster("", "/tmp/out.png")
        with self.assertRaises(ValueError):
            render_html_to_poster(None, "/tmp/out.png")
        with self.assertRaises(ValueError):
            render_html_to_poster("<html></html>", "")
        with self.assertRaises(ValueError):
            render_html_to_poster("<html></html>", None)

    @patch("pro_poster_renderer.sync_playwright")
    def test_render_html_to_poster_mocked_playwright(self, mock_playwright_cm):
        mock_p = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        mock_playwright_cm.return_value.__enter__.return_value = mock_p
        mock_p.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        out_png = self.tmp_path / "subdir" / "output.png"
        def fake_screenshot(path, **kwargs):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(b"mock_png_bytes")
        mock_page.screenshot.side_effect = fake_screenshot

        res = render_html_to_poster("<html><body>Test</body></html>", str(out_png), width=1000, height=800, wait_timeout_ms=100)
        self.assertEqual(res, str(out_png))
        self.assertTrue(out_png.exists())
        mock_browser.new_page.assert_called_with(viewport={"width": 1000, "height": 800})
        mock_page.set_content.assert_called_with("<html><body>Test</body></html>")
        mock_page.wait_for_timeout.assert_called_with(100)
        mock_page.screenshot.assert_called_with(path=str(out_png), type="png")
        mock_browser.close.assert_called_once()

        # JPEG mode
        out_jpg = self.tmp_path / "output.jpg"
        render_html_to_poster("<html><body>Test JPG</body></html>", str(out_jpg))
        mock_page.screenshot.assert_called_with(path=str(out_jpg), quality=95, type="jpeg")

    @patch("pro_poster_renderer.render_html_to_poster")
    def test_render_all_individual_presets_with_mock(self, mock_render):
        fake_bg = str(self.tmp_path / "fake_bg.png")
        Path(fake_bg).write_bytes(b"fake_bg")

        renderers = [
            render_swiss_01,
            render_swiss_02,
            render_article_01,
            render_article_02,
            render_cyber_01,
            render_cyber_02,
            render_chinese_01,
            render_chinese_02,
            render_cinema_01,
            render_cinema_02,
        ]

        for r_fn in renderers:
            with self.subTest(renderer=r_fn.__name__):
                mock_render.reset_mock()
                out_file = str(self.tmp_path / f"out_{r_fn.__name__}.png")
                res = r_fn(bg_img=fake_bg, out_img=out_file)
                self.assertEqual(res, out_file)
                mock_render.assert_called()
                call_args = mock_render.call_args[0]
                self.assertIn("<!DOCTYPE html>", call_args[0])
                self.assertEqual(call_args[1], out_file)

    @patch("pro_poster_renderer.render_html_to_poster")
    def test_render_preset_dispatch_and_run_all(self, mock_render):
        fake_bg = str(self.tmp_path / "fake_bg.png")
        Path(fake_bg).write_bytes(b"fake_bg")
        out_file = str(self.tmp_path / "out_preset.png")

        res = render_preset("swiss_01", bg_img=fake_bg, out_img=out_file)
        self.assertEqual(res, out_file)

        mock_render.reset_mock()
        all_results = run_all_posters(output_dir=str(self.tmp_path / "batch_out"))
        self.assertEqual(len(all_results), 10)
        for k in POSTER_REGISTRY.keys():
            self.assertIn(k, all_results)
            self.assertTrue(all_results[k].endswith(".png"))

    @patch("pro_poster_renderer.render_html_to_poster")
    def test_render_preset_and_run_all_quiet_mode(self, mock_render):
        from contextlib import redirect_stdout

        fake_bg = str(self.tmp_path / "fake_bg.png")
        Path(fake_bg).write_bytes(b"fake_bg")
        out_file = str(self.tmp_path / "out_preset.png")

        buf = io.StringIO()
        with redirect_stdout(buf):
            render_preset("swiss_01", bg_img=fake_bg, out_img=out_file, quiet=True)
            run_all_posters(output_dir=str(self.tmp_path / "batch_out"), quiet=True)
        self.assertEqual(buf.getvalue().strip(), "")

    @patch("pro_poster_renderer.render_html_to_poster")
    def test_run_all_with_category_filter(self, mock_render):
        results_cinema = run_all_posters(category="cinema", quiet=True)
        self.assertEqual(set(results_cinema.keys()), {"cinema_01", "cinema_02"})

        results_swiss = run_all_posters(category="swiss", quiet=True)
        self.assertEqual(set(results_swiss.keys()), {"swiss_01", "swiss_02"})

        results_none = run_all_posters(category="unknown_cat", quiet=True)
        self.assertEqual(results_none, {})

    def test_cli_main_list_mode(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pro_poster_main(["--list"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Agnes Studio 可用海报预设:", out)
        self.assertIn("swiss_01", out)
        self.assertIn("cinema_01", out)

    @patch("pro_poster_renderer.render_html_to_poster")
    def test_cli_main_key_mode_with_custom_src_and_out(self, mock_render):
        fake_bg = self.tmp_path / "custom_bg.png"
        fake_bg.write_bytes(b"custom_bg")
        out_file = self.tmp_path / "custom_out.png"

        code = pro_poster_main([
            "--key", "cinema_01",
            "--src", str(fake_bg),
            "--out", str(out_file),
            "--quiet",
        ])
        self.assertEqual(code, 0)
        mock_render.assert_called()
        self.assertEqual(mock_render.call_args[0][1], str(out_file))

    @patch("pro_poster_renderer.render_html_to_poster")
    def test_cli_main_category_mode(self, mock_render):
        out_dir = self.tmp_path / "cinema_posters"
        code = pro_poster_main([
            "--category", "cinema",
            "--out-dir", str(out_dir),
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_render.call_count, 2)

    def test_cli_main_invalid_key_strict_mode(self):
        code = pro_poster_main(["--key", "nonexistent_key", "--strict", "--quiet"])
        self.assertEqual(code, 1)

        code_lenient = pro_poster_main(["--key", "nonexistent_key", "--quiet"])
        self.assertEqual(code_lenient, 0)

    @patch("pro_poster_renderer.render_html_to_poster")
    def test_cli_main_quiet_mode_suppresses_stdout(self, mock_render):
        from contextlib import redirect_stdout

        fake_bg = self.tmp_path / "custom_bg.png"
        fake_bg.write_bytes(b"custom_bg")
        out_file = self.tmp_path / "custom_out.png"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pro_poster_main([
                "--key", "swiss_01",
                "--src", str(fake_bg),
                "--out", str(out_file),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_list_poster_categories(self):
        cats = pro_poster_list_categories()
        self.assertEqual(len(cats), 5)
        cat_ids = [c["category"] for c in cats]
        for expected in ["swiss", "article", "cyber", "chinese", "cinema"]:
            self.assertIn(expected, cat_ids)
        self.assertEqual(cats, PRO_POSTER_CATEGORIES)

    def test_build_arg_parser(self):
        parser = pro_poster_build_arg_parser()
        self.assertIsNotNone(parser)
        parsed = parser.parse_args(["--list-categories", "--json"])
        self.assertTrue(parsed.list_categories)
        self.assertTrue(parsed.json)

    def test_cli_main_list_categories_mode(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pro_poster_main(["--list-categories"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Agnes Studio 可用海报流派分类:", out)
        self.assertIn("swiss", out)
        self.assertIn("瑞士国际主义网格", out)

    def test_cli_main_json_list_and_categories(self):
        from contextlib import redirect_stdout

        # list categories json
        buf_cat = io.StringIO()
        with redirect_stdout(buf_cat):
            code_cat = pro_poster_main(["--list-categories", "--json"])
        self.assertEqual(code_cat, 0)
        data_cat = json.loads(buf_cat.getvalue())
        self.assertIsInstance(data_cat, list)
        self.assertEqual(len(data_cat), 5)

        # list presets json
        buf_list = io.StringIO()
        with redirect_stdout(buf_list):
            code_list = pro_poster_main(["--list", "--json"])
        self.assertEqual(code_list, 0)
        data_list = json.loads(buf_list.getvalue())
        self.assertIsInstance(data_list, list)
        self.assertEqual(len(data_list), 10)

    @patch("pro_poster_renderer.render_html_to_poster")
    def test_cli_main_json_render_preset(self, mock_render):
        fake_bg = self.tmp_path / "custom_bg.png"
        fake_bg.write_bytes(b"custom_bg")
        out_file = self.tmp_path / "custom_out.png"

        def fake_render(html, out_path, **kwargs):
            Path(out_path).write_bytes(b"12345")
            return out_path

        mock_render.side_effect = fake_render

        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pro_poster_main([
                "--key", "swiss_01",
                "--src", str(fake_bg),
                "--out", str(out_file),
                "--json",
            ])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("key"), "swiss_01")
        self.assertEqual(data.get("bytes"), 5)

    @patch("pro_poster_renderer.render_html_to_poster")
    def test_cli_main_json_render_category(self, mock_render):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pro_poster_main([
                "--category", "cinema",
                "--out-dir", str(self.tmp_path / "cinema_json"),
                "--json",
            ])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("category"), "cinema")
        self.assertEqual(data.get("total"), 2)

    @patch("pro_poster_renderer.render_preset", side_effect=RuntimeError("Simulated pro render crash"))
    def test_cli_main_exception_stderr_output(self, mock_render):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = pro_poster_main([
                "--key", "swiss_01",
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 渲染海报失败 [swiss_01]: Simulated pro render crash", buf.getvalue())

    @patch("pro_poster_renderer.render_preset", side_effect=RuntimeError("Simulated pro quiet crash"))
    def test_cli_main_exception_quiet_mode(self, mock_render):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            code = pro_poster_main([
                "--key", "swiss_01",
                "-q",
            ])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_cli_main_missing_src_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        missing_src = self.tmp_path / "non_existent_poster_bg.png"
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = pro_poster_main([
                "--key", "swiss_01",
                "--src", str(missing_src),
                "--strict",
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 找不到输入底图", buf.getvalue())

    @patch("pro_poster_renderer.render_preset", side_effect=RuntimeError("Simulated pro JSON crash"))
    def test_cli_main_exception_json_error(self, mock_render):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = pro_poster_main([
                "--key", "swiss_01",
                "--json",
            ])
        self.assertEqual(code, 1)
        err = json.loads(buf.getvalue())
        self.assertFalse(err["ok"])
        self.assertIn("error", err)
        self.assertIn("Simulated pro JSON crash", err["error"])
        self.assertEqual(err.get("key"), "swiss_01")


class TestGeminiEngine(unittest.TestCase):
    """Gemini 智能多模态与排版引擎单元测试"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch.dict("os.environ", {}, clear=True)
    @patch("agnes_engine.KEY_PATH", Path("/tmp/non_existent_key_path_xyz.json"))
    def test_load_credentials_defaults(self):
        base, key, model = load_credentials()
        self.assertEqual(base, DEFAULT_BASE)
        # 新行为: 无 AGNES_* 变量且无 key 文件时 key 为 None（不再默认空字符串）
        self.assertIsNone(key)
        self.assertEqual(model, DEFAULT_CHAT_MODEL)

    @patch.dict("os.environ", {
        "GEMINI_BASE_URL": "http://127.0.0.1:9999/v1",
        "ANTIGRAVITY_API_KEY": "sk-secret-token",
        "GEMINI_CHAT_MODEL": "gemini-3.1-pro-high",
    }, clear=True)
    @patch("agnes_engine.KEY_PATH", Path("/tmp/non_existent_key_path_xyz.json"))
    def test_load_credentials_with_env(self):
        base, key, model = load_credentials()
        # 无 key 文件时，GEMINI_*/OPENAI_* 通用回退生效
        self.assertEqual(base, "http://127.0.0.1:9999/v1")
        self.assertEqual(key, "sk-secret-token")
        self.assertEqual(model, "gemini-3.1-pro-high")

    @patch.dict("os.environ", {}, clear=True)
    def test_load_credentials_with_key_file(self):
        fake_key_file = self.tmp_path / "fake_key.json"
        fake_key_file.write_text(json.dumps({
            "chat_base_url": "http://example.com/api",
            "api_key": "file-key-123",
            "models": {
                "chat": ["agnes-3.0-flash", "unsupported-model"]
            }
        }), encoding="utf-8")

        with patch("agnes_engine.KEY_PATH", fake_key_file):
            base, key, model = load_credentials()
            self.assertEqual(base, "http://example.com/api")
            self.assertEqual(key, "file-key-123")
            self.assertEqual(model, "agnes-3.0-flash")

    @patch.dict("os.environ", {
        "AGNES_BASE_URL": "http://agnes.direct:8888/v1",
        "AGNES_API_KEY": "sk-agnes-direct",
        "OPENAI_BASE_URL": "http://openai.fallback:9999/v1",
        "OPENAI_API_KEY": "sk-openai-fallback",
    }, clear=True)
    def test_load_credentials_agnes_overrides_all(self):
        fake_key_file = self.tmp_path / "fake_key.json"
        fake_key_file.write_text(json.dumps({
            "chat_base_url": "http://file.example/v1",
            "api_key": "file-key-123",
        }), encoding="utf-8")

        with patch("agnes_engine.KEY_PATH", fake_key_file):
            base, key, model = load_credentials()
            self.assertEqual(base, "http://agnes.direct:8888/v1")
            self.assertEqual(key, "sk-agnes-direct")

    @patch.dict("os.environ", {
        "OPENAI_BASE_URL": "http://192.168.1.164:8045/v1",
        "OPENAI_API_BASE": "http://127.0.0.1:18045/v1",
    }, clear=True)
    @patch("agnes_engine.KEY_PATH", Path("/tmp/non_existent_key_path_xyz.json"))
    def test_load_credentials_ignores_env_fossils(self):
        # 2026-09-30 回归：sshd 携带的 8045 化石与 bashrc 的 18045 化石
        # 不得劫持默认网关，必须回退到 DEFAULT_BASE
        base, key, model = load_credentials()
        self.assertEqual(base, DEFAULT_BASE)

    @patch.dict("os.environ", {
        "OPENAI_BASE_URL": "http://openai.fallback:9999/v1",
        "OPENAI_API_KEY": "sk-openai-fallback",
    }, clear=True)
    def test_load_credentials_key_file_overrides_fallback(self):
        fake_key_file = self.tmp_path / "fake_key.json"
        fake_key_file.write_text(json.dumps({
            "chat_base_url": "http://file.example/v1",
            "api_key": "file-key-123",
        }), encoding="utf-8")

        with patch("agnes_engine.KEY_PATH", fake_key_file):
            base, key, model = load_credentials()
            self.assertEqual(base, "http://file.example/v1")
            self.assertEqual(key, "file-key-123")

    @patch.dict("os.environ", {}, clear=True)
    def test_load_credentials_key_file_base_url_fallback(self):
        fake_key_file = self.tmp_path / "fake_key.json"
        fake_key_file.write_text(json.dumps({
            "base_url": "http://fallback-base.example/v1",
            "api_key": "file-key-456",
        }), encoding="utf-8")

        with patch("agnes_engine.KEY_PATH", fake_key_file):
            base, key, model = load_credentials()
            self.assertEqual(base, "http://fallback-base.example/v1")
            self.assertEqual(key, "file-key-456")

    @patch.dict("os.environ", {
        "OPENAI_API_BASE": "http://127.0.0.1:19000/v1",
        "OPENAI_API_KEY": "sk-fallback-key",
    }, clear=True)
    @patch("agnes_engine.KEY_PATH", Path("/tmp/non_existent_key_path_xyz.json"))
    def test_load_credentials_with_openai_api_base(self):
        base, key, model = load_credentials()
        self.assertEqual(base, "http://127.0.0.1:19000/v1")
        self.assertEqual(key, "sk-fallback-key")

    @patch.dict("os.environ", {
        "OPENAI_BASE_URL": "http://127.0.0.1:3000/v1",
    }, clear=True)
    @patch("agnes_engine.KEY_PATH", Path("/tmp/non_existent_key_path_xyz.json"))
    def test_load_credentials_ignores_fossil_3000(self):
        base, key, model = load_credentials()
        self.assertEqual(base, DEFAULT_BASE)

    @patch.dict("os.environ", {
        "AGNES_CHAT_BASE_URL": "http://chat.agnes.internal:14000/v1",
        "NEW_API_KEY": "sk-new-api-credentials-key",
    }, clear=True)
    @patch("agnes_engine.KEY_PATH", Path("/tmp/non_existent_key_path_xyz.json"))
    def test_load_credentials_with_agnes_chat_base_and_new_api_key(self):
        base, key, model = load_credentials()
        self.assertEqual(base, "http://chat.agnes.internal:14000/v1")
        self.assertEqual(key, "sk-new-api-credentials-key")

    @patch.dict("os.environ", {
        "NEW_API_BASE_URL": "http://new-api.fallback:15000/v1",
        "NEW_API_KEY": "sk-new-api-fallback-key",
    }, clear=True)
    @patch("agnes_engine.KEY_PATH", Path("/tmp/non_existent_key_path_xyz.json"))
    def test_load_credentials_with_new_api_base_fallback(self):
        base, key, model = load_credentials()
        self.assertEqual(base, "http://new-api.fallback:15000/v1")
        self.assertEqual(key, "sk-new-api-fallback-key")

    @patch.dict("os.environ", {}, clear=True)
    def test_load_credentials_with_explicit_key_path(self):
        custom_key_file = self.tmp_path / "custom_key.json"
        custom_key_file.write_text(json.dumps({
            "chat_base_url": "http://custom-chat.example.com/v1",
            "api_key": "custom-key-789",
            "models": {
                "chat": ["agnes-2.5-pro", "unsupported-model"]
            }
        }), encoding="utf-8")

        base, key, model = load_credentials(key_path=custom_key_file)
        self.assertEqual(base, "http://custom-chat.example.com/v1")
        self.assertEqual(key, "custom-key-789")
        self.assertEqual(model, "agnes-2.5-pro")

    @patch.dict("os.environ", {}, clear=True)
    def test_load_credentials_with_explicit_key_path_str(self):
        custom_key_file = self.tmp_path / "custom_str_key.json"
        custom_key_file.write_text(json.dumps({
            "base_url": "http://custom-str.example.com/v1",
            "api_key": "custom-str-key-456",
        }), encoding="utf-8")

        base, key, model = load_credentials(key_path=str(custom_key_file))
        self.assertEqual(base, "http://custom-str.example.com/v1")
        self.assertEqual(key, "custom-str-key-456")

    @patch.dict("os.environ", {}, clear=True)
    def test_load_credentials_with_nonexistent_custom_key_path(self):
        nonexistent = self.tmp_path / "does_not_exist_key.json"
        base, key, model = load_credentials(key_path=nonexistent)
        self.assertEqual(base, DEFAULT_BASE)
        self.assertIsNone(key)
        self.assertEqual(model, DEFAULT_CHAT_MODEL)

    def test_call_agnes_forwards_key_path(self):
        fake_key_path = self.tmp_path / "fake_forward_key.json"
        with patch("agnes_engine.load_credentials", return_value=("http://127.0.0.1:13000/v1", "sk-forward", "agnes-3.0-flash")) as mock_load, \
             patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = json.dumps({
                "choices": [{"message": {"content": "ok"}}]
            }).encode("utf-8")
            mock_resp.__enter__.return_value = mock_resp
            mock_urlopen.return_value = mock_resp

            res = call_agnes([{"role": "user", "content": "hi"}], key_path=fake_key_path)
            self.assertTrue(res.get("ok"))
            mock_load.assert_called_once_with(key_path=fake_key_path)

    def test_generate_creative_brief_forwards_key_path(self):
        fake_key_path = self.tmp_path / "brief_key.json"
        with patch("agnes_engine.call_agnes", return_value={
            "ok": True,
            "content": json.dumps({
                "title": "测试标题",
                "subtitle": "SUBTITLE",
                "body": "正文内容",
                "author": "AGNES",
                "style_preset": "cinema_01",
                "gen_prompt": "prompt...",
            }),
            "cost_s": 0.1,
            "trace_id": "test-trace",
        }) as mock_call:
            res = generate_creative_brief("测试主题", key_path=fake_key_path)
            self.assertTrue(res.get("ok"))
            self.assertIn("key_path", mock_call.call_args[1])
            self.assertEqual(mock_call.call_args[1]["key_path"], fake_key_path)

    def test_refine_prompt_for_agnes_forwards_key_path(self):
        fake_key_path = self.tmp_path / "refine_key.json"
        with patch("agnes_engine.call_agnes", return_value={
            "ok": True,
            "content": "enhanced optical prompt",
            "cost_s": 0.1,
            "trace_id": "test-trace",
        }) as mock_call:
            res = refine_prompt_for_agnes("raw prompt", key_path=fake_key_path)
            self.assertTrue(res.get("ok"))
            self.assertIn("key_path", mock_call.call_args[1])
            self.assertEqual(mock_call.call_args[1]["key_path"], fake_key_path)

    def test_detect_visual_subjects_forwards_key_path(self):
        fake_key_path = self.tmp_path / "vision_key.json"
        sample_img = self.tmp_path / "test_vis.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")

        with patch("agnes_engine.call_agnes", return_value={
            "ok": True,
            "content": json.dumps([{"x_min": 0.1, "x_max": 0.5, "y_min": 0.2, "y_max": 0.6}]),
        }) as mock_call:
            res = detect_visual_subjects(str(sample_img), key_path=fake_key_path)
            self.assertEqual(len(res), 1)
            self.assertIn("key_path", mock_call.call_args[1])
            self.assertEqual(mock_call.call_args[1]["key_path"], fake_key_path)

    def test_vision_inspect_artwork_forwards_key_path(self):
        fake_key_path = self.tmp_path / "inspect_key.json"
        sample_img = self.tmp_path / "test_inspect.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")

        with patch("agnes_engine.call_agnes", return_value={
            "ok": True,
            "content": json.dumps({"aesthetic_score": 95, "occlusion_risk": "low"}),
            "cost_s": 0.1,
            "trace_id": "test-trace",
        }) as mock_call:
            res = vision_inspect_artwork(str(sample_img), title="测试作品", key_path=fake_key_path)
            self.assertTrue(res.get("ok"))
            self.assertIn("key_path", mock_call.call_args[1])
            self.assertEqual(mock_call.call_args[1]["key_path"], fake_key_path)

    def test_strip_markdown_codeblock(self):
        self.assertEqual(_strip_markdown_codeblock('```json\n{"k": "v"}\n```'), '{"k": "v"}')
        self.assertEqual(_strip_markdown_codeblock('```JSON\n{"k": "v"}\n```'), '{"k": "v"}')
        self.assertEqual(_strip_markdown_codeblock('```javascript\n{"k": "v"}\n```'), '{"k": "v"}')
        self.assertEqual(_strip_markdown_codeblock('```\nplain text\n```'), 'plain text')
        self.assertEqual(_strip_markdown_codeblock('raw text only'), 'raw text only')
        self.assertEqual(_strip_markdown_codeblock(None), '')

    def test_encode_image_data_uri(self):
        png_f = self.tmp_path / "sample.png"
        png_f.write_bytes(b"\x89PNG\r\n\x1a\n")
        uri_png = encode_image_data_uri(png_f)
        self.assertTrue(uri_png.startswith("data:image/png;base64,"))

        webp_f = self.tmp_path / "sample.webp"
        webp_f.write_bytes(b"RIFF....WEBP")
        uri_webp = encode_image_data_uri(webp_f)
        self.assertTrue(uri_webp.startswith("data:image/webp;base64,"))

        jpg_f = self.tmp_path / "sample.jpg"
        jpg_f.write_bytes(b"\xff\xd8\xff")
        uri_jpg = encode_image_data_uri(jpg_f)
        self.assertTrue(uri_jpg.startswith("data:image/jpeg;base64,"))

        gif_f = self.tmp_path / "sample.gif"
        gif_f.write_bytes(b"GIF89a")
        uri_gif = encode_image_data_uri(gif_f)
        self.assertTrue(uri_gif.startswith("data:image/gif;base64,"))

    def test_call_agnes_invalid_base_url(self):
        res = call_agnes([], base_url="ftp://invalid.url")
        self.assertFalse(res["ok"])
        self.assertIn("Base URL 必须以 http:// 或 https:// 开头", res["error"])

    @patch("urllib.request.urlopen")
    def test_call_agnes_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Hello Agnes"}}],
            "usage": {"total_tokens": 42}
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = call_agnes([{"role": "user", "content": "hi"}], retries=0)
        self.assertTrue(res["ok"])
        self.assertEqual(res["content"], "Hello Agnes")
        self.assertEqual(res["usage"]["total_tokens"], 42)
        self.assertIn("cost_s", res)

    @patch("urllib.request.urlopen")
    def test_call_agnes_api_error_response(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "error": {"message": "Rate limit reached"}
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = call_agnes([], retries=0)
        self.assertFalse(res["ok"])
        self.assertIn("API Error: Rate limit reached", res["error"])

    @patch("urllib.request.urlopen")
    def test_call_agnes_empty_choices(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "choices": []
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = call_agnes([], retries=0)
        self.assertFalse(res["ok"])
        self.assertIn("API 返回的 choices 列表为空", res["error"])

    @patch("agnes_engine.get_rate_limiter")
    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_call_agnes_http_error(self, mock_urlopen, mock_sleep, mock_limiter):
        # 401 是客户端错误，不应重试（学习自 agnes-video-generator 最佳实践）
        mock_err = urllib.error.HTTPError(
            url="http://127.0.0.1:18045",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(b'{"message": "Invalid token"}')
        )
        mock_urlopen.side_effect = mock_err

        res = call_agnes([], retries=1)
        self.assertFalse(res["ok"])
        self.assertIn("HTTP 401", res["error"])
        # 4xx 不重试，sleep 不应被调用
        mock_sleep.assert_not_called()

    @patch("agnes_engine.get_rate_limiter")
    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_call_agnes_http_429_retries(self, mock_urlopen, mock_sleep, mock_limiter):
        # 429 应触发指数退避重试
        def make_429(*args, **kwargs):
            raise urllib.error.HTTPError(
                url="http://127.0.0.1:18045",
                code=429,
                msg="Too Many Requests",
                hdrs={},
                fp=io.BytesIO(b'{"message": "Rate limit"}')
            )
        mock_urlopen.side_effect = make_429

        res = call_agnes([], retries=1)
        self.assertFalse(res["ok"])
        self.assertIn("HTTP 429", res["error"])
        # 429 应重试一次
        mock_sleep.assert_called_once()

    def test_generate_creative_brief_empty_topic(self):
        res = generate_creative_brief("")
        self.assertFalse(res["ok"])
        self.assertIn("主题内容不能为空", res["error"])

    @patch("agnes_engine.call_agnes")
    def test_generate_creative_brief_success(self, mock_call):
        mock_call.return_value = {
            "ok": True,
            "content": json.dumps({
                "title": "晨光破晓",
                "subtitle": "dawn of the new era",
                "body": "光线穿透薄雾照耀大地。",
                "author": "Agnes Studio",
                "style_preset": "swiss_01",
            }),
            "cost_s": 0.45,
        }

        res = generate_creative_brief("极简晨光", tone="minimalist")
        self.assertTrue(res["ok"])
        brief = res["brief"]
        self.assertEqual(brief["title"], "晨光破晓")
        self.assertEqual(brief["subtitle"], "DAWN OF THE NEW ERA")
        self.assertEqual(brief["author"], "Agnes Studio")
        self.assertEqual(res["cost_s"], 0.45)

    @patch("agnes_engine.call_agnes")
    def test_generate_creative_brief_failures(self, mock_call):
        # 1. call_gemini failure
        mock_call.return_value = {"ok": False, "error": "Network failed"}
        res = generate_creative_brief("测试")
        self.assertFalse(res["ok"])
        self.assertEqual(res["error"], "Network failed")

        # 2. Malformed JSON
        mock_call.return_value = {"ok": True, "content": "not a json string"}
        res = generate_creative_brief("测试")
        self.assertFalse(res["ok"])
        self.assertIn("JSON解析失败", res["error"])

        # 3. Non-dict JSON
        mock_call.return_value = {"ok": True, "content": '["title1", "title2"]'}
        res = generate_creative_brief("测试")
        self.assertFalse(res["ok"])
        self.assertIn("简报格式非字典对象", res["error"])

    def test_refine_prompt_for_agnes_empty(self):
        res = refine_prompt_for_agnes("   ")
        self.assertFalse(res["ok"])
        self.assertIn("原始提示词不能为空", res["error"])

    @patch("agnes_engine.call_agnes")
    def test_refine_prompt_for_agnes_success_and_failure(self, mock_call):
        mock_call.return_value = {
            "ok": True,
            "content": '"Cinematic soft volumetric light, Hasselblad H6D-100c, ultra clean frame"',
            "cost_s": 0.32,
        }
        res = refine_prompt_for_agnes("Cyberpunk tea master")
        self.assertTrue(res["ok"])
        self.assertEqual(res["prompt"], "Cinematic soft volumetric light, Hasselblad H6D-100c, ultra clean frame")
        self.assertEqual(res["cost_s"], 0.32)

        # Call failure
        mock_call.return_value = {"ok": False, "error": "Gateway timeout"}
        res_fail = refine_prompt_for_agnes("Prompt")
        self.assertFalse(res_fail["ok"])
        self.assertEqual(res_fail["error"], "Gateway timeout")

    def test_detect_visual_subjects_missing_file_and_empty(self):
        self.assertEqual(detect_visual_subjects(""), [])
        self.assertEqual(detect_visual_subjects(None), [])
        self.assertEqual(detect_visual_subjects(str(self.tmp_path / "not_found.png")), [])

    @patch("agnes_engine.call_agnes")
    def test_detect_visual_subjects_success_and_normalization(self, mock_call):
        img_f = self.tmp_path / "test.png"
        img_f.write_bytes(b"\x89PNG\r\n\x1a\n")

        # Coordinates with swapped min/max and string values
        mock_call.return_value = {
            "ok": True,
            "content": json.dumps([
                {"x_min": 0.8, "x_max": 0.2, "y_min": 0.9, "y_max": 0.3},
                {"x_min": "invalid", "x_max": 0.5, "y_min": 0.1, "y_max": 0.2},
                {"x_min": 0.0, "x_max": 1.5, "y_min": -0.5, "y_max": 1.0},
            ])
        }

        boxes = detect_visual_subjects(str(img_f))
        self.assertEqual(len(boxes), 2)
        # Swapped coords normalized
        self.assertAlmostEqual(boxes[0]["x_min"], 0.2)
        self.assertAlmostEqual(boxes[0]["x_max"], 0.8)
        self.assertAlmostEqual(boxes[0]["y_min"], 0.3)
        self.assertAlmostEqual(boxes[0]["y_max"], 0.9)
        # Clamped coords
        self.assertAlmostEqual(boxes[1]["x_min"], 0.0)
        self.assertAlmostEqual(boxes[1]["x_max"], 1.0)
        self.assertAlmostEqual(boxes[1]["y_min"], 0.0)
        self.assertAlmostEqual(boxes[1]["y_max"], 1.0)

    @patch("agnes_engine.call_agnes")
    def test_detect_visual_subjects_api_failure(self, mock_call):
        img_f = self.tmp_path / "test.png"
        img_f.write_bytes(b"\x89PNG\r\n\x1a\n")

        mock_call.return_value = {"ok": False, "error": "timeout"}
        self.assertEqual(detect_visual_subjects(str(img_f)), [])

    def test_vision_inspect_artwork_missing_file_and_empty(self):
        res_empty = vision_inspect_artwork("")
        self.assertFalse(res_empty["ok"])
        self.assertIn("图片路径不能为空", res_empty["error"])

        res_missing = vision_inspect_artwork(str(self.tmp_path / "not_found.png"))
        self.assertFalse(res_missing["ok"])
        self.assertIn("文件不存在", res_missing["error"])

    @patch("agnes_engine.call_agnes")
    def test_vision_inspect_artwork_success_and_failures(self, mock_call):
        img_f = self.tmp_path / "artwork.png"
        img_f.write_bytes(b"\x89PNG\r\n\x1a\n")

        # Success case
        mock_call.return_value = {
            "ok": True,
            "content": json.dumps({
                "aesthetic_score": 95,
                "occlusion_risk": "low",
                "text_legibility": "excellent",
                "negative_space_quality": "balanced",
                "critique": "构图严谨，留白充分。",
                "suggestions": ["无修改建议"]
            }),
            "cost_s": 0.52,
        }
        res = vision_inspect_artwork(str(img_f), title="艺术海报")
        self.assertTrue(res["ok"])
        self.assertEqual(res["inspection"]["aesthetic_score"], 95)
        self.assertEqual(res["cost_s"], 0.52)

        # Non-dict failure
        mock_call.return_value = {"ok": True, "content": '["score", 95]'}
        res_non_dict = vision_inspect_artwork(str(img_f))
        self.assertFalse(res_non_dict["ok"])
        self.assertIn("质检结果格式非字典对象", res_non_dict["error"])

        # Call error
        mock_call.return_value = {"ok": False, "error": "Quota exceeded"}
        res_call_err = vision_inspect_artwork(str(img_f))
        self.assertFalse(res_call_err["ok"])
        self.assertEqual(res_call_err["error"], "Quota exceeded")


class TestAgnesRateLimiter(unittest.TestCase):
    """Agnes 全局令牌桶限速器与重试逻辑单元测试"""

    def setUp(self):
        reset_rate_limiter()

    def tearDown(self):
        reset_rate_limiter()

    def test_should_retry_http(self):
        # 429 和 5xx 应该重试
        self.assertTrue(_should_retry_http(429))
        self.assertTrue(_should_retry_http(500))
        self.assertTrue(_should_retry_http(502))
        self.assertTrue(_should_retry_http(503))
        self.assertTrue(_should_retry_http(504))

        # 4xx (非 429) 和 2xx 不重试
        self.assertFalse(_should_retry_http(400))
        self.assertFalse(_should_retry_http(401))
        self.assertFalse(_should_retry_http(403))
        self.assertFalse(_should_retry_http(404))
        self.assertFalse(_should_retry_http(422))
        self.assertFalse(_should_retry_http(200))
        self.assertFalse(_should_retry_http(201))

    def test_rate_limiter_init_and_stats(self):
        limiter = AgnesRateLimiter(rate_per_minute=30, max_burst=5)
        self.assertEqual(limiter.max_tokens, 5)
        self.assertAlmostEqual(limiter.refill_rate, 0.5)
        stats = limiter.stats
        self.assertEqual(stats["effective_rate_per_min"], 30.0)
        self.assertEqual(stats["max_burst"], 5)
        self.assertEqual(stats["total_waits"], 0)
        self.assertEqual(stats["total_wait_seconds"], 0.0)

    def test_rate_limiter_acquire_immediate(self):
        limiter = AgnesRateLimiter(rate_per_minute=60, max_burst=2)
        limiter.acquire()
        self.assertAlmostEqual(limiter.tokens, 1.0, places=1)
        self.assertEqual(limiter.stats["total_waits"], 0)

    def test_rate_limiter_acquire_blocks_when_empty(self):
        limiter = AgnesRateLimiter(rate_per_minute=60, max_burst=1)
        limiter.acquire()
        self.assertAlmostEqual(limiter.tokens, 0.0, places=1)

        with patch("time.sleep") as mock_sleep, patch("time.monotonic") as mock_mono:
            mock_mono.return_value = limiter.last_refill
            limiter.acquire()
            mock_sleep.assert_called_once_with(1.0)
            self.assertEqual(limiter.stats["total_waits"], 1)
            self.assertAlmostEqual(limiter.stats["total_wait_seconds"], 1.0)

    def test_rate_limiter_refills_over_time(self):
        limiter = AgnesRateLimiter(rate_per_minute=60, max_burst=4)
        limiter.tokens = 0.0
        limiter.last_refill = 100.0

        with patch("time.monotonic", return_value=102.5):
            limiter.acquire()
            self.assertAlmostEqual(limiter.tokens, 1.5, places=1)

    def test_get_and_reset_rate_limiter_singleton(self):
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        self.assertIs(limiter1, limiter2)

        reset_rate_limiter()
        limiter3 = get_rate_limiter()
        self.assertIsNot(limiter1, limiter3)

class TestRenderCinemaPoster(unittest.TestCase):
    """测试电影级海报渲染器 render_cinema_poster 及其版式模板规范与鲁棒性"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_b64_with_data_uri(self):
        raw_uri = "data:" + "image/png;base64,mocked_test_data"
        result = cinema_b64(raw_uri)
        self.assertEqual(result, raw_uri)

    def test_b64_mime_types(self):
        types = [
            ("sample.png", "image/png"),
            ("sample.jpg", "image/jpeg"),
            ("sample.jpeg", "image/jpeg"),
            ("sample.webp", "image/webp"),
            ("sample.svg", "image/svg+xml"),
            ("sample.gif", "image/gif"),
        ]
        for filename, expected_mime in types:
            file_p = self.tmp_path / filename
            file_p.write_bytes(b"\x00\x01\x02\x03")
            uri = cinema_b64(file_p)
            self.assertTrue(uri.startswith(f"data:{expected_mime};base64,"))
            # Test string path support as well
            uri_str = cinema_b64(str(file_p))
            self.assertTrue(uri_str.startswith(f"data:{expected_mime};base64,"))

    def test_b64_missing_file_raises_filenotfound(self):
        with self.assertRaises(FileNotFoundError):
            cinema_b64(self.tmp_path / "non_existent_poster.png")

    def test_sanitize_img_uri(self):
        malicious = "data:image/png;base64,abc\r\ndef'\"<script>"
        sanitized = cinema_sanitize_img_uri(malicious)
        self.assertNotIn("\r", sanitized)
        self.assertNotIn("\n", sanitized)
        self.assertNotIn("'", sanitized)
        self.assertNotIn('"', sanitized)
        self.assertNotIn("<", sanitized)
        self.assertNotIn(">", sanitized)
        self.assertIn("%27", sanitized)
        self.assertIn("%22", sanitized)
        self.assertIn("%3C", sanitized)
        self.assertIn("%3E", sanitized)

    def test_wrap_css_structure(self):
        html = cinema_wrap("data:image/png;base64,test", "<div class='content'>Cinema Test</div>", extra_css=".test{color:red}")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<div class='content'>Cinema Test</div>", html)
        self.assertIn(".test{color:red}", html)
        self.assertIn("src=\"data:image/png;base64,test\"", html)
        self.assertIn("font-family:'NSB'", html)
        self.assertIn("font-family:'PHH'", html)

    def test_build_film_bottom_html_escaping_and_custom_text(self):
        # 1. 默认参数
        html_default = build_film_bottom_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("A FILM STILL · AGNES", html_default)
        self.assertIn("180deg,transparent 42%", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_film_bottom_html(
            "data:image/png;base64,abc",
            title="<危险标题>",
            latin="ESCAPE & TEST",
            tagline="“标语内容”",
        )
        self.assertNotIn("<危险标题>", html_custom)
        self.assertIn("&lt;危险标题&gt;", html_custom)
        self.assertIn("ESCAPE &amp; TEST", html_custom)
        self.assertIn("“标语内容”", html_custom)

        # 3. None 参数防御
        html_none = build_film_bottom_html("data:image/png;base64,abc", title=None, latin=None, tagline=None)
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)

    def test_build_film_top_html_escaping_and_custom_text(self):
        # 1. 默认参数
        html_default = build_film_top_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("她把城市调成静音", html_default)
        self.assertIn("rgba(0,0,0,.72) 0%", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_film_top_html(
            "data:image/png;base64,abc",
            title="<黑客帝国>",
            latin="THE MATRIX & REVOLUTIONS",
            tagline="觉醒吧，尼奥",
        )
        self.assertNotIn("<黑客帝国>", html_custom)
        self.assertIn("&lt;黑客帝国&gt;", html_custom)
        self.assertIn("THE MATRIX &amp; REVOLUTIONS", html_custom)
        self.assertIn("觉醒吧，尼奥", html_custom)

        # 3. None 参数防御
        html_none = build_film_top_html("data:image/png;base64,abc", title=None, latin=None, tagline=None)
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)

    def test_build_side_rail_html_escaping_and_custom_text(self):
        # 1. 默认参数
        html_default = build_side_rail_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("writing-mode:vertical-rl", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_side_rail_html(
            "data:image/png;base64,abc",
            title="<银翼杀手>",
            latin="BLADE RUNNER & 2049",
            tagline="所有这些时刻都将消逝于时间中",
        )
        self.assertNotIn("<银翼杀手>", html_custom)
        self.assertIn("&lt;银翼杀手&gt;", html_custom)
        self.assertIn("BLADE RUNNER &amp; 2049", html_custom)
        self.assertIn("所有这些时刻都将消逝于时间中", html_custom)

        # 3. None 参数防御
        html_none = build_side_rail_html("data:image/png;base64,abc", title=None, latin=None, tagline=None)
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)

    def test_shot_mkdir_and_invocation(self):
        out_target = self.tmp_path / "deep" / "nested" / "cinema.png"
        fake_page = MagicMock()
        fake_browser = MagicMock()
        fake_browser.new_page.return_value = fake_page
        fake_chromium = MagicMock()
        fake_chromium.launch.return_value = fake_browser
        fake_playwright_ctx = MagicMock()
        fake_playwright_ctx.chromium = fake_chromium
        fake_playwright_cm = MagicMock()
        fake_playwright_cm.__enter__.return_value = fake_playwright_ctx

        # When screenshot is called, simulate creating file
        def fake_screenshot(path, type="png"):
            Path(path).write_bytes(b"\x89PNGfake")

        fake_page.screenshot.side_effect = fake_screenshot

        with patch("playwright.sync_api.sync_playwright", return_value=fake_playwright_cm):
            res_path = cinema_shot("<html><body>Cinema</body></html>", out_target, timeout_ms=10)
            self.assertEqual(res_path, out_target)
            self.assertTrue(out_target.exists())
            fake_page.set_content.assert_called_once_with("<html><body>Cinema</body></html>")
            fake_page.wait_for_timeout.assert_called_once_with(10)
            fake_browser.close.assert_called_once()

    @patch("render_cinema_poster.shot")
    def test_film_bottom_film_top_side_rail_integration(self, mock_shot):
        sample_img = self.tmp_path / "cinema_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out.png"

        mock_shot.return_value = out_p

        # 1. film_bottom
        res_bottom = film_bottom(sample_img, out_p, title="夜航底标", latin="Night Flight", tagline="AGNES FILM")
        self.assertEqual(res_bottom, out_p)
        mock_shot.assert_called()
        call_html_bottom = mock_shot.call_args[0][0]
        self.assertIn("夜航底标", call_html_bottom)
        self.assertIn("Night Flight", call_html_bottom)

        # 2. film_top
        res_top = film_top(sample_img, out_p, title="夜航顶标", latin="Night Top", tagline="Top Tagline")
        self.assertEqual(res_top, out_p)
        call_html_top = mock_shot.call_args[0][0]
        self.assertIn("夜航顶标", call_html_top)
        self.assertIn("Night Top", call_html_top)

        # 3. side_rail
        res_rail = side_rail(sample_img, out_p, title="夜航侧轴", latin="Night Rail", tagline="Side Tagline")
        self.assertEqual(res_rail, out_p)
        call_html_rail = mock_shot.call_args[0][0]
        self.assertIn("夜航侧轴", call_html_rail)
        self.assertIn("Night Rail", call_html_rail)

    @patch("render_cinema_poster.shot")
    def test_main_execution(self, mock_shot):
        mock_shot.return_value = self.tmp_path / "mock.png"
        # Calling main shouldn't raise any exception
        render_cinema_poster.main()
        self.assertEqual(mock_shot.call_count, 3)

    @patch("playwright.sync_api.sync_playwright")
    def test_shot_quiet_mode(self, mock_playwright):
        from contextlib import redirect_stdout

        fake_page = MagicMock()
        fake_browser = MagicMock()
        fake_browser.new_page.return_value = fake_page
        mock_p_inst = MagicMock()
        mock_p_inst.chromium.launch.return_value = fake_browser
        mock_playwright.return_value.__enter__.return_value = mock_p_inst

        out_p = self.tmp_path / "shot_quiet.png"
        out_p.write_bytes(b"\x89PNG\r\n\x1a\n")

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = cinema_shot("<html></html>", out_p, quiet=True)
        self.assertEqual(ret, out_p)
        self.assertEqual(buf.getvalue().strip(), "")

    @patch("render_cinema_poster.shot")
    def test_render_styles_quiet_mode(self, mock_shot):
        sample_img = self.tmp_path / "cinema_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out.png"
        mock_shot.return_value = out_p

        res = film_bottom(sample_img, out_p, quiet=True)
        self.assertEqual(res, out_p)
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

        res_top = film_top(sample_img, out_p, quiet=True)
        self.assertEqual(res_top, out_p)
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

        res_rail = side_rail(sample_img, out_p, quiet=True)
        self.assertEqual(res_rail, out_p)
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

    @patch("render_cinema_poster.shot")
    def test_list_and_render_cinema_poster_style(self, mock_shot):
        styles = list_cinema_poster_styles()
        self.assertEqual(len(styles), 3)
        keys = {s["key"] for s in styles}
        self.assertEqual(keys, {"bottom", "top", "rail"})

        sample_img = self.tmp_path / "cinema_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "dispatched.png"
        mock_shot.return_value = out_p

        ret = render_cinema_poster_style("rail", sample_img, out_p, title="自定义", latin="CUSTOM", quiet=True)
        self.assertEqual(ret, out_p)
        mock_shot.assert_called()
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

        with self.assertRaises(KeyError):
            render_cinema_poster_style("unknown", sample_img, out_p)

    def test_cli_main_list_mode(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cinema_poster_main(["--list"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Agnes Studio 可用电影级海报风格预设:", out)
        self.assertIn("bottom", out)
        self.assertIn("rail", out)

    @patch("render_cinema_poster.shot")
    def test_cli_main_single_style_with_custom_src_and_out(self, mock_shot):
        sample_img = self.tmp_path / "cinema_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "single_out.png"
        mock_shot.return_value = out_p

        code = cinema_poster_main([
            "--style", "top",
            "--src", str(sample_img),
            "--out", str(out_p),
            "--title", "极简夜航",
            "--latin", "MINIMAL NIGHT",
            "--tagline", "全新视觉体验",
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_shot.call_count, 1)

    @patch("render_cinema_poster.shot")
    def test_cli_main_all_mode(self, mock_shot):
        sample_img = self.tmp_path / "cinema_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"
        mock_shot.return_value = self.tmp_path / "out.png"

        code = cinema_poster_main([
            "--style", "all",
            "--src", str(sample_img),
            "--out", str(out_base),
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_shot.call_count, 3)

    def test_cli_main_missing_src_strict_mode(self):
        missing_src = self.tmp_path / "does_not_exist.png"
        code_strict = cinema_poster_main([
            "--style", "bottom",
            "--src", str(missing_src),
            "--strict",
            "--quiet",
        ])
        self.assertEqual(code_strict, 1)

        code_lenient = cinema_poster_main([
            "--style", "bottom",
            "--src", str(missing_src),
            "--quiet",
        ])
        self.assertEqual(code_lenient, 0)

    @patch("render_cinema_poster.shot")
    def test_cli_main_quiet_mode_suppresses_stdout(self, mock_shot):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "cinema_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "quiet_out.png"
        mock_shot.return_value = out_p

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cinema_poster_main([
                "--style", "bottom",
                "--src", str(sample_img),
                "--out", str(out_p),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_build_arg_parser(self):
        parser = cinema_build_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("style", actions)
        self.assertIn("src", actions)
        self.assertIn("out", actions)
        self.assertIn("out_dir", actions)
        self.assertIn("title", actions)
        self.assertIn("latin", actions)
        self.assertIn("tagline", actions)
        self.assertIn("list", actions)
        self.assertIn("json", actions)
        self.assertIn("dry_run", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_cli_main_list_json(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cinema_poster_main(["--list", "--json"])
        self.assertEqual(code, 0)
        items = json.loads(buf.getvalue())
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 3)
        keys = [x["key"] for x in items]
        self.assertEqual(keys, ["bottom", "top", "rail"])
        for item in items:
            self.assertIn("default_file", item)
            self.assertIn("default_tagline", item)
            self.assertIn("description", item)

    def test_shot_dry_run_returns_path_without_playwright(self):
        out_target = self.tmp_path / "dry_run_dir" / "poster_dry.png"
        res = cinema_shot("<html><body>Dry</body></html>", out_target, quiet=True, dry_run=True)
        self.assertEqual(res, out_target)
        self.assertTrue(out_target.parent.exists())

    def test_render_cinema_poster_style_dry_run(self):
        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_target = self.tmp_path / "dry_style.png"
        res = render_cinema_poster_style("rail", sample_img, out_target, dry_run=True, quiet=True)
        self.assertEqual(res, out_target)

    def test_cli_main_dry_run_single(self):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "single_dry.png"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cinema_poster_main([
                "--style", "bottom",
                "--src", str(sample_img),
                "--out", str(out_p),
                "--dry-run",
            ])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("(dry_run)", out)
        self.assertIn("single_dry.png", out)

    def test_cli_main_dry_run_all(self):
        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"

        code = cinema_poster_main([
            "--style", "all",
            "--src", str(sample_img),
            "--out", str(out_base),
            "--dry-run",
            "--quiet",
        ])
        self.assertEqual(code, 0)

    def test_cli_main_dry_run_json_output(self):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cinema_poster_main([
                "--style", "all",
                "--src", str(sample_img),
                "--out", str(out_base),
                "--dry-run",
                "--json",
            ])
        self.assertEqual(code, 0)
        items = json.loads(buf.getvalue())
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 3)
        for it in items:
            self.assertEqual(it["status"], "ok")
            self.assertTrue(it["dry_run"])
            self.assertIn("style", it)
            self.assertIn("output", it)

    def test_cli_main_missing_src_json_error(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cinema_poster_main([
                "--src", str(self.tmp_path / "not_there.png"),
                "--json",
                "--strict",
            ])
        self.assertEqual(code, 1)
        err = json.loads(buf.getvalue())
        self.assertFalse(err["ok"])
        self.assertIn("error", err)

    @patch("render_cinema_poster.render_cinema_poster_style", side_effect=RuntimeError("Simulated cinema render crash"))
    def test_main_cli_exception_stderr_output(self, mock_render):
        import io
        from contextlib import redirect_stderr
        sample_img = self.tmp_path / "cinema_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = cinema_poster_main([
                "--style", "bottom",
                "--src", str(sample_img),
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 电影级海报渲染失败: Simulated cinema render crash", buf.getvalue())

    @patch("render_cinema_poster.render_cinema_poster_style", side_effect=RuntimeError("Simulated quiet crash"))
    def test_main_cli_exception_quiet_mode(self, mock_render):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        sample_img = self.tmp_path / "cinema_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            code = cinema_poster_main([
                "--style", "bottom",
                "--src", str(sample_img),
                "-q",
            ])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_main_cli_missing_src_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        missing_src = self.tmp_path / "non_existent_cinema_src.png"
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = cinema_poster_main([
                "--style", "bottom",
                "--src", str(missing_src),
                "--strict",
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 找不到输入底图", buf.getvalue())

    @patch("render_cinema_poster.render_cinema_poster_style", side_effect=RuntimeError("Simulated JSON crash"))
    def test_cli_main_exception_json_error(self, mock_render):
        import io
        from contextlib import redirect_stdout
        sample_img = self.tmp_path / "cinema_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cinema_poster_main([
                "--style", "bottom",
                "--src", str(sample_img),
                "--json",
            ])
        self.assertEqual(code, 1)
        err = json.loads(buf.getvalue())
        self.assertFalse(err["ok"])
        self.assertIn("error", err)
        self.assertIn("Simulated JSON crash", err["error"])

    @patch("render_cinema_poster.render_cinema_poster_style", side_effect=RuntimeError("Simulated stderr crash"))
    def test_cli_main_exception_stderr_output(self, mock_render):
        import io
        from contextlib import redirect_stderr
        sample_img = self.tmp_path / "cinema_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = cinema_poster_main([
                "--style", "bottom",
                "--src", str(sample_img),
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 电影级海报渲染失败: Simulated stderr crash", buf.getvalue())

    @patch("render_cinema_poster.render_cinema_poster_style", side_effect=RuntimeError("Simulated quiet crash"))
    def test_cli_main_exception_quiet_mode(self, mock_render):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        sample_img = self.tmp_path / "cinema_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            code = cinema_poster_main([
                "--style", "bottom",
                "--src", str(sample_img),
                "-q",
            ])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_cli_list_exception_json_output(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("render_cinema_poster.list_cinema_poster_styles", side_effect=RuntimeError("Cinema styles index corrupted")):
            with redirect_stdout(buf):
                code = cinema_poster_main(["--list", "--json"])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "Cinema styles index corrupted")

    def test_cli_list_exception_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("render_cinema_poster.list_cinema_poster_styles", side_effect=RuntimeError("Cinema styles index corrupted")):
            with redirect_stderr(buf):
                code = cinema_poster_main(["--list"])
        self.assertEqual(code, 1)
        self.assertIn("❌ 电影级海报渲染失败: Cinema styles index corrupted", buf.getvalue())

    def test_cli_list_exception_quiet_mode(self):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with patch("render_cinema_poster.list_cinema_poster_styles", side_effect=RuntimeError("Cinema styles index corrupted")):
            with redirect_stdout(out_buf), redirect_stderr(err_buf):
                code = cinema_poster_main(["--list", "-q"])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")



class TestRenderDramaPoster(unittest.TestCase):
    """测试反 slop 巨幅戏剧性海报渲染器 render_drama_poster 及其三大视觉构图模式与鲁棒性"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_b64_with_data_uri(self):
        raw_uri = "data:image/png;base64,mocked_drama_data"
        result = drama_b64(raw_uri)
        self.assertEqual(result, raw_uri)

    def test_b64_mime_types(self):
        types = [
            ("sample.png", "image/png"),
            ("sample.jpg", "image/jpeg"),
            ("sample.jpeg", "image/jpeg"),
            ("sample.webp", "image/webp"),
            ("sample.svg", "image/svg+xml"),
            ("sample.gif", "image/gif"),
        ]
        for filename, expected_mime in types:
            file_p = self.tmp_path / filename
            file_p.write_bytes(b"\x00\x01\x02\x03")
            uri = drama_b64(file_p)
            self.assertTrue(uri.startswith(f"data:{expected_mime};base64,"))
            uri_str = drama_b64(str(file_p))
            self.assertTrue(uri_str.startswith(f"data:{expected_mime};base64,"))

    def test_b64_missing_file_raises_filenotfound(self):
        with self.assertRaises(FileNotFoundError):
            drama_b64(self.tmp_path / "non_existent_poster.png")

    def test_sanitize_img_uri(self):
        malicious = "data:image/png;base64,abc\r\ndef'\"<script>"
        sanitized = drama_sanitize_img_uri(malicious)
        self.assertNotIn("\r", sanitized)
        self.assertNotIn("\n", sanitized)
        self.assertNotIn("'", sanitized)
        self.assertNotIn('"', sanitized)
        self.assertNotIn("<", sanitized)
        self.assertNotIn(">", sanitized)
        self.assertIn("%27", sanitized)
        self.assertIn("%22", sanitized)
        self.assertIn("%3C", sanitized)
        self.assertIn("%3E", sanitized)

    def test_css_generation(self):
        css_content = drama_css(".extra{color:blue;}")
        self.assertIn("@font-face", css_content)
        self.assertIn(".extra{color:blue;}", css_content)
        self.assertIn("font-family:'NSB'", css_content)
        self.assertIn("font-family:'PHH'", css_content)
        self.assertIn("font-family:'PHM'", css_content)

    def test_build_mega_bleed_html_escaping_and_custom_text(self):
        # 1. 默认参数
        html_default = build_mega_bleed_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("Agnes · 2026", html_default)
        self.assertIn("font-size:176px", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_mega_bleed_html(
            "data:image/png;base64,abc",
            title="<巨字裁切>",
            subtitle_top="TOP & SUB",
            subtitle_bottom="“极简主义”",
            extra_css=".custom{display:flex;}",
        )
        self.assertNotIn("<巨字裁切>", html_custom)
        self.assertIn("&lt;巨字裁切&gt;", html_custom)
        self.assertIn("TOP &amp; SUB", html_custom)
        self.assertIn("“极简主义”", html_custom)
        self.assertIn(".custom{display:flex;}", html_custom)

        # 3. None 参数防御
        html_none = build_mega_bleed_html("data:image/png;base64,abc", title=None, subtitle_top=None, subtitle_bottom=None)
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)
        self.assertIn("Agnes · 2026", html_none)

    def test_build_hard_field_html_escaping_and_custom_text(self):
        # 1. 默认参数
        html_default = build_hard_field_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("她把城市调成静音", html_default)
        self.assertIn("A Film Still", html_default)
        self.assertIn("background:#0A0A0C", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_hard_field_html(
            "data:image/png;base64,abc",
            title="<色场反转>",
            tagline="黑色力量 & 寂静",
            micro_text="AGNES EXCLUSIVE",
        )
        self.assertNotIn("<色场反转>", html_custom)
        self.assertIn("&lt;色场反转&gt;", html_custom)
        self.assertIn("黑色力量 &amp; 寂静", html_custom)
        self.assertIn("AGNES EXCLUSIVE", html_custom)

        # 3. None 参数防御
        html_none = build_hard_field_html("data:image/png;base64,abc", title=None, tagline=None, micro_text=None)
        self.assertIn("夜航", html_none)
        self.assertIn("她把城市调成静音", html_none)
        self.assertIn("A Film Still", html_none)

    def test_build_chinese_corner_html_escaping_and_custom_text(self):
        # 1. 默认参数
        html_default = build_chinese_corner_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("Agnes Studio", html_default)
        self.assertIn("航", html_default)
        self.assertIn("writing-mode:vertical-rl", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_chinese_corner_html(
            "data:image/png;base64,abc",
            title="<边角计白>",
            subtitle="CHINESE & MODERN",
            bottom_label="Studio <Agnes>",
            seal_char="印",
        )
        self.assertNotIn("<边角计白>", html_custom)
        self.assertIn("&lt;边角计白&gt;", html_custom)
        self.assertIn("CHINESE &amp; MODERN", html_custom)
        self.assertIn("Studio &lt;Agnes&gt;", html_custom)
        self.assertIn("印", html_custom)

        # 3. None 参数防御
        html_none = build_chinese_corner_html("data:image/png;base64,abc", title=None, subtitle=None, bottom_label=None, seal_char=None)
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)
        self.assertIn("Agnes Studio", html_none)
        self.assertIn("航", html_none)

    def test_shot_mkdir_and_invocation(self):
        out_target = self.tmp_path / "deep" / "nested" / "drama.png"
        fake_page = MagicMock()
        fake_browser = MagicMock()
        fake_browser.new_page.return_value = fake_page
        fake_chromium = MagicMock()
        fake_chromium.launch.return_value = fake_browser
        fake_playwright_ctx = MagicMock()
        fake_playwright_ctx.chromium = fake_chromium
        fake_playwright_cm = MagicMock()
        fake_playwright_cm.__enter__.return_value = fake_playwright_ctx

        def fake_screenshot(path, type="png"):
            Path(path).write_bytes(b"\x89PNGfake_drama")

        fake_page.screenshot.side_effect = fake_screenshot

        with patch("playwright.sync_api.sync_playwright", return_value=fake_playwright_cm):
            res_path = drama_shot("<html><body>Drama</body></html>", out_target, timeout_ms=10)
            self.assertEqual(res_path, out_target)
            self.assertTrue(out_target.exists())
            fake_page.set_content.assert_called_once_with("<html><body>Drama</body></html>")
            fake_page.wait_for_timeout.assert_called_once_with(10)
            fake_browser.close.assert_called_once()

    @patch("render_drama_poster.shot")
    def test_mega_bleed_hard_field_chinese_corner_integration(self, mock_shot):
        sample_img = self.tmp_path / "drama_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out_drama.png"
        mock_shot.return_value = out_p

        # 1. mega_bleed
        res_bleed = mega_bleed(sample_img, out_p, title="巨标裁切测试", subtitle_top="TOP DRAMA", subtitle_bottom="BOTTOM DRAMA")
        self.assertEqual(res_bleed, out_p)
        mock_shot.assert_called()
        call_html_bleed = mock_shot.call_args[0][0]
        self.assertIn("巨标裁切测试", call_html_bleed)
        self.assertIn("TOP DRAMA", call_html_bleed)
        self.assertIn("BOTTOM DRAMA", call_html_bleed)

        # 2. hard_field
        res_field = hard_field(sample_img, out_p, title="硬色场反转测试", tagline="反转标语", micro_text="微小说明")
        self.assertEqual(res_field, out_p)
        call_html_field = mock_shot.call_args[0][0]
        self.assertIn("硬色场反转测试", call_html_field)
        self.assertIn("反转标语", call_html_field)
        self.assertIn("微小说明", call_html_field)

        # 3. chinese_corner
        res_corner = chinese_corner(sample_img, out_p, title="边角式测试", subtitle="CORNER LATIN", bottom_label="AGNES BOT", seal_char="章")
        self.assertEqual(res_corner, out_p)
        call_html_corner = mock_shot.call_args[0][0]
        self.assertIn("边角式测试", call_html_corner)
        self.assertIn("CORNER LATIN", call_html_corner)
        self.assertIn("AGNES BOT", call_html_corner)
        self.assertIn("章", call_html_corner)

    @patch("render_drama_poster.shot")
    def test_main_execution(self, mock_shot):
        mock_shot.return_value = self.tmp_path / "mock_drama.png"
        render_drama_poster.main()
        self.assertEqual(mock_shot.call_count, 3)

    @patch("playwright.sync_api.sync_playwright")
    def test_shot_quiet_mode(self, mock_playwright):
        from contextlib import redirect_stdout

        fake_page = MagicMock()
        fake_browser = MagicMock()
        fake_browser.new_page.return_value = fake_page
        mock_p_inst = MagicMock()
        mock_p_inst.chromium.launch.return_value = fake_browser
        mock_playwright.return_value.__enter__.return_value = mock_p_inst

        out_p = self.tmp_path / "shot_quiet.png"
        out_p.write_bytes(b"\x89PNG\r\n\x1a\n")

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = drama_shot("<html></html>", out_p, quiet=True)
        self.assertEqual(ret, out_p)
        self.assertEqual(buf.getvalue().strip(), "")

    @patch("render_drama_poster.shot")
    def test_render_styles_quiet_mode(self, mock_shot):
        sample_img = self.tmp_path / "drama_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out.png"
        mock_shot.return_value = out_p

        res_bleed = mega_bleed(sample_img, out_p, quiet=True)
        self.assertEqual(res_bleed, out_p)
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

        res_field = hard_field(sample_img, out_p, quiet=True)
        self.assertEqual(res_field, out_p)
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

        res_corner = chinese_corner(sample_img, out_p, quiet=True)
        self.assertEqual(res_corner, out_p)
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

    @patch("render_drama_poster.shot")
    def test_list_and_render_drama_poster_style(self, mock_shot):
        styles = list_drama_poster_styles()
        self.assertEqual(len(styles), 3)
        keys = {s["key"] for s in styles}
        self.assertEqual(keys, {"mega_bleed", "hard_field", "chinese_corner"})

        sample_img = self.tmp_path / "drama_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "dispatched.png"
        mock_shot.return_value = out_p

        ret = render_drama_poster_style(
            "chinese_corner",
            sample_img,
            out_p,
            title="戏曲夜航",
            subtitle="OPERA NIGHT",
            tagline="AGNES",
            seal="印",
            quiet=True,
        )
        self.assertEqual(ret, out_p)
        mock_shot.assert_called()
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

        with self.assertRaises(KeyError):
            render_drama_poster_style("unknown_style", sample_img, out_p)

    def test_cli_main_list_mode(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = drama_poster_main(["--list"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Agnes Studio 可用戏剧性海报风格预设:", out)
        self.assertIn("mega_bleed", out)
        self.assertIn("hard_field", out)
        self.assertIn("chinese_corner", out)

    @patch("render_drama_poster.shot")
    def test_cli_main_single_style_with_custom_src_and_out(self, mock_shot):
        sample_img = self.tmp_path / "drama_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "single_out.png"
        mock_shot.return_value = out_p

        code = drama_poster_main([
            "--style", "hard_field",
            "--src", str(sample_img),
            "--out", str(out_p),
            "--title", "反转硬场",
            "--subtitle", "SUBTITLE",
            "--tagline", "TAGLINE",
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_shot.call_count, 1)

    @patch("render_drama_poster.shot")
    def test_cli_main_all_mode(self, mock_shot):
        sample_img = self.tmp_path / "drama_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"
        mock_shot.return_value = self.tmp_path / "out.png"

        code = drama_poster_main([
            "--style", "all",
            "--src", str(sample_img),
            "--out", str(out_base),
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_shot.call_count, 3)

    def test_cli_main_missing_src_strict_mode(self):
        missing_src = self.tmp_path / "does_not_exist.png"
        code_strict = drama_poster_main([
            "--style", "mega_bleed",
            "--src", str(missing_src),
            "--strict",
            "--quiet",
        ])
        self.assertEqual(code_strict, 1)

        code_lenient = drama_poster_main([
            "--style", "mega_bleed",
            "--src", str(missing_src),
            "--quiet",
        ])
        self.assertEqual(code_lenient, 0)

    @patch("render_drama_poster.shot")
    def test_cli_main_quiet_mode_suppresses_stdout(self, mock_shot):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "drama_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "quiet_out.png"
        mock_shot.return_value = out_p

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = drama_poster_main([
                "--style", "mega_bleed",
                "--src", str(sample_img),
                "--out", str(out_p),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_build_arg_parser(self):
        parser = drama_build_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("style", actions)
        self.assertIn("src", actions)
        self.assertIn("out", actions)
        self.assertIn("out_dir", actions)
        self.assertIn("title", actions)
        self.assertIn("subtitle", actions)
        self.assertIn("tagline", actions)
        self.assertIn("seal", actions)
        self.assertIn("list", actions)
        self.assertIn("json", actions)
        self.assertIn("dry_run", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_cli_main_list_json(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = drama_poster_main(["--list", "--json"])
        self.assertEqual(code, 0)
        items = json.loads(buf.getvalue())
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 3)
        keys = [x["key"] for x in items]
        self.assertEqual(keys, ["mega_bleed", "hard_field", "chinese_corner"])
        for item in items:
            self.assertIn("default_file", item)
            self.assertIn("description", item)

    def test_shot_dry_run_returns_path_without_playwright(self):
        out_target = self.tmp_path / "dry_run_dir" / "poster_dry.png"
        res = drama_shot("<html><body>Dry</body></html>", out_target, quiet=True, dry_run=True)
        self.assertEqual(res, out_target)
        self.assertTrue(out_target.parent.exists())

    def test_render_drama_poster_style_dry_run(self):
        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_target = self.tmp_path / "dry_style.png"
        res = render_drama_poster_style("chinese_corner", sample_img, out_target, dry_run=True, quiet=True)
        self.assertEqual(res, out_target)

    def test_cli_main_dry_run_single(self):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "single_dry.png"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = drama_poster_main([
                "--style", "hard_field",
                "--src", str(sample_img),
                "--out", str(out_p),
                "--dry-run",
            ])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("(dry_run)", out)
        self.assertIn("single_dry.png", out)

    def test_cli_main_dry_run_all(self):
        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"

        code = drama_poster_main([
            "--style", "all",
            "--src", str(sample_img),
            "--out", str(out_base),
            "--dry-run",
            "--quiet",
        ])
        self.assertEqual(code, 0)

    def test_cli_main_dry_run_json_output(self):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = drama_poster_main([
                "--style", "all",
                "--src", str(sample_img),
                "--out", str(out_base),
                "--dry-run",
                "--json",
            ])
        self.assertEqual(code, 0)
        items = json.loads(buf.getvalue())
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 3)
        for it in items:
            self.assertEqual(it["status"], "ok")
            self.assertTrue(it["dry_run"])
            self.assertIn("style", it)
            self.assertIn("output", it)

    def test_cli_main_missing_src_json_error(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = drama_poster_main([
                "--src", str(self.tmp_path / "not_there.png"),
                "--json",
                "--strict",
            ])
        self.assertEqual(code, 1)
        err = json.loads(buf.getvalue())
        self.assertFalse(err["ok"])
        self.assertIn("error", err)

    @patch("render_drama_poster.render_drama_poster_style", side_effect=RuntimeError("Simulated drama render crash"))
    def test_main_cli_exception_stderr_output(self, mock_render):
        import io
        from contextlib import redirect_stderr
        sample_img = self.tmp_path / "drama_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = drama_poster_main([
                "--style", "mega_bleed",
                "--src", str(sample_img),
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 戏剧性海报渲染失败: Simulated drama render crash", buf.getvalue())

    @patch("render_drama_poster.render_drama_poster_style", side_effect=RuntimeError("Simulated quiet crash"))
    def test_main_cli_exception_quiet_mode(self, mock_render):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        sample_img = self.tmp_path / "drama_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            code = drama_poster_main([
                "--style", "mega_bleed",
                "--src", str(sample_img),
                "-q",
            ])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_main_cli_missing_src_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        missing_src = self.tmp_path / "non_existent_drama_src.png"
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = drama_poster_main([
                "--style", "mega_bleed",
                "--src", str(missing_src),
                "--strict",
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 找不到输入底图", buf.getvalue())

    @patch("render_drama_poster.render_drama_poster_style", side_effect=RuntimeError("Simulated JSON crash"))
    def test_cli_main_exception_json_error(self, mock_render):
        import io
        from contextlib import redirect_stdout
        sample_img = self.tmp_path / "drama_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = drama_poster_main([
                "--style", "mega_bleed",
                "--src", str(sample_img),
                "--json",
            ])
        self.assertEqual(code, 1)
        err = json.loads(buf.getvalue())
        self.assertFalse(err["ok"])
        self.assertIn("error", err)
        self.assertIn("Simulated JSON crash", err["error"])

    def test_cli_list_exception_json_output(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("render_drama_poster.list_drama_poster_styles", side_effect=RuntimeError("Drama styles index corrupted")):
            with redirect_stdout(buf):
                code = drama_poster_main(["--list", "--json"])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "Drama styles index corrupted")

    def test_cli_list_exception_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("render_drama_poster.list_drama_poster_styles", side_effect=RuntimeError("Drama styles index corrupted")):
            with redirect_stderr(buf):
                code = drama_poster_main(["--list"])
        self.assertEqual(code, 1)
        self.assertIn("❌ 戏剧性海报渲染失败: Drama styles index corrupted", buf.getvalue())

    def test_cli_list_exception_quiet_mode(self):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with patch("render_drama_poster.list_drama_poster_styles", side_effect=RuntimeError("Drama styles index corrupted")):
            with redirect_stdout(out_buf), redirect_stderr(err_buf):
                code = drama_poster_main(["--list", "-q"])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")



class TestRenderCnTypePoster(unittest.TestCase):
    """测试高级中文字排渲染器 render_cn_type_poster 及其三大纪念碑式构图与输入安全防御"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_b64_with_data_uri(self):
        raw_uri = "data:image/png;base64,mocked_cn_type_data"
        result = cn_b64(raw_uri)
        self.assertEqual(result, raw_uri)

    def test_b64_mime_types(self):
        types = [
            ("sample.png", "image/png"),
            ("sample.jpg", "image/jpeg"),
            ("sample.jpeg", "image/jpeg"),
            ("sample.webp", "image/webp"),
            ("sample.svg", "image/svg+xml"),
            ("sample.gif", "image/gif"),
        ]
        for filename, expected_mime in types:
            file_p = self.tmp_path / filename
            file_p.write_bytes(b"\x00\x01\x02\x03")
            uri = cn_b64(file_p)
            self.assertTrue(uri.startswith(f"data:{expected_mime};base64,"))
            uri_str = cn_b64(str(file_p))
            self.assertTrue(uri_str.startswith(f"data:{expected_mime};base64,"))

    def test_b64_missing_file_raises_filenotfound(self):
        with self.assertRaises(FileNotFoundError):
            cn_b64(self.tmp_path / "non_existent_poster.png")

    def test_sanitize_img_uri(self):
        malicious = "data:image/png;base64,abc\r\ndef'\"<script>"
        sanitized = cn_sanitize_img_uri(malicious)
        self.assertNotIn("\r", sanitized)
        self.assertNotIn("\n", sanitized)
        self.assertNotIn("'", sanitized)
        self.assertNotIn('"', sanitized)
        self.assertNotIn("<", sanitized)
        self.assertNotIn(">", sanitized)
        self.assertIn("%27", sanitized)
        self.assertIn("%22", sanitized)
        self.assertIn("%3C", sanitized)
        self.assertIn("%3E", sanitized)

    def test_build_monument_html_escaping_and_custom_text(self):
        # 1. 默认参数
        html_default = build_monument_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("NIGHT VOYAGE", html_default)
        self.assertIn("一部还没写完的电影", html_default)
        self.assertIn("2026", html_default)
        self.assertIn("Agnes Studio · Monument", html_default)
        self.assertIn("font-size:148px", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_monument_html(
            "data:image/png;base64,abc",
            title="<纪念碑字体>",
            latin="MONUMENT & ARCHITECTURE",
            sub="“空间与文字”",
            year="2027",
            meta="Custom <Meta>",
            extra_css=".custom{opacity:0.9;}",
        )
        self.assertNotIn("<纪念碑字体>", html_custom)
        self.assertIn("&lt;纪念碑字体&gt;", html_custom)
        self.assertIn("MONUMENT &amp; ARCHITECTURE", html_custom)
        self.assertIn("“空间与文字”", html_custom)
        self.assertIn("Custom &lt;Meta&gt;", html_custom)
        self.assertIn(".custom{opacity:0.9;}", html_custom)

        # 3. None 参数防御
        html_none = build_monument_html("data:image/png;base64,abc", title=None, latin=None, sub=None, year=None, meta=None)
        self.assertIn("夜航", html_none)
        self.assertIn("NIGHT VOYAGE", html_none)
        self.assertIn("一部还没写完的电影", html_none)
        self.assertIn("2026", html_none)
        self.assertIn("Agnes Studio · Monument", html_none)

    def test_build_puhui_mega_html_escaping_and_custom_text(self):
        # 1. 默认参数
        html_default = build_puhui_mega_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("NIGHT VOYAGE", html_default)
        self.assertIn("font-size:168px", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_puhui_mega_html(
            "data:image/png;base64,abc",
            title="<巨字建筑>",
            latin="MEGA & BOLD",
            en_bottom="BOTTOM <LABEL>",
            extra_css=".mega{display:block;}",
        )
        self.assertNotIn("<巨字建筑>", html_custom)
        self.assertIn("&lt;巨字建筑&gt;", html_custom)
        self.assertIn("MEGA &amp; BOLD", html_custom)
        self.assertIn("BOTTOM &lt;LABEL&gt;", html_custom)
        self.assertIn(".mega{display:block;}", html_custom)

        # 3. None 参数防御
        html_none = build_puhui_mega_html("data:image/png;base64,abc", title=None, latin=None, en_bottom=None)
        self.assertIn("夜航", html_none)
        self.assertIn("NIGHT VOYAGE", html_none)

    def test_build_vertical_epic_html_escaping_and_custom_text(self):
        # 1. 默认参数
        html_default = build_vertical_epic_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("NIGHT VOYAGE", html_default)
        self.assertIn("她把城市调成静音", html_default)
        self.assertIn("航", html_default)
        self.assertIn("writing-mode:vertical-rl", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_vertical_epic_html(
            "data:image/png;base64,abc",
            title="<东方史诗>",
            latin="EPIC & ORIENT",
            slogan="千山暮雪 · 寂寥无声",
            seal_char="印",
            extra_css=".epic{color:#fff;}",
        )
        self.assertNotIn("<东方史诗>", html_custom)
        self.assertIn("&lt;东方史诗&gt;", html_custom)
        self.assertIn("EPIC &amp; ORIENT", html_custom)
        self.assertIn("千山暮雪 · 寂寥无声", html_custom)
        self.assertIn("印", html_custom)
        self.assertIn(".epic{color:#fff;}", html_custom)

        # 3. None 参数防御
        html_none = build_vertical_epic_html("data:image/png;base64,abc", title=None, latin=None, slogan=None, seal_char=None)
        self.assertIn("夜航", html_none)
        self.assertIn("NIGHT VOYAGE", html_none)
        self.assertIn("她把城市调成静音", html_none)
        self.assertIn("航", html_none)

    def test_render_html_mkdir_and_invocation(self):
        out_target = self.tmp_path / "deep" / "nested" / "cn_type.png"
        fake_page = MagicMock()
        fake_browser = MagicMock()
        fake_browser.new_page.return_value = fake_page
        fake_chromium = MagicMock()
        fake_chromium.launch.return_value = fake_browser
        fake_playwright_ctx = MagicMock()
        fake_playwright_ctx.chromium = fake_chromium
        fake_playwright_cm = MagicMock()
        fake_playwright_cm.__enter__.return_value = fake_playwright_ctx

        def fake_screenshot(path, type="png"):
            Path(path).write_bytes(b"\x89PNGfake_cn_type")

        fake_page.screenshot.side_effect = fake_screenshot

        with patch("playwright.sync_api.sync_playwright", return_value=fake_playwright_cm):
            res_path = cn_render_html("<html><body>CnType</body></html>", out_target, timeout_ms=10)
            self.assertEqual(res_path, out_target)
            self.assertTrue(out_target.exists())
            fake_page.set_content.assert_called_once_with("<html><body>CnType</body></html>")
            fake_page.wait_for_timeout.assert_called_once_with(10)
            fake_browser.close.assert_called_once()

    @patch("render_cn_type_poster.render_html")
    def test_style_monument_mega_vertical_integration(self, mock_render):
        sample_img = self.tmp_path / "base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out.png"
        mock_render.return_value = out_p

        # 1. style_monument
        res_m = style_monument(sample_img, out_p, title="纪念碑测试", latin="MONUMENT TEST", sub="副标测试")
        self.assertEqual(res_m, out_p)
        mock_render.assert_called()
        call_html_m = mock_render.call_args[0][0]
        self.assertIn("纪念碑测试", call_html_m)
        self.assertIn("MONUMENT TEST", call_html_m)
        self.assertIn("副标测试", call_html_m)

        # 2. style_puhui_mega
        res_p = style_puhui_mega(sample_img, out_p, title="巨字测试", latin="MEGA TEST")
        self.assertEqual(res_p, out_p)
        call_html_p = mock_render.call_args[0][0]
        self.assertIn("巨字测试", call_html_p)
        self.assertIn("MEGA TEST", call_html_p)

        # 3. style_vertical_epic
        res_v = style_vertical_epic(sample_img, out_p, title="竖排测试", latin="VERTICAL TEST", slogan="标语测试", seal_char="章")
        self.assertEqual(res_v, out_p)
        call_html_v = mock_render.call_args[0][0]
        self.assertIn("竖排测试", call_html_v)
        self.assertIn("VERTICAL TEST", call_html_v)
        self.assertIn("标语测试", call_html_v)
        self.assertIn("章", call_html_v)

    @patch("render_cn_type_poster.render_html")
    def test_main_execution(self, mock_render):
        mock_render.return_value = self.tmp_path / "mock_cn_type.png"
        ret = render_cn_type_poster.main([])
        self.assertEqual(ret, 0)
        self.assertEqual(mock_render.call_count, 3)

    def test_main_missing_input_returns_nonzero(self):
        ret = render_cn_type_poster.main(["--input", str(self.tmp_path / "does_not_exist.png")])
        self.assertEqual(ret, 1)

    @patch("playwright.sync_api.sync_playwright")
    def test_render_html_quiet_mode(self, mock_playwright):
        from contextlib import redirect_stdout

        fake_page = MagicMock()
        fake_browser = MagicMock()
        fake_browser.new_page.return_value = fake_page
        mock_p_inst = MagicMock()
        mock_p_inst.chromium.launch.return_value = fake_browser
        mock_playwright.return_value.__enter__.return_value = mock_p_inst

        out_p = self.tmp_path / "shot_quiet.png"
        out_p.write_bytes(b"\x89PNG\r\n\x1a\n")

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = cn_render_html("<html></html>", out_p, quiet=True)
        self.assertEqual(ret, out_p)
        self.assertEqual(buf.getvalue().strip(), "")

    @patch("render_cn_type_poster.render_html")
    def test_render_styles_quiet_mode(self, mock_render):
        sample_img = self.tmp_path / "cn_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out.png"
        mock_render.return_value = out_p

        res_m = style_monument(sample_img, out_p, quiet=True)
        self.assertEqual(res_m, out_p)
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

        res_p = style_puhui_mega(sample_img, out_p, quiet=True)
        self.assertEqual(res_p, out_p)
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

        res_v = style_vertical_epic(sample_img, out_p, quiet=True)
        self.assertEqual(res_v, out_p)
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

    @patch("render_cn_type_poster.render_html")
    def test_list_and_render_cn_type_poster_style(self, mock_render):
        styles = list_cn_type_poster_styles()
        self.assertEqual(len(styles), 3)
        keys = {s["key"] for s in styles}
        self.assertEqual(keys, {"monument", "puhui_mega", "vertical_epic"})

        sample_img = self.tmp_path / "cn_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "dispatched.png"
        mock_render.return_value = out_p

        ret = render_cn_type_poster_style(
            "vertical_epic",
            sample_img,
            out_p,
            title="戏曲夜航",
            latin="OPERA NIGHT",
            slogan="千山暮雪",
            seal="印",
            quiet=True,
        )
        self.assertEqual(ret, out_p)
        mock_render.assert_called()
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

        with self.assertRaises(KeyError):
            render_cn_type_poster_style("unknown_style", sample_img, out_p)

    def test_cli_main_list_mode(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cn_type_poster_main(["--list"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Agnes Studio 可用纪念碑字排风格预设:", out)
        self.assertIn("monument", out)
        self.assertIn("puhui_mega", out)
        self.assertIn("vertical_epic", out)

    @patch("render_cn_type_poster.render_html")
    def test_cli_main_single_style_with_custom_src_and_out(self, mock_render):
        sample_img = self.tmp_path / "cn_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "single_out.png"
        mock_render.return_value = out_p

        code = cn_type_poster_main([
            "--style", "puhui_mega",
            "--src", str(sample_img),
            "--out", str(out_p),
            "--title", "巨字测试",
            "--latin", "MEGA TEST",
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_render.call_count, 1)

    @patch("render_cn_type_poster.render_html")
    def test_cli_main_all_mode(self, mock_render):
        sample_img = self.tmp_path / "cn_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"
        mock_render.return_value = self.tmp_path / "out.png"

        code = cn_type_poster_main([
            "--style", "all",
            "--src", str(sample_img),
            "--out", str(out_base),
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_render.call_count, 3)

    def test_cli_main_missing_src_strict_mode(self):
        missing_src = self.tmp_path / "does_not_exist.png"
        code_strict = cn_type_poster_main([
            "--style", "monument",
            "--src", str(missing_src),
            "--strict",
            "--quiet",
        ])
        self.assertEqual(code_strict, 1)

        code_lenient = cn_type_poster_main([
            "--style", "monument",
            "--src", str(missing_src),
            "--quiet",
        ])
        self.assertEqual(code_lenient, 0)

    @patch("render_cn_type_poster.render_html")
    def test_cli_main_quiet_mode_suppresses_stdout(self, mock_render):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "cn_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "quiet_out.png"
        mock_render.return_value = out_p

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cn_type_poster_main([
                "--style", "monument",
                "--src", str(sample_img),
                "--out", str(out_p),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_build_arg_parser(self):
        parser = cn_build_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("style", actions)
        self.assertIn("src", actions)
        self.assertIn("input", actions)
        self.assertIn("out", actions)
        self.assertIn("out_dir", actions)
        self.assertIn("title", actions)
        self.assertIn("latin", actions)
        self.assertIn("sub", actions)
        self.assertIn("slogan", actions)
        self.assertIn("seal", actions)
        self.assertIn("list", actions)
        self.assertIn("json", actions)
        self.assertIn("dry_run", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_cli_main_list_json(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cn_type_poster_main(["--list", "--json"])
        self.assertEqual(code, 0)
        items = json.loads(buf.getvalue())
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 3)
        keys = [x["key"] for x in items]
        self.assertEqual(keys, ["monument", "puhui_mega", "vertical_epic"])
        for item in items:
            self.assertIn("default_file", item)
            self.assertIn("description", item)

    def test_render_html_dry_run_returns_path_without_playwright(self):
        out_target = self.tmp_path / "dry_run_dir" / "poster_dry.png"
        res = cn_render_html("<html><body>Dry</body></html>", out_target, quiet=True, dry_run=True)
        self.assertEqual(res, out_target)
        self.assertTrue(out_target.parent.exists())

    def test_render_cn_type_poster_style_dry_run(self):
        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_target = self.tmp_path / "dry_style.png"
        res = render_cn_type_poster_style("vertical_epic", sample_img, out_target, dry_run=True, quiet=True)
        self.assertEqual(res, out_target)

    def test_cli_main_dry_run_single(self):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "single_dry.png"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cn_type_poster_main([
                "--style", "puhui_mega",
                "--src", str(sample_img),
                "--out", str(out_p),
                "--dry-run",
            ])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("(dry_run)", out)
        self.assertIn("single_dry.png", out)

    def test_cli_main_dry_run_all(self):
        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"

        code = cn_type_poster_main([
            "--style", "all",
            "--src", str(sample_img),
            "--out", str(out_base),
            "--dry-run",
            "--quiet",
        ])
        self.assertEqual(code, 0)

    def test_cli_main_dry_run_json_output(self):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cn_type_poster_main([
                "--style", "all",
                "--src", str(sample_img),
                "--out", str(out_base),
                "--dry-run",
                "--json",
            ])
        self.assertEqual(code, 0)
        items = json.loads(buf.getvalue())
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 3)
        for it in items:
            self.assertEqual(it["status"], "ok")
            self.assertTrue(it["dry_run"])
            self.assertIn("style", it)
            self.assertIn("output", it)

    def test_cli_main_missing_src_json_error(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cn_type_poster_main([
                "--src", str(self.tmp_path / "not_there.png"),
                "--json",
                "--strict",
            ])
        self.assertEqual(code, 1)
        err = json.loads(buf.getvalue())
        self.assertFalse(err["ok"])
        self.assertIn("error", err)

    @patch("render_cn_type_poster.render_cn_type_poster_style", side_effect=RuntimeError("Simulated cn_type render crash"))
    def test_main_cli_exception_stderr_output(self, mock_render):
        import io
        from contextlib import redirect_stderr
        sample_img = self.tmp_path / "cn_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = cn_type_poster_main([
                "--style", "monument",
                "--src", str(sample_img),
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 纪念碑式海报渲染失败: Simulated cn_type render crash", buf.getvalue())

    @patch("render_cn_type_poster.render_cn_type_poster_style", side_effect=RuntimeError("Simulated quiet crash"))
    def test_main_cli_exception_quiet_mode(self, mock_render):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        sample_img = self.tmp_path / "cn_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            code = cn_type_poster_main([
                "--style", "monument",
                "--src", str(sample_img),
                "-q",
            ])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_main_cli_missing_src_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        missing_src = self.tmp_path / "non_existent_cn_src.png"
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = cn_type_poster_main([
                "--style", "monument",
                "--src", str(missing_src),
                "--strict",
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 找不到输入底图", buf.getvalue())

    @patch("render_cn_type_poster.render_cn_type_poster_style", side_effect=RuntimeError("Simulated JSON crash"))
    def test_cli_main_exception_json_error(self, mock_render):
        import io
        from contextlib import redirect_stdout
        sample_img = self.tmp_path / "cn_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cn_type_poster_main([
                "--style", "monument",
                "--src", str(sample_img),
                "--json",
            ])
        self.assertEqual(code, 1)
        err = json.loads(buf.getvalue())
        self.assertFalse(err["ok"])
        self.assertIn("error", err)
        self.assertIn("Simulated JSON crash", err["error"])

    def test_cli_list_exception_json_output(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("render_cn_type_poster.list_cn_type_poster_styles", side_effect=RuntimeError("CN type styles index corrupted")):
            with redirect_stdout(buf):
                code = cn_type_poster_main(["--list", "--json"])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "CN type styles index corrupted")

    def test_cli_list_exception_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("render_cn_type_poster.list_cn_type_poster_styles", side_effect=RuntimeError("CN type styles index corrupted")):
            with redirect_stderr(buf):
                code = cn_type_poster_main(["--list"])
        self.assertEqual(code, 1)
        self.assertIn("❌ 纪念碑式海报渲染失败: CN type styles index corrupted", buf.getvalue())

    def test_cli_list_exception_quiet_mode(self):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with patch("render_cn_type_poster.list_cn_type_poster_styles", side_effect=RuntimeError("CN type styles index corrupted")):
            with redirect_stdout(out_buf), redirect_stderr(err_buf):
                code = cn_type_poster_main(["--list", "-q"])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")



class TestRenderLayoutPoster(unittest.TestCase):
    """测试海报「设计排版」范式库渲染器 render_layout_poster 及其 4 大版式系统与安全防御"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_b64_with_data_uri(self):
        raw_uri = "data:image/png;base64,mocked_layout_data"
        result = layout_b64(raw_uri)
        self.assertEqual(result, raw_uri)

    def test_b64_mime_types(self):
        types = [
            ("sample.png", "image/png"),
            ("sample.jpg", "image/jpeg"),
            ("sample.jpeg", "image/jpeg"),
            ("sample.webp", "image/webp"),
            ("sample.svg", "image/svg+xml"),
            ("sample.gif", "image/gif"),
        ]
        for filename, expected_mime in types:
            file_p = self.tmp_path / filename
            file_p.write_bytes(b"\x00\x01\x02\x03")
            uri = layout_b64(file_p)
            self.assertTrue(uri.startswith(f"data:{expected_mime};base64,"))
            uri_str = layout_b64(str(file_p))
            self.assertTrue(uri_str.startswith(f"data:{expected_mime};base64,"))

    def test_b64_missing_file_raises_filenotfound(self):
        with self.assertRaises(FileNotFoundError):
            layout_b64(self.tmp_path / "non_existent_layout.png")

    def test_sanitize_img_uri(self):
        malicious = "data:image/png;base64,layout\r\ndef'\"<script>"
        sanitized = layout_sanitize_img_uri(malicious)
        self.assertNotIn("\r", sanitized)
        self.assertNotIn("\n", sanitized)
        self.assertNotIn("'", sanitized)
        self.assertNotIn('"', sanitized)
        self.assertNotIn("<", sanitized)
        self.assertNotIn(">", sanitized)
        self.assertIn("%27", sanitized)
        self.assertIn("%22", sanitized)
        self.assertIn("%3C", sanitized)
        self.assertIn("%3E", sanitized)

    def test_build_swiss_asym_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_swiss_asym_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("她把城市调成静音", html_default)
        self.assertIn("Swiss · Asym", html_default)
        self.assertIn("01", html_default)
        self.assertIn(".colL", html_default)
        self.assertIn(".colR", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_swiss_asym_html(
            "data:image/png;base64,abc",
            title="<瑞士非对称>",
            latin="SWISS & ASYM",
            slogan="“网格与秩序”",
            system_tag="Tag <Special>",
            num="99",
            extra_css=".custom_swiss{opacity:0.8;}",
        )
        self.assertNotIn("<瑞士非对称>", html_custom)
        self.assertIn("&lt;瑞士非对称&gt;", html_custom)
        self.assertIn("SWISS &amp; ASYM", html_custom)
        self.assertIn("“网格与秩序”", html_custom)
        self.assertIn("Tag &lt;Special&gt;", html_custom)
        self.assertIn("99", html_custom)
        self.assertIn(".custom_swiss{opacity:0.8;}", html_custom)

        # 3. None 参数防御
        html_none = build_swiss_asym_html(
            "data:image/png;base64,abc",
            title=None,
            latin=None,
            slogan=None,
            system_tag=None,
            num=None,
        )
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)
        self.assertIn("她把城市调成静音", html_none)
        self.assertIn("Swiss · Asym", html_none)
        self.assertIn("01", html_none)

    def test_build_type_band_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_type_band_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("一部还没写完的电影", html_default)
        self.assertIn("Layout 02<br>Band / Field", html_default)
        self.assertIn(".band", html_default)
        self.assertIn(".field", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_type_band_html(
            "data:image/png;base64,abc",
            title="<上字带>",
            latin="TYPE & BAND",
            slogan="视觉与信息的分区<测试>",
            tag="Custom Band<br>Sub & Line",
            extra_css=".band_custom{top:10%;}",
        )
        self.assertNotIn("<上字带>", html_custom)
        self.assertIn("&lt;上字带&gt;", html_custom)
        self.assertIn("TYPE &amp; BAND", html_custom)
        self.assertIn("视觉与信息的分区&lt;测试&gt;", html_custom)
        self.assertIn("Custom Band<br>Sub &amp; Line", html_custom)
        self.assertIn(".band_custom{top:10%;}", html_custom)

        # 3. None 参数防御
        html_none = build_type_band_html(
            "data:image/png;base64,abc",
            title=None,
            latin=None,
            slogan=None,
            tag=None,
        )
        self.assertIn("夜航", html_none)
        self.assertIn("一部还没写完的电影", html_none)

    def test_build_axis_tension_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_axis_tension_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("她把城市调成静音", html_default)
        self.assertIn("MMXXVI", html_default)
        self.assertIn("Agnes Layout · Diagonal", html_default)
        self.assertIn(".veil", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_axis_tension_html(
            "data:image/png;base64,abc",
            title="<对角张力>",
            latin="AXIS & TENSION",
            slogan="城市声浪 · 极速留白",
            year_text="2027",
            tag="Diagonal <V2>",
            extra_css=".diag{color:gold;}",
        )
        self.assertNotIn("<对角张力>", html_custom)
        self.assertIn("&lt;对角张力&gt;", html_custom)
        self.assertIn("AXIS &amp; TENSION", html_custom)
        self.assertIn("2027", html_custom)
        self.assertIn("Diagonal &lt;V2&gt;", html_custom)
        self.assertIn(".diag{color:gold;}", html_custom)

        # 3. None 参数防御
        html_none = build_axis_tension_html(
            "data:image/png;base64,abc",
            title=None,
            latin=None,
            slogan=None,
            year_text=None,
            tag=None,
        )
        self.assertIn("夜航", html_none)
        self.assertIn("MMXXVI", html_none)
        self.assertIn("Agnes Layout · Diagonal", html_none)

    def test_build_window_editorial_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_window_editorial_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("一部还没写完的电影", html_default)
        self.assertIn("No.01", html_default)
        self.assertIn("writing-mode:vertical-rl", html_default)
        self.assertIn(".paper", html_default)
        self.assertIn(".spine", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_window_editorial_html(
            "data:image/png;base64,abc",
            title="<杂志开窗>",
            latin="WINDOW & EDITORIAL",
            slogan="书脊与版心",
            idx_text="Vol.<05>",
            extra_css=".win_custom{padding:10px;}",
        )
        self.assertNotIn("<杂志开窗>", html_custom)
        self.assertIn("&lt;杂志开窗&gt;", html_custom)
        self.assertIn("WINDOW &amp; EDITORIAL", html_custom)
        self.assertIn("书脊与版心", html_custom)
        self.assertIn("Vol.&lt;05&gt;", html_custom)
        self.assertIn(".win_custom{padding:10px;}", html_custom)

        # 3. None 参数防御
        html_none = build_window_editorial_html(
            "data:image/png;base64,abc",
            title=None,
            latin=None,
            slogan=None,
            idx_text=None,
        )
        self.assertIn("夜航", html_none)
        self.assertIn("No.01", html_none)

    def test_render_html_mkdir_and_invocation(self):
        out_target = self.tmp_path / "deep" / "nested" / "layout.png"
        fake_page = MagicMock()
        fake_browser = MagicMock()
        fake_browser.new_page.return_value = fake_page
        fake_chromium = MagicMock()
        fake_chromium.launch.return_value = fake_browser
        fake_playwright_ctx = MagicMock()
        fake_playwright_ctx.chromium = fake_chromium
        fake_playwright_cm = MagicMock()
        fake_playwright_cm.__enter__.return_value = fake_playwright_ctx

        def fake_screenshot(path, type="png"):
            Path(path).write_bytes(b"\x89PNGfake_layout")

        fake_page.screenshot.side_effect = fake_screenshot

        with patch("playwright.sync_api.sync_playwright", return_value=fake_playwright_cm):
            res_path = layout_render_html("<html><body>Layout</body></html>", out_target, timeout_ms=10)
            self.assertEqual(res_path, out_target)
            self.assertTrue(out_target.exists())
            fake_page.set_content.assert_called_once_with("<html><body>Layout</body></html>")
            fake_page.wait_for_timeout.assert_called_once_with(10)
            fake_browser.close.assert_called_once()

    @patch("render_layout_poster.render_html")
    def test_all_layout_functions_integration(self, mock_render):
        sample_img = self.tmp_path / "base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out.png"
        mock_render.return_value = out_p

        # 1. layout_swiss_asym
        res1 = layout_swiss_asym(sample_img, out_p, title="瑞士测试", latin="SWISS TEST")
        self.assertEqual(res1, out_p)
        mock_render.assert_called()
        call_html1 = mock_render.call_args[0][0]
        self.assertIn("瑞士测试", call_html1)
        self.assertIn("SWISS TEST", call_html1)

        # 2. layout_type_band
        res2 = layout_type_band(sample_img, out_p, title="字带测试", latin="BAND TEST")
        self.assertEqual(res2, out_p)
        call_html2 = mock_render.call_args[0][0]
        self.assertIn("字带测试", call_html2)
        self.assertIn("BAND TEST", call_html2)

        # 3. layout_axis_tension
        res3 = layout_axis_tension(sample_img, out_p, title="张力测试", latin="TENSION TEST")
        self.assertEqual(res3, out_p)
        call_html3 = mock_render.call_args[0][0]
        self.assertIn("张力测试", call_html3)
        self.assertIn("TENSION TEST", call_html3)

        # 4. layout_window_editorial
        res4 = layout_window_editorial(sample_img, out_p, title="开窗测试", latin="WINDOW TEST")
        self.assertEqual(res4, out_p)
        call_html4 = mock_render.call_args[0][0]
        self.assertIn("开窗测试", call_html4)
        self.assertIn("WINDOW TEST", call_html4)

    @patch("render_layout_poster.render_html")
    def test_main_execution(self, mock_render):
        mock_render.return_value = self.tmp_path / "mock_layout.png"
        ret = render_layout_poster.main([])
        self.assertEqual(ret, 0)
        self.assertEqual(mock_render.call_count, 4)

    def test_main_missing_input_returns_nonzero(self):
        ret = render_layout_poster.main(["--input", str(self.tmp_path / "does_not_exist.png")])
        self.assertEqual(ret, 1)

    @patch("playwright.sync_api.sync_playwright")
    def test_render_html_quiet_mode(self, mock_playwright):
        from contextlib import redirect_stdout

        fake_page = MagicMock()
        fake_browser = MagicMock()
        fake_browser.new_page.return_value = fake_page
        mock_p_inst = MagicMock()
        mock_p_inst.chromium.launch.return_value = fake_browser
        mock_playwright.return_value.__enter__.return_value = mock_p_inst

        out_p = self.tmp_path / "shot_quiet.png"
        out_p.write_bytes(b"\x89PNG\r\n\x1a\n")

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = layout_render_html("<html></html>", out_p, quiet=True)
        self.assertEqual(ret, out_p)
        self.assertEqual(buf.getvalue().strip(), "")

    @patch("render_layout_poster.render_html")
    def test_render_styles_quiet_mode(self, mock_render):
        sample_img = self.tmp_path / "layout_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out.png"
        mock_render.return_value = out_p

        res1 = layout_swiss_asym(sample_img, out_p, quiet=True)
        self.assertEqual(res1, out_p)
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

        res2 = layout_type_band(sample_img, out_p, quiet=True)
        self.assertEqual(res2, out_p)
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

        res3 = layout_axis_tension(sample_img, out_p, quiet=True)
        self.assertEqual(res3, out_p)
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

        res4 = layout_window_editorial(sample_img, out_p, quiet=True)
        self.assertEqual(res4, out_p)
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

    @patch("render_layout_poster.render_html")
    def test_list_and_render_layout_poster_style(self, mock_render):
        styles = list_layout_poster_styles()
        self.assertEqual(len(styles), 4)
        keys = {s["key"] for s in styles}
        self.assertEqual(keys, {"swiss_asym", "type_band", "axis_tension", "window_editorial"})

        sample_img = self.tmp_path / "layout_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "dispatched.png"
        mock_render.return_value = out_p

        ret = render_layout_poster_style(
            "swiss_asym",
            sample_img,
            out_p,
            title="瑞士夜航",
            latin="SWISS NIGHT",
            slogan="网格律动",
            quiet=True,
        )
        self.assertEqual(ret, out_p)
        mock_render.assert_called()
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

        with self.assertRaises(KeyError):
            render_layout_poster_style("unknown_style", sample_img, out_p)

    def test_cli_main_list_mode(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = layout_poster_main(["--list"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Agnes Studio 可用设计排版风格预设:", out)
        self.assertIn("swiss_asym", out)
        self.assertIn("type_band", out)
        self.assertIn("axis_tension", out)
        self.assertIn("window_editorial", out)

    @patch("render_layout_poster.render_html")
    def test_cli_main_single_style_with_custom_src_and_out(self, mock_render):
        sample_img = self.tmp_path / "layout_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "single_out.png"
        mock_render.return_value = out_p

        code = layout_poster_main([
            "--style", "axis_tension",
            "--src", str(sample_img),
            "--out", str(out_p),
            "--title", "张力测试",
            "--latin", "TENSION TEST",
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_render.call_count, 1)

    @patch("render_layout_poster.render_html")
    def test_cli_main_all_mode(self, mock_render):
        sample_img = self.tmp_path / "layout_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"
        mock_render.return_value = self.tmp_path / "out.png"

        code = layout_poster_main([
            "--style", "all",
            "--src", str(sample_img),
            "--out", str(out_base),
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_render.call_count, 4)

    def test_cli_main_missing_src_strict_mode(self):
        missing_src = self.tmp_path / "does_not_exist.png"
        code_strict = layout_poster_main([
            "--style", "swiss_asym",
            "--src", str(missing_src),
            "--strict",
            "--quiet",
        ])
        self.assertEqual(code_strict, 1)

        code_lenient = layout_poster_main([
            "--style", "swiss_asym",
            "--src", str(missing_src),
            "--quiet",
        ])
        self.assertEqual(code_lenient, 0)

    @patch("render_layout_poster.render_html")
    def test_cli_main_quiet_mode_suppresses_stdout(self, mock_render):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "layout_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "quiet_out.png"
        mock_render.return_value = out_p

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = layout_poster_main([
                "--style", "swiss_asym",
                "--src", str(sample_img),
                "--out", str(out_p),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_build_arg_parser(self):
        parser = layout_build_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("style", actions)
        self.assertIn("src", actions)
        self.assertIn("input", actions)
        self.assertIn("out", actions)
        self.assertIn("out_dir", actions)
        self.assertIn("title", actions)
        self.assertIn("latin", actions)
        self.assertIn("slogan", actions)
        self.assertIn("list", actions)
        self.assertIn("json", actions)
        self.assertIn("dry_run", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_cli_main_list_json(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = layout_poster_main(["--list", "--json"])
        self.assertEqual(code, 0)
        items = json.loads(buf.getvalue())
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 4)
        keys = [x["key"] for x in items]
        self.assertEqual(keys, ["swiss_asym", "type_band", "axis_tension", "window_editorial"])
        for item in items:
            self.assertIn("default_file", item)
            self.assertIn("description", item)

    def test_render_html_dry_run_returns_path_without_playwright(self):
        out_target = self.tmp_path / "dry_run_dir" / "layout_dry.png"
        res = layout_render_html("<html><body>Dry Layout</body></html>", out_target, quiet=True, dry_run=True)
        self.assertEqual(res, out_target)
        self.assertTrue(out_target.parent.exists())

    def test_render_layout_poster_style_dry_run(self):
        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_target = self.tmp_path / "dry_layout_style.png"
        res = render_layout_poster_style("swiss_asym", sample_img, out_target, dry_run=True, quiet=True)
        self.assertEqual(res, out_target)

    def test_cli_main_dry_run_single(self):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "single_dry.png"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = layout_poster_main([
                "--style", "swiss_asym",
                "--src", str(sample_img),
                "--out", str(out_p),
                "--dry-run",
            ])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("(dry_run)", out)
        self.assertIn("single_dry.png", out)

    def test_cli_main_dry_run_all(self):
        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"

        code = layout_poster_main([
            "--style", "all",
            "--src", str(sample_img),
            "--out", str(out_base),
            "--dry-run",
            "--quiet",
        ])
        self.assertEqual(code, 0)

    def test_cli_main_dry_run_json_output(self):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = layout_poster_main([
                "--style", "all",
                "--src", str(sample_img),
                "--out", str(out_base),
                "--dry-run",
                "--json",
            ])
        self.assertEqual(code, 0)
        items = json.loads(buf.getvalue())
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 4)
        for it in items:
            self.assertEqual(it["status"], "ok")
            self.assertTrue(it["dry_run"])
            self.assertIn("style", it)
            self.assertIn("output", it)

    def test_cli_main_missing_src_json_error(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = layout_poster_main([
                "--src", str(self.tmp_path / "not_there.png"),
                "--json",
                "--strict",
            ])
        self.assertEqual(code, 1)
        err = json.loads(buf.getvalue())
        self.assertFalse(err.get("ok", True))
        self.assertIn("error", err)

    @patch("render_layout_poster.render_layout_poster_style", side_effect=RuntimeError("Simulated layout render crash"))
    def test_main_cli_exception_stderr_output(self, mock_render):
        import io
        from contextlib import redirect_stderr
        sample_img = self.tmp_path / "layout_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = layout_poster_main([
                "--style", "swiss_asym",
                "--src", str(sample_img),
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 设计排版海报渲染失败: Simulated layout render crash", buf.getvalue())

    @patch("render_layout_poster.render_layout_poster_style", side_effect=RuntimeError("Simulated layout quiet crash"))
    def test_main_cli_exception_quiet_mode(self, mock_render):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        sample_img = self.tmp_path / "layout_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            code = layout_poster_main([
                "--style", "swiss_asym",
                "--src", str(sample_img),
                "-q",
            ])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_main_cli_missing_src_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        missing_src = self.tmp_path / "non_existent_layout_src.png"
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = layout_poster_main([
                "--style", "swiss_asym",
                "--src", str(missing_src),
                "--strict",
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 找不到输入底图", buf.getvalue())

    @patch("render_layout_poster.render_layout_poster_style", side_effect=RuntimeError("Simulated layout JSON crash"))
    def test_cli_main_exception_json_error(self, mock_render):
        import io
        from contextlib import redirect_stdout
        sample_img = self.tmp_path / "layout_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = layout_poster_main([
                "--style", "swiss_asym",
                "--src", str(sample_img),
                "--json",
            ])
        self.assertEqual(code, 1)
        err = json.loads(buf.getvalue())
        self.assertFalse(err["ok"])
        self.assertIn("error", err)
        self.assertIn("Simulated layout JSON crash", err["error"])


class TestRenderTitleDesign(unittest.TestCase):
    """测试海报标题字设计（Title Lettering Design）渲染器 render_title_design 及其 6 大设计范式"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_b64_with_data_uri(self):
        raw_uri = "data:image/png;base64,mocked_title_data"
        result = title_b64(raw_uri)
        self.assertEqual(result, raw_uri)

    def test_b64_mime_types(self):
        types = [
            ("sample.png", "image/png"),
            ("sample.jpg", "image/jpeg"),
            ("sample.jpeg", "image/jpeg"),
            ("sample.webp", "image/webp"),
            ("sample.svg", "image/svg+xml"),
            ("sample.gif", "image/gif"),
        ]
        for filename, expected_mime in types:
            file_p = self.tmp_path / filename
            file_p.write_bytes(b"\x00\x01\x02\x03")
            uri = title_b64(file_p)
            self.assertTrue(uri.startswith(f"data:{expected_mime};base64,"))
            uri_str = title_b64(str(file_p))
            self.assertTrue(uri_str.startswith(f"data:{expected_mime};base64,"))

    def test_b64_missing_file_raises_filenotfound(self):
        with self.assertRaises(FileNotFoundError):
            title_b64(self.tmp_path / "non_existent_title.png")

    def test_sanitize_img_uri(self):
        malicious = "data:image/png;base64,title\r\ndef'\"<script>"
        sanitized = title_sanitize_img_uri(malicious)
        self.assertNotIn("\r", sanitized)
        self.assertNotIn("\n", sanitized)
        self.assertNotIn("'", sanitized)
        self.assertNotIn('"', sanitized)
        self.assertNotIn("<", sanitized)
        self.assertNotIn(">", sanitized)
        self.assertIn("%27", sanitized)
        self.assertIn("%22", sanitized)
        self.assertIn("%3C", sanitized)
        self.assertIn("%3E", sanitized)

    def test_shell_structure_and_fonts(self):
        html = title_shell("data:image/png;base64,sample", "<div class='title'>夜航</div>", extra_css=".custom{color:red;}")
        self.assertIn("@font-face{font-family:'NSB'", html)
        self.assertIn("@font-face{font-family:'PHH'", html)
        self.assertIn("@font-face{font-family:'PHM'", html)
        self.assertIn("@font-face{font-family:'SM'", html)
        self.assertIn("width:864px;height:1152px", html)
        self.assertIn("<div class='title'>夜航</div>", html)
        self.assertIn(".custom{color:red;}", html)
        self.assertIn('src="data:image/png;base64,sample"', html)

    def test_build_t1_cut_slash_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_t1_cut_slash_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("她把城市调成静音", html_default)
        self.assertIn("#C8102E", html_default)
        self.assertIn('class="slash"', html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_t1_cut_slash_html(
            "data:image/png;base64,abc",
            title="<切割字>",
            latin="CUT & SLASH",
            slogan="倾斜割裂 · 破格<标>",
            slash_color="#FF3300",
            extra_css=".custom_cut{opacity:0.9;}",
        )
        self.assertNotIn("<切割字>", html_custom)
        self.assertIn("&lt;切割字&gt;", html_custom)
        self.assertIn("CUT &amp; SLASH", html_custom)
        self.assertIn("倾斜割裂 · 破格&lt;标&gt;", html_custom)
        self.assertIn("#FF3300", html_custom)
        self.assertIn(".custom_cut{opacity:0.9;}", html_custom)

        # 3. None 参数防御
        html_none = build_t1_cut_slash_html(
            "data:image/png;base64,abc",
            title=None,
            latin=None,
            slogan=None,
            slash_color=None,
        )
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)
        self.assertIn("她把城市调成静音", html_none)

    def test_build_t2_double_offset_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_t2_double_offset_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage · 2026", html_default)
        self.assertIn("-webkit-text-stroke:1.5px", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_t2_double_offset_html(
            "data:image/png;base64,abc",
            title="<双层错位>",
            latin="DOUBLE & OFFSET",
            stroke_color="rgba(255,255,255,.8)",
            text_color="#00FFFF",
            extra_css=".custom_offset{top:20px;}",
        )
        self.assertNotIn("<双层错位>", html_custom)
        self.assertIn("&lt;双层错位&gt;", html_custom)
        self.assertIn("DOUBLE &amp; OFFSET", html_custom)
        self.assertIn("#00FFFF", html_custom)
        self.assertIn(".custom_offset{top:20px;}", html_custom)

        # 3. None 参数防御
        html_none = build_t2_double_offset_html(
            "data:image/png;base64,abc",
            title=None,
            latin=None,
            stroke_color=None,
            text_color=None,
        )
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage · 2026", html_none)

    def test_build_t3_color_split_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_t3_color_split_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("A Film Still", html_default)
        self.assertIn("clip-path:polygon", html_default)
        self.assertIn("#C8102E", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_t3_color_split_html(
            "data:image/png;base64,abc",
            title="<色块切割>",
            latin="COLOR & SPLIT",
            slogan="双色断层",
            split_color="#00E5FF",
            extra_css=".split_custom{margin:5px;}",
        )
        self.assertNotIn("<色块切割>", html_custom)
        self.assertIn("&lt;色块切割&gt;", html_custom)
        self.assertIn("COLOR &amp; SPLIT", html_custom)
        self.assertIn("#00E5FF", html_custom)
        self.assertIn(".split_custom{margin:5px;}", html_custom)

        # 3. None 参数防御
        html_none = build_t3_color_split_html(
            "data:image/png;base64,abc",
            title=None,
            latin=None,
            slogan=None,
            split_color=None,
        )
        self.assertIn("夜航", html_none)
        self.assertIn("A Film Still", html_none)

    def test_build_t4_image_in_type_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_t4_image_in_type_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("-webkit-background-clip:text", html_default)
        self.assertIn("background-image:url('data:image/png;base64,abc')", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_t4_image_in_type_html(
            "data:image/png;base64,abc",
            title="<图窗字>",
            latin="IMAGE & TYPE",
            slogan="画面融入<字>",
            bar_color="#E0A96D",
            extra_css=".win_css{border:none;}",
        )
        self.assertNotIn("<图窗字>", html_custom)
        self.assertIn("&lt;图窗字&gt;", html_custom)
        self.assertIn("IMAGE &amp; TYPE", html_custom)
        self.assertIn("#E0A96D", html_custom)
        self.assertIn(".win_css{border:none;}", html_custom)

        # 3. None 参数防御
        html_none = build_t4_image_in_type_html(
            "data:image/png;base64,abc",
            title=None,
            latin=None,
            slogan=None,
            bar_color=None,
        )
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)

    def test_build_t5_geo_lock_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_t5_geo_lock_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("border-left:2px solid #D4B896", html_default)
        self.assertIn("border-right:2px solid #D4B896", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_t5_geo_lock_html(
            "data:image/png;base64,abc",
            title="<几何锁字>",
            latin="GEO & LOCK",
            slogan="徽章与结构",
            frame_color="#FFB800",
            extra_css=".geo_css{padding:12px;}",
        )
        self.assertNotIn("<几何锁字>", html_custom)
        self.assertIn("&lt;几何锁字&gt;", html_custom)
        self.assertIn("GEO &amp; LOCK", html_custom)
        self.assertIn("#FFB800", html_custom)
        self.assertIn(".geo_css{padding:12px;}", html_custom)

        # 3. None 参数防御
        html_none = build_t5_geo_lock_html(
            "data:image/png;base64,abc",
            title=None,
            latin=None,
            slogan=None,
            frame_color=None,
        )
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)

    def test_build_t6_outline_stretch_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_t6_outline_stretch_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("2026 / NIGHT", html_default)
        self.assertIn("transform:scaleX(0.92)", html_default)
        self.assertIn("-webkit-text-stroke:2.5px #F4F0E8", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_t6_outline_stretch_html(
            "data:image/png;base64,abc",
            title="<挤压描边>",
            latin="OUTLINE & STRETCH",
            slogan="工业先锋力场",
            stroke_color="#00FFAA",
            extra_css=".outline_css{margin:2px;}",
        )
        self.assertNotIn("<挤压描边>", html_custom)
        self.assertIn("&lt;挤压描边&gt;", html_custom)
        self.assertIn("OUTLINE &amp; STRETCH", html_custom)
        self.assertIn("#00FFAA", html_custom)
        self.assertIn(".outline_css{margin:2px;}", html_custom)

        # 3. None 参数防御
        html_none = build_t6_outline_stretch_html(
            "data:image/png;base64,abc",
            title=None,
            latin=None,
            slogan=None,
            stroke_color=None,
        )
        self.assertIn("夜航", html_none)
        self.assertIn("2026 / NIGHT", html_none)

    def test_render_html_mkdir_and_invocation(self):
        out_target = self.tmp_path / "deep" / "nested" / "title_render.png"
        fake_page = MagicMock()
        fake_browser = MagicMock()
        fake_browser.new_page.return_value = fake_page
        fake_chromium = MagicMock()
        fake_chromium.launch.return_value = fake_browser
        fake_playwright_ctx = MagicMock()
        fake_playwright_ctx.chromium = fake_chromium
        fake_playwright_cm = MagicMock()
        fake_playwright_cm.__enter__.return_value = fake_playwright_ctx

        def fake_screenshot(path, type="png"):
            Path(path).write_bytes(b"\x89PNGfake_title_lettering")

        fake_page.screenshot.side_effect = fake_screenshot

        with patch("playwright.sync_api.sync_playwright", return_value=fake_playwright_cm):
            res_path = title_render_html("<html><body>Title Lettering</body></html>", out_target, timeout_ms=10)
            self.assertEqual(res_path, out_target)
            self.assertTrue(out_target.exists())
            fake_page.set_content.assert_called_once_with("<html><body>Title Lettering</body></html>")
            fake_page.wait_for_timeout.assert_called_once_with(10)
            fake_browser.close.assert_called_once()

    def test_title_design_registry(self):
        self.assertEqual(len(TITLE_DESIGN_REGISTRY), 6)
        expected_keys = {
            "t1_cut_slash",
            "t2_double_offset",
            "t3_color_split",
            "t4_image_in_type",
            "t5_geo_lock",
            "t6_outline_stretch",
        }
        self.assertEqual(set(TITLE_DESIGN_REGISTRY.keys()), expected_keys)

    @patch("render_title_design.render_html")
    def test_all_title_designs_integration(self, mock_render):
        sample_img = self.tmp_path / "base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out.png"
        mock_render.return_value = out_p

        # 1. render_t1_cut_slash
        res1 = render_t1_cut_slash(sample_img, out_p, title="切割测试", latin="CUT TEST")
        self.assertEqual(res1, out_p)
        call_html1 = mock_render.call_args[0][0]
        self.assertIn("切割测试", call_html1)
        self.assertIn("CUT TEST", call_html1)

        # 2. render_t2_double_offset
        res2 = render_t2_double_offset(sample_img, out_p, title="错位测试", latin="OFFSET TEST")
        self.assertEqual(res2, out_p)
        call_html2 = mock_render.call_args[0][0]
        self.assertIn("错位测试", call_html2)
        self.assertIn("OFFSET TEST", call_html2)

        # 3. render_t3_color_split
        res3 = render_t3_color_split(sample_img, out_p, title="色块测试", latin="SPLIT TEST")
        self.assertEqual(res3, out_p)
        call_html3 = mock_render.call_args[0][0]
        self.assertIn("色块测试", call_html3)
        self.assertIn("SPLIT TEST", call_html3)

        # 4. render_t4_image_in_type
        res4 = render_t4_image_in_type(sample_img, out_p, title="图窗测试", latin="WINDOW TEST")
        self.assertEqual(res4, out_p)
        call_html4 = mock_render.call_args[0][0]
        self.assertIn("图窗测试", call_html4)
        self.assertIn("WINDOW TEST", call_html4)

        # 5. render_t5_geo_lock
        res5 = render_t5_geo_lock(sample_img, out_p, title="锁字测试", latin="LOCK TEST")
        self.assertEqual(res5, out_p)
        call_html5 = mock_render.call_args[0][0]
        self.assertIn("锁字测试", call_html5)
        self.assertIn("LOCK TEST", call_html5)

        # 6. render_t6_outline_stretch
        res6 = render_t6_outline_stretch(sample_img, out_p, title="挤压测试", latin="STRETCH TEST")
        self.assertEqual(res6, out_p)
        call_html6 = mock_render.call_args[0][0]
        self.assertIn("挤压测试", call_html6)
        self.assertIn("STRETCH TEST", call_html6)

    @patch("render_title_design.render_html")
    def test_render_all_title_designs(self, mock_render):
        sample_img = self.tmp_path / "base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_d = self.tmp_path / "title_batch"
        mock_render.side_effect = lambda html, out, **kw: Path(out)

        results = render_all_title_designs(sample_img, out_dir=out_d, title="全量测试")
        self.assertEqual(len(results), 6)
        self.assertEqual(mock_render.call_count, 6)
        for key in ("t1_cut_slash", "t2_double_offset", "t3_color_split", "t4_image_in_type", "t5_geo_lock", "t6_outline_stretch"):
            self.assertIn(key, results)
            self.assertEqual(results[key].parent, out_d)

    @patch("render_title_design.render_html")
    def test_main_execution(self, mock_render):
        mock_render.side_effect = lambda html, out, **kw: Path(out)
        ret = render_title_design.main([])
        self.assertEqual(ret, 0)
        self.assertEqual(mock_render.call_count, 6)

    def test_main_missing_input_returns_nonzero(self):
        ret = render_title_design.main(["--input", str(self.tmp_path / "does_not_exist.png")])
        self.assertEqual(ret, 1)

    @patch("playwright.sync_api.sync_playwright")
    def test_render_html_quiet_mode(self, mock_playwright):
        from contextlib import redirect_stdout

        fake_page = MagicMock()
        fake_browser = MagicMock()
        fake_browser.new_page.return_value = fake_page
        mock_p_inst = MagicMock()
        mock_p_inst.chromium.launch.return_value = fake_browser
        mock_playwright.return_value.__enter__.return_value = mock_p_inst

        out_p = self.tmp_path / "shot_quiet.png"
        out_p.write_bytes(b"\x89PNG\r\n\x1a\n")

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = title_render_html("<html></html>", out_p, quiet=True)
        self.assertEqual(ret, out_p)
        self.assertEqual(buf.getvalue().strip(), "")

    @patch("render_title_design.render_html")
    def test_render_styles_quiet_mode(self, mock_render):
        sample_img = self.tmp_path / "title_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out.png"
        mock_render.return_value = out_p

        res1 = render_t1_cut_slash(sample_img, out_p, quiet=True)
        self.assertEqual(res1, out_p)
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

        res2 = render_t2_double_offset(sample_img, out_p, quiet=True)
        self.assertEqual(res2, out_p)
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

        res3 = render_t3_color_split(sample_img, out_p, quiet=True)
        self.assertEqual(res3, out_p)
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

        res4 = render_t4_image_in_type(sample_img, out_p, quiet=True)
        self.assertEqual(res4, out_p)
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

        res5 = render_t5_geo_lock(sample_img, out_p, quiet=True)
        self.assertEqual(res5, out_p)
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

        res6 = render_t6_outline_stretch(sample_img, out_p, quiet=True)
        self.assertEqual(res6, out_p)
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

    @patch("render_title_design.render_html")
    def test_list_and_render_title_design_style(self, mock_render):
        styles = list_title_design_styles()
        self.assertEqual(len(styles), 6)
        keys = {s["key"] for s in styles}
        self.assertEqual(
            keys,
            {"t1_cut_slash", "t2_double_offset", "t3_color_split", "t4_image_in_type", "t5_geo_lock", "t6_outline_stretch"},
        )

        sample_img = self.tmp_path / "title_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "dispatched.png"
        mock_render.return_value = out_p

        ret = render_title_design_style(
            "t1_cut_slash",
            sample_img,
            out_p,
            title="刀锋夜航",
            latin="BLADE NIGHT",
            slogan="刀锋切割",
            quiet=True,
        )
        self.assertEqual(ret, out_p)
        mock_render.assert_called()
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

        with self.assertRaises(KeyError):
            render_title_design_style("unknown_style", sample_img, out_p)

    def test_cli_main_list_mode(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = title_design_main(["--list"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Agnes Studio 可用标题字设范式预设:", out)
        self.assertIn("t1_cut_slash", out)
        self.assertIn("t2_double_offset", out)
        self.assertIn("t3_color_split", out)
        self.assertIn("t4_image_in_type", out)
        self.assertIn("t5_geo_lock", out)
        self.assertIn("t6_outline_stretch", out)

    @patch("render_title_design.render_html")
    def test_cli_main_single_style_with_custom_src_and_out(self, mock_render):
        sample_img = self.tmp_path / "title_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "single_out.png"
        mock_render.return_value = out_p

        code = title_design_main([
            "--style", "t1_cut_slash",
            "--src", str(sample_img),
            "--out", str(out_p),
            "--title", "刀锋测试",
            "--latin", "BLADE TEST",
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_render.call_count, 1)

    @patch("render_title_design.render_html")
    def test_cli_main_all_mode(self, mock_render):
        sample_img = self.tmp_path / "title_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"
        mock_render.return_value = self.tmp_path / "out.png"

        code = title_design_main([
            "--style", "all",
            "--src", str(sample_img),
            "--out", str(out_base),
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_render.call_count, 6)

    def test_cli_main_missing_src_strict_mode(self):
        missing_src = self.tmp_path / "does_not_exist.png"
        code_strict = title_design_main([
            "--style", "t1_cut_slash",
            "--src", str(missing_src),
            "--strict",
            "--quiet",
        ])
        self.assertEqual(code_strict, 1)

        code_lenient = title_design_main([
            "--style", "t1_cut_slash",
            "--src", str(missing_src),
            "--quiet",
        ])
        self.assertEqual(code_lenient, 0)

    @patch("render_title_design.render_html")
    def test_cli_main_quiet_mode_suppresses_stdout(self, mock_render):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "title_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "quiet_out.png"
        mock_render.return_value = out_p

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = title_design_main([
                "--style", "t1_cut_slash",
                "--src", str(sample_img),
                "--out", str(out_p),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_build_arg_parser(self):
        parser = title_build_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("style", actions)
        self.assertIn("src", actions)
        self.assertIn("input", actions)
        self.assertIn("out", actions)
        self.assertIn("out_dir", actions)
        self.assertIn("title", actions)
        self.assertIn("latin", actions)
        self.assertIn("slogan", actions)
        self.assertIn("color", actions)
        self.assertIn("list", actions)
        self.assertIn("json", actions)
        self.assertIn("dry_run", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_cli_main_list_json(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = title_design_main(["--list", "--json"])
        self.assertEqual(code, 0)
        items = json.loads(buf.getvalue())
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 6)
        keys = [x["key"] for x in items]
        self.assertEqual(
            keys,
            ["t1_cut_slash", "t2_double_offset", "t3_color_split", "t4_image_in_type", "t5_geo_lock", "t6_outline_stretch"],
        )
        for item in items:
            self.assertIn("default_file", item)
            self.assertIn("description", item)

    def test_render_html_dry_run_returns_path_without_playwright(self):
        out_target = self.tmp_path / "dry_run_dir" / "title_dry.png"
        res = title_render_html("<html><body>Dry Title</body></html>", out_target, quiet=True, dry_run=True)
        self.assertEqual(res, out_target)
        self.assertTrue(out_target.parent.exists())

    def test_render_title_design_style_dry_run(self):
        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_target = self.tmp_path / "dry_title_style.png"
        res = render_title_design_style("t1_cut_slash", sample_img, out_target, dry_run=True, quiet=True)
        self.assertEqual(res, out_target)

    def test_cli_main_dry_run_single(self):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "single_dry.png"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = title_design_main([
                "--style", "t1_cut_slash",
                "--src", str(sample_img),
                "--out", str(out_p),
                "--dry-run",
            ])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("(dry_run)", out)
        self.assertIn("single_dry.png", out)

    def test_cli_main_dry_run_all(self):
        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"

        code = title_design_main([
            "--style", "all",
            "--src", str(sample_img),
            "--out", str(out_base),
            "--dry-run",
            "--quiet",
        ])
        self.assertEqual(code, 0)

    def test_cli_main_dry_run_json_output(self):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = title_design_main([
                "--style", "all",
                "--src", str(sample_img),
                "--out", str(out_base),
                "--dry-run",
                "--json",
            ])
        self.assertEqual(code, 0)
        items = json.loads(buf.getvalue())
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 6)
        for it in items:
            self.assertEqual(it["status"], "ok")
            self.assertTrue(it["dry_run"])
            self.assertIn("style", it)
            self.assertIn("output", it)

    def test_cli_main_missing_src_json_error(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = title_design_main([
                "--src", str(self.tmp_path / "not_there.png"),
                "--json",
                "--strict",
            ])
        self.assertEqual(code, 1)
        err = json.loads(buf.getvalue())
        self.assertFalse(err.get("ok", True))
        self.assertIn("error", err)

    @patch("render_title_design.render_title_design_style", side_effect=RuntimeError("Simulated title design render crash"))
    def test_main_cli_exception_stderr_output(self, mock_render):
        import io
        from contextlib import redirect_stderr
        sample_img = self.tmp_path / "title_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = title_design_main([
                "--style", "t1_cut_slash",
                "--src", str(sample_img),
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 标题字设计海报渲染失败: Simulated title design render crash", buf.getvalue())

    @patch("render_title_design.render_title_design_style", side_effect=RuntimeError("Simulated title design quiet crash"))
    def test_main_cli_exception_quiet_mode(self, mock_render):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        sample_img = self.tmp_path / "title_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            code = title_design_main([
                "--style", "t1_cut_slash",
                "--src", str(sample_img),
                "-q",
            ])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_main_cli_missing_src_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        missing_src = self.tmp_path / "non_existent_title_src.png"
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = title_design_main([
                "--style", "t1_cut_slash",
                "--src", str(missing_src),
                "--strict",
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 找不到输入底图", buf.getvalue())

    @patch("render_title_design.render_title_design_style", side_effect=RuntimeError("Simulated title design JSON crash"))
    def test_cli_main_exception_json_error(self, mock_render):
        import io
        from contextlib import redirect_stdout
        sample_img = self.tmp_path / "title_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = title_design_main([
                "--style", "t1_cut_slash",
                "--src", str(sample_img),
                "--json",
            ])
        self.assertEqual(code, 1)
        err = json.loads(buf.getvalue())
        self.assertFalse(err["ok"])
        self.assertIn("error", err)
        self.assertIn("Simulated title design JSON crash", err["error"])


class TestRenderTitleRefined(unittest.TestCase):
    """测试高级中文海报标题字设（Refined Title Typography）渲染器 render_title_refined 及其 5 大设计范式"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_b64_with_data_uri(self):
        raw_uri = "data:image/png;base64,mocked_refined_data"
        result = refined_b64(raw_uri)
        self.assertEqual(result, raw_uri)

    def test_b64_mime_types(self):
        types = [
            ("sample.png", "image/png"),
            ("sample.jpg", "image/jpeg"),
            ("sample.jpeg", "image/jpeg"),
            ("sample.webp", "image/webp"),
            ("sample.svg", "image/svg+xml"),
            ("sample.gif", "image/gif"),
        ]
        for filename, expected_mime in types:
            file_p = self.tmp_path / filename
            file_p.write_bytes(b"\x00\x01\x02\x03")
            uri = refined_b64(file_p)
            self.assertTrue(uri.startswith(f"data:{expected_mime};base64,"))
            uri_str = refined_b64(str(file_p))
            self.assertTrue(uri_str.startswith(f"data:{expected_mime};base64,"))

    def test_b64_missing_file_raises_filenotfound(self):
        with self.assertRaises(FileNotFoundError):
            refined_b64(self.tmp_path / "non_existent_refined.png")

    def test_sanitize_img_uri(self):
        malicious = "data:image/png;base64,refined\r\ndef'\"<script>"
        sanitized = refined_sanitize_img_uri(malicious)
        self.assertNotIn("\r", sanitized)
        self.assertNotIn("\n", sanitized)
        self.assertNotIn("'", sanitized)
        self.assertNotIn('"', sanitized)
        self.assertNotIn("<", sanitized)
        self.assertNotIn(">", sanitized)
        self.assertIn("%27", sanitized)

    def test_get_base_css(self):
        css = refined_get_base_css()
        self.assertIn("NSB", css)
        self.assertIn("NSBO", css)
        self.assertIn("PHM", css)
        self.assertIn("PHH", css)
        self.assertIn("Didot", css)

    def test_build_r1_oriental_center_html(self):
        html = build_r1_oriental_center_html(
            "data:image/png;base64,sample",
            title="夜航<测试>",
            latin="Night Voyage & Agnes",
            slogan="她把城市调成静音 <Slogan>",
            seal_text="航",
        )
        self.assertIn("夜航&lt;测试&gt;", html)
        self.assertNotIn("<测试>", html)
        self.assertIn("Night Voyage &amp; Agnes", html)
        self.assertIn("radial-gradient", html)
        self.assertIn('class="seal"', html)
        self.assertIn("航", html)

    def test_build_r2_left_big_html(self):
        html = build_r2_left_big_html(
            "data:image/png;base64,sample",
            title="黑宋<大标>",
            latin="Left Big & Minimal",
            slogan="城市夜景",
        )
        self.assertIn("黑宋&lt;大标&gt;", html)
        self.assertIn("Left Big &amp; Minimal", html)
        self.assertIn('class="wrap"', html)

    def test_build_r3_vertical_spine_html(self):
        html = build_r3_vertical_spine_html(
            "data:image/png;base64,sample",
            title="书脊<竖排>",
            latin="Spine & Agnes",
            slogan="画册扉页",
        )
        self.assertIn("书脊&lt;竖排&gt;", html)
        self.assertIn("writing-mode:vertical-rl", html)
        self.assertIn("Spine &amp; Agnes", html)

    def test_build_r4_sky_field_html(self):
        html = build_r4_sky_field_html(
            "data:image/png;base64,sample",
            title="天 幕",
            latin="Sky Field",
            slogan="黄金分割留白",
        )
        self.assertIn("天 幕", html)
        self.assertIn("Sky Field", html)
        self.assertIn("top:18%", html)

    def test_build_r5_film_bottom_html(self):
        html = build_r5_film_bottom_html(
            "data:image/png;base64,sample",
            title="院线大片",
            latin="Film Release",
            slogan="全国上映",
        )
        self.assertIn("院线大片", html)
        self.assertIn("Film Release", html)
        self.assertIn('class="top"', html)
        self.assertIn('class="bot"', html)

    def test_registry_and_render_refined_variant(self):
        self.assertEqual(len(REFINED_TITLE_REGISTRY), 5)
        for key in ("r1_oriental_center", "r2_left_big", "r3_vertical_spine", "r4_sky_field", "r5_film_bottom"):
            self.assertIn(key, REFINED_TITLE_REGISTRY)

        sample_img = self.tmp_path / "base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out.png"

        with self.assertRaises(ValueError):
            render_refined_variant("unknown_variant", sample_img, out_p)

    @patch("render_title_refined.render_html")
    def test_render_individual_variants(self, mock_render):
        sample_img = self.tmp_path / "base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out.png"
        mock_render.side_effect = lambda html, out, **kw: Path(out)

        # 1. render_r1_oriental_center
        res1 = render_r1_oriental_center(sample_img, out_p, title="东方海报", latin="ORIENTAL TEST", seal_text="印")
        self.assertEqual(res1, out_p)
        call_html1 = mock_render.call_args[0][0]
        self.assertIn("东方海报", call_html1)
        self.assertIn("ORIENTAL TEST", call_html1)
        self.assertIn("印", call_html1)

        # 2. render_r2_left_big
        res2 = render_r2_left_big(sample_img, out_p, title="左大标", latin="LEFT BIG TEST")
        self.assertEqual(res2, out_p)
        call_html2 = mock_render.call_args[0][0]
        self.assertIn("左大标", call_html2)
        self.assertIn("LEFT BIG TEST", call_html2)

        # 3. render_r3_vertical_spine
        res3 = render_r3_vertical_spine(sample_img, out_p, title="竖排书脊", latin="SPINE TEST")
        self.assertEqual(res3, out_p)
        call_html3 = mock_render.call_args[0][0]
        self.assertIn("竖排书脊", call_html3)
        self.assertIn("SPINE TEST", call_html3)

        # 4. render_r4_sky_field
        res4 = render_r4_sky_field(sample_img, out_p, title="天幕字", latin="SKY TEST")
        self.assertEqual(res4, out_p)
        call_html4 = mock_render.call_args[0][0]
        self.assertIn("天幕字", call_html4)
        self.assertIn("SKY TEST", call_html4)

        # 5. render_r5_film_bottom
        res5 = render_r5_film_bottom(sample_img, out_p, title="院线结构", latin="FILM BOTTOM TEST")
        self.assertEqual(res5, out_p)
        call_html5 = mock_render.call_args[0][0]
        self.assertIn("院线结构", call_html5)
        self.assertIn("FILM BOTTOM TEST", call_html5)

        # 6. shot alias test
        res_shot = refined_shot("<html>test</html>", out_p)
        self.assertEqual(res_shot, out_p)

        # 7. render_refined_variant helper
        res_var = render_refined_variant("r1_oriental_center", sample_img, out_p, title="通用变体")
        self.assertEqual(res_var, out_p)

    @patch("render_title_refined.render_html")
    def test_render_all_refined_titles(self, mock_render):
        sample_img = self.tmp_path / "base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_d = self.tmp_path / "refined_batch"
        mock_render.side_effect = lambda html, out, **kw: Path(out)

        results = render_all_refined_titles(sample_img, out_dir=out_d, title="全量测试")
        self.assertEqual(len(results), 5)
        self.assertEqual(mock_render.call_count, 5)
        for key in ("r1_oriental_center", "r2_left_big", "r3_vertical_spine", "r4_sky_field", "r5_film_bottom"):
            self.assertIn(key, results)
            self.assertEqual(results[key].parent, out_d)

    @patch("render_title_refined.render_html")
    def test_main_execution(self, mock_render):
        mock_render.side_effect = lambda html, out, **kw: Path(out)
        ret = render_title_refined.main([])
        self.assertEqual(ret, 0)
        self.assertEqual(mock_render.call_count, 5)

        # Test single variant via CLI
        mock_render.reset_mock()
        ret_single = render_title_refined.main(["--variant", "r1_oriental_center"])
        self.assertEqual(ret_single, 0)
        self.assertEqual(mock_render.call_count, 1)

    def test_main_missing_input_returns_nonzero(self):
        ret = render_title_refined.main(["--input", str(self.tmp_path / "does_not_exist.png")])
        self.assertEqual(ret, 1)

    def test_render_html_quiet_mode(self):
        from contextlib import redirect_stdout
        out_p = self.tmp_path / "dummy_render.png"
        out_p.write_bytes(b"\x89PNG\r\n\x1a\n")

        with patch("playwright.sync_api.sync_playwright") as mock_pw:
            mock_browser = MagicMock()
            mock_page = MagicMock()
            mock_pw.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
            mock_browser.new_page.return_value = mock_page

            # quiet=True 应完全抑制标准输出
            buf_quiet = io.StringIO()
            with redirect_stdout(buf_quiet):
                refined_render_html("<html>test</html>", out_p, quiet=True)
            self.assertEqual(buf_quiet.getvalue().strip(), "")

            # quiet=False 应打印生成日志
            buf_loud = io.StringIO()
            with redirect_stdout(buf_loud):
                refined_render_html("<html>test</html>", out_p, quiet=False)
            self.assertIn("✓", buf_loud.getvalue())

    @patch("render_title_refined.render_html")
    def test_render_styles_quiet_mode(self, mock_render):
        sample_img = self.tmp_path / "base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out.png"
        mock_render.side_effect = lambda html, out, **kw: Path(out)

        # 验证 5 大高级字设函数透传 quiet 标志位
        funcs = [
            render_r1_oriental_center,
            render_r2_left_big,
            render_r3_vertical_spine,
            render_r4_sky_field,
            render_r5_film_bottom,
        ]
        for fn in funcs:
            mock_render.reset_mock()
            fn(sample_img, out_p, quiet=True)
            self.assertTrue(mock_render.call_args[1].get("quiet", False))

    def test_normalize_refined_style_key_and_list_styles(self):
        # 1. 验证别名解析与数字映射
        self.assertEqual(normalize_refined_style_key("1"), "r1_oriental_center")
        self.assertEqual(normalize_refined_style_key("r1"), "r1_oriental_center")
        self.assertEqual(normalize_refined_style_key("oriental"), "r1_oriental_center")
        self.assertEqual(normalize_refined_style_key("2"), "r2_left_big")
        self.assertEqual(normalize_refined_style_key("left_big"), "r2_left_big")
        self.assertEqual(normalize_refined_style_key("3"), "r3_vertical_spine")
        self.assertEqual(normalize_refined_style_key("spine"), "r3_vertical_spine")
        self.assertEqual(normalize_refined_style_key("4"), "r4_sky_field")
        self.assertEqual(normalize_refined_style_key("sky"), "r4_sky_field")
        self.assertEqual(normalize_refined_style_key("5"), "r5_film_bottom")
        self.assertEqual(normalize_refined_style_key("film_bottom"), "r5_film_bottom")

        # 2. 未知变体抛出 KeyError
        with self.assertRaises(KeyError):
            normalize_refined_style_key("invalid_style")

        # 3. 验证清单查询接口
        styles = list_refined_title_styles()
        self.assertEqual(len(styles), 5)
        keys = [s["key"] for s in styles]
        self.assertIn("r1_oriental_center", keys)
        self.assertIn("r2_left_big", keys)
        self.assertIn("r3_vertical_spine", keys)
        self.assertIn("r4_sky_field", keys)
        self.assertIn("r5_film_bottom", keys)

    @patch("render_title_refined.render_html")
    def test_render_refined_title_style_dispatch(self, mock_render):
        sample_img = self.tmp_path / "base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out.png"
        mock_render.side_effect = lambda html, out, **kw: Path(out)

        # 1. 派发成功
        res = render_refined_title_style("1", sample_img, out_p, quiet=True)
        self.assertEqual(res, out_p)
        self.assertTrue(mock_render.call_args[1].get("quiet", False))

        # 2. r4_sky_field 标题分词逻辑验证
        mock_render.reset_mock()
        render_refined_title_style("sky", sample_img, out_p, title="夜航", quiet=True)
        call_html = mock_render.call_args[0][0]
        self.assertIn("夜 航", call_html)

        # 3. 未知风格抛出 KeyError
        with self.assertRaises(KeyError):
            render_refined_title_style("unknown", sample_img, out_p)

    def test_cli_main_list_mode(self):
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = refined_title_main(["--list"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("r1_oriental_center", out)
        self.assertIn("r2_left_big", out)
        self.assertIn("r3_vertical_spine", out)
        self.assertIn("r4_sky_field", out)
        self.assertIn("r5_film_bottom", out)

    @patch("render_title_refined.render_html")
    def test_cli_main_single_style_with_custom_src_and_out(self, mock_render):
        sample_img = self.tmp_path / "title_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "single_out.png"
        mock_render.return_value = out_p

        code = refined_title_main([
            "--style", "r1_oriental_center",
            "--src", str(sample_img),
            "--out", str(out_p),
            "--title", "极简宋体",
            "--latin", "MINIMAL SERIF",
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_render.call_count, 1)

    @patch("render_title_refined.render_html")
    def test_cli_main_all_mode(self, mock_render):
        sample_img = self.tmp_path / "title_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"
        mock_render.return_value = self.tmp_path / "out.png"

        code = refined_title_main([
            "--style", "all",
            "--src", str(sample_img),
            "--out", str(out_base),
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_render.call_count, 5)

    def test_cli_main_missing_src_strict_mode(self):
        missing_src = self.tmp_path / "does_not_exist.png"
        code_strict = refined_title_main([
            "--style", "r1_oriental_center",
            "--src", str(missing_src),
            "--strict",
            "--quiet",
        ])
        self.assertEqual(code_strict, 1)

        code_lenient = refined_title_main([
            "--style", "r1_oriental_center",
            "--src", str(missing_src),
            "--quiet",
        ])
        self.assertEqual(code_lenient, 0)

    @patch("render_title_refined.render_html")
    def test_cli_main_quiet_mode_suppresses_stdout(self, mock_render):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "title_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "quiet_out.png"
        mock_render.return_value = out_p

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = refined_title_main([
                "--style", "r1_oriental_center",
                "--src", str(sample_img),
                "--out", str(out_p),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_build_arg_parser(self):
        parser = refined_title_build_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("style", actions)
        self.assertIn("src", actions)
        self.assertIn("input", actions)
        self.assertIn("out", actions)
        self.assertIn("out_dir", actions)
        self.assertIn("title", actions)
        self.assertIn("latin", actions)
        self.assertIn("slogan", actions)
        self.assertIn("seal", actions)
        self.assertIn("list", actions)
        self.assertIn("json", actions)
        self.assertIn("dry_run", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_cli_main_list_json(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = refined_title_main(["--list", "--json"])
        self.assertEqual(code, 0)
        items = json.loads(buf.getvalue())
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 5)
        keys = [x["key"] for x in items]
        self.assertEqual(
            keys,
            ["r1_oriental_center", "r2_left_big", "r3_vertical_spine", "r4_sky_field", "r5_film_bottom"],
        )
        for item in items:
            self.assertIn("default_file", item)
            self.assertIn("description", item)

    def test_render_html_dry_run_returns_path_without_playwright(self):
        out_target = self.tmp_path / "dry_run_dir" / "refined_dry.png"
        res = refined_render_html("<html><body>Dry Refined</body></html>", out_target, quiet=True, dry_run=True)
        self.assertEqual(res, out_target)
        self.assertTrue(out_target.parent.exists())

    def test_render_refined_title_style_dry_run(self):
        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_target = self.tmp_path / "dry_refined_style.png"
        res = render_refined_title_style("r1_oriental_center", sample_img, out_target, dry_run=True, quiet=True)
        self.assertEqual(res, out_target)

    def test_cli_main_dry_run_single(self):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "single_dry.png"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = refined_title_main([
                "--style", "r1_oriental_center",
                "--src", str(sample_img),
                "--out", str(out_p),
                "--dry-run",
            ])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("(dry_run)", out)
        self.assertIn("single_dry.png", out)

    def test_cli_main_dry_run_all(self):
        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"

        code = refined_title_main([
            "--style", "all",
            "--src", str(sample_img),
            "--out", str(out_base),
            "--dry-run",
            "--quiet",
        ])
        self.assertEqual(code, 0)

    def test_cli_main_dry_run_json_output(self):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "sample.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = refined_title_main([
                "--style", "all",
                "--src", str(sample_img),
                "--out", str(out_base),
                "--dry-run",
                "--json",
            ])
        self.assertEqual(code, 0)
        items = json.loads(buf.getvalue())
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 5)
        for it in items:
            self.assertEqual(it["status"], "ok")
            self.assertTrue(it["dry_run"])
            self.assertIn("style", it)
            self.assertIn("output", it)

    def test_cli_main_missing_src_json_error(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = refined_title_main([
                "--src", str(self.tmp_path / "not_there.png"),
                "--json",
                "--strict",
            ])
        self.assertEqual(code, 1)
        err = json.loads(buf.getvalue())
        self.assertFalse(err.get("ok", True))
        self.assertIn("error", err)

    @patch("render_title_refined.render_refined_title_style", side_effect=RuntimeError("Simulated refined title render crash"))
    def test_main_cli_exception_stderr_output(self, mock_render):
        import io
        from contextlib import redirect_stderr
        sample_img = self.tmp_path / "refined_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = refined_title_main([
                "--style", "r1_oriental_center",
                "--src", str(sample_img),
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 高级字设海报渲染失败: Simulated refined title render crash", buf.getvalue())

    @patch("render_title_refined.render_refined_title_style", side_effect=RuntimeError("Simulated refined title quiet crash"))
    def test_main_cli_exception_quiet_mode(self, mock_render):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        sample_img = self.tmp_path / "refined_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            code = refined_title_main([
                "--style", "r1_oriental_center",
                "--src", str(sample_img),
                "-q",
            ])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_main_cli_missing_src_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        missing_src = self.tmp_path / "non_existent_refined_src.png"
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = refined_title_main([
                "--style", "r1_oriental_center",
                "--src", str(missing_src),
                "--strict",
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 找不到输入底图", buf.getvalue())

    @patch("render_title_refined.render_refined_title_style", side_effect=RuntimeError("Simulated refined title JSON crash"))
    def test_cli_main_exception_json_error(self, mock_render):
        import io
        from contextlib import redirect_stdout
        sample_img = self.tmp_path / "refined_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = refined_title_main([
                "--style", "r1_oriental_center",
                "--src", str(sample_img),
                "--json",
            ])
        self.assertEqual(code, 1)
        err = json.loads(buf.getvalue())
        self.assertFalse(err["ok"])
        self.assertIn("error", err)
        self.assertIn("Simulated refined title JSON crash", err["error"])


class TestRenderVariantsVerify(unittest.TestCase):
    """测试全量版式变体渲染器 render_variants_verify 及其 8 大版式构图与安全防御"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_b64_with_data_uri(self):
        raw_uri = "data:image/png;base64,mocked_verify_data"
        result = verify_b64(raw_uri)
        self.assertEqual(result, raw_uri)

    def test_b64_mime_types(self):
        types = [
            ("sample.png", "image/png"),
            ("sample.jpg", "image/jpeg"),
            ("sample.jpeg", "image/jpeg"),
            ("sample.webp", "image/webp"),
            ("sample.svg", "image/svg+xml"),
            ("sample.gif", "image/gif"),
        ]
        for filename, expected_mime in types:
            file_p = self.tmp_path / filename
            file_p.write_bytes(b"\x00\x01\x02\x03")
            uri = verify_b64(file_p)
            self.assertTrue(uri.startswith(f"data:{expected_mime};base64,"))
            uri_str = verify_b64(str(file_p))
            self.assertTrue(uri_str.startswith(f"data:{expected_mime};base64,"))

    def test_b64_missing_file_raises_filenotfound(self):
        with self.assertRaises(FileNotFoundError):
            verify_b64(self.tmp_path / "non_existent_poster.png")

    def test_sanitize_img_uri(self):
        malicious = "data:image/png;base64,verify\r\ndef'\"<script>"
        sanitized = verify_sanitize_img_uri(malicious)
        self.assertNotIn("\r", sanitized)
        self.assertNotIn("\n", sanitized)
        self.assertNotIn("'", sanitized)
        self.assertNotIn('"', sanitized)
        self.assertNotIn("<", sanitized)
        self.assertNotIn(">", sanitized)
        self.assertIn("%27", sanitized)
        self.assertIn("%22", sanitized)
        self.assertIn("%3C", sanitized)
        self.assertIn("%3E", sanitized)

    def test_get_base_css_and_shell(self):
        css_text = verify_get_base_css(".custom{color:red;}")
        self.assertIn("@font-face", css_text)
        self.assertIn("NSB", css_text)
        self.assertIn("PHH", css_text)
        self.assertIn("PHM", css_text)
        self.assertIn(".custom{color:red;}", css_text)

        shell_html = verify_shell("data:image/png;base64,abc", "<div>InnerContent</div>", extra=".shell{margin:0}")
        self.assertIn("InnerContent", shell_html)
        self.assertIn("data:image/png;base64,abc", shell_html)
        self.assertIn(".shell{margin:0}", shell_html)

    def test_build_v1_top_title_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_v1_top_title_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("她把城市调成静音", html_default)
        self.assertIn("font-size:110px", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_v1_top_title_html(
            "data:image/png;base64,abc",
            title="<天空标题>",
            latin="TOP & SKY",
            slogan="留白与纯粹<测试>",
            extra_css=".v1{opacity:1;}",
        )
        self.assertNotIn("<天空标题>", html_custom)
        self.assertIn("&lt;天空标题&gt;", html_custom)
        self.assertIn("TOP &amp; SKY", html_custom)
        self.assertIn("留白与纯粹&lt;测试&gt;", html_custom)
        self.assertIn(".v1{opacity:1;}", html_custom)

        # 3. None 参数防御
        html_none = build_v1_top_title_html("data:image/png;base64,abc", title=None, latin=None, slogan=None)
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)
        self.assertIn("她把城市调成静音", html_none)

    def test_build_v2_topleft_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_v2_topleft_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("width:38%", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_v2_topleft_html(
            "data:image/png;base64,abc",
            title="<左上排版>",
            latin="TOP & LEFT",
            slogan="右侧人物完整<保护>",
        )
        self.assertNotIn("<左上排版>", html_custom)
        self.assertIn("&lt;左上排版&gt;", html_custom)
        self.assertIn("TOP &amp; LEFT", html_custom)
        self.assertIn("右侧人物完整&lt;保护&gt;", html_custom)

        # 3. None 参数防御
        html_none = build_v2_topleft_html("data:image/png;base64,abc", title=None, latin=None, slogan=None)
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)

    def test_build_v3_vertical_corner_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_v3_vertical_corner_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("Night Voyage", html_default)
        self.assertIn("writing-mode:vertical-rl", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_v3_vertical_corner_html(
            "data:image/png;base64,abc",
            title="<竖排右上>",
            latin="VERTICAL & CORNER",
        )
        self.assertNotIn("<竖排右上>", html_custom)
        self.assertIn("&lt;竖排右上&gt;", html_custom)
        self.assertIn("VERTICAL &amp; CORNER", html_custom)

        # 3. None 参数防御
        html_none = build_v3_vertical_corner_html("data:image/png;base64,abc", title=None, latin=None)
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)

    def test_build_v4_bottom_left_min_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_v4_bottom_left_min_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("bottom:7%", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_v4_bottom_left_min_html(
            "data:image/png;base64,abc",
            title="<极简角标>",
            latin="MINIMAL & MICRO",
        )
        self.assertNotIn("<极简角标>", html_custom)
        self.assertIn("&lt;极简角标&gt;", html_custom)
        self.assertIn("MINIMAL &amp; MICRO", html_custom)

        # 3. None 参数防御
        html_none = build_v4_bottom_left_min_html("data:image/png;base64,abc", title=None, latin=None)
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)

    def test_build_v5_whisper_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_v5_whisper_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("2026", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_v5_whisper_html(
            "data:image/png;base64,abc",
            title="<大留白>",
            tag="2027<MMXXVII>",
        )
        self.assertNotIn("<大留白>", html_custom)
        self.assertIn("&lt;大留白&gt;", html_custom)
        self.assertIn("2027&lt;MMXXVII&gt;", html_custom)

        # 3. None 参数防御
        html_none = build_v5_whisper_html("data:image/png;base64,abc", title=None, tag=None)
        self.assertIn("夜航", html_none)
        self.assertIn("2026", html_none)

    def test_build_v6_center_top_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_v6_center_top_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("text-align:center", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_v6_center_top_html(
            "data:image/png;base64,abc",
            title="<中轴顶部>",
            latin="CENTER & TOP",
        )
        self.assertNotIn("<中轴顶部>", html_custom)
        self.assertIn("&lt;中轴顶部&gt;", html_custom)
        self.assertIn("CENTER &amp; TOP", html_custom)

        # 3. None 参数防御
        html_none = build_v6_center_top_html("data:image/png;base64,abc", title=None, latin=None)
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)

    def test_build_v7_diag_minimal_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_v7_diag_minimal_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("font-size:64px", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_v7_diag_minimal_html(
            "data:image/png;base64,abc",
            title="<对角极简>",
            latin="DIAG & MINIMAL",
        )
        self.assertNotIn("<对角极简>", html_custom)
        self.assertIn("&lt;对角极简&gt;", html_custom)
        self.assertIn("DIAG &amp; MINIMAL", html_custom)

        # 3. None 参数防御
        html_none = build_v7_diag_minimal_html("data:image/png;base64,abc", title=None, latin=None)
        self.assertIn("夜航", html_none)
        self.assertIn("Night Voyage", html_none)

    def test_build_v8_vertical_seal_html_escaping_and_defaults(self):
        # 1. 默认参数
        html_default = build_v8_vertical_seal_html("data:image/png;base64,abc")
        self.assertIn("夜航", html_default)
        self.assertIn("航", html_default)
        self.assertIn("border:1.5px solid #B4232A", html_default)

        # 2. 自定义参数与 XSS 过滤
        html_custom = build_v8_vertical_seal_html(
            "data:image/png;base64,abc",
            title="<竖排印章>",
            seal_char="印<章>",
        )
        self.assertNotIn("<竖排印章>", html_custom)
        self.assertIn("&lt;竖排印章&gt;", html_custom)
        self.assertIn("印&lt;章&gt;", html_custom)

        # 3. None 参数防御 (seal_char 自动取 title 最后一个字)
        html_none = build_v8_vertical_seal_html("data:image/png;base64,abc", title="星汉灿烂", seal_char=None)
        self.assertIn("烂", html_none)

    def test_shot_mkdir_and_invocation(self):
        out_target = self.tmp_path / "deep" / "nested" / "verify_poster.png"
        fake_page = MagicMock()
        fake_browser = MagicMock()
        fake_browser.new_page.return_value = fake_page
        fake_chromium = MagicMock()
        fake_chromium.launch.return_value = fake_browser
        fake_playwright_ctx = MagicMock()
        fake_playwright_ctx.chromium = fake_chromium
        fake_playwright_cm = MagicMock()
        fake_playwright_cm.__enter__.return_value = fake_playwright_ctx

        def fake_screenshot(path, type="png"):
            Path(path).write_bytes(b"\x89PNGfake_verify_shot")

        fake_page.screenshot.side_effect = fake_screenshot

        with patch("playwright.sync_api.sync_playwright", return_value=fake_playwright_cm):
            res_path = verify_shot("<html><body>Verify</body></html>", out_target, timeout_ms=10)
            self.assertEqual(res_path, out_target)
            self.assertTrue(out_target.exists())
            fake_page.set_content.assert_called_once_with("<html><body>Verify</body></html>")
            fake_page.wait_for_timeout.assert_called_once_with(10)
            fake_browser.close.assert_called_once()

    @patch("render_variants_verify.shot")
    def test_individual_renderer_functions(self, mock_shot):
        sample_img = self.tmp_path / "base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out_v.png"
        mock_shot.side_effect = lambda html, out, **kw: Path(out)

        # 1. render_v1_top_title
        r1 = render_v1_top_title(sample_img, out_p, title="V1测试", latin="V1 LATIN")
        self.assertEqual(r1, out_p)
        call_html1 = mock_shot.call_args[0][0]
        self.assertIn("V1测试", call_html1)
        self.assertIn("V1 LATIN", call_html1)

        # 2. render_v2_topleft
        r2 = render_v2_topleft(sample_img, out_p, title="V2测试", latin="V2 LATIN")
        self.assertEqual(r2, out_p)
        call_html2 = mock_shot.call_args[0][0]
        self.assertIn("V2测试", call_html2)

        # 3. render_v3_vertical_corner
        r3 = render_v3_vertical_corner(sample_img, out_p, title="V3测试", latin="V3 LATIN")
        self.assertEqual(r3, out_p)
        call_html3 = mock_shot.call_args[0][0]
        self.assertIn("V3测试", call_html3)

        # 4. render_v4_bottom_left_min
        r4 = render_v4_bottom_left_min(sample_img, out_p, title="V4测试", latin="V4 LATIN")
        self.assertEqual(r4, out_p)
        call_html4 = mock_shot.call_args[0][0]
        self.assertIn("V4测试", call_html4)

        # 5. render_v5_whisper
        r5 = render_v5_whisper(sample_img, out_p, title="V5测试", tag="2028")
        self.assertEqual(r5, out_p)
        call_html5 = mock_shot.call_args[0][0]
        self.assertIn("V5测试", call_html5)
        self.assertIn("2028", call_html5)

        # 6. render_v6_center_top
        r6 = render_v6_center_top(sample_img, out_p, title="V6测试", latin="V6 LATIN")
        self.assertEqual(r6, out_p)
        call_html6 = mock_shot.call_args[0][0]
        self.assertIn("V6测试", call_html6)

        # 7. render_v7_diag_minimal
        r7 = render_v7_diag_minimal(sample_img, out_p, title="V7测试", latin="V7 LATIN")
        self.assertEqual(r7, out_p)
        call_html7 = mock_shot.call_args[0][0]
        self.assertIn("V7测试", call_html7)

        # 8. render_v8_vertical_seal
        r8 = render_v8_vertical_seal(sample_img, out_p, title="V8测试", seal_char="印")
        self.assertEqual(r8, out_p)
        call_html8 = mock_shot.call_args[0][0]
        self.assertIn("V8测试", call_html8)
        self.assertIn("印", call_html8)

    @patch("render_variants_verify.shot")
    def test_render_all_variants(self, mock_shot):
        sample_img = self.tmp_path / "base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_d = self.tmp_path / "variants_batch"
        mock_shot.side_effect = lambda html, out, **kw: Path(out)

        results = verify_render_all_variants(sample_img, out_dir=out_d, title="全量变体测试")
        self.assertEqual(len(results), 8)
        self.assertEqual(mock_shot.call_count, 8)
        expected_keys = [
            "v1_top_title",
            "v2_topleft",
            "v3_vertical_corner",
            "v4_bottom_left_min",
            "v5_whisper",
            "v6_center_top",
            "v7_diag_minimal",
            "v8_vertical_seal",
        ]
        for key in expected_keys:
            self.assertIn(key, results)
            self.assertEqual(results[key].parent, out_d)

    def test_variants_registry(self):
        expected_keys = [
            "v1_top_title",
            "v2_topleft",
            "v3_vertical_corner",
            "v4_bottom_left_min",
            "v5_whisper",
            "v6_center_top",
            "v7_diag_minimal",
            "v8_vertical_seal",
        ]
        for k in expected_keys:
            self.assertIn(k, VERIFY_VARIANTS_REGISTRY)
            self.assertTrue(callable(VERIFY_VARIANTS_REGISTRY[k]["builder"]))
            self.assertTrue(callable(VERIFY_VARIANTS_REGISTRY[k]["renderer"]))
            self.assertTrue(VERIFY_VARIANTS_REGISTRY[k]["default_filename"].endswith(".png"))

    @patch("render_variants_verify.shot")
    def test_main_execution(self, mock_shot):
        mock_shot.side_effect = lambda html, out, **kw: Path(out)
        ret = render_variants_verify.main([])
        self.assertEqual(ret, 0)
        self.assertEqual(mock_shot.call_count, 8)

        # Test single variant via CLI
        mock_shot.reset_mock()
        ret_single = render_variants_verify.main(["--variant", "v2"])
        self.assertEqual(ret_single, 0)
        self.assertEqual(mock_shot.call_count, 1)

    def test_main_missing_input_returns_nonzero(self):
        ret = render_variants_verify.main(["--input", str(self.tmp_path / "does_not_exist.png")])
        self.assertEqual(ret, 1)

    @patch("playwright.sync_api.sync_playwright")
    def test_shot_quiet_mode(self, mock_playwright):
        from contextlib import redirect_stdout

        fake_page = MagicMock()
        fake_browser = MagicMock()
        fake_browser.new_page.return_value = fake_page
        mock_p_inst = MagicMock()
        mock_p_inst.chromium.launch.return_value = fake_browser
        mock_playwright.return_value.__enter__.return_value = mock_p_inst

        out_p = self.tmp_path / "shot_quiet.png"
        out_p.write_bytes(b"\x89PNG\r\n\x1a\n")

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = verify_shot("<html></html>", out_p, quiet=True)
        self.assertEqual(ret, out_p)
        self.assertEqual(buf.getvalue().strip(), "")

    @patch("render_variants_verify.shot")
    def test_render_styles_quiet_mode(self, mock_shot):
        sample_img = self.tmp_path / "variant_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "out.png"
        mock_shot.return_value = out_p

        render_v1_top_title(sample_img, out_p, quiet=True)
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

        render_v2_topleft(sample_img, out_p, quiet=True)
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

        render_v3_vertical_corner(sample_img, out_p, quiet=True)
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

        render_v4_bottom_left_min(sample_img, out_p, quiet=True)
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

        render_v5_whisper(sample_img, out_p, quiet=True)
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

        render_v6_center_top(sample_img, out_p, quiet=True)
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

        render_v7_diag_minimal(sample_img, out_p, quiet=True)
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

        render_v8_vertical_seal(sample_img, out_p, quiet=True)
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

    def test_normalize_variant_key_and_list_variants(self):
        self.assertEqual(verify_normalize_variant_key("1"), "v1_top_title")
        self.assertEqual(verify_normalize_variant_key("V1"), "v1_top_title")
        self.assertEqual(verify_normalize_variant_key("top_title"), "v1_top_title")
        self.assertEqual(verify_normalize_variant_key("v8_vertical_seal"), "v8_vertical_seal")
        with self.assertRaises(KeyError):
            verify_normalize_variant_key("v99_nonexistent")

        variants = verify_list_variants()
        self.assertEqual(len(variants), 8)
        keys = {v["key"] for v in variants}
        self.assertIn("v1_top_title", keys)
        self.assertIn("v8_vertical_seal", keys)

    @patch("render_variants_verify.shot")
    def test_render_variant_style_dispatch(self, mock_shot):
        sample_img = self.tmp_path / "variant_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "dispatched.png"
        mock_shot.return_value = out_p

        ret = verify_render_variant_style(
            "v1_top_title",
            sample_img,
            out_p,
            title="顶部测试",
            latin="TOP TEST",
            slogan="标语",
            quiet=True,
        )
        self.assertEqual(ret, out_p)
        mock_shot.assert_called()
        self.assertTrue(mock_shot.call_args[1].get("quiet", False))

        # test v8 seal dispatch
        ret8 = verify_render_variant_style(
            "8",
            sample_img,
            out_p,
            title="金石测试",
            seal_char="印",
            quiet=True,
        )
        self.assertEqual(ret8, out_p)

    def test_cli_main_list_mode(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = verify_variants_main(["--list"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Agnes Studio 可用版式变体预设清单:", out)
        self.assertIn("v1_top_title", out)
        self.assertIn("v8_vertical_seal", out)

    @patch("render_variants_verify.shot")
    def test_cli_main_single_variant_with_custom_src_and_out(self, mock_shot):
        sample_img = self.tmp_path / "variant_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "single_out.png"
        mock_shot.return_value = out_p

        code = verify_variants_main([
            "--variant", "v3",
            "--src", str(sample_img),
            "--out", str(out_p),
            "--title", "竖排测试",
            "--latin", "VERTICAL TEST",
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_shot.call_count, 1)

    @patch("render_variants_verify.shot")
    def test_cli_main_all_mode(self, mock_shot):
        sample_img = self.tmp_path / "variant_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_base = self.tmp_path / "bundle.png"
        mock_shot.return_value = self.tmp_path / "out.png"

        code = verify_variants_main([
            "--variant", "all",
            "--src", str(sample_img),
            "--out", str(out_base),
            "--quiet",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(mock_shot.call_count, 8)

    def test_cli_main_missing_src_strict_mode(self):
        missing_src = self.tmp_path / "does_not_exist.png"
        code_strict = verify_variants_main([
            "--variant", "v1",
            "--src", str(missing_src),
            "--strict",
            "--quiet",
        ])
        self.assertEqual(code_strict, 1)

        code_lenient = verify_variants_main([
            "--variant", "v1",
            "--src", str(missing_src),
            "--quiet",
        ])
        self.assertEqual(code_lenient, 0)

    @patch("render_variants_verify.shot")
    def test_cli_main_quiet_mode_suppresses_stdout(self, mock_shot):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "variant_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "quiet_out.png"
        mock_shot.return_value = out_p

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = verify_variants_main([
                "--variant", "v1",
                "--src", str(sample_img),
                "--out", str(out_p),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_build_arg_parser(self):
        parser = verify_build_arg_parser()
        self.assertIsNotNone(parser)
        parsed = parser.parse_args([
            "--variant", "v2",
            "--src", "dummy.png",
            "--out", "dummy_out.png",
            "--out-dir", "/tmp",
            "--title", "测试标题",
            "--latin", "TEST LATIN",
            "--slogan", "测试标语",
            "--list",
            "--json",
            "--dry-run",
            "--quiet",
            "--strict",
        ])
        self.assertEqual(parsed.variant, "v2")
        self.assertEqual(parsed.src, "dummy.png")
        self.assertEqual(parsed.out, "dummy_out.png")
        self.assertEqual(parsed.out_dir, "/tmp")
        self.assertEqual(parsed.title, "测试标题")
        self.assertEqual(parsed.latin, "TEST LATIN")
        self.assertEqual(parsed.slogan, "测试标语")
        self.assertTrue(parsed.list)
        self.assertTrue(parsed.json)
        self.assertTrue(parsed.dry_run)
        self.assertTrue(parsed.quiet)
        self.assertTrue(parsed.strict)

    def test_cli_main_list_json(self):
        from contextlib import redirect_stdout
        import json

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = verify_variants_main(["--list", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(len(data), 8)
        keys = [item["key"] for item in data]
        for expected in ["v1_top_title", "v2_topleft", "v8_vertical_seal"]:
            self.assertIn(expected, keys)

    def test_shot_dry_run_returns_path_without_playwright(self):
        out_p = self.tmp_path / "dry_shot.png"
        ret = verify_shot("<html></html>", out_p, quiet=True, dry_run=True)
        self.assertEqual(ret, out_p)
        self.assertFalse(out_p.exists())

    def test_cli_main_dry_run_single(self):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "variant_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_p = self.tmp_path / "dry_out.png"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = verify_variants_main([
                "--variant", "v2",
                "--src", str(sample_img),
                "--out", str(out_p),
                "--dry-run",
            ])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("DRY dry_out.png", out)
        self.assertIn("done", out)
        self.assertFalse(out_p.exists())

    def test_cli_main_dry_run_all(self):
        from contextlib import redirect_stdout

        sample_img = self.tmp_path / "variant_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_dir = self.tmp_path / "dry_batch"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = verify_variants_main([
                "--variant", "all",
                "--src", str(sample_img),
                "--out-dir", str(out_dir),
                "--dry-run",
            ])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("DRY v1_top_title.png", out)
        self.assertIn("DRY v8_vertical_seal.png", out)
        self.assertIn("done", out)

    def test_cli_main_dry_run_json_output(self):
        from contextlib import redirect_stdout
        import json

        sample_img = self.tmp_path / "variant_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_dir = self.tmp_path / "dry_batch_json"

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = verify_variants_main([
                "--variant", "all",
                "--src", str(sample_img),
                "--out-dir", str(out_dir),
                "--dry-run",
                "--json",
            ])
        self.assertEqual(code, 0)
        raw_out = buf.getvalue()
        data = json.loads(raw_out)
        self.assertEqual(len(data), 8)
        for item in data:
            self.assertEqual(item["status"], "ok")
            self.assertTrue(item["dry_run"])
            self.assertTrue(item["output"].endswith(".png"))

    def test_cli_main_strict_invalid_variant(self):
        from contextlib import redirect_stdout
        import json

        sample_img = self.tmp_path / "variant_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")

        buf_json = io.StringIO()
        with redirect_stdout(buf_json):
            code_json = verify_variants_main([
                "--variant", "invalid_variant_key",
                "--src", str(sample_img),
                "--strict",
                "--json",
            ])
        self.assertEqual(code_json, 1)
        err_data = json.loads(buf_json.getvalue())
        self.assertFalse(err_data["ok"])
        self.assertIn("Unknown variant key", err_data["error"])

        code_strict = verify_variants_main([
            "--variant", "invalid_variant_key",
            "--src", str(sample_img),
            "--strict",
            "--quiet",
        ])
        self.assertEqual(code_strict, 1)

    @patch("render_variants_verify.render_variant_style", side_effect=RuntimeError("Simulated variant render crash"))
    def test_main_cli_exception_stderr_output(self, mock_render):
        import io
        from contextlib import redirect_stderr
        sample_img = self.tmp_path / "variant_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = verify_variants_main([
                "--variant", "v1",
                "--src", str(sample_img),
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 版式变体海报渲染失败: Simulated variant render crash", buf.getvalue())

    @patch("render_variants_verify.render_variant_style", side_effect=RuntimeError("Simulated variant quiet crash"))
    def test_main_cli_exception_quiet_mode(self, mock_render):
        import io
        from contextlib import redirect_stdout, redirect_stderr
        sample_img = self.tmp_path / "variant_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            code = verify_variants_main([
                "--variant", "v1",
                "--src", str(sample_img),
                "-q",
            ])
        self.assertEqual(code, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_main_cli_missing_src_stderr_output(self):
        import io
        from contextlib import redirect_stderr
        missing_src = self.tmp_path / "non_existent_variant_src.png"
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = verify_variants_main([
                "--variant", "v1",
                "--src", str(missing_src),
                "--strict",
            ])
        self.assertEqual(code, 1)
        self.assertIn("❌ 找不到输入底图", buf.getvalue())

    @patch("render_variants_verify.render_variant_style", side_effect=RuntimeError("Simulated variant JSON crash"))
    def test_cli_main_exception_json_error(self, mock_render):
        import io
        from contextlib import redirect_stdout
        sample_img = self.tmp_path / "variant_base.png"
        sample_img.write_bytes(b"\x89PNG\r\n\x1a\n")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = verify_variants_main([
                "--variant", "v1",
                "--src", str(sample_img),
                "--json",
            ])
        self.assertEqual(code, 1)
        err = json.loads(buf.getvalue())
        self.assertFalse(err["ok"])
        self.assertIn("error", err)
        self.assertIn("Simulated variant JSON crash", err["error"])


class TestBatchLayoutCn789(unittest.TestCase):
    """测试 7/8/9 版式精修与中文排版渲染器 batch_layout_cn_789"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)
        # 创建样例底图
        self.test_img_path = self.tmp_path / "test_portrait.png"
        test_img = Image.new("RGB", (600, 800), color=(180, 170, 160))
        test_img.save(self.test_img_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_resolve_layout_font(self):
        # 1. 存在字体加载
        fnt1 = resolve_layout_font("wenkai", 24)
        self.assertIsNotNone(fnt1)

        # 2. 语义别名
        fnt2 = resolve_layout_font("smiley", 20)
        self.assertIsNotNone(fnt2)

        # 3. 不存在的字体路径应安全降级而不崩溃
        fnt3 = resolve_layout_font(self.tmp_path / "non_existent.ttf", 18)
        self.assertIsNotNone(fnt3)

        # 4. None 或空入参降级
        fnt4 = resolve_layout_font(None, 16)
        self.assertIsNotNone(fnt4)

        # 5. layout_cn_font 兼容旧接口
        fnt5 = layout_cn_font(self.tmp_path / "fake.otf", 32)
        self.assertIsNotNone(fnt5)

    def test_measure_and_text_rgba(self):
        fnt = resolve_layout_font("wenkai", 24)
        # 正常测量
        w, h = layout_cn_measure("留白设计", fnt, tracking=4)
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)

        # 空字符串测量
        w_empty, h_empty = layout_cn_measure("", fnt)
        self.assertEqual((w_empty, h_empty), (1, 1))

        # 横排图层
        layer_h = layout_cn_text_rgba((200, 50), "横排文本", fnt, (0, 0, 0, 255), tracking=2)
        self.assertEqual(layer_h.size, (200, 50))
        self.assertEqual(layer_h.mode, "RGBA")

        # 竖排图层
        layer_v = layout_cn_text_rgba((50, 200), "竖排文本", fnt, (0, 0, 0, 255), vertical=True)
        self.assertEqual(layer_v.size, (50, 200))
        self.assertEqual(layer_v.mode, "RGBA")

        # paste_rgba
        base = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
        overlay = Image.new("RGBA", (20, 20), (255, 0, 0, 255))
        layout_cn_paste_rgba(base, overlay, (10, 10))
        self.assertEqual(base.getpixel((15, 15)), (255, 0, 0, 255))

    def test_compose_07(self):
        out_p = self.tmp_path / "out_07.png"
        res = compose_07(
            src=self.test_img_path,
            out=out_p,
            title="开窗",
            latin="WINDOW",
            caption="空气与光影",
        )
        self.assertEqual(res, out_p)
        self.assertTrue(out_p.is_file())
        self.assertGreater(out_p.stat().st_size, 1000)

        # 校验底图不存在时抛出 FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            compose_07(self.tmp_path / "not_exist.png", self.tmp_path / "fail.png")

    def test_compose_08(self):
        out_p = self.tmp_path / "out_08.png"
        res = compose_08(
            src=self.test_img_path,
            out=out_p,
            title="静物",
            latin="STILL LIFE",
            caption="安静是最好的滤镜",
        )
        self.assertEqual(res, out_p)
        self.assertTrue(out_p.is_file())
        self.assertGreater(out_p.stat().st_size, 1000)

        with self.assertRaises(FileNotFoundError):
            compose_08(self.tmp_path / "not_exist.png", self.tmp_path / "fail.png")

    def test_compose_09(self):
        out_p = self.tmp_path / "out_09.png"
        res = compose_09(
            src=self.test_img_path,
            out=out_p,
            title="独白",
            latin="SOLO",
            micro="一个人的完整场",
        )
        self.assertEqual(res, out_p)
        self.assertTrue(out_p.is_file())
        self.assertGreater(out_p.stat().st_size, 1000)

        # 验证 caption 覆盖 micro 参数
        out_p2 = self.tmp_path / "out_09_cap.png"
        res2 = compose_09(
            src=self.test_img_path,
            out=out_p2,
            title="独白",
            latin="SOLO",
            caption="覆盖微文案",
        )
        self.assertTrue(out_p2.is_file())

        with self.assertRaises(FileNotFoundError):
            compose_09(self.tmp_path / "not_exist.png", self.tmp_path / "fail.png")

    def test_normalize_variant_key(self):
        self.assertEqual(normalize_layout_cn_key("07"), "07")
        self.assertEqual(normalize_layout_cn_key("7"), "07")
        self.assertEqual(normalize_layout_cn_key("07a"), "07")
        self.assertEqual(normalize_layout_cn_key("window"), "07")

        self.assertEqual(normalize_layout_cn_key("08"), "08")
        self.assertEqual(normalize_layout_cn_key("8"), "08")
        self.assertEqual(normalize_layout_cn_key("offset_window"), "08")

        self.assertEqual(normalize_layout_cn_key("09"), "09")
        self.assertEqual(normalize_layout_cn_key("9"), "09")
        self.assertEqual(normalize_layout_cn_key("solo"), "09")

        with self.assertRaises(KeyError):
            normalize_layout_cn_key("invalid_key")

    def test_render_layout_cn_and_render_all(self):
        # 1. 单项调度
        out_single = self.tmp_path / "render_07.png"
        p = render_layout_cn("07", self.test_img_path, out_single, title="观景", latin="VIEW")
        self.assertEqual(p, out_single)
        self.assertTrue(out_single.is_file())

        # 2. 全量批量调度
        out_dir = self.tmp_path / "all_out"
        all_res = render_all_layout_cn(self.test_img_path, out_dir)
        self.assertEqual(len(all_res), 3)
        for k in ("07", "08", "09"):
            self.assertIn(k, all_res)
            self.assertTrue(all_res[k].is_file())

    def test_registry_metadata(self):
        for k in ("07", "08", "09"):
            self.assertIn(k, LAYOUT_CN_REGISTRY)
            entry = LAYOUT_CN_REGISTRY[k]
            self.assertTrue(callable(entry["func"]))
            self.assertTrue(entry["default_filename"].endswith(".png"))
            self.assertTrue(len(entry["default_title"]) > 0)

    def test_main_cli_execution(self):
        # 1. 正常执行单项
        out_file = self.tmp_path / "cli_07.png"
        ret = batch_layout_cn_789.main([
            "--variant", "07",
            "--src", str(self.test_img_path),
            "--out", str(out_file),
            "--title", "测试标题",
        ])
        self.assertEqual(ret, 0)
        self.assertTrue(out_file.is_file())

        # 2. 正常执行 all
        out_all_dir = self.tmp_path / "cli_all"
        ret_all = batch_layout_cn_789.main([
            "--variant", "all",
            "--src", str(self.test_img_path),
            "--out", str(out_all_dir),
        ])
        self.assertEqual(ret_all, 0)

        # 3. 缺少底图报错
        ret_missing = batch_layout_cn_789.main([
            "--variant", "07",
            "--src", str(self.tmp_path / "not_there.png"),
        ])
        self.assertEqual(ret_missing, 1)

    def test_classify_generation_error(self):
        self.assertEqual(layout_cn_classify_error("HTTP 502: Bad Gateway"), "gateway_502")
        self.assertEqual(layout_cn_classify_error("HTTP 401: Unauthorized"), "auth")
        self.assertEqual(layout_cn_classify_error("upstream timed out"), "timeout")
        self.assertEqual(layout_cn_classify_error("invalid prompt"), "generation_error")

    def test_shots_constants(self):
        self.assertGreaterEqual(len(LAYOUT_CN_SHOTS), 6)
        for stem, prompt in LAYOUT_CN_SHOTS:
            self.assertTrue(stem)
            self.assertTrue(prompt)

    def test_generate_layout_shot_and_errors(self):
        # 1. 空 stem / prompt 参数校验
        res_no_stem = generate_layout_shot("", "prompt", out_dir=self.tmp_path)
        self.assertFalse(res_no_stem["ok"])
        self.assertEqual(res_no_stem.get("error_class"), "generation_error")

        res_no_prompt = generate_layout_shot("07a_portrait", "", out_dir=self.tmp_path)
        self.assertFalse(res_no_prompt["ok"])
        self.assertEqual(res_no_prompt.get("error_class"), "generation_error")

        # 2. 演练模式 dry_run
        res_dry = generate_layout_shot(
            "07a_portrait",
            "prompt",
            out_dir=self.tmp_path,
            dry_run=True,
        )
        self.assertTrue(res_dry["ok"])
        self.assertTrue(res_dry.get("dry_run"))

        # 3. 正常生成调用与保存
        def fake_gen(prompt, **kwargs):
            return {"ok": True, "b64": "mock_b64"}

        def fake_save(res, path):
            Path(path).write_bytes(b"x" * 25000)

        res_ok = generate_layout_shot(
            "07a_portrait",
            "prompt",
            out_dir=self.tmp_path,
            generate_fn=fake_gen,
            save_image_fn=fake_save,
        )
        self.assertTrue(res_ok["ok"])
        self.assertTrue(Path(res_ok["path"]).is_file())

        # 4. 再次执行触发跳过 (文件 > 20KB)
        res_skip = generate_layout_shot(
            "07a_portrait",
            "prompt",
            out_dir=self.tmp_path,
            generate_fn=fake_gen,
            save_image_fn=fake_save,
        )
        self.assertTrue(res_skip.get("skipped", False))

        # 5. force=True 强制重新生成
        res_force = generate_layout_shot(
            "07a_portrait",
            "prompt",
            out_dir=self.tmp_path,
            force=True,
            generate_fn=fake_gen,
            save_image_fn=fake_save,
        )
        self.assertFalse(res_force.get("skipped", False))

        # 6. 生成器不可调用
        with patch("batch_layout_cn_789.generate", None):
            res_no_gen = generate_layout_shot(
                "07b_portrait",
                "prompt",
                out_dir=self.tmp_path,
                generate_fn=None,
            )
            self.assertFalse(res_no_gen["ok"])
            self.assertEqual(res_no_gen.get("error_class"), "generation_error")

        # 7. 网关 502 错误分类
        def fake_502_gen(*args, **kwargs):
            return {"ok": False, "error": "HTTP 502: Bad Gateway"}

        res_502 = generate_layout_shot(
            "07b_portrait",
            "prompt",
            out_dir=self.tmp_path,
            generate_fn=fake_502_gen,
        )
        self.assertFalse(res_502["ok"])
        self.assertEqual(res_502.get("error_class"), "gateway_502")

        # 8. 鉴权错误分类
        def fake_auth_gen(*args, **kwargs):
            return {"ok": False, "error": "HTTP 401: Unauthorized"}

        res_auth = generate_layout_shot(
            "07b_portrait",
            "prompt",
            out_dir=self.tmp_path,
            generate_fn=fake_auth_gen,
        )
        self.assertFalse(res_auth["ok"])
        self.assertEqual(res_auth.get("error_class"), "auth")

        # 9. 超时错误分类
        def fake_timeout_gen(*args, **kwargs):
            raise TimeoutError("upstream request timed out")

        res_timeout = generate_layout_shot(
            "07b_portrait",
            "prompt",
            out_dir=self.tmp_path,
            generate_fn=fake_timeout_gen,
        )
        self.assertFalse(res_timeout["ok"])
        self.assertEqual(res_timeout.get("error_class"), "timeout")

    def test_run_batch_generate_shots_and_cli(self):
        # 1. 批量测试 (dry_run)
        sample_shots = [("test_07", "prompt 1"), ("test_08", "prompt 2")]
        rep = run_batch_generate_shots(
            out_dir=self.tmp_path / "batch_shots",
            shots=sample_shots,
            dry_run=True,
        )
        self.assertEqual(len(rep), 2)
        self.assertTrue(all(r["ok"] for r in rep))

        # 2. CLI 带 --generate 与 --dry-run
        ret = batch_layout_cn_789.main([
            "--generate",
            "--dry-run",
            "--src", str(self.test_img_path),
            "--variant", "07",
            "--out", str(self.tmp_path / "cli_gen_07.png"),
        ])
        self.assertEqual(ret, 0)

    def test_list_layout_cn_variants(self):
        variants = list_layout_cn_variants()
        self.assertIsInstance(variants, list)
        self.assertEqual(len(variants), 3)
        keys = [v["key"] for v in variants]
        self.assertEqual(keys, ["07", "08", "09"])
        for v in variants:
            self.assertIn("key", v)
            self.assertIn("name", v)
            self.assertIn("default_title", v)
            self.assertIn("default_latin", v)
            self.assertIn("default_caption", v)
            self.assertIn("default_filename", v)
            self.assertTrue(v["default_filename"].endswith(".png"))

    def test_build_layout_cn_arg_parser(self):
        parser = build_layout_cn_arg_parser()
        args = parser.parse_args(["--list", "--json", "-q", "--strict"])
        self.assertTrue(args.list)
        self.assertTrue(args.json)
        self.assertTrue(args.quiet)
        self.assertTrue(args.strict)

    def test_cli_list_and_json_modes(self):
        # 1. --list 纯文本模式
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = batch_layout_cn_789.main(["--list"])
        self.assertEqual(ret, 0)
        output = buf.getvalue()
        self.assertIn("Agnes Studio · 7/8/9 经典中文版式清单", output)
        self.assertIn("[07]", output)

        # 2. --list --json 格式化输出
        buf_json = io.StringIO()
        with redirect_stdout(buf_json):
            ret_json = batch_layout_cn_789.main(["--list", "--json"])
        self.assertEqual(ret_json, 0)
        data = json.loads(buf_json.getvalue())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["key"], "07")

        # 3. 单项渲染 + --json
        buf_single = io.StringIO()
        out_single = self.tmp_path / "cli_single_json.png"
        with redirect_stdout(buf_single):
            ret_single = batch_layout_cn_789.main([
                "--variant", "07",
                "--src", str(self.test_img_path),
                "--out", str(out_single),
                "--json",
            ])
        self.assertEqual(ret_single, 0)
        single_data = json.loads(buf_single.getvalue())
        self.assertTrue(single_data.get("ok"))
        self.assertEqual(single_data.get("variant"), "07")
        self.assertTrue(out_single.is_file())

        # 4. 全量渲染 + --json
        buf_all = io.StringIO()
        out_all_dir = self.tmp_path / "cli_all_json"
        with redirect_stdout(buf_all):
            ret_all = batch_layout_cn_789.main([
                "--variant", "all",
                "--src", str(self.test_img_path),
                "--out", str(out_all_dir),
                "--json",
            ])
        self.assertEqual(ret_all, 0)
        all_data = json.loads(buf_all.getvalue())
        self.assertTrue(all_data.get("ok"))
        self.assertEqual(len(all_data.get("results", {})), 3)

    def test_cli_quiet_and_strict_modes(self):
        # 1. quiet 模式下不输出 stdout
        buf_quiet = io.StringIO()
        with redirect_stdout(buf_quiet):
            ret = batch_layout_cn_789.main(["--list", "--quiet"])
        self.assertEqual(ret, 0)
        self.assertEqual(buf_quiet.getvalue().strip(), "")

        # 2. strict 模式在底图丢失时返回 1
        ret_strict_missing = batch_layout_cn_789.main([
            "--variant", "08",
            "--src", str(self.tmp_path / "no_such_file.png"),
            "--strict",
            "--quiet",
        ])
        self.assertEqual(ret_strict_missing, 1)

    def test_compose_quiet_parameter(self):
        # 验证 compose 函数的 quiet 参数静默标准输出
        buf = io.StringIO()
        out_p = self.tmp_path / "quiet_07.png"
        with redirect_stdout(buf):
            compose_07(
                src=self.test_img_path,
                out=out_p,
                quiet=True,
            )
        self.assertEqual(buf.getvalue().strip(), "")
        self.assertTrue(out_p.is_file())

    def test_cli_missing_source_image_json_error(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = batch_layout_cn_789.main([
                "--variant", "07",
                "--src", str(self.tmp_path / "not_found_source.png"),
                "--json",
            ])
        self.assertEqual(ret, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertIn("error", data)
        self.assertIn("找不到底图文件", data["error"])

    def test_cli_render_exception_json_error(self):
        buf = io.StringIO()
        with patch("batch_layout_cn_789.render_layout_cn", side_effect=RuntimeError("渲染过程崩溃")):
            with redirect_stdout(buf):
                ret = batch_layout_cn_789.main([
                    "--variant", "07",
                    "--src", str(self.test_img_path),
                    "--json",
                ])
        self.assertEqual(ret, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertIn("error", data)
        self.assertIn("渲染过程崩溃", data["error"])

    def test_cli_list_json_with_quiet_flag(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = batch_layout_cn_789.main(["--list", "--json", "--quiet"])
        self.assertEqual(ret, 0)
        data = json.loads(buf.getvalue().strip())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)

    def test_cli_batch_strict_missing_json_error(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = batch_layout_cn_789.main([
                "--batch",
                "--strict",
                "--json",
                "--src", str(self.tmp_path / "missing_batch_src.png"),
            ])
        self.assertEqual(ret, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertIn("error", data)

    def test_cli_main_exception_stderr_output(self):
        from contextlib import redirect_stderr
        err_buf = io.StringIO()
        with patch("batch_layout_cn_789.render_layout_cn", side_effect=RuntimeError("Simulated layout crash")):
            with redirect_stderr(err_buf):
                ret = batch_layout_cn_789.main([
                    "--variant", "07",
                    "--src", str(self.test_img_path),
                ])
        self.assertEqual(ret, 1)
        self.assertIn("❌ 执行失败: Simulated layout crash", err_buf.getvalue())

    def test_cli_main_exception_quiet_mode(self):
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with patch("batch_layout_cn_789.render_layout_cn", side_effect=RuntimeError("Simulated layout quiet crash")):
            with redirect_stdout(out_buf), redirect_stderr(err_buf):
                ret = batch_layout_cn_789.main([
                    "--variant", "07",
                    "--src", str(self.test_img_path),
                    "-q",
                ])
        self.assertEqual(ret, 1)
        self.assertEqual(out_buf.getvalue(), "")
        self.assertEqual(err_buf.getvalue(), "")

    def test_cli_missing_source_image_stderr_output(self):
        from contextlib import redirect_stderr
        err_buf = io.StringIO()
        missing_src = self.tmp_path / "non_existent_layout_cn_src.png"
        with redirect_stderr(err_buf):
            ret = batch_layout_cn_789.main([
                "--variant", "07",
                "--src", str(missing_src),
            ])
        self.assertEqual(ret, 1)
        self.assertIn("❌ 找不到底图文件", err_buf.getvalue())

    def test_cli_list_exception_json_output(self):
        buf = io.StringIO()
        with patch("batch_layout_cn_789.list_layout_cn_variants", side_effect=RuntimeError("Simulated list layout error")):
            with redirect_stdout(buf):
                code = batch_layout_cn_789.main(["--list", "--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue().strip())
            self.assertFalse(data.get("ok"))
            self.assertEqual(data.get("error"), "Simulated list layout error")

    def test_cli_list_exception_stderr_output(self):
        from contextlib import redirect_stderr
        err_buf = io.StringIO()
        with patch("batch_layout_cn_789.list_layout_cn_variants", side_effect=RuntimeError("Simulated list layout error")):
            with redirect_stderr(err_buf):
                code = batch_layout_cn_789.main(["--list"])
            self.assertEqual(code, 1)
            self.assertIn("❌ 执行失败: Simulated list layout error", err_buf.getvalue())

    def test_cli_list_exception_quiet_mode(self):
        from contextlib import redirect_stdout, redirect_stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        with patch("batch_layout_cn_789.list_layout_cn_variants", side_effect=RuntimeError("Simulated list layout error")):
            with redirect_stdout(out_buf), redirect_stderr(err_buf):
                code = batch_layout_cn_789.main(["--list", "-q"])
            self.assertEqual(code, 1)
            self.assertEqual(out_buf.getvalue(), "")
            self.assertEqual(err_buf.getvalue(), "")


class TestBatchLayoutVariants(unittest.TestCase):
    """测试 12 款经典构图版式编号册生成器 batch_layout_variants"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_catalog_and_layouts_compatibility(self):
        # 1. 验证向后兼容的元组列表
        self.assertEqual(len(BATCH_LAYOUTS), 12)
        for stem, prompt in BATCH_LAYOUTS:
            self.assertTrue(isinstance(stem, str) and len(stem) > 0)
            self.assertTrue(isinstance(prompt, str) and len(prompt) > 20)

        # 2. 验证注册表字典与元数据
        self.assertEqual(len(LAYOUT_VARIANTS), 12)
        catalog = get_layout_variants_catalog()
        self.assertEqual(len(catalog), 12)

        indices = [item["index"] for item in catalog]
        self.assertEqual(sorted(indices), list(range(1, 13)))

        for item in catalog:
            self.assertIn("stem", item)
            self.assertIn("name", item)
            self.assertIn("category", item)
            self.assertIn("word", item)
            self.assertIn("prompt", item)
            self.assertTrue(len(item["name"]) > 0)
            self.assertTrue(len(item["word"]) > 0)

    def test_find_layout_variant(self):
        # 1. 精确 stem 查找
        v1 = find_layout_variant("01_swiss_asym")
        self.assertIsNotNone(v1)
        self.assertEqual(v1["stem"], "01_swiss_asym")
        self.assertEqual(v1["word"], "FORM")

        # 2. 数字字符串与整数查找
        self.assertEqual(find_layout_variant(1)["stem"], "01_swiss_asym")
        self.assertEqual(find_layout_variant("1")["stem"], "01_swiss_asym")
        self.assertEqual(find_layout_variant("01")["stem"], "01_swiss_asym")
        self.assertEqual(find_layout_variant(12)["stem"], "12_giant_minimal")
        self.assertEqual(find_layout_variant("12")["stem"], "12_giant_minimal")

        # 3. 前缀查找
        self.assertEqual(find_layout_variant("03")["stem"], "03_type_band")
        self.assertEqual(find_layout_variant("07")["stem"], "07_window_editorial")

        # 4. 主词匹配
        self.assertEqual(find_layout_variant("SILK")["stem"], "02_swiss_asym")
        self.assertEqual(find_layout_variant("void")["stem"], "12_giant_minimal")

        # 5. 无效入参返回 None
        self.assertIsNone(find_layout_variant(None))
        self.assertIsNone(find_layout_variant(""))
        self.assertIsNone(find_layout_variant("999_non_existent"))

    def test_build_layout_prompt(self):
        # 1. 默认主词提取
        p1 = build_layout_prompt("01_swiss_asym")
        self.assertIn("FORM", p1)

        # 2. 动态替换主词
        p1_custom = build_layout_prompt("01_swiss_asym", word="AGNES")
        self.assertIn("AGNES", p1_custom)
        self.assertNotIn("FORM", p1_custom)

        # 3. 错误编号抛出 KeyError
        with self.assertRaises(KeyError):
            build_layout_prompt("invalid_key")

    def test_generate_layout_variant_dry_run(self):
        res = generate_layout_variant(
            "05_axis_tension",
            out_dir=self.tmp_path,
            dry_run=True,
        )
        self.assertTrue(res["ok"])
        self.assertTrue(res.get("dry_run"))
        self.assertEqual(res["stem"], "05_axis_tension")

    def test_generate_layout_variant_mock_success(self):
        def fake_generate(prompt, size, model, retries):
            return {"ok": True, "data": "fake_image_payload"}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"x" * 25000)

        out_fp = self.tmp_path / "mock_out"
        res = generate_layout_variant(
            "02_swiss_asym",
            out_dir=out_fp,
            generate_fn=fake_generate,
            save_image_fn=fake_save,
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["stem"], "02_swiss_asym")
        self.assertTrue(Path(res["path"]).is_file())
        self.assertGreaterEqual(res["size_kb"], 24)

    def test_generate_layout_variant_skip_existing(self):
        # 预先生成一个 > 20KB 的文件
        existing_file = self.tmp_path / "03_type_band.png"
        existing_file.write_bytes(b"x" * 25000)

        called = []
        def fake_gen(*args, **kwargs):
            called.append(True)
            return {"ok": True}

        # 1. 默认应跳过
        res_skip = generate_layout_variant(
            "03_type_band",
            out_dir=self.tmp_path,
            generate_fn=fake_gen,
            force=False,
        )
        self.assertTrue(res_skip["ok"])
        self.assertTrue(res_skip.get("skipped"))
        self.assertEqual(len(called), 0)

        # 2. force=True 应重新调用
        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"x" * 25000)

        res_force = generate_layout_variant(
            "03_type_band",
            out_dir=self.tmp_path,
            generate_fn=fake_gen,
            save_image_fn=fake_save,
            force=True,
        )
        self.assertTrue(res_force["ok"])
        self.assertFalse(res_force.get("skipped", False))
        self.assertEqual(len(called), 1)

    def test_classify_generation_error(self):
        self.assertEqual(layout_variants_classify_error("HTTP 502: Bad Gateway"), "gateway_502")
        self.assertEqual(layout_variants_classify_error("HTTP 401: Unauthorized"), "auth")
        self.assertEqual(layout_variants_classify_error("upstream timed out"), "timeout")
        self.assertEqual(layout_variants_classify_error("invalid prompt"), "generation_error")

    def test_generate_layout_variant_errors(self):
        # 1. 未知 variant
        res_unknown = generate_layout_variant("unknown_key", out_dir=self.tmp_path)
        self.assertFalse(res_unknown["ok"])
        self.assertIn("Unknown layout variant", res_unknown["err"])
        self.assertEqual(res_unknown.get("error_class"), "generation_error")

        # 2. 模拟 generate 返回失败
        def fake_fail_gen(*args, **kwargs):
            return {"ok": False, "error": "Quota exceeded"}

        res_fail = generate_layout_variant(
            "04_type_band",
            out_dir=self.tmp_path,
            generate_fn=fake_fail_gen,
        )
        self.assertFalse(res_fail["ok"])
        self.assertIn("Quota exceeded", res_fail["err"])
        self.assertEqual(res_fail.get("error_class"), "generation_error")

        # 3. 模拟抛出异常
        def fake_throw_gen(*args, **kwargs):
            raise RuntimeError("Network crash")

        res_throw = generate_layout_variant(
            "04_type_band",
            out_dir=self.tmp_path,
            generate_fn=fake_throw_gen,
        )
        self.assertFalse(res_throw["ok"])
        self.assertIn("Network crash", res_throw["err"])
        self.assertEqual(res_throw.get("error_class"), "generation_error")

        # 4. 生成器不可调用
        with patch("batch_layout_variants.generate", None):
            res_no_gen = generate_layout_variant(
                "04_type_band",
                out_dir=self.tmp_path,
                generate_fn=None,
            )
            self.assertFalse(res_no_gen["ok"])
            self.assertIn("not available or not callable", res_no_gen["err"])
            self.assertEqual(res_no_gen.get("error_class"), "generation_error")

        # 5. 网关 502 错误分类
        def fake_502_gen(*args, **kwargs):
            return {"ok": False, "error": "HTTP 502: Bad Gateway"}

        res_502 = generate_layout_variant(
            "04_type_band",
            out_dir=self.tmp_path,
            generate_fn=fake_502_gen,
        )
        self.assertFalse(res_502["ok"])
        self.assertEqual(res_502.get("error_class"), "gateway_502")

        # 6. 鉴权错误分类
        def fake_auth_gen(*args, **kwargs):
            return {"ok": False, "error": "HTTP 401: Unauthorized"}

        res_auth = generate_layout_variant(
            "04_type_band",
            out_dir=self.tmp_path,
            generate_fn=fake_auth_gen,
        )
        self.assertFalse(res_auth["ok"])
        self.assertEqual(res_auth.get("error_class"), "auth")

        # 7. 超时错误分类
        def fake_timeout_gen(*args, **kwargs):
            raise TimeoutError("upstream request timed out")

        res_timeout = generate_layout_variant(
            "04_type_band",
            out_dir=self.tmp_path,
            generate_fn=fake_timeout_gen,
        )
        self.assertFalse(res_timeout["ok"])
        self.assertEqual(res_timeout.get("error_class"), "timeout")

    def test_run_batch_layout_variants(self):
        def fake_generate(prompt, size, model, retries):
            return {"ok": True}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"x" * 22000)

        out_dir = self.tmp_path / "batch_out"
        report = run_batch_layout_variants(
            out_dir=out_dir,
            stems=["01", "02"],
            generate_fn=fake_generate,
            save_image_fn=fake_save,
        )
        self.assertEqual(len(report), 2)
        self.assertTrue(all(r["ok"] for r in report))

        # 验证 batch_report.json 已写盘
        report_file = out_dir / "batch_report.json"
        self.assertTrue(report_file.is_file())
        loaded = json.loads(report_file.read_text(encoding="utf-8"))
        self.assertEqual(len(loaded), 2)

    def test_build_layout_variants_arg_parser(self):
        parser = build_layout_variants_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)

        # 默认解析
        args = parser.parse_args([])
        self.assertFalse(args.list)
        self.assertFalse(args.json)
        self.assertFalse(args.quiet)
        self.assertFalse(args.strict)
        self.assertIsNone(args.stems)
        self.assertFalse(args.dry_run)

        # 短选项与长选项解析
        args_flags = parser.parse_args([
            "-l",
            "--json",
            "-q",
            "--strict",
            "--stems", "01,02",
            "--word", "CUSTOM",
            "--dry-run",
        ])
        self.assertTrue(args_flags.list)
        self.assertTrue(args_flags.json)
        self.assertTrue(args_flags.quiet)
        self.assertTrue(args_flags.strict)
        self.assertEqual(args_flags.stems, "01,02")
        self.assertEqual(args_flags.word, "CUSTOM")
        self.assertTrue(args_flags.dry_run)

    def test_cli_list_catalog_text_and_json(self):
        # 1. -l / --list 文本输出
        buf_text = io.StringIO()
        with redirect_stdout(buf_text):
            ret_list = batch_layout_variants.main(["-l"])
        self.assertEqual(ret_list, 0)
        output_text = buf_text.getvalue()
        self.assertIn("12 款经典构图版式清单", output_text)
        self.assertIn("01_swiss_asym", output_text)
        self.assertIn("12_giant_minimal", output_text)

        # 2. --list --json 结构化输出
        buf_json = io.StringIO()
        with redirect_stdout(buf_json):
            ret_json = batch_layout_variants.main(["--list", "--json"])
        self.assertEqual(ret_json, 0)
        catalog = json.loads(buf_json.getvalue())
        self.assertIsInstance(catalog, list)
        self.assertEqual(len(catalog), 12)
        self.assertEqual(catalog[0]["stem"], "01_swiss_asym")
        self.assertEqual(catalog[0]["word"], "FORM")
        self.assertIn("category", catalog[0])
        self.assertIn("prompt", catalog[0])

        # 3. -l -q 静默清单输出
        buf_quiet = io.StringIO()
        with redirect_stdout(buf_quiet):
            ret_quiet = batch_layout_variants.main(["-l", "-q"])
        self.assertEqual(ret_quiet, 0)
        self.assertEqual(buf_quiet.getvalue().strip(), "")

    def test_cli_json_batch_output(self):
        cli_out = self.tmp_path / "cli_json_out"
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = batch_layout_variants.main([
                "--dry-run",
                "--stems", "01,02",
                "--out", str(cli_out),
                "--json",
            ])
        self.assertEqual(ret, 0)
        # 验证 stdout 是纯净有效的 JSON，无 SKIP/OK 等控制台文本干扰
        raw_output = buf.getvalue().strip()
        report = json.loads(raw_output)
        self.assertIsInstance(report, list)
        self.assertEqual(len(report), 2)
        self.assertTrue(report[0]["ok"])
        self.assertTrue(report[0]["dry_run"])
        self.assertEqual(report[0]["stem"], "01_swiss_asym")
        self.assertEqual(report[1]["stem"], "02_swiss_asym")
        self.assertTrue((cli_out / "batch_report.json").is_file())

    def test_cli_quiet_mode(self):
        cli_out = self.tmp_path / "cli_quiet_out"
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = batch_layout_variants.main([
                "--dry-run",
                "--stems", "01",
                "--out", str(cli_out),
                "-q",
            ])
        self.assertEqual(ret, 0)
        self.assertEqual(buf.getvalue().strip(), "")
        self.assertTrue((cli_out / "batch_report.json").is_file())

    def test_cli_strict_mode(self):
        # 1. 全成功场景在 --strict 模式下返回 0
        cli_out = self.tmp_path / "cli_strict_ok"
        ret_ok = batch_layout_variants.main([
            "--dry-run",
            "--stems", "01,02",
            "--out", str(cli_out),
            "--strict",
            "-q",
        ])
        self.assertEqual(ret_ok, 0)

        # 2. 包含未知/失败项时，常规模式只要有成功即返回 0，而 --strict 返回 1
        cli_out_mixed = self.tmp_path / "cli_strict_mixed"
        ret_normal = batch_layout_variants.main([
            "--dry-run",
            "--stems", "01,999_invalid",
            "--out", str(cli_out_mixed),
            "-q",
        ])
        self.assertEqual(ret_normal, 0)  # 常规模式允许部分成功

        ret_strict = batch_layout_variants.main([
            "--dry-run",
            "--stems", "01,999_invalid",
            "--out", str(cli_out_mixed),
            "--strict",
            "-q",
        ])
        self.assertEqual(ret_strict, 1)  # strict 模式严格拦截失败

    def test_main_cli_execution(self):
        # 1. --list 命令
        ret_list = batch_layout_variants.main(["--list"])
        self.assertEqual(ret_list, 0)

        # 2. --dry-run 命令
        cli_out = self.tmp_path / "cli_dry"
        ret_dry = batch_layout_variants.main([
            "--dry-run",
            "--stems", "01,02",
            "--out", str(cli_out),
        ])
        self.assertEqual(ret_dry, 0)
        self.assertTrue((cli_out / "batch_report.json").is_file())

    def test_cli_exception_json_output(self):
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("batch_layout_variants.run_batch_layout_variants", side_effect=RuntimeError("Disk I/O error")):
            with redirect_stdout(buf):
                code = batch_layout_variants.main(["--stems", "01", "--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "Disk I/O error")

    def test_cli_exception_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("batch_layout_variants.run_batch_layout_variants", side_effect=ValueError("Invalid layout variant")):
            with redirect_stderr(buf):
                code = batch_layout_variants.main(["--stems", "01"])
            self.assertEqual(code, 1)
            self.assertIn("❌ 12 款经典构图版式批量生成失败: Invalid layout variant", buf.getvalue())

    def test_cli_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("batch_layout_variants.run_batch_layout_variants", side_effect=RuntimeError("Silent failure")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = batch_layout_variants.main(["--stems", "01", "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")

    def test_cli_list_exception_json_output(self):
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("batch_layout_variants.get_layout_variants_catalog", side_effect=RuntimeError("Catalog corrupt")):
            with redirect_stdout(buf):
                code = batch_layout_variants.main(["--list", "--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "Catalog corrupt")

    def test_cli_list_exception_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("batch_layout_variants.get_layout_variants_catalog", side_effect=RuntimeError("Catalog corrupt")):
            with redirect_stderr(buf):
                code = batch_layout_variants.main(["--list"])
            self.assertEqual(code, 1)
            self.assertIn("❌ 12 款经典构图版式批量生成失败: Catalog corrupt", buf.getvalue())

    def test_cli_list_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("batch_layout_variants.get_layout_variants_catalog", side_effect=RuntimeError("Catalog corrupt")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = batch_layout_variants.main(["--list", "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")


class TestBatchTypeBehind(unittest.TestCase):
    """测试「字在人后」(Type Behind Person) 时尚海报批量生成引擎"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_detect_language(self):
        self.assertEqual(detect_type_behind_lang("MODE"), "en")
        self.assertEqual(detect_type_behind_lang("SILK_123"), "en")
        self.assertEqual(detect_type_behind_lang("留白"), "cn")
        self.assertEqual(detect_type_behind_lang("清欢_A"), "cn")
        self.assertEqual(detect_type_behind_lang("12345"), "en")

    def test_get_preset_words(self):
        fashion = get_type_behind_presets("fashion")
        self.assertIn("MODE", fashion)
        self.assertIn("CHIC", fashion)

        zen = get_type_behind_presets("zen")
        self.assertIn("留白", zen)
        self.assertIn("风骨", zen)

        cinema = get_type_behind_presets("cinema")
        self.assertIn("NOIR", cinema)

        all_words = get_type_behind_presets()
        self.assertTrue(len(all_words) >= 15)
        self.assertIn("MODE", all_words)
        self.assertIn("留白", all_words)

    def test_build_type_behind_prompt_en(self):
        p = build_type_behind_prompt("MODE")
        self.assertIn("PRIMARY: young Asian woman", p)
        self.assertIn("giant English condensed word MODE", p)
        self.assertIn("ABSOLUTE LAYER ORDER: BACKGROUND then TYPE then PERSON", p)
        self.assertIn("Letters MODE pass BEHIND her head and body", p)
        self.assertIn("Exactly ONE word MODE. No other text.", p)
        self.assertIn("#F3EDE3", p)

    def test_build_type_behind_prompt_cn(self):
        p = build_type_behind_prompt("留白")
        self.assertIn("PRIMARY: young Asian woman", p)
        self.assertIn("giant Chinese characters 留白", p)
        self.assertIn("ABSOLUTE LAYER ORDER: BACKGROUND then TYPE then PERSON", p)
        self.assertIn("Characters 留白 pass BEHIND her head and body", p)
        self.assertIn("Exactly the characters 留白. No other text.", p)

    def test_build_type_behind_prompt_custom(self):
        custom_primary = "cyberpunk model with silver hair, neon rain reflections"
        p = build_type_behind_prompt(
            "CYBER",
            primary=custom_primary,
            ink_color="#00FFCC",
            lang="en",
        )
        self.assertIn("PRIMARY: cyberpunk model with silver hair", p)
        self.assertIn("in cream #00FFCC as BACKDROP architecture", p)

        # 强制指定 lang='cn'
        p_cn = build_type_behind_prompt(
            "CYBER",
            primary=custom_primary,
            lang="cn",
        )
        self.assertIn("giant Chinese characters CYBER", p_cn)

    def test_build_type_behind_prompt_validation(self):
        with self.assertRaises(ValueError):
            build_type_behind_prompt("")
        with self.assertRaises(ValueError):
            build_type_behind_prompt("   ")

    def test_prompt_backward_compatibility(self):
        p_compat = type_behind_prompt("MODE")
        p_standard = build_type_behind_prompt("MODE")
        self.assertEqual(p_compat, p_standard)

    def test_generate_type_behind_success(self):
        def fake_generate(prompt, size, model, retries):
            self.assertIn("MODE", prompt)
            return {"ok": True, "cost_s": 0.42, "via": "mock"}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"mock_png_data_" * 2000)

        res = generate_type_behind(
            "MODE",
            out_dir=self.tmp_path,
            generate_fn=fake_generate,
            save_image_fn=fake_save,
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["word"], "MODE")
        self.assertEqual(res["clean_word"], "MODE")
        self.assertTrue(Path(res["path"]).is_file())
        self.assertGreaterEqual(res["size_kb"], 20)
        self.assertEqual(res.get("via"), "mock")

    def test_generate_type_behind_skip_existing(self):
        existing_file = self.tmp_path / "behind_CHIC.png"
        existing_file.write_bytes(b"x" * 25000)

        called = []
        def fake_gen(*args, **kwargs):
            called.append(True)
            return {"ok": True}

        # 1. 默认应跳过
        res_skip = generate_type_behind(
            "CHIC",
            out_dir=self.tmp_path,
            generate_fn=fake_gen,
            force=False,
        )
        self.assertTrue(res_skip["ok"])
        self.assertTrue(res_skip.get("skipped"))
        self.assertEqual(len(called), 0)

        # 2. force=True 应重新调用
        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"x" * 25000)

        res_force = generate_type_behind(
            "CHIC",
            out_dir=self.tmp_path,
            generate_fn=fake_gen,
            save_image_fn=fake_save,
            force=True,
        )
        self.assertTrue(res_force["ok"])
        self.assertFalse(res_force.get("skipped", False))
        self.assertEqual(len(called), 1)

    def test_generate_type_behind_dry_run(self):
        res = generate_type_behind(
            "SILK",
            out_dir=self.tmp_path,
            dry_run=True,
        )
        self.assertTrue(res["ok"])
        self.assertTrue(res.get("dry_run"))
        self.assertIn("behind_SILK.png", res["path"])
        self.assertGreater(res["prompt_len"], 100)

    def test_classify_generation_error(self):
        self.assertEqual(type_behind_classify_error("HTTP 502: Bad Gateway"), "gateway_502")
        self.assertEqual(type_behind_classify_error("HTTP 401: Unauthorized"), "auth")
        self.assertEqual(type_behind_classify_error("upstream timed out"), "timeout")
        self.assertEqual(type_behind_classify_error("invalid prompt"), "generation_error")

    def test_generate_type_behind_errors(self):
        # 1. 空字
        res_empty = generate_type_behind("", out_dir=self.tmp_path)
        self.assertFalse(res_empty["ok"])
        self.assertIn("Word cannot be empty", res_empty["err"])
        self.assertEqual(res_empty.get("error_class"), "generation_error")

        # 2. 生成器返回失败
        def fake_fail_gen(*args, **kwargs):
            return {"ok": False, "error": "Rate limit exceeded"}

        res_fail = generate_type_behind(
            "FAIL",
            out_dir=self.tmp_path,
            generate_fn=fake_fail_gen,
        )
        self.assertFalse(res_fail["ok"])
        self.assertIn("Rate limit exceeded", res_fail["err"])
        self.assertEqual(res_fail.get("error_class"), "generation_error")

        # 3. 模拟异常
        def fake_throw_gen(*args, **kwargs):
            raise ConnectionResetError("Socket reset")

        res_throw = generate_type_behind(
            "ERR",
            out_dir=self.tmp_path,
            generate_fn=fake_throw_gen,
        )
        self.assertFalse(res_throw["ok"])
        self.assertIn("Socket reset", res_throw["err"])
        self.assertEqual(res_throw.get("error_class"), "generation_error")

        # 4. 生成器不可调用
        with patch("batch_type_behind.generate", None):
            res_no_gen = generate_type_behind(
                "NOGEN",
                out_dir=self.tmp_path,
                generate_fn=None,
            )
            self.assertFalse(res_no_gen["ok"])
            self.assertIn("not available or not callable", res_no_gen["err"])
            self.assertEqual(res_no_gen.get("error_class"), "generation_error")

        # 5. 网关 502 错误分类
        def fake_502_gen(*args, **kwargs):
            return {"ok": False, "error": "HTTP 502: Bad Gateway"}

        res_502 = generate_type_behind("MODE", out_dir=self.tmp_path, generate_fn=fake_502_gen)
        self.assertFalse(res_502["ok"])
        self.assertEqual(res_502.get("error_class"), "gateway_502")

        # 6. 超时错误分类
        def fake_timeout_gen(*args, **kwargs):
            raise TimeoutError("upstream request timed out")

        res_timeout = generate_type_behind("MODE", out_dir=self.tmp_path, generate_fn=fake_timeout_gen)
        self.assertFalse(res_timeout["ok"])
        self.assertEqual(res_timeout.get("error_class"), "timeout")

    def test_run_batch_type_behind(self):
        def fake_gen(prompt, size, model, retries):
            return {"ok": True}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"y" * 22000)

        out_dir = self.tmp_path / "batch_test"
        results = run_batch_type_behind(
            words=["MODE", "留白"],
            out_dir=out_dir,
            generate_fn=fake_gen,
            save_image_fn=fake_save,
        )
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r["ok"] for r in results))

        # 验证 report
        report_file = out_dir / "batch_report.json"
        self.assertTrue(report_file.is_file())
        report_data = json.loads(report_file.read_text(encoding="utf-8"))
        self.assertEqual(report_data["total"], 2)
        self.assertEqual(report_data["ok"], 2)
        self.assertEqual(report_data["failed"], 0)

    def test_main_cli_execution(self):
        # 1. --list-presets
        ret_list = batch_type_behind.main(["--list-presets"])
        self.assertEqual(ret_list, 0)

        # 2. --dry-run
        cli_out = self.tmp_path / "cli_dry"
        ret_dry = batch_type_behind.main([
            "--dry-run",
            "--words", "MODE,CHIC",
            "--out", str(cli_out),
        ])
        self.assertEqual(ret_dry, 0)
        self.assertTrue((cli_out / "batch_report.json").is_file())

    def test_build_arg_parser(self):
        parser = build_type_behind_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("words", actions)
        self.assertIn("out", actions)
        self.assertIn("model", actions)
        self.assertIn("size", actions)
        self.assertIn("retries", actions)
        self.assertIn("force", actions)
        self.assertIn("dry_run", actions)
        self.assertIn("primary", actions)
        self.assertIn("ink_color", actions)
        self.assertIn("lang", actions)
        self.assertIn("list_presets", actions)
        self.assertIn("json", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_cli_list_presets_json(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = batch_type_behind.main(["--list-presets", "--json"])
        self.assertEqual(code, 0)
        presets = json.loads(buf.getvalue())
        self.assertIsInstance(presets, dict)
        self.assertIn("fashion", presets)
        self.assertIn("zen", presets)
        self.assertIn("cinema", presets)
        self.assertIn("MODE", presets["fashion"])

    def test_cli_dry_run_json_output(self):
        from contextlib import redirect_stdout

        cli_out = self.tmp_path / "cli_json_dry"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = batch_type_behind.main([
                "--dry-run",
                "--words", "MODE,留白",
                "--out", str(cli_out),
                "--json",
            ])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["ok"], 2)
        self.assertEqual(data["failed"], 0)
        self.assertTrue(data["dry_run"])
        self.assertEqual(len(data["results"]), 2)

    def test_cli_quiet_mode_suppresses_stdout(self):
        from contextlib import redirect_stdout

        cli_out = self.tmp_path / "cli_quiet_dry"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = batch_type_behind.main([
                "--dry-run",
                "--words", "MODE",
                "--out", str(cli_out),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_run_batch_quiet_mode(self):
        from contextlib import redirect_stdout

        def fake_gen(prompt, size, model, retries):
            return {"ok": True}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"x" * 100)

        out_dir = self.tmp_path / "batch_quiet"
        buf = io.StringIO()
        with redirect_stdout(buf):
            results = run_batch_type_behind(
                words=["MODE"],
                out_dir=out_dir,
                generate_fn=fake_gen,
                save_image_fn=fake_save,
                quiet=True,
            )
        self.assertEqual(len(results), 1)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_cli_strict_mode_failure(self):
        with patch("batch_type_behind.generate", None):
            cli_out = self.tmp_path / "cli_strict_fail"
            code = batch_type_behind.main([
                "--words", "FAIL_WORD",
                "--out", str(cli_out),
                "--strict",
                "--quiet",
            ])
            self.assertEqual(code, 1)

    def test_cli_exception_json_output(self):
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("batch_type_behind.run_batch_type_behind", side_effect=RuntimeError("Disk full")):
            with redirect_stdout(buf):
                code = batch_type_behind.main(["--words", "MODE", "--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "Disk full")

    def test_cli_exception_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("batch_type_behind.run_batch_type_behind", side_effect=ValueError("Invalid parameters")):
            with redirect_stderr(buf):
                code = batch_type_behind.main(["--words", "MODE"])
            self.assertEqual(code, 1)
            self.assertIn("❌ 批量字在人后渲染失败: Invalid parameters", buf.getvalue())

    def test_cli_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("batch_type_behind.run_batch_type_behind", side_effect=RuntimeError("Silent failure")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = batch_type_behind.main(["--words", "MODE", "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")

    def test_cli_list_presets_exception_json_output(self):
        from contextlib import redirect_stdout

        class FaultyDict:
            def items(self):
                raise RuntimeError("Presets corrupted")

        buf = io.StringIO()
        with patch("batch_type_behind.PRESET_WORDS", new=FaultyDict()):
            with redirect_stdout(buf):
                code = batch_type_behind.main(["--list-presets", "--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "Presets corrupted")

    def test_cli_list_presets_exception_stderr_output(self):
        from contextlib import redirect_stderr

        class FaultyDict:
            def items(self):
                raise RuntimeError("Presets corrupted")

        buf = io.StringIO()
        with patch("batch_type_behind.PRESET_WORDS", new=FaultyDict()):
            with redirect_stderr(buf):
                code = batch_type_behind.main(["--list-presets"])
            self.assertEqual(code, 1)
            self.assertIn("❌ 批量字在人后渲染失败: Presets corrupted", buf.getvalue())

    def test_cli_list_presets_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout

        class FaultyDict:
            def items(self):
                raise RuntimeError("Presets corrupted")

        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("batch_type_behind.PRESET_WORDS", new=FaultyDict()):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = batch_type_behind.main(["--list-presets", "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")


class TestBatchTypeBehindV154(unittest.TestCase):
    """测试「字在人后」v154-v159 未测维度生成引擎 batch_type_behind_v154"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_versions_and_metadata(self):
        versions = list_type_behind_v154_versions()
        expected = ["v154", "v155", "v156", "v157", "v158", "v159"]
        self.assertEqual(versions, expected)
        for ver in expected:
            self.assertIn(ver, TYPE_BEHIND_V154_METADATA)
            meta = TYPE_BEHIND_V154_METADATA[ver]
            self.assertIn("title", meta)
            self.assertIn("desc", meta)
            self.assertTrue(len(meta["title"]) > 0)
            self.assertTrue(len(meta["desc"]) > 0)

    def test_list_experiments_filtering(self):
        # 1. 默认列出全部 36 组
        all_exps = list_type_behind_v154_experiments()
        self.assertEqual(len(all_exps), 36)
        self.assertEqual(len(all_exps), len(TYPE_BEHIND_V154_EXPERIMENTS))

        # 2. 按版本筛选（支持 v 前缀或纯数字）
        v154_exps = list_type_behind_v154_experiments("v154")
        self.assertEqual(len(v154_exps), 6)
        self.assertTrue(all(item[0] == "v154" for item in v154_exps))

        v157_exps = list_type_behind_v154_experiments("157")
        self.assertEqual(len(v157_exps), 6)
        self.assertTrue(all(item[0] == "v157" for item in v157_exps))

        # 3. 不存在版本返回空列表
        empty_exps = list_type_behind_v154_experiments("v999")
        self.assertEqual(len(empty_exps), 0)

    def test_get_experiment_by_stem(self):
        # 1. 存在 stem
        exp = get_type_behind_v154_experiment_by_stem("r154_out")
        self.assertIsNotNone(exp)
        self.assertEqual(exp[0], "v154")
        self.assertEqual(exp[1], "r154_out")
        self.assertIn("PRIMARY:", exp[2])

        # 2. 中文多字实验 stem
        exp_cn = get_type_behind_v154_experiment_by_stem("r157_cn_qing")
        self.assertIsNotNone(exp_cn)
        self.assertEqual(exp_cn[0], "v157")
        self.assertIn("清欢", exp_cn[2])

        # 3. 不存在或空输入
        self.assertIsNone(get_type_behind_v154_experiment_by_stem("non_existent_stem"))
        self.assertIsNone(get_type_behind_v154_experiment_by_stem(""))
        self.assertIsNone(get_type_behind_v154_experiment_by_stem(None))

    def test_generate_single_validation(self):
        # 1. stem 为空
        res_no_stem = generate_type_behind_v154_single(
            ver="v154", stem="", prompt="some prompt", out_dir=self.tmp_path
        )
        self.assertFalse(res_no_stem["ok"])
        self.assertIn("Stem cannot be empty", res_no_stem["err"])

        # 2. prompt 为空
        res_no_prompt = generate_type_behind_v154_single(
            ver="v154", stem="r154_test", prompt="", out_dir=self.tmp_path
        )
        self.assertFalse(res_no_prompt["ok"])
        self.assertIn("Prompt cannot be empty", res_no_prompt["err"])

    def test_generate_single_dry_run(self):
        res = generate_type_behind_v154_single(
            ver="v154",
            stem="r154_test_dry",
            prompt="PRIMARY: model SECONDARY: MODE",
            out_dir=self.tmp_path,
            dry_run=True,
        )
        self.assertTrue(res["ok"])
        self.assertTrue(res.get("dry_run"))
        self.assertEqual(res["stem"], "r154_test_dry")
        self.assertIn("r154_test_dry.png", res["path"])
        self.assertGreater(res["prompt_len"], 0)

    def test_generate_single_success_and_skip(self):
        called = []
        def fake_generate(prompt, size, model, retries):
            called.append(prompt)
            return {"ok": True, "cost_s": 0.35, "via": "mock_v154"}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"data_png_v154_" * 2500)

        # 1. 成功生成
        res = generate_type_behind_v154_single(
            ver="v154",
            stem="r154_out",
            prompt="PRIMARY: woman SECONDARY: OUT",
            out_dir=self.tmp_path,
            generate_fn=fake_generate,
            save_image_fn=fake_save,
        )
        self.assertTrue(res["ok"])
        self.assertFalse(res.get("skipped", False))
        self.assertEqual(res["version"], "v154")
        self.assertEqual(res["stem"], "r154_out")
        self.assertEqual(res.get("via"), "mock_v154")
        self.assertTrue(Path(res["path"]).is_file())
        self.assertGreaterEqual(res["size_kb"], 20)
        self.assertEqual(len(called), 1)

        # 2. 第二次调用（未开启 force）：跳过
        res_skip = generate_type_behind_v154_single(
            ver="v154",
            stem="r154_out",
            prompt="PRIMARY: woman SECONDARY: OUT",
            out_dir=self.tmp_path,
            generate_fn=fake_generate,
            save_image_fn=fake_save,
            force=False,
        )
        self.assertTrue(res_skip["ok"])
        self.assertTrue(res_skip.get("skipped"))
        self.assertEqual(len(called), 1)

        # 3. 第三次调用（开启 force）：重新执行
        res_force = generate_type_behind_v154_single(
            ver="v154",
            stem="r154_out",
            prompt="PRIMARY: woman SECONDARY: OUT",
            out_dir=self.tmp_path,
            generate_fn=fake_generate,
            save_image_fn=fake_save,
            force=True,
        )
        self.assertTrue(res_force["ok"])
        self.assertFalse(res_force.get("skipped", False))
        self.assertEqual(len(called), 2)

    def test_classify_generation_error(self):
        self.assertEqual(type_behind_v154_classify_error("HTTP 502: Bad Gateway"), "gateway_502")
        self.assertEqual(type_behind_v154_classify_error("HTTP 401: Unauthorized"), "auth")
        self.assertEqual(type_behind_v154_classify_error("upstream timed out"), "timeout")
        self.assertEqual(type_behind_v154_classify_error("invalid prompt"), "generation_error")

    def test_generate_single_errors(self):
        # 0. 参数校验错误
        res_no_stem = generate_type_behind_v154_single(
            ver="v154",
            stem="",
            prompt="prompt",
            out_dir=self.tmp_path,
        )
        self.assertFalse(res_no_stem["ok"])
        self.assertEqual(res_no_stem.get("error_class"), "generation_error")

        res_no_prompt = generate_type_behind_v154_single(
            ver="v154",
            stem="r154_noprompt",
            prompt="",
            out_dir=self.tmp_path,
        )
        self.assertFalse(res_no_prompt["ok"])
        self.assertEqual(res_no_prompt.get("error_class"), "generation_error")

        # 1. 生成器返回失败字典
        def fake_fail_gen(*args, **kwargs):
            return {"ok": False, "error": "Quota limit reached"}

        res_fail = generate_type_behind_v154_single(
            ver="v154",
            stem="r154_fail",
            prompt="prompt",
            out_dir=self.tmp_path,
            generate_fn=fake_fail_gen,
        )
        self.assertFalse(res_fail["ok"])
        self.assertIn("Quota limit reached", res_fail["err"])
        self.assertEqual(res_fail.get("error_class"), "generation_error")

        # 2. 生成器抛出异常
        def fake_throw_gen(*args, **kwargs):
            raise TimeoutError("Gateway timed out")

        res_throw = generate_type_behind_v154_single(
            ver="v154",
            stem="r154_err",
            prompt="prompt",
            out_dir=self.tmp_path,
            generate_fn=fake_throw_gen,
        )
        self.assertFalse(res_throw["ok"])
        self.assertIn("Gateway timed out", res_throw["err"])
        self.assertEqual(res_throw.get("error_class"), "timeout")

        # 3. 生成器不可调用
        with patch("batch_type_behind_v154.generate", None):
            res_no_gen = generate_type_behind_v154_single(
                ver="v154",
                stem="r154_nogen",
                prompt="prompt",
                out_dir=self.tmp_path,
                generate_fn=None,
            )
            self.assertFalse(res_no_gen["ok"])
            self.assertIn("not available or not callable", res_no_gen["err"])
            self.assertEqual(res_no_gen.get("error_class"), "generation_error")

        # 4. 网关 502 错误分类
        def fake_502_gen(*args, **kwargs):
            return {"ok": False, "error": "HTTP 502: Bad Gateway"}

        res_502 = generate_type_behind_v154_single(
            ver="v154",
            stem="r154_502",
            prompt="prompt",
            out_dir=self.tmp_path,
            generate_fn=fake_502_gen,
        )
        self.assertFalse(res_502["ok"])
        self.assertEqual(res_502.get("error_class"), "gateway_502")

        # 5. 鉴权错误分类
        def fake_auth_gen(*args, **kwargs):
            return {"ok": False, "error": "HTTP 401: Unauthorized"}

        res_auth = generate_type_behind_v154_single(
            ver="v154",
            stem="r154_auth",
            prompt="prompt",
            out_dir=self.tmp_path,
            generate_fn=fake_auth_gen,
        )
        self.assertFalse(res_auth["ok"])
        self.assertEqual(res_auth.get("error_class"), "auth")

    def test_run_batch_v154(self):
        def fake_gen(prompt, size, model, retries):
            return {"ok": True}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"batch_v154_data" * 2000)

        out_dir = self.tmp_path / "batch_test_v154"
        # 筛选 v157 版本且 limit=2
        results = run_batch_type_behind_v154(
            versions="v157",
            limit=2,
            out_dir=out_dir,
            generate_fn=fake_gen,
            save_image_fn=fake_save,
        )
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r["ok"] for r in results))
        self.assertTrue(all(r["version"] == "v157" for r in results))

        # 校验生成的 batch_v154_report.json
        report_file = out_dir / "batch_v154_report.json"
        self.assertTrue(report_file.is_file())
        report_data = json.loads(report_file.read_text(encoding="utf-8"))
        self.assertEqual(report_data["total"], 2)
        self.assertEqual(report_data["ok"], 2)
        self.assertEqual(report_data["failed"], 0)

        # 按照 stems 过滤
        stem_results = run_batch_type_behind_v154(
            stems="r154_out,r158_eleg",
            out_dir=out_dir,
            dry_run=True,
        )
        self.assertEqual(len(stem_results), 2)
        stems = {r["stem"] for r in stem_results}
        self.assertEqual(stems, {"r154_out", "r158_eleg"})

    def test_main_cli_execution(self):
        # 1. --list-experiments
        ret_list = batch_type_behind_v154.main(["--list-experiments"])
        self.assertEqual(ret_list, 0)

        # 2. --dry-run CLI 执行
        cli_out = self.tmp_path / "cli_dry_v154"
        ret_dry = batch_type_behind_v154.main([
            "--dry-run",
            "-v", "v154",
            "-n", "2",
            "--out", str(cli_out),
        ])
        self.assertEqual(ret_dry, 0)
        self.assertTrue((cli_out / "batch_v154_report.json").is_file())

    def test_build_arg_parser(self):
        parser = build_type_behind_v154_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("list_experiments", actions)
        self.assertIn("version", actions)
        self.assertIn("stems", actions)
        self.assertIn("limit", actions)
        self.assertIn("out", actions)
        self.assertIn("model", actions)
        self.assertIn("size", actions)
        self.assertIn("retries", actions)
        self.assertIn("force", actions)
        self.assertIn("dry_run", actions)
        self.assertIn("json", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_cli_list_experiments_json(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = batch_type_behind_v154.main(["--list-experiments", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 6)
        versions = [item["version"] for item in data]
        self.assertEqual(versions, ["v154", "v155", "v156", "v157", "v158", "v159"])
        for item in data:
            self.assertIn("title", item)
            self.assertIn("description", item)
            self.assertIn("count", item)
            self.assertEqual(item["count"], len(item["experiments"]))
            self.assertGreater(len(item["experiments"]), 0)
            for exp in item["experiments"]:
                self.assertIn("stem", exp)
                self.assertIn("prompt", exp)

    def test_cli_dry_run_json_output(self):
        from contextlib import redirect_stdout

        cli_out = self.tmp_path / "cli_json_dry_v154"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = batch_type_behind_v154.main([
                "--dry-run",
                "-v", "v154",
                "-n", "2",
                "--out", str(cli_out),
                "--json",
            ])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["ok"], 2)
        self.assertEqual(data["failed"], 0)
        self.assertTrue(data["dry_run"])
        self.assertEqual(len(data["results"]), 2)
        self.assertTrue((cli_out / "batch_v154_report.json").is_file())

    def test_cli_quiet_mode_suppresses_stdout(self):
        from contextlib import redirect_stdout

        cli_out = self.tmp_path / "cli_quiet_dry_v154"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = batch_type_behind_v154.main([
                "--dry-run",
                "-v", "v154",
                "-n", "1",
                "--out", str(cli_out),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_run_batch_quiet_mode(self):
        from contextlib import redirect_stdout

        def fake_gen(prompt, size, model, retries):
            return {"ok": True}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"x" * 100)

        out_dir = self.tmp_path / "batch_quiet_v154"
        buf = io.StringIO()
        with redirect_stdout(buf):
            results = run_batch_type_behind_v154(
                versions="v154",
                limit=1,
                out_dir=out_dir,
                generate_fn=fake_gen,
                save_image_fn=fake_save,
                quiet=True,
            )
        self.assertEqual(len(results), 1)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_cli_strict_mode_failure(self):
        with patch("batch_type_behind_v154.generate", None):
            cli_out = self.tmp_path / "cli_strict_fail_v154"
            code = batch_type_behind_v154.main([
                "-v", "v154",
                "-n", "1",
                "--out", str(cli_out),
                "--strict",
                "--quiet",
            ])
            self.assertEqual(code, 1)

    def test_cli_exception_json_output(self):
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("batch_type_behind_v154.run_batch_v154", side_effect=RuntimeError("GPU out of memory")):
            with redirect_stdout(buf):
                code = batch_type_behind_v154.main(["-v", "v154", "--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "GPU out of memory")

    def test_cli_exception_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("batch_type_behind_v154.run_batch_v154", side_effect=ValueError("Invalid version range")):
            with redirect_stderr(buf):
                code = batch_type_behind_v154.main(["-v", "v154"])
            self.assertEqual(code, 1)
            self.assertIn("❌ 批量字在人后 v154-v159 渲染失败: Invalid version range", buf.getvalue())

    def test_cli_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("batch_type_behind_v154.run_batch_v154", side_effect=RuntimeError("Silent failure")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = batch_type_behind_v154.main(["-v", "v154", "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")

    def test_cli_list_experiments_exception_json_output(self):
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("batch_type_behind_v154.list_versions", side_effect=RuntimeError("Experiments corrupted")):
            with redirect_stdout(buf):
                code = batch_type_behind_v154.main(["--list-experiments", "--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "Experiments corrupted")

    def test_cli_list_experiments_exception_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("batch_type_behind_v154.list_versions", side_effect=RuntimeError("Experiments corrupted")):
            with redirect_stderr(buf):
                code = batch_type_behind_v154.main(["--list-experiments"])
            self.assertEqual(code, 1)
            self.assertIn("❌ 批量字在人后 v154-v159 渲染失败: Experiments corrupted", buf.getvalue())

    def test_cli_list_experiments_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("batch_type_behind_v154.list_versions", side_effect=RuntimeError("Experiments corrupted")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = batch_type_behind_v154.main(["--list-experiments", "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")


class TestBatchSkill71HifiP0(unittest.TestCase):
    """测试 P0 八套高保真生图样张批处理引擎 batch_skill71_hifi_p0"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_list_presets_and_prompts(self):
        presets = list_hifi_presets()
        self.assertEqual(len(presets), 8)
        self.assertEqual(len(presets), len(SKILL71_HIFI_P0_PROMPTS))

        expected_ids = {"S05", "S07", "S09", "S15", "S11", "N01", "S04", "S02"}
        actual_ids = {p[0] for p in presets}
        self.assertEqual(actual_ids, expected_ids)

        for sid, name, size, prompt in presets:
            self.assertTrue(len(name) > 0)
            self.assertIn("x", size)
            self.assertGreater(len(prompt), 50)

    def test_get_hifi_preset(self):
        # 1. 存在 ID
        p_s05 = get_hifi_preset("S05")
        self.assertIsNotNone(p_s05)
        self.assertEqual(p_s05["id"], "S05")
        self.assertIn("mono-color", p_s05["name"])
        self.assertEqual(p_s05["size"], "1088x1456")

        # 2. 大小写与空格兼容
        p_s07 = get_hifi_preset("  s07  ")
        self.assertIsNotNone(p_s07)
        self.assertEqual(p_s07["id"], "S07")

        p_n01 = get_hifi_preset("n01")
        self.assertIsNotNone(p_n01)
        self.assertEqual(p_n01["id"], "N01")

        # 3. 不存在或空输入
        self.assertIsNone(get_hifi_preset("NON_EXISTENT"))
        self.assertIsNone(get_hifi_preset(""))
        self.assertIsNone(get_hifi_preset(None))

    def test_render_single_hifi_validation(self):
        # 1. sid 为空
        res_no_sid = render_single_hifi("", out_dir=self.tmp_path)
        self.assertFalse(res_no_sid["ok"])
        self.assertIn("Skill ID cannot be empty", res_no_sid["err"])

        # 2. 未知 sid 且未提供 spec
        res_unknown = render_single_hifi("UNKNOWN", out_dir=self.tmp_path)
        self.assertFalse(res_unknown["ok"])
        self.assertIn("not found in PROMPTS", res_unknown["err"])

        # 3. 提供 spec 但 prompt 为空
        res_no_prompt = render_single_hifi("S05", spec={"prompt": ""}, out_dir=self.tmp_path)
        self.assertFalse(res_no_prompt["ok"])
        self.assertIn("Prompt cannot be empty", res_no_prompt["err"])

    def test_render_single_hifi_dry_run(self):
        res = render_single_hifi("S05", out_dir=self.tmp_path, dry_run=True)
        self.assertTrue(res["ok"])
        self.assertTrue(res.get("dry_run"))
        self.assertEqual(res["id"], "S05")
        self.assertTrue(res["path"].endswith(".png"))
        self.assertGreater(res["prompt_len"], 100)

    def test_render_single_hifi_success_and_skip(self):
        calls = []

        def fake_generate(prompt, size, model, retries):
            calls.append({"prompt": prompt, "size": size, "model": model})
            return {"ok": True, "cost_s": 0.42, "via": "mock_gateway", "model": model}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"data_png_hifi_" * 2000)

        # 1. 成功生成
        res = render_single_hifi(
            "S05",
            out_dir=self.tmp_path,
            generate_fn=fake_generate,
            save_image_fn=fake_save,
        )
        self.assertTrue(res["ok"])
        self.assertFalse(res.get("skipped", False))
        self.assertEqual(res["id"], "S05")
        self.assertEqual(res.get("via"), "mock_gateway")
        self.assertTrue(Path(res["path"]).is_file())
        self.assertGreaterEqual(res["kb"], 20)
        self.assertEqual(len(calls), 1)

        # 2. 第二次调用（未开启 force）：跳过
        res_skip = render_single_hifi(
            "S05",
            out_dir=self.tmp_path,
            generate_fn=fake_generate,
            save_image_fn=fake_save,
            force=False,
        )
        self.assertTrue(res_skip["ok"])
        self.assertTrue(res_skip.get("skipped"))
        self.assertEqual(len(calls), 1)

        # 3. 第三次调用（开启 force）：重新执行
        res_force = render_single_hifi(
            "S05",
            out_dir=self.tmp_path,
            generate_fn=fake_generate,
            save_image_fn=fake_save,
            force=True,
        )
        self.assertTrue(res_force["ok"])
        self.assertFalse(res_force.get("skipped", False))
        self.assertEqual(len(calls), 2)

    def test_classify_generation_error(self):
        self.assertEqual(hifi_classify_error("HTTP 502: Bad Gateway"), "gateway_502")
        self.assertEqual(hifi_classify_error("HTTP 401: Unauthorized"), "auth")
        self.assertEqual(hifi_classify_error("upstream timed out"), "timeout")
        self.assertEqual(hifi_classify_error("invalid prompt"), "generation_error")

    def test_render_single_hifi_errors(self):
        # 1. 生成器返回失败字典
        def fake_fail_gen(*args, **kwargs):
            return {"ok": False, "error": "Quota rate limit reached"}

        res_fail = render_single_hifi(
            "S05",
            out_dir=self.tmp_path,
            generate_fn=fake_fail_gen,
        )
        self.assertFalse(res_fail["ok"])
        self.assertIn("Quota rate limit reached", res_fail["err"])
        self.assertEqual(res_fail.get("error_class"), "generation_error")

        # 2. 生成器抛出异常
        def fake_throw_gen(*args, **kwargs):
            raise ConnectionError("Gateway network timeout")

        res_throw = render_single_hifi(
            "S05",
            out_dir=self.tmp_path,
            generate_fn=fake_throw_gen,
        )
        self.assertFalse(res_throw["ok"])
        self.assertIn("Gateway network timeout", res_throw["err"])
        self.assertEqual(res_throw.get("error_class"), "timeout")

        # 3. 网关 502 错误分类
        def fake_502_gen(*args, **kwargs):
            return {"ok": False, "error": "HTTP 502: Bad Gateway"}

        res_502 = render_single_hifi(
            "S05",
            out_dir=self.tmp_path,
            generate_fn=fake_502_gen,
        )
        self.assertFalse(res_502["ok"])
        self.assertEqual(res_502.get("error_class"), "gateway_502")

        # 4. 生成器不可调用
        with patch("batch_skill71_hifi_p0.generate", None):
            res_no_gen = render_single_hifi(
                "S05",
                out_dir=self.tmp_path,
                generate_fn=None,
            )
            self.assertFalse(res_no_gen["ok"])
            self.assertIn("not available or not callable", res_no_gen["err"])

    def test_run_batch_hifi(self):
        def fake_gen(prompt, size, model, retries):
            return {"ok": True, "cost_s": 0.15, "via": "mock"}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"batch_hifi_data" * 2000)

        out_dir = self.tmp_path / "batch_hifi_test"
        # 筛选 S05, S07 并且 limit=2
        results = run_batch_hifi(
            skills="S05,s07",
            limit=2,
            out_dir=out_dir,
            generate_fn=fake_gen,
            save_image_fn=fake_save,
        )
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r["ok"] for r in results))
        self.assertEqual({r["id"] for r in results}, {"S05", "S07"})

        # 校验生成的 hifi_report.json
        report_file = out_dir / "hifi_report.json"
        self.assertTrue(report_file.is_file())
        report_data = json.loads(report_file.read_text(encoding="utf-8"))
        self.assertEqual(report_data["total"], 2)
        self.assertEqual(report_data["ok"], 2)
        self.assertEqual(report_data["failed"], 0)

    def test_main_cli_execution(self):
        # 1. --list-presets
        ret_list = batch_skill71_hifi_p0.main(["--list-presets"])
        self.assertEqual(ret_list, 0)

        # 2. --dry-run CLI 执行
        cli_out = self.tmp_path / "cli_dry_hifi"
        ret_dry = batch_skill71_hifi_p0.main([
            "--dry-run",
            "-s", "S05,S09",
            "-n", "2",
            "--out", str(cli_out),
        ])
        self.assertEqual(ret_dry, 0)
        self.assertTrue((cli_out / "hifi_report.json").is_file())

    def test_build_arg_parser(self):
        parser = build_skill71_hifi_p0_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("list_presets", actions)
        self.assertIn("skills", actions)
        self.assertIn("limit", actions)
        self.assertIn("out", actions)
        self.assertIn("model", actions)
        self.assertIn("size", actions)
        self.assertIn("retries", actions)
        self.assertIn("force", actions)
        self.assertIn("dry_run", actions)
        self.assertIn("json", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_cli_list_presets_json(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = batch_skill71_hifi_p0.main(["--list-presets", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 8)
        ids = {item["id"] for item in data}
        self.assertEqual(ids, {"S05", "S07", "S09", "S15", "S11", "N01", "S04", "S02"})
        for item in data:
            self.assertIn("id", item)
            self.assertIn("name", item)
            self.assertIn("size", item)
            self.assertIn("prompt_length", item)
            self.assertIn("prompt", item)
            self.assertEqual(item["prompt_length"], len(item["prompt"]))

    def test_cli_dry_run_json_output(self):
        from contextlib import redirect_stdout

        cli_out = self.tmp_path / "cli_json_dry_hifi"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = batch_skill71_hifi_p0.main([
                "--dry-run",
                "-s", "S05,S09",
                "-n", "2",
                "--out", str(cli_out),
                "--json",
            ])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["ok"], 2)
        self.assertEqual(data["failed"], 0)
        self.assertTrue(data["dry_run"])
        self.assertEqual(len(data["results"]), 2)
        self.assertTrue((cli_out / "hifi_report.json").is_file())

    def test_cli_quiet_mode_suppresses_stdout(self):
        from contextlib import redirect_stdout

        cli_out = self.tmp_path / "cli_quiet_dry_hifi"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = batch_skill71_hifi_p0.main([
                "--dry-run",
                "-s", "S05",
                "-n", "1",
                "--out", str(cli_out),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_run_batch_quiet_mode(self):
        from contextlib import redirect_stdout

        def fake_gen(prompt, size, model, retries):
            return {"ok": True}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"x" * 100)

        out_dir = self.tmp_path / "batch_quiet_hifi"
        buf = io.StringIO()
        with redirect_stdout(buf):
            results = run_batch_hifi(
                skills="S05",
                limit=1,
                out_dir=out_dir,
                generate_fn=fake_gen,
                save_image_fn=fake_save,
                quiet=True,
            )
        self.assertEqual(len(results), 1)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_cli_strict_mode_failure(self):
        with patch("batch_skill71_hifi_p0.generate", None):
            cli_out = self.tmp_path / "cli_strict_fail_hifi"
            code = batch_skill71_hifi_p0.main([
                "-s", "S05",
                "-n", "1",
                "--out", str(cli_out),
                "--strict",
                "--quiet",
            ])
            self.assertEqual(code, 1)

    def test_cli_exception_json_output(self):
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("batch_skill71_hifi_p0.run_batch_hifi", side_effect=RuntimeError("Disk I/O error")):
            with redirect_stdout(buf):
                code = batch_skill71_hifi_p0.main(["-s", "S05", "--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "Disk I/O error")

    def test_cli_exception_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("batch_skill71_hifi_p0.run_batch_hifi", side_effect=ValueError("Invalid skill identifier")):
            with redirect_stderr(buf):
                code = batch_skill71_hifi_p0.main(["-s", "S05"])
            self.assertEqual(code, 1)
            self.assertIn("❌ P0 高保真样张批量生成失败: Invalid skill identifier", buf.getvalue())

    def test_cli_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("batch_skill71_hifi_p0.run_batch_hifi", side_effect=RuntimeError("Silent failure")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = batch_skill71_hifi_p0.main(["-s", "S05", "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")

    def test_cli_list_presets_exception_json_output(self):
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("batch_skill71_hifi_p0.list_hifi_presets", side_effect=RuntimeError("HiFi presets corrupted")):
            with redirect_stdout(buf):
                code = batch_skill71_hifi_p0.main(["--list-presets", "--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "HiFi presets corrupted")

    def test_cli_list_presets_exception_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("batch_skill71_hifi_p0.list_hifi_presets", side_effect=RuntimeError("HiFi presets corrupted")):
            with redirect_stderr(buf):
                code = batch_skill71_hifi_p0.main(["--list-presets"])
            self.assertEqual(code, 1)
            self.assertIn("❌ P0 高保真样张批量生成失败: HiFi presets corrupted", buf.getvalue())

    def test_cli_list_presets_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("batch_skill71_hifi_p0.list_hifi_presets", side_effect=RuntimeError("HiFi presets corrupted")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = batch_skill71_hifi_p0.main(["--list-presets", "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")


class TestBatchSkill71Samples(unittest.TestCase):
    """测试 71 项生图 Skill 批量样张生成引擎 batch_skill71_samples"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_slugify(self):
        self.assertEqual(skill71_slugify("星年奥德赛"), "星年奥德赛")
        self.assertEqual(skill71_slugify("hello_world! 123"), "hello_world-123")
        self.assertEqual(skill71_slugify(""), "item")
        self.assertEqual(skill71_slugify(None), "item")
        self.assertEqual(skill71_slugify("a" * 50), "a" * 28)

    def test_classify_generation_error(self):
        self.assertEqual(skill71_classify_error("HTTP 502: Bad Gateway"), "gateway_502")
        self.assertEqual(skill71_classify_error("HTTP 401: Unauthorized"), "auth")
        self.assertEqual(skill71_classify_error("upstream timed out"), "timeout")
        self.assertEqual(skill71_classify_error("invalid prompt"), "generation_error")

    def test_load_skills_index_default(self):
        skills = skill71_load_index()
        self.assertEqual(len(skills), 71)
        self.assertEqual(skills[0]["id"], "ST03")
        self.assertTrue(all("id" in s and "display_name" in s for s in skills))

    def test_load_skills_index_custom_and_errors(self):
        # 1. 正常自定义 index
        dummy_index = self.tmp_path / "custom_index.json"
        dummy_index.write_text(json.dumps({
            "skills": [
                {"id": "TEST01", "display_name": "测试技能01", "group": "测试组", "declared_skill_name": "test-01"}
            ]
        }, ensure_ascii=False), encoding="utf-8")

        loaded = skill71_load_index(dummy_index)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["id"], "TEST01")

        # 2. 文件不存在
        with self.assertRaises(FileNotFoundError):
            skill71_load_index(self.tmp_path / "not_found.json")

        # 3. 结构不合法
        invalid_index = self.tmp_path / "invalid_index.json"
        invalid_index.write_text(json.dumps({"invalid_key": []}), encoding="utf-8")
        with self.assertRaises(ValueError):
            skill71_load_index(invalid_index)

    def test_build_prompt(self):
        # 1. 默认 keep_text = False
        s1 = {
            "id": "ST03",
            "style": "抽象叙事双联",
            "scope": "9:16画幅",
            "ages": {"keep_text": False},
        }
        p1 = skill71_build_prompt(s1)
        self.assertIn(SKILL71_BASE_SUBJECT, p1)
        self.assertIn("Visual style transform: 抽象叙事双联", p1)
        self.assertIn("Constraints: 9:16画幅", p1)
        self.assertIn(SKILL71_CLEAN, p1)

        # 2. keep_text = True
        s2 = {
            "id": "S01",
            "style": "千禧海报",
            "scope": "排版海报",
            "ages": {"keep_text": True},
        }
        p2 = skill71_build_prompt(s2)
        self.assertIn("intentional poster lettering allowed", p2)
        self.assertNotIn(SKILL71_CLEAN, p2)

        # 3. 自定义 base_subject
        p3 = skill71_build_prompt(s1, base_subject="A minimalist ceramic vase on a wooden table")
        self.assertTrue(p3.startswith("A minimalist ceramic vase on a wooden table."))

        # 4. 非 dict 抛出 ValueError
        with self.assertRaises(ValueError):
            skill71_build_prompt("not a dict")

    def test_filter_skills(self):
        skills = [
            {"id": "ST03", "group": "照片转超现实叙事"},
            {"id": "ST07", "group": "照片转超现实叙事"},
            {"id": "S11", "group": "光色与氛围改造"},
            {"id": "S23", "group": "照片转插画与材质"},
        ]

        # 1. 按 ID 字符串筛选
        f_ids = skill71_filter_skills(skills, skills="st03,s11")
        self.assertEqual([s["id"] for s in f_ids], ["ST03", "S11"])

        # 2. 按 ID 列表筛选
        f_id_list = skill71_filter_skills(skills, skills=["st07"])
        self.assertEqual([s["id"] for s in f_id_list], ["ST07"])

        # 3. 按 Group 筛选
        f_grp = skill71_filter_skills(skills, group="超现实")
        self.assertEqual([s["id"] for s in f_grp], ["ST03", "ST07"])

        # 4. 按 limit 筛选
        f_lim = skill71_filter_skills(skills, limit=2)
        self.assertEqual(len(f_lim), 2)

        # 5. 组合筛选
        f_comb = skill71_filter_skills(skills, group="超现实", limit=1)
        self.assertEqual([s["id"] for s in f_comb], ["ST03"])

    def test_list_skills(self):
        items = skill71_list_skills()
        self.assertEqual(len(items), 71)
        first = items[0]
        self.assertIn("id", first)
        self.assertIn("display_name", first)
        self.assertIn("group", first)
        self.assertIn("declared_skill_name", first)
        self.assertEqual(first["id"], "ST03")

    def test_render_single_skill_sample_validation(self):
        # 1. 非 dict
        res_invalid = skill71_render_single("not-a-dict", out_dir=self.tmp_path)
        self.assertFalse(res_invalid["ok"])
        self.assertIn("Invalid skill format", res_invalid["error"])

        # 2. id 为空
        res_no_id = skill71_render_single({"display_name": "No ID"}, out_dir=self.tmp_path)
        self.assertFalse(res_no_id["ok"])
        self.assertIn("Skill ID cannot be empty", res_no_id["error"])

    def test_render_single_skill_sample_dry_run(self):
        sample_skill = {
            "id": "ST03",
            "display_name": "星年奥德赛",
            "style": "双联叙事",
        }
        res = skill71_render_single(sample_skill, out_dir=self.tmp_path, dry_run=True)
        self.assertTrue(res["ok"])
        self.assertTrue(res["dry_run"])
        self.assertEqual(res["id"], "ST03")
        self.assertTrue(res["path"].endswith(".png"))
        self.assertGreater(res["prompt_len"], 50)

    def test_render_single_skill_sample_success_and_skip(self):
        calls = []

        def fake_gen(prompt, size, model, retries):
            calls.append({"prompt": prompt, "model": model})
            return {"ok": True, "cost_s": 0.35, "via": "mock_gw"}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"data_sample_png_" * 2000)

        sample_skill = {
            "id": "ST03",
            "display_name": "星年奥德赛",
            "style": "双联叙事",
        }

        # 1. 成功生成
        res = skill71_render_single(
            sample_skill,
            out_dir=self.tmp_path,
            generate_fn=fake_gen,
            save_image_fn=fake_save,
        )
        self.assertTrue(res["ok"])
        self.assertFalse(res.get("skipped", False))
        self.assertEqual(res["id"], "ST03")
        self.assertEqual(res.get("via"), "mock_gw")
        self.assertTrue(Path(res["path"]).is_file())
        self.assertGreaterEqual(res["kb"], 20)
        self.assertEqual(len(calls), 1)

        # 2. 再次执行（未开启 force）：跳过
        res_skip = skill71_render_single(
            sample_skill,
            out_dir=self.tmp_path,
            generate_fn=fake_gen,
            save_image_fn=fake_save,
            force=False,
        )
        self.assertTrue(res_skip["ok"])
        self.assertTrue(res_skip.get("skipped"))
        self.assertEqual(len(calls), 1)

        # 3. 第三次执行（开启 force）：重新生成
        res_force = skill71_render_single(
            sample_skill,
            out_dir=self.tmp_path,
            generate_fn=fake_gen,
            save_image_fn=fake_save,
            force=True,
        )
        self.assertTrue(res_force["ok"])
        self.assertFalse(res_force.get("skipped", False))
        self.assertEqual(len(calls), 2)

    def test_render_single_skill_sample_errors(self):
        sample_skill = {"id": "ST03", "display_name": "测试"}

        # 1. 生成器返回失败字典
        def fake_fail_gen(*args, **kwargs):
            return {"ok": False, "error": "Rate limit exceeded"}

        res_fail = skill71_render_single(
            sample_skill,
            out_dir=self.tmp_path,
            generate_fn=fake_fail_gen,
        )
        self.assertFalse(res_fail["ok"])
        self.assertIn("Rate limit exceeded", res_fail["error"])

        # 2. 生成器抛出异常
        def fake_throw_gen(*args, **kwargs):
            raise TimeoutError("Network connection timed out")

        res_throw = skill71_render_single(
            sample_skill,
            out_dir=self.tmp_path,
            generate_fn=fake_throw_gen,
        )
        self.assertFalse(res_throw["ok"])
        self.assertIn("Network connection timed out", res_throw["error"])

        # 3. 生成器不可调用
        with patch("batch_skill71_samples.generate", None):
            res_no_gen = skill71_render_single(
                sample_skill,
                out_dir=self.tmp_path,
                generate_fn=None,
            )
            self.assertFalse(res_no_gen["ok"])
            self.assertIn("not available or not callable", res_no_gen["error"])

    def test_run_batch_skill_samples(self):
        def fake_gen(prompt, size, model, retries):
            return {"ok": True, "cost_s": 0.22, "via": "mock"}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"batch_sample_content" * 2000)

        out_dir = self.tmp_path / "batch_samples_test"
        results = skill71_run_batch(
            skills="ST03,st07",
            limit=2,
            out_dir=out_dir,
            generate_fn=fake_gen,
            save_image_fn=fake_save,
        )
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r["ok"] for r in results))
        self.assertEqual({r["id"] for r in results}, {"ST03", "ST07"})

        # 校验 batch_report.json 写入
        report_file = out_dir / "batch_report.json"
        self.assertTrue(report_file.is_file())
        report_data = json.loads(report_file.read_text(encoding="utf-8"))
        self.assertEqual(len(report_data), 2)
        self.assertTrue(all(r["ok"] for r in report_data))

    def test_main_cli_execution(self):
        # 1. --list-skills
        ret_list = batch_skill71_samples.main(["--list-skills"])
        self.assertEqual(ret_list, 0)

        # 2. --dry-run CLI
        cli_out = self.tmp_path / "cli_dry_skills"
        ret_dry = batch_skill71_samples.main([
            "--dry-run",
            "-s", "ST03,ST08",
            "-n", "2",
            "--out", str(cli_out),
        ])
        self.assertEqual(ret_dry, 0)
        self.assertTrue((cli_out / "batch_report.json").is_file())

    def test_one_compatibility(self):
        sample_skill = {"id": "TEST_ONE", "display_name": "兼容测试"}
        with patch("batch_skill71_samples.render_single_skill_sample") as mock_render:
            mock_render.return_value = {"id": "TEST_ONE", "ok": True}
            res = skill71_one(sample_skill)
            self.assertEqual(res["id"], "TEST_ONE")
            mock_render.assert_called_once_with(sample_skill, out_dir=batch_skill71_samples.OUT)

    def test_build_arg_parser(self):
        parser = build_skill71_samples_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("list_skills", actions)
        self.assertIn("skills", actions)
        self.assertIn("group", actions)
        self.assertIn("limit", actions)
        self.assertIn("out", actions)
        self.assertIn("workers", actions)
        self.assertIn("model", actions)
        self.assertIn("size", actions)
        self.assertIn("index", actions)
        self.assertIn("base_subject", actions)
        self.assertIn("force", actions)
        self.assertIn("dry_run", actions)
        self.assertIn("json", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_cli_list_skills_json(self):
        from contextlib import redirect_stdout

        dummy_index = self.tmp_path / "skills_test.json"
        dummy_index.write_text(json.dumps({
            "skills": [
                {"id": "TST1", "display_name": "测试1", "group": "测试组", "declared_skill_name": "tst-1"},
                {"id": "TST2", "display_name": "测试2", "group": "测试组", "declared_skill_name": "tst-2"},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = batch_skill71_samples.main(["--list-skills", "--index", str(dummy_index), "--json"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], "TST1")
        self.assertEqual(data[1]["id"], "TST2")
        for item in data:
            self.assertIn("id", item)
            self.assertIn("display_name", item)
            self.assertIn("group", item)
            self.assertIn("declared_skill_name", item)

    def test_cli_dry_run_json_output(self):
        from contextlib import redirect_stdout

        dummy_index = self.tmp_path / "skills_dry.json"
        dummy_index.write_text(json.dumps({
            "skills": [
                {"id": "DRY01", "display_name": "演练1", "group": "测试组", "declared_skill_name": "dry-1"},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        cli_out = self.tmp_path / "cli_json_dry_skill71"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = batch_skill71_samples.main([
                "--dry-run",
                "--index", str(dummy_index),
                "--out", str(cli_out),
                "--json",
            ])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["ok"], 1)
        self.assertEqual(data["failed"], 0)
        self.assertTrue(data["dry_run"])
        self.assertEqual(len(data["results"]), 1)
        self.assertTrue((cli_out / "batch_report.json").is_file())

    def test_cli_quiet_mode_suppresses_stdout(self):
        from contextlib import redirect_stdout

        dummy_index = self.tmp_path / "skills_quiet.json"
        dummy_index.write_text(json.dumps({
            "skills": [
                {"id": "Q01", "display_name": "静默1", "group": "测试组", "declared_skill_name": "q-1"},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        cli_out = self.tmp_path / "cli_quiet_dry_skill71"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = batch_skill71_samples.main([
                "--dry-run",
                "--index", str(dummy_index),
                "--out", str(cli_out),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_run_batch_quiet_mode(self):
        from contextlib import redirect_stdout

        dummy_index = self.tmp_path / "skills_batch_quiet.json"
        dummy_index.write_text(json.dumps({
            "skills": [
                {"id": "BQ01", "display_name": "批处理静默1", "group": "测试组", "declared_skill_name": "bq-1"},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        def fake_gen(prompt, size, model, retries):
            return {"ok": True}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"x" * 100)

        out_dir = self.tmp_path / "batch_quiet_samples"
        buf = io.StringIO()
        with redirect_stdout(buf):
            results = skill71_run_batch(
                index_path=dummy_index,
                out_dir=out_dir,
                generate_fn=fake_gen,
                save_image_fn=fake_save,
                quiet=True,
            )
        self.assertEqual(len(results), 1)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_cli_strict_mode_failure(self):
        dummy_index = self.tmp_path / "skills_strict.json"
        dummy_index.write_text(json.dumps({
            "skills": [
                {"id": "FAIL01", "display_name": "严格失败1", "group": "测试组", "declared_skill_name": "fail-1"},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        with patch("batch_skill71_samples.generate", None):
            cli_out = self.tmp_path / "cli_strict_fail_skill71"
            code = batch_skill71_samples.main([
                "--index", str(dummy_index),
                "--out", str(cli_out),
                "--strict",
                "--quiet",
            ])
            self.assertEqual(code, 1)

    def test_cli_exception_json_output(self):
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("batch_skill71_samples.run_batch_skill_samples", side_effect=RuntimeError("Disk I/O error")):
            with redirect_stdout(buf):
                code = batch_skill71_samples.main(["-s", "ST03", "--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "Disk I/O error")

    def test_cli_exception_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("batch_skill71_samples.run_batch_skill_samples", side_effect=ValueError("Invalid skill identifier")):
            with redirect_stderr(buf):
                code = batch_skill71_samples.main(["-s", "ST03"])
            self.assertEqual(code, 1)
            self.assertIn("❌ 71 项生图 Skill 批量样张生成失败: Invalid skill identifier", buf.getvalue())

    def test_cli_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("batch_skill71_samples.run_batch_skill_samples", side_effect=RuntimeError("Silent failure")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = batch_skill71_samples.main(["-s", "ST03", "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")

    def test_cli_list_skills_exception_json_output(self):
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("batch_skill71_samples.list_skills", side_effect=RuntimeError("Skills index corrupted")):
            with redirect_stdout(buf):
                code = batch_skill71_samples.main(["--list-skills", "--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "Skills index corrupted")

    def test_cli_list_skills_exception_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("batch_skill71_samples.list_skills", side_effect=RuntimeError("Skills index corrupted")):
            with redirect_stderr(buf):
                code = batch_skill71_samples.main(["--list-skills"])
            self.assertEqual(code, 1)
            self.assertIn("❌ 71 项生图 Skill 批量样张生成失败: Skills index corrupted", buf.getvalue())

    def test_cli_list_skills_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("batch_skill71_samples.list_skills", side_effect=RuntimeError("Skills index corrupted")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = batch_skill71_samples.main(["--list-skills", "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")


class TestMergeSkill71Gallery(unittest.TestCase):
    """测试 71 项生图 Skill 画廊合并脚本 merge_skill71_gallery"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_build_gallery_item_standard(self):
        skill = {
            "id": "ST03",
            "display_name": "星年奥德赛",
            "declared_skill_name": "odyssey-photo-diptych",
            "group": "照片转超现实叙事",
            "style": "上原照下抽象叙事双联",
            "license_note": "个人学习",
        }
        item = merge_build_gallery_item(skill, "ST03_odyssey.png", cost_s=1.234)
        self.assertEqual(item["id"], "skill71_ST03")
        self.assertEqual(item["title"], "ST03 · 星年奥德赛")
        self.assertEqual(item["category_id"], "skill-surreal")
        self.assertEqual(item["category_name"], "照片转超现实叙事")
        self.assertEqual(item["style_tag"], "ST03 · odyssey-photo-diptych")
        self.assertEqual(item["style_slug"], "odyssey-photo-diptych")
        self.assertEqual(item["desc"], "上原照下抽象叙事双联")
        self.assertIn("style_skill:ST03", item["prompt"])
        self.assertEqual(item["duration"], 1.23)
        self.assertEqual(item["img"], "skill71_samples/ST03_odyssey.png")
        self.assertEqual(item["aspect_ratio"], "3:4")
        self.assertEqual(item["model"], "agnes-image-2.5-flash")
        self.assertEqual(item["license"], "个人学习")

    def test_build_gallery_item_fallbacks_and_unknown_group(self):
        empty_skill = {}
        item_empty = merge_build_gallery_item(empty_skill, "sample.png", cost_s="invalid")
        self.assertEqual(item_empty["id"], "skill71_UNKNOWN")
        self.assertEqual(item_empty["title"], "UNKNOWN · UNKNOWN")
        self.assertEqual(item_empty["category_id"], "skill-unknown")
        self.assertEqual(item_empty["duration"], 0.0)

        custom_group_skill = {"id": "CUSTOM_01", "group": "新潮流派"}
        item_custom = merge_build_gallery_item(custom_group_skill, "custom.png", cost_s=None)
        self.assertEqual(item_custom["category_id"], "skill-custom_01")
        self.assertEqual(item_custom["category_name"], "新潮流派")
        self.assertEqual(item_custom["duration"], 0.0)

    def test_load_skills_index(self):
        # 1. 字典包裹格式
        f1 = self.tmp_path / "skills1.json"
        f1.write_text(json.dumps({"skills": [{"id": "S01"}, {"id": "S02"}]}), encoding="utf-8")
        loaded1 = merge_load_skills_index(f1)
        self.assertEqual(len(loaded1), 2)
        self.assertEqual(loaded1[0]["id"], "S01")

        # 2. 裸列表格式
        f2 = self.tmp_path / "skills2.json"
        f2.write_text(json.dumps([{"id": "S03"}]), encoding="utf-8")
        loaded2 = merge_load_skills_index(f2)
        self.assertEqual(len(loaded2), 1)

        # 3. 文件不存在
        with self.assertRaises(FileNotFoundError):
            merge_load_skills_index(self.tmp_path / "non_existent.json")

        # 4. 结构不合法
        f_bad = self.tmp_path / "skills_bad.json"
        f_bad.write_text(json.dumps("a string"), encoding="utf-8")
        with self.assertRaises(ValueError):
            merge_load_skills_index(f_bad)

    def test_load_batch_report(self):
        # 1. 缺失文件返回空字典
        empty_rep = merge_load_batch_report(self.tmp_path)
        self.assertEqual(empty_rep, {})

        # 2. 列表结构解析
        rep_file = self.tmp_path / "batch_report.json"
        rep_file.write_text(json.dumps([
            {"id": "ST03", "ok": True, "cost_s": 1.5, "path": "/tmp/st03.png"},
            {"id": "ST07", "ok": True, "cost_s": 2.1, "path": "/tmp/st07.png"},
        ]), encoding="utf-8")
        loaded = merge_load_batch_report(self.tmp_path)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded["ST03"]["cost_s"], 1.5)

        # 3. 损坏内容防崩溃
        rep_file.write_text("{corrupted-json", encoding="utf-8")
        self.assertEqual(merge_load_batch_report(self.tmp_path), {})

    def test_collect_gallery_items(self):
        samples_dir = self.tmp_path / "samples"
        samples_dir.mkdir()

        # 生成样张文件
        file_st03 = samples_dir / "ST03_odyssey_sample.png"
        file_st03.write_bytes(b"ST03 PNG DATA")
        file_st07 = samples_dir / "ST07_eye_sample.png"
        file_st07.write_bytes(b"ST07 PNG DATA")

        skills = [
            {"id": "ST03", "display_name": "星年奥德赛", "group": "照片转超现实叙事"},
            {"id": "ST07", "display_name": "星年眼眸", "group": "照片转超现实叙事"},
            {"id": "ST99", "display_name": "缺失样张项", "group": "光色与氛围改造"},
        ]

        report = {
            "ST03": {"id": "ST03", "path": str(file_st03), "cost_s": 0.88},
            # ST07 不在 report，依靠 glob 回退扫描
        }

        items, copy_tasks = merge_collect_gallery_items(skills, samples_dir, report=report)
        self.assertEqual(len(items), 2)
        self.assertEqual(len(copy_tasks), 2)

        st03_item = next(x for x in items if x["id"] == "skill71_ST03")
        self.assertEqual(st03_item["duration"], 0.88)
        self.assertEqual(st03_item["img"], f"skill71_samples/{file_st03.name}")

        st07_item = next(x for x in items if x["id"] == "skill71_ST07")
        self.assertEqual(st07_item["duration"], 0.0)
        self.assertEqual(st07_item["img"], f"skill71_samples/{file_st07.name}")

    def test_update_index_html_insertion_and_counts(self):
        sample_html = """<!DOCTYPE html>
<html>
<body>
<nav><span>资产画廊 (10)</span></nav>
<script>
    const GPT_AGNES_GALLERY = [{"id": "gpt_1", "category_id": "gpt-portrait"}];
    const MASTER_GALLERY = [{"id": "m_1", "category_id": "asian-portraits"}];
    const ECOSYSTEM_DATA = [];
</script>
</body>
</html>"""
        skill_items = [
            {"id": "skill71_ST03", "category_id": "skill-surreal"},
            {"id": "skill71_ST07", "category_id": "skill-surreal"},
        ]

        updated, meta = merge_update_index_html(sample_html, skill_items)
        self.assertIn("const SKILL71_GALLERY =", updated)
        self.assertIn("const MASTER_CATEGORIES =", updated)
        self.assertIn("const ALL_GALLERY =", updated)
        self.assertIn("资产画廊 (4)", updated)

        self.assertEqual(meta["gallery_total"], 4)
        self.assertEqual(meta["skill71"], 2)
        self.assertEqual(meta["gpt_agnes"], 1)
        self.assertEqual(meta["master"], 1)

        cats = {c["id"]: c["count"] for c in meta["categories"]}
        self.assertEqual(cats.get("all"), 4)
        self.assertEqual(cats.get("gpt-portrait"), 1)
        self.assertEqual(cats.get("asian-portraits"), 1)
        self.assertEqual(cats.get("skill-surreal"), 2)

    def test_update_index_html_idempotency_and_replacement(self):
        sample_html = """<script>
    const GPT_AGNES_GALLERY = [{"id": "g1", "category_id": "gpt-portrait"}];
    const MASTER_GALLERY = [{"id": "m1", "category_id": "asian-portraits"}];
    const SKILL71_GALLERY = [{"id": "old_skill", "category_id": "skill-surreal"}];
    const MASTER_CATEGORIES = [{"id": "all", "count": 3}];
    const ALL_GALLERY = [...GPT_AGNES_GALLERY, ...MASTER_GALLERY];
</script>
<span>资产画廊 (3)</span>"""

        new_items = [{"id": "new_skill", "category_id": "skill-atmosphere"}]
        updated, meta = merge_update_index_html(sample_html, new_items)

        self.assertNotIn("old_skill", updated)
        self.assertIn("new_skill", updated)
        self.assertIn("资产画廊 (3)", updated)
        self.assertEqual(updated.count("const SKILL71_GALLERY ="), 1)
        self.assertEqual(updated.count("const MASTER_CATEGORIES ="), 1)
        self.assertEqual(updated.count("const ALL_GALLERY ="), 1)

    def test_merge_gallery_dry_run_and_execution(self):
        # 准备沙盒文件结构
        html_file = self.tmp_path / "index.html"
        html_file.write_text("""<script>
    const GPT_AGNES_GALLERY = [{"id": "g1", "category_id": "gpt-portrait"}];
    const MASTER_GALLERY = [{"id": "m1", "category_id": "asian-portraits"}];
</script>
<span>资产画廊 (2)</span>""", encoding="utf-8")

        index_file = self.tmp_path / "skills.json"
        index_file.write_text(json.dumps({"skills": [
            {"id": "ST03", "display_name": "星年奥德赛", "group": "照片转超现实叙事"}
        ]}), encoding="utf-8")

        samples_dir = self.tmp_path / "samples"
        samples_dir.mkdir()
        sample_png = samples_dir / "ST03_test.png"
        sample_png.write_bytes(b"ST03 IMAGE BYTES")

        assets_dir = self.tmp_path / "assets" / "skill71_samples"
        report_json = self.tmp_path / "merge_report.json"

        # 1. Dry run 模式
        meta_dry = merge_gallery(
            html_path=html_file,
            index_path=index_file,
            samples_dir=samples_dir,
            assets_dir=assets_dir,
            output_json=report_json,
            dry_run=True,
        )
        self.assertTrue(meta_dry["dry_run"])
        self.assertEqual(meta_dry["copied"], 1)
        self.assertEqual(meta_dry["gallery_total"], 3)
        self.assertFalse(assets_dir.exists())
        self.assertFalse(report_json.exists())
        # HTML 原文不变
        self.assertNotIn("const SKILL71_GALLERY =", html_file.read_text(encoding="utf-8"))

        # 2. 真实执行模式
        meta_real = merge_gallery(
            html_path=html_file,
            index_path=index_file,
            samples_dir=samples_dir,
            assets_dir=assets_dir,
            output_json=report_json,
            dry_run=False,
        )
        self.assertFalse(meta_real["dry_run"])
        self.assertEqual(meta_real["copied"], 1)
        self.assertTrue((assets_dir / "ST03_test.png").is_file())
        self.assertTrue(report_json.is_file())
        updated_html = html_file.read_text(encoding="utf-8")
        self.assertIn("const SKILL71_GALLERY =", updated_html)
        self.assertIn("资产画廊 (3)", updated_html)

        # 3. HTML 不存在时抛出异常
        with self.assertRaises(FileNotFoundError):
            merge_gallery(html_path=self.tmp_path / "not_found.html", index_path=index_file)

    def test_cli_main(self):
        # 1. --list-groups
        self.assertEqual(merge_main(["--list-groups"]), 0)

        # 2. --dry-run
        self.assertEqual(merge_main(["--dry-run"]), 0)

        # 3. 传递不存在的路径时返回 1
        self.assertEqual(merge_main(["--html", str(self.tmp_path / "not_there.html")]), 1)

    def test_build_arg_parser(self):
        parser = merge_build_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("dry_run", actions)
        self.assertIn("html", actions)
        self.assertIn("index", actions)
        self.assertIn("samples_dir", actions)
        self.assertIn("assets_dir", actions)
        self.assertIn("report", actions)
        self.assertIn("output_json", actions)
        self.assertIn("list_groups", actions)
        self.assertIn("json", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_cli_list_groups_json(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = merge_main(["--list-groups", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), len(MERGE_GROUP_META))
        for item in data:
            self.assertIn("id", item)
            self.assertIn("label", item)
            self.assertIn("source_group", item)

    def test_cli_dry_run_json_output(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = merge_main(["--dry-run", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertIsInstance(data, dict)
        self.assertIn("gallery_total", data)
        self.assertIn("skill71", data)
        self.assertIn("copied", data)
        self.assertTrue(data.get("dry_run"))

    def test_cli_quiet_mode_suppresses_stdout(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = merge_main(["--dry-run", "--quiet"])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_cli_strict_json_error(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = merge_main(["--html", str(self.tmp_path / "not_there.html"), "--json", "--strict"])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue())
        self.assertFalse(data["ok"])
        self.assertIn("HTML file not found", data["error"])

    def test_cli_exception_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("merge_skill71_gallery.merge_gallery", side_effect=RuntimeError("Merge gallery disk error")):
            with redirect_stderr(buf):
                code = merge_main([])
            self.assertEqual(code, 1)
            self.assertIn("❌ 画廊合并失败: Merge gallery disk error", buf.getvalue())

    def test_cli_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("merge_skill71_gallery.merge_gallery", side_effect=RuntimeError("Merge gallery disk error")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = merge_main(["--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")

    def test_cli_exception_json_output(self):
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("merge_skill71_gallery.merge_gallery", side_effect=RuntimeError("Merge gallery disk error")):
            with redirect_stdout(buf):
                code = merge_main(["--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "Merge gallery disk error")

    def test_cli_list_groups_exception_json_output(self):
        from contextlib import redirect_stdout

        class FaultyDict:
            def items(self):
                raise RuntimeError("Group meta load error")

        buf = io.StringIO()
        with patch("merge_skill71_gallery.GROUP_META", new=FaultyDict()):
            with redirect_stdout(buf):
                code = merge_main(["--list-groups", "--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "Group meta load error")

    def test_cli_list_groups_exception_stderr_output(self):
        from contextlib import redirect_stderr

        class FaultyDict:
            def items(self):
                raise RuntimeError("Group meta load error")

        buf = io.StringIO()
        with patch("merge_skill71_gallery.GROUP_META", new=FaultyDict()):
            with redirect_stderr(buf):
                code = merge_main(["--list-groups"])
            self.assertEqual(code, 1)
            self.assertIn("❌ 71 项 Skill 分组映射读取失败: Group meta load error", buf.getvalue())

    def test_cli_list_groups_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout

        class FaultyDict:
            def items(self):
                raise RuntimeError("Group meta load error")

        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("merge_skill71_gallery.GROUP_META", new=FaultyDict()):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = merge_main(["--list-groups", "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")

    def test_public_index_html_integrity(self):
        """确保工作区真实 public/index.html 具备完整的全局画廊定义且计数精准无冲突"""
        real_html = (ROOT / "public" / "index.html").read_text(encoding="utf-8")
        self.assertIn("const GPT_AGNES_GALLERY =", real_html)
        self.assertIn("const MASTER_GALLERY =", real_html)
        self.assertIn("const SKILL71_GALLERY =", real_html)
        self.assertIn("const MASTER_CATEGORIES =", real_html)
        self.assertIn("const ALL_GALLERY =", real_html)


class TestBatchAgnesSamples(unittest.TestCase):
    """测试 GPT Image 转 Agnes 批量样张生成引擎 batch_agnes_samples"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_slugify(self):
        self.assertEqual(agnes_samples_slugify("室内棚拍-烟雾缭绕(Vol:1)"), "室内棚拍-烟雾缭绕-Vol-1")
        self.assertEqual(agnes_samples_slugify("hello_world! 123"), "hello_world-123")
        self.assertEqual(agnes_samples_slugify(""), "item")
        self.assertEqual(agnes_samples_slugify(None), "item")
        self.assertEqual(agnes_samples_slugify(12345), "item")
        self.assertEqual(agnes_samples_slugify("a" * 50, max_len=36), "a" * 36)

    def test_classify_generation_error(self):
        self.assertEqual(agnes_samples_classify_error("HTTP 502: Bad Gateway"), "gateway_502")
        self.assertEqual(agnes_samples_classify_error("HTTP 401: Unauthorized"), "auth")
        self.assertEqual(agnes_samples_classify_error("upstream timed out"), "timeout")
        self.assertEqual(agnes_samples_classify_error("invalid prompt"), "generation_error")

    def test_load_prompts_library_default(self):
        items = agnes_samples_load_lib()
        self.assertGreaterEqual(len(items), 40)
        self.assertEqual(items[0]["id"], "1001")
        self.assertTrue(all("id" in it and ("agnes_prompt" in it or "gpt_image_prompt" in it) for it in items))

    def test_load_prompts_library_custom_and_errors(self):
        # 1. 正常自定义 library
        custom_lib = self.tmp_path / "custom_prompts.json"
        custom_lib.write_text(json.dumps({
            "items": [
                {"id": "TEST_01", "title": "测试预设01", "category": "test", "agnes_prompt": "x" * 50}
            ]
        }, ensure_ascii=False), encoding="utf-8")

        loaded = agnes_samples_load_lib(custom_lib)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["id"], "TEST_01")

        # 2. 文件不存在
        with self.assertRaises(FileNotFoundError):
            agnes_samples_load_lib(self.tmp_path / "not_found.json")

        # 3. 结构不合法
        invalid_lib = self.tmp_path / "invalid_lib.json"
        invalid_lib.write_text(json.dumps({"invalid_key": []}), encoding="utf-8")
        with self.assertRaises(ValueError):
            agnes_samples_load_lib(invalid_lib)

    def test_build_item_prompt(self):
        # 1. 优先使用 agnes_prompt
        item1 = {
            "id": "1001",
            "agnes_prompt": "Clean Agnes prompt text with adequate detail.",
            "gpt_image_prompt": "Fallback GPT prompt --ar 3:4",
        }
        self.assertEqual(agnes_samples_build_prompt(item1), "Clean Agnes prompt text with adequate detail.")

        # 2. 回退使用 gpt_image_prompt
        item2 = {
            "id": "1002",
            "gpt_image_prompt": "Fallback GPT prompt without Agnes override.",
        }
        self.assertEqual(agnes_samples_build_prompt(item2), "Fallback GPT prompt without Agnes override.")

        # 3. 非 dict 返回空串
        self.assertEqual(agnes_samples_build_prompt("not a dict"), "")

    def test_filter_items(self):
        items = [
            {"id": "1001", "title": "棚拍", "category": "portrait"},
            {"id": "1002", "title": "机车", "category": "portrait"},
            {"id": "2001", "title": "汽水", "category": "product"},
            {"id": "3002", "title": "城市", "category": "poster"},
        ]

        # 1. 按 ID 字符串筛选
        f_ids = agnes_samples_filter_items(items, ids="1001,2001")
        self.assertEqual([it["id"] for it in f_ids], ["1001", "2001"])

        # 2. 按 ID 列表筛选
        f_ids_list = agnes_samples_filter_items(items, ids=["1002", "3002"])
        self.assertEqual([it["id"] for it in f_ids_list], ["1002", "3002"])

        # 3. 按分类筛选 (忽略大小写)
        f_cat = agnes_samples_filter_items(items, category="PORTRAIT")
        self.assertEqual(len(f_cat), 2)
        self.assertEqual([it["id"] for it in f_cat], ["1001", "1002"])

        # 4. limit 限制
        f_lim = agnes_samples_filter_items(items, limit=2)
        self.assertEqual(len(f_lim), 2)
        self.assertEqual([it["id"] for it in f_lim], ["1001", "1002"])

    def test_render_single_sample_validation_and_errors(self):
        # 1. 非 dict 格式
        r1 = agnes_samples_render_single("invalid", out_dir=self.tmp_path)
        self.assertFalse(r1["ok"])
        self.assertIn("expected dict", r1["error"])

        # 2. 缺少 ID
        r2 = agnes_samples_render_single({"title": "无 ID"}, out_dir=self.tmp_path)
        self.assertFalse(r2["ok"])
        self.assertIn("ID cannot be empty", r2["error"])

        # 3. prompt 长度小于 40 字符
        r3 = agnes_samples_render_single({"id": "1001", "title": "短词", "agnes_prompt": "too short"}, out_dir=self.tmp_path)
        self.assertFalse(r3["ok"])
        self.assertEqual(r3["error"], "prompt too short")

        # 4. 未提供有效的 generator
        item = {
            "id": "1001",
            "title": "测试生成",
            "agnes_prompt": "A" * 60,
        }
        r4 = agnes_samples_render_single(item, out_dir=self.tmp_path, generate_fn="not_callable")
        self.assertFalse(r4["ok"])
        self.assertIn("not available or not callable", r4["error"])

    def test_render_single_sample_dry_run_and_skip(self):
        item = {
            "id": "1001",
            "title": "室内棚拍",
            "agnes_size": "1088x1456",
            "agnes_prompt": "Editorial fashion photography of East Asian model in studio with smoke trails.",
        }

        # 1. dry-run
        r_dry = agnes_samples_render_single(item, out_dir=self.tmp_path, dry_run=True)
        self.assertTrue(r_dry["ok"])
        self.assertTrue(r_dry["dry_run"])
        self.assertEqual(r_dry["file"], "1001_室内棚拍.png")
        self.assertEqual(r_dry["size"], "1088x1456")
        self.assertFalse(Path(r_dry["path"]).exists())

        # 2. 模拟已存在大于 20KB 的文件
        existing_file = self.tmp_path / "1001_室内棚拍.png"
        existing_file.write_bytes(b"x" * 25_000)

        r_skip = agnes_samples_render_single(item, out_dir=self.tmp_path)
        self.assertTrue(r_skip["ok"])
        self.assertTrue(r_skip["skipped"])
        self.assertEqual(r_skip["kb"], 24)

        # 3. force 覆盖跳过逻辑并调用生成
        mock_gen = MagicMock(return_value={"ok": True, "cost_s": 0.88, "via": "new-api"})
        mock_saver = MagicMock()
        r_force = agnes_samples_render_single(
            item,
            out_dir=self.tmp_path,
            force=True,
            generate_fn=mock_gen,
            save_image_fn=mock_saver,
        )
        self.assertTrue(r_force["ok"])
        self.assertFalse(r_force.get("skipped", False))
        mock_gen.assert_called_once()
        mock_saver.assert_called_once()

    def test_render_single_sample_mock_success_and_failure(self):
        item = {
            "id": "2001",
            "title": "汽水广告",
            "agnes_size": "1088x1456",
            "agnes_prompt": "Commercial product shot of citrus soda bottle with energetic splash and condensation.",
        }

        # 1. 成功生成
        def fake_gen(prompt, size, model, retries):
            return {"ok": True, "cost_s": 1.25, "via": "mock-api", "model": model}

        def fake_save(res, path):
            Path(path).write_bytes(b"fake_image_data" * 1500)

        r_ok = agnes_samples_render_single(
            item,
            out_dir=self.tmp_path,
            generate_fn=fake_gen,
            save_image_fn=fake_save,
        )
        self.assertTrue(r_ok["ok"])
        self.assertEqual(r_ok["id"], "2001")
        self.assertEqual(r_ok["file"], "2001_汽水广告.png")
        self.assertEqual(r_ok["cost_s"], 1.25)
        self.assertEqual(r_ok["via"], "mock-api")
        self.assertTrue(Path(r_ok["path"]).is_file())

        # 2. 生成失败 (API 返回 ok=False)
        def fail_gen(prompt, size, model, retries):
            return {"ok": False, "error": "rate limit exceeded"}

        item_fail = {
            "id": "2002",
            "title": "失败案例",
            "agnes_prompt": "A" * 60,
        }
        r_fail = agnes_samples_render_single(
            item_fail,
            out_dir=self.tmp_path,
            generate_fn=fail_gen,
        )
        self.assertFalse(r_fail["ok"])
        self.assertEqual(r_fail["error"], "rate limit exceeded")
        self.assertEqual(r_fail["error_class"], "generation_error")

        # 3. 抛出异常
        def err_gen(prompt, size, model, retries):
            raise ConnectionResetError("network disconnected")

        r_err = agnes_samples_render_single(
            item_fail,
            out_dir=self.tmp_path,
            generate_fn=err_gen,
        )
        self.assertFalse(r_err["ok"])
        self.assertIn("network disconnected", r_err["error"])
        self.assertEqual(r_err["error_class"], "generation_error")

        # 4. 网关 502 错误分类
        def gateway_fail_gen(prompt, size, model, retries):
            return {"ok": False, "error": "HTTP 502: Bad Gateway"}

        r_502 = agnes_samples_render_single(
            item_fail,
            out_dir=self.tmp_path,
            generate_fn=gateway_fail_gen,
        )
        self.assertFalse(r_502["ok"])
        self.assertEqual(r_502["error_class"], "gateway_502")

    def test_run_batch_agnes_samples_and_cli(self):
        batch_out = self.tmp_path / "batch_out"

        # 1. run_batch_agnes_samples dry run
        results_dry = agnes_samples_run_batch(
            ids="1001,1002",
            out_dir=batch_out,
            dry_run=True,
        )
        self.assertEqual(len(results_dry), 2)
        self.assertTrue(all(r["ok"] and r.get("dry_run") for r in results_dry))
        report_file = batch_out / "batch_report.json"
        self.assertTrue(report_file.is_file())
        report_data = json.loads(report_file.read_text(encoding="utf-8"))
        self.assertEqual(len(report_data), 2)

        # 2. run_batch_agnes_samples with mock generator
        real_batch_out = self.tmp_path / "batch_real"
        def mock_gen(prompt, size, model, retries):
            return {"ok": True, "cost_s": 0.5, "via": "mock"}

        def mock_save(res, path):
            Path(path).write_bytes(b"img" * 8000)

        results_real = agnes_samples_run_batch(
            limit=2,
            out_dir=real_batch_out,
            workers=1,
            generate_fn=mock_gen,
            save_image_fn=mock_save,
        )
        self.assertEqual(len(results_real), 2)
        self.assertTrue(all(r["ok"] for r in results_real))
        self.assertTrue((real_batch_out / "batch_report.json").is_file())

        # 3. CLI --list-items
        self.assertEqual(agnes_samples_main(["--list-items"]), 0)

        # 4. CLI --dry-run
        cli_out = self.tmp_path / "cli_dry"
        self.assertEqual(agnes_samples_main(["--dry-run", "-n", "2", "-o", str(cli_out)]), 0)
        self.assertTrue((cli_out / "batch_report.json").is_file())

        # 5. CLI 传递不存在的 lib 时返回非 0 退出码 1
        self.assertEqual(
            agnes_samples_main(["--lib", str(self.tmp_path / "not_there.json")]),
            1,
        )

    def test_list_items_and_one_compat(self):
        items = agnes_samples_list_items()
        self.assertGreaterEqual(len(items), 40)
        self.assertEqual(items[0]["id"], "1001")
        self.assertIn("category", items[0])
        self.assertIn("agnes_size", items[0])

        # test one() compat with dry run
        mock_item = {
            "id": "9999",
            "title": "兼容测试",
            "agnes_prompt": "A" * 50,
        }
        res = agnes_samples_render_single(mock_item, out_dir=self.tmp_path, dry_run=True)
        self.assertTrue(res["ok"])
        self.assertEqual(res["id"], "9999")

    def test_build_arg_parser(self):
        parser = build_agnes_samples_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("list_items", actions)
        self.assertIn("ids", actions)
        self.assertIn("category", actions)
        self.assertIn("limit", actions)
        self.assertIn("out", actions)
        self.assertIn("workers", actions)
        self.assertIn("model", actions)
        self.assertIn("size", actions)
        self.assertIn("lib", actions)
        self.assertIn("force", actions)
        self.assertIn("dry_run", actions)
        self.assertIn("json", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_cli_list_items_json(self):
        from contextlib import redirect_stdout

        dummy_lib = self.tmp_path / "lib_test.json"
        dummy_lib.write_text(json.dumps({
            "items": [
                {"id": "L01", "title": "测试预设1", "category": "cat1", "agnes_size": "1024x1024", "agnes_prompt": "p" * 50},
                {"id": "L02", "title": "测试预设2", "category": "cat2", "agnes_size": "800x1200", "agnes_prompt": "p" * 50},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = agnes_samples_main(["--list-items", "--lib", str(dummy_lib), "--json"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], "L01")
        self.assertEqual(data[1]["id"], "L02")
        for it in data:
            self.assertIn("id", it)
            self.assertIn("title", it)
            self.assertIn("category", it)
            self.assertIn("agnes_size", it)

    def test_cli_dry_run_json_output(self):
        from contextlib import redirect_stdout

        dummy_lib = self.tmp_path / "lib_dry.json"
        dummy_lib.write_text(json.dumps({
            "items": [
                {"id": "DRY01", "title": "演练预设1", "category": "cat1", "agnes_prompt": "prompt1" * 10},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        cli_out = self.tmp_path / "cli_json_dry_agnes"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = agnes_samples_main([
                "--dry-run",
                "--lib", str(dummy_lib),
                "-o", str(cli_out),
                "--json",
            ])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["ok"], 1)
        self.assertEqual(data["failed"], 0)
        self.assertTrue(data["dry_run"])
        self.assertEqual(len(data["results"]), 1)
        self.assertTrue((cli_out / "batch_report.json").is_file())

    def test_cli_quiet_mode_suppresses_stdout(self):
        from contextlib import redirect_stdout

        dummy_lib = self.tmp_path / "lib_quiet.json"
        dummy_lib.write_text(json.dumps({
            "items": [
                {"id": "Q01", "title": "静默预设1", "category": "cat1", "agnes_prompt": "prompt1" * 10},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        cli_out = self.tmp_path / "cli_quiet_dry_agnes"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = agnes_samples_main([
                "--dry-run",
                "--lib", str(dummy_lib),
                "-o", str(cli_out),
                "--quiet",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_run_batch_quiet_mode(self):
        from contextlib import redirect_stdout

        dummy_lib = self.tmp_path / "lib_batch_quiet.json"
        dummy_lib.write_text(json.dumps({
            "items": [
                {"id": "BQ01", "title": "批处理静默1", "category": "cat1", "agnes_prompt": "prompt1" * 10},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        def fake_gen(prompt, size, model, retries):
            return {"ok": True}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"x" * 100)

        out_dir = self.tmp_path / "batch_quiet_agnes_samples"
        buf = io.StringIO()
        with redirect_stdout(buf):
            results = agnes_samples_run_batch(
                lib_path=dummy_lib,
                out_dir=out_dir,
                generate_fn=fake_gen,
                save_image_fn=fake_save,
                quiet=True,
            )
        self.assertEqual(len(results), 1)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_cli_strict_mode_failure(self):
        dummy_lib = self.tmp_path / "lib_strict.json"
        dummy_lib.write_text(json.dumps({
            "items": [
                {"id": "FAIL01", "title": "严格失败1", "category": "cat1", "agnes_prompt": "prompt1" * 10},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        with patch("batch_agnes_samples.generate", None):
            cli_out = self.tmp_path / "cli_strict_fail_agnes"
            code = agnes_samples_main([
                "--lib", str(dummy_lib),
                "-o", str(cli_out),
                "--strict",
                "--quiet",
            ])
            self.assertEqual(code, 1)

    def test_cli_exception_json_output(self):
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("batch_agnes_samples.run_batch_agnes_samples", side_effect=RuntimeError("Disk I/O error")):
            with redirect_stdout(buf):
                code = agnes_samples_main(["--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "Disk I/O error")

    def test_cli_exception_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("batch_agnes_samples.run_batch_agnes_samples", side_effect=ValueError("Invalid preset item")):
            with redirect_stderr(buf):
                code = agnes_samples_main([])
            self.assertEqual(code, 1)
            self.assertIn("❌ GPT Image 样张批量生成失败: Invalid preset item", buf.getvalue())

    def test_cli_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("batch_agnes_samples.run_batch_agnes_samples", side_effect=RuntimeError("Silent failure")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = agnes_samples_main(["--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")

    def test_cli_list_items_exception_json_output(self):
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("batch_agnes_samples.list_items", side_effect=RuntimeError("Lib parse failure")):
            with redirect_stdout(buf):
                code = agnes_samples_main(["--list-items", "--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "Lib parse failure")

    def test_cli_list_items_exception_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("batch_agnes_samples.list_items", side_effect=RuntimeError("Lib parse failure")):
            with redirect_stderr(buf):
                code = agnes_samples_main(["--list-items"])
            self.assertEqual(code, 1)
            self.assertIn("❌ GPT Image 预设清单读取失败: Lib parse failure", buf.getvalue())

    def test_cli_list_items_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("batch_agnes_samples.list_items", side_effect=RuntimeError("Lib parse failure")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = agnes_samples_main(["--list-items", "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")


class TestInstallSkills71(unittest.TestCase):
    """测试 71 项生图 Skill 全局安装引擎 install_skills_71"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.cache_dir = self.tmp_path / "cache"
        self.out_root = self.tmp_path / "skills"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.out_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_sha256_bytes_and_file(self):
        data = b"hello agnes studio"
        expected = "9d3b137adb92d3d7b83662896ff2117032cb750fb34693a11f59abdfd4bee80d"
        self.assertEqual(skills_71_sha256_bytes(data), expected)

        test_file = self.tmp_path / "test.txt"
        test_file.write_bytes(data)
        self.assertEqual(skills_71_sha256_file(test_file), expected)

    def test_url_helpers(self):
        tar_url = skills_71_repo_tarball_url("owner/repo", "abcdef123456")
        self.assertEqual(tar_url, "https://codeload.github.com/owner/repo/tar.gz/abcdef123456")

        blob_url = "https://github.com/owner/repo/blob/main/skills/archive.zip"
        raw_url = skills_71_raw_url_from_blob(blob_url)
        self.assertEqual(raw_url, "https://raw.githubusercontent.com/owner/repo/main/skills/archive.zip")

    def test_load_manifest_and_errors(self):
        # 1. 成功解析自定义 manifest
        manifest_file = self.tmp_path / "test_manifest.json"
        manifest_file.write_text(json.dumps({
            "entries": [
                {
                    "id": "ST01",
                    "display_name": "星年四象重构",
                    "group": "照片抽象转译",
                    "install": {"target_directory_name": "starryear-abstract-quartet", "kind": "directory"}
                }
            ]
        }, ensure_ascii=False), encoding="utf-8")

        data = skills_71_load_manifest(manifest_file)
        self.assertIn("entries", data)
        self.assertEqual(len(data["entries"]), 1)
        self.assertEqual(data["entries"][0]["id"], "ST01")

        # 2. 文件不存在
        with self.assertRaises(FileNotFoundError):
            skills_71_load_manifest(self.tmp_path / "non_existent.json")

        # 3. 结构不合法
        invalid_file = self.tmp_path / "invalid.json"
        invalid_file.write_text(json.dumps({"wrong_key": []}), encoding="utf-8")
        with self.assertRaises(ValueError):
            skills_71_load_manifest(invalid_file)

    def test_filter_entries(self):
        entries = [
            {"id": "ST01", "display_name": "四象", "group": "照片抽象转译"},
            {"id": "ST03", "display_name": "奥德赛", "group": "照片转超现实叙事"},
            {"id": "S05", "display_name": "少色", "group": "照片转编辑海报"},
            {"id": "N01", "display_name": "工业夜景", "group": "光色与氛围改造"},
        ]

        # 1. 按 ID 字符串筛选
        f1 = skills_71_filter_entries(entries, ids="ST01,S05")
        self.assertEqual([e["id"] for e in f1], ["ST01", "S05"])

        # 2. 按 ID 列表筛选
        f2 = skills_71_filter_entries(entries, ids=["ST03", "N01"])
        self.assertEqual([e["id"] for e in f2], ["ST03", "N01"])

        # 3. 按分组筛选
        f3 = skills_71_filter_entries(entries, group="照片抽象转译")
        self.assertEqual([e["id"] for e in f3], ["ST01"])

        # 4. limit 限制
        f4 = skills_71_filter_entries(entries, limit=2)
        self.assertEqual(len(f4), 2)
        self.assertEqual([e["id"] for e in f4], ["ST01", "ST03"])

    def test_safe_extract_zip(self):
        import zipfile

        # 1. 正常 zip 提取
        valid_zip_path = self.tmp_path / "valid.zip"
        with zipfile.ZipFile(valid_zip_path, "w") as zf:
            zf.writestr("root_dir/SKILL.md", "# Skill Document\n")
            zf.writestr("root_dir/sub/file.txt", "content\n")

        dest = self.tmp_path / "extracted_valid_zip"
        top = skills_71_safe_extract_zip(zipfile.ZipFile(valid_zip_path), dest)
        self.assertTrue((dest / "root_dir" / "SKILL.md").is_file())
        self.assertEqual(top.name, "root_dir")

        # 2. 恶意路径穿越 zip 拦截
        bad_zip_path = self.tmp_path / "bad.zip"
        with zipfile.ZipFile(bad_zip_path, "w") as zf:
            zf.writestr("../evil.txt", "hack")

        dest_bad = self.tmp_path / "extracted_bad_zip"
        with self.assertRaises(RuntimeError):
            skills_71_safe_extract_zip(zipfile.ZipFile(bad_zip_path), dest_bad)

    def test_safe_extract_tar(self):
        import tarfile

        # 1. 正常 tar 提取
        valid_tar_path = self.tmp_path / "valid.tar"
        with tarfile.open(valid_tar_path, "w") as tf:
            info1 = tarfile.TarInfo(name="repo_top/SKILL.md")
            content1 = b"# Tar Skill\n"
            info1.size = len(content1)
            tf.addfile(info1, io.BytesIO(content1))

        dest = self.tmp_path / "extracted_valid_tar"
        with tarfile.open(valid_tar_path) as tf:
            top = skills_71_safe_extract_tar(tf, dest)
        self.assertTrue((dest / "repo_top" / "SKILL.md").is_file())
        self.assertEqual(top.name, "repo_top")

        # 2. 恶意路径穿越 tar 拦截
        bad_tar_path = self.tmp_path / "bad.tar"
        with tarfile.open(bad_tar_path, "w") as tf:
            info_bad = tarfile.TarInfo(name="../escape.txt")
            bad_content = b"escape"
            info_bad.size = len(bad_content)
            tf.addfile(info_bad, io.BytesIO(bad_content))

        dest_bad = self.tmp_path / "extracted_bad_tar"
        with tarfile.open(bad_tar_path) as tf:
            with self.assertRaises(RuntimeError):
                skills_71_safe_extract_tar(tf, dest_bad)

    def test_verify_skill_md(self):
        skill_dir = self.tmp_path / "test_skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        md_file = skill_dir / "SKILL.md"
        content = b"# Verified Skill\n"
        md_file.write_bytes(content)
        expected_hash = skills_71_sha256_bytes(content)

        # 1. 匹配成功
        ok, res = skills_71_verify_skill_md(skill_dir, "SKILL.md", expected_hash)
        self.assertTrue(ok)
        self.assertEqual(res, expected_hash)

        # 2. 哈希不匹配
        ok, res = skills_71_verify_skill_md(skill_dir, "SKILL.md", "wrong_hash")
        self.assertFalse(ok)
        self.assertIn("sha256 mismatch", res)

        # 3. 文件不存在
        ok, res = skills_71_verify_skill_md(skill_dir, "MISSING.md", expected_hash)
        self.assertFalse(ok)
        self.assertIn("missing MISSING.md", res)

    def test_copy_skill_tree_and_backup(self):
        src = self.tmp_path / "src_skill"
        src.mkdir()
        (src / "file.txt").write_text("v1", encoding="utf-8")

        target = self.tmp_path / "installed_skill"
        skills_71_copy_skill_tree(src, target)
        self.assertTrue((target / "file.txt").is_file())
        self.assertEqual((target / "file.txt").read_text(encoding="utf-8"), "v1")

        # 再次复制应生成备份
        (src / "file.txt").write_text("v2", encoding="utf-8")
        skills_71_copy_skill_tree(src, target)
        self.assertEqual((target / "file.txt").read_text(encoding="utf-8"), "v2")
        backups = list(self.tmp_path.glob("installed_skill.bak.*"))
        self.assertGreaterEqual(len(backups), 1)

    def test_write_meta_and_license_notes(self):
        target = self.tmp_path / "meta_skill"
        target.mkdir()
        entry = {
            "id": "ST09",
            "display_name": "星年影像成标",
            "declared_skill_name": "s-008-starryear-visual-mark",
            "repository": "owner/repo",
            "group": "照片转编辑海报",
        }
        skills_71_write_meta(target, entry, "commit123")
        meta_file = target / "INSTALL_META.json"
        self.assertTrue(meta_file.is_file())
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        self.assertEqual(meta["entry_id"], "ST09")
        self.assertEqual(meta["verified_ref"], "commit123")
        self.assertIn("Starryear Personal", meta["license_note"])

        license_file = target / "LICENSE_NOTE.md"
        self.assertTrue(license_file.is_file())
        self.assertIn("ST09", license_file.read_text(encoding="utf-8"))

    def test_install_one_dry_run_and_errors(self):
        # 1. dry-run
        entry = {
            "id": "ST03",
            "display_name": "星年奥德赛",
            "install": {
                "target_directory_name": "odyssey-photo-diptych",
                "kind": "zip",
            },
        }
        res = skills_71_install_one(entry, out_root=self.out_root, cache_dir=self.cache_dir, dry_run=True)
        self.assertEqual(res["status"], "dry_run")
        self.assertEqual(res["id"], "ST03")

        # 2. invalid entry dict
        err1 = skills_71_install_one("not a dict")
        self.assertEqual(err1["status"], "error")

        # 3. missing install
        err2 = skills_71_install_one({"id": "X01"})
        self.assertEqual(err2["status"], "error")

    def test_install_one_with_mock_fetch_zip(self):
        skill_content = b"# Mock Zip Skill\n"
        skill_hash = skills_71_sha256_bytes(skill_content)

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("my-skill-pack/SKILL.md", skill_content)
        zip_bytes = zip_buf.getvalue()
        zip_hash = skills_71_sha256_bytes(zip_bytes)

        entry = {
            "id": "TEST_ZIP",
            "display_name": "测试ZIP技能",
            "repository": "test/repo",
            "verified_ref": "v1.0.0",
            "source_url": "https://github.com/test/repo/blob/main/skill.zip",
            "install": {
                "target_directory_name": "test-zip-skill",
                "kind": "zip",
                "zip_path": "skill.zip",
                "zip_sha256": zip_hash,
                "source_directory": "my-skill-pack",
                "skill_md_path": "SKILL.md",
                "skill_md_sha256": skill_hash,
            }
        }

        def mock_fetch(url, dest):
            dest.write_bytes(zip_bytes)

        res = skills_71_install_one(
            entry,
            out_root=self.out_root,
            cache_dir=self.cache_dir,
            dry_run=False,
            fetch_fn=mock_fetch,
        )
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["id"], "TEST_ZIP")
        target_dir = self.out_root / "test-zip-skill"
        self.assertTrue((target_dir / "SKILL.md").is_file())
        self.assertTrue((target_dir / "INSTALL_META.json").is_file())

    def test_install_one_with_mock_fetch_directory_tarball(self):
        skill_content = b"# Mock Tarball Skill\n"
        skill_hash = skills_71_sha256_bytes(skill_content)

        tar_buf = io.BytesIO()
        with tarfile.open(fileobj=tar_buf, mode="w") as tf:
            info = tarfile.TarInfo(name="repo_root/sub/SKILL.md")
            info.size = len(skill_content)
            tf.addfile(info, io.BytesIO(skill_content))
        tar_bytes = tar_buf.getvalue()

        entry = {
            "id": "TEST_DIR",
            "display_name": "测试目录技能",
            "repository": "test/tar_repo",
            "verified_ref": "v2.0.0",
            "install": {
                "target_directory_name": "test-tar-skill",
                "kind": "directory",
                "source_directory": "sub",
                "skill_md_path": "SKILL.md",
                "skill_md_sha256": skill_hash,
            }
        }

        def mock_fetch(url, dest):
            dest.write_bytes(tar_bytes)

        res = skills_71_install_one(
            entry,
            out_root=self.out_root,
            cache_dir=self.cache_dir,
            dry_run=False,
            fetch_fn=mock_fetch,
        )
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["id"], "TEST_DIR")
        target_dir = self.out_root / "test-tar-skill"
        self.assertTrue((target_dir / "SKILL.md").is_file())
        self.assertTrue((target_dir / "INSTALL_META.json").is_file())

    def test_run_install_and_cli(self):
        manifest_file = self.tmp_path / "skills-manifest.json"
        manifest_file.write_text(json.dumps({
            "entries": [
                {
                    "id": "ST01",
                    "display_name": "技能一",
                    "group": "照片抽象转译",
                    "install": {"target_directory_name": "skill-01", "kind": "zip"}
                },
                {
                    "id": "ST02",
                    "display_name": "技能二",
                    "group": "光色与氛围改造",
                    "install": {"target_directory_name": "skill-02", "kind": "directory"}
                }
            ]
        }, ensure_ascii=False), encoding="utf-8")

        # 1. run_install dry_run
        report = skills_71_run_install(
            manifest_path=manifest_file,
            cache_dir=self.cache_dir,
            out_root=self.out_root,
            dry_run=True,
            workers=2,
        )
        self.assertEqual(report["total"], 2)
        self.assertEqual(report["dry_run"], 2)
        self.assertEqual(report["error"], 0)
        self.assertTrue((self.cache_dir / "install_report.json").is_file())

        # 2. CLI --list
        ret_list = skills_71_main(["--manifest", str(manifest_file), "--list"])
        self.assertEqual(ret_list, 0)

        # 3. CLI --dry-run with --ids
        ret_dry = skills_71_main([
            "--manifest", str(manifest_file),
            "--cache-dir", str(self.cache_dir),
            "--out-dir", str(self.out_root),
            "--ids", "ST01",
            "--dry-run",
            "-w", "1"
        ])
        self.assertEqual(ret_dry, 0)

        # 4. CLI 不存在 manifest 报错
        ret_err = skills_71_main(["--manifest", str(self.tmp_path / "not_found.json")])
        self.assertEqual(ret_err, 1)

    def test_build_arg_parser(self):
        parser = skills_71_build_arg_parser()
        args = parser.parse_args(["-m", "custom.json", "--json", "-q", "--strict", "--dry-run", "-w", "4"])
        self.assertEqual(args.manifest, "custom.json")
        self.assertTrue(args.json)
        self.assertTrue(args.quiet)
        self.assertTrue(args.strict)
        self.assertTrue(args.dry_run)
        self.assertEqual(args.workers, 4)

    def test_list_skills_helper(self):
        manifest_file = self.tmp_path / "skills-manifest.json"
        manifest_file.write_text(json.dumps({
            "entries": [
                {
                    "id": "ST01",
                    "display_name": "技能一",
                    "group": "照片抽象转译",
                    "install": {"target_directory_name": "skill-01", "kind": "zip"},
                    "repository": "test/repo-1",
                    "verified_ref": "v1.0.0"
                },
                {
                    "id": "ST02",
                    "display_name": "技能二",
                    "group": "光色与氛围改造",
                    "install": {"target_directory_name": "skill-02", "kind": "directory"},
                    "repository": "test/repo-2",
                    "verified_ref": "v2.0.0"
                }
            ]
        }, ensure_ascii=False), encoding="utf-8")

        all_skills = skills_71_list_skills(manifest_path=manifest_file)
        self.assertEqual(len(all_skills), 2)
        self.assertEqual(all_skills[0]["id"], "ST01")
        self.assertEqual(all_skills[0]["display_name"], "技能一")
        self.assertEqual(all_skills[0]["group"], "照片抽象转译")
        self.assertEqual(all_skills[0]["target_directory_name"], "skill-01")
        self.assertEqual(all_skills[0]["repository"], "test/repo-1")
        self.assertEqual(all_skills[0]["verified_ref"], "v1.0.0")

        filtered = skills_71_list_skills(manifest_path=manifest_file, group="光色与氛围改造")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["id"], "ST02")

    def test_cli_list_json(self):
        manifest_file = self.tmp_path / "skills-manifest.json"
        manifest_file.write_text(json.dumps({
            "entries": [
                {
                    "id": "ST01",
                    "display_name": "技能一",
                    "group": "照片抽象转译",
                    "install": {"target_directory_name": "skill-01", "kind": "zip"}
                }
            ]
        }, ensure_ascii=False), encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = skills_71_main(["--manifest", str(manifest_file), "--list", "--json"])
        self.assertEqual(ret, 0)
        items = json.loads(buf.getvalue())
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], "ST01")
        self.assertEqual(items[0]["display_name"], "技能一")
        self.assertEqual(items[0]["target_directory_name"], "skill-01")

    def test_cli_dry_run_json_output(self):
        manifest_file = self.tmp_path / "skills-manifest.json"
        manifest_file.write_text(json.dumps({
            "entries": [
                {
                    "id": "ST01",
                    "display_name": "技能一",
                    "group": "照片抽象转译",
                    "install": {"target_directory_name": "skill-01", "kind": "zip"}
                }
            ]
        }, ensure_ascii=False), encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = skills_71_main([
                "--manifest", str(manifest_file),
                "--cache-dir", str(self.cache_dir),
                "--out-dir", str(self.out_root),
                "--dry-run",
                "--json",
                "-w", "1"
            ])
        self.assertEqual(ret, 0)
        report = json.loads(buf.getvalue())
        self.assertEqual(report["total"], 1)
        self.assertEqual(report["dry_run"], 1)
        self.assertEqual(report["ok"], 0)
        self.assertEqual(report["error"], 0)
        self.assertIn("results", report)
        self.assertEqual(len(report["results"]), 1)
        self.assertEqual(report["results"][0]["id"], "ST01")

    def test_cli_quiet_mode_suppresses_stdout(self):
        manifest_file = self.tmp_path / "skills-manifest.json"
        manifest_file.write_text(json.dumps({
            "entries": [
                {
                    "id": "ST01",
                    "display_name": "技能一",
                    "group": "照片抽象转译",
                    "install": {"target_directory_name": "skill-01", "kind": "zip"}
                }
            ]
        }, ensure_ascii=False), encoding="utf-8")

        # 1. --list -q 静默
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = skills_71_main(["--manifest", str(manifest_file), "--list", "-q"])
        self.assertEqual(ret, 0)
        self.assertEqual(buf.getvalue(), "")

        # 2. --dry-run -q 静默
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            ret = skills_71_main([
                "--manifest", str(manifest_file),
                "--cache-dir", str(self.cache_dir),
                "--out-dir", str(self.out_root),
                "--dry-run",
                "-q",
                "-w", "1"
            ])
        self.assertEqual(ret, 0)
        self.assertEqual(buf2.getvalue(), "")

    def test_cli_strict_json_error(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = skills_71_main([
                "--manifest", str(self.tmp_path / "not_found.json"),
                "--strict",
                "--json"
            ])
        self.assertEqual(ret, 1)
        payload = json.loads(buf.getvalue())
        self.assertFalse(payload["ok"])
        self.assertIn("error", payload)

    def test_cli_load_manifest_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with redirect_stderr(buf):
            ret = skills_71_main([
                "--manifest", str(self.tmp_path / "not_found.json"),
            ])
        self.assertEqual(ret, 1)
        self.assertIn("❌ 71 项生图 Skill 清单加载失败:", buf.getvalue())

    def test_cli_load_manifest_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with redirect_stderr(err_buf), redirect_stdout(out_buf):
            ret = skills_71_main([
                "--manifest", str(self.tmp_path / "not_found.json"),
                "--quiet",
            ])
        self.assertEqual(ret, 1)
        self.assertEqual(err_buf.getvalue(), "")
        self.assertEqual(out_buf.getvalue(), "")

    def test_cli_list_exception_json_output(self):
        manifest_file = self.tmp_path / "valid_manifest.json"
        manifest_file.write_text(json.dumps({"entries": [{"id": "ST01"}]}), encoding="utf-8")
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("install_skills_71.list_skills", side_effect=RuntimeError("List parse crash")):
            with redirect_stdout(buf):
                ret = skills_71_main([
                    "--manifest", str(manifest_file),
                    "--list",
                    "--json",
                ])
            self.assertEqual(ret, 1)
            payload = json.loads(buf.getvalue())
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"], "List parse crash")

    def test_cli_list_exception_stderr_output(self):
        manifest_file = self.tmp_path / "valid_manifest.json"
        manifest_file.write_text(json.dumps({"entries": [{"id": "ST01"}]}), encoding="utf-8")
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("install_skills_71.list_skills", side_effect=RuntimeError("List parse crash")):
            with redirect_stderr(buf):
                ret = skills_71_main([
                    "--manifest", str(manifest_file),
                    "--list",
                ])
            self.assertEqual(ret, 1)
            self.assertIn("❌ 71 项生图 Skill 清单读取失败: List parse crash", buf.getvalue())

    def test_cli_list_exception_quiet_mode(self):
        manifest_file = self.tmp_path / "valid_manifest.json"
        manifest_file.write_text(json.dumps({"entries": [{"id": "ST01"}]}), encoding="utf-8")
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("install_skills_71.list_skills", side_effect=RuntimeError("List parse crash")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                ret = skills_71_main([
                    "--manifest", str(manifest_file),
                    "--list",
                    "--quiet",
                ])
            self.assertEqual(ret, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")

    def test_cli_install_exception_json_output(self):
        manifest_file = self.tmp_path / "valid_manifest.json"
        manifest_file.write_text(json.dumps({"entries": [{"id": "ST01"}]}), encoding="utf-8")
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("install_skills_71.run_install", side_effect=PermissionError("Permission denied")):
            with redirect_stdout(buf):
                ret = skills_71_main([
                    "--manifest", str(manifest_file),
                    "--json",
                ])
            self.assertEqual(ret, 1)
            payload = json.loads(buf.getvalue())
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"], "Permission denied")

    def test_cli_install_exception_stderr_output(self):
        manifest_file = self.tmp_path / "valid_manifest.json"
        manifest_file.write_text(json.dumps({"entries": [{"id": "ST01"}]}), encoding="utf-8")
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("install_skills_71.run_install", side_effect=PermissionError("Permission denied")):
            with redirect_stderr(buf):
                ret = skills_71_main([
                    "--manifest", str(manifest_file),
                ])
            self.assertEqual(ret, 1)
            self.assertIn("❌ 71 项生图 Skill 安装失败: Permission denied", buf.getvalue())

    def test_cli_install_exception_quiet_mode(self):
        manifest_file = self.tmp_path / "valid_manifest.json"
        manifest_file.write_text(json.dumps({"entries": [{"id": "ST01"}]}), encoding="utf-8")
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("install_skills_71.run_install", side_effect=RuntimeError("Silent failure")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                ret = skills_71_main([
                    "--manifest", str(manifest_file),
                    "--quiet",
                ])
            self.assertEqual(ret, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")


class TestGenAgnesSamples(unittest.TestCase):
    """测试 GPT Image 转 Agnes 单条与批量生成引擎 gen_agnes_samples"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_slugify(self):
        self.assertEqual(gen_agnes_slugify("室内棚拍-烟雾缭绕(Vol:1)"), "室内棚拍-烟雾缭绕-Vol-1")
        self.assertEqual(gen_agnes_slugify("test_item_title! 123"), "test_item_title-123")
        self.assertEqual(gen_agnes_slugify(""), "item")
        self.assertEqual(gen_agnes_slugify(None), "item")
        self.assertEqual(gen_agnes_slugify(999), "item")
        self.assertEqual(gen_agnes_slugify("x" * 50, max_len=20), "x" * 20)

    def test_classify_generation_error(self):
        self.assertEqual(gen_agnes_classify_error("HTTP 502: Bad Gateway"), "gateway_502")
        self.assertEqual(gen_agnes_classify_error("HTTP 401: Unauthorized"), "auth")
        self.assertEqual(gen_agnes_classify_error("upstream timed out"), "timeout")
        self.assertEqual(gen_agnes_classify_error("invalid prompt"), "generation_error")

    def test_load_prompts_library_default(self):
        items = gen_agnes_load_lib()
        self.assertGreaterEqual(len(items), 40)
        self.assertEqual(items[0]["id"], "1001")
        self.assertTrue(all("id" in it for it in items))

    def test_load_prompts_library_custom_and_errors(self):
        custom_lib = self.tmp_path / "custom_lib.json"
        custom_lib.write_text(json.dumps({
            "items": [
                {"id": "G01", "title": "自定义样张", "category": "test", "agnes_prompt": "Test prompt text."}
            ]
        }, ensure_ascii=False), encoding="utf-8")

        loaded = gen_agnes_load_lib(custom_lib)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["id"], "G01")

        with self.assertRaises(FileNotFoundError):
            gen_agnes_load_lib(self.tmp_path / "not_found.json")

        invalid_lib = self.tmp_path / "invalid.json"
        invalid_lib.write_text(json.dumps({"wrong": []}), encoding="utf-8")
        with self.assertRaises(ValueError):
            gen_agnes_load_lib(invalid_lib)

    def test_build_item_prompt(self):
        # 1. 优先 agnes_prompt
        item1 = {"agnes_prompt": "Agnes prompt value", "gpt_image_prompt": "Fallback prompt"}
        self.assertEqual(gen_agnes_build_prompt(item1), "Agnes prompt value")

        # 2. 回退 gpt_image_prompt
        item2 = {"gpt_image_prompt": "Fallback prompt only"}
        self.assertEqual(gen_agnes_build_prompt(item2), "Fallback prompt only")

        # 3. 非字典
        self.assertEqual(gen_agnes_build_prompt("not a dict"), "")

    def test_filter_items(self):
        items = [
            {"id": "1001", "title": "人像1", "category": "portrait"},
            {"id": "1002", "title": "人像2", "category": "portrait"},
            {"id": "2001", "title": "商业1", "category": "commercial"},
            {"id": "3002", "title": "海报1", "category": "poster"},
        ]

        # 字符串筛选
        f1 = gen_agnes_filter_items(items, ids="1001,2001")
        self.assertEqual([x["id"] for x in f1], ["1001", "2001"])

        # 列表筛选
        f2 = gen_agnes_filter_items(items, ids=["1002", "3002"])
        self.assertEqual([x["id"] for x in f2], ["1002", "3002"])

        # 分类筛选
        f3 = gen_agnes_filter_items(items, category="commercial")
        self.assertEqual([x["id"] for x in f3], ["2001"])

        # 限制数量
        f4 = gen_agnes_filter_items(items, limit=2)
        self.assertEqual(len(f4), 2)
        self.assertEqual([x["id"] for x in f4], ["1001", "1002"])

    def test_run_one_validation_and_errors(self):
        # 非 dict
        r1 = gen_agnes_run_one("not a dict", out_dir=self.tmp_path)
        self.assertFalse(r1["ok"])
        self.assertIn("expected dict", r1["error"])

        # 空 ID
        r2 = gen_agnes_run_one({"title": "无 ID"}, out_dir=self.tmp_path)
        self.assertFalse(r2["ok"])
        self.assertIn("Item ID cannot be empty", r2["error"])

        # 空 prompt
        r3 = gen_agnes_run_one({"id": "1001", "title": "空 Prompt"}, out_dir=self.tmp_path)
        self.assertFalse(r3["ok"])
        self.assertIn("prompt is empty", r3["error"])

    def test_run_one_dry_run(self):
        item = {
            "id": "1001",
            "title": "测试人像",
            "agnes_prompt": "A beautiful cinematic portrait of a dancer in golden hour.",
            "agnes_size": "1088x1456",
        }
        res = gen_agnes_run_one(item, out_dir=self.tmp_path, dry_run=True)
        self.assertTrue(res["ok"])
        self.assertTrue(res.get("dry_run"))
        self.assertEqual(res["id"], "1001")
        self.assertIn("1001_测试人像.png", res["file"])

    def test_run_one_skip_existing(self):
        item = {
            "id": "1001",
            "title": "测试跳过",
            "agnes_prompt": "A beautiful cinematic portrait.",
        }
        # 创建大于 20KB 的占位文件
        target_file = self.tmp_path / "1001_测试跳过.png"
        target_file.write_bytes(b"x" * 25_000)

        res = gen_agnes_run_one(item, out_dir=self.tmp_path, force=False)
        self.assertTrue(res["ok"])
        self.assertTrue(res.get("skipped"))
        self.assertEqual(res["kb"], 24)

    def test_run_one_with_mock_generate(self):
        item = {
            "id": "1001",
            "title": "测试生成",
            "agnes_prompt": "A stunning visual piece.",
        }

        def mock_generate(prompt, **kwargs):
            return {"ok": True, "cost_s": 1.25, "via": "mock_gateway", "model": "agnes-mock"}

        def mock_save_image(res, path):
            Path(path).write_bytes(b"MOCK_PNG_DATA" * 2000)

        res = gen_agnes_run_one(
            item,
            out_dir=self.tmp_path,
            generate_fn=mock_generate,
            save_image_fn=mock_save_image,
        )
        self.assertTrue(res["ok"])
        self.assertEqual(res["id"], "1001")
        self.assertEqual(res["via"], "mock_gateway")
        self.assertTrue((self.tmp_path / "1001_测试生成.png").is_file())

    def test_run_one_generate_error_handling(self):
        item = {
            "id": "1001",
            "title": "测试错误",
            "agnes_prompt": "Prompt for error check.",
        }

        # 1. generate 返回 ok=False
        def mock_gen_fail(prompt, **kwargs):
            return {"ok": False, "error": "Quota limit reached"}

        r1 = gen_agnes_run_one(item, out_dir=self.tmp_path, generate_fn=mock_gen_fail)
        self.assertFalse(r1["ok"])
        self.assertIn("Quota limit reached", r1["error"])
        self.assertEqual(r1.get("error_class"), "generation_error")

        # 2. generate 抛出异常
        def mock_gen_raise(prompt, **kwargs):
            raise ConnectionResetError("Connection reset by peer")

        r2 = gen_agnes_run_one(item, out_dir=self.tmp_path, generate_fn=mock_gen_raise)
        self.assertFalse(r2["ok"])
        self.assertIn("Connection reset by peer", r2["error"])
        self.assertEqual(r2.get("error_class"), "generation_error")

        # 3. 网关 502 错误分类
        def mock_502(prompt, **kwargs):
            return {"ok": False, "error": "HTTP 502: Bad Gateway"}

        r3 = gen_agnes_run_one(item, out_dir=self.tmp_path, generate_fn=mock_502)
        self.assertFalse(r3["ok"])
        self.assertEqual(r3.get("error_class"), "gateway_502")

        # 4. 超时错误分类
        def mock_timeout(prompt, **kwargs):
            raise TimeoutError("upstream request timed out")

        r4 = gen_agnes_run_one(item, out_dir=self.tmp_path, generate_fn=mock_timeout)
        self.assertFalse(r4["ok"])
        self.assertEqual(r4.get("error_class"), "timeout")

    def test_run_batch_gen_execution(self):
        items = [
            {"id": "1001", "title": "批量1", "agnes_prompt": "Prompt 1"},
            {"id": "1002", "title": "批量2", "agnes_prompt": "Prompt 2"},
        ]

        def mock_gen(prompt, **kwargs):
            return {"ok": True, "cost_s": 0.5, "via": "mock"}

        def mock_save(res, path):
            Path(path).write_bytes(b"OK" * 100)

        report = gen_agnes_run_batch(
            items_to_run=items,
            out_dir=self.tmp_path,
            workers=2,
            generate_fn=mock_gen,
            save_image_fn=mock_save,
        )
        self.assertEqual(report["total"], 2)
        self.assertEqual(report["ok"], 2)
        self.assertTrue((self.tmp_path / "_batch_report.json").is_file())

    def test_list_items(self):
        items = gen_agnes_list_items()
        self.assertGreaterEqual(len(items), 40)
        self.assertIn("id", items[0])
        self.assertIn("title", items[0])
        self.assertIn("category", items[0])

    def test_cli_positional_and_options(self):
        custom_lib = self.tmp_path / "cli_lib.json"
        custom_lib.write_text(json.dumps({
            "items": [
                {"id": "1001", "title": "样张1", "category": "portrait", "agnes_prompt": "Prompt 1001"},
                {"id": "1002", "title": "样张2", "category": "commercial", "agnes_prompt": "Prompt 1002"},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        # 1. --list-items
        ret_list = gen_agnes_main(["--lib", str(custom_lib), "--list-items"])
        self.assertEqual(ret_list, 0)

        # 2. positional IDs with --dry-run
        ret_pos = gen_agnes_main([
            "1001",
            "--lib", str(custom_lib),
            "--out", str(self.tmp_path / "out_pos"),
            "--dry-run",
            "-w", "1",
        ])
        self.assertEqual(ret_pos, 0)
        self.assertTrue((self.tmp_path / "out_pos" / "_batch_report.json").is_file())

        # 3. --ids and --category with --dry-run
        ret_flags = gen_agnes_main([
            "--ids", "1002",
            "--category", "commercial",
            "--lib", str(custom_lib),
            "--out", str(self.tmp_path / "out_flags"),
            "--dry-run",
        ])
        self.assertEqual(ret_flags, 0)
        self.assertTrue((self.tmp_path / "out_flags" / "_batch_report.json").is_file())

    def test_cli_error_exit_code(self):
        # 不存在的 lib 文件导致报错退出
        ret = gen_agnes_main(["--lib", str(self.tmp_path / "non_existent.json")])
        self.assertEqual(ret, 1)

    def test_build_arg_parser(self):
        parser = gen_agnes_build_arg_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        actions = {dest: a for a in parser._actions for dest in a.dest.split()}
        self.assertIn("list_items", actions)
        self.assertIn("ids", actions)
        self.assertIn("category", actions)
        self.assertIn("limit", actions)
        self.assertIn("out", actions)
        self.assertIn("workers", actions)
        self.assertIn("lib", actions)
        self.assertIn("force", actions)
        self.assertIn("dry_run", actions)
        self.assertIn("json", actions)
        self.assertIn("quiet", actions)
        self.assertIn("strict", actions)

    def test_cli_list_items_json(self):
        from contextlib import redirect_stdout

        dummy_lib = self.tmp_path / "lib_test.json"
        dummy_lib.write_text(json.dumps({
            "items": [
                {"id": "G01", "title": "测试样张1", "category": "cat1", "agnes_size": "1024x1024", "agnes_prompt": "p" * 50},
                {"id": "G02", "title": "测试样张2", "category": "cat2", "agnes_size": "800x1200", "agnes_prompt": "p" * 50},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = gen_agnes_main(["--list-items", "--lib", str(dummy_lib), "--json"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue().strip())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], "G01")
        self.assertEqual(data[1]["id"], "G02")
        for it in data:
            self.assertIn("id", it)
            self.assertIn("title", it)
            self.assertIn("category", it)
            self.assertIn("agnes_size", it)

    def test_cli_dry_run_json_output(self):
        from contextlib import redirect_stdout

        dummy_lib = self.tmp_path / "lib_dry.json"
        dummy_lib.write_text(json.dumps({
            "items": [
                {"id": "DRY01", "title": "演练样张1", "category": "cat1", "agnes_prompt": "prompt1" * 10},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        cli_out = self.tmp_path / "cli_json_dry_gen_agnes"
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = gen_agnes_main([
                "--dry-run",
                "--lib", str(dummy_lib),
                "-o", str(cli_out),
                "--json",
                "-w", "1",
            ])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue().strip())
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["ok"], 1)
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 1)
        self.assertTrue(data["results"][0]["dry_run"])
        self.assertTrue((cli_out / "_batch_report.json").is_file())

    def test_cli_quiet_mode_suppresses_stdout(self):
        from contextlib import redirect_stdout

        dummy_lib = self.tmp_path / "lib_quiet.json"
        dummy_lib.write_text(json.dumps({
            "items": [
                {"id": "Q01", "title": "静默样张1", "category": "cat1", "agnes_prompt": "prompt1" * 10},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        # 1. --list-items -q 静默
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = gen_agnes_main(["--list-items", "--lib", str(dummy_lib), "--quiet"])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "")

        # 2. --dry-run -q 静默
        cli_out = self.tmp_path / "cli_quiet_dry_gen_agnes"
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            code = gen_agnes_main([
                "--dry-run",
                "--lib", str(dummy_lib),
                "-o", str(cli_out),
                "--quiet",
                "-w", "1",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(buf2.getvalue().strip(), "")

    def test_run_batch_quiet_mode(self):
        from contextlib import redirect_stdout

        dummy_lib = self.tmp_path / "lib_batch_quiet.json"
        dummy_lib.write_text(json.dumps({
            "items": [
                {"id": "BQ01", "title": "批处理静默1", "category": "cat1", "agnes_prompt": "prompt1" * 10},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        def fake_gen(prompt, size, model, retries):
            return {"ok": True}

        def fake_save(res, out_file):
            Path(out_file).write_bytes(b"x" * 100)

        out_dir = self.tmp_path / "batch_quiet_gen_agnes"
        buf = io.StringIO()
        with redirect_stdout(buf):
            report = gen_agnes_run_batch(
                lib_path=dummy_lib,
                out_dir=out_dir,
                generate_fn=fake_gen,
                save_image_fn=fake_save,
                quiet=True,
                workers=1,
            )
        self.assertEqual(report["total"], 1)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_cli_strict_mode_failure(self):
        dummy_lib = self.tmp_path / "lib_strict.json"
        dummy_lib.write_text(json.dumps({
            "items": [
                {"id": "FAIL01", "title": "严格失败1", "category": "cat1", "agnes_prompt": "prompt1" * 10},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        with patch("gen_agnes_samples.generate", None):
            cli_out = self.tmp_path / "cli_strict_fail_gen_agnes"
            code = gen_agnes_main([
                "--lib", str(dummy_lib),
                "-o", str(cli_out),
                "--strict",
                "--quiet",
                "-w", "1",
            ])
            self.assertEqual(code, 1)

    def test_cli_exception_json_error(self):
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = gen_agnes_main([
                "--lib", str(self.tmp_path / "non_existent_file.json"),
                "--json",
            ])
        self.assertEqual(code, 1)
        data = json.loads(buf.getvalue().strip())
        self.assertFalse(data.get("ok"))
        self.assertIn("error", data)
        self.assertIn("non_existent_file.json", data["error"])

    def test_cli_exception_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("gen_agnes_samples.run_batch_gen", side_effect=ValueError("Invalid preset item")):
            with redirect_stderr(buf):
                code = gen_agnes_main([])
            self.assertEqual(code, 1)
            self.assertIn("❌ GPT Image 样张批量生成失败: Invalid preset item", buf.getvalue())

    def test_cli_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("gen_agnes_samples.run_batch_gen", side_effect=RuntimeError("Silent failure")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = gen_agnes_main(["--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")

    def test_cli_list_items_exception_json_output(self):
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with patch("gen_agnes_samples.list_items", side_effect=RuntimeError("Lib parse failure")):
            with redirect_stdout(buf):
                code = gen_agnes_main(["--list-items", "--json"])
            self.assertEqual(code, 1)
            data = json.loads(buf.getvalue())
            self.assertFalse(data["ok"])
            self.assertEqual(data["error"], "Lib parse failure")

    def test_cli_list_items_exception_stderr_output(self):
        from contextlib import redirect_stderr
        buf = io.StringIO()
        with patch("gen_agnes_samples.list_items", side_effect=RuntimeError("Lib parse failure")):
            with redirect_stderr(buf):
                code = gen_agnes_main(["--list-items"])
            self.assertEqual(code, 1)
            self.assertIn("❌ GPT Image 预设清单读取失败: Lib parse failure", buf.getvalue())

    def test_cli_list_items_exception_quiet_mode(self):
        from contextlib import redirect_stderr, redirect_stdout
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("gen_agnes_samples.list_items", side_effect=RuntimeError("Lib parse failure")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                code = gen_agnes_main(["--list-items", "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")
            self.assertEqual(out_buf.getvalue(), "")


class TestGeminiIntegrationSuite(unittest.TestCase):
    """测试 Gemini 智能引擎与全链路排印管线自动化验证套件 test_gemini_integration"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_parse_steps(self):
        self.assertEqual(gemini_parse_steps(None), [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(gemini_parse_steps(""), [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(gemini_parse_steps("1,3,5"), [1, 3, 5])
        self.assertEqual(gemini_parse_steps("7, 2, 1, 9, abc"), [7, 2, 1])

    def test_build_arg_parser(self):
        parser = gemini_build_arg_parser()
        args = parser.parse_args([
            "--steps", "1,2,5",
            "--mock",
            "--skip-network",
            "--dry-run",
            "--out-dir", str(self.tmp_path),
            "--json", "report.json",
            "--quiet",
        ])
        self.assertEqual(args.steps, "1,2,5")
        self.assertTrue(args.mock)
        self.assertTrue(args.skip_network)
        self.assertTrue(args.dry_run)
        self.assertEqual(args.out_dir, str(self.tmp_path))
        self.assertEqual(args.json, "report.json")
        self.assertTrue(args.quiet)

    def test_step_1_chrome(self):
        # 1. 成功探测
        r_ok = gemini_step_1_chrome(resolve_fn=lambda: sys.executable)
        self.assertTrue(r_ok["ok"])
        self.assertEqual(r_ok["path"], sys.executable)

        # 2. 失败路径不存在
        r_not_found = gemini_step_1_chrome(chrome_path_override=str(self.tmp_path / "no_chrome"))
        self.assertFalse(r_not_found["ok"])
        self.assertIn("不存在", r_not_found["error"])

        # 3. 异常处理
        def faulty_resolve():
            raise RuntimeError("Chromium resolution failure")
        r_err = gemini_step_1_chrome(resolve_fn=faulty_resolve)
        self.assertFalse(r_err["ok"])
        self.assertIn("Chromium resolution failure", r_err["error"])

    def test_step_2_gateway(self):
        # 1. Mock 模式
        r_mock = gemini_step_2_gateway(mock=True, load_creds_fn=lambda: ("http://mock-base", "mock-key-12345", "mock-model"))
        self.assertTrue(r_mock["ok"])
        self.assertTrue(r_mock["mock"])
        self.assertEqual(r_mock["chat_model"], "mock-model")

        # 2. 正常调用
        r_ok = gemini_step_2_gateway(
            mock=False,
            call_agnes_fn=lambda msgs, max_tokens: {"ok": True, "cost_s": 0.05},
            load_creds_fn=lambda: ("http://base", "key", "model"),
        )
        self.assertTrue(r_ok["ok"])
        self.assertEqual(r_ok["cost_s"], 0.05)

        # 3. 调用失败
        r_fail = gemini_step_2_gateway(
            mock=False,
            call_agnes_fn=lambda msgs, max_tokens: {"ok": False, "error": "Gateway timeout"},
            load_creds_fn=lambda: ("http://base", "key", "model"),
        )
        self.assertFalse(r_fail["ok"])
        self.assertEqual(r_fail["error"], "Gateway timeout")

    def test_step_3_brief(self):
        # 1. Mock 模式
        r_mock = gemini_step_3_brief(mock=True)
        self.assertTrue(r_mock["ok"])
        self.assertIn("title", r_mock["brief"])

        # 2. 正常生成
        mock_brief = {"title": "宋韵", "subtitle": "SONG", "body": "文案", "author": "Agnes"}
        r_ok = gemini_step_3_brief(gen_brief_fn=lambda t, platform, tone: {"ok": True, "brief": mock_brief})
        self.assertTrue(r_ok["ok"])
        self.assertEqual(r_ok["brief"]["title"], "宋韵")

        # 3. 生成失败
        r_fail = gemini_step_3_brief(gen_brief_fn=lambda t, platform, tone: {"ok": False, "error": "Quota limit"})
        self.assertFalse(r_fail["ok"])
        self.assertIn("Quota limit", r_fail["error"])

    def test_step_4_prompt(self):
        # 1. Mock 模式
        r_mock = gemini_step_4_prompt(prompt="minimalist vase", mock=True)
        self.assertTrue(r_mock["ok"])
        self.assertIn("minimalist vase", r_mock["prompt"])

        # 2. 正常生成
        r_ok = gemini_step_4_prompt(refine_fn=lambda p, aspect_ratio, negative_space_zone: {"ok": True, "prompt": "refined prompt"})
        self.assertTrue(r_ok["ok"])
        self.assertEqual(r_ok["prompt"], "refined prompt")

        # 3. 失败
        r_fail = gemini_step_4_prompt(refine_fn=lambda p, aspect_ratio, negative_space_zone: {"ok": False, "error": "Prompt error"})
        self.assertFalse(r_fail["ok"])
        self.assertEqual(r_fail["error"], "Prompt error")

    def test_step_5_detector(self):
        # 1. 图片不存在且未找到候补图片
        r_skip = gemini_step_5_detector(image_path=self.tmp_path / "not_there.png")
        self.assertTrue(r_skip["ok"])

        # 2. Mock 模式
        dummy_img = self.tmp_path / "dummy.png"
        dummy_img.write_bytes(b"test")
        r_mock = gemini_step_5_detector(image_path=dummy_img, mock=True)
        self.assertTrue(r_mock["ok"])
        self.assertTrue(r_mock["mock"])
        self.assertEqual(len(r_mock["faces"]), 1)

        # 3. 自定义检测函数
        r_custom = gemini_step_5_detector(
            image_path=dummy_img,
            detect_fn=lambda path: [[0.1, 0.1, 0.2, 0.2]],
            occlusion_fn=lambda box, faces: (True, "top-left"),
            mock=False,
        )
        self.assertTrue(r_custom["ok"])
        self.assertTrue(r_custom["occlusion_overlap"])
        self.assertEqual(r_custom["occlusion_zone"], "top-left")

    def test_step_6_rasterizer(self):
        target_out = self.tmp_path / "rendered.png"

        # 1. Dry run 模式
        r_dry = gemini_step_6_rasterizer(out_path=target_out, dry_run=True)
        self.assertTrue(r_dry["ok"])
        self.assertTrue(r_dry["dry_run"])
        self.assertFalse(target_out.exists())

        # 2. 正常模拟渲染
        def mock_render(html, out_file):
            Path(out_file).write_bytes(b"png_data" * 200)

        r_render = gemini_step_6_rasterizer(out_path=target_out, render_fn=mock_render, dry_run=False)
        self.assertTrue(r_render["ok"])
        self.assertTrue(target_out.exists())
        self.assertGreater(r_render["size_kb"], 0)

        # 3. 渲染未生成文件
        r_fail = gemini_step_6_rasterizer(
            out_path=self.tmp_path / "failed.png",
            render_fn=lambda html, out_file: None,
            dry_run=False,
        )
        self.assertFalse(r_fail["ok"])
        self.assertIn("未成功生成", r_fail["error"])

    def test_step_7_inspect(self):
        target_poster = self.tmp_path / "poster.png"
        target_poster.write_bytes(b"poster_bytes")

        # 1. Mock 模式
        r_mock = gemini_step_7_inspect(poster_path=target_poster, mock=True)
        self.assertTrue(r_mock["ok"])
        self.assertTrue(r_mock["mock"])
        self.assertGreaterEqual(r_mock["inspection"]["aesthetic_score"], 90)

        # 2. 正常审查
        mock_insp = {"aesthetic_score": 95, "critique": "Excellent"}
        r_ok = gemini_step_7_inspect(
            poster_path=target_poster,
            inspect_fn=lambda path, title: {"ok": True, "inspection": mock_insp},
            mock=False,
        )
        self.assertTrue(r_ok["ok"])
        self.assertEqual(r_ok["inspection"]["aesthetic_score"], 95)

        # 3. 海报文件不存在
        r_missing = gemini_step_7_inspect(poster_path=self.tmp_path / "missing.png", mock=False)
        self.assertFalse(r_missing["ok"])
        self.assertIn("不存在", r_missing["error"])

    def test_run_integration_suite_full_and_filtered(self):
        # 1. 全量执行 (Mock + Dry Run)
        suite_res = gemini_run_integration_suite(
            out_dir=self.tmp_path,
            mock=True,
            dry_run=True,
            verbose=False,
        )
        self.assertTrue(suite_res["ok"])
        self.assertEqual(suite_res["total_steps"], 7)
        self.assertEqual(suite_res["passed"], 7)
        self.assertEqual(suite_res["failed"], 0)

        # 2. 步骤筛选
        sub_res = gemini_run_integration_suite(
            steps=[1, 3],
            mock=True,
            dry_run=True,
            verbose=False,
        )
        self.assertTrue(sub_res["ok"])
        self.assertEqual(sub_res["total_steps"], 2)
        self.assertIn("step_1", sub_res["steps"])
        self.assertIn("step_3", sub_res["steps"])
        self.assertNotIn("step_4", sub_res["steps"])

    def test_run_integration_suite_raise_on_error(self):
        # 模拟步骤 1 报错
        custom_runners = {
            "step_1": lambda: {"step": 1, "ok": False, "error": "Mocked critical error"}
        }
        with self.assertRaises(AssertionError):
            gemini_run_integration_suite(
                steps=[1],
                custom_runners=custom_runners,
                verbose=False,
                raise_on_error=True,
            )

    def test_main_cli_success_and_json_report(self):
        json_report = self.tmp_path / "report.json"
        ret = gemini_main([
            "--mock",
            "--dry-run",
            "--out-dir", str(self.tmp_path),
            "--json", str(json_report),
            "--quiet",
        ])
        self.assertEqual(ret, 0)
        self.assertTrue(json_report.exists())
        data = json.loads(json_report.read_text(encoding="utf-8"))
        self.assertTrue(data["ok"])
        self.assertEqual(data["passed"], 7)

    def test_run_tests_wrapper(self):
        res = gemini_run_tests(
            mock=True,
            dry_run=True,
            verbose=False,
            raise_on_error=False,
        )
        self.assertTrue(res["ok"])

    def test_cli_stdout_json_output(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = gemini_main([
                "--mock",
                "--dry-run",
                "--out-dir", str(self.tmp_path),
                "--json",
                "--quiet",
            ])
        self.assertEqual(ret, 0)
        data = json.loads(buf.getvalue())
        self.assertTrue(data["ok"])
        self.assertEqual(data["passed"], 7)

    def test_cli_exception_stderr_output(self):
        buf = io.StringIO()
        with patch("test_gemini_integration.run_integration_suite", side_effect=RuntimeError("Integration crash")):
            with redirect_stderr(buf):
                ret = gemini_main(["--mock"])
        self.assertEqual(ret, 1)
        self.assertIn("❌ Gemini 集成验证套件执行失败: Integration crash", buf.getvalue())

    def test_cli_exception_quiet_mode(self):
        err_buf = io.StringIO()
        out_buf = io.StringIO()
        with patch("test_gemini_integration.run_integration_suite", side_effect=RuntimeError("Integration crash")):
            with redirect_stderr(err_buf), redirect_stdout(out_buf):
                ret = gemini_main(["--mock", "--quiet"])
        self.assertEqual(ret, 1)
        self.assertEqual(err_buf.getvalue(), "")
        self.assertEqual(out_buf.getvalue(), "")

    def test_cli_exception_json_stdout(self):
        buf = io.StringIO()
        with patch("test_gemini_integration.run_integration_suite", side_effect=RuntimeError("Integration crash")):
            with redirect_stdout(buf):
                ret = gemini_main(["--mock", "--json"])
        self.assertEqual(ret, 1)
        data = json.loads(buf.getvalue())
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"], "Integration crash")

    def test_cli_exception_json_file(self):
        json_report = self.tmp_path / "err_report.json"
        with patch("test_gemini_integration.run_integration_suite", side_effect=RuntimeError("File write crash")):
            ret = gemini_main(["--mock", "--json", str(json_report)])
        self.assertEqual(ret, 1)
        self.assertTrue(json_report.exists())
        data = json.loads(json_report.read_text(encoding="utf-8"))
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"], "File write crash")


class TestComposeBeautyCovers(unittest.TestCase):
    """测试高定美妆封面 2350×1000 负空间与对角拆字排版组件 (Beauty Cover Suite)"""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.dummy_src = self.tmp_path / "dummy_beauty.png"
        Image.new("RGB", (1000, 1000), color=(60, 40, 30)).save(self.dummy_src, "PNG")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_env_and_dimension_constants(self):
        self.assertEqual(BEAUTY_W, 2350)
        self.assertEqual(BEAUTY_H, 1000)
        self.assertEqual(compose_beauty_covers.FONTS, FONTS_DIR)
        self.assertEqual(compose_beauty_covers.ASSETS, ASSETS_DIR)
        self.assertEqual(compose_beauty_covers.CHROME, resolve_chrome_path())
        self.assertTrue(str(compose_beauty_covers.SRC).endswith("_beauty_hero.png"))

    def test_resolve_source_image(self):
        # 1. 显式指定有效路径
        self.assertEqual(beauty_resolve_source(self.dummy_src), self.dummy_src)

        # 2. 显式指定不存在路径报错
        missing = self.tmp_path / "missing.png"
        with self.assertRaises(FileNotFoundError):
            beauty_resolve_source(missing)

        # 3. 自动 fallback 找到存在的底图
        found = beauty_resolve_source()
        self.assertTrue(found.is_file())

        # 4. 当全部 fallback 候选均不存在时抛出 FileNotFoundError
        with patch.object(Path, "is_file", return_value=False):
            with self.assertRaises(FileNotFoundError):
                beauty_resolve_source()

    def test_image_to_base64_uri(self):
        uri = beauty_image_to_b64(self.dummy_src)
        self.assertTrue(uri.startswith("data:image/png;base64,"))

        # 缺失文件报错
        missing = self.tmp_path / "not_there.png"
        with self.assertRaises(FileNotFoundError):
            beauty_image_to_b64(missing)

    def test_cover_html_generation_and_typography(self):
        # safe 区域排版
        html_safe = beauty_cover_html("data:image/png;base64,TEST", title_band="safe")
        self.assertIn("top: 11%; left: 7%;", html_safe)
        self.assertIn("SmileySans", html_safe)
        self.assertIn("神<em>颜</em>", html_safe)
        self.assertIn("ORIENTAL&nbsp;BEAUTY", html_safe)

        # risk 区域排版
        html_risk = beauty_cover_html("data:image/png;base64,TEST", title_band="risk")
        self.assertIn("bottom: 6%; left: 7%;", html_risk)

        # 自定义文案与 XSS 转义
        html_custom = beauty_cover_html(
            "data:image/png;base64,TEST",
            title_a="盛世<美>",
            title_b="极致&奢华",
            title_accent="奢",
            latin="PURE LUXURY",
            slogan="光影掠过<夜色>",
        )
        self.assertIn("盛世&lt;美&gt;", html_custom)
        self.assertIn("极致&amp;<em>奢</em>华", html_custom)
        self.assertIn("PURE&nbsp;LUXURY", html_custom)
        self.assertIn("光影掠过&lt;夜色&gt;", html_custom)

    def test_render_dry_run_modes(self):
        dst_png = self.tmp_path / "sub" / "cover.png"
        res_png = beauty_render("<html></html>", dst_png, fmt="png", dry_run=True)
        self.assertEqual(res_png, dst_png)
        self.assertTrue(dst_png.exists())
        with Image.open(dst_png) as im:
            self.assertEqual(im.size, (BEAUTY_W, BEAUTY_H))
            self.assertEqual(im.format, "PNG")

        dst_jpg = self.tmp_path / "sub" / "cover.jpg"
        res_jpg = beauty_render("<html></html>", dst_jpg, fmt="jpeg", dry_run=True)
        self.assertEqual(res_jpg, dst_jpg)
        self.assertTrue(dst_jpg.exists())
        with Image.open(dst_jpg) as im:
            self.assertEqual(im.size, (BEAUTY_W, BEAUTY_H))
            self.assertEqual(im.format, "JPEG")

    def test_run_beauty_experiment_dry_run(self):
        out_dir = self.tmp_path / "exp_out"
        report = beauty_run_experiment(
            src=self.dummy_src,
            out_dir=out_dir,
            title_band="all",
            dry_run=True,
            quiet=True,
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["src"], str(self.dummy_src))
        self.assertTrue(report["dry_run"])
        self.assertEqual(len(report["rendered_files"]), 4)
        for f in report["rendered_files"]:
            self.assertTrue(Path(f).exists())

        # safe-only
        out_safe = self.tmp_path / "exp_safe"
        report_safe = beauty_run_experiment(
            src=self.dummy_src,
            out_dir=out_safe,
            title_band="safe",
            dry_run=True,
            quiet=True,
        )
        self.assertEqual(len(report_safe["rendered_files"]), 1)
        self.assertTrue(report_safe["rendered_files"][0].endswith("H1_title_top_safe.png"))

    def test_main_cli_success_and_failure(self):
        # 1. 成功执行 CLI
        json_report = self.tmp_path / "cli_report.json"
        exit_code = beauty_main([
            "--src", str(self.dummy_src),
            "--out-dir", str(self.tmp_path / "cli_out"),
            "--dry-run",
            "--json", str(json_report),
            "--quiet",
        ])
        self.assertEqual(exit_code, 0)
        self.assertTrue(json_report.exists())
        data = json.loads(json_report.read_text(encoding="utf-8"))
        self.assertTrue(data["ok"])
        self.assertTrue(data["dry_run"])

        # 2. 传入不存在的底图时返回 1
        fail_code = beauty_main([
            "--src", str(self.tmp_path / "non_existent.png"),
            "--quiet",
        ])
        self.assertEqual(fail_code, 1)

    def test_main_cli_exception_stderr_output(self):
        from contextlib import redirect_stderr
        err_buf = io.StringIO()
        with patch("compose_beauty_covers.run_beauty_experiment", side_effect=RuntimeError("Simulated beauty crash")):
            with redirect_stderr(err_buf):
                exit_code = beauty_main([
                    "--src", str(self.dummy_src),
                ])
        self.assertEqual(exit_code, 1)
        self.assertIn("❌ 运行失败: Simulated beauty crash", err_buf.getvalue())

    def test_main_cli_missing_source_stderr_output(self):
        from contextlib import redirect_stderr
        err_buf = io.StringIO()
        missing_src = self.tmp_path / "non_existent_beauty_source.png"
        with redirect_stderr(err_buf):
            exit_code = beauty_main([
                "--src", str(missing_src),
            ])
        self.assertEqual(exit_code, 1)
        self.assertIn("❌ 运行失败: Source image not found", err_buf.getvalue())


if __name__ == "__main__":
    unittest.main()
