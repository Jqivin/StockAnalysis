"""市场情绪判断模块"""
from typing import Dict, Tuple
from data.akshare_client import DataClient


class MarketSentiment:
    """市场情绪判断类"""

    # 情绪判断阈值
    STRONG_LIMIT_UP_MIN = 50      # 强势：涨停家数
    STRONG_LIMIT_DOWN_MAX = 5     # 强势：跌停家数
    STRONG_SUCCESS_RATE_MIN = 0.7 # 强势：连板成功率

    DIVERGENT_LIMIT_UP_MIN = 30    # 分歧：涨停家数下限
    DIVERGENT_LIMIT_UP_MAX = 50   # 分歧：涨停家数上限
    DIVERGENT_LIMIT_DOWN_MIN = 5  # 分歧：跌停家数下限
    DIVERGENT_LIMIT_DOWN_MAX = 15 # 分歧：跌停家数上限
    DIVERGENT_SUCCESS_RATE_MIN = 0.5 # 分歧：连板成功率下限
    DIVERGENT_SUCCESS_RATE_MAX = 0.7 # 分歧：连板成功率上限

    # 硬性条件
    MIN_LIMIT_UP_TO_TRADE = 20    # 最低涨停家数才能交易
    MAX_LIMIT_DOWN_TO_TRADE = 20  # 最高跌停家数还能交易
    MAX_BROKEN_RATE_TO_TRADE = 0.3 # 最高炸板率还能交易

    @classmethod
    def get_sentiment(cls, limit_up_count: int, limit_down_count: int,
                    success_rate: float, broken_rate: float = 0) -> Tuple[str, str]:
        """获取市场情绪等级

        Args:
            limit_up_count: 涨停家数
            limit_down_count: 跌停家数
            success_rate: 连板成功率 (0-1)
            broken_rate: 炸板率 (0-1)

        Returns:
            (情绪等级, 操作建议)
        """
        # 检查硬性条件
        if limit_up_count < cls.MIN_LIMIT_UP_TO_TRADE or limit_down_count > cls.MAX_LIMIT_DOWN_TO_TRADE:
            return "downtrend", "禁止操作（市场环境恶劣）"

        if broken_rate > cls.MAX_BROKEN_RATE_TO_TRADE:
            return "downtrend", "禁止操作（炸板率过高）"

        # 判断情绪等级
        if (limit_up_count >= cls.STRONG_LIMIT_UP_MIN and
            limit_down_count <= cls.STRONG_LIMIT_DOWN_MAX and
            success_rate >= cls.STRONG_SUCCESS_RATE_MIN):
            return "strong", "积极出击"

        elif (cls.DIVERGENT_LIMIT_UP_MIN <= limit_up_count <= cls.DIVERGENT_LIMIT_UP_MAX and
              cls.DIVERGENT_LIMIT_DOWN_MIN <= limit_down_count <= cls.DIVERGENT_LIMIT_DOWN_MAX and
              cls.DIVERGENT_SUCCESS_RATE_MIN <= success_rate <= cls.DIVERGENT_SUCCESS_RATE_MAX):
            return "divergent", "控制仓位"

        else:
            return "downtrend", "空仓观望"

    @classmethod
    def check_trade_conditions(cls, limit_up_count: int, limit_down_count: int,
                              broken_rate: float = 0) -> bool:
        """检查是否满足交易条件

        Args:
            limit_up_count: 涨停家数
            limit_down_count: 跌停家数
            broken_rate: 炸板率

        Returns:
            是否可以交易
        """
        if limit_up_count < cls.MIN_LIMIT_UP_TO_TRADE:
            return False

        if limit_down_count > cls.MAX_LIMIT_DOWN_TO_TRADE:
            return False

        if broken_rate > cls.MAX_BROKEN_RATE_TO_TRADE:
            return False

        return True

    @classmethod
    def get_position_limit(cls, sentiment: str) -> Dict[str, float]:
        """根据情绪等级获取仓位限制

        Args:
            sentiment: 情绪等级 (strong/divergent/downtrend)

        Returns:
            仓位限制字典
        """
        if sentiment == "strong":
            return {
                'single_stock_max': 0.3,  # 单股最多30%
                'total_position_max': 0.7,  # 总仓位最多70%
                'max_stocks': 3             # 最多3只股票
            }
        elif sentiment == "divergent":
            return {
                'single_stock_max': 0.2,
                'total_position_max': 0.5,
                'max_stocks': 2
            }
        else:  # downtrend
            return {
                'single_stock_max': 0.0,
                'total_position_max': 0.0,
                'max_stocks': 0
            }


def get_market_sentiment(date: str = None) -> Dict:
    """获取市场情绪分析

    Args:
        date: 日期 (YYYY-MM-DD)，默认为今天

    Returns:
        市场情绪字典
    """
    client = DataClient(source="akshare")
    overview = client.get_market_overview(date)

    # 模拟连板成功率和炸板率（实际需要历史数据计算）
    success_rate = 0.6  # 假设60%
    broken_rate = 0.2   # 假设20%

    sentiment, advice = MarketSentiment.get_sentiment(
        overview['limit_up_count'],
        overview['limit_down_count'],
        success_rate,
        broken_rate
    )

    can_trade = MarketSentiment.check_trade_conditions(
        overview['limit_up_count'],
        overview['limit_down_count'],
        broken_rate
    )

    position_limit = MarketSentiment.get_position_limit(sentiment)

    return {
        'date': overview['date'],
        'limit_up_count': overview['limit_up_count'],
        'limit_down_count': overview['limit_down_count'],
        'success_rate': success_rate,
        'broken_rate': broken_rate,
        'sentiment': sentiment,
        'advice': advice,
        'can_trade': can_trade,
        'position_limit': position_limit,
        'limit_up_list': overview['limit_up_list']
    }


def check_yesterday_success_rate(date: str = None) -> float:
    """计算昨日连板成功率

    Args:
        date: 日期

    Returns:
        连板成功率 (0-1)
    """
    # 这里需要实际实现，计算昨日连板股今日的表现
    # 简化实现，返回默认值
    return 0.6


def check_yesterday_broken_rate(date: str = None) -> float:
    """计算昨日炸板率

    Args:
        date: 日期

    Returns:
        炸板率 (0-1)
    """
    # 这里需要实际实现，计算昨日涨停股今日的表现
    # 简化实现，返回默认值
    return 0.2
