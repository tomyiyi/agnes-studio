"""
Agnes Studio - 专业级中文字体排印学与网格系统引擎 (Typography & Grid Engine)
=============================================================================
理论与工程规范吸收自全网权威排印规范与经典设计哲学：
1. sparanoid/chinese-copywriting-guidelines (中文文案排版指北 / 盘古之白)
2. sivan/heti (赫蹏现代中文排印框架 / 标点挤压与基线网格)
3. Josef Müller-Brockmann (瑞士国际主义平面设计风格 / 栅格系统与模块化字阶)
4. 书生·电影感封面与色块排版实战法则 (负空间借力、双向错位拆字、极端字阶对比)
"""

import re
import math
from typing import List, Dict, Tuple, Optional, Any

# =============================================================================
# 一、中西文混排规范与盘古之白 (Pangu Spacing & Punctuation)
# =============================================================================

class ChineseTypographyRules:
    """中文文案排版与标点符号规范化处理器"""
    
    # CJK 汉字正则范围
    CJK_REGEX = r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]'
    # 半角英数与常见拉丁符号 (含 %, $, #, @ 等)
    LATIN_REGEX = r'[a-zA-Z0-9%#$@&+=]'
    
    @classmethod
    def apply_pangu_spacing(cls, text: str) -> str:
        """
        盘古之白 (Pangu Spacing)：
        在汉字和半角英文、数字、符号之间插入 1 个标准四分之一字宽空格 (0.25em)。
        在汉字和全角标点符号之间严禁插入空格。
        """
        if not text:
            return ""
        
        # 汉字紧接半角英文/数字/符号 -> 加空格
        text = re.sub(f'({cls.CJK_REGEX})({cls.LATIN_REGEX})', r'\1 \2', text)
        # 半角英文/数字/符号紧接汉字 -> 加空格
        text = re.sub(f'({cls.LATIN_REGEX})({cls.CJK_REGEX})', r'\1 \2', text)
        
        # 清理多余连续空格
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()

    @classmethod
    def normalize_quotes_and_brackets(cls, text: str, style: str = "corner") -> str:
        """
        规范化引号与括号：
        电影海报与艺术封面设计中，推荐使用直角引号「」与『』，
        替代传统曲线引号“”，消除视觉重力失衡与突兀倾斜。
        """
        if style == "corner":
            # 将外层双引号替换为直角引号「」
            text = re.sub(r'["“](.*?)[”"]', r'「\1」', text)
            # 将内层单引号替换为双直角引号『』
            text = re.sub(r"['‘](.*?)['’]", r'『\1』', text)
        return text

    @classmethod
    def squeeze_punctuation(cls, text: str) -> str:
        """
        标点挤压规则 (借鉴赫蹏 Heti)：
        连续的全角标点（如逗号+后引号、句号+后引号）会留下大块空白窟窿，
        在紧凑排版中需合并处理或缩减留白。
        """
        text = re.sub(r'([，。！？；：])\s*([」』”’])', r'\1\2', text)
        text = re.sub(r'([「『“‘])\s*([，。！？；：])', r'\1\2', text)
        return text

    @classmethod
    def format_poster_copy(cls, text: str) -> str:
        """一站式海报文案格式化"""
        text = cls.normalize_quotes_and_brackets(text)
        text = cls.squeeze_punctuation(text)
        text = cls.apply_pangu_spacing(text)
        return text


# =============================================================================
# 二、模块化字阶系统 (Modular Scale Ratio System)
# =============================================================================

