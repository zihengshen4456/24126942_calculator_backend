"""扩展功能：计算历史统计。"""

import re
from collections import Counter
from typing import Any, Dict

from model import history_repository
from utils.timeutil import current_date

OPERATOR_PATTERN = re.compile(r"(?<=[\d).])\s*([+\-*/%^])\s*(?=[\d.(])")


def build_statistics() -> Dict[str, Any]:
    """统计总记录数、今日记录数、运算符使用情况。"""
    records = history_repository.find_all()
    today = current_date()

    operator_counter = Counter()
    for record in records:
        operator_counter.update(OPERATOR_PATTERN.findall(record["expression"]))

    today_count = sum(1 for record in records if record["createdAt"].startswith(today))
    most_used = operator_counter.most_common(1)

    return {
        "total": len(records),
        "today": today_count,
        "operators": dict(operator_counter),
        "mostUsedOperator": most_used[0][0] if most_used else None,
        "mostUsedCount": most_used[0][1] if most_used else 0,
    }
