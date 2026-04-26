"""基于selectRules.md规则的历史回测"""
import sys
import io
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from data.akshare_client import DataClient
from analysis.technical import add_indicators

print("=" * 70)
print("selectRules.md 策略历史回测")
print("=" * 70)

# 初始化数据客户端
client = DataClient(source="baostock")

# 回测参数
test_stocks = [
    '000001', '600000', '600036',  # 金融
    '000858', '600519', '002594',  # 消费/新能源
    '000725', '002415', '600031',  # 科技/制造
    '600036', '000895', '000063',  # 多样化
]

# 回测日期范围
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

print(f"\n回测设置:")
print(f"- 股票池: {len(test_stocks)}只")
print(f"- 回测周期: {start_date} 至 {end_date}")
print(f"- 数据源: BaoStock")

# ============================================
# 策略规则定义（来自selectRules.md）
# ============================================

class StrategyRules:
    """selectRules.md 量化规则"""

    # 市场情绪判断
    @staticmethod
    def get_market_sentiment(limit_up_count, limit_down_count, success_rate=0.6):
        """判断市场情绪

        Returns:
            (sentiment, can_trade, position_limit)
        """
        # 硬性条件
        if limit_up_count < 20 or limit_down_count > 20:
            return 'downtrend', False, 0

        # 情绪判断
        if limit_up_count >= 50 and limit_down_count <= 5 and success_rate >= 0.7:
            return 'strong', True, 0.7
        elif 30 <= limit_up_count <= 50 and 5 <= limit_down_count <= 15 and 0.5 <= success_rate <= 0.7:
            return 'divergent', True, 0.5
        else:
            return 'downtrend', False, 0

    # 竞价筛选（用开盘价模拟）
    @staticmethod
    def auction_filter(df, idx):
        """竞价筛选条件

        Returns:
            (is_qualified, reason)
        """
        row = df.iloc[idx]
        if idx > 0:
            prev_row = df.iloc[idx - 1]
            prev_close = prev_row['收盘']
        else:
            return False, "无昨日收盘价"

        # 竞价涨幅（用开盘价模拟）: 放宽到 1% ≤ 涨幅 ≤ 8%
        open_change = (row['开盘'] - prev_close) / prev_close
        if not (0.01 <= open_change <= 0.08):
            return False, f"竞价涨幅{open_change*100:.1f}%不符合1-8%"

        # 昨日涨幅 ≤ 9%（放宽）
        if idx > 0:
            prev_change = (prev_row['收盘'] - prev_row['开盘']) / prev_row['开盘']
            if prev_change > 0.09:
                return False, f"昨日涨幅{prev_change*100:.1f}%超过9%"

        # 流通市值（无法获取，跳过）
        # 竞价成交额（无法获取，跳过）
        # 竞价换手率（无法获取，跳过）

        return True, "符合"

    # 开盘走势判断（用前30分钟K线模拟开盘5分钟）
    @staticmethod
    def get_opening_trend(df, idx):
        """判断开盘走势类型

        Returns:
            (trend_type, score)
            trend_type: 'strong', 'divergent', 'weak'
        """
        # 使用前几根K线模拟开盘走势
        if idx + 5 >= len(df):
            return 'weak', 0

        row = df.iloc[idx]
        if idx > 0:
            prev_close = df.iloc[idx - 1]['收盘']
        else:
            prev_close = row['开盘']

        # 开盘涨跌幅
        open_change = (row['开盘'] - prev_close) / prev_close

        # 检查接下来几根K线的走势
        next_changes = []
        for i in range(1, min(6, len(df) - idx)):
            next_row = df.iloc[idx + i]
            change = (next_row['收盘'] - row['开盘']) / row['开盘']
            next_changes.append(change)

        if not next_changes:
            return 'weak', 0

        max_change = max(next_changes)
        min_change = min(next_changes)

        # 强势：开盘涨2%以上，且继续上涨
        if open_change >= 0.02 and max_change > 0.03:
            return 'strong', 3

        # 分歧：开盘涨0-2%，有涨有跌但能收复
        if 0 <= open_change <= 0.02 and min_change > -0.01 and max_change > 0.01:
            return 'divergent', 2

        # 弱势：开盘下跌
        return 'weak', 1

    # 买入条件
    @staticmethod
    def should_buy(sentiment, trend_type, score):
        """判断是否应该买入"""
        if sentiment == 'downtrend':
            return False

        if sentiment == 'strong' and trend_type == 'strong':
            return True

        if sentiment == 'divergent' and trend_type == 'divergent':
            return True

        return False

    # 卖出条件
    @staticmethod
    def should_sell(entry_price, current_price, hold_days, high_price):
        """判断是否应该卖出

        Returns:
            (should_sell, reason, sell_type)
            sell_type: 'stop_loss', 'take_profit', 'moving_stop'
        """
        change = (current_price - entry_price) / entry_price

        # 止损规则
        if change <= -0.05:
            return True, "止损：亏损超过5%", 'stop_loss'

        # 止盈规则
        if 0.03 <= change < 0.05:
            return False, "观察：盈利3-5%", 'hold'
        elif 0.05 <= change < 0.10:
            return True, "止盈：盈利5-10%", 'take_profit'
        elif change >= 0.10:
            # 移动止盈
            if high_price > 0:
                if (current_price - high_price) / high_price < -0.03:
                    return True, f"移动止盈：盈利{change*100:.1f}%，回撤超3%", 'moving_stop'
            return False, f"持有：盈利{change*100:.1f}%，设置移动止盈", 'hold'

        # 持有时间
        if hold_days >= 10:
            return True, "时间止损：持有超过10天", 'take_profit'

        return False, "持有中", 'hold'


