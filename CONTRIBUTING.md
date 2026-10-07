# Contributing to agnes-studio

## 基本原则

1. **验证先行**：任何改动先在本地实跑验证（渲染 / 导入 / smoke），贴出命令与结果再合入。
2. **Conventional Commits**：`feat:` / `fix:` / `docs:` / `ci:` / `refactor:` 等前缀，一句话说清改动。
3. **绝不提交凭据**：API Key、token、密钥文件、私有配置一律不进仓库。密钥走 `~/.new-api/local_key.json` 或 `NEW_API_KEY` 环境变量。

## 本地验证

```bash
python3 -m compileall scripts
python3 scripts/pro_poster_renderer.py --key swiss_01
# 检查 public/assets/poster_pro_swiss_01.png 为 1200x1200
```

## 提 PR

- 填写 PR 模板中的改动说明与验证过程
- CI（GitHub Actions）必须全绿
