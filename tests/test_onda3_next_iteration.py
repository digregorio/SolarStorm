from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm.onda3._next_iteration import build_onda3_next_iteration


def _matrix() -> pl.DataFrame:
    rows = []
    for cp in ("20:00", "21:00"):
        for i in range(12):
            is_train = i < 8
            macro = "macro_non_southerly" if i % 2 == 0 else "macro_southerly_flow"
            k_cp = 20.0 + i
            target = k_cp + (0.5 if macro == "macro_non_southerly" else 1.5)
            rows.append(
                {
                    "date_local": dt.date(2024 if is_train else 2025, 1, (i % 8) + 1),
                    "cp": cp,
                    "k_cp": k_cp,
                    "cloud_cover_suppression": float(i % 3),
                    "binary_macro_regime_label": macro,
                    "tmax_int": target,
                    "fold": "train" if is_train else "test",
                }
            )
    return pl.DataFrame(rows)


def test_next_iteration_reports_cp_specific_results_predictions_and_decision():
    artifacts = build_onda3_next_iteration(
        _matrix(),
        numeric_feature_columns=["k_cp", "cloud_cover_suppression"],
        categorical_feature_columns=["binary_macro_regime_label"],
        target_column="tmax_int",
    )

    results = artifacts["onda3_next_model_results_v1"]
    predictions = artifacts["onda3_next_predictions_v1"]
    diagnostics = artifacts["onda3_next_slice_diagnostics_v1"]
    uncertainty = artifacts["onda3_next_uncertainty_abstention_v1"]
    decision = artifacts["onda3_next_decision_update_v1"].row(0, named=True)

    assert set(results["cp"].to_list()) == {"20:00", "21:00"}
    assert set(results["model_name"].to_list()) == {"train_mean_null", "ridge_challenger"}
    assert predictions.filter(pl.col("model_name") == "ridge_challenger").height == 8
    assert {"date_local", "cp", "actual", "prediction", "absolute_error", "model_name"}.issubset(
        set(predictions.columns)
    )
    assert {"cp", "binary_macro_regime_label"}.issubset(set(diagnostics["slice_column"].to_list()))
    assert set(uncertainty["production_status"].to_list()) == {"EXPERIMENT_ONLY"}
    assert decision["decision_status"] == "READY_FOR_ONDA4_MODEL_RERUN"
    assert decision["production_status"] == "EXPERIMENT_ONLY"


def test_next_iteration_keeps_unknown_test_category_as_safe_zero_encoding():
    matrix = _matrix().with_columns(
        pl.when((pl.col("fold") == "test") & (pl.col("cp") == "21:00"))
        .then(pl.lit("macro_unknown"))
        .otherwise(pl.col("binary_macro_regime_label"))
        .alias("binary_macro_regime_label")
    )

    artifacts = build_onda3_next_iteration(
        matrix,
        numeric_feature_columns=["k_cp", "cloud_cover_suppression"],
        categorical_feature_columns=["binary_macro_regime_label"],
        target_column="tmax_int",
    )

    predictions = artifacts["onda3_next_predictions_v1"]
    assert predictions["absolute_error"].null_count() == 0
