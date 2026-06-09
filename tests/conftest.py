"""Shared test fixtures."""
import datetime as dt

import polars as pl
import pytest


@pytest.fixture
def sample_obs_calm_day() -> pl.DataFrame:
    """A calm winter day: T rises gently to 15°C at 14:00 local, then eases off.

    Hourly NZST observations across the full local daytime of 2025-06-15
    (06:00-19:00 local). A single local date with full intraday coverage so
    ``day_complete`` is satisfied and the Tmax peak lands in the afternoon.
    """
    nzst = dt.timezone(dt.timedelta(hours=12))
    rows = []
    for local_hour in range(0, 24):  # full day 2025-06-15
        if local_hour < 6:
            t = 8.0  # stable overnight
        elif local_hour < 14:
            t = 8 + local_hour * 0.5  # morning warming
        else:
            t = 15 - (local_hour - 14) * 0.4  # afternoon cooling
        ts = dt.datetime(2025, 6, 15, local_hour, 0, 0, tzinfo=nzst)
        rows.append({
            "valid": ts,
            "metar": f"NZWN {ts:%d%H%M}Z AUTO 36005KT 9999 FEW020 {round(t):02d}/08 Q1020",
            "tmpf": t * 9/5 + 32,
            "dwpf": 46.0, "sknt": 5.0, "drct": 360.0, "alti": 30.12, "p01i": 0.0,
            "tmp_c_int": round(t),
            "dwp_c_int": 8,
            "dq_tmp_c_int": "ok",
        })
    return pl.DataFrame(rows)
