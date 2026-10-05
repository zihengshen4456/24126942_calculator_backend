"""计算相关接口：POST /api/calculate。"""

from flask import Blueprint, request

from service.calculator_service import CalculatorService
from service.history_service import add_record
from utils.api_response import ok
from utils.exceptions import ValidationError

calculate_blueprint = Blueprint("calculate", __name__)

calculator_service = CalculatorService()


@calculate_blueprint.post("/api/calculate")
def calculate():
    """接收表达式 -> 后端计算 -> 写入历史 -> 返回结果。"""
    payload = request.get_json(silent=True)
    if payload is None:
        raise ValidationError("请求体必须是合法的 JSON")
    if "expression" not in payload:
        raise ValidationError("请求体缺少 expression 字段")

    expression, result = calculator_service.calculate(payload["expression"])
    record = add_record(expression, result)

    return ok(
        {
            "expression": expression,
            "result": result,
            "id": record["id"],
            "createdAt": record["createdAt"],
        }
    )
