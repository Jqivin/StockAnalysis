"""测试整个交易系统"""
import sys
import io

# 设置输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 70)
print("A股短线交易系统 - 系统测试")
print("=" * 70)

# 测试市场情绪判断
print("\n【测试1】市场情绪判断模块...")
from strategy.sentiment import get_market_sentiment

sentiment = get_market_sentiment()
print(f"✅ 情绪等级: {sentiment['sentiment']}")
print(f"✅ 涨停家数: {sentiment['limit_up_count']}")
print(f"✅ 跌停家数: {sentiment['limit_down_count']}")
print(f"✅ 可以交易: {sentiment['can_trade']}")

# 测试板块分析
print("\n【测试2】板块分析模块...")
from strategy.sector import get_sector_analysis

sectors = get_sector_analysis()
print(f"✅ 找到 {len(sectors)} 个热门板块")
for sector in sectors:
    print(f"   - {sector['sector_name']} (+{sector['change']*100:.2f}%)")

# 测试龙头识别
print("\n【测试3】龙头识别模块...")
from strategy.leader import get_all_leaders

leaders = get_all_leaders()
print(f"✅ 找到 {len(leaders)} 只龙头股")
for leader in leaders[:3]:
    print(f"   - {leader['name']} ({leader['code']}) - {leader['leader_type']}")

# 测试股票筛选器
print("\n【测试4】股票筛选器模块...")
from strategy.filter import filter_stocks_by_auction

test_codes = ['000001', '000002', '600000', '600036']
filtered = filter_stocks_by_auction(test_codes)
print(f"✅ 筛选出 {len(filtered)} 只股票")

# 测试开盘监控
print("\n【测试5】开盘监控模块...")
from realtime.tick_monitor import OpeningMonitor

monitor = OpeningMonitor()
monitor.add_stock_to_monitor('000001', 10.0)
monitor.add_stock_to_monitor('000002', 10.0)
results = monitor.monitor_opening(duration=10)  # 只监控10秒测试
print(f"✅ 监控完成")
print(f"   - 强势: {len(results.get('strong_stocks', []))}只")
print(f"   - 分歧: {len(results.get('divergent_stocks', []))}只")
print(f"   - 弱势: {len(results.get('weak_stocks', []))}只")

# 测试邮件推送（模拟）
print("\n【测试6】邮件推送模块...")
from signals.email_notifier import EmailNotifier

notifier = EmailNotifier()
print("✅ 邮件推送模块初始化成功")
print("   （实际发送需要配置config/email_config.json）")

# 测试定时调度器
print("\n【测试7】定时执行模块...")
from scheduler import get_scheduler

scheduler = get_scheduler()
print("✅ 定时调度器初始化成功")
print("   （使用get_scheduler().start()启动定时任务）")

# 测试每日策略
print("\n【测试8】每日策略程序...")
from daily import get_daily_strategy

strategy = get_daily_strategy()
print("✅ 每日策略模块初始化成功")
print("   （使用strategy.run()运行完整流程）")

print("\n" + "=" * 70)
print("系统测试完成！")
print("=" * 70)

print("\n使用说明:")
print("-" * 70)
print("# 1. 手动运行完整流程")
print("python daily.py")
print()
print("# 2. 启动定时任务（8:30自动运行）")
print("from scheduler import start_scheduler, get_scheduler")
print("scheduler = get_scheduler()")
print("scheduler.schedule_daily_report(run_daily_strategy, '08:30')")
print("scheduler.schedule_auction_monitor(auction_monitor_func, '09:15')")
print("scheduler.schedule_opening_monitor(opening_monitor_func, '09:30')")
print("scheduler.start()")
print()
print("# 3. 配置邮件推送（复制并编辑）")
print("cp config/email_config.example.json config/email_config.json")
print("# 然后编辑config/email_config.json填入你的邮箱信息")
print()
print("# 4. 查看规则配置")
print("cat config/rules.json")
print()
print("=" * 70)
