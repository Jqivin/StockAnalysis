"""测试不同数据源"""
import sys
import io

# 设置输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from data.akshare_client import DataClient, AkShareClient, BaoStockClient

print("=" * 60)
print("测试不同数据源获取A股数据")
print("=" * 60)

# 测试1: BaoStock (免费开源)
print("\n【1】测试 BaoStock 数据源...")
try:
    client = BaoStockClient()
    name = client.get_stock_name("000001")
    print(f"股票名称: {name}")

    if name != "未知":
        df = client.get_stock_history("000001")
        if not df.empty:
            print(f"成功获取 {len(df)} 条历史数据")
            print("\n最新5条数据:")
            print(df[['日期', '开盘', '最高', '最低', '收盘', '成交量']].tail().to_string(index=False))
        else:
            print("未获取到历史数据")
    else:
        print("无法获取股票信息")
except Exception as e:
    print(f"BaoStock测试失败: {e}")

# 测试2: AkShare
print("\n" + "=" * 60)
print("【2】测试 AkShare 数据源...")
try:
    client = AkShareClient()
    name = client.get_stock_name("000001")
    print(f"股票名称: {name}")

    try:
        df = client.get_stock_history("000001")
        if not df.empty:
            print(f"成功获取 {len(df)} 条历史数据")
            print("\n最新5条数据:")
            print(df[['日期', '开盘', '最高', '最低', '收盘', '成交量']].tail().to_string(index=False))
        else:
            print("未获取到历史数据")
    except Exception as e:
        print(f"AkShare获取历史数据失败: {e}")

except Exception as e:
    print(f"AkShare测试失败: {e}")

# 测试3: 使用统一客户端切换数据源
print("\n" + "=" * 60)
print("【3】测试统一数据客户端...")
try:
    # 使用BaoStock
    print("\n使用 BaoStock:")
    client = DataClient(source="baostock")
    name = client.get_stock_name("000001")
    print(f"股票名称: {name}")

    df = client.get_stock_history("000001", start_date="20250101", end_date="20260425")
    if not df.empty:
        print(f"成功获取 {len(df)} 条历史数据 (2025-01-01 至今)")
        latest = df.iloc[-1]
        print(f"\n最新数据 ({latest['日期'].strftime('%Y-%m-%d')}):")
        print(f"  收盘价: {latest['收盘']:.2f}")
        print(f"  成交量: {int(latest['成交量']):,}")
    else:
        print("未获取到历史数据")

    # 切换到AkShare
    print("\n切换到 AkShare:")
    client.switch_source("akshare")
    name = client.get_stock_name("000001")
    print(f"股票名称: {name}")

    try:
        df = client.get_stock_history("000001", start_date="20250101", end_date="20260425")
        if not df.empty:
            print(f"成功获取 {len(df)} 条历史数据")
            latest = df.iloc[-1]
            print(f"\n最新数据 ({latest['日期'].strftime('%Y-%m-%d')}):")
            print(f"  收盘价: {latest['收盘']:.2f}")
            print(f"  成交量: {int(latest['成交量']):,}")
        else:
            print("未获取到历史数据")
    except Exception as e:
        print(f"AkShare获取失败: {e}")

except Exception as e:
    print(f"统一客户端测试失败: {e}")

print("\n" + "=" * 60)
print("数据源对比:")
print("=" * 60)
print("""
┌─────────────┬─────────┬─────────┬─────────┬──────────┐
│   数据源    │  免费   │ 注册   │ 实时   │  稳定性  │
├─────────────┼─────────┼─────────┼─────────┼──────────┤
│  BaoStock   │   ✓    │   无   │   ✗    │    ★★★   │
│  AkShare    │   ✓    │   无   │   ✓    │    ★★☆   │
│  Tushare    │ 部分 ✓ │  需要  │   ✓    │    ★★★★  │
└─────────────┴─────────┴─────────┴─────────┴──────────┘

推荐使用 BaoStock 获取历史数据，稳定性较好！
""")

print("使用示例:")
print("-" * 60)
print("""
# 使用BaoStock（推荐）
from data.akshare_client import DataClient
client = DataClient(source="baostock")
df = client.get_stock_history("000001")

# 使用AkShare
client = DataClient(source="akshare")
df = client.get_stock_history("000001")

# 使用Tushare（需要token）
client = DataClient(source="tushare", tushare_token="你的token")
df = client.get_stock_history("000001")
""")
