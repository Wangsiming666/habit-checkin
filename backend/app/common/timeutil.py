"""北京时间工具：服务端唯一日期权威。

容器默认 UTC，禁止裸用 datetime.now()；所有打卡日期统一由本模块生成。
上海 1991 年后无夏令时，仍用 zoneinfo 表达 "Asia/Shanghai" 语义。
Windows 环境需安装 tzdata，否则 zoneinfo 找不到时区库会直接抛异常。
"""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")


def now_bj() -> datetime:
    return datetime.now(TZ)


def today_bj() -> date:
    return now_bj().date()


def date_key(d: date | None = None) -> str:
    """缓存/锁 key 的日期后缀，保证 23:59:59 与 00:00:01 分属两天。"""
    return (d or today_bj()).strftime("%Y%m%d")


def seconds_to_midnight(now: datetime | None = None) -> int:
    """到北京时间次日零点的剩余秒数（最小 1 秒），用于当日缓存 TTL。"""
    now = now or now_bj()
    if now.tzinfo is None:
        now = now.replace(tzinfo=TZ)
    tomorrow = now.date() + timedelta(days=1)
    next_midnight = datetime.combine(tomorrow, time.min, tzinfo=TZ)
    return max(1, int((next_midnight - now).total_seconds()))
