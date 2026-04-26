#!/bin/bash

# A股短线交易系统 - 启动脚本

# 设置工作目录
cd "$(dirname "$0")"

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "错误：虚拟环境不存在，请先运行 deploy.sh"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 记录启动信息
echo "========================================" >> logs/strategy.log
echo "策略启动时间: $(date '+%Y-%m-%d %H:%M:%S')" >> logs/strategy.log
echo "========================================" >> logs/strategy.log

# 运行策略
echo "正在启动A股短线交易策略..."
python daily.py 2>&1 | tee -a logs/strategy.log
