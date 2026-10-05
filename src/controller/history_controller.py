"""History endpoints: list, delete one, clear all and statistics."""

from flask import Blueprint, request

from service import history_service, statistics_service
from utils.api_response import ok
from utils.exceptions import ValidationError

history_blueprint = Blueprint("history", __name__)


def _parse_int(raw, field: str, default: int) -> int:
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise ValidationError(f"Query parameter '{field}' must be an integer")


@history_blueprint.get("/api/history")
def list_history():
    """Return history with keyword filtering and pagination."""
    page = _parse_int(request.args.get("page"), "page", 1)
    page_size = _parse_int(request.args.get("pageSize"), "pageSize", 10)
    keyword = request.args.get("keyword", "")
    return ok(history_service.list_records(keyword, page, page_size))


@history_blueprint.delete("/api/history/<int:record_id>")
def delete_history(record_id: int):
    """Delete the history record with the given id."""
    history_service.delete_record(record_id)
    return ok({"id": record_id, "message": "Deleted successfully"})


@history_blueprint.delete("/api/history")
def clear_history():
    """Extended feature: delete every history record."""
    deleted = history_service.clear_records()
    return ok({"deleted": deleted, "message": f"Deleted {deleted} history record(s)"})


@history_blueprint.get("/api/statistics")
def statistics():
    """Extended feature: aggregated statistics over the history."""
    return ok({"statistics": statistics_service.build_statistics()})