class ModularScale:
    """
    模块化字阶生成器 (Modular Scale):
    严禁随意设置字号！文字层级必须严格遵循音程/几何级数递进。
    """
    RATIOS = {
        "golden": 1.618,         # 黄金分割率 (强视觉冲击力电影大片封面)
        "perfect_fifth": 1.500,  # 纯五度 (气势雄壮的戏剧与杂志封面)
        "augmented_fourth": 1.414,# 增四度 (严谨现代科技风格)
        "perfect_fourth": 1.333, # 纯四度 (经典版式与书籍杂志最均衡比例)
        "major_third": 1.250,    # 大三度 (致密卡片与信息图表)
        "minor_third": 1.200,    # 小三度 (微型 UI 与标签系统)
    }

    def __init__(self, base_size: float = 16.0, ratio_name: str = "golden"):
        self.base = base_size
        self.ratio = self.RATIOS.get(ratio_name, 1.618)
        self.ratio_name = ratio_name

    def step(self, n: int) -> int:
        """计算第 n 阶字号 (向下取整保持清晰像素)"""
        return int(round(self.base * (self.ratio ** n)))

    def get_poster_hierarchy(self) -> Dict[str, int]:
        """
        获取经典海报层级阶梯：
        - mega: 极大幅主字标 (比主标题更高阶，常用于底纹或破格字)
        - h1: 主标题 (Title)
        - h2: 副标题 (Subtitle)
        - h3: 章节/金句 (Section / Quote)
        - body: 正文/诗文 (Body Text)
        - tag: 标签/分类 (Kicker / Tag)
        - micro: 胶片注记/元数据 (Credits / Metadata)
        """
        if self.ratio >= 1.5:
            # 高对比度模式 (电影海报大片)
            return {
                "mega": self.step(4),   # 如 base=16, r=1.618 -> 109pt
                "h1": self.step(3),     # -> 68pt
                "h2": self.step(2),     # -> 42pt
                "h3": self.step(1),     # -> 26pt
                "body": self.step(0),   # -> 16pt (Base)
                "tag": self.step(-1),   # -> 10pt
                "micro": max(9, self.step(-2)), # -> 9~10pt
            }
        else:
            # 均衡平滑模式 (画册/画报/信息图)
            return {
                "mega": self.step(5),
                "h1": self.step(4),
                "h2": self.step(3),
                "h3": self.step(2),
                "body": self.step(1),
                "tag": self.step(0),
                "micro": max(9, self.step(-1)),
            }


# =============================================================================
# 三、瑞士国际网格系统与版面基线 (Swiss Grid & Baseline Rhythm)
# =============================================================================

class SwissGridSystem:
    """
    瑞士国际主义网格系统：
    通过栏网格 (Column Grid) 与基线网格 (Baseline Grid) 规范空间，
    确保所有视觉元素都有明确的对齐参考线，消除“乱摆乱放”。
    """
    def __init__(self, canvas_width: int, canvas_height: int, columns: int = 12, margin_ratio: float = 0.06):
        self.width = canvas_width
        self.height = canvas_height
        self.columns = columns
        
        # 页面安全边距 (Margins)
        self.margin_x = int(canvas_width * margin_ratio)
        self.margin_y = int(canvas_height * margin_ratio)
        
        # 净版心宽高
        self.content_w = canvas_width - 2 * self.margin_x
        self.content_h = canvas_height - 2 * self.margin_y
        
        # 栏间距 (Gutter) 与栏宽 (Column Width)
        # 栏间距通常为字号的 1~1.5 倍，取整
        self.gutter = int(canvas_width * 0.018)
        total_gutter_w = (columns - 1) * self.gutter
        self.col_w = (self.content_w - total_gutter_w) / columns
        
        # 垂直基线韵律 (Vertical Rhythm Unit)
        # 以 8px 或 12px 为基本网格微单元 (8-pt Grid)
        self.baseline_unit = int(round(canvas_height / 128.0))  # 1024 -> 8px

    def get_column_rect(self, col_start: int, col_span: int) -> Tuple[int, int]:
        """计算起始栏与跨栏的水平起始坐标与总宽度 (0-indexed)"""
        col_start = max(0, min(col_start, self.columns - 1))
        col_span = max(1, min(col_span, self.columns - col_start))
        
        x = int(self.margin_x + col_start * (self.col_w + self.gutter))
        w = int(col_span * self.col_w + (col_span - 1) * self.gutter)
        return x, w

    def snap_to_baseline(self, y: int) -> int:
        """将任意垂直坐标吸附至最近的基线网格上"""
        return int(round(y / self.baseline_unit) * self.baseline_unit)

    def get_layout_zones(self) -> Dict[str, Tuple[int, int, int, int]]:
        """
        预设经典海报功能区定义 (x, y, w, h)：
        - top_banner: 顶部天头通栏
        - left_col: 左侧立轴环境区 (跨 3~4 栏)
        - right_col: 右侧落款立轴区 (跨 3~4 栏)
        - center_corridor: 中间主体展示走廊 (跨 4~6 栏，严禁横排大字侵占)
        - bottom_credits: 底部地脚元数据栏
        """
        x_left, w_left = self.get_column_rect(0, 4)
        x_right, w_right = self.get_column_rect(8, 4)
        x_center, w_center = self.get_column_rect(3, 6)
        
        return {
            "top_banner": (self.margin_x, self.margin_y, self.content_w, int(self.height * 0.15)),
            "left_col": (x_left, int(self.height * 0.12), w_left, int(self.height * 0.75)),
            "right_col": (x_right, int(self.height * 0.18), w_right, int(self.height * 0.70)),
            "center_corridor": (x_center, int(self.height * 0.08), w_center, int(self.height * 0.80)),
            "bottom_credits": (self.margin_x, int(self.height * 0.92), self.content_w, int(self.height * 0.05)),
        }


