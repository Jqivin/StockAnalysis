"""测试邮件发送功能"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from signals.email_notifier import EmailNotifier
from datetime import datetime

print("=" * 70)
print("邮件发送功能测试")
print("=" * 70)

# 创建邮件发送器
notifier = EmailNotifier()

print("\n【当前邮件配置】")
print(f"  SMTP服务器: {notifier.config.get('smtp_server', '未配置')}")
print(f"  SMTP端口: {notifier.config.get('smtp_port', '未配置')}")
print(f"  发件人: {notifier.config.get('sender_email', '未配置')}")
print(f"  密码: {'已配置' if notifier.config.get('sender_password') else '未配置'}")
print(f"  收件人: {notifier.config.get('receiver_emails', '未配置')}")

print("\n【测试1：发送买入信号】")
buy_stock = {
    'code': '000001',
    'name': '平安银行',
    'price': 10.50,
    'change': 0.03,
    'volume': 1000000
}
buy_reason = """
- 市场情绪：强势（涨停80家，跌停5家）
- 板块热点：金融板块涨幅3.5%
- 技术信号：MACD金叉，RSI超卖反弹
- 竞价表现：开盘涨幅4.2%，放量上涨
"""

result = notifier.send_buy_signal(buy_stock, buy_reason)
print(f"  结果: {'✅ 成功' if result else '❌ 失败'}")

print("\n【测试2：发送卖出信号】")
sell_stock = {
    'code': '000001',
    'name': '平安银行',
    'price': 11.50,
    'change': 0.05,
    'volume': 1500000
}
sell_reason = """
- 止盈触发：盈利达到8.5%
- 持有天数：3天
- 卖出策略：5-10%止盈区间
"""

result = notifier.send_sell_signal(sell_stock, sell_reason)
print(f"  结果: {'✅ 成功' if result else '❌ 失败'}")

print("\n【测试3：发送每日报告】")
daily_report = {
    'date': datetime.now().strftime("%Y-%m-%d"),
    'limit_up_count': 85,
    'limit_down_count': 3,
    'success_rate': 0.72,
    'broken_rate': 0.18,
    'sentiment': 'strong',
    'advice': '积极出击',
    'sectors': [
        {
            'sector_name': 'AI人工智能',
            'change': 0.055,
            'limit_up_count': 12,
            'logic': '政策利好，科技股领涨',
            'leader': {
                'name': '科大讯飞',
                'code': '002230'
            }
        },
        {
            'sector_name': '新能源汽车',
            'change': 0.038,
            'limit_up_count': 8,
            'logic': '销量超预期，产业链景气',
            'leader': {
                'name': '比亚迪',
                'code': '002594'
            }
        }
    ],
    'auction_results': [
        {
            'name': '科大讯飞',
            'code': '002230',
            'auction_change': 0.045,
            'auction_amount': 85000000,
            'auction_turnover': 0.032,
            'yesterday_performance': '首板',
            'priority': '板块龙头',
            'rating': '强势'
        },
        {
            'name': '比亚迪',
            'code': '002594',
            'auction_change': 0.032,
            'auction_amount': 120000000,
            'auction_turnover': 0.025,
            'yesterday_performance': '2连板',
            'priority': '连板龙头',
            'rating': '强势'
        }
    ],
    'opening_strategy': '''
1. 科科讯飞 - 预期分歧低吸（竞价4.5%，可关注回踩机会）
2. 比亚迪 - 预期弱转强打板（竞价3.2%，开盘后观察量能）
3. 中科曙光 - 观察回踩均线（均线多头排列，支撑强劲）
    ''',
    'risk_warnings': [
        '高位连板风险：部分连板股已超5板，注意退潮',
        '板块分化风险：热点板块内部分化加剧',
        '量能不足风险：今日整体成交量有所萎缩'
    ]
}

result = notifier.send_daily_report(daily_report)
print(f"  结果: {'✅ 成功' if result else '❌ 失败'}")

print("\n" + "=" * 70)
print("测试完成!")
print("=" * 70)

print("\n【配置说明】")
print("-" * 70)
print("如需配置邮箱，请按照以下步骤：")
print()
print("1. 获取邮箱授权码:")
print("   QQ邮箱:")
print("   - 登录QQ邮箱 → 设置 → 账户 → POP3/IMAP/SMTP服务")
print("   - 开启服务，生成授权码（不是QQ密码）")
print()
print("   163邮箱:")
print("   - 登录163邮箱 → 设置 → POP3/SMTP/IMAP")
print("   - 开启服务，获取授权码")
print()
print("   Gmail:")
print("   - 需要开启两步验证")
print("   - 生成应用专用密码")
print()
print("2. 创建配置文件:")
print("   复制示例文件：cp config/email_config.example.json config/email_config.json")
print()
print("3. 编辑配置文件，填入你的信息:")
print("   {")
print('     "smtp_server": "smtp.qq.com",')
print('     "smtp_port": 587,')
print('     "sender_email": "your_email@qq.com",')
print('     "sender_password": "your_authorization_code",')
print('     "receiver_emails": ["receiver@example.com"]')
print("   }")
print()
print("4. 常用SMTP服务器:")
print("   QQ邮箱: smtp.qq.com:587")
print("   163邮箱: smtp.163.com:465")
print("   Gmail: smtp.gmail.com:587")
print("   126邮箱: smtp.126.com:465")
print()
print("=" * 70)
