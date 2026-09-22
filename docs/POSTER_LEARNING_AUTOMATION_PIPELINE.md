# Agnes Studio · 短视频与全网海报设计自动化学习系统设计方案

> **核心目标**：构建“短视频多模态逆向拆解 + Agent Reach 全网知识互验”的工业化海报设计自学习流水线，将网络优质设计内容自动提炼为排版代码与算法模板。

---

## 一、系统架构总览 (System Architecture)

学习海报设计不能仅靠文本提示词，海报的精髓在于**栅格网格（Grid）、字阶比例（Type Hierarchy）、负空间（Negative Space）与色彩层级（Color Chiaroscuro）**。

整个系统分为五大核心流水线阶段：

```
                       [ 学习源 1: 短视频 (抖音/B站/TikTok) ]         [ 学习源 2: 全网设计生态 (Agent Reach) ]
                                        │                                                  │
                                        ▼                                                  ▼
                        ┌───────────────────────────────┐                  ┌───────────────────────────────┐
                        │ 1. 视频抓取与音画解耦管线     │                  │ 2. 全网多源检索与知识提取     │
                        │ - Tabbit / yt-dlp 视频下载    │                  │ - 小红书爆款排版与调色案例   │
                        │ - ffmpeg 提取 16kHz WAV 音频  │                  │ - B站/YouTube 栅格设计教程    │
                        │ - 场景切分提取海报关键帧      │                  │ - GitHub 开源字体与排版规范   │
                        └───────────────┬───────────────┘                  └───────────────┬───────────────┘
                                        │                                                  │
                 ┌──────────────────────┴──────────────────────┐                           │
                 ▼                                             ▼                           │
   ┌───────────────────────────┐                 ┌───────────────────────────┐             │
   │ 3. 声音转文字 (ASR)       │                 │ 4. 关键帧视觉解析 (Vision) │             │
   │ - 本地 Whisper (免Token)  │                 │ - 识别标题/副标/正文字阶比│             │
   │ - MiniMax ASR (云端保障)  │                 │ - 提取色块与透明度参数    │             │
   │ 获得博主口述设计心法口诀  │                 │ - 测算人物主体与留白负空间│             │
   └─────────────┬─────────────┘                 └─────────────┬─────────────┘             │
                 │                                             │                           │
                 └──────────────────────┬──────────────────────┘                           │
                                        │ (视听融合对齐)                                   │
                                        ▼                                                  ▼
                        ┌──────────────────────────────────────────────────────────────────┐
                        │ 5. 多模态设计法则蒸馏器 (Cognitive Distillation Engine)          │
                        │ - 将博主口述与海报关键帧融合，提炼结构化排版参数 (JSON Schema)   │
                        │ - 结合 Agent Reach 检索到的全网规范进行交叉验证 (LLM Wiki 模式) │
                        └───────────────────────────────┬──────────────────────────────────┘
                                                        ▼
                        ┌──────────────────────────────────────────────────────────────────┐
                        │ 6. 代码化落地与工作台消费 (Code Generation & Studio Delivery)    │
                        │ - 生成 Python PIL / Satori 自动化矢量排版脚本                    │
                        │ - 沉淀至 Agnes Studio 海报与中文字体工坊 (public/index.html)     │
                        └──────────────────────────────────────────────────────────────────┘
```

---

## 二、短视频学习流水线关键技术实现 (Step-by-Step)

### 1. 视频与音频解耦 (Audio Extraction)
通过 `ffmpeg` 将视频中的声音无损分离，并标准化为 16kHz 单声道采样率，以便 ASR 高精度识别：
```bash
ffmpeg -i video.mp4 -vn -ar 16000 -ac 1 -c:a pcm_s16le audio_16k.wav
```

### 2. 声音转文字 (ASR)：MiniMax Token 与本地引擎的定位决策
关于用户的核心疑问：**“我有 MiniMax Token Plan，可以声音转文字吗？”**

