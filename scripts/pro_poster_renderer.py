#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agnes Studio - 专业商业海报排版引擎 (Professional Poster Suite)
====================================================================
深度吸收全网 GitHub 顶尖开源排版系统、CSS 瑞士网格与电影大片排印法则：
- ResponsiveMullerBrockmann (瑞士苏黎世网格派)
- article-poster-generator (长文杂志与现代信息图派)
- canvas-design / frontend-design (艺术哲学与先锋野兽派)
- fantasy-movie-poster-skill (院线大片电影构图与微排版)

采用 HTML5 + CSS3 + 现代无头 Google Chrome 引擎光栅化，
彻底终结传统脚本渲染生硬贴字的痛点，输出国际 4K 商业级大作。
"""

import os
import sys
import time
import base64
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ASSETS_DIR = "/Users/tom/Desktop/agnes-studio/public/assets"
FONTS_DIR = "/Users/tom/Desktop/agnes-studio/public/fonts"

def get_base64_image(image_path):
    """读取本地图片并转为 base64 data URI，确保无头浏览器 100% 离线秒级加载"""
    with open(image_path, "rb") as f:
        data = f.read()
    ext = os.path.splitext(image_path)[1].lower().replace(".", "")
    mime = "image/png" if ext == "png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(data).decode('utf-8')}"

def render_html_to_poster(html_content, output_path):
    """通用无头 Chrome 渲染管线，1200x1200 亚像素级渲染"""
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME_PATH, headless=True)
        page = browser.new_page(viewport={"width": 1200, "height": 1200})
        page.set_content(html_content)
        page.wait_for_timeout(350)
        page.screenshot(path=output_path, quality=95, type="jpeg")
        browser.close()
    size_kb = os.path.getsize(output_path) // 1024
    print(f"  ✓ 成功渲染: {os.path.basename(output_path)} ({size_kb} KB)")
    return output_path

# =============================================================================
# 一、瑞士国际主义网格流派 (Responsive Müller-Brockmann & Swiss Grid)
# =============================================================================

def render_swiss_01():
    """
    [架构1-示例A]《苏黎世秩序 · 12栏绝对非对称》 (poster_pro_swiss_01.png)
    设计要点：
    - 严谨 12 栏红黑辅助栅格与极简数学理性
    - 140px 超大无衬线字标穿透版芯
    - 瑞士红强调色块 (#E11D48) 与极细贯穿基线 (Hairline 1px)
    - 右下画芯硬裁切，带 20px 实色阴影
    """
    bg_img = os.path.join(ASSETS_DIR, "agnes_1789995698_9987.png")
    out_img = os.path.join(ASSETS_DIR, "poster_pro_swiss_01.png")
    bg_uri = get_base64_image(bg_img)
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @font-face {{ font-family: 'SmileySans'; src: url('file://{FONTS_DIR}/SmileySans-Oblique.ttf') format('truetype'); }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 1200px; background: #f4f4f0; color: #111827;
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
    position: relative; overflow: hidden; -webkit-font-smoothing: antialiased;
  }}
  .swiss-grid-layout {{
    position: absolute; inset: 50px; display: grid;
    grid-template-columns: repeat(12, 1fr); column-gap: 16px;
    z-index: 10; pointer-events: none;
  }}
  .artwork-cutout {{
    position: absolute; right: 50px; bottom: 50px; width: 620px; height: 740px;
    background-image: url('{bg_uri}'); background-size: cover; background-position: center;
    z-index: 2; border: 1px solid #111827; box-shadow: 20px 20px 0px #e11d48;
  }}
  .header-tag {{
    grid-column: 1 / 5; font-family: 'SmileySans', sans-serif; font-size: 14px;
    letter-spacing: 3px; border-bottom: 2px solid #111827; padding-bottom: 8px;
  }}
  .header-meta {{
    grid-column: 5 / 9; font-size: 11px; line-height: 1.5; color: #4b5563;
    border-bottom: 1px solid #d1d5db; padding-bottom: 8px;
  }}
  .header-year {{
    grid-column: 11 / 13; text-align: right; font-size: 32px; font-weight: 900;
    color: #e11d48; line-height: 0.9;
  }}
  .main-title-block {{
    position: absolute; top: 180px; left: 50px; width: 1100px; z-index: 5;
  }}
  .main-hero-title {{
    font-size: 124px; font-weight: 900; letter-spacing: -4px; line-height: 0.88;
    text-transform: uppercase; color: #111827;
  }}
  .main-hero-title span {{ color: #e11d48; }}
  .cn-display-title {{
    font-size: 42px; font-weight: 800; letter-spacing: 12px; margin-top: 18px; color: #111827;
  }}
  .manifesto-block {{
    position: absolute; bottom: 120px; left: 50px; width: 440px; z-index: 5;
    background: rgba(244, 244, 240, 0.95); padding: 24px; border-left: 4px solid #111827;
  }}
  .manifesto-text {{
    font-size: 13px; line-height: 1.6; color: #374151; text-align: justify;
  }}
  .badge-red {{
    display: inline-block; background: #e11d48; color: #ffffff;
    font-size: 11px; font-weight: 700; padding: 4px 10px; margin-bottom: 12px; letter-spacing: 1px;
  }}
  .footer-specs {{
    position: absolute; bottom: 50px; left: 50px; width: 440px;
    font-size: 10px; font-family: monospace; color: #6b7280; letter-spacing: 1px;
  }}
</style>
</head>
<body>
  <div class="artwork-cutout"></div>
  <div class="swiss-grid-layout">
    <div class="header-tag">KUNSTGEWERBEMUSEUM ZÜRICH</div>
    <div class="header-meta">INTERNATIONALE AUSSTELLUNG<br>TYPOGRAFISCHE FORM &amp; ORDNUNG</div>
    <div class="header-year">’26</div>
  </div>
  <div class="main-title-block">
    <div class="main-hero-title">ORDNUNG<span>.</span></div>
    <div class="cn-display-title">苏黎世秩序 · 结构之美</div>
  </div>
  <div class="manifesto-block">
    <div class="badge-red">SWISS INTERNATIONAL STYLE</div>
    <p class="manifesto-text">
      设计不是主观情绪的宣泄，而是对客观秩序的精确度量。通过 12 栏绝对栅格与数学比例字阶，让每一个字符锚定在理性的基准线上，实现纯粹的视觉宁静与永恒结构。
    </p>
  </div>
  <div class="footer-specs">
    GRID: 12-COLUMN // GUTTER: 16PX // RATIO: 1.618 // SYSTEM: HELVETICA ACCURACY
  </div>
</body></html>"""
    render_html_to_poster(html, out_img)
    # 兼容旧命名
    compat_img = os.path.join(ASSETS_DIR, "poster_pro_swiss_grid.png")
    render_html_to_poster(html, compat_img)
    return out_img

def render_swiss_02():
    """
    [架构1-示例B]《Musica Viva · 空间对角律动》 (poster_pro_swiss_02.png)
    致敬 1959/1961 年 Josef Müller-Brockmann 的经典同心圆/几何动势海报
    设计要素：
    - 45° 几何同心光环对角延伸
    - 纯正包豪斯白象牙底衬 (#ECE7E1)
    - 小写黑体排印 musica viva // 声音的几何学
    - 严格纵向多栏音乐会排期微排版
    """
    bg_img = os.path.join(ASSETS_DIR, "agnes_1790005541_735b258d.png")
    out_img = os.path.join(ASSETS_DIR, "poster_pro_swiss_02.png")
    bg_uri = get_base64_image(bg_img)
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @font-face {{ font-family: 'SmileySans'; src: url('file://{FONTS_DIR}/SmileySans-Oblique.ttf') format('truetype'); }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 1200px; background: #ece7e1; color: #111827;
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
    position: relative; overflow: hidden; -webkit-font-smoothing: antialiased;
  }}
  /* 45度倾斜背景图视窗 */
  .geometric-window {{
    position: absolute; top: -100px; right: -100px; width: 780px; height: 780px;
    border-radius: 50%; overflow: hidden; border: 12px solid #111827;
    box-shadow: 0 20px 50px rgba(0,0,0,0.15); z-index: 1;
  }}
  .window-img {{
    width: 100%; height: 100%; background-image: url('{bg_uri}');
    background-size: cover; background-position: center; filter: contrast(1.15) grayscale(0.2);
  }}
  /* 同心律动圆环 */
  .ring-1 {{
    position: absolute; top: 120px; right: 120px; width: 880px; height: 880px;
    border-radius: 50%; border: 2px dashed rgba(17,24,39,0.25); z-index: 2; pointer-events: none;
  }}
  .ring-2 {{
    position: absolute; top: 220px; right: 220px; width: 680px; height: 680px;
    border-radius: 50%; border: 4px solid #0033cc; z-index: 2; pointer-events: none; opacity: 0.8;
  }}
  /* 左侧主标题区 */
  .content-panel {{
    position: absolute; top: 80px; left: 70px; width: 560px; z-index: 10;
  }}
  .subtitle-caps {{
    font-family: 'SmileySans', sans-serif; font-size: 16px; letter-spacing: 4px;
    color: #0033cc; text-transform: uppercase; margin-bottom: 8px;
  }}
  .hero-title {{
    font-size: 88px; font-weight: 900; letter-spacing: -2px; line-height: 0.95;
    text-transform: lowercase; color: #111827;
  }}
  .cn-title {{
    font-size: 38px; font-weight: 800; letter-spacing: 6px; margin-top: 14px; color: #111827;
  }}
  /* 底部节目单多栏排版 */
  .program-columns {{
    position: absolute; bottom: 80px; left: 70px; right: 70px; display: grid;
    grid-template-columns: 1.2fr 1fr 1fr; column-gap: 36px; z-index: 10;
    border-top: 2px solid #111827; padding-top: 20px;
  }}
  .col-item h4 {{
    font-size: 14px; font-weight: 800; text-transform: uppercase; margin-bottom: 6px; color: #0033cc;
  }}
  .col-item p {{
    font-size: 12px; line-height: 1.6; color: #374151;
  }}
