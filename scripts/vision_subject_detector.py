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

def check_occlusion(text_box, exclusion_zones, padding=None):
    """
    检查文本框 (tx1, ty1, tx2, ty2) 与保护区是否存在遮挡交叠
    坐标统一为 0.0 ~ 1.0 百分比
    支持 dict {"x_min", "x_max", "y_min", "y_max"} 或 (x1, y1, x2, y2) 格式的保护区
    支持自定义 padding: float, dict(top, bottom, side) 或 tuple(pad_x, pad_y)
    """
    if not text_box or len(text_box) != 4:
        return False, None
    if not exclusion_zones or not isinstance(exclusion_zones, (list, tuple)):
        return False, None

    try:
        t0, t1, t2, t3 = (float(text_box[0]), float(text_box[1]), float(text_box[2]), float(text_box[3]))
        tx1, tx2 = min(t0, t2), max(t0, t2)
        ty1, ty2 = min(t1, t3), max(t1, t3)
    except (TypeError, ValueError):
        return False, None

    # 默认外扩头部上方 5% 和两侧各 3% 作为发饰与眼神呼吸缓冲区
    pad_left = pad_right = 0.03
    pad_top = 0.05
    pad_bottom = 0.03
    if padding is not None:
        try:
            if isinstance(padding, (int, float)):
                p = float(padding)
                pad_left = pad_right = pad_top = pad_bottom = p
            elif isinstance(padding, dict):
                pad_top = float(padding.get("top", 0.05))
                pad_bottom = float(padding.get("bottom", 0.03))
                side = float(padding.get("side", padding.get("x", 0.03)))
                pad_left = float(padding.get("left", side))
                pad_right = float(padding.get("right", side))
            elif isinstance(padding, (list, tuple)):
                if len(padding) == 2:
                    pad_left = pad_right = float(padding[0])
                    pad_top = pad_bottom = float(padding[1])
                elif len(padding) == 4:
                    pad_left, pad_top, pad_right, pad_bottom = (
                        float(padding[0]), float(padding[1]), float(padding[2]), float(padding[3])
                    )
        except (TypeError, ValueError):
            pass

    for zone in exclusion_zones:
        try:
            if isinstance(zone, dict):
                z_x1 = float(zone["x_min"])
                z_x2 = float(zone["x_max"])
                z_y1 = float(zone["y_min"])
                z_y2 = float(zone["y_max"])
            elif isinstance(zone, (list, tuple)) and len(zone) == 4:
                z_x1, z_y1, z_x2, z_y2 = (float(zone[0]), float(zone[1]), float(zone[2]), float(zone[3]))
            else:
                continue

            zx_min, zx_max = min(z_x1, z_x2), max(z_x1, z_x2)
            zy_min, zy_max = min(z_y1, z_y2), max(z_y1, z_y2)

            zx1 = zx_min - pad_left
            zx2 = zx_max + pad_right
            zy1 = zy_min - pad_top
            zy2 = zy_max + pad_bottom
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
