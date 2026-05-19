#!/bin/bash
#
# bootstrap.sh - 股票K线数据服务 启动/停止/管理脚本
#
# 使用方法:
#   ./bootstrap.sh start     # 后台启动服务
#   ./bootstrap.sh stop      # 停止服务
#   ./bootstrap.sh restart   # 重启服务
#   ./bootstrap.sh status    # 查看状态
#   ./bootstrap.sh logs      # 查看日志（实时）
#   ./bootstrap.sh health    # 健康检查
#

set -e

# ==================== 配置区 ====================

APP_NAME="stock-kline-api"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="${APP_DIR}/app.pid"
LOG_FILE="${APP_DIR}/logs/app.log"
ERROR_LOG="${APP_DIR}/logs/error.log"

# Hypercorn 配置
HOST="0.0.0.0"
PORT=8000
WORKERS=1  # 生产环境建议设为 CPU核心数

# Python 环境
PYTHON_CMD="python3"
VENV_DIR="${APP_DIR}/venv"

# ==================== 颜色定义 ====================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==================== 工具函数 ====================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 检查端口是否被占用
check_port() {
    if lsof -i :$PORT >/dev/null 2>&1; then
        return 1  # 端口被占用
    else
        return 0  # 端口可用
    fi
}

# 强制释放端口（杀死占用进程）
force_free_port() {
    log_warn "尝试释放端口 ${PORT}..."

    local pids=$(lsof -t -i :$PORT 2>/dev/null)

    if [ -z "$pids" ]; then
        log_info "端口 ${PORT} 已释放"
        return 0
    fi

    for pid in $pids; do
        local cmd=$(ps -p $pid -o command= 2>/dev/null | head -1)
        log_warn "   发现进程: PID=${pid}, CMD=${cmd}"

        # 先尝试优雅终止
        kill -TERM "$pid" 2>/dev/null || true

        # 等待2秒
        sleep 2

        # 如果还在运行，强制终止
        if kill -0 "$pid" 2>/dev/null; then
            log_warn "   进程未响应 SIGTERM，强制终止 (kill -9)..."
            kill -9 "$pid" 2>/dev/null || true
            sleep 1
        fi
    done

    # 再次检查
    if check_port; then
        log_info "✅ 端口 ${PORT} 已成功释放"
        return 0
    else
        log_error "❌ 端口 ${PORT} 仍被占用"
        return 1
    fi
}

# 获取进程PID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        return 1
    fi
}

# 检查进程是否在运行
is_running() {
    local pid=$(get_pid 2>/dev/null)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0  # 正在运行
    else
        return 1  # 未运行
    fi
}

# 创建日志目录
ensure_log_dir() {
    if [ ! -d "${APP_DIR}/logs" ]; then
        mkdir -p "${APP_DIR}/logs"
        log_info "创建日志目录: ${APP_DIR}/logs"
    fi
}

# 激活虚拟环境（如果存在）
activate_venv() {
    if [ -d "$VENV_DIR" ] && [ -f "${VENV_DIR}/bin/activate" ]; then
        source "${VENV_DIR}/bin/activate"
        log_debug "已激活虚拟环境: $VENV_DIR"
    fi
}

# ==================== 核心功能 ====================

