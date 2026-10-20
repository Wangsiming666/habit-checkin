"""连续天数算法单元测试：覆盖跨天、断签、跨月、跨年、闰年、重复等边界。"""
from datetime import date, timedelta

from app.service.streak_service import compute_streak

TODAY = date(2026, 10, 20)


def d(*args) -> date:
    return date(*args)


def test_today_checked_with_two_previous_days():
    assert compute_streak({d(2026, 10, 20), d(2026, 10, 19), d(2026, 10, 18)}, TODAY) == 3


def test_today_not_checked_counts_from_yesterday():
    assert compute_streak({d(2026, 10, 19), d(2026, 10, 18)}, TODAY) == 2


def test_both_today_and_yesterday_missing_returns_zero():
    assert compute_streak({d(2026, 10, 17)}, TODAY) == 0


def test_gap_of_one_day_stops_counting():
    assert compute_streak({d(2026, 10, 20), d(2026, 10, 19), d(2026, 10, 17)}, TODAY) == 2


def test_cross_month_boundary():
    assert compute_streak({d(2026, 10, 1), d(2026, 9, 30), d(2026, 9, 29)}, d(2026, 10, 1)) == 3


def test_cross_year_boundary():
    assert compute_streak({d(2026, 1, 1), d(2025, 12, 31)}, d(2026, 1, 1)) == 2


def test_leap_year_feb_29():
    dates = {d(2024, 3, 1), d(2024, 2, 29), d(2024, 2, 28)}
    assert compute_streak(dates, d(2024, 3, 1)) == 3


def test_duplicate_dates_do_not_change_streak():
    # set 天然去重；同日重复打卡在业务层被 409 + 唯一索引拦截
    assert compute_streak({d(2026, 10, 20), d(2026, 10, 20), d(2026, 10, 19)}, TODAY) == 2


def test_first_check_ever():
    assert compute_streak({d(2026, 10, 20)}, TODAY) == 1


def test_input_order_irrelevant():
    dates = {d(2026, 10, 18), d(2026, 10, 20), d(2026, 10, 19)}
    assert compute_streak(dates, TODAY) == 3


def test_long_chain_100_days():
    dates = {TODAY - timedelta(days=i) for i in range(100)}
    assert compute_streak(dates, TODAY) == 100


def test_simple_date_diff_would_be_wrong():
    # 反例：最后打卡 10-17，今天 10-20。日期差公式给 4，正确展示应为 0
    assert compute_streak({d(2026, 10, 17)}, TODAY) == 0
