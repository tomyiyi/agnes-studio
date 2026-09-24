# Agnes Studio 封面设计全流程（闭环总表）

> 单一真相源。执行顺序不可跳步：**简报 → 人物 → 文字 → 排版 → 质检 → 交付**。  
> 出图入口：`scripts/cover_pipeline.py`。本文件同时列出**已覆盖 / 遗漏 / 待补**。

---

## 0. 全流程总图

```
[0 简报 Brief]  ← 变量入口，不是固定模板
    platform / goal / subject / tone / mode / copy
        ↓  cover_style.resolve_style()
[变量表]  生图提示词 · 字体栈 · 色板 · 字阶 · scrim · mode
        ↓
[1 人物]  New API 轮换生图或选图 → 抹水印 → 焦点裁切 place → 头肩门禁
[2 文字]  按 tone/subject 选字体 · 模式 diag|bignews|stack · 盘古/字数
[3 排版]  平台安全区 · tone 的 scrim/滤镜 · 10:1 字阶 · 双格式导出
        ↓
[4 QA]  布局/文案/缩略/列表遮挡模拟/对照板
[5 强制目检]
[6 命名交付]
```

**经验：生图必须走 Agnes 工作台 / New API 轮换池**（不要单 Key 直连 apihub，**不要 MiMo `image_gen`**）：
`scripts/agnes_gateway.py` → `http://127.0.0.1:3000/v1/images/generations`  
渠道池 `Agnes-Hub-01..06` 权重分流 + 熔断 + 探活；Token 在 `~/.new-api/local_key.json`。

```bash
# 按简报出变量样式
python3 scripts/cover_style.py data/briefs/xhs_fresh_ctr.json

# 经 New API 轮换生成底图
python3 scripts/agnes_gateway.py --brief data/briefs/xhs_fresh_ctr.json --out /tmp/b.png --size 1080x1440
```

---

## 0.5 简报变量（流程是骨架，变量是血肉）

| 变量 | 取值 | 影响 |
| :--- | :--- | :--- |
| `goal` | editorial / ctr / brand / story | 模式、文案语气、标题区 |
| `subject` | beauty / product / scenery / character / abstract / none | 生图提示词、字体衬线感 |
| `tone` | luxury / minimal / cyber / neo-chinese / magazine / warm / fresh | 色板、scrim、滤镜、字阶、字体栈 |
| `mode` | auto→diag / bignews / stack | 文字版式 |
| `platform` | wechat / wechat-sq / xhs / xhs-sq | 画布、place、字号 |

目录：`data/style_catalog.json`、`data/briefs/*.json`、`scripts/cover_style.py`。

### 0.6 GPT Image Prompt → Agnes 转换（2026-09-24 学习沉淀）

外部 GPT Image / MJ 词库（如飞书《100组Prompt合集》）入库前必须转换：

| 步骤 | 动作 | 示例 |
| :--- | :--- | :--- |
| 1 | 剥 MJ 参数 | `--ar 3:4 --v 6.0` → 不进 prompt |
| 2 | 画幅进 `agnes_size` | `3:4→1088x1456` `1:1→1088x1088` `16:9→2352x1008` |
| 3 | 净框后缀 | `no text, no watermark, no signature, no corner stamp, no glitch block…` |
| 4 | 需字模板例外 | 表情包/签名/多宫格 → `keep_text:true`，保留文字指令 |
| 5 | 去重合并 | 同条被滚动切开的 prompt 切片合并；错挂标题改正 |

产物：`data/gpt_image_agnes_prompts.json`  
样张：`outputs/agnes_samples/`（每条 1 张，文件名 `{id}_{slug}.png`）  
调用：`scripts/agnes_gateway.py`（New API 轮换池，**禁止 MiMo `image_gen`**）。

---

## 1. 平台规格（锁定）

| 平台码 | 平台 | 画布 | 安全区 | 遮挡/裁切带 | 人脸 place | 命令 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `wx_head` | 微信头条 | **2350×1000** 2.35:1 | 上 70% · 左右 6% | 底 25% 标题条 | (0.62, 0.42) | `--platform wechat` |
| `wx_sub` | 微信次条 | **1080×1080** 1:1 | 中央 80% | 外圈 15% | (0.58, 0.36) | `--platform wechat-sq` |
| `xhs_main` | 小红书竖版 | **1080×1440** 3:4 | 高 12%–72% · 左右 8% | 底 28% 信息栏 | (0.55, 0.34) | `--platform xhs` |
| `xhs_sq` | 小红书方图 | **1080×1080** 1:1 | 中央 84% | 底 22% | (0.55, 0.36) | `--platform xhs-sq` |

导出固定 **PNG-24 sRGB + JPEG q92**。中英/数字之间 **0.25em 盘古之白**。

```bash
python3 scripts/cover_pipeline.py --platform all --mode diag --title-zone safe
python3 scripts/cover_pipeline.py --platform xhs --mode bignews --title-zone safe

# 批量：目录内所有简报 × 四规格（含人脸自动避让）
python3 scripts/cover_pipeline.py --briefs-dir data/briefs
```

---

## 2. 人物工作流 Subject

