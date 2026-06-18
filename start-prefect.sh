#!/bin/bash
# Prefect 每日任务调度进程管理脚本（PM2 守护）
# 连接线上 Prefect Server: https://prefect.lanren.site/  （⚠️ 必须 https，nginx 会 301 重定向 http）
#
# 架构：
#   stock-prefect-serve : daily_flow.serve()
#   - 向线上 Prefect Server 注册 deployment（带 cron 定时）
#   - 到点由 Server 下发触发信号，本机执行 flow
#   - 执行完毕，结果回传 Server（UI 上可直接看 flow run 详情）
#
# 用法：
#   ./start-prefect.sh start                  # 启动 PM2 守护 + 注册每日 cron
#   ./start-prefect.sh stop                   # 停止守护
#   ./start-prefect.sh restart                # 重启守护
#   ./start-prefect.sh status               # 查看状态 + 最近日志
#   ./start-prefect.sh logs                 # 查看日志
#   ./start-prefect.sh run                    # 立即手动跑一次（全量：newbee+value+trend）
#   ./start-prefect.sh run newbee             # 立即只跑优质次新
#   ./start-prefect.sh run value              # 立即只跑优质低价
#   ./start-prefect.sh run trend              # 立即只跑趋势（全市场）
#   ./start-prefect.sh run trend us           # 立即只跑美股趋势
#   ./start-prefect.sh run trend hk a         # 立即只跑港股+A 股趋势
#   ./start-prefect.sh run trend us newbee      # 组合：美股趋势 + 优质次新
#   ./start-prefect.sh deploy               # 向 Prefect Server 注册 deployment
#

set -e

SERVE_NAME="stock-prefect-serve"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"

# ⭐ 加载项目内的 .env 文件（关键：PREFECT_API_URL 等配置由此生效）
# 优先级：.env 文件 > shell 环境变量 > 脚本默认值
if [ -f "$SCRIPT_DIR/.env" ]; then
    while IFS='=' read -r key value; do
        # 跳过空行和注释
        case "$key" in
            ''|\#*) continue ;;
        esac
        # 去除前后引号
        value="${value%\"}"
        value="${value#\"}"
        # 从 .env 加载（覆盖 shell 环境变量）
        export "$key=$value"
    done < "$SCRIPT_DIR/.env"
fi

# ⭐ 线上 Prefect Server API 地址（必须用 https，nginx 会 301 重定向 http）
PREFECT_API_URL="${PREFECT_API_URL:-https://prefect.lanren.site/api}"

# 独立的 Prefect 元数据目录：避免与其它项目共享 ~/.prefect 配置/缓存
export PREFECT_HOME="$SCRIPT_DIR/.prefect"
export PREFECT_API_URL
export PYTHONPATH="$SCRIPT_DIR"

mkdir -p "$LOG_DIR" "$PREFECT_HOME"

echo "使用 Prefect Server: ${PREFECT_API_URL}"
echo "PREFECT_HOME: ${PREFECT_HOME}"

# 探测线上 server API 是否可达
wait_for_server() {
    echo "检测线上 Prefect Server (${PREFECT_API_URL}) ..."
    for i in $(seq 1 15); do
        if curl -sf -m 3 "${PREFECT_API_URL}/health" >/dev/null 2>&1; then
            echo "线上 Prefect Server 可达 ✓"
            return 0
        fi
        sleep 2
    done
    echo "WARN: 线上 Prefect Server 不可达，serve 将无法注册调度，请检查网络与 ${PREFECT_API_URL}"
    echo "如果使用 nginx 反代，确认 proxy_pass 到 Prefect UI 和 Prefect Server 上的 /api"
    return 1
}

start() {
    echo "Starting Prefect serve (连接线上 ${PREFECT_API_URL}) with PM2..."
    cd "$SCRIPT_DIR" || exit 1
    pm2 delete "$SERVE_NAME" 2>/dev/null || true

    wait_for_server

    # serve：向线上 Server 注册 deployment(cron 每天 00:00 Asia/Shanghai) 并执行 flow
    PREFECT_HOME="$PREFECT_HOME" PREFECT_API_URL="$PREFECT_API_URL" PYTHONPATH="$PYTHONPATH" pm2 start ./venv/bin/python \
        --name "$SERVE_NAME" \
        --cron-restart="0" \
        --log-date-format "YYYY-MM-DD HH:mm:ss" \
        --error "$LOG_DIR/serve-error.log" \
        --output "$LOG_DIR/serve-out.log" \
        --max-memory-restart 1024M \
        -- -m flows.daily serve

    pm2 save 2>/dev/null || true
    sleep 3
    echo "启动完成，当前 PM2 进程列表："
    pm2 status
    echo ""
    echo "使用以下命令管理："
    echo "  ./start-prefect.sh status    # 查看状态"
    echo "  ./start-prefect.sh logs      # 查看日志"
}

stop() {
    echo "Stopping Prefect serve..."
    pm2 stop "$SERVE_NAME" 2>/dev/null || true
    echo "已停止 $SERVE_NAME"
}

restart() {
    wait_for_server
    pm2 restart "$SERVE_NAME" 2>/dev/null || true
    echo "重启完成"
}

status() {
    pm2 status
    echo "=== serve 最近日志 ==="
    pm2 logs "$SERVE_NAME" --lines 20 --nostream 2>/dev/null
}

logs() {
    pm2 logs "$SERVE_NAME" --lines 100 2>/dev/null
}

# 部署（向 Prefect Server 注册 deployment）
# Prefect 3.x 的 .serve() 会自动创建 deployment，无需单独 deploy 命令
deploy_info() {
    echo "Deployment 信息："
    echo "  Flow: daily-scheduler"
    echo "  部署名: lanren-daily-scheduler"
    echo "  调度: 每日 00:00 (Asia/Shanghai)  [cron: 0 0 * * *]"
    echo ""
    echo "启动后可以通过以下方式验证："
    echo "  curl ${PREFECT_API_URL}/deployments/query  查看部署"
    echo "  Prefect UI: https://prefect.lanren.site/"
}

# 手动立即跑一次（不走调度，便于调试）
run_once() {
    cd "$SCRIPT_DIR" || exit 1
    # 把 $@ 剩余参数全部传给 Python
    shift  # 吃掉第一个参数 "run"
    echo "立即执行一次 flow（不走调度）..."
    PREFECT_HOME="$PREFECT_HOME" PREFECT_API_URL="$PREFECT_API_URL" PYTHONPATH="$PYTHONPATH" \
        ./venv/bin/python -m flows.daily run "$@"
}

case "${1:-start}" in
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
    status)  status ;;
    logs)    logs ;;
    deploy)  deploy_info ;;
    run)     run_once "$@" ;;
    *)        echo "Usage: $0 {start|stop|restart|status|logs|deploy|run [task_types...]" ;;
esac
