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
from solarstorm.open_meteo._pilot import (
    _bool_pct,
    _encode,
    _open_meteo_by_month,
    _open_meteo_by_month_cp,
    _open_meteo_regime_performance,
)

CALIBRATED_NESTED_FILENAMES = {
    "onda3_open_meteo_calibrated_nested_candidate_scope_v1": (
        "onda3_open_meteo_calibrated_nested_candidate_scope_v1.csv"
    ),
    "onda3_open_meteo_calibrated_nested_model_results_v1": (
        "onda3_open_meteo_calibrated_nested_model_results_v1.csv"
    ),
    "onda3_open_meteo_calibrated_nested_predictions_v1": (
        "onda3_open_meteo_calibrated_nested_predictions_v1.csv"
    ),
    "onda3_open_meteo_calibrated_nested_metric_summary_v1": (
        "onda3_open_meteo_calibrated_nested_metric_summary_v1.csv"
    ),
    "onda3_open_meteo_calibrated_nested_selection_v1": (
        "onda3_open_meteo_calibrated_nested_selection_v1.csv"
    ),
    "onda3_open_meteo_calibrated_nested_selected_test_summary_v1": (
        "onda3_open_meteo_calibrated_nested_selected_test_summary_v1.csv"
    ),
    "onda3_open_meteo_calibrated_nested_by_month_v1": (
        "onda3_open_meteo_calibrated_nested_by_month_v1.csv"
    ),
    "onda3_open_meteo_calibrated_nested_by_month_cp_v1": (
        "onda3_open_meteo_calibrated_nested_by_month_cp_v1.csv"
    ),
    "onda3_open_meteo_calibrated_nested_regime_performance_v1": (
        "onda3_open_meteo_calibrated_nested_regime_performance_v1.csv"
    ),
    "onda3_open_meteo_calibrated_nested_decision_update_v1": (
        "onda3_open_meteo_calibrated_nested_decision_update_v1.csv"
    ),
    "onda3_open_meteo_defensive_selection_guardrail_v1": (
        "onda3_open_meteo_defensive_selection_guardrail_v1.csv"
    ),
}

LOCAL_ONDA3F_ID = "local_only_onda3f"
LOCAL_ONDA3F_LABEL = "Local-only Onda 3F"
OPEN_METEO_AUGMENTED_ONDA3F_ID = "open_meteo_augmented_onda3f"
OPEN_METEO_AUGMENTED_ONDA3F_LABEL = "Open-Meteo augmented Onda 3F"
GFS_AUGMENTATION_ID = "om_gfs_previous_runs_raw"
CALIBRATED_REVIEW = "KEEP_CALIBRATED_OPEN_METEO_IN_EXPERIMENT_REVIEW"
PROMOTE_CALIBRATED = "PROMOTE_CALIBRATED_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION"


def _ensure_date(frame: pl.DataFrame) -> pl.DataFrame:
    dtype = frame.schema.get("date_local")
    if dtype == pl.Utf8:
        return frame.with_columns(pl.col("date_local").str.to_date())
    if isinstance(dtype, pl.Datetime):
        return frame.with_columns(pl.col("date_local").dt.date())
    return frame


def _date_range_for_year(year: int) -> tuple[dt.date, dt.date]:
    return dt.date(year, 1, 1), dt.date(year, 12, 31)


def _subset_through_year(
    matrix: pl.DataFrame,
    *,
    train_start: dt.date,
    evaluation_year: int,
) -> pl.DataFrame:
    _, evaluation_end = _date_range_for_year(evaluation_year)
    return matrix.filter(
        (pl.col("date_local") >= train_start) & (pl.col("date_local") <= evaluation_end)
    )


def _common_candidate_keys(
    *,
    local_fold: pl.DataFrame,
    candidates: pl.DataFrame,
    candidate_ids: list[str],
    open_meteo_features: pl.DataFrame | None,
) -> pl.DataFrame:
    common = local_fold.select(["date_local", "cp"]).unique()
    if open_meteo_features is not None:
        common = common.join(
            open_meteo_features.select(["date_local", "cp"]).unique(),
            on=["date_local", "cp"],
            how="inner",
        )
    for candidate_id in candidate_ids:
        candidate_keys = (
            candidates.filter(pl.col("candidate_id") == candidate_id)
            .select(["date_local", "cp"])
            .unique()
        )
        common = common.join(candidate_keys, on=["date_local", "cp"], how="inner")
    return common


