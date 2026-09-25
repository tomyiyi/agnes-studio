# Agnes Studio - 海报渲染管线与前端端到端验证排障报告

**测试环境**: Omarchy Linux (Physical Hackintosh Guest VM)  
**网关地址**: 黑苹果物理机 New API (`http://192.168.1.164:3000/v1`)  
**服务端口**: `http://localhost:8088/#poster-studio`  
**测试日期**: 2026-09-23  

---

## 一、Git 分支与跨机同步状态核查
1. **当前分支**: `main`
2. **远程状态**: 执行 `git fetch origin`，远程 `origin/main` 位于 commit `6a8132d`，MacBook Pro M5 暂无更新的未拉取提交；
3. **本地状态**: 本地包含已推进功能提交（`0814ed1`, `d79b8fe`），已覆盖跨平台环境路径动态探测与极简 Zine 风格支持。

---

## 二、Studio Server 启动与 New API 端到端验证
1. **服务启动**:
   - 入口: `python3 scripts/studio_server.py 8088`
   - 增强项: 脚本头部内置环境智能提升逻辑，直接调用系统 `python3` 时会自动探测并透明转入 `.venv/bin/python`，确保依赖库（`playwright` 等）开箱即用。
2. **网关握手测试 (`/api/test-connection`)**:
   - 目标: `http://192.168.1.164:3000/v1`
   - 响应耗时: **13 ms**
   - 模型发现: 成功获取 13 个可用模型（包含 `agnes-image-2.5-flash`, `agnes-2.5-pro`, `dall-e-3` 等）。
3. **留白底图生成验证 (`/api/generate-image`)**:
   - 模型: `agnes-image-2.5-flash`
   - 规格: 1024×1024
   - 生成耗时: **16.33 秒**
   - 文件落盘: `public/assets/generated/agnes_1790185420.png` (903 KB 高清 PNG)
4. **海报光栅化渲染 (`/api/render-poster`)**:
   - 排版流派: 瑞士国际主义网格 (`swiss_01`) / 新中式金石 (`chinese_01`)
   - 渲染内核: 无头 Chromium + Playwright
   - 渲染耗时: **1242 ms** (1.2 秒)
   - 输出海报: `public/assets/poster_custom_1790185591.png` (460 KB, 1200×1200 亚像素级渲染)

---

## 三、前端 `public/index.html` 排障与体验优化记录

### 1. 致命缺陷修复：缺失 `btn-download-poster` 导致 TypeError
- **问题现象**: 用户在海报工作台点击切换预设时，由于 DOM 中不存在 `btn-download-poster`，执行 `document.getElementById('btn-download-poster').href = data.img;` 抛出 `TypeError: Cannot set properties of null (setting 'href')`，导致脚本执行中断。
- **解决方案**:
  1. 在海报检视工具栏中正式补齐 `<a id="btn-download-poster" download="...">⬇ 导出海报</a>` 实体组件；
  2. 在 `switchPosterPreset` 与 `renderCustomPoster` 中添加元素存在性守卫，渲染完成后自动关联时间戳海报链接与语义化下载文件名。

### 2. 运行时未定义异常修复：`escapeHtml is not defined`
- **问题现象**: 前端渲染回调中触发通知与卡片渲染时，引用了未定义的 `escapeHtml` 工具函数，抛出 `ReferenceError` 并进入 catch 块，导致成功的渲染被界面误报为“请求失败”。
- **解决方案**: 在 `<script>` 顶层声明标准的 HTML 转义函数 `escapeHtml(str)`，杜绝 XSS 风险并修复未定义引用。

### 3. 全局非阻塞通知系统 (Toast Notification)
- **改进前**: 使用系统原生阻塞式 `alert()`，在自动化测试和无头交互中阻断线程。
- **改进后**: 在页面底部注入 `#toast-container`，实现自适应动效 Toast 组件 `showNotification(msg, type, duration)`，支持 `success`、`error`、`warning`、`info` 多状态实时视觉反馈。

### 4. 商业海报全流程端到端闭环接入
- 前端新增 **「🎨 唤起 Agnes 现场生图」** 交互组件：
  1. 输入主题（如：“雨夜江南茶舍” / “极简山川”）；
  2. 点击「AI 撰写」由 Gemini 2.5 Flash 自动规划视觉参数与摄影 Prompt；
  3. 点击「唤起 Agnes 现场生图」直连宿主机 New API 生成高审美留白底图；
  4. 底图生成后自动注入下拉框并设为选中；
  5. 点击「🚀 光栅化渲染（过门禁）」秒级合成 1200×1200 商业海报；
  6. 点击「🔍 Gemini 视觉多模态审美审查」进行多模态审美打分（实测得分 **91/100**，主体避障低风险）。

---

## 四、自动化端到端测试结论
使用 Playwright 在无头 Chromium 环境下执行全流程交互测试，控制台 0 报错，全链路 100% 通过（PASS）。
服务已稳定运行在 `http://localhost:8088/#poster-studio`。
