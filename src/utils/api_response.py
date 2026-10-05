"""Unified API response format.

Success: {"success": true, ...business fields}
Failure: {"success": false, "message": "...", "code": "..."}
"""

from typing import Any, Dict, Optional, Tuple

from flask import jsonify


def ok(payload: Optional[Dict[str, Any]] = None, status: int = 200) -> Tuple[Any, int]:
    body: Dict[str, Any] = {"success": True}
    if payload:
        body.update(payload)
    return jsonify(body), status


def fail(message: str, code: Optional[str] = None, status: int = 400):
    body: Dict[str, Any] = {"success": False, "message": message}
    if code:
        body["code"] = code
    return jsonify(body), status
