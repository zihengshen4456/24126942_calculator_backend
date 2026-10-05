"""后端服务启动入口。

用法：
    python run.py

默认监听 http://127.0.0.1:5000 ，可通过环境变量覆盖：
    CALCULATOR_HOST  监听地址，默认 127.0.0.1
    CALCULATOR_PORT  监听端口，默认 5000
    CALCULATOR_DB_PATH  SQLite 数据库文件路径
"""

import os
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC_DIR))

from app import create_app  # noqa: E402  (需要先注册好 src 目录)


def main() -> None:
    app = create_app()
    host = os.environ.get("CALCULATOR_HOST", "127.0.0.1")
    port = int(os.environ.get("CALCULATOR_PORT", "5000"))
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
