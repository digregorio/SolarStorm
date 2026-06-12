from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import polars as pl

from solarstorm.onda3._baseline_model import _mae, _ridge_predict
from solarstorm.onda3._interactions import add_binary_macro_interaction_features
from solarstorm.onda3._pooled_iteration import (
    CP_ORDER,
    TEMPORAL_FEATURE_COLUMNS,
    add_pooled_temporal_features,
    normalize_pooled_cp_column,
)
from solarstorm.open_meteo._availability import PRODUCTION_STATUS

ONDA3_OPEN_METEO_PILOT_FILENAMES = {
    "onda3_open_meteo_pilot_join_scope_v1": (
        "onda3_open_meteo_pilot_join_scope_v1.csv"
    ),
    "onda3_open_meteo_pilot_model_results_v1": (
        "onda3_open_meteo_pilot_model_results_v1.csv"
    ),
    "onda3_open_meteo_pilot_predictions_v1": (
        "onda3_open_meteo_pilot_predictions_v1.csv"
    ),
    "onda3_open_meteo_pilot_decision_update_v1": (
        "onda3_open_meteo_pilot_decision_update_v1.csv"
    ),
}
ONDA3_OPEN_METEO_NESTED_FILENAMES = {
    "onda3_open_meteo_nested_fold_scope_v1": (
        "onda3_open_meteo_nested_fold_scope_v1.csv"
    ),
    "onda3_open_meteo_nested_model_results_v1": (
        "onda3_open_meteo_nested_model_results_v1.csv"
    ),
    "onda3_open_meteo_nested_predictions_v1": (
        "onda3_open_meteo_nested_predictions_v1.csv"
    ),
    "onda3_open_meteo_nested_metric_summary_v1": (
        "onda3_open_meteo_nested_metric_summary_v1.csv"
    ),
    "onda3_open_meteo_nested_selection_v1": (
        "onda3_open_meteo_nested_selection_v1.csv"
    ),
    "onda3_open_meteo_nested_selected_test_summary_v1": (
        "onda3_open_meteo_nested_selected_test_summary_v1.csv"
    ),
    "onda3_open_meteo_nested_by_month_v1": (
        "onda3_open_meteo_nested_by_month_v1.csv"
    ),
    "onda3_open_meteo_nested_by_month_cp_v1": (
        "onda3_open_meteo_nested_by_month_cp_v1.csv"
    ),
    "onda3_open_meteo_nested_regime_performance_v1": (
        "onda3_open_meteo_nested_regime_performance_v1.csv"
    ),
    "onda3_open_meteo_nested_decision_update_v1": (
        "onda3_open_meteo_nested_decision_update_v1.csv"
    ),
}
LOCAL_ONDA3F_ID = "local_only_onda3f"
OPEN_METEO_ONDA3F_ID = "open_meteo_augmented_onda3f"
OPEN_METEO_NESTED_LABELS = {
    LOCAL_ONDA3F_ID: "Local-only Onda 3F",
    OPEN_METEO_ONDA3F_ID: "Open-Meteo augmented Onda 3F",
}


def _ensure_date(frame: pl.DataFrame) -> pl.DataFrame:
    dtype = frame.schema.get("date_local")
    if dtype == pl.Utf8:
        return frame.with_columns(pl.col("date_local").str.to_date())
    if isinstance(dtype, pl.Datetime):
        return frame.with_columns(pl.col("date_local").dt.date())
    return frame


def join_open_meteo_features(
    local_features: pl.DataFrame,
    open_meteo_features: pl.DataFrame,
) -> pl.DataFrame:
    local = normalize_pooled_cp_column(_ensure_date(local_features))
    om = normalize_pooled_cp_column(_ensure_date(open_meteo_features))
    if om.height - om.select(["date_local", "cp"]).unique().height:
        raise ValueError("duplicate Open-Meteo feature keys for pilot join")
    return local.join(om, on=["date_local", "cp"], how="inner", suffix="_om_meta")


