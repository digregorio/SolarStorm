"""Tests for the narrow live empirical panel fast path."""

from __future__ import annotations

from datetime import date, datetime, timezone

import polars as pl

from core.features.builder import build_cp_features, build_empirical_panel_fast
from core.baselines.empirical import fit_empirical_conditional

TZ_NAME = "Pacific/Auckland"


def _obs() -> pl.DataFrame:
    rows = [
        ("2026-06-02T19:30:00+00:00", 10),
        ("2026-06-02T20:00:00+00:00", 99),  # exact CP20 for 2026-06-03, must not leak
        ("2026-06-02T20:30:00+00:00", 12),
        ("2026-06-02T21:00:00+00:00", 13),  # exact CP21 for 2026-06-03, must not leak
        ("2026-06-03T19:30:00+00:00", 14),
        ("2026-06-03T20:00:00+00:00", 98),  # exact CP20 for 2026-06-04, must not leak
        ("2026-06-03T20:30:00+00:00", 15),
    ]
    return pl.DataFrame({
        "ts_utc": [
            datetime.fromisoformat(ts).astimezone(timezone.utc)
            for ts, _ in rows
        ],
        "tmp_c_int": [tmp for _, tmp in rows],
        "dq_tmp_c_int": ["ok"] * len(rows),
        "tmpf": [float(tmp) * 9.0 / 5.0 + 32.0 for _, tmp in rows],
        "drct": [180.0] * len(rows),
        "sknt": [10.0] * len(rows),
        "alti": [29.9] * len(rows),
    })


def _labels() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "date_local": [date(2026, 6, 3), date(2026, 6, 4)],
            "tmax_int": [13, 16],
            "tmin_int": [9, 11],
            "day_complete": [True, True],
        },
        schema_overrides={
            "date_local": pl.Date,
            "tmax_int": pl.Int32,
            "tmin_int": pl.Int32,
            "day_complete": pl.Boolean,
        },
    )


def test_build_empirical_panel_fast_matches_cp_features_for_kcp():
    obs = _obs()
    labels = _labels()
    cps = ("20:00", "21:00")
    dates = [date(2026, 6, 3), date(2026, 6, 4)]

    fast = build_empirical_panel_fast(
        obs,
        labels,
        tz_name=TZ_NAME,
        cp_set=cps,
        dates=dates,
    ).sort("date_local")

    for cp in cps:
        col = f"k_cp__cp_{cp[:2]}"
        expected = [
            build_cp_features(
                obs,
                date_local=d,
                cp_hhmm=cp,
                tz_name=TZ_NAME,
                labels=labels,
            ).features["k_cp"]
            for d in dates
        ]
        assert fast[col].to_list() == expected


def test_build_empirical_panel_fast_preserves_left_closed_cp_boundary():
    fast = build_empirical_panel_fast(
        _obs(),
        _labels(),
        tz_name=TZ_NAME,
        cp_set=("20:00", "21:00"),
        dates=[date(2026, 6, 3)],
    )

    assert fast["k_cp__cp_20"].to_list() == [10]
    assert fast["k_cp__cp_21"].to_list() == [99]


def test_fit_empirical_conditional_ignores_incomplete_days():
    panel = pl.DataFrame(
        {
            "date_local": [date(2026, 6, 1), date(2026, 6, 2)],
            "month": [6, 6],
            "tmax_int": [15, 99],
            "day_complete": [True, False],
            "k_cp__cp_20": [14, 14],
        },
        schema_overrides={"date_local": pl.Date},
    )

    empirical = fit_empirical_conditional(
        panel,
        train_window=(date(2026, 6, 1), date(2026, 6, 3)),
        n_min_bucket=1,
    )

    assert empirical.cond[(6, "20:00", 14)] == {15: 1}
    assert 99 not in empirical.marginal[(6, "20:00")]
