"""SQLite connection handling and schema creation."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# src/model/database.py -> src/model -> src -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "calculator.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS calculation_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    expression  TEXT    NOT NULL,
    result      TEXT    NOT NULL,
    created_at  TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_history_created_at
    ON calculation_history (created_at DESC);
"""


def get_database_path() -> Path:
    """Return the database file path; can be overridden by an environment variable."""
    configured = os.environ.get("CALCULATOR_DB_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    """Create a new connection (one per request avoids thread issues)."""
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def connection_scope():
    """Commit on success and always close the connection."""
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_database() -> None:
    """Create the schema (idempotent, safe to call on every start-up)."""
    with connection_scope() as connection:
        connection.executescript(SCHEMA)
