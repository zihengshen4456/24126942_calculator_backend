"""SQLite 数据库连接与建表逻辑。"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# src/model/database.py -> src/model -> src -> 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "calculator.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS calculation_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    expression  TEXT    NOT NULL,
    result      TEXT    NOT NULL,
    created_at  TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_history_created_at
    ON calculation_history (created_at DESC);
"""


def get_database_path() -> Path:
    """返回数据库文件路径，允许通过环境变量覆盖。"""
    configured = os.environ.get("CALCULATOR_DB_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    """创建一个新的数据库连接（每个请求独立连接，避免线程问题）。"""
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def connection_scope():
    """连接上下文管理器：正常结束时提交事务，无论如何都关闭连接。"""
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_database() -> None:
    """初始化数据库结构（幂等，可重复调用）。"""
    with connection_scope() as connection:
        connection.executescript(SCHEMA)
