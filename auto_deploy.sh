#!/bin/bash

# ========================================
# A股短线交易系统 - 一键部署脚本
# 服务器: 60.205.188.111
# ========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
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

print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo ""
}

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    print_warning "建议使用root用户运行此脚本"
    print_warning "当前用户: $(whoami)"
fi

# 工作目录
WORK_DIR="/root/StockAnalysis"

print_header "A股短线交易系统 - 一键部署"

# 1. 检查系统
print_info "检查系统环境..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
    print_success "系统: $OS $VERSION"
else
    print_error "无法检测系统类型"
    exit 1
fi

# 2. 安装系统依赖
print_header "步骤 1/7: 安装系统依赖"
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    print_info "使用apt安装依赖..."
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-venv git wget
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "almalinux" ]; then
    print_info "使用yum安装依赖..."
    yum install -y python3 python3-pip git wget
    # CentOS 8可能需要使用dnf
    if ! command -v python3 &> /dev/null; then
        dnf install -y python3 python3-pip git wget
    fi
elif [ "$OS" = "fedora" ]; then
    print_info "使用dnf安装依赖..."
    dnf install -y python3 python3-pip git wget
else
    print_warning "未知系统，跳过依赖安装"
fi
print_success "系统依赖安装完成"

# 3. 创建工作目录
print_header "步骤 2/7: 创建工作目录"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"
print_success "工作目录: $WORK_DIR"

# 4. 检查项目文件
print_header "步骤 3/7: 检查项目文件"
if [ -f "daily.py" ]; then
    print_success "项目文件已存在"
else
    print_error "未找到项目文件 daily.py"
    print_info "请先上传项目文件到 $WORK_DIR"
    print_info "上传命令: scp -r stock/ root@60.205.188.111:$WORK_DIR/"
    exit 1
fi

# 5. 创建虚拟环境
print_header "步骤 4/7: 创建Python虚拟环境"
if [ ! -d "venv" ]; then
    print_info "创建虚拟环境..."
    python3 -m venv venv
    print_success "虚拟环境创建完成"
else
    print_success "虚拟环境已存在"
fi

# 6. 安装Python依赖
print_header "步骤 5/7: 安装Python依赖"
source venv/bin/activate

# 升级pip
print_info "升级pip..."
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip -q

# 安装核心依赖
print_info "安装核心依赖包..."
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pandas \
    numpy \
    akshare \
    baostock \
    schedule \
    matplotlib \
    plotly \
    -q

print_success "Python依赖安装完成"

# 7. 创建配置文件
print_header "步骤 6/7: 配置项目"
mkdir -p logs config

# 邮件配置
if [ ! -f "config/email_config.json" ]; then
    if [ -f "config/email_config.example.json" ]; then
        cp config/email_config.example.json config/email_config.json
        print_success "邮件配置文件已创建"
    else
        print_warning "未找到邮件配置模板，创建默认配置..."
        cat > config/email_config.json << 'EOF'
{
  "smtp_server": "smtp.163.com",
  "smtp_port": 465,
  "sender_email": "your_email@163.com",
  "sender_password": "your_authorization_code",
  "receiver_emails": ["receiver@example.com"]
}
EOF
        print_success "默认邮件配置已创建"
    fi
else
    print_success "邮件配置文件已存在"
fi

# 设置脚本权限
chmod +x start_strategy.sh monitor.sh deploy.sh 2>/dev/null || true

# 8. 测试安装
print_header "步骤 7/7: 测试安装"
print_info "测试Python环境..."
python --version
print_info "已安装的包:"
pip list | grep -E "pandas|numpy|akshare|baostock|schedule"

# 9. 完成提示
print_header "部署完成！"

echo ""
echo "下一步操作:"
echo ""
echo "1. 配置邮箱:"
echo "   nano $WORK_DIR/config/email_config.json"
echo "   填入你的163邮箱和授权码"
echo ""
echo "2. 测试邮件发送:"
echo "   cd $WORK_DIR"
echo "   source venv/bin/activate"
echo "   python test_email.py"
echo ""
echo "3. 启动策略:"
echo "   cd $WORK_DIR"
echo "   source venv/bin/activate"
echo "   nohup python daily.py > logs/strategy.log 2>&1 &"
echo ""
echo "4. 查看日志:"
echo "   tail -f $WORK_DIR/logs/strategy.log"
echo ""
echo "5. 查看进程:"
echo "   ps aux | grep daily.py"
echo ""
echo "6. 停止策略:"
echo "   pkill -f daily.py"
echo ""
echo "========================================"

# 10. 提示配置邮箱
print_warning "请记得配置邮箱后再启动策略！"
print_info "配置文件: $WORK_DIR/config/email_config.json"
