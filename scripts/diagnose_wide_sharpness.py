#!/usr/bin/env python3
"""只读诊断宽幅图片的全画布与主体候选区域锐度。"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
from PIL import Image

DEFAULT_ROI: tuple[float, float, float, float] = (0.20, 0.15, 0.80, 0.90)

def _gradient_mean(gray: np.ndarray) -> float:
    if gray.ndim != 2 or min(gray.shape) < 2:
        raise ValueError("gray image must be a 2D array with both dimensions >= 2")
    return float((np.abs(np.diff(gray, axis=1)).mean() + np.abs(np.diff(gray, axis=0)).mean()) / 2)

def diagnose(path: Path | str, roi: tuple[float, float, float, float] | list[float] = DEFAULT_ROI) -> dict:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Image file not found: {path}")
    if not isinstance(roi, (tuple, list)) or len(roi) != 4:
        raise ValueError("roi must be a sequence of 4 numbers (left, top, right, bottom)")
    try:
        left, top, right, bottom = (float(roi[0]), float(roi[1]), float(roi[2]), float(roi[3]))
    except (TypeError, ValueError):
        raise ValueError(f"roi coordinates must be numeric: {roi}")
    if not (0.0 <= left < right <= 1.0 and 0.0 <= top < bottom <= 1.0):
        raise ValueError(f"Invalid roi coordinates: {roi}. Must satisfy 0 <= left < right <= 1 and 0 <= top < bottom <= 1")
    raw = path.read_bytes()
    with Image.open(path) as source:
        image = source.convert("L")
        width, height = image.size
        gray = np.asarray(image, dtype=np.float32)
    crop_x1, crop_x2 = int(width * left), int(width * right)
    crop_y1, crop_y2 = int(height * top), int(height * bottom)
    if (crop_x2 - crop_x1) < 2 or (crop_y2 - crop_y1) < 2:
        raise ValueError(
            f"ROI pixel crop ({crop_x2 - crop_x1}x{crop_y2 - crop_y1}) must have width and height >= 2 pixels"
        )
    crop = gray[crop_y1:crop_y2, crop_x1:crop_x2]
    full = _gradient_mean(gray)
    candidate = _gradient_mean(crop)
    return {"file": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "size": [width, height], "full_gradient_mean": round(full, 4),
            "candidate_roi_gradient_mean": round(candidate, 4),
            "candidate_to_full_ratio": round(candidate / max(full, 1e-9), 3),
            "roi_fraction": [left, top, right, bottom], "input_unchanged": True}

def build_arg_parser() -> argparse.ArgumentParser:
    """构建只读宽幅图片锐度诊断命令行参数解析器。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path, help="One or more image file paths to diagnose")
    parser.add_argument("--out", "-o", type=Path, default=None, help="Optional output JSON report path")
    parser.add_argument(
        "--roi",
        nargs=4,
        type=float,
        default=list(DEFAULT_ROI),
        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
        help="Candidate ROI coordinates: left top right bottom (0.0 to 1.0)",
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress JSON output to stdout")
    parser.add_argument("--strict", action="store_true", help="Exit with non-zero code if any image diagnostic fails")
    return parser

def main(argv=None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    roi_tuple = tuple(args.roi)
    rows = []
    has_error = False
    for path in args.images:
        try:
            row = diagnose(path, roi=roi_tuple)
            rows.append(row)
        except Exception as e:
            has_error = True
            if args.strict:
                if not args.quiet:
                    print(json.dumps({
                        "ok": False,
                        "error": str(e),
                        "file": str(path),
                    }, ensure_ascii=False, indent=2), file=sys.stderr)
                return 1
            rows.append({
                "file": str(path),
                "error": str(e),
                "ok": False,
                "input_unchanged": True,
            })
    report = {"schema": "agnes.wide-sharpness-diagnostic.v1", "scope": "read-only existing images",
              "count": len(rows), "rows": rows,
              "interpretation": "candidate ROI is diagnostic evidence only; it does not alter acceptance thresholds"}
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if not args.quiet:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if (args.strict and has_error) else 0

if __name__ == "__main__":
    raise SystemExit(main())
