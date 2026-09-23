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

if __name__ == "__main__":
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Assets Dir:   {ASSETS_DIR}")
    print(f"Fonts Dir:    {FONTS_DIR}")
    print(f"Detected Chrome: {resolve_chrome_path()}")
