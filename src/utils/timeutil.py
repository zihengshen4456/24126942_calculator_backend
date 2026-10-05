"""时间工具：统一后端的时间来源。

默认使用服务器本地时间；如果部署环境的时区与使用者所在时区不同，
可以通过环境变量 CALCULATOR_TZ_OFFSET 指定相对 UTC 的小时偏移，
例如 CALCULATOR_TZ_OFFSET=8 表示东八区（北京时间）。
"""

import os
from datetime import datetime, timedelta, timezone

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def current_datetime() -> datetime:
    offset = os.environ.get("CALCULATOR_TZ_OFFSET")
    if offset:
        try:
            return datetime.now(timezone(timedelta(hours=float(offset))))
        except ValueError:
            pass
    return datetime.now()


def current_timestamp() -> str:
    return current_datetime().strftime(TIMESTAMP_FORMAT)


def current_date() -> str:
    return current_datetime().strftime("%Y-%m-%d")
