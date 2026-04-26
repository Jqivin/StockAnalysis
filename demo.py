"""使用模拟数据演示功能"""
import sys
import io

# 设置输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from analysis.technical import add_indicators
from backtest.engine import backtest
from backtest.metrics import print_backtest_report


def generate_mock_data(days: int = 252, start_price: float = 10.0) -> pd.DataFrame:
    """生成模拟股票数据

    Args:
        days: 天数
        start_price: 起始价格

    Returns:
        模拟K线数据
    """
    np.random.seed(42)

    dates = [datetime.now() - timedelta(days=i) for i in range(days)][::-1]
    prices = [start_price]

    for _ in range(days - 1):
        change = np.random.normal(0, 0.02)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 0.1))

    df = pd.DataFrame({
        '日期': dates,
        '开盘': [p * (1 + np.random.uniform(-0.01, 0.01)) for p in prices],
        '收盘': prices,
        '最高': [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
        '最低': [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
        '成交量': [int(np.random.uniform(100000, 1000000)) for _ in range(days)]
    })

    df['最高'] = df[['开盘', '收盘', '最高']].max(axis=1)
    df['最低'] = df[['开盘', '收盘', '最低']].min(axis=1)

    return df


def main():
    """演示主函数"""
    print("=" * 60)
    print("A股量化分析工具 - 演示模式")
    print("=" * 60)

    # 生成模拟数据
    print("\n生成模拟股票数据...")
    df = generate_mock_data(days=252, start_price=10.0)

    # 显示最新数据
    latest = df.iloc[-1]
    print(f"\n股票代码: DEMO001 - 演示股票")
    print("-" * 60)
    print(f"日期: {latest['日期'].strftime('%Y-%m-%d')}")
    print(f"收盘价: ¥{latest['收盘']:.2f}")
    print(f"涨跌幅: {((latest['收盘'] - latest['开盘']) / latest['开盘'] * 100):.2f}%")
    print(f"成交量: {latest['成交量']:,}")

    # 添加技术指标
    df = add_indicators(df)

    print("-" * 60)
    print(f"MA5: {latest.get('MA5', 0):.2f}")
    print(f"MA10: {latest.get('MA10', 0):.2f}")
    print(f"MA20: {latest.get('MA20', 0):.2f}")
    print(f"RSI: {latest.get('RSI', 0):.2f}")
    print(f"MACD: {latest.get('MACD', 0):.4f}")

    # 运行回测
    print("\n" + "=" * 60)
    print("运行回测 - 均线交叉策略")
    print("=" * 60)
    result = backtest(df, strategy_name='ma', initial_capital=100000,
                     short_period=5, long_period=20)
    print_backtest_report(result)

    # 运行其他策略
    print("\n" + "=" * 60)
    print("运行回测 - MACD策略")
    print("=" * 60)
    result = backtest(df, strategy_name='macd', initial_capital=100000)
    print_backtest_report(result)

    print("\n" + "=" * 60)
    print("运行回测 - RSI策略")
    print("=" * 60)
    result = backtest(df, strategy_name='rsi', initial_capital=100000,
                     oversold=30, overbought=70)
    print_backtest_report(result)

    # 保存数据
    df.to_csv('demo_data.csv', index=False, encoding='utf-8-sig')
    print("\n模拟数据已保存到: demo_data.csv")


if __name__ == '__main__':
    main()
