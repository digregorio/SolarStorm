from __future__ import annotations

import numpy as np
import polars as pl


def _mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - predicted)))


def _ridge_predict(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    *,
    alpha: float = 1.0,
) -> np.ndarray:
    train_x = np.asarray(train_x, dtype=float)
    test_x = np.asarray(test_x, dtype=float)
    train_y = np.asarray(train_y, dtype=float)
    train_mean = np.nanmean(train_x, axis=0)
    train_mean = np.where(np.isnan(train_mean), 0.0, train_mean)
    train_x = np.where(np.isnan(train_x), train_mean, train_x)
    test_x = np.where(np.isnan(test_x), train_mean, test_x)
    train_std = train_x.std(axis=0)
    train_std = np.where(train_std == 0.0, 1.0, train_std)
    x = (train_x - train_mean) / train_std
    x_test = (test_x - train_mean) / train_std
    x_design = np.column_stack([np.ones(x.shape[0]), x])
    x_test_design = np.column_stack([np.ones(x_test.shape[0]), x_test])
    penalty = np.eye(x_design.shape[1]) * alpha
    penalty[0, 0] = 0.0
    coefficients = np.linalg.solve(x_design.T @ x_design + penalty, x_design.T @ train_y)
    return x_test_design @ coefficients


def run_onda3_baseline_model(
    matrix: pl.DataFrame,
    *,
    feature_columns: list[str],
    target_column: str,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    train = matrix.filter(pl.col("fold") == "train")
    test = matrix.filter(pl.col("fold") == "test")
    if train.is_empty() or test.is_empty():
        raise ValueError("Onda 3 baseline model requires non-empty train and test folds.")
    if not feature_columns:
        raise ValueError("Onda 3 baseline model requires at least one numeric feature column.")

    train_y = train[target_column].to_numpy()
    test_y = test[target_column].to_numpy()
    null_pred = np.full(test.height, float(np.mean(train_y)))
    null_mae = _mae(test_y, null_pred)

    challenger_pred = _ridge_predict(
        train.select(feature_columns).to_numpy(),
        train_y,
        test.select(feature_columns).to_numpy(),
    )
    challenger_mae = _mae(test_y, challenger_pred)

    results = pl.DataFrame(
        [
            {
                "model_name": "train_mean_null",
                "cp": "ALL",
                "n_train": train.height,
                "n_test": test.height,
                "mae": null_mae,
                "beats_train_mean_null": False,
                "production_status": "EXPERIMENT_ONLY",
            },
            {
                "model_name": "ridge_challenger",
                "cp": "ALL",
                "n_train": train.height,
                "n_test": test.height,
                "mae": challenger_mae,
                "beats_train_mean_null": challenger_mae < null_mae,
                "production_status": "EXPERIMENT_ONLY",
            },
        ],
        strict=False,
    )
    residuals = test_y - challenger_pred
    uncertainty = pl.DataFrame(
        [
            {
                "model_name": "ridge_challenger",
                "residual_abs_p50": float(np.quantile(np.abs(residuals), 0.5)),
                "residual_abs_p90": float(np.quantile(np.abs(residuals), 0.9)),
                "abstention_rule": "abstain when slice support or interval calibration fails",
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )
    return results, uncertainty
