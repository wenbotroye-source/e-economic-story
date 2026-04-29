#!/bin/bash

# 修图工具 - macOS/Linux 启动脚本
# 使用方法: ./启动工具.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[信息]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

print_info "修图工具 - macOS/Linux 启动脚本"
echo ""

# 检查Python版本
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            print_info "找到 Python $PYTHON_VERSION"
            PYTHON_CMD="python3"
            return 0
        else
            print_error "Python 版本过低: $PYTHON_VERSION (需要 Python 3.8+)"
            return 1
        fi
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            print_info "找到 Python $PYTHON_VERSION"
            PYTHON_CMD="python"
            return 0
        else
            print_error "Python 版本过低: $PYTHON_VERSION (需要 Python 3.8+)"
            return 1
        fi
    else
        print_error "未找到 Python"
        print_info "请先安装 Python 3.8 或更高版本"
        print_info "macOS: brew install python3"
        print_info "Linux: sudo apt-get install python3"
        return 1
    fi
}

# 检查虚拟环境
check_venv() {
    if [ -d ".venv" ]; then
        print_info "找到虚拟环境，正在激活..."
        source .venv/bin/activate
        if [ $? -eq 0 ]; then
            print_info "虚拟环境已激活"
            return 0
        else
            print_warning "虚拟环境激活失败，使用系统 Python"
            return 1
        fi
    else
        print_warning "未找到虚拟环境"
        return 1
    fi
}

# 创建虚拟环境
create_venv() {
    print_info "创建虚拟环境..."
    $PYTHON_CMD -m venv .venv

    if [ $? -eq 0 ]; then
        print_info "虚拟环境创建成功"
        source .venv/bin/activate
        return 0
    else
        print_error "虚拟环境创建失败"
        return 1
    fi
}

# 安装依赖
install_dependencies() {
    print_info "检查依赖..."

    if [ -f "requirements.txt" ]; then
        print_info "发现 requirements.txt，正在安装依赖..."
        pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

        if [ $? -eq 0 ]; then
            print_info "依赖安装完成"
            return 0
        else
            print_error "依赖安装失败"
            return 1
        fi
    else
        print_warning "未找到 requirements.txt，跳过依赖安装"
        return 0
    fi
}

# 启动GUI
start_gui() {
    print_info "启动 GUI 界面..."
    python gui_app.py
}

# 主流程
main() {
    # 1. 检查Python
    if ! check_python; then
        exit 1
    fi

    echo ""

    # 2. 检查或创建虚拟环境
    if ! check_venv; then
        read -p "是否创建虚拟环境? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if ! create_venv; then
                exit 1
            fi
        fi
    fi

    echo ""

    # 3. 安装依赖
    if ! install_dependencies; then
        exit 1
    fi

    echo ""

    # 4. 启动GUI
    start_gui
}

# 运行主流程
main