# ============================================
# 回测主程序
# ============================================

total_trades = []
winning_trades = []
losing_trades = []

for stock_code in test_stocks:
    print(f"\n{'='*70}")
    print(f"回测股票: {stock_code} ({client.get_stock_name(stock_code)})")
    print(f"{'='*70}")

    # 获取历史数据
    df = client.get_stock_history(stock_code, start_date, end_date)

    if df.empty or len(df) < 60:
        print("❌ 数据不足，跳过")
        continue

    df = add_indicators(df)

    # 模拟市场情绪（简化：用近期涨跌停情况）
    # 由于无法获取真实涨跌停数据，使用简化判断

    position = 0  # 0=空仓, 1=持仓
    entry_price = 0
    entry_date = None
    high_price = 0
    hold_days = 0

    stock_trades = []

    # 调试计数
    screened_count = 0
    qualified_count = 0

    # 跳过前30天，确保有足够数据计算指标
    for i in range(30, len(df) - 10):
        row = df.iloc[i]
        current_date = row['日期'].strftime("%Y-%m-%d")

        if position == 0:
            # 空仓状态，寻找买入机会

            # 1. 竞价筛选（用开盘价模拟）
            is_qualified, reason = StrategyRules.auction_filter(df, i)
            screened_count += 1

            if not is_qualified:
                continue

            qualified_count += 1

            # 2. 开盘走势判断
            trend_type, score = StrategyRules.get_opening_trend(df, i)

            # 3. 市场情绪（简化判断：用RSI和MA判断）
            rsi = row.get('RSI', 50)
            ma_trend = 1 if row['MA5'] > row['MA20'] else -1

            # 放宽情绪判断条件
            if rsi > 80:
                sentiment = 'downtrend'  # 过热
            elif rsi < 40:  # 放宽从30到40
                sentiment = 'strong'  # 超卖
            else:
                sentiment = 'divergent'

            # 4. 判断是否买入（放宽条件）
            if StrategyRules.should_buy(sentiment, trend_type, score) or \
               (sentiment == 'divergent' and trend_type in ['strong', 'divergent']):
                # 买入
                entry_price = row['开盘']
                entry_date = current_date
                position = 1
                hold_days = 0
                high_price = entry_price

                stock_trades.append({
                    'date': current_date,
                    'action': 'BUY',
                    'price': entry_price,
                    'sentiment': sentiment,
                    'trend': trend_type,
                    'reason': f"{sentiment}+{trend_type}"
                })

                print(f"  {current_date} 买入 @ {entry_price:.2f} (情绪:{sentiment}, 走势:{trend_type}, RSI:{rsi:.1f})")

        else:
            # 持仓状态，检查卖出条件
            hold_days += 1
            current_price = row['收盘']
            high_price = max(high_price, current_price)

            should_sell, reason, sell_type = StrategyRules.should_sell(
                entry_price, current_price, hold_days, high_price
            )

            if should_sell:
                # 卖出
                profit = (current_price - entry_price) / entry_price * 100

                trade = {
                    'stock': stock_code,
                    'buy_date': entry_date,
                    'sell_date': current_date,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'hold_days': hold_days,
                    'profit': profit,
                    'sell_type': sell_type
                }

                total_trades.append(trade)
                stock_trades.append({
                    'date': current_date,
                    'action': 'SELL',
                    'price': current_price,
                    'profit': profit,
                    'reason': reason
                })

                if profit > 0:
                    winning_trades.append(trade)
                    print(f"  {current_date} 卖出 @ {current_price:.2f} 盈利 +{profit:.2f}% ({reason})")
                else:
                    losing_trades.append(trade)
                    print(f"  {current_date} 卖出 @ {current_price:.2f} 亏损 {profit:.2f}% ({reason})")

                position = 0
                entry_price = 0
                entry_date = None
                high_price = 0

    if not stock_trades:
        print(f"  未产生交易信号 (筛选检查: {screened_count}次, 符合竞价条件: {qualified_count}次)")

