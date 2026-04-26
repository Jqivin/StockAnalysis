#!/bin/bash

# ========================================
# A股短线交易系统 - 查看日志脚本
# ========================================

WORK_DIR="/root/stock"
LOG_FILE="$WORK_DIR/logs/strategy.log"
ERROR_LOG="$WORK_DIR/logs/error.log"

echo "========================================"
echo "查看策略日志"
echo "========================================"
echo ""

# 检查日志文件
if [ ! -f "$LOG_FILE" ]; then
    echo "❌ 日志文件不存在: $LOG_FILE"
    echo "请先启动策略程序"
    exit 1
fi

echo "请选择查看方式："
echo "  1. 实时查看日志（类似 tail -f）"
echo "  2. 查看最近50行"
echo "  3. 查看最近100行"
echo "  4. 查看最近200行"
echo "  5. 查看错误日志"
echo "  6. 搜索日志内容"
echo "  7. 查看今天的日志"
echo "  0. 退出"
echo ""
read -p "请输入选项: " choice

case $choice in
    1)
        echo "📡 实时查看日志（按 Ctrl+C 退出）..."
        tail -f "$LOG_FILE"
        ;;
    2)
        echo "📄 最近50行日志："
        echo "========================================"
        tail -n 50 "$LOG_FILE"
        ;;
    3)
        echo "📄 最近100行日志："
        echo "========================================"
        tail -n 100 "$LOG_FILE"
        ;;
    4)
        echo "📄 最近200行日志："
        echo "========================================"
        tail -n 200 "$LOG_FILE"
        ;;
    5)
        echo "📄 错误日志："
        echo "========================================"
        if [ -f "$ERROR_LOG" ]; then
            tail -n 50 "$ERROR_LOG"
        else
            echo "错误日志不存在"
        fi
        ;;
    6)
        read -p "请输入搜索关键词: " keyword
        echo "🔍 搜索结果: '$keyword'"
        echo "========================================"
        grep "$keyword" "$LOG_FILE" | tail -n 20
        ;;
    7)
        today=$(date +%Y-%m-%d)
        echo "📅 今天的日志 ($today):"
        echo "========================================"
        grep "$today" "$LOG_FILE" | tail -n 50
        ;;
    0)
        echo "退出"
        exit 0
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
