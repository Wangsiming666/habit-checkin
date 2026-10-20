"""Redis 异步客户端（redis.asyncio）。

decode_responses=True：业务侧拿到的都是 str，避免到处 decode。
客户端本身是惰性连接，import 时不会建立网络连接。
"""
from redis.asyncio import Redis

from app.common.config import settings

redis_client = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    decode_responses=True,
)