start_service() {
    log_info "正在启动 ${APP_NAME}..."

    # 检查是否已在运行
    if is_running; then
        local pid=$(get_pid)
        log_warn "服务已经在运行中 (PID: ${pid})"
        return 1
    fi

    # 检查端口
    if ! check_port; then
        log_warn "端口 ${PORT} 被占用，正在自动释放..."

        # 检查是否是本服务之前的实例
        if [ -f "$PID_FILE" ]; then
            local old_pid=$(cat "$PID_FILE")
            if kill -0 "$old_pid" 2>/dev/null; then
                log_info "发现旧实例 (PID: ${old_pid})，正在停止..."
                stop_service
                sleep 2
            fi
        fi

        # 如果还被占用，强制释放
        if ! check_port; then
            log_warn "端口仍被其他进程占用"

            # 询问用户（非交互模式直接强制释放）
            if [ -t 1 ]; then  # 检查是否是交互式终端
                read -p "是否强制终止占用端口的进程？(y/N): " answer
                case $answer in
                    [Yy]*)
                        force_free_port || return 1
                        ;;
                    *)
                        log_error "用户取消操作"
                        return 1
                        ;;
                esac
            else
                # 非交互模式，自动强制释放
                log_warn "非交互模式，自动强制释放端口..."
                force_free_port || return 1
            fi

            sleep 1
        fi
    fi

    # 创建日志目录
    ensure_log_dir

    # 切换到应用目录
    cd "$APP_DIR"

    # 激活虚拟环境（关键！）
    activate_venv

    # 设置环境变量
    export PYTHONPATH="$APP_DIR:$PYTHONPATH"

    # 使用虚拟环境中的Python
    if [ -f "${VENV_DIR}/bin/python3" ]; then
        PYTHON_CMD="${VENV_DIR}/bin/python3"
        log_debug "使用虚拟环境Python: $PYTHON_CMD"
    fi

    # 启动命令
    log_info "启动参数: HOST=${HOST}, PORT=${PORT}, WORKERS=${WORKERS}"

    # 使用后台启动
    $PYTHON_CMD -m hypercorn main:app \
        --bind "${HOST}:${PORT}" \
        --workers $WORKERS \
        --access-logfile "$LOG_FILE" \
        --error-logfile "$ERROR_LOG" \
        --log-level info \
        >> "$LOG_FILE" 2>> "$ERROR_LOG" &

    local pid=$!
    echo $pid > "$PID_FILE"

    # 等待启动完成
    sleep 3

    # 验证启动成功
    if is_running; then
        log_info "✅ 服务启动成功!"
        log_info "   PID: ${pid}"
        log_info "   地址: http://${HOST}:${PORT}"
        log_info "   健康检查: http://${HOST}:${PORT}/api/health"
        log_info "   API文档: http://${HOST}:${PORT}/docs"
        log_info ""
        log_info "   日志文件: $LOG_FILE"
        log_info "   PID文件: $PID_FILE"

        # 自动执行健康检查
        sleep 1
        health_check
    else
        log_error "❌ 服务启动失败，请查看日志:"
        log_error "   tail -20 ${ERROR_LOG}"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_service() {
    log_info "正在停止 ${APP_NAME}..."

    if ! is_running; then
        log_warn "服务未在运行"
        rm -f "$PID_FILE"
        return 0
    fi

    local pid=$(get_pid)

    # 尝试优雅停止
    log_info "发送 SIGTERM 信号 (PID: ${pid})..."
    kill -TERM "$pid" 2>/dev/null || true

    # 等待进程结束
    local wait_time=0
    local max_wait=10

    while [ $wait_time -lt $max_wait ]; do
        if ! kill -0 "$pid" 2>/dev/null; then
            break
        fi
        sleep 1
        wait_time=$((wait_time + 1))
    done

    # 如果还没停止，强制杀死
    if kill -0 "$pid" 2>/dev/null; then
        log_warn "优雅停止超时，强制终止..."
        kill -9 "$pid" 2>/dev/null || true
        sleep 1
    fi

    # 清理PID文件
    rm -f "$PID_FILE"

    log_info "✅ 服务已停止"
}

restart_service() {
    log_info "正在重启 ${APP_NAME}..."
    stop_service
    sleep 2
    start_service
}

show_status() {
    echo ""
    echo "=========================================="
    echo "  ${APP_NAME} 服务状态"
    echo "=========================================="
    echo ""

    if is_running; then
        local pid=$(get_pid)
        local uptime=""
        if command -v ps >/dev/null 2>&1; then
            uptime=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ')
        fi

        echo -e "  状态: ${GREEN}● 运行中${NC}"
        echo -e "  PID:  ${pid}"

        if [ -n "$uptime" ]; then
            echo -e "  运行时间: ${uptime}"
        fi

        echo -e "  监听地址: http://${HOST}:${PORT}"
        echo ""

        # 显示端口占用情况
        if command -v lsof >/dev/null 2>&1; then
            echo "  端口信息:"
            lsof -i :$PORT 2>/dev/null | grep LISTEN | awk '{printf "    %-8s %s\n", $1, $9}' | head -5
        fi

        echo ""

        # 自动健康检查
        health_check

    else
        echo -e "  状态: ${RED}○ 未运行${NC}"
        echo ""

        if [ -f "$PID_FILE" ]; then
            log_warn "发现残留的PID文件，正在清理..."
            rm -f "$PID_FILE"
        fi
    fi

    echo "=========================================="
    echo ""
}

