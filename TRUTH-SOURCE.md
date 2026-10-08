# agnes-studio 真相源裁决（2026-10-08）

**代码真相源：`blackapple:/Volumes/3TB_DATA/05-开发项目/agnes-studio-work`**

判定依据（逐副本哈希比对，排除 data/outputs/图片/缓存）：

- 本副本 31 次提交、工作区干净、最近提交 2026-10-08（海报 footer 裁切修复），带 `.github/` CI 与 CONTRIBUTING，其余副本均无。
- 运行副本 `~/Services/agnes-studio/scripts/studio_server.py` 唯一独有的函数是 `ensure_venv()`；本副本已在模块顶部内联实现同一逻辑（`.venv` 自提 + `AGNES_VENV_SWITCHED` 防递归），**运行侧没有未合并的独有代码**。
- 两份旧快照（3TB `workspace/agnesstudio`、本机 `Desktop/workspace/agnesstudio`）在共享文件上全部落后于本副本，且本机副本 `scripts/` 缺 4 个文件（`autonomous_followup.py` / `env_config.py` / `gemini_engine.py` / `test_gemini_integration.py`）。

## 各副本现状（一律保留，未删除任何文件）

| 位置 | 角色 | 状态 |
| --- | --- | --- |
| `3TB:05-开发项目/agnes-studio-work` | **真相源（代码）** | 最新、干净、有 CI |
| `blackapple:~/Services/agnes-studio` | 8088 运行时（`studio_server.py 8088`，PID 见 `lsof -nP -i:8088`） | 代码停在 2026-09-27；有 1 个未提交改动 + 1 个 `.before-*` 备份文件 |
| `3TB:05-开发项目/workspace/agnesstudio` | 2026-10-05 旧快照 | 13 个共享文件落后；含 2.1G `.skill-cache`（可再生缓存） |
| `本机 Desktop/workspace/agnesstudio` | 2026-10-07 旧快照 | `scripts/` 缺 4 个文件 |

## 独有资产已收编

统一放 `3TB:05-开发项目/agnes-studio-assets/`：

- `mimocode/` ← `workspace/agnesstudio/.mimocode`（11 个文件 3.8M，poster-atelier 技能与参考，原先只有一份）
- `open_source_posters/` ← `~/Services/agnes-studio/open_source_posters`（171M 开源海报参考库，原先只在启动盘上有一份，未进 3TB）

## 待用户决定

1. 8088 服务是否改指向真相源并重启（当前跑的是 9-27 的旧代码）。
2. `.skill-cache`（2.1G，上游技能包下载解包产物）判定为可再生，未纳入备份；若需保留请说明。
3. 两份旧快照是否归档到 `90-历史归档/`。
