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


if __name__ == "__main__":
    demo = "东方BEAUTY的“高级感”来自10:1字阶"
    print("in ", demo)
    print("fix", apply_fix(demo))
    print("lint", lint_copy(demo))
