"""邮件推送模块"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime
import json
import os


class EmailNotifier:
    """邮件推送类"""

    def __init__(self, config_file: str = "config/email_config.json"):
        """初始化邮件推送器

        Args:
            config_file: 配置文件路径
        """
        self.config = self._load_config(config_file)

    def _load_config(self, config_file: str) -> Dict:
        """加载邮件配置

        Args:
            config_file: 配置文件路径

        Returns:
            配置字典
        """
        default_config = {
            "smtp_server": "smtp.qq.com",
            "smtp_port": 587,
            "sender_email": "",
            "sender_password": "",
            "receiver_emails": []
        }

        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"警告：无法加载邮件配置，使用默认配置: {e}")

        return default_config

    def _send_email(self, subject: str, content: str, html: bool = False) -> bool:
        """发送邮件

        Args:
            subject: 邮件主题
            content: 邮件内容
            html: 是否为HTML格式

        Returns:
            是否发送成功
        """
        if not self.config['sender_email'] or not self.config['sender_password']:
            print("警告：邮件配置不完整，无法发送邮件")
            return False

        if not self.config['receiver_emails']:
            print("警告：没有配置收件人，无法发送邮件")
            return False

        try:
            # 创建邮件
            if html:
                msg = MIMEMultipart('alternative')
                msg.attach(MIMEText(content, 'plain', 'utf-8'))
                msg.attach(MIMEText(content, 'html', 'utf-8'))
            else:
                msg = MIMEText(content, 'plain', 'utf-8')

            msg['Subject'] = subject
            msg['From'] = self.config['sender_email']
            msg['To'] = ', '.join(self.config['receiver_emails'])

            # 发送邮件
            # 根据端口选择连接方式：465用SSL，587用STARTTLS
            if self.config['smtp_port'] == 465:
                # 163/126邮箱使用SSL
                with smtplib.SMTP_SSL(self.config['smtp_server'], self.config['smtp_port']) as server:
                    server.login(self.config['sender_email'], self.config['sender_password'])
                    server.send_message(msg)
            else:
                # QQ/Gmail等使用STARTTLS
                with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                    server.starttls()
                    server.login(self.config['sender_email'], self.config['sender_password'])
                    server.send_message(msg)

            print(f"邮件发送成功: {subject}")
            return True

        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False

    def send_buy_signal(self, stock_info: Dict, reason: str) -> bool:
        """发送买入信号

        Args:
            stock_info: 股票信息
            reason: 买入理由

        Returns:
            是否发送成功
        """
        subject = f"【买入信号】{stock_info.get('name', '')} ({stock_info.get('code', '')})"

        content = f"""
A股短线交易系统 - 买入信号

{'='*50}

股票信息：
- 股票代码：{stock_info.get('code', '')}
- 股票名称：{stock_info.get('name', '')}
- 当前价格：¥{stock_info.get('price', 0):.2f}
- 涨跌幅：{stock_info.get('change', 0)*100:.2f}%
- 成交量：{stock_info.get('volume', 0):,}

买入理由：
{reason}

{'='*50}

风险提示：
- 本信号仅供参考，不构成投资建议
- 请根据实际情况自主决策
- 严格执行止损纪律

发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return self._send_email(subject, content)

    def send_sell_signal(self, stock_info: Dict, reason: str) -> bool:
        """发送卖出信号

        Args:
            stock_info: 股票信息
            reason: 卖出理由

        Returns:
            是否发送成功
        """
        subject = f"【卖出信号】{stock_info.get('name', '')} ({stock_info.get('code', '')})"

        content = f"""
A股短线交易系统 - 卖出信号

{'='*50}

股票信息：
- 股票代码：{stock_info.get('code', '')}
- 股票名称：{stock_info.get('name', '')}
- 当前价格：¥{stock_info.get('price', 0):.2f}
- 涨跌幅：{stock_info.get('change', 0)*100:.2f}%
- 成交量：{stock_info.get('volume', 0):,}

卖出理由：
{reason}

{'='*50}

风险提示：
- 本信号仅供参考，不构成投资建议
- 请根据实际情况自主决策
- 严格执行止损纪律

发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return self._send_email(subject, content)

    def send_daily_report(self, report: Dict) -> bool:
        """发送每日策略报告

        Args:
            report: 每日报告字典

        Returns:
            是否发送成功
        """
        subject = f"【每日策略报告】{report.get('date', datetime.now().strftime('%Y-%m-%d'))}"

        # 构建报告内容
        content = f"""
