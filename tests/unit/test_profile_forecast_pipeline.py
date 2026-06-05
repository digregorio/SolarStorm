"""Tests for the Wave 4.1 forecast profiler."""

from __future__ import annotations

import sys
import types
from datetime import date, datetime, timezone
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

import profile_forecast_pipeline as profiler


class _Cfg:
    tz = "Pacific/Auckland"
    cp_set_utc = ["20:00", "21:00", "22:00", "23:00"]

    class tmp_c_int_plausibility:
        min = -10
        max = 40


class _Stats:
    fallback_rate = 0.0


class _Climo:
    def tmax_dec_for(self, d):
        return 15.0


class _Feats:
    cp_utc = datetime(2026, 6, 3, 20, 0, tzinfo=timezone.utc)
    feature_max_ts_utc = datetime(2026, 6, 3, 19, 30, tzinfo=timezone.utc)
    features = {"k_cp": 15}


def _labels() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "date_local": [date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3)],
            "tmax_int": [14, 15, 16],
            "day_complete": [True, True, True],
        },
        schema_overrides={"date_local": pl.Date},
    )


def test_profile_rich_panel_sample_uses_requested_cp_only(monkeypatch):
    captured: list[tuple[str, ...]] = []

    monkeypatch.setattr(profiler, "load_station_config", lambda _: _Cfg())
    monkeypatch.setattr(profiler, "load_observations", lambda *a, **kw: (pl.DataFrame({"x": [1, 2]}), _Stats()))
    monkeypatch.setattr(profiler, "build_tmax_labels", lambda *a, **kw: _labels())
    monkeypatch.setattr(profiler, "build_empirical_panel_fast", lambda *a, **kw: pl.DataFrame({"date_local": [date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3)]}))
    monkeypatch.setattr(profiler, "fit_climatology", lambda *a, **kw: _Climo())
    monkeypatch.setattr(profiler, "fit_empirical_conditional", lambda *a, **kw: types.SimpleNamespace())
    monkeypatch.setattr(profiler, "build_cp_features", lambda *a, **kw: _Feats())

    def _build_training_panel(*a, **kw):
        captured.append(tuple(kw["cp_set"]))
        return pl.DataFrame({"date_local": kw["dates"], "cp": ["22:00"] * len(kw["dates"])})

    monkeypatch.setattr(profiler, "build_training_panel", _build_training_panel)

    report = profiler.profile_pipeline(
        station_yaml=Path("nzwn/config/station.yaml"),
        csv=Path("NZWN.csv"),
        target_date=date(2026, 6, 4),
        cp="22",
        train_start=date(2026, 6, 1),
        train_end=date(2026, 6, 3),
        rich_panel_sample_days=2,
    )

    assert captured == [("22:00",)]
    assert report["ridge_rich_panel_profile"]["sample_days"] == 2
    assert report["ridge_rich_panel_profile"]["sample_rows"] == 2
    assert report["ridge_rich_panel_profile"]["full_train_dates"] == 3
    assert report["target_feature_gap_to_cp_min"] == 30
