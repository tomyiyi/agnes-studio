#!/usr/bin/env bash
# ==============================================================================
# Agnes Studio - 跨电脑一键启动与同步工作台脚本
# ==============================================================================
# 用法：
#   ./start.sh             启动服务（默认端口 8088，可用 PORT 环境变量覆盖）
#   ./start.sh --update    先从 GitHub 拉取最新改动，再启动服务
# 安全约定：
#   - 默认绝不静默改动工作区（git pull 必须显式 --update 触发）
#   - 端口被占用时只报告占用进程并退出，绝不自动 kill 任何进程
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 端口可用环境变量覆盖，方便测试与多实例
PORT="${PORT:-8088}"

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

# 只有显式传入 --update 时才拉取远程更新；默认不碰工作区
if [ "${1:-}" = "--update" ]; then
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "🔄 正在拉取远程 GitHub 最新改动..."
        git pull --rebase origin main || echo "⚠️  拉取失败（离线或存在冲突），继续使用本地版本"
    else
        echo "ℹ️  非 git 工作区，跳过更新"
    fi
fi

# 检查端口是否被占用：只报告占用进程并退出，绝不自动 kill
if lsof -i :$PORT >/dev/null 2>&1; then
    echo "❌ 错误: 端口 $PORT 已被占用，拒绝启动（不会自动杀掉占用进程）。"
    echo "   占用该端口的进程："
    lsof -ti :$PORT 2>/dev/null | while read -r pid; do
        if [ -n "$pid" ]; then
            ps -p "$pid" -o pid=,command= 2>/dev/null | sed 's/^/     /'
        fi
    done
    echo "   请手动处理后重试，或用 PORT=<空闲端口> ./start.sh 指定其他端口启动。"
    exit 1
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