# =============================================================================
# 四、智能避障与对角拆字版式推导器 (Smart Anti-Collision Composer)
# =============================================================================

class SmartPosterComposer:
    """
    智能避障海报排版规划师：
    结合图像主体检测 (Exclusion Zones) 与文本语义，
    自动推导绝不挡脸、极富动态张力的最佳版式方案。
    """
    
    @staticmethod
    def plan_layout(
        image_w: int,
        image_h: int,
        exclusion_zones: List[Dict[str, float]],
        title: str,
        subtitle: str = "",
        en_title: str = ""
    ) -> Dict[str, Any]:
        """
        推导排版方案：
        输入图像尺寸与主体保护区列表 (如人脸 x_min, y_min, x_max, y_max)，
        输出各文本组件的推荐坐标、字号与对齐方式。
        """
        grid = SwissGridSystem(image_w, image_h)
        scale_sys = ModularScale(base_size=16.0 * (image_w / 1024.0), ratio_name="golden")
        h_sizes = scale_sys.get_poster_hierarchy()
        
        # 格式化文本
        title_fmt = ChineseTypographyRules.format_poster_copy(title)
        sub_fmt = ChineseTypographyRules.format_poster_copy(subtitle)
        
        # 检查人脸是否位于顶部居中区域 (y < 0.35, x 在 0.30~0.70 之间)
        has_top_center_face = False
        face_zone = None
        for z in exclusion_zones:
            mid_x = (z["x_min"] + z["x_max"]) / 2.0
            mid_y = (z["y_min"] + z["y_max"]) / 2.0
            if 0.25 <= mid_x <= 0.75 and mid_y < 0.35:
                has_top_center_face = True
                face_zone = z
                break
                
        plan = {
            "title_raw": title,
            "title_formatted": title_fmt,
            "subtitle_formatted": sub_fmt,
            "hierarchy_sizes": h_sizes,
            "grid": grid,
            "elements": []
        }
        
        if has_top_center_face:
            # 🚨 触发【两边拆字错位竖排法则】(Bilateral Split Vertical Layout)
            # 严禁居中横排！拆分为前半部在左侧，后半部在右侧稍低位置
            mid_idx = len(title_fmt) // 2
            part1 = title_fmt[:mid_idx].strip()
            part2 = title_fmt[mid_idx:].strip()
            
            # 左列放置 (Column 0, 跨 2 栏)
            lx, lw = grid.get_column_rect(0, 2)
            ly = grid.snap_to_baseline(int(image_h * 0.12))
            
            # 右列放置 (Column 10, 跨 2 栏，向下错开 1.5 个字高，形成视觉流动)
            rx, rw = grid.get_column_rect(10, 2)
            ry = grid.snap_to_baseline(int(image_h * 0.28))
            
            plan["layout_style"] = "bilateral_split_vertical"
            plan["elements"].append({
                "role": "title_part_1",
                "text": part1,
                "orientation": "vertical",
                "x": lx, "y": ly,
                "font_size": h_sizes["h1"],
                "color_scheme": "primary"
            })
            plan["elements"].append({
                "role": "title_part_2",
                "text": part2,
                "orientation": "vertical",
                "x": rx, "y": ry,
                "font_size": h_sizes["h1"],
                "color_scheme": "primary"
            })
            
            # 英文装饰对齐
            if en_title:
                plan["elements"].append({
                    "role": "en_subtitle",
                    "text": en_title.upper(),
                    "orientation": "horizontal",
                    "x": lx,
                    "y": ly + len(part1) * int(h_sizes["h1"] * 1.3) + int(12 * (image_w / 1024.0)),
                    "font_size": h_sizes["tag"],
                    "color_scheme": "accent"
                })
        else:
            # 经典顶部或左上角横向排版
            x, w = grid.get_column_rect(0, 8)
            y = grid.snap_to_baseline(int(image_h * 0.08))
            plan["layout_style"] = "top_horizontal_magazine"
            plan["elements"].append({
                "role": "title",
                "text": title_fmt,
                "orientation": "horizontal",
                "x": x, "y": y,
                "font_size": h_sizes["h1"],
                "color_scheme": "primary"
            })
            if en_title:
                plan["elements"].append({
                    "role": "en_subtitle",
                    "text": en_title.upper(),
                    "orientation": "horizontal",
                    "x": x,
                    "y": y + int(h_sizes["h1"] * 1.25),
                    "font_size": h_sizes["tag"],
                    "color_scheme": "accent"
                })

        # 底部元数据通栏 (统一对齐基线网格)
        bot_y = grid.snap_to_baseline(int(image_h * 0.93))
        plan["elements"].append({
            "role": "footer_metadata",
            "text": "AGNES 2.5 FLASH // HYBRID AI VECTOR TYPOGRAPHY // 2026 MASTER SERIES",
            "orientation": "horizontal",
            "x": grid.margin_x,
            "y": bot_y,
            "font_size": h_sizes["micro"],
            "color_scheme": "muted"
        })
        
        return plan


