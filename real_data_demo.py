"""使用BaoStock真实数据演示"""
import sys
import io

# 设置输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import pandas as pd
import matplotlib.pyplot as plt
from data.akshare_client import DataClient
from analysis.technical import add_indicators
from backtest.engine import backtest
from backtest.metrics import print_backtest_report

print("=" * 60)
print("A股量化分析工具 - BaoStock真实数据模式")
print("=" * 60)

# 使用BaoStock获取真实数据
print("\n正在获取真实数据...")
client = DataClient(source="baostock")

# 获取平安银行近一年数据
df = client.get_stock_history("000001", start_date="20250425", end_date="20260425")

if df.empty:
    print("未能获取到数据，请稍后重试")
    sys.exit(1)

print(f"成功获取 {len(df)} 条K线数据")
print(f"数据时间范围: {df['日期'].min().strftime('%Y-%m-%d')} 至 {df['日期'].max().strftime('%Y-%m-%d')}")

# 显示最新数据
latest = df.iloc[-1]
name = client.get_stock_name("000001")
print(f"\n股票代码: 000001 - {name}")
print("-" * 60)
print(f"日期: {latest['日期'].strftime('%Y-%m-%d')}")
print(f"收盘价: ¥{latest['收盘']:.2f}")
print(f"涨跌幅: {((latest['收盘'] - latest['开盘']) / latest['开盘'] * 100):.2f}%")
print(f"成交量: {int(latest['成交量']):,}")
print(f"成交额: {int(latest['成交额']):,}")

# 添加技术指标
df = add_indicators(df)

print("-" * 60)
print(f"MA5: {latest.get('MA5', 0):.2f}")
print(f"MA10: {latest.get('MA10', 0):.2f}")
print(f"MA20: {latest.get('MA20', 0):.2f}")
print(f"RSI: {latest.get('RSI', 0):.2f}")
print(f"MACD: {latest.get('MACD', 0):.4f}")
print(f"KDJ: K={latest.get('K', 0):.2f}, D={latest.get('D', 0):.2f}, J={latest.get('J', 0):.2f}")

# 生成图表
print("\n正在生成K线图表...")
fig, axes = plt.subplots(3, 1, figsize=(14, 12))
fig.suptitle(f'000001 {name} - 技术分析图 (BaoStock真实数据)', fontsize=16, fontweight='bold')

# K线图 + 均线 + 布林带
ax1 = axes[0]
ax1.plot(df['日期'], df['收盘'], label='收盘价', linewidth=1.5, color='black')
ax1.plot(df['日期'], df['MA5'], label='MA5', linewidth=1, alpha=0.7, color='red')
ax1.plot(df['日期'], df['MA10'], label='MA10', linewidth=1, alpha=0.7, color='orange')
ax1.plot(df['日期'], df['MA20'], label='MA20', linewidth=1, alpha=0.7, color='blue')
ax1.fill_between(df['日期'], df['lower'], df['upper'], alpha=0.1, color='gray', label='布林带')
ax1.set_ylabel('价格 (元)', fontsize=12)
ax1.set_title('价格走势与均线', fontsize=14)
ax1.legend(loc='upper left', fontsize=10)
ax1.grid(True, alpha=0.3)

# MACD
ax2 = axes[1]
ax2.plot(df['日期'], df['DIF'], label='DIF', linewidth=1, color='blue')
ax2.plot(df['日期'], df['DEA'], label='DEA', linewidth=1, color='orange')
colors = ['red' if x >= 0 else 'green' for x in df['MACD']]
ax2.bar(df['日期'], df['MACD'], label='MACD', alpha=0.5, color=colors)
ax2.set_ylabel('MACD', fontsize=12)
ax2.set_title('MACD指标', fontsize=14)
ax2.legend(loc='upper left', fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)

# RSI
ax3 = axes[2]
ax3.plot(df['日期'], df['RSI'], label='RSI', linewidth=1.5, color='purple')
ax3.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='超买线(70)')
ax3.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='超卖线(30)')
ax3.set_ylabel('RSI', fontsize=12)
ax3.set_xlabel('日期', fontsize=12)
ax3.set_title('RSI相对强弱指标', fontsize=14)
ax3.set_ylim(0, 100)
ax3.legend(loc='upper left', fontsize=10)
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('charts/000001_real_chart.png', dpi=150, bbox_inches='tight')
print("图表已保存到: charts/000001_real_chart.png")
plt.close()

# 运行回测
print("\n" + "=" * 60)
print("使用真实数据运行回测")
print("=" * 60)

strategies = [
    ('ma', {'short_period': 5, 'long_period': 20}),
    ('macd', {}),
    ('rsi', {'oversold': 30, 'overbought': 70}),
]

results = []
for strategy_name, params in strategies:
    print(f"\n【{strategy_name.upper()}策略】")
    result = backtest(df, strategy_name=strategy_name, initial_capital=100000, **params)
    print_backtest_report(result)
    results.append((strategy_name, result))

# 总结
print("\n" + "=" * 60)
print("策略对比总结")
print("=" * 60)
print(f"{'策略':<12} {'收益率':<12} {'夏普比率':<12} {'最大回撤':<12} {'胜率':<10}")
print("-" * 60)

for name, result in results:
    print(f"{name.upper():<12} {result['total_return']*100:>8.2f}%   "
          f"{result.get('sharpe_ratio', 0):>8.2f}     "
          f"{result.get('max_drawdown', 0)*100:>8.2f}%    "
          f"{result.get('win_rate', 0)*100:>7.2f}%")

# 保存数据
df.to_csv('000001_real_data.csv', index=False, encoding='utf-8-sig')
print("\n真实数据已保存到: 000001_real_data.csv")
print("=" * 60)
