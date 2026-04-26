"""A股量化分析工具主入口"""
import argparse
import sys
import io
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib

# 设置输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
matplotlib.use('Agg')

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from data.akshare_client import AkShareClient
from analysis.technical import add_indicators
from analysis.fundamental import get_stock_fundamental_summary
from backtest.engine import backtest
from backtest.metrics import print_backtest_report


def cmd_get_quotes(args):
    """获取股票行情"""
    client = AkShareClient()

    # 获取股票名称
    name = client.get_stock_name(args.code)
    print(f"\n股票代码: {args.code} - {name}")
    print("-" * 60)

    # 获取历史数据
    df = client.get_stock_history(args.code, args.start, args.end)

    if df.empty:
        print("未获取到数据")
        return

    # 添加技术指标
    df = add_indicators(df)

    # 显示最新数据
    latest = df.iloc[-1]
    print(f"日期: {latest['日期'].strftime('%Y-%m-%d')}")
    print(f"收盘价: ¥{latest['收盘']:.2f}")
    print(f"涨跌幅: {((latest['收盘'] - latest['开盘']) / latest['开盘'] * 100):.2f}%")
    print(f"成交量: {latest['成交量']:,}")
    print("-" * 60)
    print(f"MA5: {latest.get('MA5', 0):.2f}")
    print(f"MA10: {latest.get('MA10', 0):.2f}")
    print(f"MA20: {latest.get('MA20', 0):.2f}")
    print(f"RSI: {latest.get('RSI', 0):.2f}")

    # 保存数据
    if args.save:
        filename = f"{args.code}_{args.start or 'start'}_{args.end or 'end'}.csv"
        df.to_csv(f"data/csv/{filename}", index=False, encoding='utf-8-sig')
        print(f"\n数据已保存到: data/csv/{filename}")


def cmd_chart(args):
    """生成K线图表"""
    client = AkShareClient()
    df = client.get_stock_history(args.code, args.start, args.end)

    if df.empty:
        print("未获取到数据")
        return

    df = add_indicators(df)

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle(f"{args.code} - {client.get_stock_name(args.code)}", fontsize=14)

    # K线图
    ax1 = axes[0]
    ax1.plot(df['日期'], df['收盘'], label='收盘价', linewidth=1)
    ax1.plot(df['日期'], df['MA5'], label='MA5', alpha=0.7)
    ax1.plot(df['日期'], df['MA10'], label='MA10', alpha=0.7)
    ax1.plot(df['日期'], df['MA20'], label='MA20', alpha=0.7)
    ax1.fill_between(df['日期'], df['lower'], df['upper'], alpha=0.2, label='布林带')
    ax1.set_ylabel('价格')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # MACD
    ax2 = axes[1]
    ax2.plot(df['日期'], df['DIF'], label='DIF', linewidth=1)
    ax2.plot(df['日期'], df['DEA'], label='DEA', linewidth=1)
    ax2.bar(df['日期'], df['MACD'], label='MACD', alpha=0.5)
    ax2.set_ylabel('MACD')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # RSI
    ax3 = axes[2]
    ax3.plot(df['日期'], df['RSI'], label='RSI', linewidth=1, color='purple')
    ax3.axhline(y=70, color='r', linestyle='--', alpha=0.5)
    ax3.axhline(y=30, color='g', linestyle='--', alpha=0.5)
    ax3.set_ylabel('RSI')
    ax3.set_ylim(0, 100)
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()

    filename = f"charts/{args.code}_chart.png"
    Path('charts').mkdir(exist_ok=True)
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"图表已保存到: {filename}")


def cmd_backtest(args):
    """运行回测"""
    client = AkShareClient()
    df = client.get_stock_history(args.code, args.start, args.end)

    if df.empty:
        print("未获取到数据")
        return

    print(f"\n开始回测 {args.code} - {client.get_stock_name(args.code)}")
    print(f"策略: {args.strategy}")
    print(f"初始资金: ¥{args.capital:,.2f}")
    print("-" * 60)

    # 解析策略参数
    params = {}
    if args.strategy == 'ma':
        params = {'short_period': args.short, 'long_period': args.long}
    elif args.strategy == 'rsi':
        params = {'oversold': args.oversold, 'overbought': args.overbought}

    # 运行回测
    result = backtest(df, args.strategy, args.capital, **params)

    # 打印报告
    print_backtest_report(result)

    # 保存结果
    if args.save:
        Path('backtest_results').mkdir(exist_ok=True)
        result['equity_curve'].to_csv(f"backtest_results/{args.code}_{args.strategy}_equity.csv", index=False)
        result['trades'].to_csv(f"backtest_results/{args.code}_{args.strategy}_trades.csv", index=False)
        print(f"\n回测结果已保存到: backtest_results/")


