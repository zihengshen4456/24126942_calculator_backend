# Calculator Backend

Back-end service of an online calculator built with a front-end / back-end separated
architecture. It is responsible for expression parsing and evaluation, input validation,
exception handling and persistence of the calculation history, and exposes all of this
through a RESTful API.

> The matching front-end repository is linked in the assignment blog post.

## 1. Overview

This service is the "brain" of the system:

- the front end only handles interaction and presentation;
- every arithmetic operation, expression validation and error decision happens here;
- each successful calculation is written to an SQLite database and can be queried or
  deleted by the client at any time.

Core principle: **the front end performs no arithmetic and only sends an expression string.**

## 2. Technology Stack

| Item | Choice |
| --- | --- |
| Language | Python 3.8+ (developed on Python 3.13) |
| Web framework | Flask 3.1 |
| Database | SQLite 3 through the standard-library `sqlite3` module |
| Expression evaluation | Hand-written tokenizer plus recursive descent parser; no `eval` or `exec` |
| Testing | Standard-library `unittest` |

## 3. Requirements

- Python 3.8 or later
- Windows, macOS or Linux
- No third-party dependency other than Flask; the database is part of the standard library

## 4. Installation

```bash
# 1. Enter the project directory
cd 24126942_calculator_backend

# 2. (Recommended) create a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install the dependencies
pip install -r requirements.txt
```

## 5. Database Initialisation

No manual step is required. The database file and the `calculation_history` table are
created automatically the first time the service starts, and the operation is idempotent
so restarting is always safe.

```
data/calculator.db          # created automatically on first start
```

Schema:

```sql
CREATE TABLE IF NOT EXISTS calculation_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    expression  TEXT    NOT NULL,
    result      TEXT    NOT NULL,
    created_at  TEXT    NOT NULL
);
```

To start from an empty database, delete `data/calculator.db` and restart the service.

## 6. Running the Service

```bash
python run.py
```

On success the console prints:

```
 * Running on http://127.0.0.1:5000
```

Opening <http://127.0.0.1:5000/api/health> should return:

```json
{ "success": true, "service": "calculator-backend", "status": "UP" }
```

## 7. Configuration

All configuration is supplied through environment variables, and every one of them has a
default, so the service also runs with no configuration at all.

| Variable | Meaning | Default |
| --- | --- | --- |
| `CALCULATOR_HOST` | Listen address | `127.0.0.1` |
| `CALCULATOR_PORT` | Listen port | `5000` |
| `CALCULATOR_DB_PATH` | Path of the SQLite database file | `data/calculator.db` |
| `CALCULATOR_TZ_OFFSET` | UTC offset in hours used when recording timestamps, e.g. `8` | server local time |

Example, making the service reachable from other machines on the network:

```bash
CALCULATOR_HOST=0.0.0.0 python run.py
```

## 8. API

Every endpoint returns JSON in one of two shapes:

- success: `{ "success": true, ...business fields }`
- failure: `{ "success": false, "message": "...", "code": "..." }`

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/calculate` | Evaluate an expression and record it |
| `GET` | `/api/history` | Query the history (`keyword`, `page`, `pageSize`) |
| `DELETE` | `/api/history/{id}` | Delete one history record |
| `DELETE` | `/api/history` | Delete all history records (extended feature) |
| `GET` | `/api/statistics` | Aggregated statistics (extended feature) |
| `GET` | `/api/health` | Health check |

### 8.1 Evaluate an expression

```http
POST /api/calculate
Content-Type: application/json

