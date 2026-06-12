from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.open_meteo import (
    ONDA3_OPEN_METEO_NESTED_FILENAMES,
    ONDA3_OPEN_METEO_PILOT_FILENAMES,
    PRODUCTION_STATUS,
    build_open_meteo_nested_validation,
    build_open_meteo_pilot,
    join_open_meteo_features,
    write_open_meteo_nested_validation_artifacts,
    write_open_meteo_pilot_artifacts,
)


def _local_matrix() -> pl.DataFrame:
    rows = []
    for year in [2022, 2023, 2024]:
        for day in range(1, 7):
            date_local = dt.date(year, 7, day)
            for cp in ["22:00", "23:00"]:
                base = 12.0 + day + (year - 2022) * 0.2
                om_signal = 0.5 if cp == "23:00" else 0.0
                rows.append(
                    {
                        "date_local": date_local,
                        "cp": cp,
                        "tmax_int": round(base + om_signal),
                        "k_cp": base - 1.0,
                        "slope_3h": 0.1 * day,
                        "dewpoint_depression": 3.0 + day,
                        "binary_macro_regime_label": (
                            "macro_non_southerly"
                            if day % 2
                            else "macro_southerly_flow"
                        ),
                    }
                )
    return pl.DataFrame(rows)


def _om_features() -> pl.DataFrame:
    rows = []
    for row in _local_matrix().iter_rows(named=True):
        if row["date_local"].year < 2023:
            continue
        rows.append(
            {
                "date_local": row["date_local"],
                "cp": row["cp"],
                "om_prev_d1_temp_23_local_c": float(row["tmax_int"]),
                "om_prev_d1_remaining_warming_c": (
                    0.5 if row["cp"] == "22:00" else 0.0
                ),
                "om_prev_d1_foehn_support": 2.0,
                "om_prev_d1_stratus_support": 1.0,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows)


def _om_features_for_nested() -> pl.DataFrame:
    return _om_features().vstack(
        pl.DataFrame(
            [
                {
                    "date_local": row["date_local"],
                    "cp": row["cp"],
                    "om_prev_d1_temp_23_local_c": float(row["tmax_int"]),
                    "om_prev_d1_remaining_warming_c": (
                        0.5 if row["cp"] == "22:00" else 0.0
                    ),
                    "om_prev_d1_foehn_support": 2.0,
                    "om_prev_d1_stratus_support": 1.0,
                    "production_status": PRODUCTION_STATUS,
                }
                for row in _local_matrix()
                .filter(pl.col("date_local").dt.year() == 2022)
                .iter_rows(named=True)
            ]
        )
    )


def test_join_open_meteo_features_keeps_only_covered_rows():
    joined = join_open_meteo_features(_local_matrix(), _om_features())

    assert joined.height == _om_features().height
    assert set(joined["date_local"].dt.year().to_list()) == {2023, 2024}
    assert "om_prev_d1_temp_23_local_c" in joined.columns
    assert "k_cp" in joined.columns


def test_build_open_meteo_pilot_compares_local_and_augmented_on_same_rows():
    artifacts = build_open_meteo_pilot(
        local_features=_local_matrix(),
        open_meteo_features=_om_features(),
        test_years=[2024],
        numeric_feature_columns=["k_cp", "slope_3h", "dewpoint_depression"],
        categorical_feature_columns=["binary_macro_regime_label"],
        open_meteo_numeric_columns=[
            "om_prev_d1_temp_23_local_c",
            "om_prev_d1_remaining_warming_c",
        ],
    )

    results = artifacts["onda3_open_meteo_pilot_model_results_v1"]
    decision = artifacts["onda3_open_meteo_pilot_decision_update_v1"].row(
        0,
        named=True,
    )
    predictions = artifacts["onda3_open_meteo_pilot_predictions_v1"]

    assert set(results["candidate_id"].to_list()) == {
        "local_only_reference",
        "open_meteo_augmented",
    }
    by_candidate = {row["candidate_id"]: row for row in results.iter_rows(named=True)}
    assert by_candidate["local_only_reference"]["n_train"] == (
        by_candidate["open_meteo_augmented"]["n_train"]
    )
    assert by_candidate["local_only_reference"]["n_test"] == (
        by_candidate["open_meteo_augmented"]["n_test"]
    )
    assert decision["decision_status"] in {
        "KEEP_LOCAL_ONLY_REFERENCE",
        "KEEP_OPEN_METEO_IN_EXPERIMENT_REVIEW",
        "PROMOTE_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION",
    }
    assert decision["production_status"] == PRODUCTION_STATUS
    assert set(predictions["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_build_open_meteo_pilot_blocks_when_coverage_has_no_train_test_fold():
    local = _local_matrix().filter(pl.col("date_local") == dt.date(2024, 7, 1))
    om = _om_features().filter(pl.col("date_local") == dt.date(2024, 7, 1))

    artifacts = build_open_meteo_pilot(
        local_features=local,
        open_meteo_features=om,
        test_years=[2024],
        numeric_feature_columns=["k_cp"],
        categorical_feature_columns=[],
        open_meteo_numeric_columns=["om_prev_d1_temp_23_local_c"],
    )

    decision = artifacts["onda3_open_meteo_pilot_decision_update_v1"].row(
        0,
        named=True,
    )
    assert decision["decision_status"] == "BLOCK_OPEN_METEO_BY_AVAILABILITY"
    assert decision["decision_rationale"] == (
        "Open-Meteo coverage did not contain enough train/test rows for the "
        "requested pilot folds."
    )


def test_build_open_meteo_nested_validation_uses_validation_year_before_test():
    artifacts = build_open_meteo_nested_validation(
        local_features=_local_matrix(),
        open_meteo_features=_om_features_for_nested(),
        test_years=[2024],
        numeric_feature_columns=["k_cp", "slope_3h", "dewpoint_depression"],
        categorical_feature_columns=["binary_macro_regime_label"],
        open_meteo_numeric_columns=[
            "om_prev_d1_temp_23_local_c",
            "om_prev_d1_remaining_warming_c",
        ],
        train_start=dt.date(2022, 1, 1),
    )

    scope = artifacts["onda3_open_meteo_nested_fold_scope_v1"]
    results = artifacts["onda3_open_meteo_nested_model_results_v1"]
    predictions = artifacts["onda3_open_meteo_nested_predictions_v1"]
    selection = artifacts["onda3_open_meteo_nested_selection_v1"].row(0, named=True)

    validation_scope = scope.filter(pl.col("stage") == "validation").row(
        0,
        named=True,
    )
    test_scope = scope.filter(pl.col("stage") == "test").row(0, named=True)

    assert validation_scope["train_end_year"] == 2022
    assert validation_scope["evaluation_year"] == 2023
    assert test_scope["train_end_year"] == 2023
    assert test_scope["evaluation_year"] == 2024
    assert set(results["stage"].to_list()) == {"validation", "test"}
    assert set(results["candidate_id"].to_list()) == {
        "local_only_onda3f",
        "open_meteo_augmented_onda3f",
    }
    assert selection["outer_test_year"] == 2024
    assert selection["selected_candidate_id"] in {
        "local_only_onda3f",
        "open_meteo_augmented_onda3f",
    }
    assert set(predictions["production_status"].to_list()) == {PRODUCTION_STATUS}
    assert "exact_bracket" in predictions.columns


def test_write_open_meteo_pilot_artifacts_creates_csvs_and_report(tmp_path: Path):
    artifacts = build_open_meteo_pilot(
        local_features=_local_matrix(),
        open_meteo_features=_om_features(),
        test_years=[2024],
        numeric_feature_columns=["k_cp", "slope_3h", "dewpoint_depression"],
        categorical_feature_columns=["binary_macro_regime_label"],
        open_meteo_numeric_columns=["om_prev_d1_temp_23_local_c"],
    )

    paths = write_open_meteo_pilot_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 10),
    )

    for key, filename in ONDA3_OPEN_METEO_PILOT_FILENAMES.items():
        assert paths[key] == tmp_path / filename
        assert paths[key].exists()
    report = paths["onda3_open_meteo_pilot_report_md"].read_text(encoding="utf-8")
    assert "Open-Meteo augmented candidate" in report
    assert "EXPERIMENT_ONLY" in report


def test_write_open_meteo_nested_validation_artifacts_creates_csvs_and_report(
    tmp_path: Path,
):
    artifacts = build_open_meteo_nested_validation(
        local_features=_local_matrix(),
        open_meteo_features=_om_features_for_nested(),
        test_years=[2024],
        numeric_feature_columns=["k_cp", "slope_3h", "dewpoint_depression"],
        categorical_feature_columns=["binary_macro_regime_label"],
        open_meteo_numeric_columns=["om_prev_d1_temp_23_local_c"],
        train_start=dt.date(2022, 1, 1),
    )

    paths = write_open_meteo_nested_validation_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 10),
    )

    for key, filename in ONDA3_OPEN_METEO_NESTED_FILENAMES.items():
        assert paths[key] == tmp_path / filename
        assert paths[key].exists()
    report = paths["onda3_open_meteo_nested_report_md"].read_text(encoding="utf-8")
    assert "Onda 3 Open-Meteo Nested Validation Report" in report
    assert "EXPERIMENT_ONLY" in report
