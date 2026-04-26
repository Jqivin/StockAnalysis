"""龙头识别模块"""
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from data.akshare_client import DataClient
from analysis.technical import add_indicators


class LeaderIdentification:
    """龙头识别类"""

    @staticmethod
    def identify_sector_leader(sector_name: str, market_data: pd.DataFrame) -> Optional[Dict]:
        """识别板块龙头

        Args:
            sector_name: 板块名称
            market_data: 市场数据

        Returns:
            龙头股信息字典
        """
        if market_data.empty:
            return None

        sector_stocks = market_data[market_data['所属行业'] == sector_name]

        if sector_stocks.empty:
            return None

        # 板块龙头 = 板块涨幅第一且 > 7%
        top_stock = sector_stocks.nlargest(1, '涨跌幅').iloc[0]

        if top_stock['涨跌幅'] < 0.07:
            return None

        return {
            'code': top_stock['代码'],
            'name': top_stock['名称'],
            'price': top_stock['最新价'],
            'change': top_stock['涨跌幅'],
            'volume': top_stock['成交量'],
            'priority': 1,  # 板块龙头优先级最高
            'leader_type': 'sector_leader',
            'reason': f'板块涨幅第一({top_stock["涨跌幅"]:.2f}%)'
        }

    @staticmethod
    def identify_consecutive_leader(code: str, days: int = 5) -> Dict:
        """识别连板龙头

        Args:
            code: 股票代码
            days: 查看天数

        Returns:
            连板信息字典
        """
        client = DataClient(source="akshare")

        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

        df = client.get_stock_history(code, start_date, end_date)

        if df.empty or len(df) < 2:
            return {
                'code': code,
                'consecutive_count': 0,
                'priority': 0,
                'leader_type': 'none'
            }

        # 计算连板数
        consecutive_count = 0
        for _, row in df[::-1].iterrows():  # 从最近开始
            if (row['收盘'] - row['开盘']) / row['开盘'] >= 0.095:
                consecutive_count += 1
            else:
                break

        return {
            'code': code,
            'name': client.get_stock_name(code),
            'consecutive_count': consecutive_count,
            'priority': 2 if consecutive_count >= 2 else 0,
            'leader_type': 'consecutive_leader' if consecutive_count >= 2 else 'none',
            'reason': f'{consecutive_count}连板'
        }

    @staticmethod
    def identify_new_leader(code: str, history_df: pd.DataFrame = None) -> Dict:
        """识别新晋龙头（首次涨停的强势股）

        Args:
            code: 股票代码
            history_df: 历史数据（可选）

        Returns:
            新晋龙头信息字典
        """
        client = DataClient(source="akshare")

        if history_df is None:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")
            history_df = client.get_stock_history(code, start_date, end_date)

        if history_df.empty or len(history_df) < 2:
            return {
                'code': code,
                'priority': 0,
                'leader_type': 'none'
            }

        latest = history_df.iloc[-1]
        previous = history_df.iloc[-2]

        # 检查是否首次涨停且强势
        is_new_limit_up = (
            (latest['收盘'] - latest['开盘']) / latest['开盘'] >= 0.095 and  # 今日涨停
            (previous['收盘'] - previous['开盘']) / previous['开盘'] < 0.095 and  # 昨日未涨停
            latest['成交量'] > previous['成交量'] * 1.5  # 放量
        )

        if is_new_limit_up:
            return {
                'code': code,
                'name': client.get_stock_name(code),
                'price': latest['收盘'],
                'change': (latest['收盘'] - latest['开盘']) / latest['开盘'],
                'volume': latest['成交量'],
                'priority': 3,
                'leader_type': 'new_leader',
                'reason': '新晋龙头（首次涨停放量）'
            }

        return {
            'code': code,
            'priority': 0,
            'leader_type': 'none'
        }

    @staticmethod
    def identify_old_leader(code: str, history_df: pd.DataFrame = None) -> Dict:
        """识别老龙头（历史妖股再次启动）

        Args:
            code: 股票代码
            history_df: 历史数据（可选）

        Returns:
            老龙头信息字典
        """
        # 简化实现：检查是否有历史连板记录
        # 实际需要维护历史妖股数据库
        consecutive_info = LeaderIdentification.identify_consecutive_leader(code)

        if consecutive_info['consecutive_count'] > 0:
            return {
                'code': code,
                'name': consecutive_info['name'],
                'consecutive_count': consecutive_info['consecutive_count'],
                'priority': 4,
                'leader_type': 'old_leader',
                'reason': f'历史妖股再次启动（{consecutive_info["consecutive_count"]}连板）'
            }

        return {
            'code': code,
            'priority': 0,
            'leader_type': 'none'
        }

    @staticmethod
    def rank_stocks_by_priority(stocks: List[Dict]) -> List[Dict]:
        """按优先级排序股票

        Args:
            stocks: 股票列表

        Returns:
            排序后的股票列表
        """
        # 过滤出有效股票（priority > 0）
        valid_stocks = [s for s in stocks if s.get('priority', 0) > 0]

        # 按优先级排序
        sorted_stocks = sorted(valid_stocks, key=lambda x: x.get('priority', 999))

        return sorted_stocks


