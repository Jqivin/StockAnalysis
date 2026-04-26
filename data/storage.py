"""数据存储模块"""
import pandas as pd
import sqlite3
from pathlib import Path
from typing import Optional


class DataStorage:
    """数据存储类，支持SQLite和CSV"""

    def __init__(self, db_path: str = "data/stock_data.db", csv_dir: str = "data/csv"):
        self.db_path = db_path
        self.csv_dir = Path(csv_dir)
        self.csv_dir.mkdir(parents=True, exist_ok=True)

    def save_to_sqlite(self, df: pd.DataFrame, table_name: str, if_exists: str = "replace"):
        """保存数据到SQLite

        Args:
            df: 要保存的DataFrame
            table_name: 表名
            if_exists: 如果表已存在的行为 ('fail', 'replace', 'append')
        """
        conn = sqlite3.connect(self.db_path)
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)
        conn.close()

    def load_from_sqlite(self, table_name: str, sql: Optional[str] = None) -> pd.DataFrame:
        """从SQLite加载数据

        Args:
            table_name: 表名
            sql: 自定义SQL查询

        Returns:
            DataFrame
        """
        conn = sqlite3.connect(self.db_path)
        if sql:
            df = pd.read_sql(sql, conn)
        else:
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df

    def save_to_csv(self, df: pd.DataFrame, filename: str):
        """保存数据到CSV"""
        filepath = self.csv_dir / filename
        df.to_csv(filepath, index=False, encoding="utf-8-sig")

    def load_from_csv(self, filename: str) -> pd.DataFrame:
        """从CSV加载数据"""
        filepath = self.csv_dir / filename
        return pd.read_csv(filepath, encoding="utf-8-sig")

    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
