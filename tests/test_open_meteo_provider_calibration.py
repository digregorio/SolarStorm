from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
import pytest

from solarstorm.open_meteo import (
    PRODUCTION_STATUS,
    build_provider_calibrated_candidates,
    build_provider_calibration_artifacts,
    collapse_provider_family_predictions,
    write_provider_calibration_artifacts,
)


def _provider_features() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for index, date_local in enumerate(
        [dt.date(2024, 1, 1), dt.date(2024, 1, 2), dt.date(2024, 1, 3)],
        start=1,
    ):
        actual = 16.0 + index
        for model, family, offset in [
            ("gfs_seamless", "NOAA_GFS", -2.0),
            ("icon_seamless", "DWD_ICON", -2.0),
            ("ecmwf_ifs025", "ECMWF_IFS", -1.0),
        ]:
            rows.append(
                {
                    "date_local": date_local,
                    "cp": "23:00",
                    "endpoint": "previous_runs",
                    "model": model,
                    "provider": model.split("_")[0].upper(),
                    "provider_family": family,
                    "om_provider_tmax_pred_c": actual + offset,
                    "production_status": PRODUCTION_STATUS,
                }
            )
    return pl.DataFrame(rows, strict=False)


def _labels() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {"date_local": dt.date(2024, 1, 1), "tmax_int": 17},
            {"date_local": dt.date(2024, 1, 2), "tmax_int": 18},
            {"date_local": dt.date(2024, 1, 3), "tmax_int": 19},
        ]
    )


def _assignments() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2024, 1, 1),
                "cp": "23:00",
                "binary_macro_regime_label": "macro_non_southerly",
            },
            {
                "date_local": dt.date(2024, 1, 2),
                "cp": "23:00",
                "binary_macro_regime_label": "macro_southerly_flow",
            },
            {
                "date_local": dt.date(2024, 1, 3),
                "cp": "23:00",
                "binary_macro_regime_label": "macro_non_southerly",
            },
        ]
    )


def test_collapse_provider_family_keeps_one_value_per_family():
    collapsed = collapse_provider_family_predictions(
        [
            {"model": "icon_seamless", "provider_family": "DWD_ICON", "value": 18.0},
            {"model": "icon_d2", "provider_family": "DWD_ICON", "value": 19.0},
            {"model": "gfs_seamless", "provider_family": "NOAA_GFS", "value": 17.5},
        ],
        priority=["icon_d2", "icon_seamless", "gfs_seamless"],
    )

    assert collapsed == {
        "DWD_ICON": {"model": "icon_d2", "value": 19.0},
        "NOAA_GFS": {"model": "gfs_seamless", "value": 17.5},
    }


