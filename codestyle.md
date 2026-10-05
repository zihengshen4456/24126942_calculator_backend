# Back-End Code Standard (Python / Flask)

## Source of the Standard

The rules in this document are derived from the following publicly available and widely
recognised official or community standards:

1. [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/) (the official Python style guide)
2. [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)
3. [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
4. [The Zen of Python (PEP 20)](https://peps.python.org/pep-0020/)

On top of those general standards, a small number of project-specific conventions are
added below so that responsibilities remain clearly separated in a front-end / back-end
separated architecture.

## 1. Layout and Formatting

| Item | Convention |
| --- | --- |
| Indentation | 4 spaces; tabs are not permitted |
| Line length | At most 88 characters per line |
| Blank lines | 2 blank lines around top-level functions and classes; 1 between methods |
| Line continuation | Prefer implicit continuation inside brackets over a backslash |
| File encoding | UTF-8 |
| End of file | Exactly one trailing newline, with no trailing whitespace |

## 2. Naming Conventions

| Element | Convention | Example |
| --- | --- | --- |
| Modules and packages | lowercase, words separated by underscores | `calculator_service.py` |
| Classes | CapWords | `CalculatorService`, `ExpressionError` |
| Functions, methods and variables | snake_case | `calculate()`, `record_id` |
| Constants | UPPER_CASE_WITH_UNDERSCORES | `MAX_EXPRESSION_LENGTH` |
| Non-public members | leading underscore | `_row_to_dict()`, `self._peek()` |

Names must be descriptive. Pinyin, unexplained abbreviations and single-letter names are
not used, except for conventional loop counters such as `i`.

## 3. Imports

- All imports appear at the top of the file and are grouped as standard library, third
  party and project modules, in that order;
- the groups are separated by a blank line;
- `from module import *` is not used;
- imports needed only for type annotations are declared explicitly under `typing`.

```python
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import Blueprint, request

from service.calculator_service import CalculatorService
from utils.api_response import ok
```

## 4. Comments and Docstrings

- Every module, public class and public function has a docstring written with triple
  quotes;
- docstrings describe what the code does and why it is designed that way;
- inline comments explain *why*, not *what*, and never restate the code;
- comments are updated together with the code; stale comments are not acceptable.

```python
def normalize_expression(expression: str) -> str:
    """Remove redundant whitespace so the stored expression is easy to read."""
    return "".join(expression.split())
```

## 5. Type Annotations

- Public functions annotate both their parameters and their return value;
- annotations are documentation, not runtime enforcement;
- optional parameters use `Optional[...]`, containers use `List[...]` and `Dict[...]`.

## 6. Layered Architecture

The project follows a controller / service / data-access structure, and the
responsibilities of the layers are strictly separated.

| Layer | Directory | Responsibility | Must not |
| --- | --- | --- | --- |
| Controller | `src/controller/` | Parse request parameters, call services, return unified responses | Contain business logic or write SQL |
| Service | `src/service/` | Business rules, evaluation, validation, raising exceptions | Touch HTTP objects |
| Model | `src/model/` | Database connections and SQL statements | Contain business decisions |

Every SQL statement is kept in `src/model/history_repository.py` and uses parameterised
queries (`?` placeholders) to prevent SQL injection. Building SQL by string concatenation
is forbidden.

## 7. Error Handling

- Predictable failures (invalid input, division by zero, missing records) are raised as
  the custom exceptions in `utils/exceptions.py` and converted into JSON responses by the
  handlers registered in `app.py`;
- bare `except:` clauses are not allowed; at minimum `Exception` must be caught;
- a caught exception is either handled or re-raised, never silently ignored;
- messages shown to the user must be clear and must not expose stack traces or internal
  implementation details.

## 8. Security Rules

- `eval`, `exec`, `compile` and any other dynamic execution of user input are forbidden;
- user input is validated for type, length and allowed characters before evaluation;
- database access always uses parameterised queries;
- the expression parser only accepts functions and constants from an explicit whitelist.

## 9. Testing

- Test modules live in `tests/` and their names start with `test_`;
- tests use the standard-library `unittest` framework and are independent of each other;
- both happy paths and edge cases are covered (division by zero, unsupported characters,
  over-long expressions and so on);
- new behaviour is accompanied by new test cases.

## 10. Committing

- Commit messages are short imperative sentences describing the change;
- database files, virtual environments and editor configuration are not committed;
- `python -m unittest discover -s tests -t . -v` must pass before anything is committed.
