"""Persistence-block ablation over the Onda 3F pooled ridge."""
from __future__ import annotations

import polars as pl

from solarstorm.onda3._baseline_model import _mae, _ridge_predict
from solarstorm.onda3._pooled_iteration import (
    _encode_features,
    add_pooled_temporal_features,
)

PRODUCTION_STATUS = "EXPERIMENT_ONLY"
PERSISTENCE_BLOCK = ("tmax_dminus1", "slope_3h", "warming_rate_06_09")


def _fold_frames(matrix: pl.DataFrame, test_year: int) -> tuple[pl.DataFrame, pl.DataFrame]:
    dated = matrix.with_columns(pl.col("date_local").dt.year().alias("_year"))
    train = dated.filter(pl.col("_year") < test_year)
    test = dated.filter(pl.col("_year") == test_year)
    if train.is_empty() and not test.is_empty():
        ordered = test.sort("date_local")
        cutoff_index = int(ordered.height * 0.8)
        train = ordered.head(cutoff_index)
        test = ordered.slice(cutoff_index)
    return train.drop("_year"), test.drop("_year")


def _fit_mae(
    train: pl.DataFrame,
    test: pl.DataFrame,
    *,
    numeric: list[str],
    categorical: list[str],
    target_column: str,
) -> float:
    train_x, test_x = _encode_features(
        train,
        test,
        numeric_feature_columns=numeric,
        categorical_feature_columns=categorical,
    )
    predictions = _ridge_predict(train_x, train[target_column].to_numpy(), test_x)
    return _mae(test[target_column].to_numpy(), predictions)


def run_persistence_ablation(
    matrix: pl.DataFrame,
    *,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    target_column: str = "tmax_int",
) -> pl.DataFrame:
    """Compare pooled ridge MAE with and without persistence-block features."""
    matrix = add_pooled_temporal_features(matrix)
    numeric = [
        column
        for column in [
            *numeric_feature_columns,
            "cp_sin",
            "cp_cos",
            "month_sin",
            "month_cos",
            "doy_sin",
            "doy_cos",
        ]
        if column in matrix.columns and matrix.schema[column].is_numeric()
    ]
    numeric = list(dict.fromkeys(numeric))
    ablated_numeric = [column for column in numeric if column not in PERSISTENCE_BLOCK]
    rows: list[dict[str, object]] = []
    for test_year in test_years:
        train, test = _fold_frames(matrix, test_year)
        if train.is_empty() or test.is_empty():
            continue
        full_mae = _fit_mae(
            train,
            test,
            numeric=numeric,
            categorical=categorical_feature_columns,
            target_column=target_column,
        )
        ablated_mae = _fit_mae(
            train,
            test,
            numeric=ablated_numeric,
            categorical=categorical_feature_columns,
            target_column=target_column,
        )
        rows.append(
            {
                "test_year": test_year,
                "n_train": train.height,
                "n_test": test.height,
                "full_mae": full_mae,
                "ablated_mae": ablated_mae,
                "mae_delta_ablated_minus_full": ablated_mae - full_mae,
                "ablated_features": ",".join(PERSISTENCE_BLOCK),
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False)
