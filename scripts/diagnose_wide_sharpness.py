#!/usr/bin/env python3
"""只读诊断宽幅图片的全画布与主体候选区域锐度。"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image

def _gradient_mean(gray: np.ndarray) -> float:
    if gray.ndim != 2 or min(gray.shape) < 2:
        raise ValueError("gray image must be a 2D array with both dimensions >= 2")
    return float((np.abs(np.diff(gray, axis=1)).mean() + np.abs(np.diff(gray, axis=0)).mean()) / 2)

def diagnose(path: Path | str, roi=(0.20, 0.15, 0.80, 0.90)) -> dict:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Image file not found: {path}")
    if not isinstance(roi, (tuple, list)) or len(roi) != 4:
        raise ValueError("roi must be a sequence of 4 numbers (left, top, right, bottom)")
    left, top, right, bottom = roi
    if not (0.0 <= left < right <= 1.0 and 0.0 <= top < bottom <= 1.0):
        raise ValueError(f"Invalid roi coordinates: {roi}. Must satisfy 0 <= left < right <= 1 and 0 <= top < bottom <= 1")
    raw = path.read_bytes()
    with Image.open(path) as source:
        image = source.convert("L")
        width, height = image.size
        gray = np.asarray(image, dtype=np.float32)
    crop = gray[int(height * top):int(height * bottom), int(width * left):int(width * right)]
    full = _gradient_mean(gray)
    candidate = _gradient_mean(crop)
    return {"file": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "size": [width, height], "full_gradient_mean": round(full, 4),
            "candidate_roi_gradient_mean": round(candidate, 4),
            "candidate_to_full_ratio": round(candidate / max(full, 1e-9), 3),
            "roi_fraction": list(roi), "input_unchanged": True}

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = [diagnose(path) for path in args.images]
    report = {"schema": "agnes.wide-sharpness-diagnostic.v1", "scope": "read-only existing images",
              "count": len(rows), "rows": rows,
              "interpretation": "candidate ROI is diagnostic evidence only; it does not alter acceptance thresholds"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
