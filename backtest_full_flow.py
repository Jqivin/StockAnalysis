"""完整流程回测 - 模拟selectRules.md的三重筛选（市场→板块→个股）"""
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
print("selectRules.md 完整流程回测")
print("(市场情绪 → 板块筛选 → 竞价选股 → 开盘决策)")
print("=" * 70)

# 初始化数据客户端
client = DataClient(source="baostock")

# 扩大股票池 - 包含不同板块的代表股票
# 按板块分类
stock_pool = {
    # 金融板块
    '金融': ['000001', '600000', '600036', '601398', '601318', '600016'],
    # 消费板块
    '消费': ['000858', '600519', '002594', '000568', '600887', '600690'],
    # 科技板块
    '科技': ['000725', '002415', '000063', '002230', '300059', '300750'],
    # 医药板块
    '医药': ['000661', '600276', '300015', '002007', '300760', '603259'],
    # 新能源
    '新能源': ['300750', '002460', '688111', '300124', '002812', '601012'],
    # 制造业
    '制造': ['600031', '000333', '002008', '300433', '600104', '000651'],
    # 周期股
    '周期': ['000895', '600585', '601899', '000708', '600309', '601898'],
    # 军工
    '军工': ['600893', '000768', '002025', '300722', '600502', '002151'],
}

# 展平股票列表
all_stocks = []
for sector, stocks in stock_pool.items():
    for stock in stocks:
        all_stocks.append({'code': stock, 'sector': sector})

print(f"\n股票池配置:")
for sector, stocks in stock_pool.items():
    print(f"  {sector}: {len(stocks)}只")
print(f"  总计: {len(all_stocks)}只股票")

# 回测日期范围
end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

print(f"\n回测周期: {start_date} 至 {end_date}")

# ============================================
# 策略规则
# ============================================