def cmd_fundamental(args):
    """基本面分析"""
    print(f"\n基本面分析 - {args.code}")
    print("-" * 60)

    summary = get_stock_fundamental_summary(args.code)

    print(f"市盈率(PE): {summary.get('pe_ratio', 0):.2f}")
    print(f"市净率(PB): {summary.get('pb_ratio', 0):.2f}")
    print(f"市值: {summary.get('market_cap', 0):,.0f} 万元")
    print("-" * 60)
    print(f"营业收入: {summary.get('revenue', 0):,.2f} 万元")
    print(f"净利润: {summary.get('net_profit', 0):,.2f} 万元")
    print(f"毛利率: {summary.get('gross_profit_margin', 0):.2f}%")
    print(f"净利率: {summary.get('net_profit_margin', 0):.2f}%")
    print("-" * 60)
    print(f"总资产: {summary.get('total_assets', 0):,.2f} 万元")
    print(f"总负债: {summary.get('total_liabilities', 0):,.2f} 万元")
    print(f"股东权益: {summary.get('total_equity', 0):,.2f} 万元")
    print(f"资产负债率: {summary.get('debt_ratio', 0):.2f}%")
    print(f"净资产收益率(ROE): {summary.get('roe', 0):.2f}%")


def cmd_list(args):
    """列出股票列表"""
    client = AkShareClient()
    df = client.get_stock_list()

    print(f"\nA股列表 (共{len(df)}只)")
    print("-" * 60)
    print(df.head(20).to_string(index=False))

    if len(df) > 20:
        print(f"\n... 还有 {len(df) - 20} 只股票")


def main():
    parser = argparse.ArgumentParser(description='A股量化分析工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 获取行情
    parser_quotes = subparsers.add_parser('quotes', help='获取股票行情')
    parser_quotes.add_argument('--code', required=True, help='股票代码')
    parser_quotes.add_argument('--start', help='开始日期 (YYYYMMDD)')
    parser_quotes.add_argument('--end', help='结束日期 (YYYYMMDD)')
    parser_quotes.add_argument('--save', action='store_true', help='保存数据')

    # 生成图表
    parser_chart = subparsers.add_parser('chart', help='生成K线图表')
    parser_chart.add_argument('--code', required=True, help='股票代码')
    parser_chart.add_argument('--start', help='开始日期 (YYYYMMDD)')
    parser_chart.add_argument('--end', help='结束日期 (YYYYMMDD)')

    # 回测
    parser_backtest = subparsers.add_parser('backtest', help='运行回测')
    parser_backtest.add_argument('--code', required=True, help='股票代码')
    parser_backtest.add_argument('--strategy', default='ma', choices=['ma', 'macd', 'rsi', 'bollinger'], help='策略类型')
    parser_backtest.add_argument('--capital', type=float, default=100000, help='初始资金')
    parser_backtest.add_argument('--start', help='开始日期 (YYYYMMDD)')
    parser_backtest.add_argument('--end', help='结束日期 (YYYYMMDD)')
    parser_backtest.add_argument('--save', action='store_true', help='保存结果')
    parser_backtest.add_argument('--short', type=int, default=5, help='短期均线周期')
    parser_backtest.add_argument('--long', type=int, default=20, help='长期均线周期')
    parser_backtest.add_argument('--oversold', type=int, default=30, help='RSI超卖阈值')
    parser_backtest.add_argument('--overbought', type=int, default=70, help='RSI超买阈值')

    # 基本面分析
    parser_fundamental = subparsers.add_parser('fundamental', help='基本面分析')
    parser_fundamental.add_argument('--code', required=True, help='股票代码')

    # 列出股票
    parser_list = subparsers.add_parser('list', help='列出股票列表')

    args = parser.parse_args()

    if args.command == 'quotes':
        cmd_get_quotes(args)
    elif args.command == 'chart':
        cmd_chart(args)
    elif args.command == 'backtest':
        cmd_backtest(args)
    elif args.command == 'fundamental':
        cmd_fundamental(args)
    elif args.command == 'list':
        cmd_list(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
