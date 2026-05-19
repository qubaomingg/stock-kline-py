#!/bin/bash
#
# install.sh - 股票K线数据服务 依赖安装脚本
#
# 使用方法:
#   ./install.sh              # 标准安装（推荐）
#   ./install.sh --force     # 强制重装所有依赖
#   ./install.sh --dev       # 安装开发依赖
#   ./install.sh --check     # 仅检查依赖，不安装
#   ./install.sh --clean     # 清理虚拟环境后重新安装
#

set -e

# ==================== 配置区 ====================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
VENV_DIR="${PROJECT_DIR}/venv"
REQUIREMENTS_FILE="${PROJECT_DIR}/requirements.txt"

PYTHON_VERSION="3.11"           # 最低Python版本要求
PIP_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"  # 清华镜像源（国内加速）
PIP_TRUSTED_HOST="pypi.tuna.tsinghua.edu.cn"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

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

log_header() {
    echo ""
    echo -e "${CYAN}==========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}==========================================${NC}"
    echo ""
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ==================== 环境检查 ====================

check_python_version() {
    log_info "检查Python版本..."

    if ! command_exists python3; then
        log_error "未找到 python3，请先安装 Python 3.11+"
        exit 1
    fi

    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local major=$(echo $python_version | cut -d'.' -f1)
    local minor=$(echo $python_version | cut -d'.' -f2)

    log_info "当前Python版本: ${python_version}"

    if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 11 ]); then
        log_error "Python版本过低: ${python_version} (需要 >= 3.11)"
        log_error "请升级Python或使用正确的Python版本"
        exit 1
    fi

    log_info "✅ Python版本满足要求 (>= 3.11)"
    return 0
}

check_pip() {
    log_info "检查pip..."

    if ! command_exists pip3; then
        log_warn "pip3 未找到，尝试使用 python3 -m pip..."

        if ! python3 -m pip --version >/dev/null 2>&1; then
            log_error "pip也未安装，请先安装pip"
            log_error "运行: python3 -m ensurepip --upgrade"
            exit 1
        fi

        PIP_CMD="python3 -m pip"
    else
        PIP_CMD="pip3"
    fi

    log_info "✅ pip可用: $(eval $PIP_CMD --version | head -1)"
}

# ==================== 虚拟环境管理 ====================

create_venv() {
    if [ -d "$VENV_DIR" ]; then
        log_info "虚拟环境已存在: $VENV_DIR"
        return 0
    fi

    log_info "创建虚拟环境..."
    python3 -m venv "$VENV_DIR"

    if [ $? -ne 0 ]; then
        log_error "创建虚拟环境失败"
        exit 1
    fi

    log_info "✅ 虚拟环境创建成功: $VENV_DIR"
}

activate_venv() {
    if [ ! -f "${VENV_DIR}/bin/activate" ]; then
        return 1
    fi

    source "${VENV_DIR}/bin/activate"
    log_debug "已激活虚拟环境: $VENV_DIR"
    return 0
}

clean_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log_info "虚拟环境不存在，无需清理"
        return 0
    fi

    log_warn "确定要删除虚拟环境吗？(y/N)"
    read -r answer
    case $answer in
        [Yy]*)
            log_info "删除虚拟环境: $VENV_DIR"
            rm -rf "$VENV_DIR"
            log_info "✅ 虚拟环境已删除"
            ;;
        *)
            log_info "取消删除操作"
            ;;
    esac
}

# ==================== 依赖安装 ====================

upgrade_pip() {
    log_info "升级pip到最新版本..."

    eval $PIP_CMD install --upgrade pip -i "$PIP_INDEX_URL" --trusted-host "$PIP_TRUSTED_HOST" -q

    if [ $? -ne 0 ]; then
        log_warn "pip升级失败，继续安装依赖..."
    else
        log_info "✅ pip已升级到最新版本"
    fi
}

