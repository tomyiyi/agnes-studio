#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio · 多模态视觉主体与避障检测引擎 (Vision Subject Detector)
调用 macOS 原生 Vision 框架，提供像素级人脸/主体保护区判定
"""

import subprocess
import json
import os
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

def detect_faces(image_path):
    safe_img = Path(image_path).resolve()
    if not safe_img.is_file():
        return []

    import shutil
    # 1. 优先使用 macOS 原生 Vision 框架 (极低延迟无网络开销)
    if shutil.which("swift"):
        safe_swift = Path("/tmp/detect_faces.swift").resolve()
        if not (str(safe_swift).startswith("/tmp") or str(safe_swift).startswith("/private/tmp")) or ".." in str(safe_swift):
            raise ValueError("Invalid swift script path")

        safe_swift.write_text(SWIFT_DETECTOR, encoding="utf-8")
            
        res = subprocess.run(["swift", str(safe_swift), str(safe_img)], capture_output=True, text=True)
        try:
            faces = json.loads(res.stdout.strip())
            if isinstance(faces, list) and faces:
                return faces
        except Exception:
            pass

    # 2. Linux / 虚拟机环境：无缝调用稳定的 Gemini 2.5 Flash 多模态视觉引擎
    try:
        from gemini_engine import detect_visual_subjects_gemini
        gemini_faces = detect_visual_subjects_gemini(str(safe_img))
        if gemini_faces:
            return gemini_faces
    except Exception as e:
        print(f"⚠️ [Vision Subject Detector] Gemini 回退探测提示: {e}")

    return []

def check_occlusion(text_box, exclusion_zones):
    """
    检查文本框 (tx1, ty1, tx2, ty2) 与保护区是否存在遮挡交叠
    坐标统一为 0.0 ~ 1.0 百分比
    """
    tx1, ty1, tx2, ty2 = text_box
    for zone in exclusion_zones:
        # 外扩头部上方 5% 和两侧各 3% 作为发饰与眼神呼吸缓冲区
        zx1 = zone["x_min"] - 0.03
        zx2 = zone["x_max"] + 0.03
        zy1 = zone["y_min"] - 0.05
        zy2 = zone["y_max"] + 0.03
        
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
