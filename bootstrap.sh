#!/bin/bash
#
# bootstrap.sh - 股票K线数据服务 启动脚本（前台运行模式）
#
# 使用方法:
#   ./bootstrap.sh start     # 前台启动服务（Ctrl+C 停止）
#   ./bootstrap.sh status    # 查看状态
#   ./bootstrap.sh logs      # 查看日志（实时）
#   ./bootstrap.sh health    # 健康检查
#   ./bootstrap.sh help      # 查看帮助
#

set -e

# ==================== 配置区 ====================

APP_NAME="stock-kline-api"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
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

    # 检查端口
    if ! check_port; then
        log_warn "端口 ${PORT} 被占用"
        # 非交互模式直接尝试释放
        if [ -t 1 ]; then  # 交互式终端，询问用户
            read -p "是否强制终止占用端口的进程？(y/N): " answer
            case $answer in
                [Yy]*)
                    force_free_port || return 1
                    ;;
                *)
                    log_error "用户取消操作，请先手动释放端口 ${PORT}"
                    return 1
                    ;;
            esac
        else
            # 非交互模式，自动释放
            log_warn "非交互模式，自动尝试释放端口..."
            force_free_port || return 1
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
    log_info "监听地址: http://${HOST}:${PORT}"
    log_info "健康检查: http://${HOST}:${PORT}/api/health"
    log_info "API文档:  http://${HOST}:${PORT}/docs"
    log_info "日志文件: $LOG_FILE"
    log_info "按 Ctrl+C 可停止服务"
    log_info ""
    log_info "✅ 服务启动中..."

    # 前台启动（Ctrl+C 直接停止）
    # 2>&1: 把 stderr 合并到 stdout
    # tee -a: 同时显示在终端和写入文件
    $PYTHON_CMD -m hypercorn main:app \
        --bind "${HOST}:${PORT}" \
        --workers $WORKERS \
        --log-level info \
        2>&1 | tee -a "$LOG_FILE"
}

stop_service() {
    log_info "服务为前台运行模式"
    log_warn "请在服务运行的终端窗口按 Ctrl+C 停止服务"
}

restart_service() {
    log_info "服务为前台运行模式"
    log_warn "请先按 Ctrl+C 停止当前服务，然后重新执行: $0 start"
}

show_status() {
    echo ""
    echo "=========================================="
    echo "  ${APP_NAME} 服务状态"
    echo "=========================================="
    echo ""
    echo -e "  运行模式: ${GREEN}● 前台运行${NC}"
    echo "  监听地址: http://${HOST}:${PORT}"
    echo "  工作线程: ${WORKERS}"
    echo ""
    echo "  服务为前台运行模式"
    echo "  启动命令: $0 start"
    echo "  停止命令: 在服务终端按 Ctrl+C"
    echo "  日志文件: $LOG_FILE"
    echo ""

    # 尝试健康检查（如果服务正在跑）
    if command -v curl >/dev/null 2>&1; then
        local url="http://${HOST}:${PORT}/api/health"
        local response
        response=$(curl -s -w "\n%{http_code}|%{time_total}" --max-time 3 "$url" 2>/dev/null)
        local http_code
        local time_total
        http_code=$(echo "$response" | tail -1 | cut -d'|' -f1)
        time_total=$(echo "$response" | tail -1 | cut -d'|' -f2)

        if [ "$http_code" = "200" ]; then
            echo -e "  健康检查: ${GREEN}✅ 正常${NC} (HTTP ${http_code}, ${time_total}s)"
        else
            echo -e "  健康检查: ${YELLOW}○ 未检测到服务${NC}"
        fi
    fi

    echo ""
    echo "=========================================="
    echo ""
}

show_logs() {
    ensure_log_dir

    if [ ! -f "$LOG_FILE" ]; then
        log_warn "日志文件不存在: $LOG_FILE"
        log_warn "请先启动服务: $0 start"
        return 1
    fi

    log_info "显示最新日志 (Ctrl+C 退出):"
    echo "----------------------------------------"
    tail -f "$LOG_FILE"
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
    echo "  start    前台启动服务（Ctrl+C 停止）"
    echo "  stop     停止服务（提示：服务在前台运行，按 Ctrl+C 停止）"
    echo "  restart  重启服务（提示：先按 Ctrl+C 再执行 start）"
    echo "  status   查看服务状态和健康检查"
    echo "  logs     实时查看日志 (Ctrl+C退出)"
    echo "  health   执行健康检查"
    echo "  help     显示帮助信息"
    echo ""
    echo "特性:"
    echo "  ✅ 前台运行模式：直接在当前终端运行，Ctrl+C 可停止"
    echo "  ✅ 自动端口管理：启动时自动检测并释放被占用的端口"
    echo "  ✅ 日志管理：自动创建日志目录，分离访问/错误日志"
    echo "  ✅ 健康检查：随时可执行健康检查"
    echo "  ✅ 状态监控：显示监听地址、工作线程、健康状态"
    echo ""
    echo "示例:"
    echo "  $0 start       # 前台启动服务（Ctrl+C 停止）"
    echo "  $0 stop        # 停止服务提示"
    echo "  $0 restart     # 重启服务提示"
    echo "  $0 status      # 查看详细状态和健康检查"
    echo "  $0 logs        # 实时查看日志"
    echo "  $0 health      # 快速健康检查"
    echo ""
    echo "文件位置:"
    echo "  日志文件:  ${APP_DIR}/logs/app.log"
    echo ""
}

main() {
    local command="${1:-start}"

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