# =============================================================================
# 自检与测试
# =============================================================================

if __name__ == "__main__":
    print("✨ [Typography Engine] 运行字体排印与网格规则引擎自检...")
    
    # 1. 测试盘古之白与标点规范化
    raw_text = 'Agnes 2.5模型震撼发布，首创"混元矢量"排版，超越99%同类产品！'
    formatted = ChineseTypographyRules.format_poster_copy(raw_text)
    print(f"  [盘古之白测试]")
    print(f"  原始输入: {raw_text}")
    print(f"  规范输出: {formatted}")
    assert "Agnes 2.5 模型" in formatted
    assert "「混元矢量」" in formatted
    assert "99% 同类产品" in formatted
    
    # 2. 测试模块化字阶
    scale = ModularScale(base_size=16, ratio_name="golden")
    h = scale.get_poster_hierarchy()
    print(f"\n  [黄金字阶层级 (base=16pt, r=1.618)]")
    for k, v in h.items():
        print(f"    - {k:8s}: {v:3d}pt")
    assert h["h1"] == 68
    
    # 3. 测试网格系统
    grid = SwissGridSystem(1024, 1024, columns=12)
    print(f"\n  [瑞士 12 栏网格计算 (1024x1024)]")
    print(f"    - Margin X: {grid.margin_x}px, Gutter: {grid.gutter}px, Col Width: {grid.col_w:.1f}px")
    x, w = grid.get_column_rect(0, 4)
    print(f"    - 跨前 4 栏起点与宽度: x={x}px, width={w}px")
    
    # 4. 模拟避障排版
    mock_exclusion = [{"x_min": 0.45, "y_min": 0.08, "x_max": 0.55, "y_max": 0.18, "type": "face"}]
    plan = SmartPosterComposer.plan_layout(1024, 1024, mock_exclusion, "苏园惊鸿", en_title="Suzhou Classic")
    print(f"\n  [智能避障推导结果]")
    print(f"    - 决策版式: {plan['layout_style']}")
    for el in plan["elements"]:
        print(f"    - 元素 [{el['role']}]: {el['text']} (x:{el['x']}, y:{el['y']}, font_size:{el['font_size']}pt)")
        
    print("\n🎉 全部排印学自检与断言测试通过！")


class PosterTypeSystem:
    """主题呈现与字排规格（data/poster_type_system.json）。"""

    def __init__(self, path=None):
        import json
        from pathlib import Path
        p = Path(path or (Path(__file__).resolve().parent.parent / "data" / "poster_type_system.json"))
        self.spec = json.loads(p.read_text(encoding="utf-8"))

    def sizes(self, canvas_w: int = 1080):
        scale = canvas_w / 1080.0
        out = self.spec.get("render_defaults_1080x1440", {})
        return {k: {**v, "size": int(v["size"] * scale)} for k, v in out.items() if isinstance(v, dict) and "size" in v}

    def theme_mode(self, goal: str) -> str:
        mapping = {
            "ctr": "压图巨字",
            "editorial": "负空间一角",
            "brand": "中轴竖排或负空间一角",
            "story": "对角拆字",
            "vertical": "中轴竖排",
        }
        return mapping.get(goal, "负空间一角")

    def validate_copy_pair(self, title: str, latin: str, slogan: str) -> list:
        issues = []
        if len(title.replace(" ", "")) > 8:
            issues.append("主标过长，大气海报宜 ≤8 字")
        if latin and not latin.isupper():
            issues.append("西文副标建议全大写 + 宽字距")
        if len(slogan.replace(" ", "")) > 18:
            issues.append("slogan >18 字，建议砍半")
        return issues
