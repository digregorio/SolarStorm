from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm.onda3._nested_validation import (
    _metric_summary,
    _selection,
    build_onda3_nested_validation,
    select_onda3h_feature_columns,
)


def _nested_matrix() -> pl.DataFrame:
    rows = []
    for year in range(2020, 2025):
        for month in (1, 7):
            for day in range(1, 7):
                date = dt.date(year, month, day)
                for cp_index, cp in enumerate(("20:00", "21:00", "22:00", "23:00")):
                    macro = (
                        "macro_non_southerly"
                        if (day + cp_index) % 2 == 0
                        else "macro_southerly_flow"
                    )
                    foehn = float(day * 4 + cp_index)
                    cloud = float(8 - day + cp_index / 10)
                    k_cp = float(13 + month / 10 + day / 4 + cp_index / 10)
                    target = k_cp + 0.05 * foehn - 0.03 * cloud
                    if macro == "macro_southerly_flow":
                        target -= 0.4
                    rows.append(
                        {
                            "date_local": date,
                            "cp": cp,
                            "k_cp": k_cp,
                            "foehn_score": foehn,
                            "cloud_cover_suppression": cloud,
                            "binary_macro_regime_label": macro,
                            "regime_label": "warm_nw"
                            if macro == "macro_non_southerly"
                            else "cool_s",
                            "regime_score_argmax": macro,
                            "day_sequence_pattern": "warming"
                            if day <= 3
                            else "cooling",
                            "tmax_int": target,
                        }
                    )
    return pl.DataFrame(rows)


def test_build_onda3_nested_validation_selects_by_validation_and_refits_for_test():
    artifacts = build_onda3_nested_validation(
        _nested_matrix(),
        test_years=[2024],
        numeric_feature_columns=["k_cp", "foehn_score", "cloud_cover_suppression"],
        categorical_feature_columns=[
            "binary_macro_regime_label",
            "regime_label",
            "regime_score_argmax",
            "day_sequence_pattern",
        ],
        train_start=dt.date(2020, 1, 1),
    )

    scope = artifacts["onda3_nested_fold_scope_v1"]
    summary = artifacts["onda3_nested_metric_summary_v1"]
    selection = artifacts["onda3_nested_selection_v1"].row(0, named=True)
    selected_summary = artifacts["onda3_nested_test_selected_summary_v1"]
    predictions = artifacts["onda3_nested_predictions_v1"]

    validation_scope = scope.filter(pl.col("stage") == "validation").row(
        0, named=True
    )
    test_scope = scope.filter(pl.col("stage") == "test").row(0, named=True)

    assert validation_scope["train_end_year"] == 2022
    assert validation_scope["evaluation_year"] == 2023
    assert test_scope["train_end_year"] == 2023
    assert test_scope["evaluation_year"] == 2024
    assert set(summary["candidate_id"].to_list()) == {
        "onda3_d_binary_macro_interactions",
        "onda3_f_pooled_temporal_regime",
    }
    assert set(summary["stage"].to_list()) == {"validation", "test"}
    assert selection["outer_test_year"] == 2024
    assert selection["selected_candidate_id"] in {
        "onda3_d_binary_macro_interactions",
        "onda3_f_pooled_temporal_regime",
    }
    assert selected_summary.height == 1
    assert set(
        predictions.select(["actual_bracket", "pred_bracket", "exact_bracket"]).columns
    ) == {"actual_bracket", "pred_bracket", "exact_bracket"}

    for artifact in artifacts.values():
        if artifact.is_empty():
            continue
        assert "production_status" in artifact.columns
        assert set(artifact["production_status"].to_list()) == {"EXPERIMENT_ONLY"}


def test_build_onda3_nested_validation_recomputes_stale_bracket_columns():
    matrix = _nested_matrix().with_columns(
        pl.lit(99).alias("actual_bracket"),
        pl.lit(-99).alias("pred_bracket"),
        pl.lit(False).alias("exact_bracket"),
    )

    artifacts = build_onda3_nested_validation(
        matrix,
        test_years=[2024],
        numeric_feature_columns=["k_cp", "foehn_score", "cloud_cover_suppression"],
        categorical_feature_columns=["binary_macro_regime_label"],
        train_start=dt.date(2020, 1, 1),
    )

    predictions = artifacts["onda3_nested_predictions_v1"]

    assert predictions["actual_bracket"].max() < 99
    assert predictions["pred_bracket"].min() > -99
    assert predictions["exact_bracket"].dtype == pl.Boolean


