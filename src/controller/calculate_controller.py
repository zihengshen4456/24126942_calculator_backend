"""Calculation endpoint: POST /api/calculate."""

from flask import Blueprint, request

from service.calculator_service import CalculatorService
from service.history_service import add_record
from utils.api_response import ok
from utils.exceptions import ValidationError

calculate_blueprint = Blueprint("calculate", __name__)

calculator_service = CalculatorService()


@calculate_blueprint.post("/api/calculate")
def calculate():
    """Receive an expression, evaluate it, store it and return the result."""
    payload = request.get_json(silent=True)
    if payload is None:
        raise ValidationError("Request body must be valid JSON")
    if "expression" not in payload:
        raise ValidationError("Request body is missing the 'expression' field")

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
