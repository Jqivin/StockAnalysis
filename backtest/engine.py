"""回测引擎"""
import pandas as pd
from typing import Dict, Any, List
from backtest.strategy import Strategy, create_strategy
from backtest.metrics import BacktestMetrics
from analysis.technical import add_indicators


class BacktestEngine:
    """回测引擎"""

    def __init__(self, initial_capital: float = 100000, commission: float = 0.0003):
        """初始化回测引擎

        Args:
            initial_capital: 初始资金
            commission: 手续费率
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.cash = initial_capital
        self.position = 0
        self.trades = []
        self.equity_curve = []

    def run(self, data: pd.DataFrame, strategy: Strategy) -> Dict[str, Any]:
        """运行回测

        Args:
            data: K线数据
            strategy: 策略实例

        Returns:
            回测结果
        """
        # 添加技术指标
        data = add_indicators(data)

        # 添加前一日的数据用于交叉判断
        data['prev_收盘'] = data['收盘'].shift(1)
        for col in ['MA5', 'MA10', 'MA20', 'MA60', 'DIF', 'DEA', 'RSI', 'upper', 'lower']:
            if col in data.columns:
                # 确保列是Series而不是DataFrame
                if isinstance(data[col], pd.Series):
                    data[f'prev_{col}'] = data[col].shift(1)

        self.cash = self.initial_capital
        self.position = 0
        self.trades = []
        self.equity_curve = []

        for i in range(len(data)):
            bar = data.iloc[i]
            signal = strategy.on_bar(bar, i)

            if signal == 'buy' and self.cash > 0:
                # 买入
                price = bar['收盘']
                shares = int(self.cash / (price * (1 + self.commission)))
                if shares > 0:
                    cost = shares * price * (1 + self.commission)
                    self.cash -= cost
                    self.position += shares
                    self.trades.append({
                        'date': bar['日期'],
                        'action': 'buy',
                        'price': price,
                        'shares': shares,
                        'cost': cost
                    })

            elif signal == 'sell' and self.position > 0:
                # 卖出
                price = bar['收盘']
                revenue = self.position * price * (1 - self.commission)
                self.cash += revenue
                self.trades.append({
                    'date': bar['日期'],
                    'action': 'sell',
                    'price': price,
                    'shares': self.position,
                    'revenue': revenue
                })
                self.position = 0

            # 记录权益曲线
            total_value = self.cash + self.position * bar['收盘']
            self.equity_curve.append({
                'date': bar['日期'],
                'equity': total_value
            })

        # 最后平仓
        if self.position > 0:
            last_price = data.iloc[-1]['收盘']
            revenue = self.position * last_price * (1 - self.commission)
            self.cash += revenue
            self.trades.append({
                'date': data.iloc[-1]['日期'],
                'action': 'sell',
                'price': last_price,
                'shares': self.position,
                'revenue': revenue
            })
            self.position = 0

        return self._generate_report()

    def _generate_report(self) -> Dict[str, Any]:
        """生成回测报告"""
        metrics = BacktestMetrics()
        equity_series = pd.Series([e['equity'] for e in self.equity_curve])
        trades_df = pd.DataFrame(self.trades)

        report = {
            'initial_capital': self.initial_capital,
            'final_capital': self.cash,
            'total_return': (self.cash - self.initial_capital) / self.initial_capital,
            'total_trades': len(trades_df),
            'win_trades': len(trades_df[trades_df['action'] == 'sell']) if not trades_df.empty else 0,
            'equity_curve': pd.DataFrame(self.equity_curve),
            'trades': trades_df
        }

        # 计算更多指标
        if len(equity_series) > 1:
            report.update(metrics.calculate_all(equity_series, trades_df))

        return report


def backtest(
    data: pd.DataFrame,
    strategy_name: str = 'ma',
    initial_capital: float = 100000,
    **strategy_params
) -> Dict[str, Any]:
    """便捷回测函数

    Args:
        data: K线数据
        strategy_name: 策略名称
        initial_capital: 初始资金
        **strategy_params: 策略参数

    Returns:
        回测结果
    """
    strategy = create_strategy(strategy_name, **strategy_params)
    engine = BacktestEngine(initial_capital=initial_capital)
    return engine.run(data, strategy)
