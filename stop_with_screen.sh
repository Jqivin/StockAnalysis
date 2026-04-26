#!/bin/bash

# ========================================
# A股短线交易系统 - Screen停止脚本
# ========================================

SESSION_NAME="stock_strategy"

echo "========================================"
echo "停止策略程序"
echo "========================================"
echo ""

# 检查会话是否存在
if ! screen -list 2>/dev/null | grep -q "$SESSION_NAME"; then
    echo "❌ Screen会话 '$SESSION_NAME' 不存在"
    echo ""
    echo "检查进程是否在运行..."
    if pgrep -f "daily.py" > /dev/null; then
        echo "⚠️  发现有daily.py进程在运行"
        echo ""
        read -p "是否强制停止进程？(y/n): " force_kill
        if [ "$force_kill" = "y" ] || [ "$force_kill" = "Y" ]; then
            echo "停止进程..."
            pkill -f daily.py
            echo "✅ 进程已停止"
        fi
    else
        echo "✅ 程序未运行"
    fi
    exit 0
fi

echo "找到Screen会话: $SESSION_NAME"
echo ""
echo "会话详情："
screen -list | grep "$SESSION_NAME"
echo ""

# 停止会话
read -p "确认停止该会话？(y/n): " confirm

if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
    echo "停止Screen会话..."
    screen -S "$SESSION_NAME" -X quit
    echo "✅ Screen会话已停止"
    echo ""

    # 检查进程是否还在运行
    sleep 1
    if pgrep -f "daily.py" > /dev/null; then
        echo "⚠️  检测到进程仍在运行，强制停止..."
        pkill -f daily.py
        echo "✅ 进程已停止"
    else
        echo "✅ 程序已完全停止"
    fi
else
    echo "❌ 操作已取消"
fi

echo ""
echo "查看日志: tail -f /root/stock/logs/strategy.log"
