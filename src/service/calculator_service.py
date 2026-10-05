"""Calculation service: input validation, parser invocation and result formatting."""

import math

from service.expression_parser import ExpressionError, evaluate
from utils.exceptions import ValidationError

MAX_EXPRESSION_LENGTH = 200
MAX_ABS_RESULT = 1e15


def normalize_expression(expression: str) -> str:
    """Remove redundant whitespace so the stored expression is easy to read."""
    return "".join(expression.split())


def format_result(value: float):
    """Convert a float result into a more intuitive representation.

    - non-finite results are rejected;
    - results whose absolute value is too large are rejected;
    - integral results are returned as int so 12+8 renders as 20, not 20.0;
    - remaining floats are rounded to 12 significant digits to remove the
      floating point tail (0.1+0.2 -> 0.3).
    """
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ExpressionError("Result is not a finite number", "RESULT_NOT_FINITE")
        if abs(value) > MAX_ABS_RESULT:
            raise ExpressionError("Result is out of the supported range", "RESULT_TOO_LARGE")
        if float(value).is_integer():
            return int(value)
        return float(f"{value:.12g}")
    return value


class CalculatorService:
    """Stateless calculation service, safe to share between threads."""

    def calculate(self, expression):
        if not isinstance(expression, str):
            raise ValidationError("Field 'expression' must be a string")
        if not expression.strip():
            raise ValidationError("Expression must not be empty")
        if len(expression) > MAX_EXPRESSION_LENGTH:
            raise ValidationError(
                f"Expression must not exceed {MAX_EXPRESSION_LENGTH} characters"
            )
        try:
            raw_result = evaluate(expression)
        except ExpressionError as error:
            raise ValidationError(error.message, getattr(error, "code", None))
        return normalize_expression(expression), format_result(raw_result)
