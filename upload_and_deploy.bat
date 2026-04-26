@echo off
chcp 65001 >nul
echo ========================================
echo A股短线交易系统 - 自动部署
echo 服务器: 60.205.188.111
echo ========================================
echo.

REM 设置变量
set SERVER_IP=60.205.188.111
set SERVER_USER=root
set REMOTE_DIR=/home/stock
set LOCAL_DIR=D:\01_Jqivin\stock

REM 询问用户名
set /p SERVER_USER="请输入服务器用户名 (默认root): "
if "%SERVER_USER%"=="" set SERVER_USER=root

echo.
echo ========================================
echo 步骤1: 压缩项目文件
echo ========================================

cd /d %LOCAL_DIR%

REM 创建临时目录
if not exist temp mkdir temp

REM 压缩项目（排除venv和日志）
echo 正在压缩项目文件...
tar -czf temp/stock.tar.gz --exclude='venv' --exclude='logs' --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' .
if errorlevel 1 (
    echo ❌ 压缩失败
    pause
    exit /b 1
)
echo ✅ 压缩完成
echo.

echo ========================================
echo 步骤2: 上传到服务器
echo ========================================
echo 正在上传到 %SERVER_USER%@%SERVER_IP%...
echo.

REM 使用scp上传
scp temp/stock.tar.gz %SERVER_USER%@%SERVER_IP%:/tmp/
if errorlevel 1 (
    echo ❌ 上传失败
    echo 请确保:
    echo   1. 服务器IP正确: %SERVER_IP%
    echo   2. 服务器SSH服务已启动
    echo   3. 已配置SSH密钥或知道密码
    pause
    exit /b 1
)
echo ✅ 上传完成
echo.

echo ========================================
echo 步骤3: 在服务器上部署
echo ========================================
echo 正在远程执行部署脚本...
echo.

REM 在服务器上执行部署命令
ssh %SERVER_USER%@%SERVER_IP% << 'ENDSSH'
    set -e

    echo "1. 创建项目目录..."
    mkdir -p /home/stock
    cd /home/stock

    echo "2. 解压项目文件..."
    tar -xzf /tmp/stock.tar.gz

    echo "3. 清理临时文件..."
    rm -f /tmp/stock.tar.gz

    echo "4. 安装系统依赖..."
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y python3 python3-pip python3-venv git
    elif command -v yum &> /dev/null; then
        yum install -y python3 python3-pip git
    fi

    echo "5. 创建虚拟环境..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    echo "6. 激活虚拟环境并安装依赖..."
    source venv/bin/activate
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pandas numpy akshare baostock schedule

    echo "7. 创建配置文件..."
    mkdir -p logs config
    if [ ! -f "config/email_config.json" ] && [ -f "config/email_config.example.json" ]; then
        cp config/email_config.example.json config/email_config.json
    fi

    echo "8. 设置脚本权限..."
    chmod +x start_strategy.sh monitor.sh deploy.sh 2>/dev/null || true

    echo "✅ 部署完成！"
ENDSSH

if errorlevel 1 (
    echo ❌ 远程部署失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 部署成功！
echo ========================================
echo.
echo 下一步操作:
echo.
echo 1. 登录服务器配置邮箱:
echo    ssh %SERVER_USER%@%SERVER_IP%
echo    cd /home/stock
echo    nano config/email_config.json
echo.
echo 2. 测试邮件发送:
echo    source venv/bin/activate
echo    python test_email.py
echo.
echo 3. 启动策略:
echo    ./start_strategy.sh
echo.
echo 4. 后台运行:
echo    nohup ./start_strategy.sh > /dev/null 2>&1 &
echo.
echo ========================================

REM 清理临时文件
rd /s /q temp 2>nul

pause
