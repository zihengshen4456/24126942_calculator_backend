"""计算历史相关接口：查询 / 删除单条 / 清空。"""

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
        raise ValidationError(f"参数 {field} 必须是整数")


@history_blueprint.get("/api/history")
def list_history():
    """支持关键字搜索与分页的历史查询。"""
    page = _parse_int(request.args.get("page"), "page", 1)
    page_size = _parse_int(request.args.get("pageSize"), "pageSize", 10)
    keyword = request.args.get("keyword", "")
    return ok(history_service.list_records(keyword, page, page_size))


@history_blueprint.delete("/api/history/<int:record_id>")
def delete_history(record_id: int):
    """删除指定 ID 的历史记录。"""
    history_service.delete_record(record_id)
    return ok({"id": record_id, "message": "删除成功"})


@history_blueprint.delete("/api/history")
def clear_history():
    """扩展功能：清空全部历史。"""
    deleted = history_service.clear_records()
    return ok({"deleted": deleted, "message": f"已清空 {deleted} 条历史记录"})


@history_blueprint.get("/api/statistics")
def statistics():
    """扩展功能：计算历史统计。"""
    return ok({"statistics": statistics_service.build_statistics()})
