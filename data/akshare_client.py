"""多数据源客户端"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import os
import warnings

# 禁用代理
os.environ['NO_PROXY'] = '*'
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''


class DataSourceBase:
    """数据源基类"""

    @staticmethod
    def get_stock_list(market: str = "A") -> pd.DataFrame:
        """获取股票列表"""
        raise NotImplementedError

    @staticmethod
    def get_stock_history(code: str, start_date: Optional[str] = None,
                         end_date: Optional[str] = None, period: str = "daily") -> pd.DataFrame:
        """获取历史K线"""
        raise NotImplementedError

    @staticmethod
    def get_stock_realtime(code: str) -> pd.DataFrame:
        """获取实时行情"""
        raise NotImplementedError

    @staticmethod
    def get_stock_name(code: str) -> str:
        """获取股票名称"""
        raise NotImplementedError


class AkShareClient(DataSourceBase):
    """AkShare数据源客户端"""

    @staticmethod
    def get_stock_list(market: str = "A") -> pd.DataFrame:
        """获取股票列表

        Args:
            market: 市场类型 (A=沪深A股)

        Returns:
            股票列表DataFrame
        """
        try:
            if market == "A":
                return ak.stock_info_a_code_name()
            elif market == "HK":
                return ak.stock_hk_spot_em()
            else:
                raise ValueError(f"不支持的市场类型: {market}")
        except Exception as e:
            warnings.warn(f"AkShare获取股票列表失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_stock_history(
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "daily"
    ) -> pd.DataFrame:
        """获取股票历史K线数据

        Args:
            code: 股票代码 (如: 000001)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            period: 周期 (daily=日线, weekly=周线, monthly=月线)

        Returns:
            K线数据DataFrame
        """
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        df = ak.stock_zh_a_hist(
            symbol=code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        df['日期'] = pd.to_datetime(df['日期'])
        df = df.sort_values('日期').reset_index(drop=True)
        return df

    @staticmethod
    def get_stock_realtime(code: str) -> pd.DataFrame:
        """获取股票实时行情

        Args:
            code: 股票代码

        Returns:
            实时行情DataFrame
        """
        return ak.stock_zh_a_spot_em()

    @staticmethod
    def get_stock_fundamental(code: str, year: int, quarter: int) -> pd.DataFrame:
        """获取股票财务数据

        Args:
            code: 股票代码
            year: 年份
            quarter: 季度 (1-4)

        Returns:
            财务数据DataFrame
        """
        return ak.stock_financial_analysis_indicator(symbol=code)

    @staticmethod
    def get_index_list() -> pd.DataFrame:
        """获取指数列表"""
        return ak.index_stock_info()

    @staticmethod
    def get_index_history(code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """获取指数历史数据"""
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        df = ak.index_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date
        )
        df['日期'] = pd.to_datetime(df['日期'])
        df = df.sort_values('日期').reset_index(drop=True)
        return df

    @staticmethod
    def get_stock_name(code: str) -> str:
        """获取股票名称"""
        try:
            df = ak.stock_info_a_code_name()
            result = df[df['code'] == code]
            if not result.empty:
                return result.iloc[0]['name']
        except Exception:
            pass
        return "未知"

    @staticmethod
    def get_auction_data(code: str) -> dict:
        """获取竞价数据

        Args:
            code: 股票代码

        Returns:
            竞价数据字典
        """
        try:
            # AkShare竞价数据接口
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == code]
            if not stock_data.empty:
                return {
                    'code': code,
                    'auction_price': stock_data.iloc[0]['最新价'],
                    'auction_change': stock_data.iloc[0]['涨跌幅'] / 100,
                    'auction_volume': stock_data.iloc[0]['成交量'],
                    'auction_amount': stock_data.iloc[0]['成交额']
                }
        except Exception as e:
            warnings.warn(f"AkShare获取竞价数据失败: {e}")
        return {
            'code': code,
            'auction_price': 0,
            'auction_change': 0,
            'auction_volume': 0,
            'auction_amount': 0
        }

    @staticmethod
    def get_limit_up_list(date: str = None) -> pd.DataFrame:
        """获取涨停板列表

        Args:
            date: 日期 (YYYYMMDD)，默认为今天

        Returns:
            涨停板列表DataFrame
        """
        try:
            if date is None:
                date = datetime.now().strftime("%Y%m%d")

            # 获取当日股票数据
            df = ak.stock_zh_a_spot_em()

            # 计算涨幅
            df['change_percent'] = df['涨跌幅']

            # 涨停筛选
            limit_up_df = df[df['涨跌幅'] >= 9.5].copy()
            return limit_up_df
        except Exception as e:
            warnings.warn(f"AkShare获取涨停板数据失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_sector_data(date: str = None) -> pd.DataFrame:
        """获取板块数据

        Args:
            date: 日期

        Returns:
            板块数据DataFrame
        """
        try:
            # 获取行业板块数据
            df = ak.stock_board_industry_name_em()
            return df
        except Exception as e:
            warnings.warn(f"AkShare获取板块数据失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_market_overview(date: str = None) -> dict:
        """获取市场整体数据

        Args:
            date: 日期

        Returns:
            市场整体数据字典
        """
        try:
            # 获取市场概况
            df = ak.stock_zh_a_spot_em()

            if df.empty:
                return {
                    'date': date or datetime.now().strftime("%Y-%m-%d"),
                    'limit_up_count': 0,
                    'limit_down_count': 0,
                    'limit_up_list': pd.DataFrame()
                }

            # 计算涨跌停
            limit_up_count = len(df[df['涨跌幅'] >= 9.5])
            limit_down_count = len(df[df['涨跌幅'] <= -9.5])

            return {
                'date': date or datetime.now().strftime("%Y-%m-%d"),
                'limit_up_count': limit_up_count,
                'limit_down_count': limit_down_count,
                'limit_up_list': df[df['涨跌幅'] >= 9.5]
            }
        except Exception as e:
            warnings.warn(f"AkShare获取市场概况失败: {e}")
            return {
                'date': date or datetime.now().strftime("%Y-%m-%d"),
                'limit_up_count': 0,
                'limit_down_count': 0,
                'limit_up_list': pd.DataFrame()
            }


class TushareClient(DataSourceBase):
    """Tushare数据源客户端 - 需要token"""

    def __init__(self, token: str = None):
        """初始化Tushare客户端

        Args:
            token: Tushare API token
        """
        self.token = token
        self.pro = None
        if token:
            try:
                import tushare as ts
                ts.set_token(token)
                self.pro = ts.pro_api()
            except Exception as e:
                warnings.warn(f"Tushare初始化失败: {e}")

    def get_stock_list(self, market: str = "A") -> pd.DataFrame:
        """获取股票列表"""
        if not self.pro:
            warnings.warn("Tushare未初始化，请提供有效的token")
            return pd.DataFrame()

        try:
            df = self.pro.stock_basic(exchange='', list_status='L',
                                     fields='ts_code,symbol,name,area,industry,list_date')
            return df
        except Exception as e:
            warnings.warn(f"Tushare获取股票列表失败: {e}")
            return pd.DataFrame()

    def get_stock_history(self, code: str, start_date: Optional[str] = None,
                         end_date: Optional[str] = None, period: str = "daily") -> pd.DataFrame:
        """获取历史K线"""
        if not self.pro:
            return pd.DataFrame()

        try:
            # 转换代码格式 (000001 -> 000001.SZ)
            ts_code = f"{code}.SZ" if code.startswith('0') or code.startswith('3') else f"{code}.SH"

            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            if end_date is None:
                end_date = datetime.now().strftime("%Y%m%d")

            df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df.empty:
                return df

            df['日期'] = pd.to_datetime(df['trade_date'])
            df = df.rename(columns={
                'open': '开盘', 'high': '最高', 'low': '最低',
                'close': '收盘', 'vol': '成交量', 'amount': '成交额'
            })
            df = df.sort_values('日期').reset_index(drop=True)
            return df
        except Exception as e:
            warnings.warn(f"Tushare获取历史数据失败: {e}")
            return pd.DataFrame()

    def get_stock_realtime(self, code: str) -> pd.DataFrame:
        """获取实时行情"""
        # Tushare主要提供历史数据，实时行情需要其他方式
        warnings.warn("Tushare暂不支持实时行情")
        return pd.DataFrame()

    def get_stock_name(self, code: str) -> str:
        """获取股票名称"""
        if not self.pro:
            return "未知"

        try:
            ts_code = f"{code}.SZ" if code.startswith('0') or code.startswith('3') else f"{code}.SH"
            df = self.pro.stock_basic(ts_code=ts_code, fields='name')
            if not df.empty:
                return df.iloc[0]['name']
        except Exception:
            pass
        return "未知"


class BaoStockClient(DataSourceBase):
    """BaoStock数据源客户端 - 免费开源"""

    def __init__(self):
        """初始化BaoStock客户端"""
        try:
            import baostock as bs
            self.bs = bs
            self.login_result = bs.login()
            if self.login_result.error_code != '0':
                warnings.warn(f"BaoStock登录失败: {self.login_result.error_msg}")
        except Exception as e:
            warnings.warn(f"BaoStock初始化失败: {e}")
            self.bs = None

    def __del__(self):
        """退出登录"""
        if hasattr(self, 'bs') and self.bs:
            try:
                self.bs.logout()
            except:
                pass

    def get_stock_list(self, market: str = "A") -> pd.DataFrame:
        """获取股票列表"""
        if not self.bs:
            return pd.DataFrame()

        try:
            rs = self.bs.query_all_stock(day=datetime.now().strftime("%Y-%m-%d"))
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            df = pd.DataFrame(data_list, columns=rs.fields)
            return df
        except Exception as e:
            warnings.warn(f"BaoStock获取股票列表失败: {e}")
            return pd.DataFrame()

    def get_stock_history(self, code: str, start_date: Optional[str] = None,
                         end_date: Optional[str] = None, period: str = "daily") -> pd.DataFrame:
        """获取历史K线"""
        if not self.bs:
            return pd.DataFrame()

        try:
            # 转换代码格式
            bs_code = f"sz.{code}" if code.startswith('0') or code.startswith('3') else f"sh.{code}"

            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")

            # 转换为BaoStock需要的YYYY-MM-DD格式（如果输入是其他格式）
            if '-' in start_date:
                # 已经是YYYY-MM-DD格式，保持不变
                pass
            else:
                # 从YYYYMMDD转换为YYYY-MM-DD
                start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"

            if '-' in end_date:
                # 已经是YYYY-MM-DD格式，保持不变
                pass
            else:
                # 从YYYYMMDD转换为YYYY-MM-DD
                end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"

            rs = self.bs.query_history_k_data_plus(
                bs_code,
                "date,open,high,low,close,volume,amount",
                start_date=start_date, end_date=end_date,
                frequency="d" if period == "daily" else "w" if period == "weekly" else "m",
                adjustflag="2"  # 前复权
            )

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                return pd.DataFrame()

            df = pd.DataFrame(data_list, columns=['日期', '开盘', '最高', '最低', '收盘', '成交量', '成交额'])
            df['日期'] = pd.to_datetime(df['日期'])
            df['开盘'] = df['开盘'].astype(float)
            df['最高'] = df['最高'].astype(float)
            df['最低'] = df['最低'].astype(float)
            df['收盘'] = df['收盘'].astype(float)
            df['成交量'] = df['成交量'].astype(float)
            df['成交额'] = df['成交额'].astype(float)

            return df.sort_values('日期').reset_index(drop=True)
        except Exception as e:
            warnings.warn(f"BaoStock获取历史数据失败: {e}")
            return pd.DataFrame()

    def get_stock_realtime(self, code: str) -> pd.DataFrame:
        """获取实时行情"""
        warnings.warn("BaoStock暂不支持实时行情")
        return pd.DataFrame()

    def get_stock_name(self, code: str) -> str:
        """获取股票名称"""
        if not self.bs:
            return "未知"

        try:
            bs_code = f"sz.{code}" if code.startswith('0') or code.startswith('3') else f"sh.{code}"
            rs = self.bs.query_stock_basic(code=bs_code)
            if rs.error_code == '0' and rs.next():
                return rs.get_row_data()[1]  # name字段
        except Exception:
            pass
        return "未知"

    def get_auction_data(self, code: str) -> dict:
        """获取竞价数据（模拟，实际需要真实数据源）

        Args:
            code: 股票代码

        Returns:
            竞价数据字典
        """
        # BaoStock不提供竞价数据，这里返回空字典
        # 实际使用时需要AkShare或其他数据源
        return {
            'code': code,
            'auction_price': 0,
            'auction_change': 0,
            'auction_volume': 0,
            'auction_amount': 0
        }

    def get_limit_up_list(self, date: str = None) -> pd.DataFrame:
        """获取涨停板列表

        Args:
            date: 日期 (YYYY-MM-DD)，默认为今天

        Returns:
            涨停板列表DataFrame
        """
        if not self.bs:
            return pd.DataFrame()

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            # 获取当日所有股票数据
            rs = self.bs.query_all_stock(day=date, field="date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pctChg,amplitude")
            data_list = []

            while (rs.error_code == '0') & rs.next():
                data = rs.get_row_data()
                data_list.append(data)

            if not data_list:
                return pd.DataFrame()

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 计算涨停板（涨幅接近10%或20%）
            df['change'] = df['close'].astype(float) - df['preclose'].astype(float)
            df['change_percent'] = (df['change'].astype(float) / df['preclose'].astype(float) * 100)

            # 涨停：主板9.8%以上，创业板/科创板19.8%以上
            df['is_limit_up'] = df['change_percent'] >= 9.8

            limit_up_stocks = df[df['is_limit_up']].copy()
            return limit_up_stocks
        except Exception as e:
            warnings.warn(f"BaoStock获取涨停板数据失败: {e}")
            return pd.DataFrame()

    def get_sector_data(self, date: str = None) -> pd.DataFrame:
        """获取板块数据

        Args:
            date: 日期

        Returns:
            板块数据DataFrame
        """
        # BaoStock不直接提供板块数据，返回空DataFrame
        # 实际使用时需要AkShare等其他数据源
        return pd.DataFrame()

    def get_market_overview(self, date: str = None) -> dict:
        """获取市场整体数据

        Args:
            date: 日期

        Returns:
            市场整体数据字典
        """
        limit_up_df = self.get_limit_up_list(date)

        # 计算涨跌停家数（模拟）
        limit_up_count = len(limit_up_df) if not limit_up_df.empty else 0
        limit_down_count = 0  # 需要实际数据

        return {
            'date': date or datetime.now().strftime("%Y-%m-%d"),
            'limit_up_count': limit_up_count,
            'limit_down_count': limit_down_count,
            'limit_up_list': limit_up_df
        }


class DataClient:
    """统一数据客户端 - 支持多数据源切换"""

    def __init__(self, source: str = "akshare", tushare_token: str = None):
        """初始化数据客户端

        Args:
            source: 数据源 ('akshare', 'tushare', 'baostock')
            tushare_token: Tushare的token (当source='tushare'时需要)
        """
        self.source = source.lower()
        self.client = None

        if self.source == "akshare":
            self.client = AkShareClient()
        elif self.source == "tushare":
            self.client = TushareClient(tushare_token)
        elif self.source == "baostock":
            self.client = BaoStockClient()
        else:
            raise ValueError(f"不支持的数据源: {source}")

    def get_stock_list(self, market: str = "A") -> pd.DataFrame:
        """获取股票列表"""
        return self.client.get_stock_list(market)

    def get_stock_history(self, code: str, start_date: Optional[str] = None,
                         end_date: Optional[str] = None, period: str = "daily") -> pd.DataFrame:
        """获取历史K线"""
        return self.client.get_stock_history(code, start_date, end_date, period)

    def get_stock_realtime(self, code: str) -> pd.DataFrame:
        """获取实时行情"""
        return self.client.get_stock_realtime(code)

    def get_stock_name(self, code: str) -> str:
        """获取股票名称"""
        return self.client.get_stock_name(code)

    def get_auction_data(self, code: str) -> dict:
        """获取竞价数据"""
        if hasattr(self.client, 'get_auction_data'):
            return self.client.get_auction_data(code)
        return {
            'code': code,
            'auction_price': 0,
            'auction_change': 0,
            'auction_volume': 0,
            'auction_amount': 0
        }

    def get_limit_up_list(self, date: str = None) -> pd.DataFrame:
        """获取涨停板列表"""
        if hasattr(self.client, 'get_limit_up_list'):
            return self.client.get_limit_up_list(date)
        return pd.DataFrame()

    def get_sector_data(self, date: str = None) -> pd.DataFrame:
        """获取板块数据"""
        if hasattr(self.client, 'get_sector_data'):
            return self.client.get_sector_data(date)
        return pd.DataFrame()

    def get_market_overview(self, date: str = None) -> dict:
        """获取市场整体数据"""
        if hasattr(self.client, 'get_market_overview'):
            return self.client.get_market_overview(date)
        return {
            'date': date or datetime.now().strftime("%Y-%m-%d"),
            'limit_up_count': 0,
            'limit_down_count': 0,
            'limit_up_list': pd.DataFrame()
        }

    def switch_source(self, source: str, tushare_token: str = None):
        """切换数据源"""
        self.__init__(source, tushare_token)