install_dependencies() {
    local force_install="$1"

    log_header "安装项目依赖"

    # 检查requirements.txt是否存在
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        log_error "requirements.txt 不存在: $REQUIREMENTS_FILE"
        exit 1
    fi

    log_info "依赖文件: $REQUIREMENTS_FILE"

    # 统计依赖数量
    local total_deps=$(grep -E '^[a-zA-Z0-9]' "$REQUIREMENTS_FILE" | wc -l | tr -d ' ')
    log_info "待安装依赖数: ${total_deps}"

    # 安装参数
    local install_args=""
    if [ "$force_install" = "--force" ]; then
        log_warn "强制重装模式：将重新安装所有依赖"
        install_args="--force-reinstall"  # 移除 --no-deps，保留依赖关系
    else
        install_args=""
    fi

    log_info "开始安装依赖..."
    log_info "使用镜像源: $PIP_INDEX_URL"
    echo ""

    # 执行安装
    eval $PIP_CMD install \
        -r "$REQUIREMENTS_FILE" \
        -i "$PIP_INDEX_URL" \
        --trusted-host "$PIP_TRUSTED_HOST" \
        $install_args \
        --no-cache-dir \
        --disable-pip-version-check \
        2>&1 | tee /tmp/pip_install.log | while IFS= read -r line; do
            if echo "$line" | grep -q "Successfully installed"; then
                log_info "  ✅ $(echo $line | sed 's/Successfully installed//')"
            elif echo "$line" | grep -q "Requirement already satisfied"; then
                log_debug "  ⏭️  $(echo $line | sed 's/Requirement already satisfied//')"
            fi
        done

    # 检查安装结果
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_error "❌ 依赖安装失败！"
        log_error "详细日志:"
        tail -30 /tmp/pip_install.log
        return 1
    fi

    log_info ""
    log_info "✅ 依赖安装完成！"
    return 0
}

install_dev_dependencies() {
    log_info "安装开发依赖..."

    # 开发工具
    eval $PIP_CMD install \
        pytest>=7.0.0 \
        pytest-cov>=4.0.0 \
        black>=23.0.0 \
        flake8>=6.0.0 \
        mypy>=1.0.0 \
        -i "$PIP_INDEX_URL" \
        --trusted-host "$PIP_TRUSTED_HOST" \
        -q

    log_info "✅ 开发依赖安装完成"
}

# ==================== 验证 ====================

verify_installation() {
    log_header "验证安装结果"

    local failed=0
    local success=0

    # 逐个检查关键依赖
    log_info "检查关键依赖..."
    echo ""

    # FastAPI
    if python3 -c "import fastapi; print(f'✅ FastAPI: v{fastapi.__version__}')" 2>/dev/null; then
        ((success++)) || true
    else
        log_error "❌ FastAPI: 未安装"
        ((failed++)) || true
    fi

    # Hypercorn
    if python3 -c "import hypercorn" 2>/dev/null; then
        local hypercorn_version=$(pip show hypercorn 2>/dev/null | grep Version | awk '{print $2}')
        log_info "✅ Hypercorn: v${hypercorn_version}"
        ((success++)) || true
    else
        log_error "❌ Hypercorn: 未安装"
        ((failed++)) || true
    fi

    # AkShare
    if python3 -c "import akshare; print(f'✅ AkShare: v{akshare.__version__}')" 2>/dev/null; then
        ((success++)) || true
    else
        log_error "❌ AkShare: 未安装"
        ((failed++)) || true
    fi

    # Baostock
    if python3 -c "import baostock" 2>/dev/null; then
        log_info "✅ Baostock: 已安装"
        ((success++)) || true
    else
        log_error "❌ Baostock: 未安装"
        ((failed++)) || true
    fi

    # PyMongo
    if python3 -c "import pymongo; print(f'✅ PyMongo: v{pymongo.__version__}')" 2>/dev/null; then
        ((success++)) || true
    else
        log_error "❌ PyMongo: 未安装"
        ((failed++)) || true
    fi

    # OpenBB
    if python3 -c "import openbb" 2>/dev/null; then
        log_info "✅ OpenBB: 已安装"
        ((success++)) || true
    else
        log_warn "⚠️  OpenBB: 未安装（可选）"
    fi

    # Pandas
    if python3 -c "import pandas; print(f'✅ Pandas: v{pandas.__version__}')" 2>/dev/null; then
        ((success++)) || true
    else
        log_error "❌ Pandas: 未安装"
        ((failed++)) || true
    fi

    # Python-dotenv
    if python3 -c "import dotenv" 2>/dev/null; then
        log_info "✅ Python-dotenv: 已安装"
        ((success++)) || true
    else
        log_warn "⚠️  Python-dotenv: 未安装"
    fi

    echo ""
    log_info "验证结果: ${success:-0} 成功, ${failed:-0} 失败"

    if [ "${failed:-0}" -gt 0 ]; then
        log_warn "⚠️  有 ${failed} 个关键依赖安装失败"
        return 1
    fi

    log_info "🎉 所有关键依赖已正确安装！"
    return 0
}

