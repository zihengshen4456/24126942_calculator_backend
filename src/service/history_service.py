"""Business logic for calculation history: create, query (search + paging), delete."""

from typing import Any, Dict, Optional

from model import history_repository
from utils.exceptions import NotFoundError, ValidationError
from utils.timeutil import current_timestamp

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100


def add_record(expression: str, result: Any) -> Dict[str, Any]:
    """Persist a successful calculation."""
    return history_repository.insert(expression, _stringify(result), current_timestamp())


def _stringify(result: Any) -> str:
    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    return str(result)


def list_records(keyword: Optional[str], page: int, page_size: int) -> Dict[str, Any]:
    """Paginated keyword search over the history table."""
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
    """Delete one record; raise 404 when it does not exist."""
    if record_id <= 0:
        raise ValidationError("Record id must be a positive integer")
    if not history_repository.delete_by_id(record_id):
        raise NotFoundError(f"History record {record_id} does not exist")
    return record_id


def clear_records() -> int:
    """Delete every record and return the number of deleted rows."""
    return history_repository.delete_all()
