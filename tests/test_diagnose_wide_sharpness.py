import json, tempfile, unittest
from pathlib import Path
import sys
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from diagnose_wide_sharpness import diagnose, main, build_arg_parser, DEFAULT_ROI

class TestDiagnoseWideSharpness(unittest.TestCase):
    def test_preserves_input_and_reports_roi(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wide.png"
            Image.new("RGB", (2350, 1000), "white").save(path)
            before = path.read_bytes(); row = diagnose(path)
            self.assertEqual(row["size"], [2350, 1000])
            self.assertTrue(row["input_unchanged"])
            self.assertEqual(path.read_bytes(), before)

    def test_cli_writes_schema_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); image = root / "wide.png"; report = root / "report.json"
            Image.new("RGB", (2350, 1000), "white").save(image)
            self.assertEqual(main([str(image), "--out", str(report)]), 0)
            payload = json.loads(report.read_text())
            self.assertEqual(payload["schema"], "agnes.wide-sharpness-diagnostic.v1")
            self.assertEqual(payload["count"], 1)

    def test_diagnose_accepts_string_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "str_wide.png"
            Image.new("RGB", (1000, 500), "black").save(image)
            row = diagnose(str(image))
            self.assertEqual(row["size"], [1000, 500])
            self.assertTrue(row["input_unchanged"])

    def test_diagnose_missing_file_raises_not_found(self):
        with self.assertRaises(FileNotFoundError):
            diagnose("non_existent_diagnostic_img.png")

    def test_diagnose_invalid_roi_raises_value_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "invalid_roi.png"
            Image.new("RGB", (200, 200), "white").save(image)
            # 倒置坐标
            with self.assertRaises(ValueError):
                diagnose(image, roi=(0.8, 0.5, 0.2, 0.9))
            # 维度不足
            with self.assertRaises(ValueError):
                diagnose(image, roi=(0.1, 0.2))
            # 超出边界
            with self.assertRaises(ValueError):
                diagnose(image, roi=(-0.1, 0.1, 0.5, 0.5))

    def test_cli_writes_report_with_custom_roi(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); image = root / "wide_roi.png"; report = root / "report.json"
            Image.new("RGB", (2000, 1000), "white").save(image)
            self.assertEqual(main([str(image), "--out", str(report), "--roi", "0.1", "0.2", "0.7", "0.8"]), 0)
            payload = json.loads(report.read_text())
            self.assertEqual(payload["count"], 1)
            self.assertEqual(payload["rows"][0]["roi_fraction"], [0.1, 0.2, 0.7, 0.8])

    def test_diagnose_non_numeric_roi_raises_value_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "non_num_roi.png"
            Image.new("RGB", (200, 200), "white").save(image)
            with self.assertRaises(ValueError) as ctx:
                diagnose(image, roi=("invalid", 0.1, 0.8, 0.9))
            self.assertIn("roi coordinates must be numeric", str(ctx.exception))

    def test_diagnose_tiny_crop_raises_value_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "tiny.png"
            # 5x5 图片，若 ROI 比例极小，像素截取区间跨度小于 2
            Image.new("RGB", (5, 5), "white").save(image)
            with self.assertRaises(ValueError) as ctx:
                diagnose(image, roi=(0.1, 0.1, 0.15, 0.15))
            self.assertIn("must have width and height >= 2 pixels", str(ctx.exception))

    def test_diagnose_integer_roi_normalized(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "int_roi.png"
            Image.new("RGB", (500, 400), "white").save(image)
            row = diagnose(image, roi=[0, 0, 1, 1])
            self.assertEqual(row["roi_fraction"], [0.0, 0.0, 1.0, 1.0])
            self.assertEqual(row["size"], [500, 400])

    def test_cli_main_without_out_prints_to_stdout(self):
        import io
        import contextlib
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "stdout_diag.png"
            Image.new("RGB", (1000, 500), "white").save(image)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = main([str(image)])
            self.assertEqual(code, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["schema"], "agnes.wide-sharpness-diagnostic.v1")
            self.assertEqual(payload["count"], 1)

    def test_cli_main_with_quiet_flag(self):
        import io
        import contextlib
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "quiet_diag.png"
            report = root / "quiet_report.json"
            Image.new("RGB", (1000, 500), "white").save(image)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = main([str(image), "--out", str(report), "-q"])
            self.assertEqual(code, 0)
            self.assertEqual(buf.getvalue(), "")
            self.assertTrue(report.exists())
            payload = json.loads(report.read_text())
            self.assertEqual(payload["count"], 1)

    def test_default_roi_constant(self):
        self.assertEqual(len(DEFAULT_ROI), 4)
        self.assertEqual(DEFAULT_ROI, (0.20, 0.15, 0.80, 0.90))

    def test_build_arg_parser(self):
        parser = build_arg_parser()
        self.assertIsNotNone(parser)
        parsed = parser.parse_args(["img.png", "--strict", "-q", "-o", "out.json"])
        self.assertTrue(parsed.strict)
        self.assertTrue(parsed.quiet)
        self.assertEqual(str(parsed.out), "out.json")
        self.assertEqual(parsed.roi, list(DEFAULT_ROI))

    def test_cli_main_error_resilience_non_strict(self):
        import io
        import contextlib
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid_img = root / "valid.png"
            Image.new("RGB", (1000, 500), "white").save(valid_img)
            missing_img = root / "missing.png"

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = main([str(valid_img), str(missing_img)])
            self.assertEqual(code, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["count"], 2)
            self.assertEqual(payload["rows"][0]["file"], str(valid_img))
            self.assertTrue(payload["rows"][0]["input_unchanged"])
            self.assertEqual(payload["rows"][1]["file"], str(missing_img))
            self.assertFalse(payload["rows"][1]["ok"])
            self.assertIn("error", payload["rows"][1])

    def test_cli_main_strict_mode_failure(self):
        import io
        import contextlib
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_img = root / "missing.png"

            err_buf = io.StringIO()
            with contextlib.redirect_stderr(err_buf):
                code = main([str(missing_img), "--strict"])
            self.assertEqual(code, 1)
            err_data = json.loads(err_buf.getvalue())
            self.assertFalse(err_data["ok"])
            self.assertEqual(err_data["file"], str(missing_img))

    def test_cli_main_strict_mode_quiet(self):
        import io
        import contextlib
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_img = root / "missing.png"

            err_buf = io.StringIO()
            with contextlib.redirect_stderr(err_buf):
                code = main([str(missing_img), "--strict", "--quiet"])
            self.assertEqual(code, 1)
            self.assertEqual(err_buf.getvalue(), "")


if __name__ == "__main__": unittest.main()
