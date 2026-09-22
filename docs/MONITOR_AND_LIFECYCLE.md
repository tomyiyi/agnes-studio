# Agnes Studio 生命周期与上游依赖同步监控机制 (Sentinel & Lifecycle)

## 1. 监控与生命周期设计哲学
Agnes Studio 不仅是一个本地生图工作台，更是与开源生态保持同频进化的动态系统。本套 Sentinel 体系旨在提供：
- **上游生态同频（Eco Sync）**：无缝捕捉 GitHub 上游提示词模板库（`ConardLi/garden-skills`）的结构升级。
- **网关自愈探活（Gateway Self-Healing）**：高频探测本地 New API 网关健康，保障 6 个 upstream key 的零死角高可用。
- **配置驱动热更新（Data Hot-Reload）**：监控巡检自动落盘至 `data/updates.json`，前端 UI 实时感知并渲染系统状态指标。

---

## 2. 核心监控拓扑

```
+-------------------------------------------------------------------------------+
|                             Agnes Studio Sentinel                             |
+-------------------------------------------------------------------------------+
         |                                                       |
         v                                                       v
+-------------------------+                           +-------------------------+
|   上游依赖同步检测器     |                           |   本地聚合网关巡检器    |
| (Upstream Repo Tracker) |                           |  (Gateway Health Check) |
+-------------------------+                           +-------------------------+
         |                                                       |
         | GitHub REST API 探测最新 commit                        | HTTP GET /v1/models 测延迟
         | 提取模板变动与新增分类                                   | 统计可用渠道数与模型列表
         v                                                       v
+-------------------------------------------------------------------------------+
|                    聚合状态持久化：data/updates.json                           |
+-------------------------------------------------------------------------------+
                                         |
                                         v
                         +-------------------------------+
                         | 前端 Dashboard / 状态哨兵面板 |
                         +-------------------------------+
```

---

## 3. 监控指标与阈值定义

| 监控项 | 检查端点 / 方式 | 正常指标 (Healthy) | 告警指标 (Warning/Critical) | 处理机制 |
| :--- | :--- | :--- | :--- | :--- |
| **本地 New API 网关** | `http://127.0.0.1:3000/v1/models` | HTTP 200, 耗时 < 100ms | 连接超时或 HTTP 500 | 自动触发重启 Docker 容器检查 |
| **Agnes 渠道上游池** | `apihub.agnes-ai.com/v1/models` | 6 渠道全部 200，平均耗时 < 2s | 某个渠道连续失败 3 次 | 触发 New API 内部自动熔断（Auto-Disable） |
| **上游 Garden-Skills** | `api.github.com/repos/.../commits` | Commit SHA 与本地吻合 | 发现远端新 commit hash | 标记提示可更新，提供一键提取新模板指令 |
| **数据库安全备份** | 本地文件大小与时间戳检测 | 每日生成，文件体积 > 50KB | 超过 24 小时未生成备份 | 自动补跑 `backup_db.sh` 脚本 |

---

## 4. 定时调度配置指南 (Cron Automation)

推荐将健康监控巡检加入系统 Crontab 或通过 ZCode 调度常驻执行：

```bash
# 1. 每天凌晨 3:00 执行 SQLite WAL 数据库快照与归档（保留 7 天）
0 3 * * * /bin/bash /Users/tom/.new-api/backup_db.sh > /dev/null 2>&1

# 2. 每小时第 15 分钟运行依赖与网关健康巡检，更新 data/updates.json
15 * * * * /usr/bin/python3 /Users/tom/Desktop/agnes-studio/scripts/check_upstream_updates.py > /dev/null 2>&1
```

---

## 5. 手动运行与验证
在终端或工作台脚本目录直接执行：
```bash
python3 /Users/tom/Desktop/agnes-studio/scripts/check_upstream_updates.py
```
控制台将即时输出探活日志并自动刷新数据文件。
