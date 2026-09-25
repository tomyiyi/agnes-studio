# Agnes Studio · 项目总览（Project Summary）

> 最后更新：2026-09-26  
> 状态：可运行 · 持续迭代中  
> 一句话：**AI 生图（Agnes / New API）+ 真字体后期排版 + 版式系统**，专攻「大气、高级、有设计感」的商业海报。

---

## 1. 项目定位

Agnes Studio 是一套**本地可运行的海报创作与研究工作台**：

| 能力 | 说明 |
|------|------|
| 生图 | 统一走 `agnes_gateway.py` → New API `127.0.0.1:3000`，模型 `agnes-image-2.5-flash` |
| 字设 | 中文后期真字体叠字（思源宋 Black / 普惠 / 宋体），禁止扩散模型写汉字 |
| 版式 | 12 种构图系统（瑞士非对称 / 字带 / 对角 / 开窗 / 独主体 / 中轴 / 巨字…） |
| 画廊 | `public/index.html` 单页工作台，资产 1055+ 条可检索 |
| 研究 | Pinterest / 开源海报库 / 字体工程 / A-B 门禁，沉淀为 JSON 规则 |

**审美目标**：大气 · 高级感 · 电影海报级。  
**硬关系**：`BACKGROUND → TYPE → PERSON`（字在人后，被轮廓切断）。

---

## 2. 目录结构

```
agnesstudio/
├── public/index.html          # 项目页 / 画廊 / 工作台（单文件）
├── public/assets/             # 画廊静态资源（workflow_iter / skill71 / …）
├── public/fonts/              # 中文字体（思源宋、普惠、宋体、文楷、得意黑）
├── scripts/                   # 31 个 Python 工具（出图 / 合成 / 同步 / 渲染）
├── data/                      # 18 个 JSON 规则与目录（版式 / 字设 / 门禁 / 71 Skill）
├── outputs/                   # 1500+ 图像产出（约 1.4G）
├── docs/                      # 项目文档（本文件为总览）
├── experiments/               # 独立实验与质检
└── ~/.config/mimocode/skills/poster-atelier/   # 融合 Skill（§6 字在人后）
```

---

## 3. 核心工作流

### 3.1 生图铁律
- **只走 Agnes / New API**（`scripts/agnes_gateway.py`）
- 禁止 MiMo `image_gen`、禁止 Gemini 生图接口
- 本地 Key：`~/.new-api/local_key.json`
- 尺寸常用 `864x1152`；偶发 403/SSL EOF，retry 3 次可过

### 3.2 中文排版铁律
- **中文后期用真字体叠字**，不交给扩散模型写
- 字重两端：特粗 condensed 或细衬线；中间粗细平庸
- 英文 3–6 字母 / 中文 1–2 字（双字需强制 BEHIND）
- 禁：face 渐变、字效花活、教材腔分栏

### 3.3 「字在人后」Prompt 四段
```
PRIMARY    人物（占比 55–68%，脸可读）
SECONDARY  giant type as BACKDROP architecture
ABSOLUTE LAYER ORDER: BACKGROUND then TYPE then PERSON
           + 轮廓切断描述（hair/face/shoulder cuts through letterforms）
FORBIDDEN  type in front / sticker / face gradient / UI / border
```

### 3.4 封面全流程
`简报 → 人物 → 文字 → 排版 → QA → 目检 → 交付`  
入口：`scripts/cover_pipeline.py`；变量解析：`cover_style.py`。

---

## 4. 版式系统（12 + 中文精修）

### L1 · 12 种构图（`outputs/layout_variants/L1/`）
| 号 | 版式 | 用途 |
|----|------|------|
| 01/02 | 瑞士非对称 | 左字塔 + 右图窗 |
| 03/04 | 上字带 + 下图场 | 电影 / 发布 |
| 05/06 | 对角张力 | 潮流 / 运动 |
| 07/08 | 杂志开窗 | 画册 / 展览 |
| 09 | 独主体 + 大空场 | 品牌主视觉 |
| 10 | 中轴庄严 | 新中式 / 发布会 |
| 11 | 上文下图 | 电影感 |
| 12 | 巨字极简 | 大字报冲击 |

### L2 · 7/8/9 中文精修（`outputs/layout_variants/L2/`）
| 号 | 版式 | 中文主标 |
|----|------|----------|
| 13/14 | 开窗 · 竖排书脊 | 留白 / 观景 |
| 15/16 | 开窗 · 横题大窗 | 静物 / 见山 |
| 17/18 | 独主体大空场 | 独白 / 自在 |

