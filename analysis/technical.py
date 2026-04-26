"""技术分析模块"""
import pandas as pd
import numpy as np


class TechnicalIndicators:
    """技术指标计算类"""

    @staticmethod
    def ma(data: pd.Series, period: int) -> pd.Series:
        """计算移动平均线 (MA)

        Args:
            data: 价格序列
            period: 周期

        Returns:
            MA序列
        """
        return data.rolling(window=period).mean()

    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """计算指数移动平均线 (EMA)

        Args:
            data: 价格序列
            period: 周期

        Returns:
            EMA序列
        """
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """计算MACD指标

        Args:
            data: 收盘价序列
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期

        Returns:
            包含MACD, DIF, DEA的DataFrame
        """
        ema_fast = TechnicalIndicators.ema(data, fast)
        ema_slow = TechnicalIndicators.ema(data, slow)
        dif = ema_fast - ema_slow
        dea = TechnicalIndicators.ema(dif, signal)
        macd = (dif - dea) * 2

        return pd.DataFrame({
            'DIF': dif,
            'DEA': dea,
            'MACD': macd
        })

    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """计算相对强弱指标 (RSI)

        Args:
            data: 价格序列
            period: 周期

        Returns:
            RSI序列
        """
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def kdj(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """计算KDJ指标

        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            n: RSV周期
            m1: K值平滑周期
            m2: D值平滑周期

        Returns:
            包含K, D, J的DataFrame
        """
        low_n = low.rolling(window=n).min()
        high_n = high.rolling(window=n).max()
        rsv = (close - low_n) / (high_n - low_n) * 100

        k = rsv.ewm(com=m1 - 1, adjust=False).mean()
        d = k.ewm(com=m2 - 1, adjust=False).mean()
        j = 3 * k - 2 * d

        return pd.DataFrame({
            'K': k,
            'D': d,
            'J': j
        })

    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2) -> pd.DataFrame:
        """计算布林带 (Bollinger Bands)

        Args:
            data: 价格序列
            period: 周期
            std_dev: 标准差倍数

        Returns:
            包含上轨、中轨、下轨的DataFrame
        """
        middle = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return pd.DataFrame({
            'upper': upper,
            'middle': middle,
            'lower': lower
        })

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """计算平均真实波幅 (ATR)

        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            period: 周期

        Returns:
            ATR序列
        """
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """计算能量潮 (OBV)

        Args:
            close: 收盘价序列
            volume: 成交量序列

        Returns:
            OBV序列
        """
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """为K线数据添加常用技术指标

    Args:
        df: K线数据DataFrame，需包含'开盘','收盘','最高','最低','成交量'列

    Returns:
        添加指标后的DataFrame
    """
    df = df.copy()

    # 移动平均线
    df['MA5'] = TechnicalIndicators.ma(df['收盘'], 5)
    df['MA10'] = TechnicalIndicators.ma(df['收盘'], 10)
    df['MA20'] = TechnicalIndicators.ma(df['收盘'], 20)
    df['MA60'] = TechnicalIndicators.ma(df['收盘'], 60)

    # MACD
    macd_df = TechnicalIndicators.macd(df['收盘'])
    df = pd.concat([df, macd_df], axis=1)

    # RSI
    df['RSI'] = TechnicalIndicators.rsi(df['收盘'])

    # KDJ
    kdj_df = TechnicalIndicators.kdj(df['最高'], df['最低'], df['收盘'])
    df = pd.concat([df, kdj_df], axis=1)

    # 布林带
    bb_df = TechnicalIndicators.bollinger_bands(df['收盘'])
    df = pd.concat([df, bb_df], axis=1)

    # ATR
    df['ATR'] = TechnicalIndicators.atr(df['最高'], df['最低'], df['收盘'])

    # OBV
    df['OBV'] = TechnicalIndicators.obv(df['收盘'], df['成交量'])

    return df
