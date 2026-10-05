"""Entry point of the back-end service.

Usage:
    python run.py

Listens on http://127.0.0.1:5000 by default. The following environment
variables can be used to override the defaults:
    CALCULATOR_HOST     listen address, default 127.0.0.1
    CALCULATOR_PORT     listen port, default 5000
    CALCULATOR_DB_PATH  path of the SQLite database file
"""

import os
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC_DIR))

from app import create_app  # noqa: E402  (src must be on sys.path first)


def main() -> None:
    app = create_app()
    host = os.environ.get("CALCULATOR_HOST", "127.0.0.1")
    port = int(os.environ.get("CALCULATOR_PORT", "5000"))
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
