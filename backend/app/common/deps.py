"""鉴权依赖：Bearer token -> Redis -> userId。"""
from dataclasses import dataclass
from typing import Optional

from fastapi import Header

from app.common.exceptions import AppException
from app.common.redis_keys import login_token_key
from app.db.redis import redis_client


@dataclass
class AuthContext:
    user_id: int
    token: str


async def get_auth(authorization: Optional[str] = Header(default=None)) -> AuthContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AppException(401, "未登录或Token已失效")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise AppException(401, "未登录或Token已失效")
    user_id = await redis_client.get(login_token_key(token))
    if user_id is None:
        # token 不存在或已过期：统一 401，前端拦截器据此跳登录页
        raise AppException(401, "未登录或Token已失效")
    return AuthContext(user_id=int(user_id), token=token)