def test_nested_selection_uses_cp23_when_validation_mae_ties_within_tolerance():
    summary = pl.DataFrame(
        [
            {
                "stage": "validation",
                "outer_test_year": 2024,
                "evaluation_year": 2023,
                "candidate_id": "onda3_d_binary_macro_interactions",
                "candidate_label": "Onda 3D binary-macro interactions",
                "mae": 1.0008,
                "any_cp_exact_pct": 35.0,
                "cp23_exact_pct": 42.0,
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "stage": "validation",
                "outer_test_year": 2024,
                "evaluation_year": 2023,
                "candidate_id": "onda3_f_pooled_temporal_regime",
                "candidate_label": "Onda 3F pooled temporal/regime",
                "mae": 1.0000,
                "any_cp_exact_pct": 36.0,
                "cp23_exact_pct": 31.0,
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "stage": "test",
                "outer_test_year": 2024,
                "evaluation_year": 2024,
                "candidate_id": "onda3_d_binary_macro_interactions",
                "candidate_label": "Onda 3D binary-macro interactions",
                "mae": 1.2,
                "any_cp_exact_pct": 34.0,
                "cp23_exact_pct": 40.0,
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "stage": "test",
                "outer_test_year": 2024,
                "evaluation_year": 2024,
                "candidate_id": "onda3_f_pooled_temporal_regime",
                "candidate_label": "Onda 3F pooled temporal/regime",
                "mae": 1.1,
                "any_cp_exact_pct": 37.0,
                "cp23_exact_pct": 32.0,
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        strict=False,
    )

    selected = _selection(summary).row(0, named=True)

    assert selected["selected_candidate_id"] == "onda3_d_binary_macro_interactions"


def test_nested_selection_prefers_available_cp23_metric_over_missing_metric():
    summary = pl.DataFrame(
        [
            {
                "stage": "validation",
                "outer_test_year": 2024,
                "evaluation_year": 2023,
                "candidate_id": "onda3_d_binary_macro_interactions",
                "candidate_label": "Onda 3D binary-macro interactions",
                "mae": 1.0,
                "any_cp_exact_pct": 35.0,
                "cp23_exact_pct": None,
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "stage": "validation",
                "outer_test_year": 2024,
                "evaluation_year": 2023,
                "candidate_id": "onda3_f_pooled_temporal_regime",
                "candidate_label": "Onda 3F pooled temporal/regime",
                "mae": 1.0,
                "any_cp_exact_pct": 35.0,
                "cp23_exact_pct": 0.0,
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "stage": "test",
                "outer_test_year": 2024,
                "evaluation_year": 2024,
                "candidate_id": "onda3_d_binary_macro_interactions",
                "candidate_label": "Onda 3D binary-macro interactions",
                "mae": 1.2,
                "any_cp_exact_pct": 35.0,
                "cp23_exact_pct": None,
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "stage": "test",
                "outer_test_year": 2024,
                "evaluation_year": 2024,
                "candidate_id": "onda3_f_pooled_temporal_regime",
                "candidate_label": "Onda 3F pooled temporal/regime",
                "mae": 1.2,
                "any_cp_exact_pct": 35.0,
                "cp23_exact_pct": 0.0,
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        strict=False,
    )

    selected = _selection(summary).row(0, named=True)

    assert selected["selected_candidate_id"] == "onda3_f_pooled_temporal_regime"


def test_metric_summary_reports_cp23_denominator_when_cp23_is_absent():
    predictions = pl.DataFrame(
        [
            {
                "stage": "validation",
                "outer_test_year": 2024,
                "evaluation_year": 2023,
                "candidate_id": "onda3_d_binary_macro_interactions",
                "candidate_label": "Onda 3D binary-macro interactions",
                "date_local": dt.date(2023, 1, 1),
                "cp": "20:00",
                "actual": 15.0,
                "prediction": 15.1,
                "absolute_error": 0.1,
                "actual_bracket": 15,
                "pred_bracket": 15,
                "exact_bracket": True,
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )

    row = _metric_summary(predictions).row(0, named=True)

    assert row["n_days_with_cp23"] == 0
    assert row["cp23_exact_days"] == 0
    assert row["cp23_exact_pct"] is None


def test_select_onda3h_feature_columns_uses_explicit_allowlist():
    matrix = _nested_matrix().with_columns(
        pl.lit(99.0).alias("late_warming_anomaly"),
        pl.lit(18.0).alias("tmax_hour_by_regime_month"),
        pl.lit(1.0).alias("intraday_regime_change"),
    )

    numeric, categorical = select_onda3h_feature_columns(matrix)

    assert "foehn_score" in numeric
    assert "cloud_cover_suppression" in numeric
    assert "late_warming_anomaly" not in numeric
    assert "tmax_hour_by_regime_month" not in numeric
    assert "intraday_regime_change" not in numeric
    assert "binary_macro_regime_label" in categorical
    assert "regime_label" not in categorical
    assert "regime_score_argmax" not in categorical
