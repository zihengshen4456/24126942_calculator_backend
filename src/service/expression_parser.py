"""Safe mathematical expression parser (no eval / exec).

Implementation approach:
1. Lexical analysis (tokenize): split the input string into numbers, operators,
   parentheses and identifiers.
2. Syntax analysis (recursive descent): parse the grammar from the lowest to the
   highest precedence level and evaluate while parsing.

Grammar (precedence from low to high):
    expression := term (('+' | '-') term)*
    term       := unary (('*' | '/' | '%') unary)*
    unary      := ('+' | '-') unary | power
    power      := primary ('^' unary)?          # right associative, allows 2^-1
    primary    := NUMBER | IDENT | IDENT '(' arguments ')' | '(' expression ')'

The parser only recognises a fixed set of operators, functions and constants.
Anything that tries to execute general purpose code is rejected during the
lexical or the syntax phase, which removes the need for eval.
"""

import math
from typing import Any, Dict, List, Tuple


class ExpressionError(Exception):
    """Base class for expression errors. Carries an error code."""

    code = "EXPRESSION_ERROR"
    status = 400

    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


def _build_functions() -> Dict[str, Tuple[int, Any]]:
    """Mapping of function name -> (arity, implementation)."""

    def mod(a: float, b: float) -> float:
        if b == 0:
            raise ExpressionError("Modulo by zero is not allowed", "DIVISION_BY_ZERO")
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
        "round": (1, math.floor),  # placeholder, replaced by round_half_up below
        "fact": (1, None),         # placeholder, replaced by factorial below
        "pow": (2, math.pow),
        "hypot": (2, math.hypot),
        "max": (2, max),
        "min": (2, min),
        "mod": (2, mod),
    }


def _factorial(x: float) -> float:
    if x < 0 or abs(x - round(x)) > 1e-9:
        raise ExpressionError(
            "fact() only accepts non-negative integers", "FUNCTION_DOMAIN_ERROR"
        )
    if x > 170:
        raise ExpressionError(
            "fact() argument is too large to represent", "FUNCTION_DOMAIN_ERROR"
        )
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
    """A single lexical token."""

    __slots__ = ("kind", "value", "position")

    def __init__(self, kind: str, value: Any, position: int):
        self.kind = kind          # NUMBER / IDENT / OP / LPAREN / RPAREN / COMMA
        self.value = value
        self.position = position  # index in the original string, used in errors

    def __repr__(self) -> str:  # pragma: no cover - debugging helper only
        return f"Token({self.kind}, {self.value!r}, {self.position})"


def tokenize(text: str) -> List[Token]:
    """Split an expression string into a list of tokens."""
    tokens: List[Token] = []
    index = 0
    length = len(text)

    while index < length:
        char = text[index]

        if char.isspace():
            index += 1
            continue

        # Numbers: integers, decimals and the ".5" form
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
                    f"Invalid number format: '{literal}'", "EXPRESSION_SYNTAX_ERROR"
                )
            tokens.append(Token("NUMBER", float(literal), start))
            continue

        # Identifiers: function names or constant names
        if char.isalpha() or char == "_":
            start = index
            while index < length and (text[index].isalnum() or text[index] == "_"):
                index += 1
            tokens.append(Token("IDENT", text[start:index].lower(), start))
            continue

        # Exponentiation: accept both ^ and **
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
            f"Unsupported character '{char}' in expression", "UNSUPPORTED_CHARACTER"
        )

    if not tokens:
        raise ExpressionError("Expression must not be empty", "EXPRESSION_SYNTAX_ERROR")
    return tokens


class Parser:
    """Recursive descent parser that evaluates while parsing."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.index = 0
        self.depth = 0

    # ---- helpers ---------------------------------------------------

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
            raise ExpressionError("Expression is nested too deeply", "EXPRESSION_TOO_DEEP")

    def _leave(self) -> None:
        self.depth -= 1

    # ---- grammar rules ---------------------------------------------

    def parse(self) -> float:
        value = self._parse_expression()
        if self.index != len(self.tokens):
            token = self.tokens[self.index]
            raise ExpressionError(
                f"Unexpected content at position {token.position}",
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
                    raise ExpressionError("Division by zero is not allowed", "DIVISION_BY_ZERO")
                value = value / right
            else:
                if right == 0:
                    raise ExpressionError("Modulo by zero is not allowed", "DIVISION_BY_ZERO")
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
            # Right associative: 2^3^2 == 2^(3^2)
            exponent = self._parse_unary()
            try:
                return float(math.pow(base, exponent))
            except (ValueError, OverflowError):
                raise ExpressionError(
                    f"Cannot evaluate {base}^{exponent} (out of domain or range)",
                    "FUNCTION_DOMAIN_ERROR",
                )
        return base

    def _parse_primary(self) -> float:
        token = self._peek()
        if token is None:
            raise ExpressionError("Expression is incomplete", "EXPRESSION_SYNTAX_ERROR")

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
                raise ExpressionError(
                    "Unbalanced parentheses: ')' expected", "EXPRESSION_SYNTAX_ERROR"
                )
            self._advance()
            return value

        if token.kind == "IDENT":
            return self._parse_identifier()

        raise ExpressionError(
            f"'{token.value}' at position {token.position} is not a valid operand",
            "EXPRESSION_SYNTAX_ERROR",
        )

    def _parse_identifier(self) -> float:
        token = self._advance()
        name = token.value

        if self._peek() and self._peek().kind == "LPAREN":
            if name not in FUNCTIONS:
                raise ExpressionError(
                    f"Unsupported function '{name}'", "UNSUPPORTED_FUNCTION"
                )
            self._advance()  # consume '('
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
                        f"Unbalanced parentheses in function '{name}'",
                        "EXPRESSION_SYNTAX_ERROR",
                    )
                self._advance()
            return self._apply_function(name, arguments, token.position)

        if name in CONSTANTS:
            return CONSTANTS[name]

        raise ExpressionError(
            f"Unknown constant or function '{name}'", "UNKNOWN_IDENTIFIER"
        )

    @staticmethod
    def _apply_function(name: str, arguments: List[float], position: int) -> float:
        arity, implementation = FUNCTIONS[name]
        if len(arguments) != arity:
            raise ExpressionError(
                f"Function '{name}' expects {arity} argument(s) but received {len(arguments)}",
                "FUNCTION_ARITY_ERROR",
            )
        try:
            return float(implementation(*arguments))
        except ExpressionError:
            raise
        except ZeroDivisionError:
            raise ExpressionError("Division by zero is not allowed", "DIVISION_BY_ZERO")
        except (ValueError, OverflowError):
            raise ExpressionError(
                f"Argument of function '{name}' at position {position} is out of domain",
                "FUNCTION_DOMAIN_ERROR",
            )


def evaluate(expression: str) -> float:
    """Parse and evaluate an expression, returning a float.

    Any invalid input raises an ExpressionError subclass.
    """
    return Parser(tokenize(expression)).parse()