class FullFlowStrategy:
    """完整流程策略"""

    @staticmethod
    def calculate_market_sentiment_with_idx(stock_data_dict):
        """计算市场情绪（带索引版本）

        Args:
            stock_data_dict: {code: {'df': df, 'idx': idx}}

        Returns:
            (sentiment, can_trade, limit_up_count, limit_down_count)
        """
        total_changes = []

        for code, data in stock_data_dict.items():
            df = data['df']
            idx = data['idx']

            if idx >= 1:
                # 使用指定索引计算涨跌
                current_price = df.iloc[idx]['收盘']
                prev_price = df.iloc[idx-1]['收盘']
                change = (current_price - prev_price) / prev_price
                total_changes.append(change)

        if not total_changes:
            return 'downtrend', False, 0, 0

        avg_change = np.mean(total_changes)
        up_count = sum(1 for c in total_changes if c > 0)
        down_count = sum(1 for c in total_changes if c < 0)
        strong_up_count = sum(1 for c in total_changes if c >= 0.05)
        strong_down_count = sum(1 for c in total_changes if c <= -0.05)

        # 放宽情绪判断条件，使用实际涨跌分布
        total = len(total_changes)
        up_ratio = up_count / total if total > 0 else 0

        # 情绪判断（进一步放宽）
        if (up_ratio >= 0.5 and avg_change > 0.005) or strong_up_count >= 4:
            return 'strong', True, strong_up_count, strong_down_count
        elif up_ratio >= 0.35 and avg_change > -0.01:
            return 'divergent', True, strong_up_count, strong_down_count
        else:
            return 'downtrend', False, strong_up_count, strong_down_count

    @staticmethod
    def calculate_market_sentiment(stock_data_dict):
        """计算市场情绪（基于股票池的整体表现）

        Returns:
            (sentiment, can_trade, limit_up_count, limit_down_count)
        """
        total_changes = []

        for code, df in stock_data_dict.items():
            if len(df) > 0:
                # 计算当日涨跌
                if len(df) > 1:
                    last_row = df.iloc[-1]
                    prev_row = df.iloc[-2]
                    change = (last_row['收盘'] - prev_row['收盘']) / prev_row['收盘']
                    total_changes.append(change)

        if not total_changes:
            return 'downtrend', False, 0, 0

        avg_change = np.mean(total_changes)
        up_count = sum(1 for c in total_changes if c > 0)
        down_count = sum(1 for c in total_changes if c < 0)
        strong_up_count = sum(1 for c in total_changes if c >= 0.05)
        strong_down_count = sum(1 for c in total_changes if c <= -0.05)

        # 放宽情绪判断条件，使用实际涨跌分布
        total = len(total_changes)
        up_ratio = up_count / total if total > 0 else 0

        # 情绪判断（进一步放宽）
        if (up_ratio >= 0.5 and avg_change > 0.005) or strong_up_count >= 4:
            return 'strong', True, strong_up_count, strong_down_count
        elif up_ratio >= 0.35 and avg_change > -0.01:
            return 'divergent', True, strong_up_count, strong_down_count
        else:
            return 'downtrend', False, strong_up_count, strong_down_count

    @staticmethod
    def filter_hot_sectors(stock_data_dict):
        """筛选热门板块

        Returns:
            排序后的板块列表 [(sector_name, change, limit_up_count), ...]
        """
        sector_stats = {}

        for code, df in stock_data_dict.items():
            if len(df) < 2:
                continue

            # 找到这只股票属于哪个板块
            sector = None
            for s, stocks in stock_pool.items():
                if code in stocks:
                    sector = s
                    break

            if not sector:
                continue

            # 计算当日涨幅
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            change = (last_row['收盘'] - prev_row['收盘']) / prev_row['收盘']

            if sector not in sector_stats:
                sector_stats[sector] = {'changes': [], 'strong_up': 0}

            sector_stats[sector]['changes'].append(change)
            if change >= 0.05:  # 强势上涨
                sector_stats[sector]['strong_up'] += 1

        # 计算板块平均涨幅
        hot_sectors = []
        for sector, stats in sector_stats.items():
            avg_change = np.mean(stats['changes'])
            strong_up_count = stats['strong_up']

            # 板块硬性条件（放宽）
            if avg_change >= 0.01:  # 板块平均涨幅>=1%
                hot_sectors.append({
                    'sector': sector,
                    'change': avg_change,
                    'limit_up_count': strong_up_count
                })

        # 按涨幅排序，取前3
        hot_sectors.sort(key=lambda x: x['change'], reverse=True)
        return hot_sectors[:3]

    @staticmethod
    def auction_filter(df, idx):
        """竞价筛选条件（用开盘价模拟）

        Returns:
            (is_qualified, auction_change)
        """
        if idx == 0 or idx >= len(df):
            return False, 0

        row = df.iloc[idx]
        prev_row = df.iloc[idx - 1]

        # 竞价涨幅：1% ≤ 涨幅 ≤ 8%
        open_change = (row['开盘'] - prev_row['收盘']) / prev_row['收盘']

        if not (0.01 <= open_change <= 0.08):
            return False, open_change

        # 昨日涨幅 ≤ 9%
        prev_change = (prev_row['收盘'] - prev_row['开盘']) / prev_row['开盘']
        if prev_change > 0.09:
            return False, open_change

        return True, open_change

    @staticmethod
    def opening_trend(df, idx):
        """开盘走势判断

        Returns:
            (trend_type, score)
        """
        if idx + 3 >= len(df):
            return 'weak', 0

        row = df.iloc[idx]
        if idx > 0:
            prev_close = df.iloc[idx - 1]['收盘']
        else:
            prev_close = row['开盘']

        open_change = (row['开盘'] - prev_close) / prev_close

        # 检查接下来走势
        next_changes = []
        for i in range(1, min(4, len(df) - idx)):
            next_row = df.iloc[idx + i]
            change = (next_row['收盘'] - row['开盘']) / row['开盘']
            next_changes.append(change)

        if not next_changes:
            return 'weak', 0

        max_change = max(next_changes)
        min_change = min(next_changes)

        # 判断走势类型
        if open_change >= 0.02 and max_change > 0.03:
            return 'strong', 3
        elif 0 <= open_change <= 0.02 and min_change > -0.01 and max_change > 0.01:
            return 'divergent', 2
        else:
            return 'weak', 1

    @staticmethod
    def should_buy(sentiment, trend_type, auction_change):
        """买入决策"""
        if sentiment == 'downtrend':
            return False

        if sentiment == 'strong' and trend_type == 'strong' and auction_change >= 0.02:
            return True

        if sentiment == 'divergent' and trend_type == 'divergent' and auction_change >= 0.01:
            return True

        return False

    @staticmethod
    def should_sell(entry_price, current_price, hold_days, high_price):
        """卖出决策"""
        change = (current_price - entry_price) / entry_price

        # 止损
        if change <= -0.05:
            return True, "止损", 'stop_loss'

        # 止盈
        if change >= 0.05 and change < 0.10:
            return True, "止盈", 'take_profit'

        # 移动止盈
        if high_price > entry_price * 1.1:
            if (current_price - high_price) / high_price < -0.03:
                return True, "移动止盈", 'moving_stop'

        # 时间止损
        if hold_days >= 10:
            return True, "时间止损", 'time_stop'

        return False, "持有", 'hold'


