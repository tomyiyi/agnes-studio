import json, tempfile, unittest
from pathlib import Path
import sys
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from diagnose_wide_sharpness import diagnose, main

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


if __name__ == "__main__": unittest.main()
