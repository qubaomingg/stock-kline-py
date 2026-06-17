#!/bin/bash
# Prefect 每日任务调度进程管理脚本（PM2 守护）
# 替代原 lanren-bg-api 的 SQS Worker + cron 触发架构
#
# 架构：连接「线上 Prefect Server」，本地只需一个常驻 serve 进程
#   stock-prefect-serve : daily_flow.serve()，连到线上 server 注册 cron 调度并执行 flow
# 说明：
#   - 线上 server 自带 scheduler，负责存调度、到点下发触发信号
#   - serve 进程负责接收触发信号、在本机执行 flow 代码（代码在哪台机器，flow 就在哪执行）
#   - 因此不再需要本地常驻 server；只要 serve 进程在跑，cron 就会按线上调度触发

SERVE_NAME="stock-prefect-serve"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"

# 线上 Prefect Server API（可用环境变量覆盖）
PREFECT_API_URL="${PREFECT_API_URL:-https://prefect.lanren.site/api}"

# 独立的 Prefect 元数据目录：避免与其它项目共享 ~/.prefect 配置/缓存
export PREFECT_HOME="$SCRIPT_DIR/.prefect"
export PYTHONPATH="$SCRIPT_DIR"

mkdir -p "$LOG_DIR" "$PREFECT_HOME"

# 探测线上 server API 是否可达
wait_for_server() {
    echo "检测线上 Prefect Server (${PREFECT_API_URL}) ..."
    for i in $(seq 1 15); do
        if curl -sf -m 3 "${PREFECT_API_URL}/health" >/dev/null 2>&1; then
            echo "线上 Prefect Server 可达"
            return 0
        fi
        sleep 2
    done
    echo "WARN: 线上 Prefect Server 不可达，serve 将无法注册调度，请检查网络与 ${PREFECT_API_URL}"
    return 1
}

start() {
    echo "Starting Prefect serve (连接线上 ${PREFECT_API_URL}) with PM2..."
    cd "$SCRIPT_DIR" || exit 1
    pm2 delete "$SERVE_NAME" 2>/dev/null || true

    wait_for_server

    # serve：连到线上 server 注册 cron(每天01:00 Asia/Shanghai) 并执行 flow
    PREFECT_HOME="$PREFECT_HOME" PYTHONPATH="$PYTHONPATH" PREFECT_API_URL="$PREFECT_API_URL" pm2 start ./venv/bin/python \
        --name "$SERVE_NAME" \
        --log-date-format "YYYY-MM-DD HH:mm:ss" \
        --error "$LOG_DIR/serve-error.log" \
        --output "$LOG_DIR/serve-out.log" \
        -- -m flows.daily serve

    pm2 save 2>/dev/null || true
    sleep 3
    pm2 status
}

stop() {
    pm2 stop "$SERVE_NAME" 2>/dev/null || true
}

restart() {
    wait_for_server
    pm2 restart "$SERVE_NAME" 2>/dev/null || true
}

status() {
    pm2 status
    echo "=== serve 最近日志 ==="
    pm2 logs "$SERVE_NAME" --lines 20 --nostream 2>/dev/null
}

logs() {
    pm2 logs "$SERVE_NAME" --lines 100 2>/dev/null
}

# 手动立即跑一次（不走调度，便于调试）；连线上 server，运行记录在线上 UI 可见
# 用法：
#   ./start-prefect.sh run            # 全量：新新+低价+趋势
#   ./start-prefect.sh run newbee     # 只跑优质次新
#   ./start-prefect.sh run value      # 只跑优质低价
#   ./start-prefect.sh run trend      # 只跑全市场趋势
#   ./start-prefect.sh run newbee value  # 同时跑指定多个类型
run_once() {
    cd "$SCRIPT_DIR" || exit 1
    # 把 $@ 剩余参数全部传给 Python（例如 newbee / value / trend）
    shift  # 吃掉第一个参数 "run"
    PREFECT_HOME="$PREFECT_HOME" PYTHONPATH="$PYTHONPATH" PREFECT_API_URL="$PREFECT_API_URL" \
        ./venv/bin/python -m flows.daily run "$@"
}

case "${1:-start}" in
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
    status)  status ;;
    logs)    logs ;;
    run)     run_once "$@" ;;
    *)       echo "Usage: $0 {start|stop|restart|status|logs|run} [newbee|value|trend]" ;;
esac