def analyze_stocks_priority(codes: List[str]) -> List[Dict]:
    """分析股票的优先级

    Args:
        codes: 股票代码列表

    Returns:
        排序后的股票信息列表
    """
    client = DataClient(source="akshare")
    market_data = client.get_stock_realtime("")

    if market_data.empty:
        return []

    results = []

    for code in codes:
        # 获取基本信息
        stock_info = market_data[market_data['代码'] == code]
        if stock_info.empty:
            continue

        stock = stock_info.iloc[0]

        # 获取历史数据
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")
        history_df = client.get_stock_history(code, start_date, end_date)

        # 判断龙头类型
        if not history_df.empty:
            latest = history_df.iloc[-1]
            is_limit_up = (latest['收盘'] - latest['开盘']) / latest['开盘'] >= 0.095

            # 确定优先级
            if is_limit_up:
                consecutive_info = LeaderIdentification.identify_consecutive_leader(code)
                if consecutive_info['consecutive_count'] >= 2:
                    # 连板龙头
                    results.append({
                        'code': code,
                        'name': stock['名称'],
                        'price': stock['最新价'],
                        'change': stock['涨跌幅'],
                        'volume': stock['成交量'],
                        'priority': 2,
                        'leader_type': 'consecutive_leader',
                        'reason': f'{consecutive_info["consecutive_count"]}连板'
                    })
                else:
                    # 新晋龙头
                    new_leader = LeaderIdentification.identify_new_leader(code, history_df)
                    if new_leader['priority'] > 0:
                        results.append(new_leader)

    # 排序
    return LeaderIdentification.rank_stocks_by_priority(results)


def get_all_leaders(sector_name: str = None) -> List[Dict]:
    """获取所有龙头股

    Args:
        sector_name: 指定板块（可选）

    Returns:
        龙头股列表
    """
    client = DataClient(source="akshare")
    market_data = client.get_stock_realtime("")

    if market_data.empty:
        return []

    # 筛选涨停股
    limit_up_stocks = market_data[market_data['涨跌幅'] >= 9.5].copy()

    if limit_up_stocks.empty:
        return []

    results = []

    # 如果指定板块，只分析该板块
    if sector_name:
        limit_up_stocks = limit_up_stocks[limit_up_stocks['所属行业'] == sector_name]

    for _, stock in limit_up_stocks.iterrows():
        code = stock['代码']

        # 获取历史数据
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")
        history_df = client.get_stock_history(code, start_date, end_date)

        if history_df.empty:
            continue

        # 判断龙头类型
        consecutive_info = LeaderIdentification.identify_consecutive_leader(code)
        new_leader_info = LeaderIdentification.identify_new_leader(code, history_df)

        if consecutive_info['priority'] > 0:
            results.append({
                'code': code,
                'name': stock['名称'],
                'price': stock['最新价'],
                'change': stock['涨跌幅'],
                'volume': stock['成交量'],
                'sector': stock.get('所属行业', ''),
                'priority': consecutive_info['priority'],
                'leader_type': consecutive_info['leader_type'],
                'reason': consecutive_info['reason']
            })
        elif new_leader_info['priority'] > 0:
            results.append({
                'code': code,
                'name': stock['名称'],
                'price': stock['最新价'],
                'change': stock['涨跌幅'],
                'volume': stock['成交量'],
                'sector': stock.get('所属行业', ''),
                'priority': new_leader_info['priority'],
                'leader_type': new_leader_info['leader_type'],
                'reason': new_leader_info['reason']
            })

    # 排序
    return LeaderIdentification.rank_stocks_by_priority(results)
