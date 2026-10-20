"""打卡项业务：创建、列表、归属校验。"""
import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common import timeutil
from app.common.exceptions import AppException
from app.common.redis_keys import check_today_key
from app.db.redis import redis_client
from app.models.check_item import CheckItem
from app.models.check_record import CheckRecord
from app.service.streak_service import get_display_streak

logger = logging.getLogger(__name__)


async def get_owned_item(
    session: AsyncSession, user_id: int, item_id: int
) -> CheckItem:
    """校验打卡项存在且属于当前用户（防越权 IDOR）。

    “不存在”与“不属于你”统一提示，避免泄露他人资源是否存在。
    """
    item = await session.get(CheckItem, item_id)
    if item is None or item.user_id != user_id:
        raise AppException(400, "打卡项不存在")
    return item


def serialize_item(
    item: CheckItem, today_checked: bool, current_streak: int
) -> dict:
    return {
        "id": item.id,
        "item_name": item.item_name,
        "current_streak": current_streak,
        "max_streak": item.max_streak,
        "today_checked": today_checked,
        "create_time": item.create_time.strftime("%Y-%m-%d %H:%M:%S")
        if item.create_time
        else None,
    }


async def create_item(
    session: AsyncSession, user_id: int, item_name: str
) -> dict:
    item = CheckItem(
        user_id=user_id, item_name=item_name, current_streak=0, max_streak=0
    )
    session.add(item)
    try:
        await session.commit()
    except IntegrityError:
        # uk_user_item 联合唯一索引兜底：并发创建同名项也只会成功一条
        await session.rollback()
        raise AppException(400, "打卡项名称已存在")
    await session.refresh(item)
    return serialize_item(item, False, 0)


async def list_items(session: AsyncSession, user_id: int) -> dict:
    items = (
        await session.execute(
            select(CheckItem)
            .where(CheckItem.user_id == user_id)
            .order_by(CheckItem.id)
        )
    ).scalars().all()

    today = timeutil.today_bj()
    dk = timeutil.date_key(today)

    # 当日状态：先 MGET 批量读缓存，未命中的再回源查记录表并回填
    keys = [check_today_key(item.id, dk) for item in items]
    values = await redis_client.mget(keys) if keys else []
    checked: dict[int, bool] = {}
    missing_ids: list[int] = []
    for item, value in zip(items, values):
        if value == "1":
            checked[item.id] = True
        elif value is None:
            missing_ids.append(item.id)

    if missing_ids:
        rows = await session.execute(
            select(CheckRecord.item_id).where(
                CheckRecord.item_id.in_(missing_ids),
                CheckRecord.check_date == today,
            )
        )
        present_ids = {row[0] for row in rows}
        ttl = timeutil.seconds_to_midnight()
        for item_id in missing_ids:
            if item_id in present_ids:
                checked[item_id] = True
                # 读时回填：未命中不等于未打卡，回源查到后写入缓存
                await redis_client.set(check_today_key(item_id, dk), "1", ex=ttl)
            else:
                checked[item_id] = False

    result = []
    for item in items:
        display_streak = await get_display_streak(session, item, today)
        result.append(serialize_item(item, checked.get(item.id, False), display_streak))

    return {"server_date": today.isoformat(), "items": result}
