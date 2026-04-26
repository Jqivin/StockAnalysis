#!/bin/bash

# A股短线交易系统 - 一键部署脚本

set -e

echo "========================================"
echo "A股短线交易系统 - 一键部署"
echo "========================================"
echo ""

# 检测操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "无法检测操作系统，请手动部署"
    exit 1
fi

echo "检测到操作系统: $OS"
echo ""

# 1. 安装系统依赖
echo "【1/5】安装系统依赖..."
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv git
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
    sudo yum install -y python3 python3-pip git
else
    echo "不支持此操作系统，请手动安装Python"
    exit 1
fi
echo "✅ 系统依赖安装完成"
echo ""

# 2. 创建虚拟环境
echo "【2/5】创建Python虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
else
    echo "✅ 虚拟环境已存在"
fi
echo ""

# 3. 激活虚拟环境并安装Python包
echo "【3/5】安装Python包..."
source venv/bin/activate

# 使用国内镜像源加速
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip

# 安装核心依赖
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pandas \
    numpy \
    akshare \
    baostock \
    schedule \
    matplotlib \
    plotly

echo "✅ Python包安装完成"
echo ""

# 4. 创建配置文件
echo "【4/5】配置文件..."
mkdir -p config logs

if [ ! -f "config/email_config.json" ]; then
    if [ -f "config/email_config.example.json" ]; then
        cp config/email_config.example.json config/email_config.json
        echo "✅ 邮件配置文件已创建: config/email_config.json"
        echo "   请编辑此文件填入你的邮箱信息"
    else
        echo "⚠️  未找到邮件配置模板"
    fi
else
    echo "✅ 邮件配置文件已存在"
fi
echo ""

# 5. 设置脚本权限
echo "【5/5】设置脚本权限..."
chmod +x start_strategy.sh monitor.sh 2>/dev/null || true
echo "✅ 脚本权限设置完成"
echo ""

# 完成
echo "========================================"
echo "部署完成！"
echo "========================================"
echo ""
echo "下一步操作："
echo ""
echo "1. 配置邮箱:"
echo "   nano config/email_config.json"
echo ""
echo "2. 测试邮件:"
echo "   source venv/bin/activate"
echo "   python test_email.py"
echo ""
echo "3. 启动策略:"
echo "   ./start_strategy.sh"
echo ""
echo "4. 后台运行:"
echo "   nohup ./start_strategy.sh > /dev/null 2>&1 &"
echo ""
echo "5. 查看日志:"
echo "   tail -f logs/strategy.log"
echo ""
echo "========================================"
