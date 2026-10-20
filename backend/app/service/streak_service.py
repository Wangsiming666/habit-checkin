"""连续天数计算与 streak 缓存。

核心规则：逐天校验，禁止日期差公式。
- 今日已打卡：从今天开始往前数；
- 今日未打卡：从昨天开始往前数；
- 遇到第一个缺口立即停止；
- 今日、昨日都无记录 -> 展示为 0（断签）。
跨月、跨年由 timedelta 自动处理。
"""
import json
import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.redis_keys import streak_key
from app.db.redis import redis_client
from app.models.check_item import CheckItem
from app.models.check_record import CheckRecord

logger = logging.getLogger(__name__)
STREAK_CACHE_TTL = 86400  # 24 小时；跨日正确性由 value 里的 as_of 校验保证


def compute_streak(dates: set[date], today: date) -> int:
    """逐天校验连续打卡天数（纯函数，单元测试直接覆盖）。"""
    cursor = today if today in dates else today - timedelta(days=1)
    if cursor not in dates:
        return 0
    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


async def fetch_check_dates(session: AsyncSession, item_id: int) -> set[date]:
    """一条 SQL 取回全部打卡日期，内存集合逐天倒推，避免逐日查库。"""
    rows = await session.execute(
        select(CheckRecord.check_date).where(CheckRecord.item_id == item_id)
    )
    return {row[0] for row in rows}


async def get_display_streak(
    session: AsyncSession, item: CheckItem, today: date
) -> int:
    """读取展示口径的连续天数：缓存 -> 回源重算 -> 回填。

    缓存 value 带 as_of 日期：命中但 as_of 不是今天，说明已跨日，
    必须回源重算（纯 24h TTL 会让“昨天连续 5 天、今天断签”在零点后继续显示 5）。
    回源发现库里的 current_streak 与展示值不一致时，懒修复入库。
    """
    cached = await redis_client.get(streak_key(item.id))
    if cached:
        try:
            payload = json.loads(cached)
            if payload.get("as_of") == today.isoformat():
                return int(payload["streak"])
        except (ValueError, KeyError, TypeError):
            logger.warning("streak 缓存格式异常，item_id=%s", item.id)

    dates = await fetch_check_dates(session, item.id)
    streak = compute_streak(dates, today)
    if item.current_streak != streak:
        # 存储口径 = 截至最后一次打卡；展示口径按今天重算。不一致时懒修复。
        item.current_streak = streak
        await session.commit()

    await redis_client.set(
        streak_key(item.id),
        json.dumps({"streak": streak, "as_of": today.isoformat()}),
        ex=STREAK_CACHE_TTL,
    )
    return streak