# ============================================
# 主回测程序
# ============================================

print(f"\n{'='*70}")
print("开始回测...")
print(f"{'='*70}")

# 获取所有股票的数据
stock_data_dict = {}
print("\n【步骤1】获取股票数据...")

for stock_info in all_stocks:
    code = stock_info['code']
    sector = stock_info['sector']

    df = client.get_stock_history(code, start_date, end_date)

    if not df.empty and len(df) > 30:
        df = add_indicators(df)
        stock_data_dict[code] = df
        print(f"  ✓ {code} ({sector}): {len(df)}天数据")

print(f"\n成功获取 {len(stock_data_dict)} 只股票的数据")

# 逐日回测
all_trades = []
daily_signals = []

# 获取交易日期列表（取第一只股票的日期）
if stock_data_dict:
    trade_dates = list(stock_data_dict[list(stock_data_dict.keys())[0]]['日期'])
    # 只交易日（排除周末，实际应该是工作日）
    trade_dates = [d for d in trade_dates if d.weekday() < 5]

    print(f"\n【步骤2】逐日回测，共{len(trade_dates)}个交易日...")

    for date_idx in range(30, len(trade_dates) - 5):
        current_date = trade_dates[date_idx]

        # 构建当日所有股票的数据快照
        daily_data = {}
        for code, df in stock_data_dict.items():
            df_date = df[df['日期'] == current_date]
            if not df_date.empty:
                idx = df_date.index[0]
                if idx >= 2:  # 确保有前2天数据
                    daily_data[code] = {
                        'df': df,
                        'idx': idx
                    }

        if not daily_data:
            continue

        # 1. 计算市场情绪（传入完整数据和当前索引）
        sentiment_data_for_calc = {}
        for code, info in daily_data.items():
            df = info['df']
            idx = info['idx']
            if idx >= 1:
                # 传入完整数据和当前索引
                sentiment_data_for_calc[code] = {'df': df, 'idx': idx}

        sentiment, can_trade, limit_up, limit_down = FullFlowStrategy.calculate_market_sentiment_with_idx(
            sentiment_data_for_calc
        )

        # 调试：每隔10天输出一次
        if date_idx % 10 == 0:
            # 显示详细的涨跌统计
            changes = []
            for code, info in daily_data.items():
                df = info['df']
                idx = info['idx']
                if idx > 0:
                    change = (df.iloc[idx]['收盘'] - df.iloc[idx-1]['收盘']) / df.iloc[idx-1]['收盘']
                    changes.append(change)

            if changes:
                up_count = sum(1 for c in changes if c > 0)
                avg_change = np.mean(changes)
                print(f"  {current_date}: 上涨{up_count}/{len(changes)}, 平均涨幅{avg_change*100:.2f}%, "
                      f"情绪={sentiment}, 可交易={can_trade}")

        if not can_trade:
            continue  # 市场环境不交易

        # 2. 筛选热门板块
        sector_data = {}
        for code, info in daily_data.items():
            df = info['df']
            idx = info['idx']
            if idx >= 2:
                sector_data[code] = df.iloc[idx-1:idx+1]

        hot_sectors = FullFlowStrategy.filter_hot_sectors(
            {code: data for code, data in sector_data.items()}
        )

        # 调试：显示筛选出的热门板块
        if date_idx % 10 == 0 and hot_sectors:
            sector_list = [f"{s['sector']}({s['change']*100:.1f}%)" for s in hot_sectors]
            print(f"    热门板块: {sector_list}")

            # 统计热门板块内的股票数
            hot_sector_stocks = sum(1 for code, info in daily_data.items()
                                   if any(code in stocks for s, stocks in stock_pool.items()
                                          if s in hot_sector_names))
            print(f"    热门板块内股票: {hot_sector_stocks}只")

        if not hot_sectors:
            continue

        # 3. 从热门板块中筛选股票
        hot_sector_names = [s['sector'] for s in hot_sectors]
        candidate_stocks = []

        auction_qualified = 0  # 通过竞价筛选的股票数
        opening_qualified = 0  # 通过开盘走势的股票数
        buy_qualified = 0  # 通过买入决策的股票数

        for code, info in daily_data.items():
            # 检查股票是否在热门板块中
            stock_sector = None
            for sector, stocks in stock_pool.items():
                if code in stocks and sector in hot_sector_names:
                    stock_sector = sector
                    break

            if not stock_sector:
                continue

            df = info['df']
            idx = info['idx']

            # 竞价筛选
            is_qualified, auction_change = FullFlowStrategy.auction_filter(df, idx)

            if is_qualified:
                auction_qualified += 1

                # 开盘走势判断
                trend_type, score = FullFlowStrategy.opening_trend(df, idx)

                if trend_type in ['strong', 'divergent']:
                    opening_qualified += 1

                # 买入决策
                if FullFlowStrategy.should_buy(sentiment, trend_type, auction_change):
                    buy_qualified += 1
                    entry_price = df.iloc[idx]['开盘']
                    candidate_stocks.append({
                        'code': code,
                        'sector': stock_sector,
                        'entry_price': entry_price,
                        'auction_change': auction_change,
                        'trend': trend_type,
                        'sentiment': sentiment
                    })

        # 4. 选择最多3只股票（按竞价涨幅排序）
        candidate_stocks.sort(key=lambda x: x['auction_change'], reverse=True)
        selected_stocks = candidate_stocks[:3]

        if not selected_stocks:
            # 调试：显示为什么没有选中
            if date_idx % 10 == 0:
                print(f"    通过竞价: {auction_qualified}只, 开盘走势: {opening_qualified}只, "
                      f"买入决策: {buy_qualified}只, 最终候选: {len(candidate_stocks)}只")
            continue

        # 调试：显示选中的股票
        if date_idx % 10 == 0:
            stock_list = [f"{s['code']}({s['auction_change']*100:.1f}%)" for s in selected_stocks]
            print(f"    ✅ 选中{len(selected_stocks)}只股票: {stock_list}")

        # 5. 持有并跟踪卖出
        for stock in selected_stocks:
            code = stock['code']
            df = daily_data[code]['df']
            entry_idx = daily_data[code]['idx']
            entry_price = stock['entry_price']
            entry_date_str = current_date.strftime("%Y-%m-%d")

            high_price = entry_price

            # 检查后续卖出点
            for hold_days in range(1, min(11, len(df) - entry_idx)):
                current_price = df.iloc[entry_idx + hold_days]['收盘']
                high_price = max(high_price, current_price)

                should_sell, reason, sell_type = FullFlowStrategy.should_sell(
                    entry_price, current_price, hold_days, high_price
                )

                if should_sell:
                    profit = (current_price - entry_price) / entry_price * 100

                    trade = {
                        'entry_date': entry_date_str,
                        'stock_code': code,
                        'stock_sector': stock['sector'],
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'hold_days': hold_days,
                        'profit': profit,
                        'sell_type': sell_type,
                        'sentiment': sentiment,
                        'trend': stock['trend'],
                        'auction_change': stock['auction_change']
                    }

                    all_trades.append(trade)
                    daily_signals.append({
                        'date': entry_date_str,
                        'action': 'BUY',
                        'code': code,
                        'sector': stock['sector'],
                        'price': entry_price
                    })
                    break