def test_build_provider_calibrated_candidates_emits_raw_family_rows():
    candidates = build_provider_calibrated_candidates(
        provider_features=_provider_features(),
        labels=_labels(),
        assignments=_assignments(),
        calibration_window_days=30,
        min_bias_samples=2,
        shrinkage_denominator=2,
    )

    raw_mean = candidates.filter(
        (pl.col("date_local") == dt.date(2024, 1, 1))
        & (pl.col("candidate_id") == "om_family_mean_raw")
    ).row(0, named=True)
    gfs = candidates.filter(
        (pl.col("date_local") == dt.date(2024, 1, 1))
        & (pl.col("candidate_id") == "om_gfs_previous_runs_raw")
    ).row(0, named=True)

    assert raw_mean["prediction"] == 15.333333333333334
    assert raw_mean["n_provider_families"] == 3
    assert raw_mean["calibration_status"] == "raw_family_dedup"
    assert gfs["prediction"] == 15.0
    assert set(candidates["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_recent_bias_correction_uses_past_rows_and_shrinkage_without_same_day_leakage():
    candidates = build_provider_calibrated_candidates(
        provider_features=_provider_features(),
        labels=_labels(),
        assignments=_assignments(),
        calibration_window_days=30,
        min_bias_samples=2,
        shrinkage_denominator=2,
    )

    corrected = candidates.filter(
        (pl.col("date_local") == dt.date(2024, 1, 3))
        & (pl.col("candidate_id") == "om_family_recent_bias_corrected")
    ).row(0, named=True)
    fallback = candidates.filter(
        (pl.col("date_local") == dt.date(2024, 1, 1))
        & (pl.col("candidate_id") == "om_family_recent_bias_corrected")
    ).row(0, named=True)

    assert corrected["bias_samples"] == 2
    assert corrected["bias_adjustment"] == pytest.approx(0.8333333333333334)
    assert corrected["prediction"] == pytest.approx(18.166666666666668)
    assert corrected["calibration_status"] == "recent_bias_corrected"
    assert fallback["bias_samples"] == 0
    assert fallback["bias_adjustment"] == 0.0
    assert fallback["calibration_status"] == "fallback_raw_family_mean"


def test_regime_bias_correction_falls_back_when_regime_support_is_insufficient():
    candidates = build_provider_calibrated_candidates(
        provider_features=_provider_features(),
        labels=_labels(),
        assignments=_assignments(),
        calibration_window_days=30,
        min_bias_samples=2,
        min_regime_bias_samples=2,
        shrinkage_denominator=2,
    )

    raw = candidates.filter(
        (pl.col("date_local") == dt.date(2024, 1, 3))
        & (pl.col("candidate_id") == "om_family_mean_raw")
    ).row(0, named=True)
    regime = candidates.filter(
        (pl.col("date_local") == dt.date(2024, 1, 3))
        & (pl.col("candidate_id") == "om_family_regime_bias_corrected")
    ).row(0, named=True)

    assert regime["prediction"] == raw["prediction"]
    assert regime["bias_samples"] == 1
    assert regime["calibration_status"] == "fallback_insufficient_regime_support"


def test_month_and_season_bias_candidates_include_bucket_metadata():
    candidates = build_provider_calibrated_candidates(
        provider_features=_provider_features(),
        labels=_labels(),
        assignments=_assignments(),
        calibration_window_days=30,
        min_bias_samples=2,
        min_month_bias_samples=2,
        min_season_bias_samples=2,
        shrinkage_denominator=2,
    )

    month = candidates.filter(
        (pl.col("date_local") == dt.date(2024, 1, 3))
        & (pl.col("candidate_id") == "om_family_month_bias_corrected")
    ).row(0, named=True)
    season = candidates.filter(
        (pl.col("date_local") == dt.date(2024, 1, 3))
        & (pl.col("candidate_id") == "om_family_season_bias_corrected")
    ).row(0, named=True)
    first_month = candidates.filter(
        (pl.col("date_local") == dt.date(2024, 1, 1))
        & (pl.col("candidate_id") == "om_family_month_bias_corrected")
    ).row(0, named=True)

    assert month["calibration_bucket_type"] == "month"
    assert month["calibration_bucket"] == "01"
    assert month["bias_samples"] == 2
    assert month["calibration_status"] == "month_bias_corrected"
    assert month["fallback_reason"] == ""
    assert season["calibration_bucket_type"] == "season"
    assert season["calibration_bucket"] == "DJF"
    assert season["calibration_status"] == "season_bias_corrected"
    assert first_month["fallback_reason"] == "insufficient_month_support"
    assert candidates.select(["date_local", "cp", "candidate_id"]).is_unique().all()


def test_provider_calibration_artifacts_include_stabilized_support_audit():
    artifacts = build_provider_calibration_artifacts(
        provider_features=_provider_features(),
        labels=_labels(),
        assignments=_assignments(),
        calibration_window_days=30,
        min_bias_samples=2,
        min_month_bias_samples=2,
        min_season_bias_samples=2,
        shrinkage_denominator=2,
    )

    support = artifacts["open_meteo_stabilized_calibration_support_v1"]

    assert {
        "candidate_id",
        "slice_type",
        "slice_name",
        "fallback_pct",
        "support_warning",
        "adjustment_warning",
        "production_status",
    }.issubset(support.columns)
    assert {
        "om_family_month_bias_corrected",
        "om_family_season_bias_corrected",
    }.issubset(set(support["candidate_id"].to_list()))
    assert set(support["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_provider_calibration_artifacts_include_metrics_decision_and_report_files(
    tmp_path: Path,
):
    artifacts = build_provider_calibration_artifacts(
        provider_features=_provider_features(),
        labels=_labels(),
        assignments=_assignments(),
        calibration_window_days=30,
        min_bias_samples=2,
        shrinkage_denominator=2,
    )

    paths = write_provider_calibration_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 10),
    )

    metrics = artifacts["open_meteo_provider_calibrated_candidate_metrics_v1"]
    decision = artifacts["open_meteo_provider_calibration_decision_v1"].row(
        0,
        named=True,
    )

    assert "om_family_recent_bias_corrected" in metrics["candidate_id"].to_list()
    assert "open_meteo_stabilized_calibration_support_v1" in artifacts
    assert decision["production_status"] == PRODUCTION_STATUS
    assert paths["open_meteo_provider_calibrated_candidates_parquet"].exists()
    assert paths["open_meteo_stabilized_calibration_support_v1"].exists()
    assert paths["open_meteo_provider_calibration_report_md"].exists()
