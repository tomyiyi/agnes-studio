#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文文案排版规范检查 / 自动修正
================================

落地 GitHub 高星方案：
  - sparanoid/chinese-copywriting-guidelines (15k+ ★)
    · 中英文之间加空格
    · 使用全形中文标点
    · 直角引号「」，不用弯引号
  - vinta/pangu.js（盘古之白自动补空）

用法：
  from copywriting_rules import lint_copy, apply_fix
"""

from __future__ import annotations

import re

# 禁则（弯引号等）
BAD_CHARS = {
    "“": "「",
    "”": "」",
    "‘": "『",
    "’": "』",
}

# 半角→全角（中文语境）
HALF_TO_FULL = {
    "!": "！",
    "?": "？",
    ",": "，",
    ";": "；",
    ":": "：",
    "(": "（",
    ")": "）",
}


def apply_pangu_spacing(text: str) -> str:
    """中英文/数字之间补空格（盘古之白）。"""
    if not text:
        return text
    # 汉字 与 [A-Za-z0-9] 之间
    text = re.sub(r"([一-鿿])([A-Za-z0-9@#$%&*+=])", r"\1 \2", text)
    text = re.sub(r"([A-Za-z0-9@#$%&*+=])([一-鿿])", r"\1 \2", text)
    return text


def normalize_punctuation(text: str) -> str:
    """弯引号→直角；中文句内半角标点→全角（保守）。"""
    out = []
    for ch in text:
        if ch in BAD_CHARS:
            out.append(BAD_CHARS[ch])
        else:
            out.append(ch)
    s = "".join(out)
    # 前后都是汉字时，将半角,!?; 换全角
    s = re.sub(r"(?<=[一-鿿])([!?;,:])(?=[一-鿿])", lambda m: HALF_TO_FULL.get(m.group(1), m.group(1)), s)
    return s


def apply_fix(text: str) -> str:
    return apply_pangu_spacing(normalize_punctuation(text))


def lint_copy(text: str) -> list[str]:
    """返回问题列表；空表示合规。"""
    issues: list[str] = []
    for bad, good in BAD_CHARS.items():
        if bad in text:
            issues.append(f"弯引号「{bad}」→ 请用「{good}」")
    # 中英粘连
    if re.search(r"[一-鿿][A-Za-z0-9]", text) or re.search(r"[A-Za-z0-9][一-鿿]", text):
        issues.append("中英文/数字之间缺空格（盘古之白 0.25em）")
    return issues


def list_rules() -> list[dict[str, str]]:
    """返回中文文案排版规范规则清单。"""
    return [
        {
            "id": "pangu-spacing",
            "name": "盘古之白",
            "scope": "中西文混排",
            "description": "汉字与英文、数字及常用半角符号之间自动补空 (0.25em)",
        },
        {
            "id": "corner-quotes",
            "name": "直角引号",
            "scope": "引号规范",
            "description": "统一使用直角引号「」与『』，杜绝弯引号“ ”‘ ’",
        },
        {
            "id": "cjk-punctuation",
            "name": "全角标点",
            "scope": "标点规范",
            "description": "汉语句内半角标点 (!?,;:()) 自动规范化为全角标点",
        },
    ]


def build_arg_parser():
    import argparse
    parser = argparse.ArgumentParser(
        description="Agnes Studio · 中文文案排版规范检查与自动修正引擎 (Chinese Copywriting Rules)"
    )
    parser.add_argument(
        "text_arg",
        nargs="?",
        default=None,
        help="待处理文案内容（可选；未提供时可通过 --text、--file 或使用内置 Demo）",
    )
    parser.add_argument(
        "-t", "--text",
        dest="text_opt",
        default=None,
        help="显式传入待处理文案内容",
    )
    parser.add_argument(
        "-f", "--file",
        dest="file_path",
        default=None,
        help="文案文本文件路径",
    )
    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="列出中文文案排版规范规则清单并退出",
    )
    parser.add_argument(
        "-c", "--check",
        action="store_true",
        help="仅执行合规性检查（Lint 模式），输出违规项",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="执行自动格式修正（修复盘古空格与直角引号，默认模式）",
    )
    parser.add_argument(
        "-i", "--in-place",
        action="store_true",
        help="与 --file 配合使用，将修正结果写回原文件",
    )
    parser.add_argument(
        "-o", "--out",
        dest="out_path",
        default=None,
        help="将修正后的文案写入指定目标文件",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 结构输出检查/修正结果",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="静默模式，抑制标准输出",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式：若检查发现排版问题或输入文件不存在，返回退出码 1",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    import json
    import sys
    from pathlib import Path

    parser = build_arg_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.list_rules:
        try:
            rules = list_rules()
            if args.json:
                print(json.dumps(rules, ensure_ascii=False, indent=2))
            elif not args.quiet:
                print("Agnes Studio · 中文文案排版规范规则清单:")
                for r in rules:
                    print(f"  [{r['id']:<16}] {r['name']:<8} | 范畴: {r['scope']:<8} | 说明: {r['description']}")
                print(f"总计: {len(rules)} 项规范")
            return 0
        except Exception as e:
            if args.json:
                print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
            elif not args.quiet:
                sys.stderr.write(f"❌ 查询文案排版规则清单失败: {e}\n")
            return 1

    is_demo = False
    raw_text: str = ""

    if args.file_path:
        p = Path(args.file_path)
        if not p.is_file():
            if args.json:
                print(json.dumps({"ok": False, "error": f"找不到文案文件: {args.file_path}"}, ensure_ascii=False))
            elif not args.quiet:
                sys.stderr.write(f"❌ 找不到文案文件: {args.file_path}\n")
            return 1
        try:
            raw_text = p.read_text(encoding="utf-8")
        except Exception as e:
            if args.json:
                print(json.dumps({"ok": False, "error": f"读取文案文件失败 {args.file_path}: {e}"}, ensure_ascii=False))
            elif not args.quiet:
                sys.stderr.write(f"❌ 读取文案文件失败 {args.file_path}: {e}\n")
            return 1
    else:
        given = args.text_opt or args.text_arg
        if given is not None:
            raw_text = given
        else:
            is_demo = True
            raw_text = "东方BEAUTY的“高级感”来自10:1字阶"

    try:
        issues = lint_copy(raw_text)
        fixed = apply_fix(raw_text)

        if args.check:
            if args.json:
                result = {
                    "clean": len(issues) == 0,
                    "issues": issues,
                    "original": raw_text,
                    "fixed": fixed,
                }
                if not args.quiet:
                    print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                if not args.quiet:
                    if not issues:
                        print("✓ 文案排版规范检查通过，未发现格式问题。")
                    else:
                        print(f"⚠️ 发现 {len(issues)} 项文案排版规范问题:")
                        for idx, issue in enumerate(issues, 1):
                            print(f"  [{idx}] {issue}")
            if args.strict and issues:
                return 1
            return 0

        # 默认或 --fix 模式
        if args.json:
            result = {
                "clean": len(issues) == 0,
                "issues": issues,
                "original": raw_text,
                "fixed": fixed,
            }
            if not args.quiet:
                print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if not args.quiet:
                if is_demo and not args.out_path and not args.in_place:
                    print("in ", raw_text)
                    print("fix", fixed)
                    print("lint", issues)
                else:
                    print(fixed)

        if args.out_path:
            out_p = Path(args.out_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(fixed, encoding="utf-8")

        if args.in_place and args.file_path:
            Path(args.file_path).write_text(fixed, encoding="utf-8")

        if args.strict and issues:
            return 1
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        elif not args.quiet:
            if getattr(args, "list_rules", False):
                sys.stderr.write(f"❌ 查询文案排版规则清单失败: {e}\n")
            else:
                sys.stderr.write(f"❌ 文案排版处理异常: {e}\n")
        return 1


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