A股短线交易系统 - 每日策略报告
{'='*50}

一、市场环境

昨日数据：
- 涨停家数：{report.get('limit_up_count', 0)}家
- 跌停家数：{report.get('limit_down_count', 0)}家
- 连板成功率：{report.get('success_rate', 0)*100:.1f}%
- 炸板率：{report.get('broken_rate', 0)*100:.1f}%

今日情绪：【{report.get('sentiment', '未知')}】
操作建议：【{report.get('advice', '观望')}】

二、主线板块
"""

        # 添加板块信息
        sectors = report.get('sectors', [])
        for i, sector in enumerate(sectors[:3], 1):
            leader = sector.get('leader', {})
            content += f"""
{i}. {sector.get('sector_name', '')} (+{sector.get('change', 0)*100:.2f}%)
   - 涨停：{sector.get('limit_up_count', 0)}家
   - 龙头：{leader.get('name', 'N/A')} ({leader.get('code', 'N/A')})
   - 逻辑：{sector.get('logic', 'N/A')}
"""

        content += f"""
三、竞价结果

"""

        # 添加竞价结果
        auction_results = report.get('auction_results', [])
        for i, stock in enumerate(auction_results[:5], 1):
            content += f"""
【{i}】{stock.get('name', '')}（{stock.get('code', '')}）
- 竞价涨幅：+{stock.get('auction_change', 0)*100:.2f}%
- 竞价成交额：{stock.get('auction_amount', 0)/10000:.0f}万
- 竞价换手率：{stock.get('auction_turnover', 0)*100:.2f}%
- 昨日表现：{stock.get('yesterday_performance', 'N/A')}
- 优先级：{stock.get('priority', 'N/A')}
- 评级：【{stock.get('rating', 'N/A')}】
"""

        content += f"""
四、开盘策略

重点观察标的：
{report.get('opening_strategy', 'N/A')}

五、风险提示

今日风险点：
{report.get('risk_warnings', 'N/A')}

{'='*50}

免责声明：
- 本报告仅供参考，不构成投资建议
- 股市有风险，投资需谨慎
- 请根据自身情况理性决策

报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return self._send_email(subject, content)


def notify_buy_signal(stock_info: Dict, reason: str, config_file: str = "config/email_config.json") -> bool:
    """发送买入信号（便捷函数）

    Args:
        stock_info: 股票信息
        reason: 买入理由
        config_file: 配置文件路径

    Returns:
        是否发送成功
    """
    notifier = EmailNotifier(config_file)
    return notifier.send_buy_signal(stock_info, reason)


def notify_sell_signal(stock_info: Dict, reason: str, config_file: str = "config/email_config.json") -> bool:
    """发送卖出信号（便捷函数）

    Args:
        stock_info: 股票信息
        reason: 卖出理由
        config_file: 配置文件路径

    Returns:
        是否发送成功
    """
    notifier = EmailNotifier(config_file)
    return notifier.send_sell_signal(stock_info, reason)


def send_daily_report(report: Dict, config_file: str = "config/email_config.json") -> bool:
    """发送每日报告（便捷函数）

    Args:
        report: 每日报告字典
        config_file: 配置文件路径

    Returns:
        是否发送成功
    """
    notifier = EmailNotifier(config_file)
    return notifier.send_daily_report(report)