{ "expression": "(1+2)*3" }
```

Success (HTTP 200):

```json
{
  "success": true,
  "expression": "(1+2)*3",
  "result": 9,
  "id": 1,
  "createdAt": "2026-10-06 10:20:00"
}
```

Failure (HTTP 400):

```json
{ "success": false, "message": "Division by zero is not allowed", "code": "DIVISION_BY_ZERO" }
```

### 8.2 Query the history

```http
GET /api/history?keyword=1%2B2&page=1&pageSize=10
```

```json
{
  "success": true,
  "items": [
    { "id": 3, "expression": "1+2", "result": "3", "createdAt": "2026-10-06 10:22:00" }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 10,
  "totalPages": 1,
  "keyword": "1+2"
}
```

### 8.3 Delete one record

```http
DELETE /api/history/3
```

Returns 200 on success, or 404 when the record does not exist:

```json
{ "success": false, "message": "History record 3 does not exist", "code": "NOT_FOUND" }
```

### 8.4 Statistics (extended feature)

```json
{
  "success": true,
  "statistics": {
    "total": 12,
    "today": 8,
    "operators": { "+": 5, "*": 4, "/": 3 },
    "mostUsedOperator": "+",
    "mostUsedCount": 5
  }
}
```

## 9. Supported Expression Syntax

| Category | Notes | Examples |
| --- | --- | --- |
| Basic arithmetic | `+ - * /` | `12+8`, `10/4` |
| Modulo | `%` | `10%3` |
| Exponentiation | `^` or `**`, right associative | `2^10`, `2^-1` |
| Parentheses | Change the order of evaluation | `(1+2)*3` |
| Unary sign | Allowed in any operand position | `-5+8`, `3*-2` |
| Decimals | The `.5` form is accepted | `0.1+0.2` |
| Constants | `pi`, `e`, `tau` | `2*pi` |
| Unary functions | `sqrt cbrt abs sin cos tan asin acos atan ln log log2 exp floor ceil round fact` | `sqrt(16)`, `fact(5)` |
| Binary functions | `pow hypot max min mod` | `pow(2,10)`, `max(3,8)` |

Invalid input produces an explicit error:

| Input | Error code | Message |
| --- | --- | --- |
| `1/0` | `DIVISION_BY_ZERO` | Division by zero is not allowed |
| `1+` | `EXPRESSION_SYNTAX_ERROR` | Expression is incomplete |
| `(1+2` | `EXPRESSION_SYNTAX_ERROR` | Unbalanced parentheses: ')' expected |
| `abc` | `UNKNOWN_IDENTIFIER` | Unknown constant or function 'abc' |
| `1@2` | `UNSUPPORTED_CHARACTER` | Unsupported character '@' in expression |

## 10. Running the Tests

```bash
python -m unittest discover -s tests -t . -v
```

The suite covers expression parsing, precedence, parentheses, unary operators, decimals,
division by zero, invalid input and injection attempts, as well as the calculation,
history, search, pagination, deletion and statistics endpoints.

## 11. Connecting the Front End

1. Start the back end with `python run.py` (listening on `127.0.0.1:5000` by default).
2. Open the front-end page; it requests `http://127.0.0.1:5000/api` by default.
3. If the API is hosted elsewhere, append the `?api=` parameter to the page URL instead of
   editing the source:

   ```
   calculator.html?api=http://192.168.1.10:5000/api
   ```

CORS is enabled on the server (`Access-Control-Allow-Origin: *`), so the two parts may be
deployed separately.

## 12. Project Structure

```
24126942_calculator_backend/
├── src/
│   ├── app.py                    # Flask application factory: blueprints, errors, CORS
│   ├── controller/               # HTTP layer: receive requests, validate parameters
│   │   ├── calculate_controller.py
│   │   └── history_controller.py
│   ├── service/                  # Business layer: calculation, history, statistics
│   │   ├── expression_parser.py  # Hand-written tokenizer and recursive descent parser
│   │   ├── calculator_service.py
│   │   ├── history_service.py
│   │   └── statistics_service.py
│   ├── model/                    # Data layer: connection handling and SQL
│   │   ├── database.py
│   │   └── history_repository.py
│   └── utils/                    # Shared helpers: responses, exceptions, time
│       ├── api_response.py
│       ├── exceptions.py
│       └── timeutil.py
├── tests/                        # Unit and integration tests
├── data/                         # Location of the SQLite file (created automatically)
├── run.py                        # Entry point
├── requirements.txt
├── README.md
└── codestyle.md
```

## 13. Security Notes

This project does **not** use `eval`, `exec` or any equivalent form of dynamic code
execution.

The parser recognises only a fixed set of operators, functions and constants. The
tokenizer rejects every character outside that set, and the syntax analyser rejects every
structure outside the grammar. An input such as `__import__('os').system('...')` therefore
fails during parsing, and there is no code-injection surface.
