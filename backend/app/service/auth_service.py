"""登录 / 登出：Redis 不透明 token 会话（不使用 JWT）。

token = secrets.token_urlsafe(32)，不可预测、无状态签名负担；
Redis 存 user_id + 7 天 TTL，登出立即 DEL，具备主动失效能力。
"""
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.config import settings
from app.common.exceptions import AppException
from app.common.redis_keys import login_token_key
from app.common.security import verify_password
from app.db.redis import redis_client
from app.models.user import User


async def login(session: AsyncSession, username: str, password: str) -> dict:
    user = (
        await session.execute(select(User).where(User.username == username))
    ).scalar_one_or_none()
    # 统一提示，不区分“用户不存在 / 密码错误”，防止账号枚举
    if user is None or not verify_password(password, user.password):
        raise AppException(400, "用户名或密码错误")

    token = secrets.token_urlsafe(32)
    await redis_client.set(
        login_token_key(token), str(user.id), ex=settings.token_ttl_seconds
    )
    return {"token": token, "user": {"id": user.id, "username": user.username}}


async def logout(token: str) -> None:
    await redis_client.delete(login_token_key(token))
