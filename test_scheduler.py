"""测试定时调度功能"""
import sys
import io
import time
from datetime import datetime, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from scheduler import Scheduler, get_scheduler
from signals.email_notifier import EmailNotifier

print("=" * 70)
print("定时调度功能测试")
print("=" * 70)

# 创建调度器实例
scheduler = Scheduler()

# 定义测试任务
def test_task_1():
    """测试任务1 - 模拟每日报告"""
    print(f"\n{'='*70}")
    print(f"【执行任务1】每日报告生成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

    # 发送测试邮件
    notifier = EmailNotifier()
    report = {
        'date': datetime.now().strftime("%Y-%m-%d"),
        'limit_up_count': 45,
        'limit_down_count': 8,
        'success_rate': 0.65,
        'broken_rate': 0.22,
        'sentiment': 'divergent',
        'advice': '控制仓位',
        'sectors': [
            {
                'sector_name': '测试板块A',
                'change': 0.035,
                'limit_up_count': 5,
                'logic': '测试逻辑',
                'leader': {'name': '测试股', 'code': '000000'}
            }
        ],
        'auction_results': [],
        'opening_strategy': '测试策略',
        'risk_warnings': []
    }

    result = notifier.send_daily_report(report)
    print(f"  邮件发送: {'✅ 成功' if result else '❌ 失败'}")

def test_task_2():
    """测试任务2 - 模拟竞价监控"""
    print(f"\n{'='*70}")
    print(f"【执行任务2】竞价监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    print("  监控竞价数据...")
    print("  筛选候选股票...")
    print("  ✅ 竞价监控完成")

def test_task_3():
    """测试任务3 - 模拟开盘监控"""
    print(f"\n{'='*70}")
    print(f"【执行任务3】开盘监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    print("  监控开盘5分钟走势...")
    print("  判断强势/分歧/弱势...")
    print("  ✅ 开盘监控完成")

# 设置定时任务
print("\n【配置定时任务】")

# 方式1：使用schedule类方法设置
print("\n1. 设置每日8:30执行每日报告任务...")
current_time = datetime.now()
target_time = current_time + timedelta(seconds=10)  # 10秒后执行（用于测试）
time_str = target_time.strftime("%H:%M")
scheduler.schedule_daily_report(test_task_1, time_str)
print(f"   已设置：{time_str} 执行每日报告")

# 设置间隔任务
print("\n2. 设置每15秒执行一次的间隔任务...")
scheduler.schedule_interval(test_task_2, 15, "竞价监控")

# 设置开盘监控任务（模拟）
print("\n3. 设置开盘监控任务...")
target_time_2 = current_time + timedelta(seconds=20)
time_str_2 = target_time_2.strftime("%H:%M")
scheduler.schedule_opening_monitor(test_task_3, time_str_2)
print(f"   已设置：{time_str_2} 执行开盘监控")

# 显示已设置的任务
print(f"\n【已设置的定时任务】")
print(f"  下次执行时间: {scheduler.get_next_run_time().strftime('%Y-%m-%d %H:%M:%S') if scheduler.get_next_run_time() else '无'}")

# 启动调度器
print(f"\n【启动调度器】")
print("  调度器正在运行...")
print(f"  等待任务执行（最长等待30秒）...")
print(f"{'-'*70}")

scheduler.start()

# 等待任务执行
wait_seconds = 30
start_wait = time.time()

try:
    while time.time() - start_wait < wait_seconds:
        time.sleep(1)
        # 每隔5秒显示一次状态
        elapsed = int(time.time() - start_wait)
        if elapsed % 5 == 0 and elapsed > 0:
            next_run = scheduler.get_next_run_time()
            if next_run:
                remaining = (next_run - datetime.now()).total_seconds()
                if remaining > 0:
                    print(f"  等待中... 距离下次执行还有 {remaining:.1f} 秒")
except KeyboardInterrupt:
    print("\n  用户中断")

# 停止调度器
print(f"\n{'-'*70}")
print(f"【停止调度器】")
scheduler.stop()
print("  ✅ 调度器已停止")

print(f"\n{'='*70}")
print("测试完成!")
print(f"{'='*70}")

print(f"\n【使用说明】")
print("-" * 70)
print("实际使用时，可以这样设置定时任务：")
print()
print("```python")
print("from scheduler import get_scheduler")
print("from daily import run_daily_strategy")
print()
print("# 获取调度器实例")
print("scheduler = get_scheduler()")
print()
print("# 设置每日8:30执行每日策略")
print("scheduler.schedule_daily_report(run_daily_strategy, '08:30')")
print()
print("# 设置9:15执行竞价监控")
print("def auction_monitor():")
print("    from daily import get_daily_strategy")
print("    strategy = get_daily_strategy()")
print("    strategy.run_auction_analysis()")
print("scheduler.schedule_auction_monitor(auction_monitor, '09:15')")
print()
print("# 设置9:30执行开盘监控")
print("def opening_monitor():")
print("    from daily import get_daily_strategy")
print("    strategy = get_daily_strategy()")
print("    strategy.run_opening_monitoring()")
print("scheduler.schedule_opening_monitor(opening_monitor, '09:30')")
print()
print("# 启动调度器")
print("scheduler.start()")
print()
print("# 调度器会在后台持续运行，按设定时间执行任务")
print("```")
print()
print(f"{'='*70}")