| # | 步骤 | 动作 | 验收 / 门禁 | 状态 |
| :- | :--- | :--- | :--- | :--- |
| 1 | 简报定调 | 美女/产品/角色；横竖构图意图 | 与平台焦点一致 | 文档化 |
| 2 | 生成或采集 | **Agnes 工作台**（`agnes_gateway.py` / New API）：头肩完整 + 负空间 + 无字 | 肉眼头饰不切；**禁止 MiMo `image_gen`** | 强制 |
| 3 | 水印清理 | `patch_watermark()` | 右下高亮≈0 | ✓ 已实现 |
| 4 | 焦点裁切 | `crop_subject(..., place=)` | 质心贴 place | ✓ 已实现 |
| 5 | 头肩门禁 | `head_visible_probe()` | skin_ratio>0.06 | ✓ 已实现 |
| 6 | 布局门禁 | `verify_layout()` | 质心不贴边、place_err<0.22 | ✓ 已实现 |
| 7 | 多人避让 | `vision_subject_detector.detect_faces` | 文字不进 face box | ✗ **未接入流水线** |

**构图约定**  
- 横版：人脸右 2/3，左侧标题光域。  
- 竖版/方图：头顶 2%–6% 空气，底部 22%–28% 留信息栏。  

**反例**（本项目踩过）  
- 用 2.35:1 已裁图再切 1:1 → 贴边 + 顶切。  
- 交稿前不做目检 → 人物错位流出。

---

## 3. 文字排版工作流 Type

| # | 步骤 | 参数 | 门禁 | 状态 |
| :- | :--- | :--- | :--- | :--- |
| 1 | 文案模板 | `data/copy_templates.json` | 主标 2–4 字 ×2；slogan≤18 | ✓ 模板库已建 |
| 2 | 盘古之白 | `typography_rules.apply_pangu_spacing` | 中英不粘连 | ✓ 已接入 |
| 3 | 禁则字符 | 直角引号「」 | 禁弯引号 | ✓ validate_copy |
| 4 | 四级层级 | T1 88–148 / T2 25–35% / T3 / T4 10–14 | 10:1 字阶 | ✓ 模板内 |
| 5 | 模式 | `--mode diag` 对角拆字 / `--mode bignews` 大字报 | 金强调单字 | ✓ |
| 6 | 字体族 | 得意黑 / 宋或楷 / Mono | ≤3 族 | ✓ |
| 7 | 竖排模式 | vertical-rl 新中式主标 | — | ✗ **未实现** |

**铁律**：禁装饰色块框 / 尺寸徽标框 / 脏高斯黑影；显示体配无衬线西文，宋体配衬线西文。

---

## 4. 整体排版工作流 Layout

| # | 步骤 | 动作 | 验收 | 状态 |
| :- | :--- | :--- | :--- | :--- |
| 1 | 画布锁定 | 平台高清尺寸 | 与表一致 | ✓ |
| 2 | 安全区网格 | 标题进 safe；底带空 | danger_band 无核心信息 | ✓ |
| 3 | 负空间 | `scrim` 光域 25%–35% | 不是色块框 | ✓ |
| 4 | 人物避让 | place + 文案左区 | 不压五官 | ✓ 基础 |
| 5 | Chrome 光栅化 | `render_html` | 1200 级亚像素 | ✓ |
| 6 | 双格式导出 | `export_pair` + 交付命名 | `build_filename` | ✓ |
| 7 | 色彩主题扩展 | 莫兰迪 / 青瓷 / 纯白 | — | ✗ 仅墨金一套 |

---

## 5. 质量门禁 QA（强制）

| # | 检查 | 工具 | 不过后果 | 状态 |
| :- | :--- | :--- | :--- | :--- |
| 1 | 文案门禁 | `validate_copy` | SystemExit | ✓ |
| 2 | 布局门禁 | `verify_layout` | SystemExit | ✓ |
| 3 | 缩略可读 | `qa_thumbnail_ok`（375px） | 标记 false | ✓ |
| 4 | 微信列表遮挡 | `render_wechat_list_sim` | 人工对照 | ✓ 头条 |
| 5 | 对照板 | `build_contact_sheet` 自动产出 | 打开目检 | ✓ |
| 6 | **人工目检** | 看图：头肩/排版/水印/叠字 | **禁止交付** | 流程强制 |
| 7 | 真机列表/信息流 | 手机实机截图 | 实验收数据 | 手动 |

**目检清单（每次交稿前）**  
- [ ] 头部完整、人物是主体、不贴边  
- [ ] 无粉红/青色装饰框、无生图水印  
- [ ] **无角落小字**（规格/页码/刊头微字一律不进成图）  
- [ ] **无补丁硬边小方块**（右下角抹水印处纹理连续）  
- [ ] 主标在安全区（除非 `title-zone risk` 实验）  
- [ ] 文字不压五官；中英有间隙  
- [ ] 缩略可读；底带无核心信息  
- [ ] 文件名符合交付规范  

---

## 6. 交付命名

