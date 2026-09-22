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

# 检查 Python 环境
if command -v python3 >/dev/null 2>&1; then
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

# 检查端口是否被占用，若被占用则提示或复用
if lsof -i :$PORT >/dev/null 2>&1; then
    echo "ℹ️  端口 $PORT 已在运行中，直接打开浏览器即可。"
else
    echo "✨ 启动轻量静态 Web 容器在端口 $PORT..."
    $PYTHON_CMD -m http.server $PORT --directory "$DIR/public" &
    SERVER_PID=$!
    echo "PID: $SERVER_PID"
fi

# 自动在系统默认浏览器中打开
if command -v open >/dev/null 2>&1; then
    open "http://localhost:$PORT/#poster-studio"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:$PORT/#poster-studio"
fi

echo "✅ 启动完成！按下 Ctrl+C 退出日志监控。"
wait
