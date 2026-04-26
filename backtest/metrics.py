"""回测指标计算模块"""
import pandas as pd
import numpy as np
from typing import Dict, Any


class BacktestMetrics:
    """回测指标计算类"""

    @staticmethod
    def calculate_return(equity_series: pd.Series) -> float:
        """计算总收益率

        Args:
            equity_series: 权益序列

        Returns:
            总收益率
        """
        if len(equity_series) < 2:
            return 0
        return (equity_series.iloc[-1] - equity_series.iloc[0]) / equity_series.iloc[0]

    @staticmethod
    def calculate_annual_return(equity_series: pd.Series, trading_days: int = 252) -> float:
        """计算年化收益率

        Args:
            equity_series: 权益序列
            trading_days: 年交易日数

        Returns:
            年化收益率
        """
        if len(equity_series) < 2:
            return 0
        days = len(equity_series)
        total_return = BacktestMetrics.calculate_return(equity_series)
        return (1 + total_return) ** (trading_days / days) - 1

    @staticmethod
    def calculate_volatility(equity_series: pd.Series, trading_days: int = 252) -> float:
        """计算年化波动率

        Args:
            equity_series: 权益序列
            trading_days: 年交易日数

        Returns:
            年化波动率
        """
        if len(equity_series) < 2:
            return 0
        returns = equity_series.pct_change().dropna()
        return returns.std() * np.sqrt(trading_days)

    @staticmethod
    def calculate_sharpe_ratio(equity_series: pd.Series, risk_free_rate: float = 0.03, trading_days: int = 252) -> float:
        """计算夏普比率

        Args:
            equity_series: 权益序列
            risk_free_rate: 无风险利率
            trading_days: 年交易日数

        Returns:
            夏普比率
        """
        if len(equity_series) < 2:
            return 0
        annual_return = BacktestMetrics.calculate_annual_return(equity_series, trading_days)
        volatility = BacktestMetrics.calculate_volatility(equity_series, trading_days)
        if volatility == 0:
            return 0
        return (annual_return - risk_free_rate) / volatility

    @staticmethod
    def calculate_max_drawdown(equity_series: pd.Series) -> float:
        """计算最大回撤

        Args:
            equity_series: 权益序列

        Returns:
            最大回撤
        """
        if len(equity_series) < 2:
            return 0
        cumulative = (equity_series / equity_series.iloc[0]).fillna(1)
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        return drawdown.min()

    @staticmethod
    def calculate_win_rate(trades_df: pd.DataFrame) -> float:
        """计算胜率

        Args:
            trades_df: 交易记录DataFrame

        Returns:
            胜率
        """
        if trades_df.empty:
            return 0

        # 配对买卖交易
        buy_trades = trades_df[trades_df['action'] == 'buy']
        sell_trades = trades_df[trades_df['action'] == 'sell']

        if len(buy_trades) == 0 or len(sell_trades) == 0:
            return 0

        # 计算每笔交易的盈亏
        profits = []
        min_pairs = min(len(buy_trades), len(sell_trades))
        for i in range(min_pairs):
            buy_price = buy_trades.iloc[i]['price']
            sell_price = sell_trades.iloc[i]['price']
            profit = (sell_price - buy_price) / buy_price
            profits.append(profit)

        if not profits:
            return 0

        wins = sum(1 for p in profits if p > 0)
        return wins / len(profits)

    @staticmethod
    def calculate_profit_factor(trades_df: pd.DataFrame) -> float:
        """计算盈亏比

        Args:
            trades_df: 交易记录DataFrame

        Returns:
            盈亏比
        """
        if trades_df.empty:
            return 0

        buy_trades = trades_df[trades_df['action'] == 'buy']
        sell_trades = trades_df[trades_df['action'] == 'sell']

        if len(buy_trades) == 0 or len(sell_trades) == 0:
            return 0

        total_profit = 0
        total_loss = 0

        min_pairs = min(len(buy_trades), len(sell_trades))
        for i in range(min_pairs):
            buy_price = buy_trades.iloc[i]['price']
            sell_price = sell_trades.iloc[i]['price']
            profit = (sell_price - buy_price) / buy_price

            if profit > 0:
                total_profit += profit
            else:
                total_loss += abs(profit)

        if total_loss == 0:
            return float('inf') if total_profit > 0 else 0

        return total_profit / total_loss

    @staticmethod
    def calculate_all(equity_series: pd.Series, trades_df: pd.DataFrame) -> Dict[str, float]:
        """计算所有指标

        Args:
            equity_series: 权益序列
            trades_df: 交易记录DataFrame

        Returns:
            指标字典
        """
        return {
            'total_return': BacktestMetrics.calculate_return(equity_series),
            'annual_return': BacktestMetrics.calculate_annual_return(equity_series),
            'volatility': BacktestMetrics.calculate_volatility(equity_series),
            'sharpe_ratio': BacktestMetrics.calculate_sharpe_ratio(equity_series),
            'max_drawdown': BacktestMetrics.calculate_max_drawdown(equity_series),
            'win_rate': BacktestMetrics.calculate_win_rate(trades_df),
            'profit_factor': BacktestMetrics.calculate_profit_factor(trades_df)
        }


def print_backtest_report(report: Dict[str, Any]):
    """打印回测报告

    Args:
        report: 回测结果字典
    """
    print("\n" + "=" * 50)
    print("回测报告".center(50))
    print("=" * 50)
    print(f"初始资金: ¥{report['initial_capital']:,.2f}")
    print(f"最终资金: ¥{report['final_capital']:,.2f}")
    print(f"总收益率: {report['total_return']*100:.2f}%")
    print("-" * 50)

    if 'annual_return' in report:
        print(f"年化收益率: {report['annual_return']*100:.2f}%")
        print(f"年化波动率: {report['volatility']*100:.2f}%")
        print(f"夏普比率: {report['sharpe_ratio']:.2f}")
        print(f"最大回撤: {report['max_drawdown']*100:.2f}%")
        print(f"胜率: {report['win_rate']*100:.2f}%")
        print(f"盈亏比: {report['profit_factor']:.2f}")

    print("-" * 50)
    print(f"总交易次数: {report['total_trades']}")
    print("=" * 50)
