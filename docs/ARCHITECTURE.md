# Agnes Studio（Agnes 智能工作台）全景系统架构与技术蓝图

> **系统定位**：专为 Agnes 扩散模型量身打造的高阶 AI 视觉创研平台、Prompt 编译工作台、数字资产沉淀矩阵与开源 Agent 工具链协同中心。  
> **设计对标**：Linear 级极简工程美学、Vercel 现代化配置驱动架构、GitHub 顶尖开源项目视觉交互规范。

---

## 1. 全局信息架构（Information Architecture, IA）

工作台采用“单视窗高聚合导航 + 多维工作舱模块化分层”的拓扑结构，确保在复杂的高密度专业操作下依然具备清爽的人机交互体验。

```
Agnes Studio 全局系统架构
 ├── 1. Global Shell (全局控制外壳)
 │    ├── 顶部状态雷达 (Agnes Health, 6-Key Active Status, Gateway Latency)
 │    ├── 全局命令调度器 (Command + K Palette)
 │    ├── 动态双模主题引擎 (Obsidian Void Dark / Paper White Editorial)
 │    └── 版本更新与依赖预警胶囊 (Update & Sentinel Capsule)
 │
 ├── 2. Prompt Studio & Transpiler (提示词编译与生图工作舱)
 │    ├── 17 大类 93 套 Skill 模板集市 (分类检索、参数提问链、动态补全)
 │    ├── GPT-Image JSON -> Agnes 物理光学语法双向转译引擎 (AST Parser)
 │    ├── 角色 DNA 锚定器 (微观三锚点锁定，杜绝人物长相漂移)
 │    └── 参数调优面板 (步数、CFG、留白区域 Negative Space、排版预留)
 │
 ├── 3. Asset & Masterpiece Matrix (数字资产与案例画廊舱)
 │    ├── 真实生成案例流 (卡片流、瀑布流、大图全景对比)
 │    ├── 双版本差异透镜 (Side-by-Side Diff / 卷帘滑块交互比对)
 │    ├── 矢量中文字体海报排版引擎 (负空间引导 + 矢量字体无乱码合成)
 │    └── 本地持久化归档浏览器 (元数据 JSON 伴随、一键重绘复现)
 │
 ├── 4. Open-Source Ecosystem Hub (开源生态与 Agent 工具舱)
 │    ├── 本地 New API 聚合网关监控 (渠道权重分布、熔断探活、用量消耗)
 │    ├── Agent Reach 互联网实时信息采集舱
 │    ├── Graphify 代码知识图谱分析器
 │    ├── Browser-Use 自主浏览器测试运行器
 │    └── Tabbit 浏览器 Native Devtools 联动控制桥
 │
 └── 5. Lifecycle & Health Sentinel (生命周期与自动化运维舱)
      ├── 上游 GitHub 开源仓库版本差分探测器 (garden-skills / new-api)
      ├── 6-Key 实时并发探针看板与延迟热力图
      └── SQLite 数据库在线热备份与 7 天轮转状态监控
```

---

## 2. 现代科技视觉与设计规范（Design System Specification）

系统严格摒弃粗糙平庸的通用后台模板风格，建立完整的微质感科技美学 Token。

### 2.1 色彩语义系统（Color Tokens）

#### 极客暗黑模式（Obsidian Void - 默认高沉浸工作模式）：
- **画布背景（Background Void）**：`#0A0B10`（极深黑蓝，带 0.02 颗粒噪点）
- **面板表面（Surface Panel）**：`#12141E`（毛玻璃半透底色，`backdrop-blur-xl`）
- **悬浮与激活层（Surface Raised）**：`#1A1D2B`
- **微质感边框（Border Glass）**：`rgba(255, 255, 255, 0.07)`，焦点发光为 `#00F0FF` 或 `#0071E3`
- **主功能点缀色（Accent Cyber Cyan）**：`#00F0FF`（用于雷达运行态、关键指标）
- **高阶暖金色（Accent Steam Gold）**：`#F5A623`（用于海报设计、VIP 案例标示）
- **状态绿色（Success Emerald）**：`#10B981`（渠道全通、低延迟指示）
- **主要文本（Text Primary）**：`#F9FAFB`（95% 纯白）
- **次级文本（Text Secondary）**：`#9CA3AF`（冷灰）

