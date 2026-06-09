import datetime as dt
from zoneinfo import ZoneInfo

from solarstorm.data._calendar import cp_to_utc, day_local_window

NZST = ZoneInfo("Pacific/Auckland")
UTC = dt.UTC


def test_day_local_window_standard_day():
    d = dt.date(2025, 6, 15)  # winter, no DST
    start, end = day_local_window(d, "Pacific/Auckland")
    assert start.tzinfo is not None
    assert end.tzinfo is not None
    assert (end - start) == dt.timedelta(hours=24)


def test_cp_to_utc_23z_standard():
    """23:00 UTC on D-1 maps to 11:00 NZST on D."""
    d = dt.date(2025, 6, 15)
    result = cp_to_utc(d, "23:00", "Pacific/Auckland")
    assert result.tzinfo == UTC
    assert result.hour == 23
    # 23:00 UTC on June 14 → 11:00 NZST June 15
    assert result == dt.datetime(2025, 6, 14, 23, 0, 0, tzinfo=UTC)


def test_cp_to_utc_20z_standard():
    """20:00 UTC on D-1 maps to 08:00 NZST on D."""
    d = dt.date(2025, 6, 15)
    result = cp_to_utc(d, "20:00", "Pacific/Auckland")
    assert result.tzinfo == UTC
    assert result.hour == 20
    assert result == dt.datetime(2025, 6, 14, 20, 0, 0, tzinfo=UTC)


def test_cp_to_utc_dst_summer():
    """NZDT (UTC+13): 23:00 UTC D-1 → 12:00 NZDT D."""
    d = dt.date(2025, 1, 15)
    result = cp_to_utc(d, "23:00", "Pacific/Auckland")
    assert result.tzinfo == UTC
    assert result == dt.datetime(2025, 1, 14, 23, 0, 0, tzinfo=UTC)
    assert result.astimezone(NZST).date() == d
    assert result.astimezone(NZST).hour == 12


def test_cp_to_utc_all_four_checkpoints():
    """All 4 contractual CPs map to the correct local morning hours."""
    d = dt.date(2025, 6, 15)
    expected_local = {"20:00": 8, "21:00": 9, "22:00": 10, "23:00": 11}
    for cp_str, expected_hour in expected_local.items():
        utc_dt = cp_to_utc(d, cp_str, "Pacific/Auckland")
        local_dt = utc_dt.astimezone(NZST)
        assert local_dt.date() == d, f"{cp_str}: {local_dt} not on {d}"
        assert local_dt.hour == expected_hour, (
            f"{cp_str}: expected {expected_hour}:00 local, got {local_dt}"
        )
