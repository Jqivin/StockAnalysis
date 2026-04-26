#!/bin/bash

# A股短线交易系统 - 监控脚本

# 设置工作目录
cd "$(dirname "$0")"

# 检查进程是否运行
if pgrep -f "daily.py" > /dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 策略运行正常" >> logs/monitor.log
    exit 0
fi

# 进程未运行，记录并重启
echo "$(date '+%Y-%m-%d %H:%M:%S') - ⚠️  策略进程未运行，正在重启..." >> logs/monitor.log

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate

    # 重启策略
    nohup python daily.py >> logs/strategy.log 2>&1 &

    echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ 策略已重启，PID: $!" >> logs/monitor.log

    # 发送告警邮件
    if [ -f "config/email_config.json" ]; then
        python -c "
from signals.email_notifier import EmailNotifier
notifier = EmailNotifier()
notifier._send_email('【告警】策略已自动重启', '策略进程检测到异常，已自动重启。\\n时间: $(date '+%Y-%m-%d %H:%M:%S')')
" 2>/dev/null || true
    fi
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ❌ 重启失败：虚拟环境不存在" >> logs/monitor.log
fi
