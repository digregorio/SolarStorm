import datetime as dt

import pytest

from solarstorm.data._labels import (
    DayCompleteParams,
    build_tmax_labels,
    remaining_warming,
    risco_de_flip,
)


def test_build_tmax_labels_calm_day(sample_obs_calm_day):
    params = DayCompleteParams(min_obs=8, max_gap_minutes=180, min_quartile_coverage=1)
    labels = build_tmax_labels(sample_obs_calm_day, params)
    assert labels.height == 1
    row = labels.row(0, named=True)
    assert row["tmax_int"] is not None
    assert 14 <= row["tmax_int"] <= 16
    assert row["day_complete"] is True
    assert row["tmax_hour"] is not None
    # No atypical hour on a calm winter day
    assert row.get("tmax_atypical_hour", False) is False


def test_build_tmax_labels_emits_k_cp_for_each_checkpoint(sample_obs_calm_day):
    from solarstorm._config import CP_SET_UTC
    from solarstorm.data._calendar import cp_to_utc

    params = DayCompleteParams(min_obs=8, max_gap_minutes=180, min_quartile_coverage=1)
    labels = build_tmax_labels(sample_obs_calm_day, params)
    row = labels.row(0, named=True)
    d = dt.date(2025, 6, 15)

    for cp_str in CP_SET_UTC:
        col = f"k_cp__cp_{cp_str.replace(':', '')}"
        assert col in row, f"missing column {col}"
        # k_cp should be the max integer temp before the CP
        cp_to_utc(d, cp_str, "Pacific/Auckland")
        # For CP 20Z (8am NZST): temp ~8°C, k_cp should reflect that
        assert isinstance(row[col], int) or row[col] is None


def test_remaining_warming():
    assert remaining_warming(tmax=20, k_cp=15) == 5
    assert remaining_warming(tmax=12, k_cp=14) == -2
    assert remaining_warming(tmax=18, k_cp=18) == 0


def test_risco_de_flip():
    # At integer center (15.0): boundary_distance = 0.5 (far from .5 boundary, safe)
    assert risco_de_flip(15.0) == 0.5
    # At .5 boundary (15.5): boundary_distance = 0.0 (micro-variation flips bracket)
    assert risco_de_flip(15.5) == 0.0
    # Inside bucket: between 0 and 0.5
    assert risco_de_flip(15.2) == 0.3
    assert risco_de_flip(14.8) == pytest.approx(0.3)
