"""安全的数学表达式解析器（不使用 eval / exec）。

实现思路：
1. 词法分析（Tokenize）：把字符串切成数字、运算符、括号、标识符四类词法单元；
2. 语法分析（递归下降）：按优先级从低到高依次解析表达式、项、一元、幂、原子；
3. 求值：在语法分析过程中直接自底向上求值。

文法（优先级由低到高）：
    expression := term (('+' | '-') term)*
    term       := unary (('*' | '/' | '%') unary)*
    unary      := ('+' | '-') unary | power
    power      := primary ('^' unary)?          # 幂运算右结合，支持 2^-1
    primary    := NUMBER | IDENT | IDENT '(' arguments ')' | '(' expression ')'

因为只认识有限的运算符、函数和常量，任何试图执行通用代码的输入都会在
词法或语法阶段被拒绝，从原理上避免了代码注入。
"""

import math
from typing import Any, Dict, List, Tuple


class ExpressionError(Exception):
    """表达式错误的基类，携带错误码与 HTTP 状态码。"""

    code = "EXPRESSION_ERROR"
    status = 400

    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


def _build_functions() -> Dict[str, Tuple[int, Any]]:
    """函数名 -> (参数个数, 实现)。"""

    def mod(a: float, b: float) -> float:
        if b == 0:
            raise ExpressionError("取模运算的除数不能为 0", "DIVISION_BY_ZERO")
        return math.fmod(a, b)

    return {
        "sqrt": (1, math.sqrt),
        "cbrt": (1, lambda x: math.copysign(abs(x) ** (1 / 3), x)),
        "abs": (1, abs),
        "sin": (1, math.sin),
        "cos": (1, math.cos),
        "tan": (1, math.tan),
        "asin": (1, math.asin),
        "acos": (1, math.acos),
        "atan": (1, math.atan),
        "ln": (1, math.log),
        "log": (1, math.log10),
        "log10": (1, math.log10),
        "log2": (1, math.log2),
        "exp": (1, math.exp),
        "floor": (1, math.floor),
        "ceil": (1, math.ceil),
        "round": (1, math.floor),  # 占位，下面会被 round_half_up 覆盖
        "fact": (1, None),  # 占位，下面会被 factorial 覆盖
        "pow": (2, math.pow),
        "hypot": (2, math.hypot),
        "max": (2, max),
        "min": (2, min),
        "mod": (2, mod),
    }


def _factorial(x: float) -> float:
    if x < 0 or abs(x - round(x)) > 1e-9:
        raise ExpressionError("阶乘只支持非负整数", "FUNCTION_DOMAIN_ERROR")
    if x > 170:
        raise ExpressionError("阶乘参数过大，结果超出可表示范围", "FUNCTION_DOMAIN_ERROR")
    return float(math.factorial(int(round(x))))


def _round_half_up(x: float) -> float:
    return float(math.floor(x + 0.5)) if x >= 0 else float(math.ceil(x - 0.5))


FUNCTIONS: Dict[str, Tuple[int, Any]] = _build_functions()
FUNCTIONS["round"] = (1, _round_half_up)
FUNCTIONS["fact"] = (1, _factorial)

CONSTANTS: Dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

MAX_NESTING_DEPTH = 32


class Token:
    """词法单元。"""

    __slots__ = ("kind", "value", "position")

    def __init__(self, kind: str, value: Any, position: int):
        self.kind = kind          # NUMBER / IDENT / OP / LPAREN / RPAREN / COMMA
        self.value = value
        self.position = position  # 在原始字符串中的下标，用于报错定位

    def __repr__(self) -> str:  # pragma: no cover - 仅调试用
        return f"Token({self.kind}, {self.value!r}, {self.position})"


def tokenize(text: str) -> List[Token]:
    """把表达式字符串切分成词法单元列表。"""
    tokens: List[Token] = []
    index = 0
    length = len(text)

    while index < length:
        char = text[index]

        if char.isspace():
            index += 1
            continue

        # 数字：整数、小数、.5 这类写法
        if char.isdigit() or char == ".":
            start = index
            dot_count = 0
            while index < length and (text[index].isdigit() or text[index] == "."):
                if text[index] == ".":
                    dot_count += 1
                index += 1
            literal = text[start:index]
            if dot_count > 1 or literal == ".":
                raise ExpressionError(
                    f"数字格式错误：'{literal}'", "EXPRESSION_SYNTAX_ERROR"
                )
            tokens.append(Token("NUMBER", float(literal), start))
            continue

        # 标识符：函数名或常量名
        if char.isalpha() or char == "_":
            start = index
            while index < length and (text[index].isalnum() or text[index] == "_"):
                index += 1
            tokens.append(Token("IDENT", text[start:index].lower(), start))
            continue

        # 幂运算：同时接受 ^ 和 ** 两种写法
        if text.startswith("**", index):
            tokens.append(Token("OP", "^", index))
            index += 2
            continue

        if char in "+-*/%^":
            tokens.append(Token("OP", char, index))
            index += 1
            continue

        if char == "(":
            tokens.append(Token("LPAREN", char, index))
            index += 1
            continue

        if char == ")":
            tokens.append(Token("RPAREN", char, index))
            index += 1
            continue

        if char == ",":
            tokens.append(Token("COMMA", char, index))
            index += 1
            continue

        raise ExpressionError(
            f"表达式包含不支持的字符 '{char}'", "UNSUPPORTED_CHARACTER"
        )

    if not tokens:
        raise ExpressionError("表达式不能为空", "EXPRESSION_SYNTAX_ERROR")
    return tokens


