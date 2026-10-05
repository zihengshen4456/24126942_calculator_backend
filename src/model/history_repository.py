"""计算历史的数据访问层：所有 SQL 都集中在这里。"""

from typing import Any, Dict, List, Optional

from model.database import connection_scope


def _row_to_dict(row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "expression": row["expression"],
        "result": row["result"],
        "createdAt": row["created_at"],
    }


def insert(expression: str, result: str, created_at: str) -> Dict[str, Any]:
    """插入一条计算历史，返回带自增主键的完整记录。"""
    with connection_scope() as connection:
        cursor = connection.execute(
            "INSERT INTO calculation_history (expression, result, created_at) "
            "VALUES (?, ?, ?)",
            (expression, result, created_at),
        )
        record_id = cursor.lastrowid
    return {
        "id": record_id,
        "expression": expression,
        "result": result,
        "createdAt": created_at,
    }


def find_all(keyword: Optional[str] = None) -> List[Dict[str, Any]]:
    """按关键字（表达式或结果）查询全部历史，按时间倒序。"""
    sql = "SELECT id, expression, result, created_at FROM calculation_history"
    params: List[Any] = []
    if keyword:
        sql += " WHERE expression LIKE ? OR result LIKE ?"
        like = f"%{keyword}%"
        params.extend([like, like])
    sql += " ORDER BY id DESC"
    with connection_scope() as connection:
        rows = connection.execute(sql, params).fetchall()
    return [_row_to_dict(row) for row in rows]


def count(keyword: Optional[str] = None) -> int:
    """统计历史记录条数。"""
    sql = "SELECT COUNT(*) AS total FROM calculation_history"
    params: List[Any] = []
    if keyword:
        sql += " WHERE expression LIKE ? OR result LIKE ?"
        like = f"%{keyword}%"
        params.extend([like, like])
    with connection_scope() as connection:
        row = connection.execute(sql, params).fetchone()
    return int(row["total"])


def delete_by_id(record_id: int) -> bool:
    """删除指定记录，返回是否真的删掉了一行。"""
    with connection_scope() as connection:
        cursor = connection.execute(
            "DELETE FROM calculation_history WHERE id = ?", (record_id,)
        )
        return cursor.rowcount > 0


def delete_all() -> int:
    """清空全部历史，返回删除条数。"""
    with connection_scope() as connection:
        cursor = connection.execute("DELETE FROM calculation_history")
        return cursor.rowcount
