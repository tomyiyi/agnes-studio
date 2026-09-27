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

if __name__ == "__main__": unittest.main()