class Parser:
    """递归下降解析器，解析与求值同时完成。"""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.index = 0
        self.depth = 0

    # ---- 工具方法 -------------------------------------------------

    def _peek(self):
        if self.index < len(self.tokens):
            return self.tokens[self.index]
        return None

    def _advance(self) -> Token:
        token = self.tokens[self.index]
        self.index += 1
        return token

    def _match_operator(self, *operators: str):
        token = self._peek()
        if token and token.kind == "OP" and token.value in operators:
            self.index += 1
            return token.value
        return None

    def _enter(self) -> None:
        self.depth += 1
        if self.depth > MAX_NESTING_DEPTH:
            raise ExpressionError("表达式嵌套层级过深", "EXPRESSION_TOO_DEEP")

    def _leave(self) -> None:
        self.depth -= 1

    # ---- 语法规则 -------------------------------------------------

    def parse(self) -> float:
        value = self._parse_expression()
        if self.index != len(self.tokens):
            token = self.tokens[self.index]
            raise ExpressionError(
                f"表达式在位置 {token.position} 处存在多余内容",
                "EXPRESSION_SYNTAX_ERROR",
            )
        return value

    def _parse_expression(self) -> float:
        self._enter()
        try:
            value = self._parse_term()
            while True:
                operator = self._match_operator("+", "-")
                if operator is None:
                    break
                right = self._parse_term()
                value = value + right if operator == "+" else value - right
            return value
        finally:
            self._leave()

    def _parse_term(self) -> float:
        value = self._parse_unary()
        while True:
            operator = self._match_operator("*", "/", "%")
            if operator is None:
                break
            right = self._parse_unary()
            if operator == "*":
                value = value * right
            elif operator == "/":
                if right == 0:
                    raise ExpressionError("除数不能为 0", "DIVISION_BY_ZERO")
                value = value / right
            else:
                if right == 0:
                    raise ExpressionError("取模运算的除数不能为 0", "DIVISION_BY_ZERO")
                value = math.fmod(value, right)
        return value

    def _parse_unary(self) -> float:
        operator = self._match_operator("+", "-")
        if operator is not None:
            self._enter()
            try:
                value = self._parse_unary()
            finally:
                self._leave()
            return value if operator == "+" else -value
        return self._parse_power()

    def _parse_power(self) -> float:
        base = self._parse_primary()
        if self._match_operator("^") is not None:
            # 右结合：2^3^2 == 2^(3^2)
            exponent = self._parse_unary()
            try:
                return float(math.pow(base, exponent))
            except (ValueError, OverflowError):
                raise ExpressionError(
                    f"无法计算 {base}^{exponent}（结果超出定义域或范围）",
                    "FUNCTION_DOMAIN_ERROR",
                )
        return base

    def _parse_primary(self) -> float:
        token = self._peek()
        if token is None:
            raise ExpressionError("表达式不完整", "EXPRESSION_SYNTAX_ERROR")

        if token.kind == "NUMBER":
            self._advance()
            return token.value

        if token.kind == "LPAREN":
            self._advance()
            self._enter()
            try:
                value = self._parse_expression()
            finally:
                self._leave()
            closing = self._peek()
            if closing is None or closing.kind != "RPAREN":
                raise ExpressionError("括号不匹配，缺少 ')'", "EXPRESSION_SYNTAX_ERROR")
            self._advance()
            return value

        if token.kind == "IDENT":
            return self._parse_identifier()

        raise ExpressionError(
            f"位置 {token.position} 处的 '{token.value}' 不是合法的运算对象",
            "EXPRESSION_SYNTAX_ERROR",
        )

    def _parse_identifier(self) -> float:
        token = self._advance()
        name = token.value

        if self._peek() and self._peek().kind == "LPAREN":
            if name not in FUNCTIONS:
                raise ExpressionError(
                    f"不支持的函数 '{name}'", "UNSUPPORTED_FUNCTION"
                )
            self._advance()  # 吃掉 '('
            arguments: List[float] = []
            if self._peek() and self._peek().kind == "RPAREN":
                self._advance()
            else:
                while True:
                    arguments.append(self._parse_expression())
                    separator = self._peek()
                    if separator and separator.kind == "COMMA":
                        self._advance()
                        continue
                    break
                closing = self._peek()
                if closing is None or closing.kind != "RPAREN":
                    raise ExpressionError(
                        f"函数 '{name}' 的括号不匹配", "EXPRESSION_SYNTAX_ERROR"
                    )
                self._advance()
            return self._apply_function(name, arguments, token.position)

        if name in CONSTANTS:
            return CONSTANTS[name]

        raise ExpressionError(
            f"未知的常量或函数 '{name}'", "UNKNOWN_IDENTIFIER"
        )

    @staticmethod
    def _apply_function(name: str, arguments: List[float], position: int) -> float:
        arity, implementation = FUNCTIONS[name]
        if len(arguments) != arity:
            raise ExpressionError(
                f"函数 '{name}' 需要 {arity} 个参数，实际传入 {len(arguments)} 个",
                "FUNCTION_ARITY_ERROR",
            )
        try:
            return float(implementation(*arguments))
        except ExpressionError:
            raise
        except ZeroDivisionError:
            raise ExpressionError("除数不能为 0", "DIVISION_BY_ZERO")
        except (ValueError, OverflowError):
            raise ExpressionError(
                f"函数 '{name}' 在位置 {position} 处的参数超出定义域",
                "FUNCTION_DOMAIN_ERROR",
            )


def evaluate(expression: str) -> float:
    """解析并计算表达式，返回浮点结果。

    任何非法输入都会抛出 ExpressionError 的子类实例。
    """
    return Parser(tokenize(expression)).parse()
