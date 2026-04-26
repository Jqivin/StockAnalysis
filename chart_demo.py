"""生成K线图表演示"""
import sys
import io

# 设置输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import rcParams

# 设置中文字体
rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv('demo_data.csv')
df['日期'] = pd.to_datetime(df['日期'])

# 创建图表
fig, axes = plt.subplots(3, 1, figsize=(14, 12))
fig.suptitle('DEMO001 - 演示股票技术分析图', fontsize=16, fontweight='bold')

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

# 调整布局
plt.tight_layout()

# 保存图表
filename = 'charts/demo_chart.png'
import os
os.makedirs('charts', exist_ok=True)
plt.savefig(filename, dpi=150, bbox_inches='tight')
print(f"图表已保存到: {filename}")

# 显示最新数据
latest = df.iloc[-1]
print(f"\n最新数据 ({latest['日期'].strftime('%Y-%m-%d')}):")
print(f"收盘价: ¥{latest['收盘']:.2f}")
print(f"MA5: {latest['MA5']:.2f}, MA10: {latest['MA10']:.2f}, MA20: {latest['MA20']:.2f}")
print(f"RSI: {latest['RSI']:.2f}")
print(f"MACD: {latest['MACD']:.4f}")
