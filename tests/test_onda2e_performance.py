from __future__ import annotations

import datetime as dt

import polars as pl

import solarstorm.onda2e._atlas as atlas
import solarstorm.onda2e._cooling as cooling


def test_cooling_domain_reuses_prerequisite_cooling_classifications(monkeypatch):
    d1 = dt.date(2025, 1, 1)
    d2 = dt.date(2025, 1, 2)
    features = pl.DataFrame(
        [
            {"date_local": d1, "cp": "20:00", "regime_label": "southerly_disrupted"},
            {"date_local": d2, "cp": "20:00", "regime_label": "standard_nw"},
        ]
    )
    labels = pl.DataFrame(
        [
            {"date_local": d1, "tmax_int": 19, "tmax_hour": 11, "k_cp__cp_2000": 18},
            {"date_local": d2, "tmax_int": 26, "tmax_hour": 15, "k_cp__cp_2000": 20},
        ]
    )
    obs = pl.DataFrame(
        [
            {
                "date_local": d1,
                "valid": dt.datetime(2025, 1, 1, 0, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 0),
                "tmp_c_int": 18,
                "dwp_c_int": 12,
                "drct": 180.0,
                "sknt": 18.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d1,
                "valid": dt.datetime(2025, 1, 1, 1, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 1, 1),
                "tmp_c_int": 15,
                "dwp_c_int": 13,
                "drct": 190.0,
                "sknt": 20.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d2,
                "valid": dt.datetime(2025, 1, 2, 0, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 2, 0),
                "tmp_c_int": 16,
                "dwp_c_int": 10,
                "drct": 350.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
            {
                "date_local": d2,
                "valid": dt.datetime(2025, 1, 2, 3, tzinfo=dt.UTC),
                "ts_local": dt.datetime(2025, 1, 2, 3),
                "tmp_c_int": 9,
                "dwp_c_int": 10,
                "drct": 20.0,
                "sknt": 3.0,
                "p01i": 0.0,
                "dq_tmp_c_int": "ok",
            },
        ]
    )

    classify_calls = 0
    original = atlas._classify_cooling_mechanism

    def counted(slice_df: pl.DataFrame) -> dict:
        nonlocal classify_calls
        classify_calls += 1
        return original(slice_df)

    monkeypatch.setattr(atlas, "_classify_cooling_mechanism", counted)
    monkeypatch.setattr(cooling, "_classify_cooling_mechanism", counted, raising=False)

    atlas.build_prerequisite_artifacts(features, labels, obs=obs, tz_name="UTC")
    artifacts = cooling.build_cooling_domain_artifacts(features, labels, obs, tz_name="UTC")

    events = artifacts["cooling_event_taxonomy_by_day_cp"]
    assert set(events.get_column("cooling_mechanism")) == {
        "radiative_pre_dawn",
        "southerly_frontal",
    }
    assert classify_calls == features.height