```
{platform_code}_{mode}_{WxH}_{YYYYMMDD}_{slug}.png
{platform_code}_{mode}_{WxH}_{YYYYMMDD}_{slug}.jpg

示例：
  wx_head_diag_2350x1000_20260923_oriental-beauty.png
  xhs_main_bignews_1080x1440_20260923_oriental-beauty.png
```

产物目录：`outputs/covers/`（含 `pipeline_report_*.json`、`_contact_*.jpg`、`*_list_sim.jpg`）。

---

## 7. 遗漏清单（按优先级）

| 优先级 | 缺口 | 影响 | 建议 |
| :--- | :--- | :--- | :--- |
| P0 | **人工目检曾被跳过** | 1:1 人物错位外流 | 流程已强制；执行时不可跳 |
| ~~P0~~ | **多人/正脸避让** | 标题压脸 | **已接入** `resolve_text_box` 自动避让 |
| ~~P1~~ | **竖排/叠字** | — | **已实现** `--mode vertical\|stack` |
| P1 | 色彩主题仅墨+金 | 高定外场景弱 | `--theme morandi\|porcelain` |
| P1 | 小红书爆款文案钩子（数字/痛点） | CTR 版式有了、钩子弱 | copy_templates 加 hook 变体 |
| ~~P2~~ | **批量简报四规格** | — | **已实现** `--briefs-dir data/briefs` |
| P2 | 真机 A/B 自动回收数据 | H1/H2 实验仍手动 | 表单回填到 `experiments/` |
| P2 | 字体加载失败兜底 | 缺字体降级丑 | CSS font-stack 已有，加探测告警 |
| P3 | 生成式底图进流水线 | 底图须走 Agnes 网关 | `--generate` → `agnes_gateway.py`；**禁用 MiMo `image_gen`** |
| P3 | learned_poster_rules 自动选版式 | 规则库未驱动 | 按 dominant_palette 推荐 mode |

---

## 8. 模块地图

| 路径 | 职责 |
| :--- | :--- |
| `scripts/cover_pipeline.py` | **总入口**：人物/文字/排版/QA/命名 |
| `scripts/cover_style.py` | **变量解析**：brief → 字体/色板/生图/模式 |
| `scripts/agnes_gateway.py` | **New API 轮换生图**（Agnes 多 Key 池） |
| `data/style_catalog.json` | subject × tone × goal 变量目录 |
| `data/briefs/*.json` | 需求简报样例 |
| `scripts/typography_rules.py` | 盘古之白、字阶、瑞士网格 |
| `scripts/vision_subject_detector.py` | macOS Vision 人脸区（待接入） |
| `data/copy_templates.json` | 文案模板与字数规则 |
| `data/learned_poster_rules.json` | 学习色板/版式规则（待驱动选型） |
| `docs/design/index.html` | 视觉规范总册 |
| `docs/WORKFLOWS.md` | 本文件，流程唯一真相源 |
| `outputs/covers/` | 交付与报告 |

---

## 9. 三条流水线一句话

1. **人物**：**New API 轮换生图**或选图 → 抹水印 → **焦点裁切 place** → 头肩+质心门禁。  
2. **文字**：简报选字体栈/模式 → 盘古 → 四级层级 → 字体≤3（竖排待补）。  
3. **整体**：tone 的 scrim/色板 → 平台安全区 → 光栅化 → 双格式命名 → **QA+强制目检**。

---

## 10. 质量事故复盘（2026-09-23 · 本轮反馈）

| 问题 | 根因 | 流程修复（已写入代码） |
| :--- | :--- | :--- |
| 2.35:1 **砍头** | 肤色质心裁切忽略发顶；head 门禁只看肤色带 | `crop_subject` 改 **Vision 人脸框** 定裁切，`y_min≥6%` 发顶 |
| **暗角过重** | `inset 120px 0.35` + 左侧 0.78 scrim | vignette→40px/0.08；scrim 只压文案侧；**暗角门禁** corners/center≥0.55 |
| **1:1 文案消失** | 人脸避让选中框宽仅 22%，字被挤出 `overflow:hidden` | 候选框 **最小宽 34%**，标题 1:1 字阶 72px |
| 亮底字不可读 | 米字打在奶油底 | `pick_text_colors()` 亮底→墨字+浅纸帘 |
| 版式无设计感 | 简单叠字 | 对角拆字 + 发丝线 + 10:1 字阶 + 宋体 slogan |
| **未目检就交付** | 门禁过 ≠ 视觉过 | **强制 Read 成片**；对比度/头完整/暗角三门禁 |
| **右下角规格小字/水印感** | 模板自带 `.meta`/`.folio`/`.kicker` 角标 | **交付成图删除全部角落小字**；只保留主标/英文/口号 |
| **补丁留下硬边小方块** | `patch_watermark` 矩形贴块 + 硬边羽化 | 改 **椭圆高斯羽化 + 环形均值色匹配**；禁止直角贴块 |
| 生图自带右下角水印 | 提示词未压死 signature/caption | `gen_prompt` 追加 no watermark/signature/corner stamp/glitch block |

**门禁现况**：place（脸框中心）· 发顶 y_min≥3% · 人脸避让 · 文案 lint · 暗角 ratio · 缩略 · **无角落小字** · **无补丁硬边** · **人工目检**