**L2 改进**：人物放大（45%→52–62% 高度）、真字体中文、英文仅作细副行。  
**验收**：编号板报号；**L1/L2 只增不删**。

---

## 5. 产出规模（截至 2026-09-26）

| 资产 | 数量 | 路径 |
|------|------|------|
| 总图像 | **1500+** | `outputs/` |
| 字在人后迭代 | 946 张 / v1–v159 | `outputs/workflow_iter/` |
| 通宵 Pinterest 学习 | 228 | `outputs/overnight_study/` |
| 商业封面 | 84 | `outputs/covers/` |
| 71 Skill 样张 | 71 | `outputs/skill71_samples/` |
| 版式 L1+L2 | 28 | `outputs/layout_variants/` |
| 画廊 EPIC 条目 | 1055（含 wf 946） | `public/index.html` |
| Python 脚本 | 31 | `scripts/` |
| JSON 规则 | 18 | `data/` |

### 里程碑
- **v100**（17:22）：592 张 / 100 组，画廊 875
- **v150**（19:59）：892 张 / 150 组，画廊 1175
- **v159**（20:42）：946 张 / 159 组，画廊 EPIC 1055
- **L2 中文精修**（00:04）：7/8/9 六张真字体中文

---

## 6. 数据与规则库（`data/`）

| 文件 | 作用 |
|------|------|
| `poster_layout_system.json` | 4 大构图 + 微规则（外边距 ≥7%、一页一系统） |
| `poster_grand_rules.json` | 大气目标：留白 35–60%、字阶 8–16:1、60/30/10 |
| `poster_type_system.json` | 字设原则、主题落位、常见错误 |
| `poster_font_recipes.json` | 纪念碑字排配方 |
| `poster_drama_grammar.json` | 戏剧海报语法、Anti-Slop |
| `poster_gate.json` | 硬门禁 8 条 / 禁止 8 条 |
| `style_catalog.json` | 字体栈 · 主体 · 色调 · 71 skill_styles |
| `skills_71_index.json` | 71 项生图 Skill 索引（全局安装） |
| `copy_templates.json` | 文案模板与钩子 |

---

## 7. 关键脚本（`scripts/`）

| 脚本 | 职责 |
|------|------|
| `agnes_gateway.py` | **唯一出图入口**（New API 轮换） |
| `batch_type_behind.py` / `batch_type_behind_v154.py` | 字在人后批量 |
| `batch_layout_variants.py` | L1 十二种版式 |
| `batch_layout_cn_789.py` | L2 中文精修（真字体叠字） |
| `render_cn_type_poster.py` | 中文纪念碑字排（Playwright + 思源宋） |
| `cover_pipeline.py` / `cover_style.py` | 商业封面全流程 |
| `pro_poster_renderer.py` | 无头 Chrome 亚像素渲染 |
| `vision_subject_detector.py` | 人脸/主体避障 |
| `studio_server.py` | 本地工作台服务 |
| `merge_skill71_gallery.py` | 71 样张并入画廊 |
| `install_skills_71.py` | 71 Skill 全局安装 |

---

## 8. 设计规范摘要

### 色场
- **主推**：greige + cream `#F3EDE3`
- **夜景**：深墨 + cream（对比最强）
- 其它：红白 / 骨白黑 / 橙黑白 / 场地色 / 黑白

### 大气硬指标
- 留白：min 35% · sweet 45% · max 60%
- 字阶（主标:微字）：8–16:1，sweet 10:1
- 版面分配：60% 空 / 30% 内容 / 10% 装饰
- 阅读路径：0.5s 印象 → 3s 核心信息

### 字体
- 中文主标：`NotoSerifCJKsc-Black`（思源宋）/ 普惠 Heavy
- 中文副文：普惠 Medium / 文楷
- 西文：Didot / Bodoni / Futura
- 拒绝：中等粗细无性格字重、字效花活

---

## 9. 用户验收约定

1. **编号对照图报号**（如「01 05 09 12 可复用」）
2. 画廊搜索：`WF·` / `behind` / `字排` / `切字` / `大气`
3. **只增不删**：L1 基线、L2 精修、workflow_iter 全部保留
4. 中文必须真字体；英文可作细副行
5. 禁止：字在人前、face 渐变、教材腔、特效堆砌

---

## 10. 快速命令

