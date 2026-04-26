"""板块分析模块"""
import pandas as pd
from typing import List, Dict, Optional
from data.akshare_client import DataClient


class SectorAnalysis:
    """板块分析类"""

    # 板块筛选条件
    MIN_SECTOR_CHANGE = 0.02      # 板块最小涨幅 2%
    MIN_LIMIT_UP_IN_SECTOR = 2   # 板块内最少涨停家数
    MIN_UP_IN_SECTOR = 10        # 板块内最少上涨家数

    @staticmethod
    def get_hot_sectors(date: str = None, limit: int = 3) -> pd.DataFrame:
        """获取热门板块

        Args:
            date: 日期
            limit: 返回数量

        Returns:
            热门板块DataFrame
        """
        client = DataClient(source="akshare")
        sectors = client.get_sector_data(date)

        if sectors.empty:
            return pd.DataFrame()

        # 筛选条件
        hot_sectors = sectors[
            (sectors['涨跌幅'] >= SectorAnalysis.MIN_SECTOR_CHANGE) &
            (sectors['上涨家数'] >= SectorAnalysis.MIN_UP_IN_SECTOR)
        ].copy()

        # 排序：按涨幅降序
        hot_sectors = hot_sectors.sort_values('涨跌幅', ascending=False)

        return hot_sectors.head(limit)

    @staticmethod
    def get_sector_leader(sector_name: str, market_data: pd.DataFrame = None) -> Optional[Dict]:
        """获取板块龙头

        Args:
            sector_name: 板块名称
            market_data: 市场数据（可选）

        Returns:
            龙头股信息字典
        """
        if market_data is None:
            client = DataClient(source="akshare")
            market_data = client.get_stock_realtime("")

        if market_data.empty:
            return None

        # 筛选该板块的股票
        sector_stocks = market_data[market_data['所属行业'] == sector_name]

        if sector_stocks.empty:
            return None

        # 找出涨幅最大的
        leader = sector_stocks.loc[sector_stocks['涨跌幅'].idxmax()]

        return {
            'code': leader['代码'],
            'name': leader['名称'],
            'price': leader['最新价'],
            'change': leader['涨跌幅'],
            'volume': leader['成交量'],
            'is_limit_up': leader['涨跌幅'] >= 9.5
        }

    @staticmethod
    def rank_sectors(sectors: pd.DataFrame) -> pd.DataFrame:
        """板块排序

        Args:
            sectors: 板块数据

        Returns:
            排序后的板块DataFrame
        """
        if sectors.empty:
            return pd.DataFrame()

        # 计算综合得分：涨幅 + 涨停家数权重 + 上涨家数权重
        sectors['score'] = (
            sectors['涨跌幅'] * 0.4 +
            sectors.get('涨停家数', 0) * 0.3 +
            sectors['上涨家数'] * 0.3
        )

        return sectors.sort_values('score', ascending=False)

    @staticmethod
    def filter_sectors(sectors: pd.DataFrame) -> pd.DataFrame:
        """筛选板块

        Args:
            sectors: 板块数据

        Returns:
            筛选后的板块DataFrame
        """
        if sectors.empty:
            return pd.DataFrame()

        # 应用筛选条件
        filtered = sectors[
            (sectors['涨跌幅'] >= SectorAnalysis.MIN_SECTOR_CHANGE) &
            (sectors.get('涨停家数', 0) >= SectorAnalysis.MIN_LIMIT_UP_IN_SECTOR) &
            (sectors['上涨家数'] >= SectorAnalysis.MIN_UP_IN_SECTOR)
        ].copy()

        return filtered


def get_sector_analysis(date: str = None, top_n: int = 3) -> List[Dict]:
    """获取板块分析结果

    Args:
        date: 日期
        top_n: 返回前N个板块

    Returns:
        板块分析结果列表
    """
    client = DataClient(source="akshare")

    # 获取板块数据
    sectors = client.get_sector_data(date)

    if sectors.empty:
        return []

    # 获取市场数据
    market_data = client.get_stock_realtime("")

    # 筛选和排序
    hot_sectors = SectorAnalysis.get_hot_sectors(date, limit=10)

    if hot_sectors.empty:
        return []

    # 为每个板块找到龙头
    results = []
    for _, sector in hot_sectors.head(top_n).iterrows():
        leader = SectorAnalysis.get_sector_leader(
            sector.get('板块名称', sector.get('名称', '')),
            market_data
        )

        results.append({
            'sector_name': sector.get('板块名称', sector.get('名称', '')),
            'change': sector.get('涨跌幅', 0),
            'limit_up_count': sector.get('涨停家数', 0),
            'up_count': sector.get('上涨家数', 0),
            'leader': leader
        })

    return results


def get_sector_stocks(sector_name: str) -> pd.DataFrame:
    """获取板块内所有股票

    Args:
        sector_name: 板块名称

    Returns:
        板块股票DataFrame
    """
    client = DataClient(source="akshare")
    market_data = client.get_stock_realtime("")

    if market_data.empty:
        return pd.DataFrame()

    return market_data[market_data['所属行业'] == sector_name].copy()
