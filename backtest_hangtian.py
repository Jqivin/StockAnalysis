"""航天发展(000547)回测分析"""
import sys
import io

# 设置输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import rcParams
from data.akshare_client import DataClient
from analysis.technical import add_indicators
from backtest.engine import backtest
from backtest.metrics import print_backtest_report

# 设置中文字体
rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

print("=" * 70)
print("航天发展(000547) - 量化回测分析")
print("=" * 70)

# 使用BaoStock获取真实数据
print("\n正在获取航天发展(000547)的真实数据...")
client = DataClient(source="baostock")

# 获取近一年数据
df = client.get_stock_history("000547", start_date="20250425", end_date="20260425")

if df.empty:
    print("未能获取到数据，请稍后重试")
    sys.exit(1)

print(f"成功获取 {len(df)} 条K线数据")
print(f"数据时间范围: {df['日期'].min().strftime('%Y-%m-%d')} 至 {df['日期'].max().strftime('%Y-%m-%d')}")

# 添加技术指标
df = add_indicators(df)

# 显示股票信息
name = client.get_stock_name("000547")
latest = df.iloc[-1]
print(f"\n【{name} (000547)】")
print("-" * 70)
print(f"最新数据 ({latest['日期'].strftime('%Y-%m-%d')}):")
print(f"  收盘价: ¥{latest['收盘']:.2f}")
print(f"  涨跌幅: {((latest['收盘'] - latest['开盘']) / latest['开盘'] * 100):+.2f}%")
print(f"  最高价: ¥{latest['最高']:.2f}")
print(f"  最低价: ¥{latest['最低']:.2f}")
print(f"  成交量: {int(latest['成交量']):,} 股")
print(f"  成交额: {int(latest['成交额']):,} 元")
print("-" * 70)
print(f"  MA5:  {latest.get('MA5', 0):.2f}")
print(f"  MA10: {latest.get('MA10', 0):.2f}")
print(f"  MA20: {latest.get('MA20', 0):.2f}")
print(f"  RSI:  {latest.get('RSI', 0):.2f}")
print(f"  MACD: {latest.get('MACD', 0):.4f}")
print(f"  KDJ:  K={latest.get('K', 0):.2f}, D={latest.get('D', 0):.2f}, J={latest.get('J', 0):.2f}")

# 生成图表
print(f"\n正在生成{name}的技术分析图表...")
fig, axes = plt.subplots(3, 1, figsize=(16, 12))
fig.suptitle(f'000547 {name} - 技术分析图 (BaoStock真实数据)', fontsize=16, fontweight='bold')

# 子图1: K线图 + 均线 + 布林带
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
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

# 子图2: MACD
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
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

# 子图3: RSI
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
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

plt.tight_layout()
plt.savefig('charts/000547_hangtian_chart.png', dpi=150, bbox_inches='tight')
print(f"图表已保存到: charts/000547_hangtian_chart.png")
plt.close()

# 运行回测
print("\n" + "=" * 70)
print("使用真实数据运行回测 - 初始资金 ¥100,000")
print("=" * 70)

strategies = [
    ('MA均线交叉', 'ma', {'short_period': 5, 'long_period': 20}),
    ('MACD金叉死叉', 'macd', {}),
    ('RSI超买超卖', 'rsi', {'oversold': 30, 'overbought': 70}),
    ('布林带突破', 'bollinger', {}),
]

results = []
for strategy_desc, strategy_name, params in strategies:
    print(f"\n【{strategy_desc}策略】")
    print("-" * 70)
    result = backtest(df, strategy_name=strategy_name, initial_capital=100000, **params)
    print_backtest_report(result)
    results.append((strategy_desc, strategy_name, result))

# 详细对比表
print("\n" + "=" * 70)
print("策略对比总结")
print("=" * 70)
print(f"{'策略名称':<16} {'收益率':<12} {'夏普比率':<10} {'最大回撤':<12} {'胜率':<10} {'盈亏比':<10}")
print("-" * 70)

best_return = -float('inf')
best_return_strategy = ""
best_sharpe = -float('inf')
best_sharpe_strategy = ""

for desc, name, result in results:
    ret = result['total_return'] * 100
    sharpe = result.get('sharpe_ratio', 0)
    drawdown = result.get('max_drawdown', 0) * 100
    win_rate = result.get('win_rate', 0) * 100
    profit_factor = result.get('profit_factor', 0)

    print(f"{desc:<16} {ret:>+8.2f}%   {sharpe:>8.2f}   {drawdown:>8.2f}%    {win_rate:>7.2f}%   {profit_factor:>8.2f}")

    if ret > best_return:
        best_return = ret
        best_return_strategy = desc
    if sharpe > best_sharpe:
        best_sharpe = sharpe
        best_sharpe_strategy = desc

print("-" * 70)
print(f"最高收益: {best_return_strategy} ({best_return:+.2f}%)")
print(f"最佳夏普: {best_sharpe_strategy} ({best_sharpe:.2f})")
print("=" * 70)

# 保存数据和交易记录
df.to_csv('000547_hangtian_data.csv', index=False, encoding='utf-8-sig')
print(f"\n数据已保存到: 000547_hangtian_data.csv")

for desc, name, result in results:
    if not result['trades'].empty:
        result['trades'].to_csv(f'000547_hangtian_{name}_trades.csv', index=False, encoding='utf-8-sig')
    if not result['equity_curve'].empty:
        result['equity_curve'].to_csv(f'000547_hangtian_{name}_equity.csv', index=False, encoding='utf-8-sig')

print("交易记录已保存")
print("\n" + "=" * 70)