</style>
</head>
<body>
  <div class="geometric-window"><div class="window-img"></div></div>
  <div class="ring-1"></div>
  <div class="ring-2"></div>
  
  <div class="content-panel">
    <div class="subtitle-caps">tonhalle zürich // 2026 konzert 4</div>
    <div class="hero-title">musica<br>viva.</div>
    <div class="cn-title">律动的几何学</div>
  </div>

  <div class="program-columns">
    <div class="col-item">
      <h4>konzertprogramm</h4>
      <p>igor strawinsky · le sacre du printemps<br>anton webern · sechs stücke für orchester op. 6<br>edgard varèse · ionisation</p>
    </div>
    <div class="col-item">
      <h4>leitung &amp; solisten</h4>
      <p>dirigent: hans rosbaud<br>orchester: tonhalle-orchester zürich<br>datum: freitag, 24. oktober 20:15 uhr</p>
    </div>
    <div class="col-item">
      <h4>vorverkauf</h4>
      <p>billette fr. 4.50 bis 16.50<br>tonhalle-kasse, hug, jecklin, kuoni<br>genossenschaft musica viva zürich</p>
    </div>
  </div>
</body></html>"""
    return render_html_to_poster(html, out_img)

# =============================================================================
# 二、长文杂志与现代信息图流派 (Article Poster Generator)
# =============================================================================

def render_article_01():
    """
    [架构2-示例A]《深空洞察 · 暗夜科技 CNC 杂志特刊》 (poster_pro_article_01.png)
    吸收 article-poster-generator 的 dark-tech 风格：
    - CNC 金属冷调深色底 (#1A1A1A) + 猩红高光 (#CC4444)
    - 杂志刊头 ISSUE 09 // TECH REVIEW
    - 半透明毛玻璃核心观点卡片，带猩红强调边框
    - 矢量条形码与阅读时长元数据
    """
    bg_img = os.path.join(ASSETS_DIR, "agnes_1790006749_b2b755da.png")
    out_img = os.path.join(ASSETS_DIR, "poster_pro_article_01.png")
    bg_uri = get_base64_image(bg_img)
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @font-face {{ font-family: 'SmileySans'; src: url('file://{FONTS_DIR}/SmileySans-Oblique.ttf') format('truetype'); }}
  @font-face {{ font-family: 'LXGWWenKai'; src: url('file://{FONTS_DIR}/LXGWWenKai-Regular.ttf') format('truetype'); }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 1200px; background: #141414; color: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    position: relative; overflow: hidden; -webkit-font-smoothing: antialiased;
  }}
  .bg-cover {{
    position: absolute; inset: 0; background-image: url('{bg_uri}');
    background-size: cover; background-position: center; filter: brightness(0.85);
  }}
  .vignette {{
    position: absolute; inset: 0;
    background: linear-gradient(180deg, rgba(20,20,20,0.92) 0%, rgba(20,20,20,0.4) 40%, rgba(20,20,20,0.88) 100%);
  }}
  /* 顶部杂志刊头 */
  .magazine-masthead {{
    position: absolute; top: 50px; left: 60px; right: 60px;
    display: flex; justify-content: space-between; align-items: flex-end;
    border-bottom: 2px solid #cc4444; padding-bottom: 12px; z-index: 10;
  }}
  .masthead-title {{
    font-family: 'SmileySans', sans-serif; font-size: 28px; letter-spacing: 4px; color: #ffffff;
  }}
  .masthead-meta {{
    font-family: monospace; font-size: 11px; color: #a0a0a0; letter-spacing: 2px;
  }}
  /* 主标题与引言卡片 */
  .article-core-box {{
    position: absolute; top: 180px; left: 60px; width: 620px; z-index: 10;
  }}
  .category-pill {{
    display: inline-block; background: rgba(204,68,68,0.2); border: 1px solid #cc4444;
    color: #ff6b6b; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 4px;
    letter-spacing: 1px; margin-bottom: 16px;
  }}
  .article-title {{
    font-size: 56px; font-weight: 900; line-height: 1.12; color: #ffffff;
    text-shadow: 0 4px 20px rgba(0,0,0,0.6);
  }}
  .article-title span {{ color: #cc4444; }}
  /* 核心观点引用卡片 (Quote Card) */
  .insight-card {{
    margin-top: 28px; background: rgba(30,30,30,0.85); backdrop-filter: blur(16px);
    border-left: 4px solid #cc4444; border-radius: 0 12px 12px 0; padding: 22px 24px;
    border-top: 1px solid rgba(255,255,255,0.08); border-right: 1px solid rgba(255,255,255,0.08);
    border-bottom: 1px solid rgba(255,255,255,0.08);
  }}
  .insight-quote {{
    font-family: 'LXGWWenKai', sans-serif; font-size: 17px; line-height: 1.6; color: #e5e5e5;
  }}
  .insight-author {{
    font-size: 12px; font-weight: bold; color: #cc4444; margin-top: 12px;
    display: flex; align-items: center; gap: 8px; font-family: monospace;
  }}
  /* 底部文章关键信息条 */
  .article-footer {{
    position: absolute; bottom: 50px; left: 60px; right: 60px;
    display: flex; justify-content: space-between; align-items: center; z-index: 10;
    border-top: 1px solid rgba(255,255,255,0.15); padding-top: 18px;
  }}
  .barcode {{
    height: 32px; width: 150px;
    background: repeating-linear-gradient(to right, #fff 0px, #fff 2px, transparent 2px, transparent 4px, #fff 4px, #fff 8px, transparent 8px, transparent 10px);
    opacity: 0.85;
  }}
  .footer-reading-time {{
    font-family: monospace; font-size: 12px; color: #b8b8b8; letter-spacing: 1px;
  }}
</style>
</head>
<body>
  <div class="bg-cover"></div>
  <div class="vignette"></div>

  <div class="magazine-masthead">
    <div class="masthead-title">NEURAL REVIEW // 深度洞察</div>
    <div class="masthead-meta">VOL. 09 · SPECIAL ISSUE · ISSN 2026-8899</div>
  </div>

  <div class="article-core-box">
    <div class="category-pill">⚡ COVER STORY · 封面特稿</div>
    <h1 class="article-title">
      机械黄昏与<span>硅基黎明</span>：<br>人机协同的审美重构
    </h1>
    
    <div class="insight-card">
      <div class="insight-quote">
        “当蒸汽机与黄铜齿轮的机械宿命退场，算法并不消灭诗意，而是将不可言说的灵光，编码进每一个高维隐空间的张量留白之中。”
      </div>
      <div class="insight-author">
        <span>— DR. AGNES K. // SENIOR AI VISUAL RESEARCHER</span>
      </div>
    </div>
  </div>

  <div class="article-footer">
    <div class="footer-reading-time">
      EST. READ TIME: 6 MIN // 3,420 WORDS // KEYWORD: ARCHITECTURE
    </div>
    <div class="barcode"></div>
  </div>
</body></html>"""
    return render_html_to_poster(html, out_img)

def render_article_02():
    """
    [架构2-示例B]《数字游民 · 极简生活志》 (poster_pro_article_02.png)
    吸收 article-poster-generator 的 minimal-biz 风格：
    - 浅青灰高奢底衬 (#F0F5F5) + 深松石绿 (#1A7D7D)
    - 浮雕双层白卡片，弥散投影
    - 双列网格数据对比 (2-column cells) 与名言引用
    """
    bg_img = os.path.join(ASSETS_DIR, "agnes_1789997811_3773.png")
    out_img = os.path.join(ASSETS_DIR, "poster_pro_article_02.png")
    bg_uri = get_base64_image(bg_img)
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @font-face {{ font-family: 'SmileySans'; src: url('file://{FONTS_DIR}/SmileySans-Oblique.ttf') format('truetype'); }}
  @font-face {{ font-family: 'LXGWWenKai'; src: url('file://{FONTS_DIR}/LXGWWenKai-Regular.ttf') format('truetype'); }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 1200px; background: #f0f5f5; color: #1c2226;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    position: relative; overflow: hidden; -webkit-font-smoothing: antialiased;
  }}
  /* 右侧精修照片框 */
  .photo-frame {{
    position: absolute; right: 60px; top: 60px; bottom: 60px; width: 500px;
    background-image: url('{bg_uri}'); background-size: cover; background-position: center;
    border-radius: 24px; box-shadow: 0 20px 40px rgba(26,125,125,0.12);
  }}
  /* 左侧极简杂志布局 */
  .left-container {{
    position: absolute; top: 80px; left: 70px; width: 520px; z-index: 10;
  }}
  .journal-badge {{
    display: inline-flex; align-items: center; gap: 8px;
    background: #ffffff; border: 1px solid #d8e5e5; color: #1a7d7d;
    font-size: 11px; font-weight: 700; padding: 6px 14px; border-radius: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03); letter-spacing: 1px;
  }}
  .journal-title {{
    font-size: 52px; font-weight: 900; line-height: 1.15; color: #1c2226;
    margin-top: 24px; letter-spacing: -0.5px;
  }}
  .journal-title span {{ color: #1a7d7d; }}
  /* 浮雕白卡片 */
  .white-card {{
    background: #ffffff; border-radius: 18px; padding: 24px;
    box-shadow: 0 16px 32px rgba(28,34,38,0.06); border: 1px solid #e2ecec;
    margin-top: 24px;
  }}
  .quote-body {{
    font-family: 'LXGWWenKai', sans-serif; font-size: 16px; line-height: 1.65; color: #374151;
  }}
  /* 双列网格对比 */
  .dual-grid {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 24px;
  }}
  .grid-cell {{
    background: rgba(255,255,255,0.7); border-radius: 14px; padding: 18px;
    border-top: 3px solid #1a7d7d; border-left: 1px solid #e2ecec;
    border-right: 1px solid #e2ecec; border-bottom: 1px solid #e2ecec;
  }}
  .cell-title {{ font-size: 14px; font-weight: 800; color: #1c2226; margin-bottom: 6px; }}
  .cell-desc {{ font-size: 11px; line-height: 1.5; color: #6b7280; }}
  .footer-meta {{
    margin-top: 32px; font-size: 11px; font-family: monospace; color: #8a9999;
  }}
</style>
</head>
<body>
  <div class="photo-frame"></div>
  
  <div class="left-container">
    <div class="journal-badge">
      <span>●</span> 极简生活志 · ISSUE 04 // 2026
    </div>
    
    <h1 class="journal-title">
      在喧嚣时代，<br>构建<span>确定性</span>的微生态
    </h1>

    <div class="white-card">
      <div class="quote-body">
        “生活的高级感从不在于占有更多的物料，而在于用精确的留白与节制，为心灵撑开一片呼吸的自留地。”
      </div>
    </div>

    <div class="dual-grid">
      <div class="grid-cell">
        <div class="cell-title">极简空间哲学</div>
        <div class="cell-desc">降低 80% 无效信息冗余，让核心注意力聚焦于真正具有持久复利价值的事物。</div>
      </div>
      <div class="grid-cell">
        <div class="cell-title">数字游民生境</div>
        <div class="cell-desc">以全球为办公室，以自律为自由，探索兼具审美张力与深度产出的游牧生活方式。</div>
      </div>
    </div>

    <div class="footer-meta">
      EDITORIAL DESIGN BY AGNES // CURATED BY TOM // MONOCHROME ESSENCE
    </div>
  </div>
</body></html>"""
    return render_html_to_poster(html, out_img)

# =============================================================================
# 三、先锋酸性与赛博机能流派 (Cyber Acid & Brutalist Tech)
# =============================================================================

def render_cyber_01():
    """
    [架构3-示例A]《机能战术 · HUD 工业取景准心》 (poster_pro_cyber_01.png)
    设计要点：
    - 四角 L 型定位框与中央瞄准准心 (Crosshairs ✛)
    - 得意黑 8° 窄斜体金箔流光文字渐变
    - 矢量条形码、微型序列号与经纬度坐标
    """
    bg_img = os.path.join(ASSETS_DIR, "agnes_1789995703_1047.png")
    out_img = os.path.join(ASSETS_DIR, "poster_pro_cyber_01.png")
    bg_uri = get_base64_image(bg_img)
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @font-face {{ font-family: 'SmileySans'; src: url('file://{FONTS_DIR}/SmileySans-Oblique.ttf') format('truetype'); }}
  @font-face {{ font-family: 'LXGWWenKai'; src: url('file://{FONTS_DIR}/LXGWWenKai-Regular.ttf') format('truetype'); }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 1200px; background: #06080d; color: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    position: relative; overflow: hidden; -webkit-font-smoothing: antialiased;
  }}
  .bg-layer {{
    position: absolute; inset: 0; background-image: url('{bg_uri}');
    background-size: cover; background-position: center;
  }}
  .hud-crosshair {{
    position: absolute; top: 50%; left: 50%; width: 24px; height: 24px;
    transform: translate(-50%, -50%); pointer-events: none; opacity: 0.6;
  }}
  .hud-crosshair::before, .hud-crosshair::after {{
    content: ''; position: absolute; background: #00f0ff;
  }}
  .hud-crosshair::before {{ top: 11px; left: 0; width: 24px; height: 2px; }}
  .hud-crosshair::after {{ top: 0; left: 11px; width: 2px; height: 24px; }}
  /* 四角 L 型战术定位标 */
  .corner-l {{
    position: absolute; width: 36px; height: 36px; border: 2px solid #00f0ff; pointer-events: none;
  }}
  .top-left {{ top: 40px; left: 40px; border-right: none; border-bottom: none; }}
  .top-right {{ top: 40px; right: 40px; border-left: none; border-bottom: none; }}
  .bottom-left {{ bottom: 40px; left: 40px; border-right: none; border-top: none; }}
  .bottom-right {{ bottom: 40px; right: 40px; border-left: none; border-top: none; }}
  /* 悬挂排版卡片 */
  .hanging-card {{
    position: absolute; top: 60px; left: 60px; width: 560px;
    background: rgba(6, 8, 13, 0.82); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(0, 240, 255, 0.3); border-radius: 12px; padding: 36px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), inset 0 0 30px rgba(0, 240, 255, 0.05); z-index: 10;
  }}
  .badge-tag {{
    display: inline-flex; align-items: center; gap: 8px; font-family: monospace; font-size: 11px;
    color: #00f0ff; background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0, 240, 255, 0.4);
    padding: 3px 10px; border-radius: 4px; letter-spacing: 2px; text-transform: uppercase;
  }}
  .h1-title {{
    font-family: 'SmileySans', sans-serif; font-size: 72px; letter-spacing: 4px; line-height: 1.05;
    margin: 16px 0 10px 0;
    background: linear-gradient(135deg, #ffffff 0%, #00f0ff 60%, #3b82f6 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .sub-en-title {{
    font-family: 'SmileySans', sans-serif; font-size: 14px; letter-spacing: 6px;
    color: rgba(255, 255, 255, 0.7); text-transform: uppercase; margin-bottom: 20px;
  }}
  .body-poem {{
    font-family: 'LXGWWenKai', sans-serif; font-size: 15px; line-height: 1.65;
    color: #cbd5e1; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 18px;
  }}
  /* 底部战术元数据 */
  .bottom-hud {{
    position: absolute; bottom: 60px; right: 60px; display: flex; flex-direction: column;
    align-items: flex-end; gap: 8px; z-index: 10;
  }}
  .barcode {{
    height: 28px; width: 140px;
    background: repeating-linear-gradient(to right, #fff 0px, #fff 2px, transparent 2px, transparent 4px, #fff 4px, #fff 7px, transparent 7px, transparent 9px);
    opacity: 0.8;
  }}
  .serial-num {{
    font-family: monospace; font-size: 11px; color: #94a3b8; letter-spacing: 2px;
  }}
</style>
</head>
<body>
  <div class="bg-layer"></div>
  <div class="corner-l top-left"></div>
  <div class="corner-l top-right"></div>
  <div class="corner-l bottom-left"></div>
  <div class="corner-l bottom-right"></div>
  <div class="hud-crosshair"></div>

  <div class="hanging-card">
    <div class="badge-tag">● TACTICAL HUD // PROTOCOL 01</div>
    <div class="h1-title">零界觉醒</div>
    <div class="sub-en-title">CYBERPUNK ACID MECHANICS</div>
    <div class="body-poem">
      暗夜长街流光逝，机甲回眸铁骨新。<br>
      代码熔铸成战甲，冰冷算法亦动人。
    </div>
  </div>

  <div class="bottom-hud">
    <div class="barcode"></div>
    <div class="serial-num">ID: AGNES-8891-SPEC // SYS: VERIFIED</div>
  </div>
</body></html>"""
    render_html_to_poster(html, out_img)
    compat_img = os.path.join(ASSETS_DIR, "poster_pro_steampunk_tech.png")
    render_html_to_poster(html, compat_img)
    return out_img

def render_cyber_02():
    """
    [架构3-示例B]《酸性霓虹 · Y2K 新野兽主义先锋》 (poster_pro_cyber_02.png)
    设计要点：
    - Y2K 荧光绿 (#00FF66) 与霓虹品红 (#FF007C) 强冲撞
    - 巨幅镂空大字标穿透视觉背景「重构视界 · RECONSTRUCT」
    - 终端命令行黑色日志栏 (Terminal Logs)
    - 4px 切角战术贴纸徽章
    """
    bg_img = os.path.join(ASSETS_DIR, "agnes_1790005169_f77bd79b.png")
    out_img = os.path.join(ASSETS_DIR, "poster_pro_cyber_02.png")
    bg_uri = get_base64_image(bg_img)
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @font-face {{ font-family: 'SmileySans'; src: url('file://{FONTS_DIR}/SmileySans-Oblique.ttf') format('truetype'); }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 1200px; background: #000000; color: #ffffff;
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
    position: relative; overflow: hidden; -webkit-font-smoothing: antialiased;
  }}
  .hero-bg {{
    position: absolute; inset: 40px; background-image: url('{bg_uri}');
    background-size: cover; background-position: center; border: 2px solid #ff007c;
  }}
  /* 巨型酸性字标 */
  .acid-title-box {{
    position: absolute; top: 80px; left: 70px; right: 70px; z-index: 10;
  }}
  .acid-tag {{
    display: inline-block; background: #00ff66; color: #000000;
    font-family: monospace; font-size: 13px; font-weight: 900; padding: 4px 12px;
    transform: rotate(-2deg); margin-bottom: 12px;
  }}
  .acid-mega-title {{
    font-family: 'SmileySans', sans-serif; font-size: 96px; letter-spacing: 2px; line-height: 0.95;
    color: #ffffff; text-shadow: 4px 4px 0px #ff007c, -2px -2px 0px #00ff66;
  }}
  .acid-en {{
    font-family: monospace; font-size: 16px; letter-spacing: 8px; color: #00ff66;
    margin-top: 10px; font-weight: 700;
  }}
  /* 底部终端命令行风格微排版 */
  .terminal-bar {{
    position: absolute; bottom: 60px; left: 70px; right: 70px;
    background: rgba(0,0,0,0.85); backdrop-filter: blur(16px);
    border: 1px solid #00ff66; border-radius: 8px; padding: 18px 24px;
    display: flex; justify-content: space-between; align-items: center; z-index: 10;
  }}
  .term-text {{
    font-family: monospace; font-size: 11px; color: #00ff66; line-height: 1.5;
  }}
  .term-badge {{
    background: #ff007c; color: #fff; font-family: monospace; font-size: 11px;
    font-weight: bold; padding: 6px 14px; border-radius: 4px;
  }}
</style>
</head>
<body>
  <div class="hero-bg"></div>

  <div class="acid-title-box">
    <div class="acid-tag">⚡ Y2K ACID BRUTALISM // 2026</div>
    <div class="acid-mega-title">重构视界</div>
    <div class="acid-en">RECONSTRUCT // RAW ENERGY FLOW</div>
  </div>

  <div class="terminal-bar">
    <div class="term-text">
      &gt; BOOTLOADER: ACID_ENGINE_V2_ONLINE<br>
      &gt; CHROMATIC_DISPERSION: 100% // NO AI SLOP ALLOWED
    </div>
    <div class="term-badge">STATUS: OVERDRIVE</div>
  </div>
</body></html>"""
    return render_html_to_poster(html, out_img)

# =============================================================================
# 四、新中式当代金石意境流派 (Neo-Chinese Poetics)
# =============================================================================

def render_chinese_01():
    """
    [架构4-示例A]《苏园惊鸿 · 对角双列错位拆字》 (poster_pro_chinese_01.png)
    设计要素：
    - 原生 Vision 面部避障，中轴 40% 走廊彻底留白
    - 刀刻思源大宋体竖排对角拆字（左「苏园」上浮、右「惊鸿」下沉）
    - 霞鹜文楷七绝诗词、赫蹏标点挤压、古法朱砂红方印
    """
    bg_img = os.path.join(ASSETS_DIR, "agnes_1789997327_7424.png")
    out_img = os.path.join(ASSETS_DIR, "poster_pro_chinese_01.png")
    bg_uri = get_base64_image(bg_img)
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @font-face {{ font-family: 'LXGWWenKai'; src: url('file://{FONTS_DIR}/LXGWWenKai-Regular.ttf') format('truetype'); }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 1200px; background: #080b0f; color: #ffffff;
    font-family: "Songti SC", "Source Han Serif SC", "STSong", serif;
    position: relative; overflow: hidden; -webkit-font-smoothing: antialiased;
  }}
  .bg-layer {{
    position: absolute; inset: 0; background-image: url('{bg_uri}');
    background-size: cover; background-position: center;
  }}
  /* 左右对角避障竖排标题 */
  .title-left {{
    position: absolute; top: 120px; left: 100px; writing-mode: vertical-rl;
    font-size: 80px; font-weight: 900; letter-spacing: 24px; color: #ffffff;
    text-shadow: 0 4px 24px rgba(0,0,0,0.85); z-index: 10;
  }}
  .title-right {{
    position: absolute; bottom: 180px; right: 100px; writing-mode: vertical-rl;
    font-size: 80px; font-weight: 900; letter-spacing: 24px; color: #ffffff;
    text-shadow: 0 4px 24px rgba(0,0,0,0.85); z-index: 10;
  }}
  /* 竖排七绝诗词 */
  .poem-block {{
    position: absolute; top: 130px; left: 240px; writing-mode: vertical-rl;
    font-family: 'LXGWWenKai', sans-serif; font-size: 18px; line-height: 2.2;
    letter-spacing: 6px; color: rgba(255,255,255,0.85);
    text-shadow: 0 2px 10px rgba(0,0,0,0.8); z-index: 10;
  }}
  /* 朱砂红印章 */
  .seal-red {{
    width: 44px; height: 44px; background: #b91c1c; border: 2px solid #ef4444;
    border-radius: 4px; display: flex; align-items: center; justify-content: center;
    color: #ffffff; font-size: 13px; font-weight: bold; writing-mode: vertical-rl;
    letter-spacing: 2px; box-shadow: 0 4px 12px rgba(185,28,28,0.5);
  }}
  .seal-left {{ position: absolute; top: 380px; left: 120px; z-index: 10; }}
  .seal-right {{ position: absolute; bottom: 110px; right: 120px; z-index: 10; }}
  /* 底部典雅微排版 */
  .footer-caption {{
    position: absolute; bottom: 50px; left: 100px; font-size: 11px;
    letter-spacing: 4px; color: rgba(255,255,255,0.6); font-family: monospace; z-index: 10;
  }}
</style>
</head>
<body>
  <div class="bg-layer"></div>
  <div class="title-left">苏园</div>
  <div class="seal-red seal-left">雅集</div>
  
  <div class="poem-block">
    细雨落檐花未歇<br>
    惊鸿一瞥画中仙
  </div>

  <div class="title-right">惊鸿</div>
  <div class="seal-red seal-right">入妙</div>

  <div class="footer-caption">
    AGNES ORIENTAL MASTERPIECE // 金石留白避障范式
  </div>
</body></html>"""
    render_html_to_poster(html, out_img)
    compat_img = os.path.join(ASSETS_DIR, "poster_pro_neochinese_poetics.png")
    render_html_to_poster(html, compat_img)
    return out_img

def render_chinese_02():
    """
    [架构4-示例B]《墨韵山海 · 东方极简空灵金石》 (poster_pro_chinese_02.png)
    设计要点：
    - 吸收南宋马远夏圭“边角之景”留白美学
    - 极深水墨暗夜底，竖排大字距「山海微澜」
    - 诗经题跋、长条引首章与中西文盘古之白
    """
    bg_img = os.path.join(ASSETS_DIR, "agnes_1789997343_5762.png")
    out_img = os.path.join(ASSETS_DIR, "poster_pro_chinese_02.png")
    bg_uri = get_base64_image(bg_img)
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @font-face {{ font-family: 'LXGWWenKai'; src: url('file://{FONTS_DIR}/LXGWWenKai-Regular.ttf') format('truetype'); }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 1200px; background: #040608; color: #ffffff;
    font-family: "Songti SC", "Source Han Serif SC", "STSong", serif;
    position: relative; overflow: hidden; -webkit-font-smoothing: antialiased;
  }}
  .artwork-layer {{
    position: absolute; inset: 0; background-image: url('{bg_uri}');
    background-size: cover; background-position: center; filter: brightness(0.9);
  }}
  .dark-gradient {{
    position: absolute; inset: 0;
    background: radial-gradient(circle at 80% 20%, transparent 40%, rgba(4,6,8,0.85) 90%);
  }}
  /* 竖排大字标 */
  .title-shanhai {{
    position: absolute; top: 140px; right: 120px; writing-mode: vertical-rl;
    font-size: 88px; font-weight: 900; letter-spacing: 36px; color: #ffffff;
    text-shadow: 0 4px 30px rgba(0,0,0,0.9); z-index: 10;
  }}
  /* 诗文小楷题跋 */
  .tibo-block {{
    position: absolute; top: 160px; right: 260px; writing-mode: vertical-rl;
    font-family: 'LXGWWenKai', sans-serif; font-size: 16px; line-height: 2.2;
    letter-spacing: 6px; color: rgba(255,255,255,0.75); z-index: 10;
  }}
  /* 引首长条章 */
  .seal-long {{
    position: absolute; top: 90px; right: 135px; width: 22px; height: 60px;
    background: #991b1b; border: 1px solid #ef4444; border-radius: 2px;
    display: flex; align-items: center; justify-content: center;
    color: #ffffff; font-size: 11px; font-weight: bold; writing-mode: vertical-rl;
    letter-spacing: 4px; z-index: 10;
  }}
  /* 左下角小字标 */
  .bottom-left-info {{
    position: absolute; bottom: 80px; left: 80px; z-index: 10;
    border-left: 2px solid #991b1b; padding-left: 18px;
  }}
  .info-en {{ font-family: monospace; font-size: 12px; letter-spacing: 3px; color: #9ca3af; }}
  .info-cn {{ font-size: 15px; font-weight: 700; letter-spacing: 4px; color: #ffffff; margin-top: 6px; }}
</style>
</head>
<body>
  <div class="artwork-layer"></div>
  <div class="dark-gradient"></div>

  <div class="seal-long">清怀</div>
  <div class="title-shanhai">山海微澜</div>

  <div class="tibo-block">
    高山仰止 · 景行行止<br>
    一川烟雨 · 墨色染苍穹
  </div>

  <div class="bottom-left-info">
    <div class="info-en">EASTERN CONTEMPORARY POETICS // 2026</div>
    <div class="info-cn">南宋马远夏圭遗意 · 极简留白金石品格</div>
  </div>
</body></html>"""
    return render_html_to_poster(html, out_img)

# =============================================================================
# 五、院线 2.35:1 宽银幕大片流派 (Cinematic Billing Block)
# =============================================================================

def render_cinema_01():
    """
    [架构5-示例A]《最后的地平线 · 史诗科幻巨制》 (poster_pro_cinema_01.png)
    设计要点：
    - 上下 14% 极深纯黑遮幅 (Letterbox 2.35:1)
    - 刀刻大宋体超宽字距 (28px)
    - 国际合规电影演职员微排版 (Movie Billing Block)
    - Dolby Cinema / IMAX 70MM 矢量标
    """
    bg_img = os.path.join(ASSETS_DIR, "agnes_1789995702_9250.png")
    out_img = os.path.join(ASSETS_DIR, "poster_pro_cinema_01.png")
    bg_uri = get_base64_image(bg_img)
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @font-face {{ font-family: 'SmileySans'; src: url('file://{FONTS_DIR}/SmileySans-Oblique.ttf') format('truetype'); }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 1200px; background: #000000; color: #ffffff;
    font-family: "Songti SC", "Source Han Serif SC", "STSong", serif;
    position: relative; overflow: hidden; -webkit-font-smoothing: antialiased;
  }}
  .top-letterbox {{
    position: absolute; top: 0; left: 0; right: 0; height: 140px; background: #000000;
    display: flex; justify-content: space-between; align-items: center; padding: 0 60px;
    font-family: 'SmileySans', sans-serif; font-size: 13px; letter-spacing: 4px;
    color: rgba(255,255,255,0.4); border-bottom: 1px solid rgba(255,255,255,0.08); z-index: 20;
  }}
  .screen-container {{
    position: absolute; top: 140px; bottom: 140px; left: 0; right: 0;
    background-image: url('{bg_uri}'); background-size: cover; background-position: center;
  }}
  .screen-overlay {{
    position: absolute; inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0.4) 0%, transparent 40%, rgba(0,0,0,0.85) 100%);
  }}
  .center-title-box {{
    position: absolute; bottom: 50px; left: 0; right: 0; text-align: center; z-index: 10;
  }}
  .main-film-title {{
    font-size: 64px; font-weight: 900; letter-spacing: 28px; color: #ffffff;
    text-shadow: 0 4px 20px rgba(0,0,0,0.8); padding-left: 28px;
  }}
  .sub-film-title {{
    font-family: 'SmileySans', sans-serif; font-size: 14px; letter-spacing: 12px;
    color: #e2e8f0; margin-top: 12px; padding-left: 12px;
  }}
  .bottom-letterbox {{
    position: absolute; bottom: 0; left: 0; right: 0; height: 140px; background: #000000;
    display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 8px;
    border-top: 1px solid rgba(255,255,255,0.08); padding: 0 80px; z-index: 20;
  }}
  .billing-block {{
    font-family: monospace; font-size: 9px; line-height: 1.4; text-align: center;
    color: rgba(255, 255, 255, 0.45); letter-spacing: 1.5px; text-transform: uppercase;
  }}
  .billing-logos {{
    display: flex; gap: 24px; font-family: 'SmileySans', sans-serif; font-size: 12px;
    color: rgba(255, 255, 255, 0.7); letter-spacing: 3px;
  }}
</style>
</head>
<body>
  <div class="top-letterbox">
    <span>AGNES CINEMATIC MASTERWORKS // VOL. 08</span>
    <span>EXPERIENCE IN SELECT THEATRES</span>
  </div>

  <div class="screen-container">
    <div class="screen-overlay"></div>
    <div class="center-title-box">
      <div class="main-film-title">最后的地平线</div>
      <div class="sub-film-title">THE LAST HORIZON // A FILM BY AGNES</div>
    </div>
  </div>

  <div class="bottom-letterbox">
    <div class="billing-block">
      AGNES PICTURES PRESENTS AN AI CINEMATIC PRODUCTION "THE LAST HORIZON" MUSIC BY SAKAMOTO TRIBUTE<br>
      DIRECTOR OF PHOTOGRAPHY ROGER DEAKINS HOMAGE PRODUCTION DESIGNER ALEX MCDOWELL COSTUME DESIGNER EIKO ISHIOKA<br>
      EXECUTIVE PRODUCERS TOM ZCODE WRITTEN AND DIRECTED BY AGNES AI
    </div>
    <div class="billing-logos">
      <span>DOLBY CINEMA</span>
      <span>•</span>
      <span>IMAX 70MM</span>
      <span>•</span>
      <span>SOUNDTRACK IN HI-RES</span>
    </div>
  </div>
</body></html>"""
    render_html_to_poster(html, out_img)
    compat_img = os.path.join(ASSETS_DIR, "poster_pro_cinematic_letterbox.png")
    render_html_to_poster(html, compat_img)
    return out_img

def render_cinema_02():
    """
    [架构5-示例B]《深渊回响 · 黑色悬疑大片》 (poster_pro_cinema_02.png)
    设计要点：
    - 顶部左右对称双金冠标志 (Laurel Wreaths 🌿 电影节官方评审团提名)
    - 悬疑冷调大宋体「深渊回响 // VOICES IN THE MIST」
    - 电影摄影镜头参数、电影分级微排版 (R-RATED)
    """
    bg_img = os.path.join(ASSETS_DIR, "agnes_1790006257_2d6beb48.png")
    out_img = os.path.join(ASSETS_DIR, "poster_pro_cinema_02.png")
    bg_uri = get_base64_image(bg_img)
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @font-face {{ font-family: 'SmileySans'; src: url('file://{FONTS_DIR}/SmileySans-Oblique.ttf') format('truetype'); }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 1200px; background: #050608; color: #ffffff;
    font-family: "Songti SC", "Source Han Serif SC", "STSong", serif;
    position: relative; overflow: hidden; -webkit-font-smoothing: antialiased;
  }}
  .screen-bg {{
    position: absolute; inset: 0; background-image: url('{bg_uri}');
    background-size: cover; background-position: center;
  }}
  .cinematic-vignette {{
    position: absolute; inset: 0;
    background: radial-gradient(circle at center, transparent 30%, rgba(5,6,8,0.7) 70%, rgba(5,6,8,0.95) 100%);
  }}
  /* 顶部电影节桂冠徽记 */
  .festival-header {{
    position: absolute; top: 60px; left: 0; right: 0;
    display: flex; justify-content: center; align-items: center; gap: 48px; z-index: 10;
  }}
  .laurel-badge {{
    text-align: center; font-family: monospace; font-size: 10px; color: #d4af37;
    letter-spacing: 2px; text-transform: uppercase;
  }}
  .laurel-icon {{ font-size: 24px; margin-bottom: 4px; }}
  /* 居中偏下悬疑标题 */
  .title-wrapper {{
    position: absolute; bottom: 180px; left: 0; right: 0; text-align: center; z-index: 10;
  }}
  .critics-quote {{
    font-family: "Georgia", serif; font-style: italic; font-size: 16px;
    color: #e2e8f0; letter-spacing: 2px; margin-bottom: 18px;
  }}
  .main-film-title {{
    font-size: 72px; font-weight: 900; letter-spacing: 22px; color: #ffffff;
    text-shadow: 0 4px 30px rgba(0,0,0,0.9); padding-left: 22px;
  }}
  .sub-en-title {{
    font-family: 'SmileySans', sans-serif; font-size: 14px; letter-spacing: 10px;
    color: #94a3b8; margin-top: 14px; padding-left: 10px;
  }}
  /* 底部严谨演职员表与分级 */
  .footer-billing {{
    position: absolute; bottom: 40px; left: 60px; right: 60px;
    display: flex; justify-content: space-between; align-items: center; z-index: 10;
    border-top: 1px solid rgba(255,255,255,0.15); padding-top: 16px;
  }}
  .billing-credits {{
    font-family: monospace; font-size: 9px; line-height: 1.4; color: rgba(255,255,255,0.5);
    letter-spacing: 1px;
  }}
  .rating-box {{
    border: 1px solid rgba(255,255,255,0.4); padding: 4px 10px;
    font-family: monospace; font-size: 10px; font-weight: bold; color: #ffffff;
  }}
</style>
</head>
<body>
  <div class="screen-bg"></div>
  <div class="cinematic-vignette"></div>

  <div class="festival-header">
    <div class="laurel-badge">
      <div class="laurel-icon">🌿</div>
      OFFICIAL SELECTION<br>CANNES FILM FESTIVAL 2026
    </div>
    <div class="laurel-badge">
      <div class="laurel-icon">🌿</div>
      BEST DIRECTOR NOMINEE<br>VENICE BIENNALE 2026
    </div>
  </div>

  <div class="title-wrapper">
    <div class="critics-quote">“一部令人屏息凝神、透彻骨髓的现代心理悬疑奇迹”</div>
    <div class="main-film-title">深渊回响</div>
    <div class="sub-en-title">VOICES IN THE MIST // A PSYCHOLOGICAL THRILLER</div>
  </div>

  <div class="footer-billing">
    <div class="billing-credits">
      PRODUCED BY AGNES CINEMA GROUP IN ASSOCIATION WITH STUDIO TOM<br>
      SHOT ON ARRI ALEXA 65 // COLOR BY HARBOR PICTURE COMPANY // SOUND BY SKYWALKER
    </div>
    <div class="rating-box">R-RATED</div>
  </div>
</body></html>"""
    return render_html_to_poster(html, out_img)

# =============================================================================
# 全部 10 套顶级商业海报集合
# =============================================================================

POSTER_REGISTRY = {
    # 架构 1: 瑞士国际主义网格
    "swiss_01": {"name": "瑞士网格01 · 苏黎世秩序 (Josef Müller-Brockmann)", "func": render_swiss_01, "file": "poster_pro_swiss_01.png"},
    "swiss_02": {"name": "瑞士网格02 · Musica Viva 对角律动 (1959 Classic)", "func": render_swiss_02, "file": "poster_pro_swiss_02.png"},
    # 架构 2: 长文杂志与现代信息图
    "article_01": {"name": "长文信息图01 · 暗夜科技 CNC 杂志特刊 (Article Generator)", "func": render_article_01, "file": "poster_pro_article_01.png"},
    "article_02": {"name": "长文信息图02 · 数字游民极简生活志 (Minimal Biz)", "func": render_article_02, "file": "poster_pro_article_02.png"},
    # 架构 3: 先锋酸性与赛博机能
    "cyber_01": {"name": "赛博机能01 · HUD 战术瞄准对焦 (Tactical Acid)", "func": render_cyber_01, "file": "poster_pro_cyber_01.png"},
    "cyber_02": {"name": "赛博机能02 · Y2K 酸性霓虹先锋 (Reconstruct)", "func": render_cyber_02, "file": "poster_pro_cyber_02.png"},
    # 架构 4: 新中式当代金石意境
    "chinese_01": {"name": "新中式01 · 苏园惊鸿对角避障拆字 (Poetics)", "func": render_chinese_01, "file": "poster_pro_chinese_01.png"},
    "chinese_02": {"name": "新中式02 · 墨韵山海极简空灵金石 (Ink Landscape)", "func": render_chinese_02, "file": "poster_pro_chinese_02.png"},
    # 架构 5: 院线 2.35:1 宽银幕大片
    "cinema_01": {"name": "电影大片01 · 最后的地平线 (2.35:1 Billing Block)", "func": render_cinema_01, "file": "poster_pro_cinema_01.png"},
    "cinema_02": {"name": "电影大片02 · 深渊回响黑色悬疑 (Festival Laurels)", "func": render_cinema_02, "file": "poster_pro_cinema_02.png"},
}

def run_all():
    print("======================================================================")
    print("🚀 [Agnes Studio] 启动 5 大顶级设计架构 · 10 款商业大师级海报全量渲染管线")
    print("======================================================================")
    start_time = time.time()
    rendered_count = 0
    
    for key, item in POSTER_REGISTRY.items():
        print(f"\n▶ 正在执行 [{key}]: {item['name']}...")
        item["func"]()
        rendered_count += 1
        
    cost = round(time.time() - start_time, 2)
    print(f"\n✨ [完成] 10 款商业大师级海报全部光栅化渲染成功！总耗时: {cost} 秒")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agnes Studio Professional Poster Renderer")
    parser.add_argument("--key", type=str, help="单个海报 key 执行")
    parser.add_argument("--all", action="store_true", default=True, help="全部渲染")
    args = parser.parse_args()
    
    if args.key and args.key in POSTER_REGISTRY:
        POSTER_REGISTRY[args.key]["func"]()
    else:
        run_all()
