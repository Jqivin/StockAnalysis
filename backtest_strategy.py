"""历史回测程序 - 测试策略在历史上的成功率"""
import sys
import io
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 设置输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from data.akshare_client import DataClient
from analysis.technical import add_indicators

print("=" * 70)
print("A股短线交易策略 - 历史回测")
print("=" * 70)

# 测试参数
test_stocks = ['000001', '600000', '600036', '000858']  # 平安银行、浦发银行、招商银行、五粮液
test_days = 60  # 回测最近60天

# 初始化数据客户端（使用BaoStock）
client = DataClient(source="baostock")

print(f"\n回测设置:")
print(f"- 股票: {', '.join(test_stocks)}")
print(f"- 回测周期: 最近{test_days}个交易日")
print(f"- 数据源: BaoStock")


def calculate_success_rate(df, entry_signal_col='ma_cross', hold_days=5):
    """计算策略成功率

    Args:
        df: 包含K线数据的DataFrame
        entry_signal_col: 入场信号列名
        hold_days: 持有天数

    Returns:
        成功率、胜率、平均收益率
    """
    if df.empty or len(df) < hold_days + 10:
        return 0, 0, 0

    df = df.copy()
    df['future_return'] = df['收盘'].pct_change(hold_days).shift(-hold_days)

    # 筛选入场信号
    entries = df[df[entry_signal_col] == True].copy()

    if entries.empty:
        return 0, 0, 0

    # 计算每次交易的收益率
    trade_returns = entries['future_return'].dropna()

    if trade_returns.empty:
        return 0, 0, 0

    # 计算成功率（收益率 > 0 的比例）
    success_count = (trade_returns > 0).sum()
    success_rate = success_count / len(trade_returns) if len(trade_returns) > 0 else 0

    # 计算胜率（收益率 > 2% 的比例）
    win_count = (trade_returns > 0.02).sum()
    win_rate = win_count / len(trade_returns) if len(trade_returns) > 0 else 0

    # 平均收益率
    avg_return = trade_returns.mean()

    return success_rate, win_rate, avg_return


# 回测结果
backtest_results = []

print(f"\n{'='*70}")
print("开始回测...")
print(f"{'='*70}")

for stock_code in test_stocks:
    print(f"\n【股票 {stock_code}】")

    # 获取历史数据
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=test_days * 3)).strftime("%Y-%m-%d")

    df = client.get_stock_history(stock_code, start_date, end_date)

    if df.empty:
        print("❌ 获取数据失败，跳过")
        continue

    # 计算技术指标
    df = add_indicators(df)

    if df is None or df.empty:
        print("❌ 技术指标计算失败，跳过")
        continue

    # 策略1: MA交叉策略
    df['ma_cross'] = (df['MA5'] > df['MA20']) & (df['MA5'].shift(1) <= df['MA20'].shift(1))
    ma_success, ma_win, ma_avg = calculate_success_rate(df, 'ma_cross')

    # 策略2: MACD金叉策略
    df['macd_cross'] = (df['MACD'] > 0) & (df['DIF'] > df['DEA']) & (df['DIF'].shift(1) <= df['DEA'].shift(1))
    macd_success, macd_win, macd_avg = calculate_success_rate(df, 'macd_cross')

    # 策略3: RSI超卖反弹策略
    df['rsi_oversold'] = (df['RSI'] < 30) & (df['RSI'].shift(1) >= 30)
    rsi_success, rsi_win, rsi_avg = calculate_success_rate(df, 'rsi_oversold')

    # 策略4: 均线多头排列策略
    df['ma_bull'] = (df['MA5'] > df['MA10']) & (df['MA10'] > df['MA20']) & (df['MA20'] > df['MA60'])
    bull_success, bull_win, bull_avg = calculate_success_rate(df, 'ma_bull')

    # 记录结果
    stock_name = client.get_stock_name(stock_code)
    backtest_results.append({
        'code': stock_code,
        'name': stock_name,
        'data_points': len(df),
        'ma_cross': (ma_success, ma_win, ma_avg),
        'macd_cross': (macd_success, macd_win, macd_avg),
        'rsi_oversold': (rsi_success, rsi_win, rsi_avg),
        'ma_bull': (bull_success, bull_win, bull_avg)
    })

    print(f"  数据点: {len(df)}天")
    print(f"  MA交叉: 成功率{ma_success*100:.1f}%, 胜率{ma_win*100:.1f}%, 平均收益{ma_avg*100:.2f}%")
    print(f"  MACD金叉: 成功率{macd_success*100:.1f}%, 胜率{macd_win*100:.1f}%, 平均收益{macd_avg*100:.2f}%")
    print(f"  RSI超卖: 成功率{rsi_success*100:.1f}%, 胜率{rsi_win*100:.1f}%, 平均收益{rsi_avg*100:.2f}%")
    print(f"  均线多头: 成功率{bull_success*100:.1f}%, 胜率{bull_win*100:.1f}%, 平均收益{bull_avg*100:.2f}%")

