from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.open_meteo import (
    PRODUCTION_STATUS,
    build_open_meteo_calibrated_nested_validation,
    write_open_meteo_calibrated_nested_validation_artifacts,
)


def _local_features() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for year in [2022, 2023, 2024, 2025]:
        for day in range(1, 6):
            date_local = dt.date(year, 7, day)
            actual = 14.0 + day + (year - 2022) * 0.3
            for cp in ["22:00", "23:00"]:
                rows.append(
                    {
                        "date_local": date_local,
                        "cp": cp,
                        "tmax_int": round(actual),
                        "k_cp": actual - 1.0,
                        "slope_3h": day * 0.1,
                        "dewpoint_depression": 4.0 + day,
                        "binary_macro_regime_label": (
                            "macro_non_southerly"
                            if day % 2
                            else "macro_southerly_flow"
                        ),
                    }
                )
    return pl.DataFrame(rows, strict=False)


def _calibrated_candidates() -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for row in _local_features().filter(pl.col("date_local").dt.year() >= 2023).iter_rows(named=True):
        actual = float(row["tmax_int"])
        rows.extend(
            [
                {
                    "date_local": row["date_local"],
                    "cp": row["cp"],
                    "candidate_id": "om_gfs_previous_runs_raw",
                    "prediction": actual - 1.0,
                    "n_provider_families": 1,
                    "calibration_status": "raw_gfs",
                    "production_status": PRODUCTION_STATUS,
                },
                {
                    "date_local": row["date_local"],
                    "cp": row["cp"],
                    "candidate_id": "om_family_mean_raw",
                    "prediction": actual - 0.5,
                    "n_provider_families": 3,
                    "calibration_status": "raw_family_dedup",
                    "production_status": PRODUCTION_STATUS,
                },
                {
                    "date_local": row["date_local"],
                    "cp": row["cp"],
                    "candidate_id": "om_family_recent_bias_corrected",
                    "prediction": actual,
                    "n_provider_families": 3,
                    "calibration_status": "recent_bias_corrected",
                    "production_status": PRODUCTION_STATUS,
                },
            ]
        )
    return pl.DataFrame(rows, strict=False)


def _open_meteo_gfs_features() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "date_local": row["date_local"],
                "cp": row["cp"],
                "om_prev_d1_temp_23_local_c": float(row["tmax_int"]),
                "om_prev_d1_remaining_warming_c": 0.25,
                "production_status": PRODUCTION_STATUS,
            }
            for row in _local_features()
            .filter(pl.col("date_local").dt.year() >= 2023)
            .iter_rows(named=True)
        ],
        strict=False,
    )


def test_calibrated_nested_uses_identical_rows_for_all_candidates():
    artifacts = build_open_meteo_calibrated_nested_validation(
        local_features=_local_features(),
        calibrated_candidates=_calibrated_candidates(),
        test_years=[2025],
        train_start=dt.date(2022, 1, 1),
    )

    scope = artifacts["onda3_open_meteo_calibrated_nested_candidate_scope_v1"]
    predictions = artifacts["onda3_open_meteo_calibrated_nested_predictions_v1"]
    test_scope = scope.filter(pl.col("stage") == "test")

    assert test_scope["n_rows"].n_unique() == 1
    assert {
        "local_only_onda3f",
        "om_gfs_previous_runs_raw",
        "om_family_mean_raw",
        "om_family_recent_bias_corrected",
    }.issubset(set(predictions["candidate_id"].to_list()))
    assert set(scope["production_status"].to_list()) == {PRODUCTION_STATUS}
    assert set(predictions["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_calibrated_nested_includes_current_gfs_augmented_onda3f_candidate():
    artifacts = build_open_meteo_calibrated_nested_validation(
        local_features=_local_features(),
        open_meteo_features=_open_meteo_gfs_features(),
        calibrated_candidates=_calibrated_candidates(),
        test_years=[2025],
        train_start=dt.date(2022, 1, 1),
    )

    scope = artifacts["onda3_open_meteo_calibrated_nested_candidate_scope_v1"]
    predictions = artifacts["onda3_open_meteo_calibrated_nested_predictions_v1"]
    decision = artifacts["onda3_open_meteo_calibrated_nested_decision_update_v1"].row(
        0,
        named=True,
    )
    test_scope = scope.filter(pl.col("stage") == "test")

    assert "open_meteo_augmented_onda3f" in predictions["candidate_id"].to_list()
    assert test_scope["n_rows"].n_unique() == 1
    assert "always_open_meteo_augmented_mean_test_mae" in decision


def test_defensive_selector_falls_back_to_augmented_when_non_southerly_degrades():
    local = _local_features()
    candidates = _calibrated_candidates()
    degraded_rows = []
    for row in candidates.iter_rows(named=True):
        if (
            row["candidate_id"].startswith("om_family_")
            and row["date_local"].year == 2024
            and row["date_local"].day in {1, 3, 5}
        ):
            row = {**row, "prediction": float(row["prediction"]) - 3.0}
        degraded_rows.append(row)
    artifacts = build_open_meteo_calibrated_nested_validation(
        local_features=local,
        open_meteo_features=_open_meteo_gfs_features(),
        calibrated_candidates=pl.DataFrame(degraded_rows, strict=False),
        test_years=[2025],
        train_start=dt.date(2022, 1, 1),
        selection_rule="validation_mae_then_non_southerly_guard_then_cp23",
    )

    selection = artifacts["onda3_open_meteo_calibrated_nested_selection_v1"].row(
        0,
        named=True,
    )
    guardrail = artifacts[
        "onda3_open_meteo_defensive_selection_guardrail_v1"
    ].filter(pl.col("candidate_id") == "om_family_recent_bias_corrected")

    assert selection["selected_candidate_id"] == "open_meteo_augmented_onda3f"
    assert selection["selection_rule"] == (
        "validation_mae_then_non_southerly_guard_then_cp23"
    )
    assert guardrail["blocked_by_non_southerly_mae"].any()
    assert set(guardrail["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_calibrated_nested_stays_in_review_when_only_one_outer_fold_is_valid():
    artifacts = build_open_meteo_calibrated_nested_validation(
        local_features=_local_features(),
        calibrated_candidates=_calibrated_candidates(),
        test_years=[2025],
        train_start=dt.date(2022, 1, 1),
    )

    decision = artifacts["onda3_open_meteo_calibrated_nested_decision_update_v1"].row(
        0,
        named=True,
    )
    selection = artifacts["onda3_open_meteo_calibrated_nested_selection_v1"]

    assert selection.height == 1
    assert decision["decision_status"] == (
        "KEEP_CALIBRATED_OPEN_METEO_IN_EXPERIMENT_REVIEW"
    )
    assert decision["n_outer_folds"] == 1
    assert decision["production_status"] == PRODUCTION_STATUS


def test_write_calibrated_nested_artifacts_creates_csvs_and_report(tmp_path: Path):
    artifacts = build_open_meteo_calibrated_nested_validation(
        local_features=_local_features(),
        calibrated_candidates=_calibrated_candidates(),
        test_years=[2025],
        train_start=dt.date(2022, 1, 1),
    )

    paths = write_open_meteo_calibrated_nested_validation_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 10),
    )

    assert paths["onda3_open_meteo_calibrated_nested_report_md"].exists()
    assert (
        paths["onda3_open_meteo_defensive_selection_guardrail_v1"].exists()
    )
    report = paths["onda3_open_meteo_calibrated_nested_report_md"].read_text(
        encoding="utf-8"
    )
    assert "Onda 3 Open-Meteo Calibrated Nested Validation Report" in report
    assert "EXPERIMENT_ONLY" in report