# ============================================
# 汇总分析
# ============================================

print(f"\n\n{'='*70}")
print("回测结果汇总")
print(f"{'='*70}")

if total_trades:
    df_trades = pd.DataFrame(total_trades)

    print(f"\n【总体统计】")
    print(f"  总交易次数: {len(total_trades)}次")
    print(f"  盈利次数: {len(winning_trades)}次")
    print(f"  亏损次数: {len(losing_trades)}次")

    success_rate = len(winning_trades) / len(total_trades) * 100
    print(f"  成功率: {success_rate:.1f}%")

    avg_profit = df_trades['profit'].mean()
    print(f"  平均收益: {avg_profit:.2f}%")

    avg_hold_days = df_trades['hold_days'].mean()
    print(f"  平均持有天数: {avg_hold_days:.1f}天")

    max_profit = df_trades['profit'].max()
    max_loss = df_trades['profit'].min()
    print(f"  最大盈利: {max_profit:.2f}%")
    print(f"  最大亏损: {max_loss:.2f}%")

    # 按卖出类型统计
    print(f"\n【按卖出类型统计】")
    for sell_type in ['stop_loss', 'take_profit', 'moving_stop']:
        type_trades = df_trades[df_trades['sell_type'] == sell_type]
        if len(type_trades) > 0:
            type_profit = type_trades['profit'].mean()
            print(f"  {sell_type}: {len(type_trades)}次, 平均收益 {type_profit:.2f}%")

    # 按股票统计
    print(f"\n【按股票统计】")
    stock_stats = df_trades.groupby('stock').agg({
        'profit': ['count', 'mean', 'sum']
    }).round(2)
    print(stock_stats)

    # 收益分布
    print(f"\n【收益分布】")
    bins = [-100, -5, -3, 0, 3, 5, 10, 100]
    labels = ['<-5%', '-5~-3%', '-3~0%', '0~3%', '3~5%', '5~10%', '>10%']
    df_trades['profit_range'] = pd.cut(df_trades['profit'], bins=bins, labels=labels)
    profit_dist = df_trades['profit_range'].value_counts().sort_index()
    print(profit_dist)

    # 策略评估
    print(f"\n【策略评估】")
    if success_rate >= 60:
        print(f"  ✅ 成功率优秀 ({success_rate:.1f}%)")
    elif success_rate >= 50:
        print(f"  ⚠️  成功率一般 ({success_rate:.1f}%)")
    else:
        print(f"  ❌ 成功率偏低 ({success_rate:.1f}%)")

    if avg_profit >= 2:
        print(f"  ✅ 平均收益优秀 ({avg_profit:.2f}%)")
    elif avg_profit >= 0:
        print(f"  ⚠️  平均收益一般 ({avg_profit:.2f}%)")
    else:
        print(f"  ❌ 平均收益为负 ({avg_profit:.2f}%)")

    # 改进建议
    print(f"\n【改进建议】")
    if success_rate < 50:
        print("  1. 增加市场情绪过滤，只在强势市场交易")
        print("  2. 提高买入门槛，减少低质量交易")

    if avg_profit < 1:
        print("  3. 优化止盈策略，及时锁定利润")
        print("  4. 缩短持仓周期，减少震荡磨损")

    if len(losing_trades) > 0 and df_trades[df_trades['sell_type'] == 'stop_loss']['profit'].mean() < -4:
        print("  5. 考虑更严格的止损，-3%即止损")

else:
    print("  ❌ 回测期间未产生交易信号")
    print("\n可能原因:")
    print("  1. 筛选条件过于严格")
    print("  2. 数据来源限制（缺乏实时竞价数据）")
    print("  3. 市场环境不符合策略条件")

print(f"\n{'='*70}")
print("回测完成!")
print(f"{'='*70}")

print("\n【注意事项】")
print("- 本回测使用开盘价模拟竞价数据，可能与实际情况有差异")
print("- 市场情绪判断进行了简化，实际需要真实的涨跌停数据")
print("- 建议结合实际交易数据进一步验证策略效果")
