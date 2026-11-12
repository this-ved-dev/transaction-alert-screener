"""Business-day roll-forward (TRA-21)."""

from datetime import date

from screener.calendar import business_day, is_business_day, load_holidays


def test_saturday_rolls_to_monday():
    assert business_day(date(2023, 7, 15)) == date(2023, 7, 17)  # Saturday → Monday


def test_sunday_rolls_to_monday():
    assert business_day(date(2023, 7, 16)) == date(2023, 7, 17)


def test_independence_day_2023_rolls_to_next_weekday():
    # 2023-07-04 is Tuesday and a holiday → 2023-07-05
    assert date(2023, 7, 4) in load_holidays()
    assert business_day(date(2023, 7, 4)) == date(2023, 7, 5)


def test_weekday_unchanged():
    assert business_day(date(2023, 7, 14)) == date(2023, 7, 14)
    assert is_business_day(date(2023, 7, 14))
    assert not is_business_day(date(2023, 7, 15))
