#!/bin/bash

# ========================================
# A股短线交易系统 - Screen启动脚本
# 使用screen让程序在后台持续运行
# ========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
SESSION_NAME="stock_strategy"
WORK_DIR="/root/stock"
PYTHON_CMD="python daily.py"

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "========================================"
echo "A股短线交易系统 - Screen启动脚本"
echo "========================================"
echo ""

# 检查screen是否安装
print_info "检查screen是否安装..."
if ! command -v screen &> /dev/null; then
    print_warning "screen未安装，正在安装..."
    if command -v yum &> /dev/null; then
        yum install -y screen
    elif command -v apt &> /dev/null; then
        apt install -y screen
    else
        print_error "无法自动安装screen，请手动安装"
        exit 1
    fi
    print_success "screen安装完成"
else
    print_success "screen已安装"
fi

# 检查是否已有会话
print_info "检查screen会话..."
if screen -list | grep -q "$SESSION_NAME"; then
    print_warning "会话 '$SESSION_NAME' 已存在"
    echo ""
    echo "现有会话："
    screen -list | grep "$SESSION_NAME"
    echo ""
    echo "请选择操作："
    echo "  1. 重新连接到现有会话"
    echo "  2. 终止现有会话并创建新会话"
    echo "  3. 取消"
    echo ""
    read -p "请输入选项 (1/2/3): " choice

    case $choice in
        1)
            print_info "重新连接到会话..."
            exec screen -r "$SESSION_NAME"
            ;;
        2)
            print_warning "终止现有会话..."
            screen -S "$SESSION_NAME" -X quit
            print_success "会话已终止"
            ;;
        3)
            print_info "操作已取消"
            exit 0
            ;;
        *)
            print_error "无效选项"
            exit 1
            ;;
    esac
fi

# 启动新会话
print_info "创建screen会话: $SESSION_NAME"
cd "$WORK_DIR"

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    print_success "虚拟环境已激活"
else
    print_warning "虚拟环境不存在，正在创建..."

    # 检测系统并安装Python
    if command -v python3 &> /dev/null; then
        python3 -m venv venv
        print_success "虚拟环境创建完成"
        source venv/bin/activate

        # 安装依赖
        print_info "安装Python依赖..."
        pip install -i https://mirrors.aliyun.com/pypi/simple/ \
            pandas numpy akshare baostock schedule -q

        print_success "依赖安装完成"
    else
        print_error "python3未找到，无法创建虚拟环境"
        exit 1
    fi
fi

# 创建启动脚本
cat > /tmp/start_in_screen.sh << 'EOF'
#!/bin/bash
cd /root/stock
source venv/bin/activate

echo "========================================"
echo "策略启动: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""
echo "按 Ctrl+A 然后按 D 可以分离会话（程序继续运行）"
echo ""

# 运行策略
python daily.py
EOF

chmod +x /tmp/start_in_screen.sh

# 启动screen并运行程序
print_info "启动程序..."
screen -dmS "$SESSION_NAME" bash -c "/tmp/start_in_screen.sh; exec bash"

# 等待一下让程序启动
sleep 2

# 检查会话状态
if screen -list | grep -q "$SESSION_NAME"; then
    print_success "程序已在screen会话中启动"
    echo ""
    echo "========================================"
    echo "常用命令："
    echo "========================================"
    echo ""
    echo "1. 查看程序输出（重新连接到screen）："
    echo "   screen -r $SESSION_NAME"
    echo ""
    echo "2. 分离会话（让程序在后台运行）："
    echo "   在screen中按: Ctrl+A, 然后按 D"
    echo ""
    echo "3. 查看所有screen会话："
    echo "   screen -ls"
    echo ""
    echo "4. 查看程序日志："
    echo "   tail -f $WORK_DIR/logs/strategy.log"
    echo ""
    echo "5. 停止程序："
    echo "   screen -S $SESSION_NAME -X quit"
    echo "   或"
    echo "   pkill -f daily.py"
    echo ""
    echo "6. 查看进程："
    echo "   ps aux | grep daily.py | grep -v grep"
    echo ""
    echo "========================================"
    echo ""
    echo "是否现在连接到screen会话查看程序输出？(y/n)"
    read -p "> " connect_now

    if [ "$connect_now" = "y" ] || [ "$connect_now" = "Y" ]; then
        print_info "连接到screen会话..."
        exec screen -r "$SESSION_NAME"
    else
        print_info "程序正在后台运行"
        print_info "使用 'screen -r $SESSION_NAME' 可以连接查看输出"
    fi
else
    print_error "会话创建失败"
    exit 1
fi
