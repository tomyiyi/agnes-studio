#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio - 跨平台环境与路径解析器 (Cross-Platform Path & Environment Resolver)
自动支持 macOS (MacBook Pro M5 / 黑苹果主机) 与 Linux (Omarchy / 虚拟机 / 服务器)
"""

import os
import sys
import shutil
from pathlib import Path

# 项目根目录自动定位 (基于当前文件上一层级)
SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
PUBLIC_DIR = PROJECT_ROOT / "public"
ASSETS_DIR = PUBLIC_DIR / "assets"
FONTS_DIR = PUBLIC_DIR / "fonts"
DATA_DIR = PROJECT_ROOT / "data"

# 确保核心资源目录存在
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
FONTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

def resolve_chrome_path() -> str:
    """自动探测不同操作系统下的真实 Chrome / Chromium 执行路径"""
    # 优先使用环境变量指定
    custom_path = os.environ.get("CHROME_PATH") or os.environ.get("PUPPETEER_EXECUTABLE_PATH")
    if custom_path and os.path.exists(custom_path):
        return custom_path

    if sys.platform == "darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        which_path = shutil.which("google-chrome") or shutil.which("chromium")
        if which_path:
            return which_path

    elif sys.platform.startswith("linux"):
        candidates = [
            "/usr/bin/chromium",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser"
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        which_path = shutil.which("chromium") or shutil.which("google-chrome") or shutil.which("google-chrome-stable")
        if which_path:
            return which_path

    elif sys.platform == "win32":
        candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
                
    return "chromium"

def resolve_font_path(font_key: str = "smiley") -> str:
    """
    自动解析跨平台中文字体路径 (macOS / Linux / Windows)
    支持 'smiley' (得意黑), 'wenkai' (霞鹜文楷), 'songti' / 'serif' (宋体/衬线), 'pingfang' / 'sans' (黑体/无衬线)。
    返回存在的字体文件绝对路径；若未命中则返回项目中可用的备选字体。
    """
    key = str(font_key).lower().strip()

    # 1. 优先检查直接传递的有效绝对路径或相对路径
    direct = Path(font_key)
    if direct.is_file():
        return str(direct.resolve())

    # 2. 检查 public/fonts 中是否有完全同名或匹配文件名
    exact_match = FONTS_DIR / font_key
    if exact_match.is_file():
        return str(exact_match.resolve())

    # 3. 按语义类型路由候选路径
    if key in ("smiley", "smileysans", "smiley-sans", "oblique"):
        candidates = [
            FONTS_DIR / "SmileySans-Oblique.ttf",
            FONTS_DIR / "SmileySans-Oblique.otf",
        ]
    elif key in ("wenkai", "lxgw", "lxgwwenkai", "kai"):
        candidates = [
            FONTS_DIR / "LXGWWenKai-Regular.ttf",
        ]
    elif key in ("songti", "song", "serif", "didot", "bodoni"):
        candidates = [
            # macOS 系统路径
            Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
            Path("/Library/Fonts/Songti.ttc"),
            Path("/System/Library/Fonts/STSong.ttc"),
            # Linux 系统路径 (Noto Serif CJK / 思源宋体)
            Path("/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc"),
            Path("/usr/share/fonts/noto-cjk/NotoSerifCJK-Bold.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/noto/NotoSerifCJK-Regular.ttc"),
            # Windows 系统路径 (中易宋体)
            Path(os.path.expandvars(r"%WINDIR%\Fonts\simsun.ttc")),
            # 项目内置优雅衬线/楷体降级
            FONTS_DIR / "LXGWWenKai-Regular.ttf",
            FONTS_DIR / "SmileySans-Oblique.ttf",
        ]
    elif key in ("pingfang", "sans", "sans-serif", "hei", "futura"):
        candidates = [
            # macOS 系统路径
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("/Library/Fonts/PingFang.ttc"),
            # Linux 系统路径 (Noto Sans CJK / 思源黑体)
            Path("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
            # Windows 系统路径 (微软雅黑)
            Path(os.path.expandvars(r"%WINDIR%\Fonts\msyh.ttc")),
            # 项目内置无衬线降级
            FONTS_DIR / "SmileySans-Oblique.ttf",
            FONTS_DIR / "LXGWWenKai-Regular.ttf",
        ]
    else:
        # 通用未指定类型
        candidates = [
            FONTS_DIR / f"{font_key}.ttf",
            FONTS_DIR / f"{font_key}.otf",
            FONTS_DIR / "SmileySans-Oblique.ttf",
            FONTS_DIR / "LXGWWenKai-Regular.ttf",
        ]

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate.resolve())

    # 4. 终极兜底：返回 fonts 目录中第一个发现的字体文件
    for fallback in sorted(FONTS_DIR.glob("*.*")):
        if fallback.suffix.lower() in (".ttf", ".otf", ".ttc"):
            return str(fallback.resolve())

    return ""

if __name__ == "__main__":
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Assets Dir:   {ASSETS_DIR}")
    print(f"Fonts Dir:    {FONTS_DIR}")
    print(f"Detected Chrome: {resolve_chrome_path()}")
