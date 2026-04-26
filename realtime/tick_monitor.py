"""实时行情监控模块"""
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from data.akshare_client import DataClient


class OpeningMonitor:
    """开盘监控类 - 9:30-9:35 5分钟监控"""

    # 开盘走势量化标准
    STRONG_1MIN_CHANGE = 0.02       # 强势：1分钟涨幅 ≥ 2%
    STRONG_3MIN_NEW_HIGH = True      # 强势：3分钟内创新高
    STRONG_VOLUME_MULTIPLIER = 1.2   # 强势：成交量 ≥ 昨日1.2倍

    DIVERGENT_CHANGE_MIN = 0.0       # 分歧：涨幅 0-2%
    DIVERGENT_CHANGE_MAX = 0.02     # 分歧：涨幅上限
    DIVERGENT_MAX_DRAWDOWN = 0.01   # 分歧：最大回撤 ≤ 1%

    WEAK_1MIN_DROP = 0.01            # 弱势：1分钟下跌 > 1%
    WEAK_3MIN_DRAWDOWN = 0.02      # 弱势：3分钟回撤 > 2%

    def __init__(self):
        """初始化监控器"""
        self.monitoring_stocks = {}  # 监控的股票数据
        self.client = DataClient(source="akshare")

    def add_stock_to_monitor(self, code: str, auction_price: float):
        """添加股票到监控列表

        Args:
            code: 股票代码
            auction_price: 竞价价格
        """
        self.monitoring_stocks[code] = {
            'code': code,
            'auction_price': auction_price,
            'data_points': []  # 5分钟数据点
            'status': 'waiting',  # waiting, strong, divergent, weak
            'start_time': datetime.now()
        }

    def record_data_point(self, code: str, price: float, volume: float):
        """记录数据点

        Args:
            code: 股票代码
            price: 当前价格
            volume: 当前成交量
        """
        if code not in self.monitoring_stocks:
            return

        stock = self.monitoring_stocks[code]
        elapsed = (datetime.now() - stock['start_time']).total_seconds()

        if elapsed > 300:  # 超过5分钟停止记录
            return

        # 计算相对竞价价格的涨幅
        change_from_auction = (price - stock['auction_price']) / stock['auction_price']

        stock['data_points'].append({
            'time': elapsed,
            'price': price,
            'volume': volume,
            'change_from_auction': change_from_auction
        })

    def determine_trend_type(self, code: str) -> str:
        """判断开盘走势类型

        Args:
            code: 股票代码

        Returns:
            走势类型 (strong/divergent/weak/unknown)
        """
        if code not in self.monitoring_stocks:
            return 'unknown'

        stock = self.monitoring_stocks[code]
        data = stock['data_points']

        if len(data) < 2:
            return 'unknown'

        # 提取关键数据
        first_price = data[0]['price']
        current_price = data[-1]['price']
        max_price = max(dp['price'] for dp in data)
        min_price = min(dp['price'] for dp in data)
        total_volume = sum(dp['volume'] for dp in data)

        # 1分钟数据
        one_min_data = [dp for dp in data if dp['time'] <= 60]
        if one_min_data:
            one_min_change = (one_min_data[-1]['price'] - one_min_data[0]['price']) / one_min_data[0]['price']
        else:
            one_min_change = 0

        # 3分钟数据
        three_min_data = [dp for dp in data if dp['time'] <= 180]
        if three_min_data:
            three_min_new_high = max(dp['price'] for dp in three_min_data) > first_price
            three_min_change = (three_min_data[-1]['price'] - three_min_data[0]['price']) / three_min_data[0]['price']
        else:
            three_min_new_high = False
            three_min_change = 0

        # 最大回撤
        max_drawdown = (max_price - min_price) / max_price

        # 判断走势类型
        if (one_min_change >= OpeningMonitor.STRONG_1MIN_CHANGE and
            three_min_new_high and
            three_min_change >= 0):
            return 'strong'

        elif (OpeningMonitor.DIVERGENT_CHANGE_MIN <= three_min_change <= OpeningMonitor.DIVERGENT_CHANGE_MAX and
              max_drawdown <= OpeningMonitor.DIVERGENT_MAX_DRAWDOWN and
              three_min_change >= -0.01):  # 3分钟内收复失地
            return 'divergent'

        elif (one_min_change < -OpeningMonitor.WEAK_1MIN_DROP or
              max_drawdown > OpeningMonitor.WEAK_3MIN_DRAWDOWN):
            return 'weak'

        return 'unknown'

    def monitor_opening(self, duration: int = 300, interval: int = 60) -> Dict:
        """监控开盘（模拟实现）

        Args:
            duration: 监控时长（秒）
            interval: 采样间隔（秒）

        Returns:
            监控结果
        """
        results = {}

        # 模拟监控（实际需要真实tick数据）
        for code in list(self.monitoring_stocks.keys()):
            stock = self.monitoring_stocks[code]

            # 模拟5分钟数据点（每分钟一个点）
            auction_change = 0.04  # 假设竞价涨幅4%
            base_price = stock['auction_price']

            # 生成模拟数据
            scenarios = {
                'strong': [0.02, 0.03, 0.025, 0.035, 0.04],   # 持续上涨
                'divergent': [0.01, -0.005, -0.008, 0.015, 0.02],  # 冲高回落再拉起
                'weak': [-0.005, -0.015, -0.02, -0.018, -0.025]  # 持续下跌
            }

            # 随机选择一种走势（实际应该使用真实数据）
            import random
            scenario = random.choice(['strong', 'divergent', 'weak'])
            changes = scenarios[scenario]

            for i, change in enumerate(changes):
                price = base_price * (1 + change)
                volume = 1000000 * (i + 1)  # 递增成交量
                self.record_data_point(code, price, volume)

            # 判断走势类型
            trend_type = self.determine_trend_type(code)

            stock['status'] = trend_type

            # 计算关键指标
            if stock['data_points']:
                data = stock['data_points']
                max_change = max(dp['change_from_auction'] for dp in data)
                max_drawdown = max(
                    (dp['change_from_auction'] - data[j]['change_from_auction'])
                    for j in range(len(data)) for dp in data[j+1:]
                ) if len(data) > 1 else 0

                results[code] = {
                    'code': code,
                    'trend_type': trend_type,
                    'max_change': max_change,
                    'max_drawdown': max_drawdown,
                    'current_change': data[-1]['change_from_auction'],
                    'total_volume': sum(dp['volume'] for dp in data)
                }

        return results

    def get_opening_summary(self) -> Dict:
        """获取开盘总结

        Returns:
            开盘总结字典
        """
        summary = {
            'monitored_count': len(self.monitoring_stocks),
            'strong_stocks': [],
            'divergent_stocks': [],
            'weak_stocks': [],
            'unknown_stocks': []
        }

        for code, stock in self.monitoring_stocks.items():
            trend_type = self.determine_trend_type(code)

            stock_info = {
                'code': code,
                'auction_price': stock['auction_price'],
                'trend_type': trend_type,
                'data_points_count': len(stock['data_points'])
            }

            if trend_type == 'strong':
                summary['strong_stocks'].append(stock_info)
            elif trend_type == 'divergent':
                summary['divergent_stocks'].append(stock_info)
            elif trend_type == 'weak':
                summary['weak_stocks'].append(stock_info)
            else:
                summary['unknown_stocks'].append(stock_info)

        return summary


def monitor_stocks_opening(codes: List[Dict], duration: int = 300) -> Dict:
    """监控股票开盘

    Args:
        codes: 股票列表，每个元素包含code和auction_price
        duration: 监控时长（秒）

    Returns:
        监控结果
    """
    monitor = OpeningMonitor()

    for stock in codes:
        monitor.add_stock_to_monitor(stock['code'], stock.get('auction_price', 0))

    return monitor.monitor_opening(duration)
