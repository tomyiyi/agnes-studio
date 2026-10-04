#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio · 多模态视觉主体与避障检测引擎 (Vision Subject Detector)
调用 macOS 原生 Vision 框架，提供像素级人脸/主体保护区判定
"""

import subprocess
import json
import os
import tempfile
from pathlib import Path

SWIFT_DETECTOR = """import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count > 1 else { exit(1) }
let path = CommandLine.arguments[1]
let url = URL(fileURLWithPath: path)
guard let image = NSImage(contentsOf: url),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("[]")
    exit(0)
}

var faces: [[String: Double]] = []
let request = VNDetectFaceRectanglesRequest { req, _ in
    guard let observations = req.results as? [VNFaceObservation] else { return }
    for obs in observations {
        let b = obs.boundingBox
        let topY = 1.0 - (b.origin.y + b.size.height)
        let bottomY = 1.0 - b.origin.y
        faces.append([
            "x_min": Double(b.origin.x),
            "x_max": Double(b.origin.x + b.size.width),
            "y_min": Double(topY),
            "y_max": Double(bottomY)
        ])
    }
}

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try? handler.perform([request])

if let data = try? JSONSerialization.data(withJSONObject: faces, options: []) {
    print(String(data: data, encoding: .utf8) ?? "[]")
}
"""

def detect_faces(image_path, base_url=None, api_key=None, trace_id=None, key_path=None):
    if not image_path:
        return []
    try:
        safe_img = Path(image_path).resolve()
        if not safe_img.is_file():
            return []
    except Exception:
        return []

    import shutil
    # 1. 优先使用 macOS 原生 Vision 框架 (极低延迟无网络开销)
    if shutil.which("swift"):
        tmp_swift = None
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".swift", delete=False, encoding="utf-8") as tf:
                tf.write(SWIFT_DETECTOR)
                tmp_swift = tf.name

            res = subprocess.run(["swift", tmp_swift, str(safe_img)], capture_output=True, text=True, timeout=15)
            faces = json.loads(res.stdout.strip())
            if isinstance(faces, list) and faces:
                return faces
        except Exception:
            pass
        finally:
            if tmp_swift and os.path.exists(tmp_swift):
                try:
                    os.remove(tmp_swift)
                except OSError:
                    pass

    # 2. Linux / 虚拟机环境：无缝调用稳定的 Agnes 多模态视觉引擎
    try:
        from agnes_engine import detect_visual_subjects
        agnes_faces = detect_visual_subjects(
            str(safe_img),
            base_url=base_url,
            api_key=api_key,
            trace_id=trace_id,
            key_path=key_path,
        )
        if agnes_faces:
            return agnes_faces
    except Exception as e:
        print(f"⚠️ [Vision Subject Detector] Agnes 回退探测提示: {e}")

    return []

def check_occlusion(text_box, exclusion_zones):
    """
    检查文本框 (tx1, ty1, tx2, ty2) 与保护区是否存在遮挡交叠
    坐标统一为 0.0 ~ 1.0 百分比
    """
    if not text_box or len(text_box) != 4:
        return False, None
    if not exclusion_zones or not isinstance(exclusion_zones, (list, tuple)):
        return False, None

    try:
        tx1, ty1, tx2, ty2 = (float(text_box[0]), float(text_box[1]), float(text_box[2]), float(text_box[3]))
    except (TypeError, ValueError):
        return False, None

    for zone in exclusion_zones:
        if not isinstance(zone, dict):
            continue
        try:
            # 外扩头部上方 5% 和两侧各 3% 作为发饰与眼神呼吸缓冲区
            zx1 = float(zone["x_min"]) - 0.03
            zx2 = float(zone["x_max"]) + 0.03
            zy1 = float(zone["y_min"]) - 0.05
            zy2 = float(zone["y_max"]) + 0.03
        except (KeyError, TypeError, ValueError):
            continue

        # 判断重叠 (无交集条件的反面)
        has_overlap = not (tx2 < zx1 or tx1 > zx2 or ty2 < zy1 or ty1 > zy2)
        if has_overlap:
            return True, zone
    return False, None

if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent.parent
    test_img = current_dir / "public" / "assets" / "agnes_1789998061_5508.png"
    if not test_img.exists():
        candidates = list((current_dir / "public" / "assets").glob("*.png"))
        test_img = candidates[0] if candidates else test_img
    faces = detect_faces(test_img)
    print("✓ 检测到人脸/主体保护区:", faces)
