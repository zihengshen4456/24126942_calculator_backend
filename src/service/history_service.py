"""计算历史业务逻辑：新增、查询（支持搜索与分页）、删除。"""

from typing import Any, Dict, Optional

from model import history_repository
from utils.timeutil import current_timestamp
from utils.exceptions import NotFoundError, ValidationError

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100


def add_record(expression: str, result: Any) -> Dict[str, Any]:
    """计算成功后写入历史记录。"""
    return history_repository.insert(expression, _stringify(result), current_timestamp())


def _stringify(result: Any) -> str:
    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    return str(result)


def list_records(keyword: Optional[str], page: int, page_size: int) -> Dict[str, Any]:
    """分页 + 关键字查询历史记录。"""
    page = max(1, page)
    page_size = min(max(1, page_size), MAX_PAGE_SIZE)
    keyword = (keyword or "").strip() or None

    total = history_repository.count(keyword)
    records = history_repository.find_all(keyword)
    start = (page - 1) * page_size
    items = records[start:start + page_size]
    total_pages = (total + page_size - 1) // page_size if total else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": total_pages,
        "keyword": keyword or "",
    }


def delete_record(record_id: int) -> int:
    """删除单条记录，不存在时抛 404。"""
    if record_id <= 0:
        raise ValidationError("记录 ID 必须是正整数")
    if not history_repository.delete_by_id(record_id):
        raise NotFoundError(f"历史记录 {record_id} 不存在")
    return record_id


def clear_records() -> int:
    """清空全部历史，返回删除条数。"""
    return history_repository.delete_all()
