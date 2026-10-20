"""北京时间与 TTL 计算测试：确保跨零点行为正确。"""
from datetime import date, datetime

from app.common.timeutil import TZ, date_key, seconds_to_midnight


def test_one_second_before_midnight():
    now = datetime(2026, 10, 20, 23, 59, 59, tzinfo=TZ)
    assert seconds_to_midnight(now) == 1


def test_one_second_after_midnight():
    now = datetime(2026, 10, 21, 0, 0, 1, tzinfo=TZ)
    assert seconds_to_midnight(now) == 86399


def test_noon_ttl_is_half_day():
    now = datetime(2026, 10, 20, 12, 0, 0, tzinfo=TZ)
    assert seconds_to_midnight(now) == 43200


def test_ttl_is_never_zero():
    now = datetime(2026, 10, 20, 23, 59, 59, 999999, tzinfo=TZ)
    assert seconds_to_midnight(now) >= 1


def test_date_key_format():
    assert date_key(date(2026, 10, 20)) == "20261020"


def test_midnight_belongs_to_new_day():
    before = datetime(2026, 10, 20, 23, 59, 59, tzinfo=TZ)
    after = datetime(2026, 10, 21, 0, 0, 0, tzinfo=TZ)
    assert date_key(before.date()) != date_key(after.date())