```bash
# 生图（唯一入口）
python3 scripts/agnes_gateway.py --prompt "..." --out out.png --size 864x1152

# 字在人后批量
python3 scripts/batch_type_behind.py --words MODE,CHIC --out outputs/custom

# L1 版式 12 张
python3 scripts/batch_layout_variants.py

# L2 中文精修 7/8/9
python3 scripts/batch_layout_cn_789.py

# 启动工作台
./start.sh
```

---

## 11. 相关文档

| 文档 | 内容 |
|------|------|
| `docs/ARCHITECTURE.md` | 系统架构与设计 Token |
| `docs/WORKFLOWS.md` | 封面全流程闭环 |
| `docs/TYPOGRAPHY_AND_POSTER_DESIGN.md` | 字设与海报设计 |
| `docs/SKILLS_71_INSTALL_RECEIPT.md` | 71 Skill 安装回执 |
| `docs/POSTER_STUDY_D1.md` | 海报研究 D1 |
| `outputs/workflow_iter/WORKFLOW_RECIPE.md` | 字在人后配方 |
| `outputs/workflow_iter/EVENING_SUMMARY.md` | 晚间收敛总结 |
| `outputs/workflow_iter/COVERAGE.md` | 变量覆盖统计 |

---

## 12. 画廊精选（2026-09-26 清理）

「照片转编辑海报」原 1101 张（大量重复 + 部分字挡脸）**精选保留 36 张**：

- **删除**：字压五官（如「美」盖脸）、排版重复、损坏图、低质花活
- **保留**：GOLD 头肩切字 · L1/L2 版式 · 通宵 BEST · 中文真字体 · 字在人后 strong · 戏剧字排
- **铁律复核**：字穿轮廓=留；字挡脸=删
- 清单：`outputs/curated_skill_poster_36.json`
- 画廊现约 182 条（精选后）；文件仍存盘，只清展示

### 展示比例纪律
嵌图改为 **原生 `aspect-ratio` + `object-fit: contain`**（对齐参考页 artwork 标准），禁止固定高度硬裁。

## 12b. 下一步（可选）

1. 将 L2 中文配方接入 `cover_pipeline` 默认路径
2. 用户真实文案批量出片
3. 中文电影标题按《電影片名字體》再精修
4. A/B 门禁自动化（已在 `poster_gate.json` 雏形）

---

## 13. 图鉴（Preview）

> 同步于项目页「项目总览」页签；资源在 `public/assets/`。

### 版式 L1（`public/assets/layout_variants/L1_*.png`）
| 号 | 文件 | 版式 |
|----|------|------|
| 01 | `L1_01_swiss_asym.png` | 瑞士非对称 |
| 02 | `L1_02_swiss_asym.png` | 瑞士非对称·b |
| 03 | `L1_03_type_band.png` | 上字带下图 |
| 04 | `L1_04_type_band.png` | 上字带下图·b |
| 05 | `L1_05_axis_tension.png` | 对角张力 |
| 06 | `L1_06_axis_tension.png` | 对角张力·b |
| 07 | `L1_07_window_editorial.png` | 杂志开窗 |
| 08 | `L1_08_window_editorial.png` | 杂志开窗·b |
| 09 | `L1_09_solo_space.png` | 独主体大空场 |
| 10 | `L1_10_axis_center.png` | 中轴庄严 |
| 11 | `L1_11_text_top.png` | 上文下图 |
| 12 | `L1_12_giant_minimal.png` | 巨字极简 |

### 版式 L2 中文精修（`L2_*.png`）
| 号 | 文件 | 主标 |
|----|------|------|
| 13 | `L2_07A_CN_留白.png` | 留白 · 开窗竖排 |
| 14 | `L2_07B_CN_观景.png` | 观景 · 开窗竖排 |
| 15 | `L2_08A_CN_静物.png` | 静物 · 开窗横题 |
| 16 | `L2_08B_CN_见山.png` | 见山 · 开窗横题 |
| 17 | `L2_09A_CN_独白.png` | 独白 · 独主体 |
| 18 | `L2_09B_CN_自在.png` | 自在 · 独主体 |

### 字在人后样张（`public/assets/workflow_iter/`）
- `r159_strong_mode.png` · strong MODE
- `r157_cn_qing.png` · 中文双字 清欢
- `r158_silh.png` · 英文长词 SILHOUETTE
- `r155_nite.png` · 夜景 NITE

### 编号板
- `outputs/layout_variants/L1/LAYOUT_NUMBERED_12.jpg`
- `outputs/layout_variants/L2/CN_LAYOUT_NUMBERED_13_18.jpg`
- `outputs/workflow_iter/WORKFLOW_NUMBERED.jpg`
