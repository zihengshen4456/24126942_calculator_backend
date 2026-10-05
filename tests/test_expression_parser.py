"""表达式解析器的单元测试（python -m unittest discover tests）。"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from service.calculator_service import CalculatorService  # noqa: E402
from service.expression_parser import ExpressionError, evaluate  # noqa: E402
from utils.exceptions import ValidationError  # noqa: E402


class ExpressionParserTest(unittest.TestCase):
    def test_basic_operations(self):
        self.assertEqual(evaluate("12+8"), 20)
        self.assertEqual(evaluate("9-15"), -6)
        self.assertEqual(evaluate("6*7"), 42)
        self.assertEqual(evaluate("10/4"), 2.5)

    def test_operator_precedence(self):
        self.assertEqual(evaluate("1+2*3"), 7)
        self.assertEqual(evaluate("10/2+7"), 12)
        self.assertEqual(evaluate("8-3*2"), 2)

    def test_parentheses(self):
        self.assertEqual(evaluate("(1+2)*3"), 9)
        self.assertEqual(evaluate("2*(3+(4-1))"), 12)

    def test_unary_operators(self):
        self.assertEqual(evaluate("-5+8"), 3)
        self.assertEqual(evaluate("3*-2"), -6)
        self.assertEqual(evaluate("-(2+3)"), -5)

    def test_decimals(self):
        self.assertAlmostEqual(evaluate("0.1+0.2"), 0.3, places=9)

    def test_power_and_functions(self):
        self.assertEqual(evaluate("2^10"), 1024)
        self.assertEqual(evaluate("2**3"), 8)
        self.assertEqual(evaluate("sqrt(16)"), 4)
        self.assertEqual(evaluate("max(3,8)"), 8)
        self.assertEqual(evaluate("fact(5)"), 120)
        self.assertAlmostEqual(evaluate("sin(pi/2)"), 1.0, places=9)

    def test_division_by_zero(self):
        with self.assertRaises(ExpressionError) as context:
            evaluate("1/0")
        self.assertEqual(context.exception.code, "DIVISION_BY_ZERO")

    def test_invalid_expressions(self):
        for expression in ["1+", "(1+2", "1+*2", "abc", "1@2", "sqrt()", "sqrt(1,2)"]:
            with self.assertRaises(ExpressionError, msg=expression):
                evaluate(expression)

    def test_no_code_injection(self):
        for expression in [
            "__import__('os').system('echo hacked')",
            "1+__import__('os')",
            "eval('1+1')",
        ]:
            with self.assertRaises(ExpressionError, msg=expression):
                evaluate(expression)


class CalculatorServiceTest(unittest.TestCase):
    def setUp(self):
        self.service = CalculatorService()

    def test_normalize_and_format(self):
        expression, result = self.service.calculate(" (1 + 2) * 3 ")
        self.assertEqual(expression, "(1+2)*3")
        self.assertEqual(result, 9)
        self.assertIsInstance(result, int)

    def test_decimal_result_keeps_float(self):
        _, result = self.service.calculate("10/4")
        self.assertEqual(result, 2.5)

    def test_empty_expression(self):
        with self.assertRaises(ValidationError):
            self.service.calculate("   ")

    def test_too_long_expression(self):
        with self.assertRaises(ValidationError):
            self.service.calculate("1+" * 200)

    def test_non_string_expression(self):
        with self.assertRaises(ValidationError):
            self.service.calculate(123)


if __name__ == "__main__":
    unittest.main()
