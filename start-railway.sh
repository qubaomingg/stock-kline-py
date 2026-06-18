#!/bin/bash
# Railway 部署：同时启动 Web 服务 + Prefect 每日任务 worker
# 负责：
#   1. 启动 FastAPI Web 服务（main.py，提供 /api/kline /api/stock/market 等接口）
#   2. 启动 Prefect worker（daily_flow.serve()，每日 01:00 触发 3 种分析）
#
# 说明：
#   - Web 服务：hypercorn 启动，监听 $PORT（Railway 自动分配）
#   - Prefect worker：后台进程，连接 http://prefect.lanren.site/api
#   - 任何一个进程异常退出都会触发重启

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# ⭐ 加载项目内的 .env 文件（关键：PREFECT_API_URL、API keys 等配置由此生效）
# 优先级：.env 文件 > shell 环境变量 > 脚本默认值
if [ -f "$SCRIPT_DIR/.env" ]; then
    while IFS='=' read -r key value; do
        case "$key" in
            ''|\#*) continue ;;
        esac
        value="${value%\"}"
        value="${value#\"}"
        export "$key=$value"
    done < "$SCRIPT_DIR/.env"
fi

# 环境变量（如未设置则使用默认值）
export PYTHONPATH="$SCRIPT_DIR"
export PREFECT_HOME="$SCRIPT_DIR/.prefect"
export PREFECT_API_URL="${PREFECT_API_URL:-https://prefect.lanren.site/api}"
export RAILWAY_API="${RAIL_WAY_API:-http://frequent-api.lanren.site}"
export PYTHON_API_URL="${PYTHON_API_URL:-https://kline-aliyun.lanren.site}"

echo "=========================================="
echo "Railway 启动脚本"
echo "=========================================="
echo "PREFECT_API_URL: ${PREFECT_API_URL}"
echo "RAILWAY_API: ${RAILWAY_API}"
echo "PYTHON_API_URL: ${PYTHON_API_URL}"
echo "PORT: ${PORT}"
echo ""

# 检查 Prefect Server 是否可达
echo "检测 Prefect Server 连接..."
for i in $(seq 1 10); do
    if curl -sf -m 3 "${PREFECT_API_URL}/health" >/dev/null 2>&1; then
        echo "  Prefect Server 可达 ✓"
        break
    fi
    echo "  尝试 $i/10: 等待 Server 就绪..."
    sleep 2
done

echo ""

# ── 启动 Prefect worker（后台运行）──
echo "启动 Prefect worker（后台）..."
cd "$SCRIPT_DIR"

./venv/bin/python -m flows.daily serve \
    > "$LOG_DIR/prefect-worker.log" 2>&1 &
WORKER_PID=$!
echo "  Prefect worker PID: $WORKER_PID"

# 给 worker 一点时间启动
sleep 5

# 检查 worker 是否还在运行
if ! kill -0 $WORKER_PID 2>/dev/null; then
    echo "  ⚠️  Prefect worker 启动失败，查看日志："
    cat "$LOG_DIR/prefect-worker.log" | tail -30
else
    echo "  Prefect worker 启动成功 ✓"
fi

echo ""

# ── 启动 Web 服务（前台阻塞）──
echo "启动 FastAPI Web 服务（前台）..."
cd "$SCRIPT_DIR"

# 同时监控 worker 进程，任何一个异常退出都触发重启
(while true; do
    if ! kill -0 $WORKER_PID 2>/dev/null; then
        echo "⚠️  Prefect worker 已退出，重启中..."
        ./venv/bin/python -m flows.daily serve \
            > "$LOG_DIR/prefect-worker.log" 2>&1 &
        WORKER_PID=$!
        echo "  新 worker PID: $WORKER_PID"
    fi
    sleep 10
done) &
MONITOR_PID=$!

echo "  Monitor PID: $MONITOR_PID"
echo ""

# 启动 Web 服务（主进程，阻塞）
./venv/bin/python -m hypercorn main:app \
    --bind "[::]:${PORT:-8000}" \
    --access-logfile "$LOG_DIR/access.log" \
    --error-logfile "$LOG_DIR/error.log" \
    --log-level info

echo "Web 服务已退出，清理 worker..."
kill $WORKER_PID 2>/dev/null || true
kill $MONITOR_PID 2>/dev/null || true
echo "已停止所有进程"
