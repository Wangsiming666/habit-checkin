"""统一返回结构：所有接口只允许 {code, msg, data} 这一种形状。"""
from typing import Any

from app.common.error_code import ErrorCode


def ok(data: Any = None, msg: str = "success") -> dict:
    return {"code": ErrorCode.SUCCESS, "msg": msg, "data": data}


def fail(code: int, msg: str) -> dict:
    return {"code": code, "msg": msg, "data": None}
