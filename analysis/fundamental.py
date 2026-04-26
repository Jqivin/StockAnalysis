"""基本面分析模块"""
import pandas as pd
from typing import Optional


class FundamentalAnalysis:
    """基本面分析类"""

    @staticmethod
    def get_valuation_metrics(code: str) -> pd.DataFrame:
        """获取估值指标

        Args:
            code: 股票代码

        Returns:
            估值指标DataFrame
        """
        import akshare as ak
        try:
            df = ak.stock_a_lg_indicator(symbol=code)
            return df
        except Exception as e:
            print(f"获取估值指标失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_financial_report(code: str, report_type: str = "利润表") -> pd.DataFrame:
        """获取财务报表

        Args:
            code: 股票代码
            report_type: 报表类型 (利润表/资产负债表/现金流量表)

        Returns:
            财务报表DataFrame
        """
        import akshare as ak
        try:
            if report_type == "利润表":
                df = ak.stock_financial_analysis_indicator(symbol=code)
            elif report_type == "资产负债表":
                df = ak.stock_balance_sheet_by_report_em(symbol=code)
            elif report_type == "现金流量表":
                df = ak.stock_cash_flow_sheet_by_report_em(symbol=code)
            else:
                raise ValueError(f"不支持的报表类型: {report_type}")
            return df
        except Exception as e:
            print(f"获取{report_type}失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def calculate_pe_ratio(price: float, eps: float) -> float:
        """计算市盈率 (PE)

        Args:
            price: 股价
            eps: 每股收益

        Returns:
            市盈率
        """
        if eps == 0:
            return 0
        return price / eps

    @staticmethod
    def calculate_pb_ratio(price: float, bps: float) -> float:
        """计算市净率 (PB)

        Args:
            price: 股价
            bps: 每股净资产

        Returns:
            市净率
        """
        if bps == 0:
            return 0
        return price / bps

    @staticmethod
    def calculate_roe(net_profit: float, equity: float) -> float:
        """计算净资产收益率 (ROE)

        Args:
            net_profit: 净利润
            equity: 股东权益

        Returns:
            ROE (%)
        """
        if equity == 0:
            return 0
        return (net_profit / equity) * 100

    @staticmethod
    def calculate_roa(net_profit: float, total_assets: float) -> float:
        """计算总资产收益率 (ROA)

        Args:
            net_profit: 净利润
            total_assets: 总资产

        Returns:
            ROA (%)
        """
        if total_assets == 0:
            return 0
        return (net_profit / total_assets) * 100

    @staticmethod
    def calculate_debt_ratio(total_liabilities: float, total_assets: float) -> float:
        """计算资产负债率

        Args:
            total_liabilities: 总负债
            total_assets: 总资产

        Returns:
            资产负债率 (%)
        """
        if total_assets == 0:
            return 0
        return (total_liabilities / total_assets) * 100

    @staticmethod
    def calculate_current_ratio(current_assets: float, current_liabilities: float) -> float:
        """计算流动比率

        Args:
            current_assets: 流动资产
            current_liabilities: 流动负债

        Returns:
            流动比率
        """
        if current_liabilities == 0:
            return 0
        return current_assets / current_liabilities

    @staticmethod
    def calculate_quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> float:
        """计算速动比率

        Args:
            current_assets: 流动资产
            inventory: 存货
            current_liabilities: 流动负债

        Returns:
            速动比率
        """
        if current_liabilities == 0:
            return 0
        return (current_assets - inventory) / current_liabilities

    @staticmethod
    def calculate_gross_revenue(revenue: float, cost: float) -> float:
        """计算毛利率

        Args:
            revenue: 营业收入
            cost: 营业成本

        Returns:
            毛利率 (%)
        """
        if revenue == 0:
            return 0
        return ((revenue - cost) / revenue) * 100

    @staticmethod
    def calculate_net_profit_margin(net_profit: float, revenue: float) -> float:
        """计算净利率

        Args:
            net_profit: 净利润
            revenue: 营业收入

        Returns:
            净利率 (%)
        """
        if revenue == 0:
            return 0
        return (net_profit / revenue) * 100


def get_stock_fundamental_summary(code: str) -> dict:
    """获取股票基本面摘要

    Args:
        code: 股票代码

    Returns:
        基本面摘要字典
    """
    fa = FundamentalAnalysis()
    summary = {}

    # 获取估值指标
    valuation = fa.get_valuation_metrics(code)
    if not valuation.empty:
        latest = valuation.iloc[0]
        summary['pe_ratio'] = latest.get('pe', 0)
        summary['pb_ratio'] = latest.get('pb', 0)
        summary['ps_ratio'] = latest.get('ps', 0)
        summary['market_cap'] = latest.get('total_mv', 0)

    # 获取利润表
    income = fa.get_financial_report(code, "利润表")
    if not income.empty:
        latest = income.iloc[0]
        summary['revenue'] = latest.get('营业收入', 0)
        summary['net_profit'] = latest.get('净利润', 0)
        summary['gross_profit_margin'] = latest.get('销售毛利率', 0)
        summary['net_profit_margin'] = latest.get('销售净利率', 0)

    # 获取资产负债表
    balance = fa.get_financial_report(code, "资产负债表")
    if not balance.empty:
        latest = balance.iloc[0]
        summary['total_assets'] = latest.get('资产总计', 0)
        summary['total_liabilities'] = latest.get('负债合计', 0)
        summary['total_equity'] = latest.get('股东权益合计', 0)

        # 计算衍生指标
        summary['debt_ratio'] = fa.calculate_debt_ratio(
            summary['total_liabilities'],
            summary['total_assets']
        )
        summary['roe'] = fa.calculate_roe(
            summary['net_profit'],
            summary['total_equity']
        )

    return summary
