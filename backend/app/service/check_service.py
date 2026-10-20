"""打卡业务：三层防重 + Cache Aside + 事务内重算连续天数。

三层防护分工：
1. check:today 缓存快路径：挡住重复点击（体验层）；
2. Redis 分布式锁：同一 item + 同一天只允许一个请求进入事务（减少无效写）；
3. 数据库 uk_item_date 唯一索引：正确性保证——即使 Redis 挂了、锁过期、
   多 worker 并发，check_record 也不会出现第二条记录。
"""
import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import timeutil
from app.common.exceptions import AppException
from app.common.redis_keys import check_lock_key, check_today_key, streak_key
from app.db.redis import redis_client
from app.models.check_record import CheckRecord
from app.service.item_service import get_owned_item
from app.service.streak_service import compute_streak, fetch_check_dates

logger = logging.getLogger(__name__)

# 只删除自己持有的锁：GET 比对 uuid 后再 DEL，避免锁过期后误删他人锁
LOCK_RELEASE_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""


async def is_checked_today(
    session: AsyncSession, item_id: int, today
) -> bool:
    """当日状态：缓存命中即返回；未命中回源，存在则回填。"""
    key = check_today_key(item_id, timeutil.date_key(today))
    if await redis_client.get(key) == "1":
        return True
    exists = await session.scalar(
        select(func.count())
        .select_from(CheckRecord)
        .where(
            CheckRecord.item_id == item_id,
            CheckRecord.check_date == today,
        )
    )
    if exists:
        await redis_client.set(key, "1", ex=timeutil.seconds_to_midnight())
        return True
    return False


async def check_in(session: AsyncSession, user_id: int, item_id: int) -> dict:
    item = await get_owned_item(session, user_id, item_id)

    today = timeutil.today_bj()
    dk = timeutil.date_key(today)
    marker_key = check_today_key(item_id, dk)

    # 第一层：当日状态缓存快路径
    if await redis_client.get(marker_key) == "1":
        raise AppException(409, "今日已打卡")

    # 第二层：分布式锁（SET NX PX，10 秒自愈；业务本身 < 1 秒）
    lock_key = check_lock_key(item_id, dk)
    lock_value = uuid.uuid4().hex
    acquired = await redis_client.set(lock_key, lock_value, nx=True, px=10000)
    if not acquired:
        raise AppException(409, "打卡处理中，请勿重复提交")

    try:
        # Cache Aside 写路径：先删除 streak 缓存，再写数据库；下次读时回填
        await redis_client.delete(streak_key(item_id))

        try:
            session.add(CheckRecord(item_id=item_id, check_date=today))
            # flush 触发唯一索引校验：并发重复写入在这里抛 IntegrityError
            await session.flush()

            dates = await fetch_check_dates(session, item_id)
            new_streak = compute_streak(dates, today)
            item.current_streak = new_streak
            item.max_streak = max(item.max_streak or 0, new_streak)
            await session.commit()
        except IntegrityError:
            # 第三层兜底：唯一冲突 -> 回滚 -> 业务提示，不向上抛 500
            await session.rollback()
            await redis_client.set(
                marker_key, "1", ex=timeutil.seconds_to_midnight()
            )
            raise AppException(409, "今日已打卡")

        # 写后置：事务提交成功后再写当日标记，失败只会退化一次回源，不产生脏数据
        await redis_client.set(marker_key, "1", ex=timeutil.seconds_to_midnight())

        return {
            "item_id": item_id,
            "check_date": today.isoformat(),
            "current_streak": new_streak,
            "max_streak": item.max_streak,
            "today_checked": True,
        }
    finally:
        # 原子释放锁：只删自己持有的锁
        try:
            await redis_client.eval(LOCK_RELEASE_LUA, 1, lock_key, lock_value)
        except Exception:
            logger.exception("释放打卡锁失败 lock_key=%s", lock_key)


async def get_streak(session: AsyncSession, user_id: int, item_id: int) -> dict:
    from app.service.streak_service import get_display_streak

    item = await get_owned_item(session, user_id, item_id)
    today = timeutil.today_bj()
    today_checked = await is_checked_today(session, item_id, today)
    display_streak = await get_display_streak(session, item, today)
    last_check_date = await session.scalar(
        select(func.max(CheckRecord.check_date)).where(
            CheckRecord.item_id == item_id
        )
    )
    return {
        "item_id": item_id,
        "current_streak": display_streak,
        "max_streak": item.max_streak,
        "today_checked": today_checked,
        "last_check_date": last_check_date.isoformat() if last_check_date else None,
    }