#### 纯白极简模式（Paper White - 成果汇报与展示画廊）：
- **画布背景**：`#FFFFFF`（纯白无杂质）
- **面板卡片**：`#F8F9FA`，边框 `1px solid #E5E5EA`
- **悬浮阴影**：`0 8px 30px rgba(0, 0, 0, 0.04)`，符合 Apple Editorial 视觉规范。

### 2.2 微交互与质感工艺规范
1. **线性发光流光边框（Border Beam Effect）**：在核心状态卡片与生成按钮边缘，运用顺时针运动的轻微渐变光丝，营造高级 AI 运算感。
2. **径向背景弥散光（Radial Backdrop Glow）**：在主要操作区背后注入低饱和度的环境光晕（`rgba(0, 240, 255, 0.08)`），产生视觉纵深。
3. **弹簧阻尼微动效（Framer Motion Springs）**：
   - 弹窗/抽屉：`transition: { type: "spring", stiffness: 350, damping: 28 }`
   - 卡片 Hover：`scale: 1.015, translateY: -3px, duration: 0.2s`
4. **字体层级**：
   - 西文/数字：`Geist Sans`, `Inter`, `SF Pro Display`（强调等宽数字 `tabular-nums`）
   - 代码/提示词：`JetBrains Mono`, `SF Mono`
   - 中文排版：`PingFang SC`, `Hiragino Sans GB`，古典海报切入 `Songti SC`

---

## 3. 配置驱动型数据架构（Data-Driven Architecture）

所有模块均由 `/Users/tom/Desktop/workspace/agnesstudio/data/` 目录下的标准 JSON 实体驱动，具备热插拔与动态扩展能力：

| 数据集路径 | 数据结构实体 | 说明 |
| :--- | :--- | :--- |
| `data/skills.json` | `SkillCategory[]`, `SkillTemplate[]` | 映射 17 大类 93 个提示词模板、字段提取规则与参数映射 |
| `data/ecosystem.json` | `EcosystemTool[]` | New API、Agent Reach、Graphify、Browser-Use 的状态与端点 |
| `data/cases.json` | `MasterpieceCase[]` | 实测验证的视觉资产、Prompt 对比、本地图片路径与耗时 |
| `data/updates.json` | `DependencyTrack[]`, `Changelog[]` | 上游 GitHub 仓库与本地运行时的版本差分数据 |

---

## 4. 核心工作流与人机工程动线

```
1. 需求输入 / 模板选择
   用户通过 Command+K 搜索或点击 17 大类 Skill，调出针对性模板
   │
2. 实时编译 (GPT-Image -> Agnes)
   系统解析 JSON 属性，自动剔除磨皮假词，注入 Hasselblad / SSS 物理光学参数
   │
3. 负空间预留与排版配置
   用户勾选是否合成中文标题，系统自动在提示词注入 "negative space for typography"
   │
4. 一键集群调度
   通过本地优化网关（6 Key 动态分流、自动熔断）并发生成，平均 10~15 秒完成
   │
5. 自动持久化落盘与矢量合成
   二进制流自动落盘至 generated_images，并由 PIL/Canvas 完成高清矢量文字合成
   │
6. 资产进入画廊矩阵
   自动沉淀入 cases.json，实时展示在 Web 画廊与 Tabbit 浏览器中
```

---

## 5. 技术栈与工程落地方案

- **核心框架**：Next.js 15 (App Router) + React 19
- **样式引擎**：Tailwind CSS v4 + Lucide React 图标体系
- **动效组件**：Framer Motion + Radix UI Primitives
- **状态与数据层**：本地轻量级 Node/Python 后端桥接，直接读取 SQLite `one-api.db` 与 `generated_images/` 资产目录
- **部署环境**：本地常驻 Node 服务（如 `localhost:8888`），可通过 Tabbit 浏览器即开即用。
