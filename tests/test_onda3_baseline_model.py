from __future__ import annotations

import datetime as dt

import polars as pl

from solarstorm.onda3._baseline_model import run_onda3_baseline_model
from solarstorm.onda3._evaluation import build_onda3_slice_diagnostics


def test_baseline_model_reports_null_challenger_and_slice_diagnostics():
    rows = []
    for i in range(20):
        rows.append(
            {
                "date_local": dt.date(2024 if i < 14 else 2025, 1, (i % 14) + 1),
                "cp": "20:00",
                "k_cp": 20 + (i % 3),
                "cloud_cover_suppression": float(i % 4),
                "tmax_int": 21 + (i % 5),
                "fold": "train" if i < 14 else "test",
                "binary_macro_regime_label": "macro_non_southerly",
            }
        )
    matrix = pl.DataFrame(rows)

    results, uncertainty = run_onda3_baseline_model(
        matrix,
        feature_columns=["k_cp", "cloud_cover_suppression"],
        target_column="tmax_int",
    )

    assert set(results["model_name"].to_list()) == {"train_mean_null", "ridge_challenger"}
    assert results.filter(pl.col("model_name") == "ridge_challenger").height == 1
    assert "mae" in results.columns
    assert "beats_train_mean_null" in results.columns
    assert uncertainty.row(0, named=True)["production_status"] == "EXPERIMENT_ONLY"

    diagnostics = build_onda3_slice_diagnostics(
        matrix,
        slice_columns=["cp", "binary_macro_regime_label"],
    )
    assert diagnostics.row(0, named=True)["slice_column"] == "cp"
    assert set(diagnostics["production_status"].to_list()) == {"EXPERIMENT_ONLY"}


def test_baseline_model_imputes_missing_numeric_features_from_train_window():
    matrix = pl.DataFrame(
        {
            "date_local": [
                dt.date(2024, 1, 1),
                dt.date(2024, 1, 2),
                dt.date(2024, 1, 3),
                dt.date(2025, 1, 1),
            ],
            "cp": ["20:00", "20:00", "20:00", "20:00"],
            "k_cp": [20.0, None, 22.0, None],
            "cloud_cover_suppression": [1.0, 2.0, None, 4.0],
            "tmax_int": [22, 23, 24, 25],
            "fold": ["train", "train", "train", "test"],
        }
    )

    results, uncertainty = run_onda3_baseline_model(
        matrix,
        feature_columns=["k_cp", "cloud_cover_suppression"],
        target_column="tmax_int",
    )

    challenger = results.filter(pl.col("model_name") == "ridge_challenger").row(0, named=True)
    assert challenger["mae"] == challenger["mae"]
    assert uncertainty.row(0, named=True)["residual_abs_p90"] == uncertainty.row(0, named=True)["residual_abs_p90"]
