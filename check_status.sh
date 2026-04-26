#!/bin/bash

# ========================================
# A股短线交易系统 - 状态检查脚本
# ========================================

SESSION_NAME="stock_strategy"
WORK_DIR="/root/stock"
LOG_FILE="$WORK_DIR/logs/strategy.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================"
echo "A股短线交易系统 - 状态检查"
echo "========================================"
echo ""

# 1. 检查进程状态
echo "【1】进程状态"
echo "----------------------------------------"
if pgrep -f "daily.py" > /dev/null; then
    PID=$(pgrep -f "daily.py" | head -n 1)
    echo -e "${GREEN}✓ 程序正在运行${NC}"
    echo "  PID: $PID"
    echo "  运行时间: $(ps -p $PID -o etime= | tail -n 1 | xargs)"
    echo "  内存使用: $(ps -p $PID -o rss= | tail -n 1 | xargs) KB"
    echo "  CPU使用: $(ps -p $PID -o %cpu= | tail -n 1 | xargs)%"
else
    echo -e "${RED}✗ 程序未运行${NC}"
fi
echo ""

# 2. 检查Screen会话
echo "【2】Screen会话"
echo "----------------------------------------"
if screen -list 2>/dev/null | grep -q "$SESSION_NAME"; then
    echo -e "${GREEN}✓ Screen会话存在${NC}"
    echo "  会话名称: $SESSION_NAME"
    echo ""
    screen -list | grep "$SESSION_NAME"
else
    echo -e "${YELLOW}○ Screen会话不存在${NC}"
fi
echo ""

# 3. 检查日志文件
echo "【3】日志文件"
echo "----------------------------------------"
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(du -h "$LOG_FILE" | cut -f1)
    LOG_LINES=$(wc -l < "$LOG_FILE")
    echo -e "${GREEN}✓ 日志文件存在${NC}"
    echo "  路径: $LOG_FILE"
    echo "  大小: $LOG_SIZE"
    echo "  行数: $LOG_LINES"
    echo ""
    echo "  最后5行日志:"
    tail -n 5 "$LOG_FILE" | sed 's/^/    /'
else
    echo -e "${YELLOW}○ 日志文件不存在${NC}"
fi
echo ""

# 4. 检查虚拟环境
echo "【4】Python环境"
echo "----------------------------------------"
if [ -d "$WORK_DIR/venv" ]; then
    echo -e "${GREEN}✓ 虚拟环境存在${NC}"
    echo "  路径: $WORK_DIR/venv"

    if [ -f "$WORK_DIR/venv/bin/python" ]; then
        PYTHON_VER=$($WORK_DIR/venv/bin/python --version 2>&1)
        echo "  版本: $PYTHON_VER"
    fi

    # 检查关键包
    if [ -f "$WORK_DIR/venv/bin/pip" ]; then
        echo ""
        echo "  已安装的关键包:"
        source "$WORK_DIR/venv/bin/activate" 2>/dev/null
        pip list 2>/dev/null | grep -E "pandas|numpy|akshare|baostock|schedule" | sed 's/^/    /'
    fi
else
    echo -e "${RED}✗ 虚拟环境不存在${NC}"
fi
echo ""

# 5. 检查配置文件
echo "【5】配置文件"
echo "----------------------------------------"
if [ -f "$WORK_DIR/config/email_config.json" ]; then
    echo -e "${GREEN}✓ 邮件配置存在${NC}"

    # 检查是否配置了邮箱
    SENDER=$(grep '"sender_email"' "$WORK_DIR/config/email_config.json" | cut -d'"' -f4)
    if [ "$SENDER" != "your_email@163.com" ] && [ -n "$SENDER" ]; then
        echo "  发件人: $SENDER"
    else
        echo -e "${YELLOW}  ⚠ 需要配置邮箱${NC}"
    fi
else
    echo -e "${YELLOW}○ 邮件配置不存在${NC}"
fi
echo ""

# 6. 快速操作
echo "========================================"
echo "【快速操作】"
echo "========================================"
echo ""
echo "启动程序: ./run_with_screen.sh"
echo "停止程序: ./stop_with_screen.sh"
echo "查看日志: ./view_logs.sh"
echo ""
echo "连接Screen: screen -r $SESSION_NAME"
echo "分离Screen: 在screen中按 Ctrl+A, 然后按 D"
echo "查看进程: ps aux | grep daily.py"
echo ""
echo "========================================"
