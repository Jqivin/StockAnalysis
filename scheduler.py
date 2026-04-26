"""定时执行调度器"""
import schedule
import time
from typing import Callable, Optional
from datetime import datetime, timedelta
from threading import Thread
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Scheduler:
    """定时调度器类"""

    def __init__(self):
        """初始化调度器"""
        self.running = False
        self.scheduler_thread = None

    def schedule_auction_monitor(self, callback: Callable, run_time: str = "09:15"):
        """竞价监控定时任务

        Args:
            callback: 回调函数
            run_time: 运行时间 (HH:MM格式)
        """
        schedule.every().day.at(run_time).do(self._run_task, callback, "竞价监控")

    def schedule_opening_monitor(self, callback: Callable, run_time: str = "09:30"):
        """开盘监控定时任务

        Args:
            callback: 回调函数
            run_time: 运行时间 (HH:MM格式)
        """
        schedule.every().day.at(run_time).do(self._run_task, callback, "开盘监控")

    def schedule_position_check(self, callback: Callable, run_time: str = "10:00"):
        """持仓检查定时任务

        Args:
            callback: 回调函数
            run_time: 运行时间 (HH:MM格式)
        """
        schedule.every().day.at(run_time).do(self._run_task, callback, "持仓检查")

    def schedule_daily_report(self, callback: Callable, run_time: str = "08:30"):
        """每日报告定时任务

        Args:
            callback: 回调函数
            run_time: 运行时间 (HH:MM格式)
        """
        schedule.every().day.at(run_time).do(self._run_task, callback, "每日报告")

    def schedule_interval(self, callback: Callable, interval_minutes: int, task_name: str):
        """间隔定时任务

        Args:
            callback: 回调函数
            interval_minutes: 间隔分钟数
            task_name: 任务名称
        """
        schedule.every(interval_minutes).minutes.do(self._run_task, callback, task_name)

    def _run_task(self, callback: Callable, task_name: str):
        """运行任务

        Args:
            callback: 回调函数
            task_name: 任务名称
        """
        logger.info(f"开始执行任务: {task_name}")
        try:
            callback()
            logger.info(f"任务执行完成: {task_name}")
        except Exception as e:
            logger.error(f"任务执行失败 {task_name}: {e}")

    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行")
            return

        self.running = True
        logger.info("调度器启动")

        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(1)

        self.scheduler_thread = Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def stop(self):
        """停止调度器"""
        if not self.running:
            return

        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)

        schedule.clear()
        logger.info("调度器已停止")

    def get_next_run_time(self) -> Optional[datetime]:
        """获取下次运行时间

        Returns:
            下次运行时间
        """
        if not schedule.jobs:
            return None

        next_run = min(job.next_run for job in schedule.jobs)
        return next_run


# 全局调度器实例
_global_scheduler = None


def get_scheduler() -> Scheduler:
    """获取全局调度器实例"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = Scheduler()
    return _global_scheduler


def start_scheduler():
    """启动全局调度器"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """停止全局调度器"""
    scheduler = get_scheduler()
    scheduler.stop()


def schedule_task(callback: Callable, run_time: str, task_name: str):
    """调度一个任务

    Args:
        callback: 回调函数
        run_time: 运行时间 (HH:MM格式)
        task_name: 任务名称
    """
    scheduler = get_scheduler()
    scheduler.schedule_daily_report(callback, run_time)