#### 决策矩阵：算力效益最大化
| 方案 | 优势 | 适用场景 | Token 消耗 |
| :--- | :--- | :--- | :--- |
| **本地 Whisper / mlx-whisper** | 完全免费、毫秒级极速响应、不依赖外网、支持断网运行 | 批量处理短视频音频转录、字幕提取 | **0 Token** |
| **MiniMax 开放平台 ASR / 智能体** | 对中英文混合、中文方言、专业术语适应度极高 | 复杂环境音、高噪音视频、长视频深度转写 | 消耗语音识别额度 |
| **MiniMax M3 / Vision 多模态（核心！）** | 顶尖审美理解、精准识别文字字体风格、计算版式布局 | **分析视频关键帧海报构图、提炼设计法则** | **发挥 Token 的最高价值** |

> 💡 **资深架构师结论**：  
> **把珍贵的 MiniMax Token 用在刀刃上！** 声音转文字（ASR）是成熟且本地轻量的流水线，优先由本地或免 Token 引擎完成；而把 MiniMax 的 Token 用于 **多模态视觉审美分析（`mmx vision describe`）** 和 **大语言模型规则提炼（M3 Reasoning）**，这是最具产出价值的工程组合。

### 3. 视频关键画面智能抽取 (Scene-Change Keyframe Detection)
短视频博主讲解海报时，PPT 或设计案例切换的瞬间画面会发生显著变化。使用 `ffmpeg` 的 `gt(scene, 0.3)` 滤镜，可以**自动剔除博主说话时的冗余视频帧，仅截出海报展示的关键定格画面**：
```bash
ffmpeg -i video.mp4 -vf "select='gt(scene,0.3)',scale=1080:-1" -vsync vfr keyframes/keyframe_%03d.png
```

---

## 三、Agent Reach 全网知识互验体系

短视频往往只提供“单点技巧”，通过 **Agent Reach** 联动全网设计生态，实现“由点及面”的质变：

### 1. 小红书 (Xiaohongshu)：获取最新流行视觉范式
* **价值**：国内设计自媒体、摄影修图师与电商美工最活跃的阵地，涵盖“排版调色公式”、“港风复古海报”、“电商大促封面”。
* **操作**：通过 `agent-reach` 搜索高赞笔记，获取真实受众买单的爆款色板与字号搭配。

### 2. Bilibili / YouTube：获取专业网格系统与大师课
* **价值**：长视频有系统化的《平面设计网格系统》（Grid System）、《排版设计中的正负空间运用》、《字体的性格与情绪表达》。
* **操作**：通过 `agent-reach transcribe` 直接提取教学视频字幕，沉淀专业设计理论。

### 3. GitHub：沉淀开源商用字体与代码排版引擎
* **价值**：
  * 开源字体：`atelier-anchor/smiley-sans` (得意黑), `lxgw/LxgwWenKai` (霞鹜文楷), `adobe-fonts/source-han-serif` (思源宋体)。
  * 排版规范：`sparanoid/chinese-copywriting-guidelines`（盘古之白呼吸间距）。
  * 渲染引擎：`vercel/satori`、`Python Pillow`。

---

## 四、落地范例：标准化海报设计 JSON 规范 (Schema)

通过上述视听双流蒸馏出的海报模板，最终标准化为以下 JSON，供 Agnes Studio 随时调用生成：

```json
{
  "template_id": "shusheng_split_green",
  "template_name": "加块绿 · 左右对角拆字电影感封面",
  "source": "抖音@书生今天也在学",
  "design_principles": {
    "visual_hook": "莫兰迪半透明暗绿圆角矩形打底，破除杂乱背景吞字",
    "typography_flow": "标题对角拆分 (左上 + 右下)，避让中心人像主体",
    "scale_ratio": "主标题 52pt : 英文副标 10pt (极端对比比率 10:1)",
    "font_pairing": {
      "chinese": "SmileySans-Oblique (得意黑 8° 窄斜体)",
      "latin": "JetBrains Mono / DIN Bold (Tracking +300%)"
    },
    "color_palette": {
      "text_main": "#F8F9FA",
      "backdrop_box": "rgba(24, 58, 43, 0.82)",
      "ambient_shadow": "rgba(0, 0, 0, 0.35)"
    }
  }
}
```
