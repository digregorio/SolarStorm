from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.open_meteo import (
    PRODUCTION_STATUS,
    build_open_meteo_forensics_artifacts,
    write_open_meteo_forensics_artifacts,
)


def _predictions() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    specs = [
        (
            dt.date(2024, 1, 1),
            "23:00",
            "macro_non_southerly",
            20.0,
            20.1,
            19.0,
        ),
        (
            dt.date(2024, 1, 2),
            "23:00",
            "macro_southerly_flow",
            15.0,
            15.9,
            15.1,
        ),
        (
            dt.date(2025, 1, 1),
            "23:00",
            "macro_non_southerly",
            21.0,
            21.1,
            20.0,
        ),
        (
            dt.date(2025, 2, 1),
            "20:00",
            "macro_southerly_flow",
            13.0,
            13.1,
            12.1,
        ),
    ]
    for date_local, cp, regime, actual, augmented, calibrated in specs:
        for candidate_id, prediction in [
            ("open_meteo_augmented_onda3f", augmented),
            ("om_family_recent_bias_corrected", calibrated),
        ]:
            rows.append(
                {
                    "date_local": date_local,
                    "cp": cp,
                    "stage": "test",
                    "outer_test_year": date_local.year,
                    "evaluation_year": date_local.year,
                    "candidate_id": candidate_id,
                    "candidate_label": candidate_id.replace("_", " "),
                    "actual": actual,
                    "prediction": prediction,
                    "absolute_error": abs(actual - prediction),
                    "actual_bracket": int(actual + 0.5),
                    "pred_bracket": int(prediction + 0.5),
                    "exact_bracket": int(actual + 0.5) == int(prediction + 0.5),
                    "month": date_local.strftime("%Y-%m"),
                    "calendar_year": date_local.year,
                    "binary_macro_regime_label": regime,
                    "production_status": PRODUCTION_STATUS,
                }
            )
    return pl.DataFrame(rows, strict=False)


def _candidates() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": dt.date(2024, 1, 1),
                "cp": "23:00",
                "candidate_id": "om_family_recent_bias_corrected",
                "bias_adjustment": -0.8,
                "bias_samples": 30,
                "n_provider_families": 4,
                "calibration_status": "recent_bias_corrected",
                "production_status": PRODUCTION_STATUS,
            },
            {
                "date_local": dt.date(2025, 1, 1),
                "cp": "23:00",
                "candidate_id": "om_family_recent_bias_corrected",
                "bias_adjustment": -1.2,
                "bias_samples": 30,
                "n_provider_families": 5,
                "calibration_status": "recent_bias_corrected",
                "production_status": PRODUCTION_STATUS,
            },
        ],
        strict=False,
    )


def test_open_meteo_forensics_builds_pairwise_delta_slices():
    artifacts = build_open_meteo_forensics_artifacts(
        predictions=_predictions(),
        calibrated_candidates=_candidates(),
    )

    paired = artifacts["open_meteo_forensics_pairwise_rows_v1"]
    slices = artifacts["open_meteo_forensics_slice_delta_v1"]
    decision = artifacts["open_meteo_forensics_decision_v1"].row(0, named=True)

    assert paired.height == 4
    assert {
        "mae_delta_calibrated_minus_augmented",
        "exact_delta_calibrated_minus_augmented_pct",
        "calibrated_wins_mae_pct",
        "augmented_wins_mae_pct",
        "bracket_lost_by_calibration_pct",
    }.issubset(slices.columns)
    overall = slices.filter(pl.col("slice_type") == "overall").row(0, named=True)
    assert overall["n_rows"] == 4
    assert overall["mae_delta_calibrated_minus_augmented"] > 0
    assert overall["exact_delta_calibrated_minus_augmented_pct"] < 0
    assert decision["decision_status"] == "KEEP_OPEN_METEO_FORENSICS_REVIEW"
    assert decision["production_status"] == PRODUCTION_STATUS


def test_write_open_meteo_forensics_artifacts_creates_report(tmp_path: Path):
    artifacts = build_open_meteo_forensics_artifacts(
        predictions=_predictions(),
        calibrated_candidates=_candidates(),
    )

    paths = write_open_meteo_forensics_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 10),
    )

    assert paths["open_meteo_forensics_report_md"].exists()
    report = paths["open_meteo_forensics_report_md"].read_text(encoding="utf-8")
    assert "Open-Meteo OM-M6 Forensic Report" in report
    assert "EXPERIMENT_ONLY" in report
