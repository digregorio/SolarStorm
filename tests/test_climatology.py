import datetime as dt

import polars as pl

from solarstorm.baselines._climatology import fit_climatology


def _make_label_rows(dates_and_temps: list[tuple[dt.date, int]]) -> pl.DataFrame:
    return pl.DataFrame([
        {"date_local": d, "tmax_int": t, "day_complete": True}
        for d, t in dates_and_temps
    ])


def test_fit_climatology_doy_smoothing():
    """SH sinusoidal pattern: summer (Jan) warm ~30°C, winter (Jul) cold ~10°C."""
    rows = []
    for doy in range(1, 366):
        d = dt.date(2022, 1, 1) + dt.timedelta(days=doy - 1)
        t = round(20 - 10 * __import__("math").sin((doy - 80) * 2 * 3.14159 / 365))
        rows.append((d, t))
    labels = _make_label_rows(rows)
    climo = fit_climatology(
        labels,
        train_start=dt.date(2022, 1, 1),
        train_end=dt.date(2022, 12, 31),
    )
    # Summer (Jan~Feb) should be warmer than winter (Jul)
    jan_mean = climo.tmax_dec_for(dt.date(2023, 1, 15))
    jul_mean = climo.tmax_dec_for(dt.date(2023, 7, 15))
    assert jan_mean > jul_mean


def test_fit_climatology_monthly_percentiles():
    rows = []
    for doy in range(1, 366):
        d = dt.date(2021, 1, 1) + dt.timedelta(days=doy - 1)
        rows.append((d, 20))
    labels = _make_label_rows(rows)
    climo = fit_climatology(
        labels,
        train_start=dt.date(2021, 1, 1),
        train_end=dt.date(2021, 12, 31),
    )
    p10, p90 = climo.percentiles_for(dt.date(2023, 6, 15), p_low=0.1, p_high=0.9)
    assert p10 <= 20 <= p90


def test_fit_climatology_rejects_short_train_window():
    labels = _make_label_rows([(dt.date(2022, 1, 1), 20)])
    try:
        fit_climatology(
            labels,
            train_start=dt.date(2022, 1, 1),
            train_end=dt.date(2022, 1, 1),
        )
        assert False, "should have raised"
    except ValueError:
        pass