def _encode(
    train: pl.DataFrame,
    test: pl.DataFrame,
    *,
    numeric_columns: list[str],
    categorical_columns: list[str],
) -> tuple[np.ndarray, np.ndarray]:
    train_parts = [train.select(numeric_columns).to_numpy()] if numeric_columns else []
    test_parts = [test.select(numeric_columns).to_numpy()] if numeric_columns else []
    for column in categorical_columns:
        if column not in train.columns or column not in test.columns:
            continue
        categories = sorted(
            str(value) for value in train[column].drop_nulls().unique().to_list()
        )
        for category in categories:
            train_parts.append(
                (train[column].cast(pl.Utf8) == category)
                .cast(pl.Float64)
                .to_numpy()
                .reshape(-1, 1)
            )
            test_parts.append(
                (test[column].cast(pl.Utf8) == category)
                .cast(pl.Float64)
                .to_numpy()
                .reshape(-1, 1)
            )
    if not train_parts:
        raise ValueError("Open-Meteo pilot requires at least one feature column")
    return np.column_stack(train_parts), np.column_stack(test_parts)


def _run_candidate(
    matrix: pl.DataFrame,
    *,
    test_year: int,
    candidate_id: str,
    numeric_columns: list[str],
    categorical_columns: list[str],
    target_column: str,
) -> tuple[dict[str, object], pl.DataFrame]:
    dated = matrix.with_columns(pl.col("date_local").dt.year().alias("_year"))
    train = dated.filter(pl.col("_year") < test_year).drop("_year")
    test = dated.filter(pl.col("_year") == test_year).drop("_year")
    train_y = train[target_column].to_numpy()
    test_y = test[target_column].to_numpy()
    train_x, test_x = _encode(
        train,
        test,
        numeric_columns=[
            column for column in numeric_columns if column in matrix.columns
        ],
        categorical_columns=[
            column for column in categorical_columns if column in matrix.columns
        ],
    )
    prediction = _ridge_predict(train_x, train_y, test_x)
    mae = _mae(test_y, prediction)
    predictions = test.select(["date_local", "cp"]).with_columns(
        pl.lit(test_year).alias("test_year"),
        pl.lit(candidate_id).alias("candidate_id"),
        pl.Series("actual", test_y),
        pl.Series("prediction", prediction),
        pl.Series("absolute_error", np.abs(test_y - prediction)),
        (pl.Series("actual_bracket", test_y) + 0.5).floor().cast(pl.Int64),
        (pl.Series("pred_bracket", prediction) + 0.5).floor().cast(pl.Int64),
        pl.lit(PRODUCTION_STATUS).alias("production_status"),
    ).with_columns(
        (pl.col("actual_bracket") == pl.col("pred_bracket")).alias("exact_bracket")
    )
    return (
        {
            "test_year": test_year,
            "candidate_id": candidate_id,
            "n_train": train.height,
            "n_test": test.height,
            "mae": mae,
            "exact_bracket_pct": float(
                predictions["exact_bracket"].cast(pl.Float64).mean() * 100.0
            ),
            "production_status": PRODUCTION_STATUS,
        },
        predictions,
    )


