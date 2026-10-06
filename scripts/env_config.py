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
from typing import Optional

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

def resolve_chrome_path() -> Optional[str]:
    """自动探测不同操作系统下的真实 Chrome / Chromium 执行路径。

    找不到任何系统 Chrome/Chromium 时返回 None；调用方此时不要再传
    executable_path，让 playwright 回退使用自带 Chromium。
    """
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
                
    # 无系统 Chrome/Chromium：返回 None，调用方改用 playwright 自带 Chromium
    return None

if __name__ == "__main__":
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Assets Dir:   {ASSETS_DIR}")
    print(f"Fonts Dir:    {FONTS_DIR}")
    _chrome = resolve_chrome_path()
    print("Detected Chrome: " + (_chrome if _chrome else "(未找到系统 Chrome，将使用 playwright 自带 Chromium)"))
