"""Redis key 统一定义，禁止业务代码散落字符串拼接。

| key | 用途 | TTL | 理由 |
|---|---|---|---|
| login:token:{token} | 登录态 | 7 天 | 每请求鉴权，高频读，不该压 MySQL |
| check:today:{item_id}:{YYYYMMDD} | 当日打卡标记 | 到北京零点 | 列表页高频查今日状态，可用 MGET 批量取 |
| streak:{item_id} | 连续天数缓存（带 as_of） | 24 小时 | 回源需遍历历史，计算昂贵 |
| lock:check:{item_id}:{YYYYMMDD} | 打卡分布式锁 | 10 秒 | 多 worker/多实例互斥，前置保护数据库 |
"""


def login_token_key(token: str) -> str:
    return f"login:token:{token}"


def check_today_key(item_id: int, date_key_str: str) -> str:
    return f"check:today:{item_id}:{date_key_str}"


def streak_key(item_id: int) -> str:
    return f"streak:{item_id}"


def check_lock_key(item_id: int, date_key_str: str) -> str:
    return f"lock:check:{item_id}:{date_key_str}"