# 汇总结果
print(f"\n{'='*70}")
print("回测结果汇总")
print(f"{'='*70}")

if backtest_results:
    # 计算各策略的平均表现
    ma_successes = [r['ma_cross'][0] for r in backtest_results if r['ma_cross'][0] > 0]
    ma_wins = [r['ma_cross'][1] for r in backtest_results if r['ma_cross'][1] > 0]

    macd_successes = [r['macd_cross'][0] for r in backtest_results if r['macd_cross'][0] > 0]
    macd_wins = [r['macd_cross'][1] for r in backtest_results if r['macd_cross'][1] > 0]

    rsi_successes = [r['rsi_oversold'][0] for r in backtest_results if r['rsi_oversold'][0] > 0]
    rsi_wins = [r['rsi_oversold'][1] for r in backtest_results if r['rsi_oversold'][1] > 0]

    bull_successes = [r['ma_bull'][0] for r in backtest_results if r['ma_bull'][0] > 0]
    bull_wins = [r['ma_bull'][1] for r in backtest_results if r['ma_bull'][1] > 0]

    print("\n【各策略平均表现】")
    if ma_successes:
        print(f"  MA交叉: 平均成功率{np.mean(ma_successes)*100:.1f}%, 平均胜率{np.mean(ma_wins)*100:.1f}%")
    if macd_successes:
        print(f"  MACD金叉: 平均成功率{np.mean(macd_successes)*100:.1f}%, 平均胜率{np.mean(macd_wins)*100:.1f}%")
    if rsi_successes:
        print(f"  RSI超卖: 平均成功率{np.mean(rsi_successes)*100:.1f}%, 平均胜率{np.mean(rsi_wins)*100:.1f}%")
    if bull_successes:
        print(f"  均线多头: 平均成功率{np.mean(bull_successes)*100:.1f}%, 平均胜率{np.mean(bull_wins)*100:.1f}%")

    print("\n【策略推荐】")
    best_strategy = None
    best_score = 0

    if ma_successes:
        score = np.mean(ma_successes) * 0.4 + np.mean(ma_wins) * 0.6
        if score > best_score:
            best_score = score
            best_strategy = "MA交叉"

    if macd_successes:
        score = np.mean(macd_successes) * 0.4 + np.mean(macd_wins) * 0.6
        if score > best_score:
            best_score = score
            best_strategy = "MACD金叉"

    if rsi_successes:
        score = np.mean(rsi_successes) * 0.4 + np.mean(rsi_wins) * 0.6
        if score > best_score:
            best_score = score
            best_strategy = "RSI超卖"

    if bull_successes:
        score = np.mean(bull_successes) * 0.4 + np.mean(bull_wins) * 0.6
        if score > best_score:
            best_score = score
            best_strategy = "均线多头"

    if best_strategy:
        print(f"  推荐策略: {best_strategy} (综合评分: {best_score*100:.1f}分)")
    else:
        print("  数据不足，无法推荐策略")

print(f"\n{'='*70}")
print("回测完成!")
print(f"{'='*70}")

print("\n注意事项:")
print("- 回测结果基于历史数据，不代表未来表现")
print("- 实际交易需要考虑交易成本、滑点等因素")
print("- 建议结合多个指标和市场环境进行综合判断")
print("- 短线交易风险较高，请谨慎操作")
