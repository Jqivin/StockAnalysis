"""回测策略模块"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd


class Strategy(ABC):
    """策略基类"""

    def __init__(self, params: Dict[str, Any] = None):
        """初始化策略

        Args:
            params: 策略参数
        """
        self.params = params or {}
        self.position = 0  # 持仓数量，正数为多头，负数为空头
        self.cash = 0  # 可用资金
        self.trades = []  # 交易记录

    @abstractmethod
    def on_bar(self, bar: pd.Series, index: int) -> str:
        """K线回调函数，生成交易信号

        Args:
            bar: 当前K线数据
            index: 当前索引

        Returns:
            交易信号 ('buy', 'sell', 'hold')
        """
        pass

    def on_order(self, order: Dict[str, Any]):
        """订单回调函数"""
        self.trades.append(order)


class MAStrategy(Strategy):
    """均线交叉策略"""

    def __init__(self, short_period: int = 5, long_period: int = 20):
        super().__init__({
            'short_period': short_period,
            'long_period': long_period
        })
        self.short_period = short_period
        self.long_period = long_period

    def on_bar(self, bar: pd.Series, index: int) -> str:
        """金叉买入，死叉卖出"""
        if index < self.long_period:
            return 'hold'

        def safe_get(key, default=0):
            val = bar.get(key, default)
            if isinstance(val, pd.Series):
                val = val.iloc[0] if len(val) > 0 else default
            try:
                return float(val) if pd.notna(val) else default
            except (ValueError, TypeError):
                return default

        ma_short = safe_get(f'MA{self.short_period}')
        ma_long = safe_get(f'MA{self.long_period}')
        prev_ma_short = safe_get(f'prev_MA{self.short_period}')
        prev_ma_long = safe_get(f'prev_MA{self.long_period}')

        if prev_ma_short <= prev_ma_long and ma_short > ma_long:
            return 'buy'  # 金叉
        elif prev_ma_short >= prev_ma_long and ma_short < ma_long:
            return 'sell'  # 死叉
        else:
            return 'hold'


class MACDStrategy(Strategy):
    """MACD策略"""

    def on_bar(self, bar: pd.Series, index: int) -> str:
        """DIF上穿DEA买入，下穿卖出"""
        def safe_get(key, default=0):
            val = bar.get(key, default)
            if isinstance(val, pd.Series):
                val = val.iloc[0] if len(val) > 0 else default
            try:
                return float(val) if pd.notna(val) else default
            except (ValueError, TypeError):
                return default

        dif = safe_get('DIF')
        dea = safe_get('DEA')
        prev_dif = safe_get('prev_DIF')
        prev_dea = safe_get('prev_DEA')

        if prev_dif <= prev_dea and dif > dea:
            return 'buy'
        elif prev_dif >= prev_dea and dif < dea:
            return 'sell'
        else:
            return 'hold'


class RSIStrategy(Strategy):
    """RSI策略"""

    def __init__(self, oversold: int = 30, overbought: int = 70):
        super().__init__({
            'oversold': oversold,
            'overbought': overbought
        })

    def on_bar(self, bar: pd.Series, index: int) -> str:
        """RSI超卖买入，超买卖出"""
        def safe_get(key, default=50):
            val = bar.get(key, default)
            if isinstance(val, pd.Series):
                val = val.iloc[0] if len(val) > 0 else default
            try:
                return float(val) if pd.notna(val) else default
            except (ValueError, TypeError):
                return default

        rsi = safe_get('RSI')
        prev_rsi = safe_get('prev_RSI')

        if prev_rsi <= self.params['oversold'] and rsi > self.params['oversold']:
            return 'buy'
        elif prev_rsi >= self.params['overbought'] and rsi < self.params['overbought']:
            return 'sell'
        else:
            return 'hold'


class BollingerBandsStrategy(Strategy):
    """布林带策略"""

    def on_bar(self, bar: pd.Series, index: int) -> str:
        """价格突破下轨买入，突破上轨卖出"""
        def safe_get(key, default=0):
            val = bar.get(key, default)
            if isinstance(val, pd.Series):
                val = val.iloc[0] if len(val) > 0 else default
            try:
                return float(val) if pd.notna(val) else default
            except (ValueError, TypeError):
                return default

        close = safe_get('收盘')
        upper = safe_get('upper')
        lower = safe_get('lower')
        prev_close = safe_get('prev_收盘')

        if prev_close <= lower and close > lower:
            return 'buy'
        elif prev_close >= upper and close < upper:
            return 'sell'
        else:
            return 'hold'


def create_strategy(strategy_name: str, **kwargs) -> Strategy:
    """创建策略实例

    Args:
        strategy_name: 策略名称
        **kwargs: 策略参数

    Returns:
        策略实例
    """
    strategies = {
        'ma': MAStrategy,
        'macd': MACDStrategy,
        'rsi': RSIStrategy,
        'bollinger': BollingerBandsStrategy,
    }

    if strategy_name.lower() not in strategies:
        raise ValueError(f"不支持的策略: {strategy_name}")

    return strategies[strategy_name.lower()](**kwargs)