# ============================================
# 结果分析
# ============================================

print(f"\n\n{'='*70}")
print("回测结果")
print(f"{'='*70}")

if all_trades:
    df_trades = pd.DataFrame(all_trades)

    print(f"\n【总体统计】")
    print(f"  总交易次数: {len(all_trades)}次")
    print(f"  盈利次数: {len(df_trades[df_trades['profit'] > 0])}次")
    print(f"  亏损次数: {len(df_trades[df_trades['profit'] <= 0])}次")

    success_rate = (df_trades['profit'] > 0).mean() * 100
    print(f"  成功率: {success_rate:.1f}%")

    avg_profit = df_trades['profit'].mean()
    print(f"  平均收益: {avg_profit:.2f}%")

    avg_hold = df_trades['hold_days'].mean()
    print(f"  平均持有天数: {avg_hold:.1f}天")

    max_profit = df_trades['profit'].max()
    max_loss = df_trades['profit'].min()
    print(f"  最大盈利: {max_profit:.2f}%")
    print(f"  最大亏损: {max_loss:.2f}%")

    # 按板块统计
    print(f"\n【按板块统计】")
    sector_stats = df_trades.groupby('stock_sector').agg({
        'profit': ['count', 'mean', 'sum']
    }).round(2)
    print(sector_stats)

    # 按卖出类型统计
    print(f"\n【按卖出类型统计】")
    for sell_type in ['stop_loss', 'take_profit', 'moving_stop', 'time_stop']:
        type_trades = df_trades[df_trades['sell_type'] == sell_type]
        if len(type_trades) > 0:
            type_profit = type_trades['profit'].mean()
            print(f"  {sell_type}: {len(type_trades)}次, 平均收益 {type_profit:.2f}%")

    # 按市场情绪统计
    print(f"\n【按市场情绪统计】")
    for sentiment in ['strong', 'divergent']:
        sentiment_trades = df_trades[df_trades['sentiment'] == sentiment]
        if len(sentiment_trades) > 0:
            s_rate = (sentiment_trades['profit'] > 0).mean() * 100
            s_profit = sentiment_trades['profit'].mean()
            print(f"  {sentiment}: {len(sentiment_trades)}次, 成功率{s_rate:.1f}%, 平均收益{s_profit:.2f}%")

    # 最近10笔交易
    print(f"\n【最近10笔交易】")
    recent_trades = df_trades.tail(10)[['entry_date', 'stock_code', 'stock_sector', 'entry_price', 'exit_price', 'profit', 'hold_days']]
    for _, trade in recent_trades.iterrows():
        profit_str = f"+{trade['profit']:.2f}%" if trade['profit'] > 0 else f"{trade['profit']:.2f}%"
        print(f"  {trade['entry_date']} {trade['stock_code']}({trade['stock_sector']}) "
              f"{trade['entry_price']:.2f}→{trade['exit_price']:.2f} {profit_str} {trade['hold_days']}天")

else:
    print("  ❌ 回测期间未产生交易信号")
    print("\n可能原因:")
    print("  1. 筛选条件过于严格")
    print("  2. 市场环境不符合策略条件")
    print("  3. 竞价筛选条件（1-8%开盘涨幅）在历史数据中较少出现")

print(f"\n{'='*70}")
print("回测完成!")
print(f"{'='*70}")