def _effective_numeric_columns(
    matrix: pl.DataFrame,
    *,
    numeric_feature_columns: list[str],
    interaction_columns: list[str],
) -> list[str]:
    return [
        column
        for column in [
            *numeric_feature_columns,
            *TEMPORAL_FEATURE_COLUMNS,
            *interaction_columns,
        ]
        if column in matrix.columns and matrix.schema[column].is_numeric()
    ]


def _candidate_label(candidate_id: str) -> str:
    if candidate_id == LOCAL_ONDA3F_ID:
        return LOCAL_ONDA3F_LABEL
    if candidate_id == OPEN_METEO_AUGMENTED_ONDA3F_ID:
        return OPEN_METEO_AUGMENTED_ONDA3F_LABEL
    return candidate_id.replace("_", " ")


def _fold_scope_row(
    matrix: pl.DataFrame,
    *,
    candidate_id: str,
    stage: str,
    outer_test_year: int,
    evaluation_year: int,
    train_start: dt.date,
) -> dict[str, object]:
    train = matrix.filter(pl.col("date_local").dt.year() < evaluation_year)
    evaluation = matrix.filter(pl.col("date_local").dt.year() == evaluation_year)
    train_end = train["date_local"].max() if not train.is_empty() else None
    evaluation_start, evaluation_end = _date_range_for_year(evaluation_year)
    return {
        "stage": stage,
        "outer_test_year": outer_test_year,
        "evaluation_year": evaluation_year,
        "candidate_id": candidate_id,
        "candidate_label": _candidate_label(candidate_id),
        "train_start": train_start,
        "train_end": train_end,
        "train_start_year": train_start.year,
        "train_end_year": train_end.year if train_end is not None else None,
        "evaluation_start": evaluation_start,
        "evaluation_end": evaluation_end,
        "n_train_rows": train.height,
        "n_rows": evaluation.height,
        "production_status": PRODUCTION_STATUS,
    }


def _local_candidate(
    matrix: pl.DataFrame,
    *,
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
    train_x, test_x = _encode(
        train,
        test,
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
    )
    prediction = _ridge_predict(train_x, train_y, test_x)
    return _result_and_predictions(
        test,
        stage=stage,
        outer_test_year=outer_test_year,
        evaluation_year=evaluation_year,
        candidate_id=LOCAL_ONDA3F_ID,
        prediction=prediction,
        actual=test_y,
        model_name="ridge_challenger",
    )


def _provider_candidate(
    matrix: pl.DataFrame,
    *,
    candidate_id: str,
    stage: str,
    outer_test_year: int,
    evaluation_year: int,
    target_column: str,
) -> tuple[dict[str, object], pl.DataFrame]:
    test = matrix.filter(pl.col("date_local").dt.year() == evaluation_year)
    prediction = test["prediction"].cast(pl.Float64).to_numpy()
    actual = test[target_column].to_numpy()
    return _result_and_predictions(
        test,
        stage=stage,
        outer_test_year=outer_test_year,
        evaluation_year=evaluation_year,
        candidate_id=candidate_id,
        prediction=prediction,
        actual=actual,
        model_name="provider_candidate",
    )


def _result_and_predictions(
    test: pl.DataFrame,
    *,
    stage: str,
    outer_test_year: int,
    evaluation_year: int,
    candidate_id: str,
    prediction: np.ndarray,
    actual: np.ndarray,
    model_name: str,
) -> tuple[dict[str, object], pl.DataFrame]:
    absolute = np.abs(actual - prediction)
    predictions = test.select(["date_local", "cp"]).with_columns(
        pl.lit(stage).alias("stage"),
        pl.lit(outer_test_year).alias("outer_test_year"),
        pl.lit(evaluation_year).alias("evaluation_year"),
        pl.lit(candidate_id).alias("candidate_id"),
        pl.lit(_candidate_label(candidate_id)).alias("candidate_label"),
        pl.lit(evaluation_year).alias("test_year"),
        pl.Series("actual", actual),
        pl.Series("prediction", prediction),
        pl.Series("absolute_error", absolute),
        (pl.Series("actual_bracket", actual) + 0.5).floor().cast(pl.Int64),
        (pl.Series("pred_bracket", prediction) + 0.5).floor().cast(pl.Int64),
        pl.lit(model_name).alias("model_name"),
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
            "candidate_label": _candidate_label(candidate_id),
            "test_year": evaluation_year,
            "cp": "ALL",
            "model_name": model_name,
            "n_test": test.height,
            "mae": _mae(actual, prediction),
            "exact_bracket_pct": float(
                predictions["exact_bracket"].cast(pl.Float64).mean() * 100.0
            ),
            "production_status": PRODUCTION_STATUS,
        },
        predictions,
    )


