"""股票筛选器模块"""
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from data.akshare_client import DataClient
from strategy.leader import analyze_stocks_priority


class StockFilter:
    """股票筛选类 - 基于竞价规则"""

    # 竞价筛选硬性条件
    MIN_AUCTION_CHANGE = 0.02       # 最小竞价涨幅 2%
    MAX_AUCTION_CHANGE = 0.06       # 最大竞价涨幅 6%
    MIN_AUCTION_AMOUNT = 50000000    # 最小竞价成交额 5000万
    MIN_AUCTION_TURNOVER = 0.02     # 最小竞价换手率 2%
    MIN_MARKET_CAP = 5000000000     # 最小流通市值 50亿
    MAX_MARKET_CAP = 30000000000    # 最大流通市值 300亿
    MAX_YESTERDAY_CHANGE = 0.08     # 昨日最大涨幅 8%
    MIN_YESTERDAY_TURNOVER = 0.05  # 昨日最小换手率 5%
    MAX_YESTERDAY_TURNOVER = 0.20  # 昨日最大换手率 20%

    # 排除条件
    MAX_AUCTION_CHANGE_EXCLUDE = 0.08  # 竞价高开上限 8%
    MAX_CONSECUTIVE_BOARDS = 5           # 最大连板数
    FORBIDDEN_PATTERNS = ['ST']           # 禁止的股票模式

    @staticmethod
    def filter_by_auction(auction_data: Dict, yesterday_data: Dict) -> bool:
        """竞价筛选 - 7条硬性条件必须同时满足

        Args:
            auction_data: 竞价数据
            yesterday_data: 昨日数据

        Returns:
            是否满足条件
        """
        auction_change = auction_data.get('auction_change', 0)
        auction_amount = auction_data.get('auction_amount', 0)
        auction_volume = auction_data.get('auction_volume', 0)
        market_cap = auction_data.get('market_cap', 0)

        yesterday_change = yesterday_data.get('change', 0)
        yesterday_turnover = yesterday_data.get('turnover_rate', 0)

        # 条件1: 竞价涨幅 2%-6%
        if not (StockFilter.MIN_AUCTION_CHANGE <= auction_change <= StockFilter.MAX_AUCTION_CHANGE):
            return False

        # 条件2: 竞价成交额 ≥ 5000万
        if auction_amount < StockFilter.MIN_AUCTION_AMOUNT:
            return False

        # 条件3: 竞价换手率 ≥ 2%
        if auction_turnover < StockFilter.MIN_AUCTION_TURNOVER:
            return False

        # 条件4: 流通市值 50-300亿
        if not (StockFilter.MIN_MARKET_CAP <= market_cap <= StockFilter.MAX_MARKET_CAP):
            return False

        # 条件5: 昨日涨幅 ≤ 8%
        if yesterday_change > StockFilter.MAX_YESTERDAY_CHANGE:
            return False

        # 条件6: 昨日换手率 5%-20%
        if not (StockFilter.MIN_YESTERDAY_TURNOVER <= yesterday_turnover <= StockFilter.MAX_YESTERDAY_TURNOVER):
            return False

        # 条件7: 非天地板
        if yesterday_data.get('is_sky_ground', False):
            return False

        return True

    @staticmethod
    def apply_exclusion_rules(auction_data: Dict, yesterday_data: Dict,
                              consecutive_count: int = 0) -> List[str]:
        """应用排除规则 - 遇到任意一条直接剔除

        Args:
            auction_data: 竞价数据
            yesterday_data: 昨日数据
            consecutive_count: 连板数

        Returns:
            排除原因列表（空列表表示通过）
        """
        reasons = []

        # 排除条件1: 竞价高开 > 8%
        if auction_data.get('auction_change', 0) > StockFilter.MAX_AUCTION_CHANGE_EXCLUDE:
            reasons.append("竞价高开诱多")

        # 排除条件2: 连板 > 5板
        if consecutive_count > StockFilter.MAX_CONSECUTIVE_BOARDS:
            reasons.append(f"连板过多({consecutive_count}板)")

        # 排除条件3: 昨日天地板
        if yesterday_data.get('is_sky_ground', False):
            reasons.append("昨日天地板")

        # 排除条件4: 有利空公告/减持公告
        if yesterday_data.get('has_bad_news', False):
            reasons.append("有利空公告")

        # 排除条件5: 停牌核查/监管关注
        if yesterday_data.get('is_suspended', False) or yesterday_data.get('is_supervised', False):
            reasons.append("停牌或监管关注")

        # 排除条件6: ST股
        code = auction_data.get('code', '')
        if any(pattern in code for pattern in StockFilter.FORBIDDEN_PATTERNS):
            reasons.append("ST股")

        return reasons

    @staticmethod
    def generate_candidate_pool(codes: List[str], limit: int = 8) -> List[Dict]:
        """生成候选股票池（5-8只）

        Args:
            codes: 股票代码列表
            limit: 最多返回数量

        Returns:
            候选股票列表
        """
        client = DataClient(source="akshare")
        market_data = client.get_stock_realtime("")

        if market_data.empty:
            return []

        candidates = []
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")

        for code in codes:
            # 获取实时数据
            stock_info = market_data[market_data['代码'] == code]
            if stock_info.empty:
                continue
            stock = stock_info.iloc[0]

            # 模拟竞价数据（实际需要真实数据源）
            auction_data = {
                'code': code,
                'auction_price': stock['最新价'],
                'auction_change': stock['涨跌幅'] / 100,
                'auction_volume': stock['成交量'],
                'auction_amount': stock['成交额'],
                'market_cap': stock.get('流通市值', 10000000000)
            }

            # 获取昨日数据
            history_df = client.get_stock_history(code, start_date, end_date)

            if history_df.empty or len(history_df) < 2:
                continue

            yesterday = history_df.iloc[-2]
            yesterday_change = (yesterday['收盘'] - yesterday['开盘']) / yesterday['开盘']
            yesterday_turnover = yesterday['成交量'] / yesterday.get('流通市值', 10000000000)

            # 判断是否天地板
            high_low = (yesterday['最高'] - yesterday['最低']) / yesterday['开盘']
            is_sky_ground = (high_low > 0.2 and yesterday_change < -0.095)

            yesterday_data = {
                'change': yesterday_change,
                'turnover_rate': yesterday_turnover,
                'is_sky_ground': is_sky_ground,
                'has_bad_news': False,
                'is_suspended': False,
                'is_supervised': False
            }

            # 计算连板数
            consecutive_count = 0
            for _, row in history_df[::-1].iterrows():
                if (row['收盘'] - row['开盘']) / row['开盘'] >= 0.095:
                    consecutive_count += 1
                else:
                    break

            # 应用排除规则
            exclusion_reasons = StockFilter.apply_exclusion_rules(
                auction_data, yesterday_data, consecutive_count
            )

            if exclusion_reasons:
                continue

            # 应用竞价筛选
            if StockFilter.filter_by_auction(auction_data, yesterday_data):
                candidates.append({
                    'code': code,
                    'name': stock['名称'],
                    'auction_price': auction_data['auction_price'],
                    'auction_change': auction_data['auction_change'],
                    'auction_amount': auction_data['auction_amount'],
                    'auction_turnover': auction_data.get('auction_turnover', 0),
                    'market_cap': auction_data['market_cap'],
                    'yesterday_change': yesterday_change,
                    'yesterday_turnover': yesterday_turnover,
                    'consecutive_count': consecutive_count
                })

        if not candidates:
            return []

        # 按优先级排序（使用龙头识别）
        prioritized = analyze_stocks_priority([c['code'] for c in candidates])

        # 合并竞价数据
        code_to_candidate = {c['code']: c for c in candidates}
        results = []
        for leader in prioritized[:limit]:
            if leader['code'] in code_to_candidate:
                candidate = code_to_candidate[leader['code']]
                candidate.update({
                    'leader_type': leader['leader_type'],
                    'leader_reason': leader['reason']
                })
                results.append(candidate)

        return results


def filter_stocks_by_auction(codes: List[str]) -> List[Dict]:
    """根据竞价规则筛选股票

    Args:
        codes: 股票代码列表

    Returns:
        筛选后的股票列表
    """
    return StockFilter.generate_candidate_pool(codes)


def get_top_candidates(limit: int = 8) -> List[Dict]:
    """获取顶级候选股票

    Args:
        limit: 返回数量

    Returns:
        候选股票列表
    """
    # 获取所有股票（实际应该有更合理的筛选方式）
    client = DataClient(source="akshare")
    stock_list = client.get_stock_list()

    if stock_list.empty:
        return []

    # 获取市场数据
    market_data = client.get_stock_realtime("")

    if market_data.empty:
        return []

    # 筛选出涨幅较好的股票
    potential_codes = market_data[
        (market_data['涨跌幅'] >= 0.02) &
        (market_data['涨跌幅'] <= 0.08)
    ]['代码'].head(100).tolist()

    # 使用竞价筛选
    return StockFilter.generate_candidate_pool(potential_codes, limit)
