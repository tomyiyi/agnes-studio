#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio · 多模态视觉主体与避障检测引擎 (Vision Subject Detector)
调用 macOS 原生 Vision 框架，提供像素级人脸/主体保护区判定
"""

import argparse
import json
import os
import subprocess
import sys
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

def build_arg_parser() -> argparse.ArgumentParser:
    """构建视觉主体与避障检测引擎 CLI 参数解析器"""
    parser = argparse.ArgumentParser(description="Agnes Studio · 多模态视觉主体与避障检测引擎 (Vision Subject Detector)")
    parser.add_argument(
        "--image",
        "-i",
        default=None,
        help="目标输入图片路径（未指定时将查找 public/assets 中的样张底图）",
    )
    parser.add_argument(
        "--out",
        "-o",
        default=None,
        help="检测与避障分析结果 JSON 保存路径",
    )
    parser.add_argument(
        "--box",
        "-b",
        nargs=4,
        type=float,
        default=None,
        metavar=("X1", "Y1", "X2", "Y2"),
        help="待测试排版文本框坐标 (0.0~1.0)，执行避障碰撞检测",
    )
    parser.add_argument(
        "--padding",
        type=float,
        default=None,
        help="避障碰撞检测外扩缓冲区 padding (0.0~1.0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出检测与避障结果至标准输出",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="静默模式，抑制常规提示与过程日志",
    )
    parser.add_argument(
        "--require-subject",
        action="store_true",
        help="要求必须检测到至少一个人脸/主体保护区，未检测到则返回退出码 1",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：文件不存在、遮挡碰撞冲突或未达主体要求时返回退出码 1",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Agnes Gateway 端点地址",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Agnes Gateway API Key",
    )
    parser.add_argument(
        "--trace-id",
        default=None,
        help="请求追踪 trace_id",
    )
    parser.add_argument(
        "--key-path",
        default=None,
        help="密钥文件路径",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    current_dir = Path(__file__).resolve().parent.parent
    if args.image:
        target_path = Path(args.image).resolve()
    else:
        test_img = current_dir / "public" / "assets" / "agnes_1789998061_5508.png"
        if not test_img.exists():
            candidates = list((current_dir / "public" / "assets").glob("*.png"))
            target_path = candidates[0] if candidates else test_img
        else:
            target_path = test_img

    if not target_path.is_file():
        err_msg = f"找不到目标图片文件: {target_path}"
        if args.json:
            print(json.dumps({
                "ok": False,
                "exists": False,
                "image": str(target_path),
                "error": err_msg,
            }, ensure_ascii=False, indent=2))
        elif not args.quiet:
            print(f"❌ {err_msg}", file=sys.stderr)
        return 1

    try:
        faces = detect_faces(
            str(target_path),
            base_url=args.base_url,
            api_key=args.api_key,
            trace_id=args.trace_id,
            key_path=args.key_path,
        )

        occlusion_result = None
        if args.box is not None:
            has_overlap, zone = check_occlusion(args.box, faces, padding=args.padding)
            occlusion_result = {
                "has_occlusion": has_overlap,
                "conflicting_zone": zone,
                "test_box": args.box,
            }

        report = {
            "ok": True,
            "image": str(target_path),
            "exists": True,
            "subjects_count": len(faces),
            "subjects": faces,
        }
        if occlusion_result is not None:
            report["occlusion"] = occlusion_result

        if args.out:
            out_file = Path(args.out).resolve()
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if not args.quiet and not args.json:
                print(f"✨ 视觉检测与避障报告已保存至: {out_file}")

        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        elif not args.quiet:
            print(f"✓ 检测到人脸/主体保护区: {faces}")
            if occlusion_result:
                if occlusion_result["has_occlusion"]:
                    print(f"⚠️ 文本框与主体保护区发生重叠: {occlusion_result['conflicting_zone']}")
                else:
                    print("✓ 文本框避障安全，未与主体重叠")

        # 退出码判定
        if args.require_subject and len(faces) == 0:
            return 1
        if args.strict:
            if occlusion_result and occlusion_result["has_occlusion"]:
                return 1

        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({
                "ok": False,
                "image": str(target_path),
                "error": str(e),
            }, ensure_ascii=False, indent=2))
        elif not args.quiet:
            print(f"❌ 视觉主体与避障检测异常: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
