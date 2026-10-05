"""Data access layer for calculation history: every SQL statement lives here."""

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
    """Insert one history row and return it including the generated id."""
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
    """Return history rows, newest first, optionally filtered by keyword."""
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
    """Count history rows, optionally filtered by keyword."""
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
    """Delete one row; return whether a row was actually removed."""
    with connection_scope() as connection:
        cursor = connection.execute(
            "DELETE FROM calculation_history WHERE id = ?", (record_id,)
        )
        return cursor.rowcount > 0


def delete_all() -> int:
    """Delete every row and return the number of deleted rows."""
    with connection_scope() as connection:
        cursor = connection.execute("DELETE FROM calculation_history")
        return cursor.rowcount
