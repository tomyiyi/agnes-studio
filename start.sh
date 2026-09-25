#!/usr/bin/env bash
# ==============================================================================
# Agnes Studio - 跨电脑一键启动与同步工作台脚本
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

PORT=8088

echo "🚀 [Agnes Studio] 正在启动智能海报与多模态生成工作台..."
echo "📂 根目录: $DIR"
echo "🌐 访问入口: http://localhost:$PORT/#poster-studio"
echo "=============================================================================="

# 检查 Python 环境 (优先使用虚拟环境)
if [ -f "$DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "❌ 错误: 未检测到 Python 环境，请先安装 Python 3.8+！"
    exit 1
fi

# 启动前自动检查远程 GitHub 更新（跨电脑无缝同步）
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "🔄 正在检查远程 GitHub 最新改动..."
    git pull --rebase origin main 2>/dev/null || echo "ℹ️  跳过远程拉取（离线或已是最新）"
fi

# 检查端口是否被占用，若被占用则杀掉旧服务或提示
if lsof -i :$PORT >/dev/null 2>&1; then
    echo "ℹ️  端口 $PORT 已在运行中，正在重启为最新统一服务..."
    lsof -ti :$PORT | xargs kill -9 2>/dev/null || true
    sleep 1
fi

echo "✨ 启动 Agnes Studio 统一智能工作台与模型网关 (端口 $PORT)..."
$PYTHON_CMD "$DIR/scripts/studio_server.py" $PORT &
SERVER_PID=$!
echo "PID: $SERVER_PID"

# 自动在系统默认浏览器中打开
if command -v open >/dev/null 2>&1; then
    open "http://localhost:$PORT/#poster-studio"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:$PORT/#poster-studio"
fi

echo "✅ 启动完成！按下 Ctrl+C 退出日志监控。"
wait
