@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo A股短线交易系统 - 一键部署工具
echo 服务器: 60.205.188.111 (root用户)
echo ========================================
echo.

REM 设置变量
set SERVER_IP=60.205.188.111
set SERVER_USER=root
set LOCAL_DIR=%~dp0
set REMOTE_DIR=/root/stock

echo 本地目录: %LOCAL_DIR%
echo 服务器: %SERVER_USER%@%SERVER_IP%
echo 远程目录: %REMOTE_DIR%
echo.

REM 检查tar命令
where tar >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到tar命令
    echo 请安装Git for Windows或使用WSL
    pause
    exit /b 1
)

echo ========================================
echo 步骤1: 压缩项目文件
echo ========================================
cd /d "%LOCAL_DIR%"

echo 正在压缩项目...
REM 创建临时目录
if not exist temp mkdir temp

REM 压缩项目（排除不需要的文件）
tar -czf temp/stock.tar.gz ^
    --exclude='venv' ^
    --exclude='logs' ^
    --exclude='__pycache__' ^
    --exclude='*.pyc' ^
    --exclude='.git' ^
    --exclude='temp' ^
    --exclude='stock.tar.gz' ^
    .

if errorlevel 1 (
    echo ❌ 压缩失败
    pause
    exit /b 1
)

echo ✅ 压缩完成: temp\stock.tar.gz
echo.

echo ========================================
echo 步骤2: 上传到服务器
echo ========================================
echo 正在上传到 %SERVER_USER%@%SERVER_IP%...
echo 这可能需要几分钟，请耐心等待...
echo.

REM 使用scp上传
scp -o StrictHostKeyChecking=no temp/stock.tar.gz %SERVER_USER%@%SERVER_IP%:/tmp/

if errorlevel 1 (
    echo.
    echo ❌ 上传失败
    echo.
    echo 请检查:
    echo   1. 服务器IP是否正确: %SERVER_IP%
    echo   2. 网络连接是否正常
    echo   3. SSH服务是否运行
    echo   4. 是否知道root密码或已配置SSH密钥
    echo.
    echo 如果使用密码登录，会提示输入密码
    pause
    exit /b 1
)

echo ✅ 上传完成
echo.

echo ========================================
echo 步骤3: 在服务器上执行部署
echo ========================================
echo 正在远程执行部署...
echo 这可能需要几分钟，请等待...
echo.

REM 在服务器上执行部署
ssh -o StrictHostKeyChecking=no %SERVER_USER%@%SERVER_IP% << 'ENDSSH'
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}开始远程部署${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 创建工作目录
mkdir -p /root/stock
cd /root/stock

# 备份旧配置（如果存在）
if [ -f "config/email_config.json" ]; then
    cp config/email_config.json /tmp/email_config.json.backup
    echo -e "${YELLOW}已备份原有邮箱配置${NC}"
fi

# 解压项目
echo "正在解压项目文件..."
tar -xzf /tmp/stock.tar.gz

# 恢复配置（如果存在备份）
if [ -f "/tmp/email_config.json.backup" ]; then
    cp /tmp/email_config.json.backup config/email_config.json
    echo -e "${GREEN}已恢复原有邮箱配置${NC}"
fi

# 清理临时文件
rm -f /tmp/stock.tar.gz

# 检测系统并安装依赖
echo ""
echo "检测系统类型..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    echo "系统: $OS $VERSION"
else
    echo -e "${RED}无法检测系统类型${NC}"
    OS="unknown"
fi

echo ""
echo "安装系统依赖..."
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-venv git wget > /dev/null 2>&1
    echo -e "${GREEN}依赖安装完成 (apt)${NC}"
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "almalinux" ]; then
    yum install -y python3 python3-pip git wget > /dev/null 2>&1
    if ! command -v python3 &> /dev/null; then
        dnf install -y python3 python3-pip git wget > /dev/null 2>&1
    fi
    echo -e "${GREEN}依赖安装完成 (yum/dnf)${NC}"
elif [ "$OS" = "fedora" ]; then
    dnf install -y python3 python3-pip git wget > /dev/null 2>&1
    echo -e "${GREEN}依赖安装完成 (dnf)${NC}"
else
    echo -e "${YELLOW}跳过依赖安装 (未知系统)${NC}"
fi

# 创建虚拟环境
echo ""
echo "创建Python虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}虚拟环境创建完成${NC}"
else
    echo -e "${GREEN}虚拟环境已存在${NC}"
fi

# 激活虚拟环境并安装依赖
echo ""
echo "安装Python依赖包..."
source venv/bin/activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip -q > /dev/null 2>&1

pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pandas \
    numpy \
    akshare \
    baostock \
    schedule \
    matplotlib \
    plotly \
    -q > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Python依赖安装完成${NC}"
else
    echo -e "${RED}Python依赖安装失败${NC}"
    exit 1
fi

# 创建配置文件
echo ""
echo "配置项目..."
mkdir -p logs config

# 创建邮件配置（如果不存在）
if [ ! -f "config/email_config.json" ]; then
    if [ -f "config/email_config.example.json" ]; then
        cp config/email_config.example.json config/email_config.json
        echo -e "${GREEN}邮件配置已创建 (从模板)${NC}"
    else
        echo -e "${YELLOW}创建默认邮件配置${NC}"
        cat > config/email_config.json << 'CONFEOF'
{
  "smtp_server": "smtp.163.com",
  "smtp_port": 465,
  "sender_email": "your_email@163.com",
  "sender_password": "your_authorization_code",
  "receiver_emails": ["receiver@example.com"]
}
CONFEOF
        echo -e "${GREEN}默认配置已创建${NC}"
    fi
else
    echo -e "${GREEN}邮件配置已存在${NC}"
fi

# 设置脚本权限
chmod +x start_strategy.sh monitor.sh deploy.sh auto_deploy.sh 2>/dev/null || true

# 测试
echo ""
echo "测试安装..."
python --version
echo "Python环境: $(which python)"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}部署成功！${NC}"
echo -e "${GREEN}========================================${NC}"

ENDSSH

if errorlevel 1 (
    echo.
    echo ❌ 远程部署失败
    pause
    exit /b 1
)

# 清理临时文件
rd /s /q temp 2>nul

echo.
echo ========================================
echo 🎉 部署完成！
echo ========================================
echo.
echo 下一步操作:
echo.
echo 1. 登录服务器:
echo    ssh root@60.205.188.111
echo.
echo 2. 配置邮箱:
echo    cd /root/stock
echo    nano config/email_config.json
echo.
echo 3. 测试邮件:
echo    source venv/bin/activate
echo    python test_email.py
echo.
echo 4. 启动策略:
echo    nohup python daily.py > logs/strategy.log 2>&1 &
echo.
echo 5. 查看日志:
echo    tail -f logs/strategy.log
echo.
echo ========================================
echo.

pause