show_logs() {
    ensure_log_dir

    if [ ! -f "$LOG_FILE" ]; then
        log_warn "日志文件不存在: $LOG_FILE"
        return 1
    fi

    log_info "显示最新日志 (Ctrl+C 退出):"
    echo "----------------------------------------"
    tail -f "$LOG_FILE" "$ERROR_LOG" 2>/dev/null
}

health_check() {
    local url="http://${HOST}:${PORT}/api/health"

    if ! is_running; then
        log_warn "服务未运行，无法执行健康检查"
        return 1
    fi

    log_info "执行健康检查: ${url}"

    local response
    local http_code
    local time_total

    # 使用curl进行健康检查
    if command -v curl >/dev/null 2>&1; then
        response=$(curl -s -w "\n%{http_code}|%{time_total}" --max-time 10 "$url" 2>/dev/null)
        http_code=$(echo "$response" | tail -1 | cut -d'|' -f1)
        time_total=$(echo "$response" | tail -1 | cut -d'|' -f2)
        body=$(echo "$response" | sed '$d')

        if [ "$http_code" = "200" ]; then
            log_info "✅ 健康检查通过"
            echo -e "   HTTP状态码: ${GREEN}${http_code}${NC}"
            echo -e "   响应时间:   ${GREEN}${time_total}s${NC}"
            echo -e "   响应内容:   ${body}"
            return 0
        else
            log_error "❌ 健康检查失败"
            echo -e "   HTTP状态码: ${RED}${http_code}${NC}"
            return 1
        fi
    else
        log_warn "curl 未安装，尝试使用 wget..."
        if command -v wget >/dev/null 2>&1; then
            wget -qO- --timeout=10 "$url" && log_info "✅ 健康检查通过" || log_error "❌ 健康检查失败"
        else
            log_error "无法执行健康检查（缺少 curl 和 wget）"
            return 1
        fi
    fi
}

# ==================== 主入口 ====================

usage() {
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs|health|help}"
    echo ""
    echo "命令说明:"
    echo "  start    后台启动服务（自动检测并释放被占用的端口）"
    echo "  stop     停止服务"
    echo "  restart  重启服务"
    echo "  status   查看服务状态和健康检查"
    echo "  logs     实时查看日志 (Ctrl+C退出)"
    echo "  health   执行健康检查"
    echo "  help     显示帮助信息"
    echo ""
    echo "特性:"
    echo "  ✅ 自动端口管理：启动时自动检测并释放被占用的端口"
    echo "  ✅ 优雅停止：先发送SIGTERM，超时后强制终止"
    echo "  ✅ 日志管理：自动创建日志目录，分离访问/错误日志"
    echo "  ✅ 健康检查：启动后自动执行健康检查"
    echo "  ✅ 状态监控：显示PID、运行时间、端口占用情况"
    echo ""
    echo "示例:"
    echo "  $0 start       # 启动服务（如果端口被占用会自动处理）"
    echo "  $0 stop        # 停止服务"
    echo "  $0 restart     # 重启服务（等同于 stop + start）"
    echo "  $0 status      # 查看详细状态"
    echo "  $0 logs        # 实时查看日志"
    echo "  $0 health      # 快速健康检查"
    echo ""
    echo "文件位置:"
    echo "  PID文件:   ${APP_DIR}/app.pid"
    echo "  访问日志:  ${APP_DIR}/logs/app.log"
    echo "  错误日志:  ${APP_DIR}/logs/error.log"
    echo ""
}

main() {
    local command="${1:-help}"

    case "$command" in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        health)
            health_check
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            log_error "未知命令: $command"
            usage
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
