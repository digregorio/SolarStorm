from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import polars as pl

from solarstorm.onda3._train_start_sensitivity import (
    TrainStartVariant,
    build_onda3_train_start_sensitivity,
    build_train_start_scope,
    filter_matrix_for_train_start,
    write_onda3_train_start_sensitivity_artifacts,
)


def _matrix() -> pl.DataFrame:
    rows = []
    for cp in ("20:00", "21:00", "22:00", "23:00"):
        for year in (2010, 2011, 2012, 2013, 2022, 2023):
            for day in range(1, 4):
                rows.append(
                    {
                        "date_local": dt.date(year, 1, day),
                        "cp": cp,
                        "k_cp": float(day + year - 2000),
                        "foehn_score": float(day * 10),
                        "cloud_cover_suppression": float(4 - day),
                        "binary_macro_regime_label": (
                            "macro_non_southerly"
                            if day % 2
                            else "macro_southerly_flow"
                        ),
                        "tmax_int": float(day + year - 1999),
                    }
                )
    return pl.DataFrame(rows)


def test_filter_matrix_for_train_start_removes_sparse_early_years():
    variant = TrainStartVariant(
        variant_id="continuous_2012_start",
        train_start=dt.date(2012, 1, 1),
    )

    filtered = filter_matrix_for_train_start(_matrix(), variant)

    assert filtered["date_local"].min() == dt.date(2012, 1, 1)
    assert 2010 not in filtered["date_local"].dt.year().unique().to_list()
    assert 2011 not in filtered["date_local"].dt.year().unique().to_list()


def test_build_train_start_scope_reports_train_and_test_periods():
    scope = build_train_start_scope(
        _matrix(),
        variants=[
            TrainStartVariant(
                variant_id="continuous_2012_start",
                train_start=dt.date(2012, 1, 1),
            )
        ],
        test_years=[2023],
    )

    row = scope.row(0, named=True)
    assert row["variant_id"] == "continuous_2012_start"
    assert row["test_year"] == 2023
    assert row["train_period"] == "2012-01-01 to 2022-12-31"
    assert row["test_period"] == "2023-01-01 to 2023-01-03"
    assert row["production_status"] == "EXPERIMENT_ONLY"


def test_build_onda3_train_start_sensitivity_emits_two_variants():
    artifacts = build_onda3_train_start_sensitivity(
        _matrix(),
        test_years=[2023],
        numeric_feature_columns=["k_cp", "foehn_score", "cloud_cover_suppression"],
        categorical_feature_columns=["binary_macro_regime_label"],
        variants=[
            TrainStartVariant("legacy_2009_start", dt.date(2009, 4, 23)),
            TrainStartVariant("continuous_2012_start", dt.date(2012, 1, 1)),
        ],
    )

    results = artifacts["onda3_train_start_model_results_v1"]
    predictions = artifacts["onda3_train_start_predictions_v1"]
    decision = artifacts["onda3_train_start_decision_update_v1"].row(0, named=True)

    assert set(results["variant_id"].to_list()) == {
        "legacy_2009_start",
        "continuous_2012_start",
    }
    assert set(predictions["variant_id"].to_list()) == {
        "legacy_2009_start",
        "continuous_2012_start",
    }
    assert decision["decision_status"] in {
        "CARRY_2012_START_TO_ONDA3F",
        "KEEP_2009_START_FOR_ONDA3F",
        "KEEP_BOTH_STARTS_UNTIL_NESTED_VALIDATION",
    }
    assert decision["production_status"] == "EXPERIMENT_ONLY"


def test_train_start_sensitivity_reports_half_up_brackets_and_cp23():
    artifacts = build_onda3_train_start_sensitivity(
        _matrix(),
        test_years=[2023],
        numeric_feature_columns=["k_cp", "foehn_score", "cloud_cover_suppression"],
        categorical_feature_columns=["binary_macro_regime_label"],
        variants=[
            TrainStartVariant("legacy_2009_start", dt.date(2009, 4, 23)),
            TrainStartVariant("continuous_2012_start", dt.date(2012, 1, 1)),
        ],
    )

    predictions = artifacts["onda3_train_start_predictions_v1"]
    bracket = artifacts["onda3_train_start_bracket_overall_v1"]
    first = predictions.row(0, named=True)

    assert first["actual_bracket"] == math.floor(first["actual"] + 0.5)
    assert first["pred_bracket"] == math.floor(first["prediction"] + 0.5)
    assert "cp_2300_exact_pct" in bracket.columns
    assert bracket.select(pl.col("cp23_exact_pct").is_not_null().all()).item()
    assert bracket.select(pl.col("any_cp_exact_pct").is_not_null().all()).item()


def test_train_start_sensitivity_artifacts_remain_experiment_only():
    artifacts = build_onda3_train_start_sensitivity(
        _matrix(),
        test_years=[2023],
        numeric_feature_columns=["k_cp", "foehn_score", "cloud_cover_suppression"],
        categorical_feature_columns=["binary_macro_regime_label"],
        variants=[
            TrainStartVariant("legacy_2009_start", dt.date(2009, 4, 23)),
            TrainStartVariant("continuous_2012_start", dt.date(2012, 1, 1)),
        ],
    )

    for artifact in artifacts.values():
        if artifact.is_empty():
            continue
        assert "production_status" in artifact.columns
        assert set(artifact["production_status"].to_list()) == {"EXPERIMENT_ONLY"}


def test_write_onda3_train_start_sensitivity_artifacts_writes_report(
    tmp_path: Path,
):
    artifacts = build_onda3_train_start_sensitivity(
        _matrix(),
        test_years=[2023],
        numeric_feature_columns=["k_cp", "foehn_score", "cloud_cover_suppression"],
        categorical_feature_columns=["binary_macro_regime_label"],
        variants=[
            TrainStartVariant("legacy_2009_start", dt.date(2009, 4, 23)),
            TrainStartVariant("continuous_2012_start", dt.date(2012, 1, 1)),
        ],
    )

    paths = write_onda3_train_start_sensitivity_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 9),
    )

    report_path = paths["onda3_train_start_sensitivity_report_md"]
    report = report_path.read_text(encoding="utf-8")
    assert report_path.exists()
    assert (tmp_path / "onda3_train_start_decision_update_v1.csv").exists()
    assert "Open-Meteo forecast data is not integrated." in report
    assert "EXPERIMENT_ONLY" in report
