"""Time helpers.

Server local time is used by default. When the deployment time zone differs from
the user's time zone, CALCULATOR_TZ_OFFSET can be set to the UTC offset in hours,
for example CALCULATOR_TZ_OFFSET=8 for UTC+8.
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
