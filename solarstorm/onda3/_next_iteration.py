from __future__ import annotations

import numpy as np
import polars as pl

from solarstorm.onda3._baseline_model import _mae, _ridge_predict


def _encode_features(
    train: pl.DataFrame,
    test: pl.DataFrame,
    *,
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
) -> tuple[np.ndarray, np.ndarray]:
    train_parts = [train.select(numeric_feature_columns).to_numpy()] if numeric_feature_columns else []
    test_parts = [test.select(numeric_feature_columns).to_numpy()] if numeric_feature_columns else []

    for column in categorical_feature_columns:
        if column not in train.columns or column not in test.columns:
            continue
        categories = sorted(str(value) for value in train[column].drop_nulls().unique().to_list())
        for category in categories:
            train_parts.append((train[column].cast(pl.Utf8) == category).cast(pl.Float64).to_numpy().reshape(-1, 1))
            test_parts.append((test[column].cast(pl.Utf8) == category).cast(pl.Float64).to_numpy().reshape(-1, 1))

    if not train_parts:
        raise ValueError("Onda 3B requires at least one numeric or categorical feature.")
    return np.column_stack(train_parts), np.column_stack(test_parts)


def _prediction_rows(
    test: pl.DataFrame,
    *,
    predictions: np.ndarray,
    target_column: str,
) -> pl.DataFrame:
    actual = test[target_column].to_numpy()
    return test.select(["date_local", "cp"]).with_columns(
        pl.Series("actual", actual),
        pl.Series("prediction", predictions),
        pl.Series("absolute_error", np.abs(actual - predictions)),
        pl.lit("ridge_challenger").alias("model_name"),
        pl.lit("EXPERIMENT_ONLY").alias("production_status"),
    )


def _slice_diagnostics(predictions: pl.DataFrame, matrix: pl.DataFrame) -> pl.DataFrame:
    enriched = predictions.join(
        matrix.select(["date_local", "cp", "binary_macro_regime_label"]),
        on=["date_local", "cp"],
        how="left",
    )
    rows: list[dict[str, object]] = []
    for column in ("cp", "binary_macro_regime_label"):
        if column not in enriched.columns:
            continue
        grouped = enriched.group_by(column).agg(
            pl.len().alias("rows"),
            pl.col("absolute_error").mean().alias("mae"),
        )
        for row in grouped.sort(column).iter_rows(named=True):
            rows.append(
                {
                    "slice_column": column,
                    "slice_value": str(row[column]),
                    "rows": row["rows"],
                    "mae": row["mae"],
                    "production_status": "EXPERIMENT_ONLY",
                }
            )
    return pl.DataFrame(rows, strict=False)


def build_onda3_next_iteration(
    matrix: pl.DataFrame,
    *,
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    target_column: str = "tmax_int",
) -> dict[str, pl.DataFrame]:
    result_rows: list[dict[str, object]] = []
    uncertainty_rows: list[dict[str, object]] = []
    prediction_frames: list[pl.DataFrame] = []

    for cp in sorted(matrix["cp"].unique().to_list()):
        cp_matrix = matrix.filter(pl.col("cp") == cp)
        train = cp_matrix.filter(pl.col("fold") == "train")
        test = cp_matrix.filter(pl.col("fold") == "test")
        if train.is_empty() or test.is_empty():
            continue

        train_y = train[target_column].to_numpy()
        test_y = test[target_column].to_numpy()
        null_prediction = np.full(test.height, float(np.mean(train_y)))
        null_mae = _mae(test_y, null_prediction)
        train_x, test_x = _encode_features(
            train,
            test,
            numeric_feature_columns=numeric_feature_columns,
            categorical_feature_columns=categorical_feature_columns,
        )
        challenger_prediction = _ridge_predict(train_x, train_y, test_x)
        challenger_mae = _mae(test_y, challenger_prediction)
        prediction_frame = _prediction_rows(
            test,
            predictions=challenger_prediction,
            target_column=target_column,
        )
        prediction_frames.append(prediction_frame)

        result_rows.extend(
            [
                {
                    "model_name": "train_mean_null",
                    "cp": cp,
                    "n_train": train.height,
                    "n_test": test.height,
                    "mae": null_mae,
                    "beats_train_mean_null": False,
                    "production_status": "EXPERIMENT_ONLY",
                },
                {
                    "model_name": "ridge_challenger",
                    "cp": cp,
                    "n_train": train.height,
                    "n_test": test.height,
                    "mae": challenger_mae,
                    "beats_train_mean_null": challenger_mae < null_mae,
                    "production_status": "EXPERIMENT_ONLY",
                },
            ]
        )
        residual_abs = prediction_frame["absolute_error"].to_numpy()
        uncertainty_rows.append(
            {
                "model_name": "ridge_challenger",
                "cp": cp,
                "residual_abs_p50": float(np.quantile(residual_abs, 0.5)),
                "residual_abs_p90": float(np.quantile(residual_abs, 0.9)),
                "abstention_rule": "abstain when CP or macro slice support is weak",
                "production_status": "EXPERIMENT_ONLY",
            }
        )

    results = pl.DataFrame(result_rows, strict=False)
    predictions = pl.concat(prediction_frames) if prediction_frames else pl.DataFrame()
    diagnostics = _slice_diagnostics(predictions, matrix) if not predictions.is_empty() else pl.DataFrame()
    uncertainty = pl.DataFrame(uncertainty_rows, strict=False)
    challenger = results.filter(pl.col("model_name") == "ridge_challenger")
    all_beat = not challenger.is_empty() and bool(
        challenger.select(pl.col("beats_train_mean_null").all()).item()
    )
    decision = pl.DataFrame(
        [
            {
                "decision_status": (
                    "READY_FOR_ONDA4_MODEL_RERUN"
                    if all_beat
                    else "KEEP_IN_ONDA3_EXPERIMENT_REVIEW"
                ),
                "decision_rationale": "Onda 3B CP-specific next model iteration completed.",
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )
    return {
        "onda3_next_model_results_v1": results,
        "onda3_next_predictions_v1": predictions,
        "onda3_next_slice_diagnostics_v1": diagnostics,
        "onda3_next_uncertainty_abstention_v1": uncertainty,
        "onda3_next_decision_update_v1": decision,
    }
