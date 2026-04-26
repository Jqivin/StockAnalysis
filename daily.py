"""每日策略主程序 - 整合所有模块的完整流程"""
import sys
import io
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd

# 设置输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from data.akshare_client import DataClient
from strategy.sentiment import get_market_sentiment
from strategy.sector import get_sector_analysis
from strategy.leader import analyze_stocks_priority
from strategy.filter import filter_stocks_by_auction
from realtime.tick_monitor import OpeningMonitor
from signals.email_notifier import send_daily_report
from scheduler import get_scheduler, start_scheduler, stop_scheduler


class DailyStrategy:
    """每日策略类 - 完整的短线交易流程"""

    def __init__(self):
        """初始化每日策略"""
        self.client = DataClient(source="akshare")
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.market_sentiment = None
        self.hot_sectors = []
        self.candidates = []
        self.opening_monitor = None

    def run_daily_preparation(self):
        """每日准备工作 (8:30-9:00)"""
        print(f"\n{'='*60}")
        print(f"每日准备工作 - {self.today}")
        print(f"{'='*60}")

        print("\n【1/4】检查市场情绪...")
        self.market_sentiment = get_market_sentiment()

        print(f"涨停家数: {self.market_sentiment['limit_up_count']}")
        print(f"跌停家数: {self.market_sentiment['limit_down_count']}")
        print(f"情绪等级: {self.market_sentiment['sentiment']}")
        print(f"操作建议: {self.market_sentiment['advice']}")

        if not self.market_sentiment['can_trade']:
            print("\n⚠️  市场环境不满足交易条件，建议空仓")
            return False

        print("\n【2/4】筛选主线板块...")
        self.hot_sectors = get_sector_analysis(date=self.today, top_n=3)

        if not self.hot_sectors:
            print("未找到符合条件的热门板块")
            return False

        print(f"找到 {len(self.hot_sectors)} 个热门板块:")
        for i, sector in enumerate(self.hot_sectors, 1):
            print(f"{i}. {sector['sector_name']} (+{sector['change']*100:.2f}%) - 涨停{sector['limit_up_count']}家")

        print("\n【3/4】准备备选股票池...")
        # 收集热门板块内的股票
        sector_stock_codes = []
        for sector in self.hot_sectors:
            sector_stocks = self.client.get_sector_data()
            if not sector_stocks.empty:
                # 这里需要实际实现获取板块内股票的逻辑
                pass

        # 使用涨停板股票作为备选
        limit_up_list = self.market_sentiment['limit_up_list']
        if not limit_up_list.empty:
            sector_stock_codes = limit_up_list['代码'].tolist()[:50]  # 取前50只

        print(f"备选股票池: {len(sector_stock_codes)}只")

        print("\n【4/4】准备就绪，等待竞价...")
        return True

    def run_auction_analysis(self):
        """竞价分析 (9:15-9:25)"""
        print(f"\n{'='*60}")
        print(f"竞价分析 - {self.today} 09:15-09:25")
        print(f"{'='*60}")

        print("\n【1/3】收集竞价数据...")
        # 实际需要真实的竞价数据接口
        # 这里使用市场数据模拟

        print("\n【2/3】量化筛选股票...")
        # 使用筛选器过滤股票
        self.candidates = filter_stocks_by_auction(sector_stock_codes if 'sector_stock_codes' in locals() else self._get_stock_list()[:50])

        if not self.candidates:
            print("未通过筛选的股票")
            return False

        print(f"筛选出 {len(self.candidates)} 只候选股票:")
        for i, candidate in enumerate(self.candidates, 1):
            print(f"{i}. {candidate['name']} ({candidate['code']}) - 竞价+{candidate['auction_change']*100:.2f}%")

        print("\n【3/3】确定优先级排序...")
        # 按优先级排序（已在筛选器中完成）
        print("候选股票已按优先级排序完成")
        return True

    def run_opening_monitoring(self):
        """开盘监控 (9:30-9:35)"""
        print(f"\n{'='*60}")
        print(f"开盘监控 - {self.today} 09:30-09:35")
        print(f"{'='*60}")

        if not self.candidates:
            print("没有需要监控的股票")
            return

        # 创建监控器
        self.opening_monitor = OpeningMonitor()

        # 添加监控股票
        for candidate in self.candidates:
            self.opening_monitor.add_stock_to_monitor(
                candidate['code'],
                candidate['auction_price']
            )

        print(f"开始监控 {len(self.candidates)} 只股票...")

        # 运行监控（实际需要实时tick数据，这里用模拟数据）
        print("\n监控中...")
        results = self.opening_monitor.monitor_opening(duration=300)

        # 输出结果
        print("\n【监控结果】")
        summary = self.opening_monitor.get_opening_summary()

        print(f"总计监控: {summary['monitored_count']}只")
        print(f"强势: {len(summary['strong_stocks'])}只")
        print(f"分歧: {len(summary['divergent_stocks'])}只")
        print(f"弱势: {len(summary['weak_stocks'])}只")

        if summary['strong_stocks']:
            print("\n强势股票（可考虑打板）:")
            for stock in summary['strong_stocks']:
                print(f"  - {stock['code']} {stock['name']}")

        if summary['divergent_stocks']:
            print("\n分歧股票（最佳买点）:")
            for stock in summary['divergent_stocks']:
                print(f"  - {stock['code']} {stock['name']}")

        if summary['weak_stocks']:
            print("\n弱势股票（放弃）:")
            for stock in summary['weak_stocks']:
                print(f"  - {stock['code']} {stock['name']}")

        return results

    def generate_daily_report(self) -> Dict:
        """生成每日策略报告"""
        print(f"\n{'='*60}")
        print(f"生成每日策略报告")
        print(f"{'='*60}")

        # 构建报告
        report = {
            'date': self.today,
            'limit_up_count': self.market_sentiment['limit_up_count'],
            'limit_down_count': self.market_sentiment['limit_down_count'],
            'success_rate': self.market_sentiment['success_rate'],
            'broken_rate': self.market_sentiment['broken_rate'],
            'sentiment': self.market_sentiment['sentiment'],
            'advice': self.market_sentiment['advice'],
            'sectors': [],
            'auction_results': [],
            'opening_strategy': '',
            'risk_warnings': []
        }

        # 添加板块信息
        for sector in self.hot_sectors:
            report['sectors'].append({
                'sector_name': sector['sector_name'],
                'change': sector['change'],
                'limit_up_count': sector['limit_up_count'],
                'logic': '热门板块'
            })

        # 添加竞价结果
        for candidate in self.candidates:
            report['auction_results'].append({
                'name': candidate['name'],
                'code': candidate['code'],
                'auction_change': candidate['auction_change'],
                'auction_amount': candidate['auction_amount'],
                'auction_turnover': candidate['auction_turnover'],
                'yesterday_performance': '正常',
                'priority': candidate.get('leader_type', '普通'),
                'rating': '待确认'
            })

        # 添加开盘策略
        if self.opening_monitor:
            summary = self.opening_monitor.get_opening_summary()

            strategies = []
            if summary['strong_stocks']:
                for stock in summary['strong_stocks']:
                    strategies.append(f"{stock['name']} - 预期弱转强打板")

            if summary['divergent_stocks']:
                for stock in summary['divergent_stocks']:
                    strategies.append(f"{stock['name']} - 预期分歧低吸")

            report['opening_strategy'] = '\n'.join(strategies) if strategies else '无明确标的'

        # 添加风险提示
        if self.market_sentiment['sentiment'] == 'downtrend':
            report['risk_warnings'].append('市场情绪较差，风险较高')
        if self.market_sentiment['limit_down_count'] > 10:
            report['risk_warnings'].append('跌停家数较多，注意风险')

        return report

    def run(self):
        """运行完整流程"""
        try:
            # 8:30-9:00 每日准备
            if not self.run_daily_preparation():
                return

            # 9:15-9:25 竞价分析
            if not self.run_auction_analysis():
                return

            # 9:30-9:35 开盘监控
            self.run_opening_monitoring()

            # 生成报告
            report = self.generate_daily_report()

            # 发送邮件报告（如果配置了邮件）
            print("\n是否发送邮件报告？(y/n): ", end="")
            # 实际使用时可以自动发送
            # send_daily_report(report)

            print("\n今日策略流程执行完成！")

        except Exception as e:
            print(f"\n执行出错: {e}")
            import traceback
            traceback.print_exc()


def _get_stock_list(self) -> List[str]:
    """获取股票列表（辅助方法）"""
    return []


# 全局实例
_daily_strategy = None


def get_daily_strategy() -> DailyStrategy:
    """获取全局每日策略实例"""
    global _daily_strategy
    if _daily_strategy is None:
        _daily_strategy = DailyStrategy()
    return _daily_strategy


def run_daily_strategy():
    """运行每日策略（便捷函数）"""
    strategy = get_daily_strategy()
    strategy.run()


# 测试用
if __name__ == '__main__':
    print("A股短线交易系统 - 每日策略")
    print("=" * 60)
    print("\n这是一个演示版本，使用模拟数据")
    print("实际使用时需要：")
    print("1. 配置邮件推送 (config/email_config.json)")
    print("2. 在交易日运行程序")
    print("3. 确保网络连接正常")

    print("\n示例使用：")
    print("-" * 60)
    print("# 方式1: 手动运行")
    print("python daily.py")
    print("\n# 方式2: 定时自动运行")
    print("from scheduler import start_scheduler, get_scheduler")
    print("scheduler = get_scheduler()")
    print("scheduler.schedule_daily_report(run_daily_strategy, '08:30')")
    print("scheduler.start()")
    print("\n" + "=" * 60)