def _decision(results: pl.DataFrame) -> pl.DataFrame:
    if results.is_empty():
        return pl.DataFrame(
            [
                {
                    "decision_status": "BLOCK_OPEN_METEO_BY_AVAILABILITY",
                    "decision_rationale": (
                        "Open-Meteo coverage did not contain enough train/test "
                        "rows for the requested pilot folds."
                    ),
                    "augmented_minus_local_mae": None,
                    "production_status": PRODUCTION_STATUS,
                }
            ],
            strict=False,
        )

    local = results.filter(pl.col("candidate_id") == "local_only_reference")
    augmented = results.filter(pl.col("candidate_id") == "open_meteo_augmented")
    local_mae = float(local["mae"].mean())
    augmented_mae = float(augmented["mae"].mean())
    delta = augmented_mae - local_mae
    if delta < -0.01:
        status = "PROMOTE_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION"
        rationale = "Open-Meteo augmented candidate improved same-row MAE."
    elif delta <= 0.05:
        status = "KEEP_OPEN_METEO_IN_EXPERIMENT_REVIEW"
        rationale = (
            "Open-Meteo augmented candidate is close enough for further review."
        )
    else:
        status = "KEEP_LOCAL_ONLY_REFERENCE"
        rationale = "Local-only reference outperformed Open-Meteo augmented candidate."
    return pl.DataFrame(
        [
            {
                "decision_status": status,
                "decision_rationale": rationale,
                "augmented_minus_local_mae": delta,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def build_open_meteo_pilot(
    *,
    local_features: pl.DataFrame,
    open_meteo_features: pl.DataFrame,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    open_meteo_numeric_columns: list[str],
    target_column: str = "tmax_int",
) -> dict[str, pl.DataFrame]:
    joined = add_pooled_temporal_features(
        join_open_meteo_features(local_features, open_meteo_features)
    )
    local_numeric = [
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
        if column in joined.columns and joined.schema[column].is_numeric()
    ]
    augmented_numeric = [
        column
        for column in [*local_numeric, *open_meteo_numeric_columns]
        if column in joined.columns and joined.schema[column].is_numeric()
    ]
    result_rows: list[dict[str, object]] = []
    prediction_frames: list[pl.DataFrame] = []
    for test_year in test_years:
        if joined.filter(pl.col("date_local").dt.year() < test_year).is_empty():
            continue
        if joined.filter(pl.col("date_local").dt.year() == test_year).is_empty():
            continue
        for candidate_id, columns in [
            ("local_only_reference", local_numeric),
            ("open_meteo_augmented", augmented_numeric),
        ]:
            result, predictions = _run_candidate(
                joined,
                test_year=test_year,
                candidate_id=candidate_id,
                numeric_columns=columns,
                categorical_columns=categorical_feature_columns,
                target_column=target_column,
            )
            result_rows.append(result)
            prediction_frames.append(predictions)

    results = pl.DataFrame(result_rows, strict=False)
    predictions = (
        pl.concat(prediction_frames, how="diagonal_relaxed")
        if prediction_frames
        else pl.DataFrame()
    )
    return {
        "onda3_open_meteo_pilot_join_scope_v1": pl.DataFrame(
            [
                {
                    "n_joined_rows": joined.height,
                    "n_joined_dates": (
                        joined["date_local"].n_unique() if joined.height else 0
                    ),
                    "production_status": PRODUCTION_STATUS,
                }
            ],
            strict=False,
        ),
        "onda3_open_meteo_pilot_model_results_v1": results,
        "onda3_open_meteo_pilot_predictions_v1": predictions,
        "onda3_open_meteo_pilot_decision_update_v1": _decision(results),
    }


def _date_range_for_year(year: int) -> tuple[object, object]:
    return dt.date(year, 1, 1), dt.date(year, 12, 31)


def _subset_through_year(
    matrix: pl.DataFrame,
    *,
    train_start: object,
    evaluation_year: int,
) -> pl.DataFrame:
    _, evaluation_end = _date_range_for_year(evaluation_year)
    return matrix.filter(
        (pl.col("date_local") >= train_start) & (pl.col("date_local") <= evaluation_end)
    )


def _open_meteo_fold_scope_row(
    fold_matrix: pl.DataFrame,
    *,
    stage: str,
    outer_test_year: int,
    evaluation_year: int,
    train_start: object,
) -> dict[str, object]:
    train = fold_matrix.filter(pl.col("date_local").dt.year() < evaluation_year)
    evaluation = fold_matrix.filter(pl.col("date_local").dt.year() == evaluation_year)
    train_end = train["date_local"].max() if not train.is_empty() else None
    evaluation_start, evaluation_end = _date_range_for_year(evaluation_year)
    return {
        "stage": stage,
        "outer_test_year": outer_test_year,
        "evaluation_year": evaluation_year,
        "train_start": train_start,
        "train_end": train_end,
        "train_start_year": train_start.year,
        "train_end_year": train_end.year if train_end is not None else None,
        "evaluation_start": evaluation_start,
        "evaluation_end": evaluation_end,
        "n_train_rows": train.height,
        "n_evaluation_rows": evaluation.height,
        "production_status": PRODUCTION_STATUS,
    }


def _open_meteo_effective_numeric_columns(
    matrix: pl.DataFrame,
    *,
    numeric_feature_columns: list[str],
    open_meteo_numeric_columns: list[str],
    interaction_columns: list[str],
    include_open_meteo: bool,
) -> list[str]:
    columns = [
        *numeric_feature_columns,
        *TEMPORAL_FEATURE_COLUMNS,
        *interaction_columns,
        *(open_meteo_numeric_columns if include_open_meteo else []),
    ]
    return [
        column
        for column in columns
        if column in matrix.columns and matrix.schema[column].is_numeric()
    ]


def _run_open_meteo_nested_candidate(
    matrix: pl.DataFrame,
    *,
    candidate_id: str,
    stage: str,
    outer_test_year: int,
    evaluation_year: int,
    numeric_columns: list[str],
    categorical_columns: list[str],
    target_column: str,
) -> tuple[dict[str, object], pl.DataFrame]:
    train = matrix.filter(pl.col("date_local").dt.year() < evaluation_year)
    test = matrix.filter(pl.col("date_local").dt.year() == evaluation_year)
    train_y = train[target_column].to_numpy()
    test_y = test[target_column].to_numpy()
    null_prediction = np.full(test.height, float(np.mean(train_y)))
    null_mae = _mae(test_y, null_prediction)
    train_x, test_x = _encode(
        train,
        test,
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
    )
    prediction = _ridge_predict(train_x, train_y, test_x)
    mae = _mae(test_y, prediction)
    predictions = test.select(["date_local", "cp"]).with_columns(
        pl.lit(stage).alias("stage"),
        pl.lit(outer_test_year).alias("outer_test_year"),
        pl.lit(evaluation_year).alias("evaluation_year"),
        pl.lit(candidate_id).alias("candidate_id"),
        pl.lit(OPEN_METEO_NESTED_LABELS[candidate_id]).alias("candidate_label"),
        pl.lit(evaluation_year).alias("test_year"),
        pl.Series("actual", test_y),
        pl.Series("prediction", prediction),
        pl.Series("absolute_error", np.abs(test_y - prediction)),
        (pl.Series("actual_bracket", test_y) + 0.5).floor().cast(pl.Int64),
        (pl.Series("pred_bracket", prediction) + 0.5).floor().cast(pl.Int64),
        pl.lit("ridge_challenger").alias("model_name"),
        pl.lit(PRODUCTION_STATUS).alias("production_status"),
    ).with_columns(
        (pl.col("actual_bracket") == pl.col("pred_bracket")).alias("exact_bracket"),
        pl.col("date_local").dt.strftime("%Y-%m").alias("month"),
        pl.col("date_local").dt.year().alias("calendar_year"),
    )
    if "binary_macro_regime_label" in test.columns:
        predictions = predictions.join(
            test.select(["date_local", "cp", "binary_macro_regime_label"]).unique(),
            on=["date_local", "cp"],
            how="left",
        )
    return (
        {
            "stage": stage,
            "outer_test_year": outer_test_year,
            "evaluation_year": evaluation_year,
            "candidate_id": candidate_id,
            "candidate_label": OPEN_METEO_NESTED_LABELS[candidate_id],
            "test_year": evaluation_year,
            "cp": "ALL",
            "model_name": "ridge_challenger",
            "n_train": train.height,
            "n_test": test.height,
            "mae": mae,
            "beats_train_mean_null": mae < null_mae,
            "exact_bracket_pct": float(
                predictions["exact_bracket"].cast(pl.Float64).mean() * 100.0
            ),
            "production_status": PRODUCTION_STATUS,
        },
        predictions,
    )


def _bool_pct(frame: pl.DataFrame, column: str) -> float | None:
    if frame.is_empty() or column not in frame.columns:
        return None
    values = frame[column].drop_nulls()
    if values.is_empty():
        return None
    return float(values.cast(pl.Float64).mean() * 100.0)


def _open_meteo_metric_summary(predictions: pl.DataFrame) -> pl.DataFrame:
    if predictions.is_empty():
        return pl.DataFrame()
    rows: list[dict[str, object]] = []
    pairs = (
        predictions.select(
            [
                "stage",
                "outer_test_year",
                "evaluation_year",
                "candidate_id",
                "candidate_label",
            ]
        )
        .unique()
        .sort(["outer_test_year", "stage", "candidate_id"])
    )
    for pair in pairs.iter_rows(named=True):
        subset = predictions.filter(
            (pl.col("stage") == pair["stage"])
            & (pl.col("outer_test_year") == pair["outer_test_year"])
            & (pl.col("candidate_id") == pair["candidate_id"])
        )
        daily = subset.group_by("date_local").agg(
            pl.col("exact_bracket").any().alias("any_cp_exact"),
            pl.col("exact_bracket").filter(pl.col("cp") == "23:00").first().alias(
                "cp23_exact"
            ),
        )
        cp23_values = daily["cp23_exact"].drop_nulls()
        n_days_with_cp23 = len(cp23_values)
        row: dict[str, object] = {
            **pair,
            "n_days": daily.height,
            "n_cp_rows": subset.height,
            "mae": float(subset["absolute_error"].mean()),
            "any_cp_exact_pct": _bool_pct(daily, "any_cp_exact"),
            "n_days_with_cp23": n_days_with_cp23,
            "cp23_exact_days": (
                int(cp23_values.cast(pl.Int64).sum()) if n_days_with_cp23 else 0
            ),
            "cp23_exact_pct": _bool_pct(daily, "cp23_exact"),
            "production_status": PRODUCTION_STATUS,
        }
        for cp in CP_ORDER:
            cp_subset = subset.filter(pl.col("cp") == cp)
            row[f"cp_{cp.replace(':', '')}_exact_pct"] = _bool_pct(
                cp_subset,
                "exact_bracket",
            )
        rows.append(row)
    return pl.DataFrame(rows, strict=False)


def _nested_tiebreak_key(row: dict[str, object]) -> tuple[int, float, int]:
    cp23 = row.get("cp23_exact_pct")
    cp23_missing = cp23 is None or (isinstance(cp23, float) and cp23 != cp23)
    cp23_sort = 0.0 if cp23_missing else -float(cp23)
    conservative_order = 0 if row["candidate_id"] == LOCAL_ONDA3F_ID else 1
    return int(cp23_missing), cp23_sort, conservative_order


def _select_open_meteo_validation_winner(
    validation: pl.DataFrame,
    *,
    mae_tolerance: float = 0.001,
) -> dict[str, object]:
    rows = list(validation.iter_rows(named=True))
    best_mae = min(float(row["mae"]) for row in rows)
    tied_rows = [
        row for row in rows if float(row["mae"]) <= best_mae + mae_tolerance
    ]
    return sorted(tied_rows, key=_nested_tiebreak_key)[0]


def _open_meteo_selection(summary: pl.DataFrame) -> pl.DataFrame:
    if summary.is_empty():
        return pl.DataFrame()
    rows: list[dict[str, object]] = []
    for outer_test_year in sorted(summary["outer_test_year"].unique().to_list()):
        validation = summary.filter(
            (pl.col("outer_test_year") == outer_test_year)
            & (pl.col("stage") == "validation")
        )
        test = summary.filter(
            (pl.col("outer_test_year") == outer_test_year)
            & (pl.col("stage") == "test")
        )
        if validation.is_empty() or test.is_empty():
            continue
        winner = _select_open_meteo_validation_winner(validation)
        winner_test_rows = test.filter(pl.col("candidate_id") == winner["candidate_id"])
        winner_test = (
            winner_test_rows.row(0, named=True) if not winner_test_rows.is_empty() else {}
        )
        rows.append(
            {
                "outer_test_year": outer_test_year,
                "validation_year": int(winner["evaluation_year"]),
                "selected_candidate_id": winner["candidate_id"],
                "selected_candidate_label": winner["candidate_label"],
                "selected_validation_mae": winner["mae"],
                "selected_validation_any_cp_exact_pct": winner["any_cp_exact_pct"],
                "selected_validation_cp23_exact_pct": winner["cp23_exact_pct"],
                "selected_test_mae": winner_test.get("mae"),
                "selected_test_any_cp_exact_pct": winner_test.get("any_cp_exact_pct"),
                "selected_test_cp23_exact_pct": winner_test.get("cp23_exact_pct"),
                "validation_candidate_count": validation.height,
                "test_candidate_count": test.height,
                "selection_rule": "validation_mae_then_cp23_exact_then_local",
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False)


def _open_meteo_selected_test_summary(
    summary: pl.DataFrame,
    selection: pl.DataFrame,
) -> pl.DataFrame:
    if summary.is_empty() or selection.is_empty():
        return pl.DataFrame()
    return (
        summary.filter(pl.col("stage") == "test")
        .join(
            selection.select(
                ["outer_test_year", "selected_candidate_id", "selection_rule"]
            ),
            on="outer_test_year",
            how="inner",
        )
        .filter(pl.col("candidate_id") == pl.col("selected_candidate_id"))
        .select(
            [
                "outer_test_year",
                "evaluation_year",
                "candidate_id",
                "candidate_label",
                "mae",
                "any_cp_exact_pct",
                "cp23_exact_pct",
                "n_days_with_cp23",
                "cp23_exact_days",
                "n_days",
                "n_cp_rows",
                "selection_rule",
                "production_status",
            ]
        )
        .sort("outer_test_year")
    )


def _open_meteo_by_month(predictions: pl.DataFrame) -> pl.DataFrame:
    if predictions.is_empty():
        return pl.DataFrame()
    daily = predictions.group_by(
        [
            "stage",
            "outer_test_year",
            "candidate_id",
            "candidate_label",
            "date_local",
            "month",
        ]
    ).agg(
        pl.col("exact_bracket").any().alias("any_cp_exact"),
        pl.col("exact_bracket").filter(pl.col("cp") == "23:00").first().alias(
            "cp23_exact"
        ),
    )
    return (
        daily.group_by(
            ["stage", "outer_test_year", "candidate_id", "candidate_label", "month"]
        )
        .agg(
            pl.len().alias("n_days"),
            pl.col("any_cp_exact").cast(pl.Float64).mean().mul(100.0).alias(
                "any_cp_exact_pct"
            ),
            pl.col("cp23_exact").cast(pl.Float64).mean().mul(100.0).alias(
                "cp23_exact_pct"
            ),
        )
        .with_columns(pl.lit(PRODUCTION_STATUS).alias("production_status"))
        .sort(["outer_test_year", "stage", "candidate_id", "month"])
    )


def _open_meteo_by_month_cp(predictions: pl.DataFrame) -> pl.DataFrame:
    if predictions.is_empty():
        return pl.DataFrame()
    return (
        predictions.group_by(
            [
                "stage",
                "outer_test_year",
                "candidate_id",
                "candidate_label",
                "month",
                "cp",
            ]
        )
        .agg(
            pl.len().alias("n_cp_rows"),
            pl.col("absolute_error").mean().alias("mae"),
            pl.col("exact_bracket").cast(pl.Float64).mean().mul(100.0).alias(
                "exact_bracket_pct"
            ),
        )
        .with_columns(pl.lit(PRODUCTION_STATUS).alias("production_status"))
        .sort(["outer_test_year", "stage", "candidate_id", "month", "cp"])
    )


def _open_meteo_regime_performance(predictions: pl.DataFrame) -> pl.DataFrame:
    if predictions.is_empty() or "binary_macro_regime_label" not in predictions.columns:
        return pl.DataFrame()
    return (
        predictions.drop_nulls("binary_macro_regime_label")
        .group_by(
            [
                "stage",
                "outer_test_year",
                "candidate_id",
                "candidate_label",
                "binary_macro_regime_label",
            ]
        )
        .agg(
            pl.len().alias("n_cp_rows"),
            pl.col("date_local").n_unique().alias("n_unique_dates"),
            pl.col("absolute_error").mean().alias("mae"),
            pl.col("exact_bracket").cast(pl.Float64).mean().mul(100.0).alias(
                "exact_bracket_pct"
            ),
        )
        .with_columns(pl.lit(PRODUCTION_STATUS).alias("production_status"))
        .sort(
            [
                "outer_test_year",
                "stage",
                "candidate_id",
                "binary_macro_regime_label",
            ]
        )
    )


def _open_meteo_nested_decision(
    summary: pl.DataFrame,
    selection: pl.DataFrame,
    selected_test: pl.DataFrame,
) -> pl.DataFrame:
    if selection.is_empty():
        return pl.DataFrame(
            [
                {
                    "decision_status": "BLOCK_OPEN_METEO_BY_AVAILABILITY",
                    "decision_rationale": (
                        "Open-Meteo coverage did not contain enough nested "
                        "validation/test folds."
                    ),
                    "n_outer_folds": 0,
                    "selected_mean_test_mae": None,
                    "always_local_mean_test_mae": None,
                    "always_open_meteo_mean_test_mae": None,
                    "production_status": PRODUCTION_STATUS,
                }
            ],
            strict=False,
        )
    test_summary = summary.filter(pl.col("stage") == "test")
    local = test_summary.filter(pl.col("candidate_id") == LOCAL_ONDA3F_ID)
    augmented = test_summary.filter(pl.col("candidate_id") == OPEN_METEO_ONDA3F_ID)
    selected_ids = set(selection["selected_candidate_id"].to_list())
    selected_mean = (
        float(selected_test["mae"].mean()) if not selected_test.is_empty() else None
    )
    local_mean = float(local["mae"].mean()) if not local.is_empty() else None
    augmented_mean = (
        float(augmented["mae"].mean()) if not augmented.is_empty() else None
    )
    if selected_ids == {OPEN_METEO_ONDA3F_ID}:
        status = "PROMOTE_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION"
        rationale = (
            "Nested validation selected the Open-Meteo augmented candidate in "
            "every valid outer fold."
        )
    elif OPEN_METEO_ONDA3F_ID in selected_ids:
        status = "KEEP_OPEN_METEO_IN_EXPERIMENT_REVIEW"
        rationale = "Nested validation selected Open-Meteo in some folds."
    else:
        status = "KEEP_LOCAL_ONLY_REFERENCE"
        rationale = "Nested validation selected the local-only reference."
    return pl.DataFrame(
        [
            {
                "decision_status": status,
                "decision_rationale": rationale,
                "n_outer_folds": selection.height,
                "selected_mean_test_mae": selected_mean,
                "always_local_mean_test_mae": local_mean,
                "always_open_meteo_mean_test_mae": augmented_mean,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def build_open_meteo_nested_validation(
    *,
    local_features: pl.DataFrame,
    open_meteo_features: pl.DataFrame,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    open_meteo_numeric_columns: list[str],
    train_start: object,
    target_column: str = "tmax_int",
) -> dict[str, pl.DataFrame]:
    joined = add_pooled_temporal_features(
        join_open_meteo_features(local_features, open_meteo_features)
    )
    if "binary_macro_regime_label" in joined.columns:
        joined, interaction_columns = add_binary_macro_interaction_features(joined)
    else:
        interaction_columns = []
    effective_categorical = [
        column for column in categorical_feature_columns if column in joined.columns
    ]
    local_numeric = _open_meteo_effective_numeric_columns(
        joined,
        numeric_feature_columns=numeric_feature_columns,
        open_meteo_numeric_columns=open_meteo_numeric_columns,
        interaction_columns=interaction_columns,
        include_open_meteo=False,
    )
    augmented_numeric = _open_meteo_effective_numeric_columns(
        joined,
        numeric_feature_columns=numeric_feature_columns,
        open_meteo_numeric_columns=open_meteo_numeric_columns,
        interaction_columns=interaction_columns,
        include_open_meteo=True,
    )
    fold_scope_rows: list[dict[str, object]] = []
    result_rows: list[dict[str, object]] = []
    prediction_frames: list[pl.DataFrame] = []

    for outer_test_year in test_years:
        for stage, evaluation_year in [
            ("validation", outer_test_year - 1),
            ("test", outer_test_year),
        ]:
            fold_matrix = _subset_through_year(
                joined,
                train_start=train_start,
                evaluation_year=evaluation_year,
            )
            fold_scope_rows.append(
                _open_meteo_fold_scope_row(
                    fold_matrix,
                    stage=stage,
                    outer_test_year=outer_test_year,
                    evaluation_year=evaluation_year,
                    train_start=train_start,
                )
            )
            if (
                fold_matrix.filter(
                    pl.col("date_local").dt.year() < evaluation_year
                ).is_empty()
                or fold_matrix.filter(
                    pl.col("date_local").dt.year() == evaluation_year
                ).is_empty()
            ):
                continue
            for candidate_id, columns in [
                (LOCAL_ONDA3F_ID, local_numeric),
                (OPEN_METEO_ONDA3F_ID, augmented_numeric),
            ]:
                result, predictions = _run_open_meteo_nested_candidate(
                    fold_matrix,
                    candidate_id=candidate_id,
                    stage=stage,
                    outer_test_year=outer_test_year,
                    evaluation_year=evaluation_year,
                    numeric_columns=columns,
                    categorical_columns=effective_categorical,
                    target_column=target_column,
                )
                result_rows.append(result)
                prediction_frames.append(predictions)

    results = pl.DataFrame(result_rows, strict=False)
    predictions = (
        pl.concat(prediction_frames, how="diagonal_relaxed")
        if prediction_frames
        else pl.DataFrame()
    )
    summary = _open_meteo_metric_summary(predictions)
    selection = _open_meteo_selection(summary)
    selected_test = _open_meteo_selected_test_summary(summary, selection)
    return {
        "onda3_open_meteo_nested_fold_scope_v1": pl.DataFrame(
            fold_scope_rows,
            strict=False,
        ),
        "onda3_open_meteo_nested_model_results_v1": results,
        "onda3_open_meteo_nested_predictions_v1": predictions,
        "onda3_open_meteo_nested_metric_summary_v1": summary,
        "onda3_open_meteo_nested_selection_v1": selection,
        "onda3_open_meteo_nested_selected_test_summary_v1": selected_test,
        "onda3_open_meteo_nested_by_month_v1": _open_meteo_by_month(predictions),
        "onda3_open_meteo_nested_by_month_cp_v1": _open_meteo_by_month_cp(
            predictions
        ),
        "onda3_open_meteo_nested_regime_performance_v1": (
            _open_meteo_regime_performance(predictions)
        ),
        "onda3_open_meteo_nested_decision_update_v1": _open_meteo_nested_decision(
            summary,
            selection,
            selected_test,
        ),
    }


def _markdown_table(frame: pl.DataFrame, max_rows: int = 30) -> str:
    if frame.is_empty():
        return "_No rows._"
    header = "| " + " | ".join(frame.columns) + " |"
    divider = "| " + " | ".join("---" for _ in frame.columns) + " |"
    rows = [
        "| "
        + " | ".join("" if row[col] is None else str(row[col]) for col in frame.columns)
        + " |"
        for row in frame.head(max_rows).iter_rows(named=True)
    ]
    return "\n".join([header, divider, *rows])


def render_open_meteo_pilot_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: object,
) -> str:
    return "\n\n".join(
        [
            "# Onda 3 Open-Meteo Pilot Report",
            f"Generated: {today}",
            f"production_status: {PRODUCTION_STATUS}",
            (
                "Open-Meteo augmented candidate is compared against "
                "local-only reference on identical covered rows."
            ),
            "## Decision",
            _markdown_table(artifacts["onda3_open_meteo_pilot_decision_update_v1"]),
            "## Join Scope",
            _markdown_table(artifacts["onda3_open_meteo_pilot_join_scope_v1"]),
            "## Model Results",
            _markdown_table(artifacts["onda3_open_meteo_pilot_model_results_v1"]),
        ]
    ) + "\n"


def render_open_meteo_nested_validation_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: object,
) -> str:
    return "\n\n".join(
        [
            "# Onda 3 Open-Meteo Nested Validation Report",
            f"Generated: {today}",
            f"production_status: {PRODUCTION_STATUS}",
            (
                "Open-Meteo augmented Onda 3F is compared against local-only "
                "Onda 3F on identical covered rows using nested validation "
                "folds: train through Y-2, validation on Y-1, test on Y."
            ),
            "## Decision",
            _markdown_table(
                artifacts["onda3_open_meteo_nested_decision_update_v1"]
            ),
            "## Fold Scope",
            _markdown_table(
                artifacts["onda3_open_meteo_nested_fold_scope_v1"],
                max_rows=20,
            ),
            "## Validation Selection",
            _markdown_table(
                artifacts["onda3_open_meteo_nested_selection_v1"],
                max_rows=20,
            ),
            "## Selected Test Summary",
            _markdown_table(
                artifacts["onda3_open_meteo_nested_selected_test_summary_v1"],
                max_rows=20,
            ),
            "## Candidate Metric Summary",
            _markdown_table(
                artifacts["onda3_open_meteo_nested_metric_summary_v1"],
                max_rows=40,
            ),
            "## Regime Performance",
            _markdown_table(
                artifacts["onda3_open_meteo_nested_regime_performance_v1"],
                max_rows=40,
            ),
        ]
    ) + "\n"


def write_open_meteo_pilot_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: object,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for key, filename in ONDA3_OPEN_METEO_PILOT_FILENAMES.items():
        path = output_dir / filename
        artifacts[key].write_csv(path)
        paths[key] = path

    report_path = output_dir / "onda3_open_meteo_pilot_report_v1.md"
    report_path.write_text(
        render_open_meteo_pilot_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["onda3_open_meteo_pilot_report_md"] = report_path
    return paths


def write_open_meteo_nested_validation_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: object,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for key, filename in ONDA3_OPEN_METEO_NESTED_FILENAMES.items():
        path = output_dir / filename
        artifacts[key].write_csv(path)
        paths[key] = path

    report_path = output_dir / "onda3_open_meteo_nested_report_v1.md"
    report_path.write_text(
        render_open_meteo_nested_validation_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["onda3_open_meteo_nested_report_md"] = report_path
    return paths
