"""计算服务：输入校验 + 调用解析器 + 结果规范化。"""

import math

from service.expression_parser import ExpressionError, evaluate
from utils.exceptions import ValidationError

MAX_EXPRESSION_LENGTH = 200
MAX_ABS_RESULT = 1e15


def normalize_expression(expression: str) -> str:
    """去掉多余空白，前端展示与入库都用规范化后的表达式。"""
    return "".join(expression.split())


def format_result(value: float):
    """把浮点结果转换为更符合直觉的形式。

    - 结果不是有限数：报错；
    - 结果绝对值过大：报错，避免出现 1e308 之类不友好的输出；
    - 结果是整数：返回 int，使 12+8 显示为 20 而不是 20.0。
    """
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ExpressionError("计算结果不是有效的有限数值", "RESULT_NOT_FINITE")
        if abs(value) > MAX_ABS_RESULT:
            raise ExpressionError("计算结果过大，超出系统支持范围", "RESULT_TOO_LARGE")
        if float(value).is_integer():
            return int(value)
        # 消除浮点误差带来的长尾（例如 0.1+0.2），保留 12 位有效数字
        return float(f"{value:.12g}")
    return value


class CalculatorService:
    """无状态的计算服务，可安全地在多线程环境下复用。"""

    def calculate(self, expression):
        if not isinstance(expression, str):
            raise ValidationError("参数 expression 必须是字符串")
        if not expression.strip():
            raise ValidationError("表达式不能为空")
        if len(expression) > MAX_EXPRESSION_LENGTH:
            raise ValidationError(
                f"表达式长度不能超过 {MAX_EXPRESSION_LENGTH} 个字符"
            )
        try:
            raw_result = evaluate(expression)
        except ExpressionError as error:
            raise ValidationError(error.message, getattr(error, "code", None))
        return normalize_expression(expression), format_result(raw_result)