show_installed_packages() {
    log_header "已安装的包列表"

    eval $PIP_CMD list --format=columns 2>/dev/null | head -50

    local total=$(eval $PIP_CMD list 2>/dev/null | wc -l | tr -d ' ')
    log_info ""
    log_info "总计: ${total} 个包"
}

# ==================== 主功能 ====================

do_install() {
    local force_flag="${1:-}"

    log_header "🚀 开始安装股票K线数据服务依赖"
    log_info "项目目录: $PROJECT_DIR"
    log_info "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # 步骤1: 检查Python环境
    check_python_version
    check_pip
    echo ""

    # 步骤2: 创建并激活虚拟环境
    create_venv
    activate_venv
    echo ""

    # 步骤3: 升级pip
    upgrade_pip
    echo ""

    # 步骤4: 安装依赖
    install_dependencies "$force_flag"

    if [ $? -ne 0 ]; then
        log_error "安装失败，请检查日志"
        exit 1
    fi
    echo ""

    # 步骤5: 验证安装
    verify_installation
    echo ""

    # 完成
    log_header "🎉 安装完成！"
    log_info "下一步操作:"
    log_info "  1. 启动服务: ./bootstrap.sh start"
    log_info "  2. 测试健康检查: curl http://localhost:8000/api/health"
    log_info "  3. 查看API文档: http://localhost:8000/docs"
    echo ""
}

do_check() {
    log_header "🔍 检查依赖状态"

    # 尝试激活虚拟环境
    if [ -f "${VENV_DIR}/bin/activate" ]; then
        source "${VENV_DIR}/bin/activate"
        log_info "已激活虚拟环境: $VENV_DIR"
    else
        log_warn "未找到虚拟环境，使用系统Python"
    fi

    verify_installation

    if [ $? -eq 0 ]; then
        echo ""
        log_info "💡 提示: 使用 './bootstrap.sh start' 启动服务"
    fi

    show_installed_packages
}

do_clean() {
    log_header "🧹 清理环境"

    clean_venv

    # 清理缓存
    log_info "清理pip缓存..."
    eval $PIP_CMD cache purge 2>/dev/null || true

    # 清理临时文件
    rm -f /tmp/pip_install.log

    log_info "✅ 清理完成"
}

# ==================== 帮助信息 ====================

usage() {
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  (无参数)      标准安装（推荐首次使用）"
    echo "  --force       强制重装所有依赖（忽略已有版本）"
    echo "  --dev         安装额外开发工具（pytest, black等）"
    echo "  --check       仅检查依赖是否正确安装"
    echo "  --list        列出所有已安装的包及版本"
    echo "  --clean       删除虚拟环境并清理缓存"
    echo "  --help,-h     显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                  # 首次安装"
    echo "  $0 --force          # 更新或修复损坏的依赖"
    echo "  $0 --dev            # 开发环境安装"
    echo "  $0 --check          # 快速检查依赖状态"
    echo "  $0 --clean          # 完全清理后重新安装"
    echo ""
    echo "特性:"
    echo "  ✅ 自动检测Python版本（需要>=3.11）"
    echo "  ✅ 自动创建和管理虚拟环境"
    echo "  ✅ 使用清华镜像源加速下载"
    echo "  ✅ 强制重装模式（解决依赖冲突）"
    echo "  ✅ 详细安装进度和错误提示"
    echo "  ✅ 安装后自动验证关键依赖"
    echo ""
    echo "文件位置:"
    echo "  项目目录: $PROJECT_DIR"
    echo "  依赖文件: $REQUIREMENTS_FILE"
    echo "  虚拟环境: $VENV_DIR"
    echo ""
}

# ==================== 主入口 ====================

main() {
    local command="${1:-}"

    cd "$PROJECT_DIR"

    case "$command" in
        ""|--install)
            do_install ""
            ;;
        --force)
            do_install "--force"
            ;;
        --dev)
            do_install ""
            activate_venv
            install_dev_dependencies
            ;;
        --check)
            activate_venv 2>/dev/null || true
            do_check
            ;;
        --list)
            activate_venv 2>/dev/null || true
            show_installed_packages
            ;;
        --clean)
            do_clean
            ;;
        --help|-h|help)
            usage
            ;;
        *)
            log_error "未知选项: $command"
            usage
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
