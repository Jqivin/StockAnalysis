#!/bin/bash

# ========================================
# A股短线交易系统 - 一键启动脚本
# 自动完成：创建环境、安装依赖、启动程序
# ========================================

set -e

SESSION_NAME="stock_strategy"
WORK_DIR="/root/StockAnalysis"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
echo "A股短线交易系统 - 一键启动"
echo "========================================"
echo ""

# 切换到工作目录
cd "$WORK_DIR"

# 1. 检查Python
print_info "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    print_error "python3未找到"
    print_info "尝试安装Python..."
    if command -v yum &> /dev/null; then
        yum install -y python3 python3-pip
    elif command -v apt &> /dev/null; then
        apt update && apt install -y python3 python3-pip python3-venv
    fi
fi
print_success "Python版本: $(python3 --version)"

# 2. 创建/检查虚拟环境
print_info "检查虚拟环境..."
if [ ! -d "venv" ]; then
    print_warning "虚拟环境不存在，正在创建..."
    python3 -m venv venv
    print_success "虚拟环境创建完成"
else
    print_success "虚拟环境已存在"
fi

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 检查并安装依赖
print_info "检查Python依赖..."
MISSING_PACKAGES=0

for pkg in pandas numpy akshare baostock schedule; do
    if ! python -c "import $pkg" 2>/dev/null; then
        print_warning "$pkg 未安装"
        MISSING_PACKAGES=1
    fi
done

if [ $MISSING_PACKAGES -eq 1 ]; then
    print_info "安装缺失的依赖包..."
    pip install -i https://mirrors.aliyun.com/pypi/simple/ \
        pandas numpy akshare baostock schedule -q
    print_success "依赖包安装完成"
else
    print_success "所有依赖包已安装"
fi

# 5. 检查screen
print_info "检查screen..."
if ! command -v screen &> /dev/null; then
    print_warning "screen未安装，正在安装..."
    if command -v yum &> /dev/null; then
        yum install -y screen
    elif command -v apt &> /dev/null; then
        apt install -y screen
    fi
fi
print_success "screen已就绪"

# 6. 检查配置文件
print_info "检查配置文件..."
mkdir -p logs config
if [ ! -f "config/email_config.json" ]; then
    if [ -f "config/email_config.example.json" ]; then
        cp config/email_config.example.json config/email_config.json
        print_warning "已创建默认邮箱配置，请记得修改"
    else
        print_warning "创建默认配置文件..."
        cat > config/email_config.json << 'EOF'
{
  "smtp_server": "smtp.163.com",
  "smtp_port": 465,
  "sender_email": "your_email@163.com",
  "sender_password": "your_authorization_code",
  "receiver_emails": ["receiver@example.com"]
}
EOF
    fi
fi
print_success "配置文件就绪"

# 7. 检查screen会话
print_info "检查screen会话..."
if screen -list 2>/dev/null | grep -q "$SESSION_NAME"; then
    print_warning "会话 '$SESSION_NAME' 已存在"
    echo ""
    screen -list | grep "$SESSION_NAME"
    echo ""
    read -p "是否终止现有会话并重新启动？(y/n): " restart
    if [ "$restart" = "y" ] || [ "$restart" = "Y" ]; then
        print_info "终止现有会话..."
        screen -S "$SESSION_NAME" -X quit
        sleep 1
    else
        print_info "操作取消"
        print_info "使用 'screen -r $SESSION_NAME' 连接到现有会话"
        exit 0
    fi
fi

# 8. 启动程序
print_info "启动程序..."

# 创建启动脚本
cat > /tmp/start_stock.sh << 'EOF'
#!/bin/bash
cd /root/stock
source venv/bin/activate

echo "========================================"
echo "策略启动: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 运行策略
python daily.py
EOF

chmod +x /tmp/start_stock.sh

# 在screen中启动
screen -dmS "$SESSION_NAME" bash -c "/tmp/start_stock.sh; exec bash"

# 等待启动
sleep 3

# 9. 检查启动状态
echo ""
echo "========================================"
echo "启动结果"
echo "========================================"
echo ""

if screen -list 2>/dev/null | grep -q "$SESSION_NAME"; then
    print_success "程序已启动"

    if pgrep -f "daily.py" > /dev/null; then
        print_success "进程运行中: $(pgrep -f 'daily.py' | wc -l) 个"
    else
        print_warning "screen会话已创建，但进程可能未正常启动"
    fi

    echo ""
    echo "========================================"
    echo "后续操作"
    echo "========================================"
    echo ""
    echo "1. 查看程序输出:"
    echo "   screen -r $SESSION_NAME"
    echo ""
    echo "2. 分离会话（让程序在后台运行）:"
    echo "   在screen中按: Ctrl+A, 然后按 D"
    echo ""
    echo "3. 查看日志:"
    echo "   tail -f $WORK_DIR/logs/strategy.log"
    echo ""
    echo "4. 查看状态:"
    echo "   ./check_status.sh"
    echo ""
    echo "5. 停止程序:"
    echo "   ./stop_with_screen.sh"
    echo ""
    echo "========================================"
else
    print_error "启动失败，请检查日志"
    echo ""
    echo "查看日志:"
    tail -50 "$WORK_DIR/logs/strategy.log"
fi