def _metric_summary(predictions: pl.DataFrame) -> pl.DataFrame:
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
        row: dict[str, object] = {
            **pair,
            "n_days": daily.height,
            "n_cp_rows": subset.height,
            "mae": float(subset["absolute_error"].mean()),
            "any_cp_exact_pct": _bool_pct(daily, "any_cp_exact"),
            "n_days_with_cp23": len(cp23_values),
            "cp23_exact_days": (
                int(cp23_values.cast(pl.Int64).sum()) if len(cp23_values) else 0
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


def _candidate_tiebreak_key(row: dict[str, object]) -> tuple[int, float, int]:
    cp23 = row.get("cp23_exact_pct")
    cp23_missing = cp23 is None or (isinstance(cp23, float) and cp23 != cp23)
    cp23_sort = 0.0 if cp23_missing else -float(cp23)
    conservative_order = 0 if row["candidate_id"] == LOCAL_ONDA3F_ID else 1
    return int(cp23_missing), cp23_sort, conservative_order


def _select_winner(validation: pl.DataFrame, *, mae_tolerance: float = 0.001) -> dict[str, object]:
    rows = list(validation.iter_rows(named=True))
    best_mae = min(float(row["mae"]) for row in rows)
    tied = [row for row in rows if float(row["mae"]) <= best_mae + mae_tolerance]
    return sorted(tied, key=_candidate_tiebreak_key)[0]


def _defensive_guardrail(
    predictions: pl.DataFrame,
    *,
    mae_tolerance: float = 0.025,
    exact_tolerance_pp: float = -1.0,
) -> pl.DataFrame:
    if predictions.is_empty() or "binary_macro_regime_label" not in predictions.columns:
        return pl.DataFrame()
    rows: list[dict[str, object]] = []
    validation = predictions.filter(
        (pl.col("stage") == "validation")
        & (pl.col("binary_macro_regime_label") == "macro_non_southerly")
    )
    for outer_test_year in sorted(validation["outer_test_year"].unique().to_list()):
        fold = validation.filter(pl.col("outer_test_year") == outer_test_year)
        augmented = fold.filter(
            pl.col("candidate_id") == OPEN_METEO_AUGMENTED_ONDA3F_ID
        )
        if augmented.is_empty():
            continue
        augmented_mae = float(augmented["absolute_error"].mean())
        augmented_exact = float(augmented["exact_bracket"].cast(pl.Float64).mean() * 100.0)
        for candidate_id in sorted(fold["candidate_id"].unique().to_list()):
            if candidate_id in {
                LOCAL_ONDA3F_ID,
                OPEN_METEO_AUGMENTED_ONDA3F_ID,
                GFS_AUGMENTATION_ID,
            }:
                continue
            candidate = fold.filter(pl.col("candidate_id") == candidate_id)
            candidate_mae = float(candidate["absolute_error"].mean())
            candidate_exact = float(
                candidate["exact_bracket"].cast(pl.Float64).mean() * 100.0
            )
            mae_delta = candidate_mae - augmented_mae
            exact_delta = candidate_exact - augmented_exact
            blocked_mae = mae_delta > mae_tolerance
            blocked_exact = exact_delta < exact_tolerance_pp
            rows.append(
                {
                    "outer_test_year": outer_test_year,
                    "validation_year": int(candidate["evaluation_year"][0]),
                    "candidate_id": candidate_id,
                    "candidate_label": _candidate_label(candidate_id),
                    "baseline_candidate_id": OPEN_METEO_AUGMENTED_ONDA3F_ID,
                    "binary_macro_regime_label": "macro_non_southerly",
                    "candidate_non_southerly_mae": candidate_mae,
                    "augmented_non_southerly_mae": augmented_mae,
                    "non_southerly_mae_delta": mae_delta,
                    "candidate_non_southerly_exact_pct": candidate_exact,
                    "augmented_non_southerly_exact_pct": augmented_exact,
                    "non_southerly_exact_delta_pp": exact_delta,
                    "blocked_by_non_southerly_mae": blocked_mae,
                    "blocked_by_non_southerly_exact": blocked_exact,
                    "eligible_by_non_southerly_guard": not (blocked_mae or blocked_exact),
                    "selected_fallback_candidate_id": (
                        OPEN_METEO_AUGMENTED_ONDA3F_ID
                        if blocked_mae or blocked_exact
                        else ""
                    ),
                    "production_status": PRODUCTION_STATUS,
                }
            )
    return pl.DataFrame(rows, strict=False)


def _selection(
    summary: pl.DataFrame,
    *,
    predictions: pl.DataFrame | None = None,
    selection_rule: str = "validation_mae_then_cp23_exact_then_local",
) -> pl.DataFrame:
    if summary.is_empty():
        return pl.DataFrame()
    guardrail = (
        _defensive_guardrail(predictions)
        if selection_rule == "validation_mae_then_non_southerly_guard_then_cp23"
        and predictions is not None
        else pl.DataFrame()
    )
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
        effective_validation = validation
        if not guardrail.is_empty():
            blocked_ids = set(
                guardrail.filter(
                    (pl.col("outer_test_year") == outer_test_year)
                    & (
                        ~pl.col("eligible_by_non_southerly_guard")
                    )
                )["candidate_id"].to_list()
            )
            if blocked_ids:
                effective_validation = validation.filter(
                    ~pl.col("candidate_id").is_in(list(blocked_ids))
                )
            calibrated_ids = [
                candidate_id
                for candidate_id in effective_validation["candidate_id"].to_list()
                if candidate_id
                not in {
                    LOCAL_ONDA3F_ID,
                    OPEN_METEO_AUGMENTED_ONDA3F_ID,
                    GFS_AUGMENTATION_ID,
                }
            ]
            if not calibrated_ids and OPEN_METEO_AUGMENTED_ONDA3F_ID in set(
                validation["candidate_id"].to_list()
            ):
                effective_validation = validation.filter(
                    pl.col("candidate_id") == OPEN_METEO_AUGMENTED_ONDA3F_ID
                )
        winner = _select_winner(effective_validation)
        winner_test = test.filter(pl.col("candidate_id") == winner["candidate_id"])
        test_row = winner_test.row(0, named=True) if not winner_test.is_empty() else {}
        rows.append(
            {
                "outer_test_year": outer_test_year,
                "validation_year": int(winner["evaluation_year"]),
                "selected_candidate_id": winner["candidate_id"],
                "selected_candidate_label": winner["candidate_label"],
                "selected_validation_mae": winner["mae"],
                "selected_validation_any_cp_exact_pct": winner["any_cp_exact_pct"],
                "selected_validation_cp23_exact_pct": winner["cp23_exact_pct"],
                "selected_test_mae": test_row.get("mae"),
                "selected_test_any_cp_exact_pct": test_row.get("any_cp_exact_pct"),
                "selected_test_cp23_exact_pct": test_row.get("cp23_exact_pct"),
                "validation_candidate_count": validation.height,
                "test_candidate_count": test.height,
                "selection_rule": selection_rule,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False)


def _selected_test_summary(summary: pl.DataFrame, selection: pl.DataFrame) -> pl.DataFrame:
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


def _decision(
    summary: pl.DataFrame,
    selection: pl.DataFrame,
    selected_test: pl.DataFrame,
) -> pl.DataFrame:
    if selection.is_empty():
        return pl.DataFrame(
            [
                {
                    "decision_status": "BLOCK_CALIBRATED_OPEN_METEO_BY_COVERAGE",
                    "decision_rationale": (
                        "Calibrated Open-Meteo coverage did not contain enough "
                        "nested validation/test folds."
                    ),
                    "n_outer_folds": 0,
                    "selected_mean_test_mae": None,
                    "always_local_mean_test_mae": None,
                    "always_open_meteo_augmented_mean_test_mae": None,
                    "always_gfs_previous_runs_mean_test_mae": None,
                    "production_status": PRODUCTION_STATUS,
                }
            ],
            strict=False,
        )
    test_summary = summary.filter(pl.col("stage") == "test")
    local = test_summary.filter(pl.col("candidate_id") == LOCAL_ONDA3F_ID)
    augmented = test_summary.filter(
        pl.col("candidate_id") == OPEN_METEO_AUGMENTED_ONDA3F_ID
    )
    gfs = test_summary.filter(pl.col("candidate_id") == GFS_AUGMENTATION_ID)
    selected_ids = set(selection["selected_candidate_id"].to_list())
    selected_mean = (
        float(selected_test["mae"].mean()) if not selected_test.is_empty() else None
    )
    local_mean = float(local["mae"].mean()) if not local.is_empty() else None
    augmented_mean = (
        float(augmented["mae"].mean()) if not augmented.is_empty() else None
    )
    gfs_mean = float(gfs["mae"].mean()) if not gfs.is_empty() else None
    n_outer_folds = selection.height
    calibrated_selected = any(
        candidate_id
        not in {LOCAL_ONDA3F_ID, OPEN_METEO_AUGMENTED_ONDA3F_ID, GFS_AUGMENTATION_ID}
        for candidate_id in selected_ids
    )
    if calibrated_selected and n_outer_folds >= 2:
        status = PROMOTE_CALIBRATED
        rationale = "Calibrated Open-Meteo was selected in enough outer folds."
    elif selected_ids == {LOCAL_ONDA3F_ID}:
        status = "KEEP_LOCAL_ONLY_REFERENCE"
        rationale = "Nested validation selected the local-only reference."
    elif selected_ids == {GFS_AUGMENTATION_ID}:
        status = "KEEP_GFS_PREVIOUS_RUNS_AUGMENTATION"
        rationale = "Nested validation selected the raw GFS Previous Runs candidate."
    elif selected_ids == {OPEN_METEO_AUGMENTED_ONDA3F_ID}:
        status = "KEEP_GFS_PREVIOUS_RUNS_AUGMENTATION"
        rationale = "Nested validation selected the current GFS-augmented Onda 3F."
    else:
        status = CALIBRATED_REVIEW
        rationale = (
            "Calibrated Open-Meteo improved or was selected, but coverage/fold "
            "support is not sufficient for a final model decision."
        )
    return pl.DataFrame(
        [
            {
                "decision_status": status,
                "decision_rationale": rationale,
                "n_outer_folds": n_outer_folds,
                "selected_mean_test_mae": selected_mean,
                "always_local_mean_test_mae": local_mean,
                "always_open_meteo_augmented_mean_test_mae": augmented_mean,
                "always_gfs_previous_runs_mean_test_mae": gfs_mean,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def build_open_meteo_calibrated_nested_validation(
    *,
    local_features: pl.DataFrame,
    calibrated_candidates: pl.DataFrame,
    open_meteo_features: pl.DataFrame | None = None,
    test_years: list[int],
    train_start: dt.date,
    numeric_feature_columns: list[str] | None = None,
    categorical_feature_columns: list[str] | None = None,
    open_meteo_numeric_columns: list[str] | None = None,
    target_column: str = "tmax_int",
    selection_rule: str = "validation_mae_then_cp23_exact_then_local",
) -> dict[str, pl.DataFrame]:
    local = add_pooled_temporal_features(
        normalize_pooled_cp_column(_ensure_date(local_features))
    )
    if "binary_macro_regime_label" in local.columns:
        local, interaction_columns = add_binary_macro_interaction_features(local)
    else:
        interaction_columns = []
    candidates = normalize_pooled_cp_column(_ensure_date(calibrated_candidates))
    if candidates.height - candidates.select(
        ["date_local", "cp", "candidate_id"]
    ).unique().height:
        raise ValueError("duplicate calibrated Open-Meteo candidate keys")
    om_features: pl.DataFrame | None = None
    if open_meteo_features is not None:
        om_features = normalize_pooled_cp_column(_ensure_date(open_meteo_features))
        if om_features.height - om_features.select(["date_local", "cp"]).unique().height:
            raise ValueError("duplicate Open-Meteo feature keys for calibrated nested join")
        if open_meteo_numeric_columns is None:
            open_meteo_numeric_columns = [
                column
                for column in om_features.columns
                if column.startswith("om_prev_d1_")
                and om_features.schema[column].is_numeric()
            ]
    if open_meteo_numeric_columns is None:
        open_meteo_numeric_columns = []
    if numeric_feature_columns is None:
        numeric_feature_columns = [
            column
            for column in ["k_cp", "slope_3h", "dewpoint_depression"]
            if column in local.columns
        ]
    if categorical_feature_columns is None:
        categorical_feature_columns = [
            column for column in ["binary_macro_regime_label"] if column in local.columns
        ]
    effective_categorical = [
        column for column in categorical_feature_columns if column in local.columns
    ]
    local_numeric = _effective_numeric_columns(
        local,
        numeric_feature_columns=numeric_feature_columns,
        interaction_columns=interaction_columns,
    )
    augmented_numeric = [
        *local_numeric,
        *[
            column
            for column in open_meteo_numeric_columns
            if om_features is not None
            and column in om_features.columns
            and om_features.schema[column].is_numeric()
        ],
    ]
    candidate_ids = sorted(candidates["candidate_id"].unique().to_list())
    comparison_ids = [LOCAL_ONDA3F_ID]
    if om_features is not None:
        comparison_ids.append(OPEN_METEO_AUGMENTED_ONDA3F_ID)
    comparison_ids.extend(candidate_ids)
    scope_rows: list[dict[str, object]] = []
    result_rows: list[dict[str, object]] = []
    prediction_frames: list[pl.DataFrame] = []

    for outer_test_year in test_years:
        for stage, evaluation_year in [
            ("validation", outer_test_year - 1),
            ("test", outer_test_year),
        ]:
            local_fold_all = _subset_through_year(
                local,
                train_start=train_start,
                evaluation_year=evaluation_year,
            )
            fold_candidate_rows = candidates.filter(
                (pl.col("date_local") >= train_start)
                & (
                    pl.col("date_local")
                    <= _date_range_for_year(evaluation_year)[1]
                )
            )
            common_keys = _common_candidate_keys(
                local_fold=local_fold_all,
                candidates=fold_candidate_rows,
                candidate_ids=candidate_ids,
                open_meteo_features=om_features,
            )
            local_fold = local_fold_all.join(
                common_keys,
                on=["date_local", "cp"],
                how="inner",
            )
            has_valid_local_fold = not (
                local_fold.filter(
                    pl.col("date_local").dt.year() < evaluation_year
                ).is_empty()
                or local_fold.filter(
                    pl.col("date_local").dt.year() == evaluation_year
                ).is_empty()
            )
            for candidate_id in comparison_ids:
                if candidate_id == LOCAL_ONDA3F_ID:
                    candidate_matrix = local_fold
                elif candidate_id == OPEN_METEO_AUGMENTED_ONDA3F_ID:
                    if om_features is None:
                        continue
                    candidate_matrix = local_fold.join(
                        om_features,
                        on=["date_local", "cp"],
                        how="inner",
                    )
                else:
                    candidate_rows = fold_candidate_rows.filter(
                        pl.col("candidate_id") == candidate_id
                    )
                    candidate_matrix = local_fold.join(
                        candidate_rows.select(
                            ["date_local", "cp", "candidate_id", "prediction"]
                        ),
                        on=["date_local", "cp"],
                        how="inner",
                    )
                scope_rows.append(
                    _fold_scope_row(
                        candidate_matrix,
                        candidate_id=candidate_id,
                        stage=stage,
                        outer_test_year=outer_test_year,
                        evaluation_year=evaluation_year,
                        train_start=train_start,
                    )
                )
                if not has_valid_local_fold:
                    continue
                if candidate_id == LOCAL_ONDA3F_ID:
                    result, predictions = _local_candidate(
                        candidate_matrix,
                        stage=stage,
                        outer_test_year=outer_test_year,
                        evaluation_year=evaluation_year,
                        numeric_columns=local_numeric,
                        categorical_columns=effective_categorical,
                        target_column=target_column,
                    )
                elif candidate_id == OPEN_METEO_AUGMENTED_ONDA3F_ID:
                    result, predictions = _local_candidate(
                        candidate_matrix,
                        stage=stage,
                        outer_test_year=outer_test_year,
                        evaluation_year=evaluation_year,
                        numeric_columns=augmented_numeric,
                        categorical_columns=effective_categorical,
                        target_column=target_column,
                    )
                    result["candidate_id"] = OPEN_METEO_AUGMENTED_ONDA3F_ID
                    result["candidate_label"] = OPEN_METEO_AUGMENTED_ONDA3F_LABEL
                    predictions = predictions.with_columns(
                        pl.lit(OPEN_METEO_AUGMENTED_ONDA3F_ID).alias("candidate_id"),
                        pl.lit(OPEN_METEO_AUGMENTED_ONDA3F_LABEL).alias(
                            "candidate_label"
                        ),
                    )
                else:
                    result, predictions = _provider_candidate(
                        candidate_matrix,
                        candidate_id=candidate_id,
                        stage=stage,
                        outer_test_year=outer_test_year,
                        evaluation_year=evaluation_year,
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
    summary = _metric_summary(predictions)
    guardrail = _defensive_guardrail(predictions)
    selection = _selection(
        summary,
        predictions=predictions,
        selection_rule=selection_rule,
    )
    selected_test = _selected_test_summary(summary, selection)
    return {
        "onda3_open_meteo_calibrated_nested_candidate_scope_v1": pl.DataFrame(
            scope_rows,
            strict=False,
        ),
        "onda3_open_meteo_calibrated_nested_model_results_v1": results,
        "onda3_open_meteo_calibrated_nested_predictions_v1": predictions,
        "onda3_open_meteo_calibrated_nested_metric_summary_v1": summary,
        "onda3_open_meteo_calibrated_nested_selection_v1": selection,
        "onda3_open_meteo_calibrated_nested_selected_test_summary_v1": selected_test,
        "onda3_open_meteo_calibrated_nested_by_month_v1": _open_meteo_by_month(
            predictions
        ),
        "onda3_open_meteo_calibrated_nested_by_month_cp_v1": _open_meteo_by_month_cp(
            predictions
        ),
        "onda3_open_meteo_calibrated_nested_regime_performance_v1": (
            _open_meteo_regime_performance(predictions)
        ),
        "onda3_open_meteo_calibrated_nested_decision_update_v1": _decision(
            summary,
            selection,
            selected_test,
        ),
        "onda3_open_meteo_defensive_selection_guardrail_v1": guardrail,
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


def render_open_meteo_calibrated_nested_validation_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: object,
) -> str:
    return "\n\n".join(
        [
            "# Onda 3 Open-Meteo Calibrated Nested Validation Report",
            f"Generated: {today}",
            f"production_status: {PRODUCTION_STATUS}",
            (
                "Calibrated Open-Meteo candidates are compared against local-only "
                "Onda 3F and raw GFS Previous Runs on identical covered rows."
            ),
            "## Decision",
            _markdown_table(
                artifacts["onda3_open_meteo_calibrated_nested_decision_update_v1"]
            ),
            "## Candidate Scope",
            _markdown_table(
                artifacts["onda3_open_meteo_calibrated_nested_candidate_scope_v1"],
                max_rows=30,
            ),
            "## Selection",
            _markdown_table(
                artifacts["onda3_open_meteo_calibrated_nested_selection_v1"],
                max_rows=30,
            ),
            "## Selected Test Summary",
            _markdown_table(
                artifacts[
                    "onda3_open_meteo_calibrated_nested_selected_test_summary_v1"
                ],
                max_rows=30,
            ),
            "## Candidate Metrics",
            _markdown_table(
                artifacts["onda3_open_meteo_calibrated_nested_metric_summary_v1"],
                max_rows=50,
            ),
            "## Regime Performance",
            _markdown_table(
                artifacts[
                    "onda3_open_meteo_calibrated_nested_regime_performance_v1"
                ],
                max_rows=50,
            ),
            "## Defensive Selection Guardrail",
            _markdown_table(
                artifacts["onda3_open_meteo_defensive_selection_guardrail_v1"],
                max_rows=50,
            ),
        ]
    ) + "\n"


def write_open_meteo_calibrated_nested_validation_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: object,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for key, filename in CALIBRATED_NESTED_FILENAMES.items():
        path = output_dir / filename
        artifacts[key].write_csv(path)
        paths[key] = path
    report_path = output_dir / "onda3_open_meteo_calibrated_nested_report_v1.md"
    report_path.write_text(
        render_open_meteo_calibrated_nested_validation_report(
            artifacts,
            today=today,
        ),
        encoding="utf-8",
    )
    paths["onda3_open_meteo_calibrated_nested_report_md"] = report_path
    return paths
