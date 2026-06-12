from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.onda3._interactions import build_onda3_interaction_iteration
from solarstorm.onda3._model_attempt_review import CP_SET
from solarstorm.onda3._pooled_iteration import build_onda3_pooled_iteration

PRODUCTION_STATUS = "EXPERIMENT_ONLY"
ONDA3D_ID = "onda3_d_binary_macro_interactions"
ONDA3F_ID = "onda3_f_pooled_temporal_regime"
ONDA3D_LABEL = "Onda 3D binary-macro interactions"
ONDA3F_LABEL = "Onda 3F pooled temporal/regime"
CANDIDATE_LABELS = {
    ONDA3D_ID: ONDA3D_LABEL,
    ONDA3F_ID: ONDA3F_LABEL,
}
ONDA3H_NUMERIC_FEATURE_ALLOWLIST = {
    "k_cp",
    "slope_3h",
    "hours_to_expected_peak",
    "dewpoint_depression",
    "tmax_dminus1",
    "tmin_delta_tmax",
    "wind_dir_change_s_to_n",
    "precip_disruption",
    "cloud_cover_suppression",
    "pressure_trend_3h",
    "foehn_score",
    "warming_rate_06_09",
    "nocturnal_plateau_flag",
    "dewpoint_collapse_rate_3h",
    "prefrontal_warming_window",
    "nw_sector_not_foehn",
    "cloud_base_transparency",
}
ONDA3H_CATEGORICAL_FEATURE_ALLOWLIST = {"binary_macro_regime_label"}
DECISION_PROMOTE_HARNESS = "PROMOTE_NESTED_VALIDATION_AS_MODEL_SELECTION_HARNESS"
DECISION_KEEP_ONDA3D = "KEEP_ONDA3D_REFERENCE_AFTER_NESTED_VALIDATION"
DECISION_KEEP_BOTH = "KEEP_BOTH_CANDIDATES_AFTER_NESTED_VALIDATION"
NESTED_FILENAMES = {
    "onda3_nested_fold_scope_v1": "onda3_nested_fold_scope_v1.csv",
    "onda3_nested_model_results_v1": "onda3_nested_model_results_v1.csv",
    "onda3_nested_predictions_v1": "onda3_nested_predictions_v1.csv",
    "onda3_nested_metric_summary_v1": "onda3_nested_metric_summary_v1.csv",
    "onda3_nested_selection_v1": "onda3_nested_selection_v1.csv",
    "onda3_nested_test_selected_summary_v1": (
        "onda3_nested_test_selected_summary_v1.csv"
    ),
    "onda3_nested_by_month_v1": "onda3_nested_by_month_v1.csv",
    "onda3_nested_by_month_cp_v1": "onda3_nested_by_month_cp_v1.csv",
    "onda3_nested_regime_performance_v1": "onda3_nested_regime_performance_v1.csv",
    "onda3_nested_decision_update_v1": "onda3_nested_decision_update_v1.csv",
}


def select_onda3h_feature_columns(matrix: pl.DataFrame) -> tuple[list[str], list[str]]:
    numeric_features = [
        column
        for column in sorted(ONDA3H_NUMERIC_FEATURE_ALLOWLIST)
        if column in matrix.columns and matrix.schema[column].is_numeric()
    ]
    categorical_features = [
        column
        for column in sorted(ONDA3H_CATEGORICAL_FEATURE_ALLOWLIST)
        if column in matrix.columns
    ]
    return numeric_features, categorical_features


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


def _candidate_assignments(matrix: pl.DataFrame) -> pl.DataFrame:
    if "binary_macro_regime_label" not in matrix.columns:
        return pl.DataFrame()
    return matrix.select(["date_local", "cp", "binary_macro_regime_label"]).unique()


def _candidate_results(
    results: pl.DataFrame,
    *,
    candidate_id: str,
    stage: str,
    outer_test_year: int,
    evaluation_year: int,
) -> pl.DataFrame:
    if results.is_empty():
        return results
    return results.with_columns(
        pl.lit(stage).alias("stage"),
        pl.lit(outer_test_year).alias("outer_test_year"),
        pl.lit(evaluation_year).alias("evaluation_year"),
        pl.lit(candidate_id).alias("candidate_id"),
        pl.lit(CANDIDATE_LABELS[candidate_id]).alias("candidate_label"),
        pl.lit(PRODUCTION_STATUS).alias("production_status"),
    ).select(
        [
            "stage",
            "outer_test_year",
            "evaluation_year",
            "candidate_id",
            "candidate_label",
            "test_year",
            "cp",
            "model_name",
            "n_train",
            "n_test",
            "mae",
            "beats_train_mean_null",
            "production_status",
        ]
    )


def _normalize_predictions(
    predictions: pl.DataFrame,
    *,
    matrix: pl.DataFrame,
    candidate_id: str,
    stage: str,
    outer_test_year: int,
    evaluation_year: int,
) -> pl.DataFrame:
    if predictions.is_empty():
        return predictions

    frame = _ensure_date(predictions)
    if "test_year" not in frame.columns:
        frame = frame.with_columns(pl.lit(evaluation_year).alias("test_year"))
    if "model_name" not in frame.columns:
        frame = frame.with_columns(pl.lit("ridge_challenger").alias("model_name"))

    assignments = _candidate_assignments(matrix)
    if (
        not assignments.is_empty()
        and "binary_macro_regime_label" not in frame.columns
    ):
        frame = frame.join(assignments, on=["date_local", "cp"], how="left")

    return frame.with_columns(
        pl.lit(stage).alias("stage"),
        pl.lit(outer_test_year).alias("outer_test_year"),
        pl.lit(evaluation_year).alias("evaluation_year"),
        pl.lit(candidate_id).alias("candidate_id"),
        pl.lit(CANDIDATE_LABELS[candidate_id]).alias("candidate_label"),
        (pl.col("actual") - pl.col("prediction")).abs().alias("absolute_error"),
        (pl.col("actual") + 0.5).floor().cast(pl.Int64).alias("actual_bracket"),
        (pl.col("prediction") + 0.5).floor().cast(pl.Int64).alias("pred_bracket"),
        pl.col("date_local").dt.strftime("%Y-%m").alias("month"),
        pl.col("date_local").dt.year().alias("calendar_year"),
        pl.lit(PRODUCTION_STATUS).alias("production_status"),
    ).with_columns(
        (pl.col("pred_bracket") == pl.col("actual_bracket")).alias("exact_bracket")
    ).select(
        [
            "stage",
            "outer_test_year",
            "evaluation_year",
            "candidate_id",
            "candidate_label",
            "date_local",
            "calendar_year",
            "test_year",
            "month",
            "cp",
            "actual",
            "prediction",
            "absolute_error",
            "actual_bracket",
            "pred_bracket",
            "exact_bracket",
            *(
                ["binary_macro_regime_label"]
                if "binary_macro_regime_label" in frame.columns
                else []
            ),
            "model_name",
            "production_status",
        ]
    )


def _run_candidate(
    matrix: pl.DataFrame,
    *,
    candidate_id: str,
    stage: str,
    outer_test_year: int,
    evaluation_year: int,
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    target_column: str,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    if candidate_id == ONDA3D_ID:
        artifacts = build_onda3_interaction_iteration(
            matrix,
            test_years=[evaluation_year],
            numeric_feature_columns=numeric_feature_columns,
            categorical_feature_columns=[
                column for column in ["binary_macro_regime_label"] if column in matrix.columns
            ],
            target_column=target_column,
        )
        result_key = "onda3_interaction_model_results_v1"
        prediction_key = "onda3_interaction_predictions_v1"
    elif candidate_id == ONDA3F_ID:
        artifacts = build_onda3_pooled_iteration(
            matrix,
            test_years=[evaluation_year],
            numeric_feature_columns=numeric_feature_columns,
            categorical_feature_columns=[
                column for column in categorical_feature_columns if column in matrix.columns
            ],
            target_column=target_column,
        )
        result_key = "onda3_pooled_model_results_v1"
        prediction_key = "onda3_pooled_predictions_v1"
    else:
        raise ValueError(f"unknown Onda 3 nested candidate: {candidate_id}")

    return (
        _candidate_results(
            artifacts[result_key],
            candidate_id=candidate_id,
            stage=stage,
            outer_test_year=outer_test_year,
            evaluation_year=evaluation_year,
        ),
        _normalize_predictions(
            artifacts[prediction_key],
            matrix=matrix,
            candidate_id=candidate_id,
            stage=stage,
            outer_test_year=outer_test_year,
            evaluation_year=evaluation_year,
        ),
    )


def _bool_pct(frame: pl.DataFrame, column: str) -> float | None:
    if frame.is_empty() or column not in frame.columns:
        return None
    values = frame[column].drop_nulls()
    if values.is_empty():
        return None
    return float(values.cast(pl.Float64).mean() * 100.0)


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
        n_days_with_cp23 = len(cp23_values)
        cp23_exact_days = (
            int(cp23_values.cast(pl.Int64).sum()) if n_days_with_cp23 else 0
        )
        row: dict[str, object] = {
            **pair,
            "n_days": daily.height,
            "n_cp_rows": subset.height,
            "mae": float(subset["absolute_error"].mean()),
            "any_cp_exact_pct": _bool_pct(daily, "any_cp_exact"),
            "n_days_with_cp23": n_days_with_cp23,
            "cp23_exact_days": cp23_exact_days,
            "cp23_exact_pct": _bool_pct(daily, "cp23_exact"),
            "production_status": PRODUCTION_STATUS,
        }
        for cp in CP_SET:
            cp_subset = subset.filter(pl.col("cp") == cp)
            row[f"cp_{cp.replace(':', '')}_exact_pct"] = _bool_pct(
                cp_subset,
                "exact_bracket",
            )
        rows.append(row)
    return pl.DataFrame(rows, strict=False)


def _candidate_tiebreak_key(row: dict[str, object]) -> tuple[int, float, int]:
    cp23 = row.get("cp23_exact_pct")
    cp23_missing = cp23 is None or (
        isinstance(cp23, float) and cp23 != cp23
    )
    cp23_sort = 0.0 if cp23_missing else -float(cp23)
    conservative_order = 0 if row["candidate_id"] == ONDA3D_ID else 1
    return int(cp23_missing), cp23_sort, conservative_order


def _select_validation_winner(
    validation: pl.DataFrame,
    *,
    mae_tolerance: float = 0.001,
) -> dict[str, object]:
    rows = list(validation.iter_rows(named=True))
    best_mae = min(float(row["mae"]) for row in rows)
    tied_rows = [
        row for row in rows if float(row["mae"]) <= best_mae + mae_tolerance
    ]
    return sorted(tied_rows, key=_candidate_tiebreak_key)[0]


def _selection(summary: pl.DataFrame) -> pl.DataFrame:
    if summary.is_empty():
        return pl.DataFrame()
    rows: list[dict[str, object]] = []
    for outer_test_year in sorted(summary["outer_test_year"].unique().to_list()):
        validation = summary.filter(
            (pl.col("outer_test_year") == outer_test_year)
            & (pl.col("stage") == "validation")
        )
        test = summary.filter(
            (pl.col("outer_test_year") == outer_test_year) & (pl.col("stage") == "test")
        )
        if validation.is_empty() or test.is_empty():
            continue
        winner = _select_validation_winner(validation)
        winner_test_rows = test.filter(pl.col("candidate_id") == winner["candidate_id"])
        winner_test = winner_test_rows.row(0, named=True) if not winner_test_rows.is_empty() else {}
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
                "selection_rule": "validation_mae_then_cp23_exact_then_onda3d",
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
                [
                    "outer_test_year",
                    "selected_candidate_id",
                    "selection_rule",
                ]
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


def _by_month(predictions: pl.DataFrame) -> pl.DataFrame:
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
        daily.group_by(["stage", "outer_test_year", "candidate_id", "candidate_label", "month"])
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


def _by_month_cp(predictions: pl.DataFrame) -> pl.DataFrame:
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


def _regime_performance(predictions: pl.DataFrame) -> pl.DataFrame:
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


def _fold_scope_rows(
    fold_matrix: pl.DataFrame,
    *,
    stage: str,
    outer_test_year: int,
    evaluation_year: int,
    train_start: dt.date,
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


def _decision(
    *,
    summary: pl.DataFrame,
    selection: pl.DataFrame,
    selected_test: pl.DataFrame,
) -> pl.DataFrame:
    if selection.is_empty():
        return pl.DataFrame(
            [
                {
                    "decision_status": DECISION_KEEP_BOTH,
                    "decision_rationale": "No valid nested validation folds were available.",
                    "n_outer_folds": 0,
                    "selected_mean_test_mae": None,
                    "always_onda3d_mean_test_mae": None,
                    "always_onda3f_mean_test_mae": None,
                    "production_status": PRODUCTION_STATUS,
                }
            ],
            strict=False,
        )

    test_summary = summary.filter(pl.col("stage") == "test")
    d_rows = test_summary.filter(pl.col("candidate_id") == ONDA3D_ID)
    f_rows = test_summary.filter(pl.col("candidate_id") == ONDA3F_ID)
    selected_ids = set(selection["selected_candidate_id"].to_list())
    selected_mean = (
        float(selected_test["mae"].mean()) if not selected_test.is_empty() else None
    )
    d_mean = float(d_rows["mae"].mean()) if not d_rows.is_empty() else None
    f_mean = float(f_rows["mae"].mean()) if not f_rows.is_empty() else None

    if selected_ids == {ONDA3D_ID}:
        status = DECISION_KEEP_ONDA3D
        rationale = "Nested validation selected Onda 3D in every valid outer fold."
    elif len(selected_ids) > 1:
        status = DECISION_KEEP_BOTH
        rationale = "Nested validation selected different candidates across outer folds."
    else:
        status = DECISION_PROMOTE_HARNESS
        rationale = (
            "Nested validation selected Onda 3F consistently; keep the nested "
            "harness as the model-selection gate before any Open-Meteo work."
        )

    return pl.DataFrame(
        [
            {
                "decision_status": status,
                "decision_rationale": rationale,
                "n_outer_folds": selection.height,
                "selected_mean_test_mae": selected_mean,
                "always_onda3d_mean_test_mae": d_mean,
                "always_onda3f_mean_test_mae": f_mean,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def build_onda3_nested_validation(
    matrix: pl.DataFrame,
    *,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    train_start: dt.date,
    target_column: str = "tmax_int",
) -> dict[str, pl.DataFrame]:
    matrix = _ensure_date(matrix)
    fold_scope_rows: list[dict[str, object]] = []
    result_frames: list[pl.DataFrame] = []
    prediction_frames: list[pl.DataFrame] = []

    for outer_test_year in test_years:
        for stage, evaluation_year in [
            ("validation", outer_test_year - 1),
            ("test", outer_test_year),
        ]:
            fold_matrix = _subset_through_year(
                matrix,
                train_start=train_start,
                evaluation_year=evaluation_year,
            )
            fold_scope_rows.append(
                _fold_scope_rows(
                    fold_matrix,
                    stage=stage,
                    outer_test_year=outer_test_year,
                    evaluation_year=evaluation_year,
                    train_start=train_start,
                )
            )
            if (
                fold_matrix.filter(pl.col("date_local").dt.year() < evaluation_year).is_empty()
                or fold_matrix.filter(
                    pl.col("date_local").dt.year() == evaluation_year
                ).is_empty()
            ):
                continue
            for candidate_id in (ONDA3D_ID, ONDA3F_ID):
                results, predictions = _run_candidate(
                    fold_matrix,
                    candidate_id=candidate_id,
                    stage=stage,
                    outer_test_year=outer_test_year,
                    evaluation_year=evaluation_year,
                    numeric_feature_columns=[
                        column
                        for column in numeric_feature_columns
                        if column in fold_matrix.columns
                    ],
                    categorical_feature_columns=[
                        column
                        for column in categorical_feature_columns
                        if column in fold_matrix.columns
                    ],
                    target_column=target_column,
                )
                if not results.is_empty():
                    result_frames.append(results)
                if not predictions.is_empty():
                    prediction_frames.append(predictions)

    model_results = (
        pl.concat(result_frames, how="diagonal_relaxed")
        if result_frames
        else pl.DataFrame()
    )
    predictions = (
        pl.concat(prediction_frames, how="diagonal_relaxed")
        if prediction_frames
        else pl.DataFrame()
    )
    metric_summary = _metric_summary(predictions)
    selection = _selection(metric_summary)
    selected_test = _selected_test_summary(metric_summary, selection)

    return {
        "onda3_nested_fold_scope_v1": pl.DataFrame(fold_scope_rows, strict=False),
        "onda3_nested_model_results_v1": model_results,
        "onda3_nested_predictions_v1": predictions,
        "onda3_nested_metric_summary_v1": metric_summary,
        "onda3_nested_selection_v1": selection,
        "onda3_nested_test_selected_summary_v1": selected_test,
        "onda3_nested_by_month_v1": _by_month(predictions),
        "onda3_nested_by_month_cp_v1": _by_month_cp(predictions),
        "onda3_nested_regime_performance_v1": _regime_performance(predictions),
        "onda3_nested_decision_update_v1": _decision(
            summary=metric_summary,
            selection=selection,
            selected_test=selected_test,
        ),
    }


def _format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if value != value:
            return ""
        return f"{value:.3f}"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, dt.date):
        return value.isoformat()
    return str(value)


def _markdown_table(df: pl.DataFrame, *, max_rows: int = 30) -> str:
    if df.is_empty():
        return "_No rows._"
    columns = df.columns
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_format_value(row[column]) for column in columns) + " |"
        for row in df.head(max_rows).iter_rows(named=True)
    ]
    suffix = ""
    if df.height > max_rows:
        suffix = f"\n\n_Showing {max_rows} of {df.height} rows. Full table is in CSV._"
    return "\n".join([header, divider, *body]) + suffix


def render_onda3_nested_validation_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    def frame(name: str) -> pl.DataFrame:
        return artifacts.get(name, pl.DataFrame())

    return "\n\n".join(
        [
            "# Onda 3H Nested Validation Report",
            f"Generated: {today.isoformat()}",
            "",
            (
                "Scope: pre-Open-Meteo local-data nested validation. "
                "Open-Meteo forecast data is not integrated."
            ),
            "All outputs remain EXPERIMENT_ONLY.",
            "## Decision",
            _markdown_table(frame("onda3_nested_decision_update_v1")),
            "## Fold Scope",
            _markdown_table(frame("onda3_nested_fold_scope_v1"), max_rows=20),
            "## Validation Selection",
            _markdown_table(frame("onda3_nested_selection_v1"), max_rows=20),
            "## Selected Test Summary",
            _markdown_table(
                frame("onda3_nested_test_selected_summary_v1"),
                max_rows=20,
            ),
            "## Candidate Metric Summary",
            _markdown_table(frame("onda3_nested_metric_summary_v1"), max_rows=40),
            "## Regime Performance",
            _markdown_table(frame("onda3_nested_regime_performance_v1"), max_rows=40),
            "## Interpretation",
            "\n".join(
                [
                    "- Validation uses train years ending at Y-2.",
                    "- Test uses the validation-selected design refit through Y-1.",
                    "- Onda 3H is a model-selection gate, not a production promotion.",
                ]
            ),
        ]
    ) + "\n"


def write_onda3_nested_validation_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact_name, filename in NESTED_FILENAMES.items():
        if artifact_name not in artifacts:
            continue
        path = output_dir / filename
        artifacts[artifact_name].write_csv(path)
        paths[f"{artifact_name}_csv"] = path
        md_path = path.with_suffix(".md")
        md_path.write_text(
            f"# {artifact_name}\n\n{_markdown_table(artifacts[artifact_name])}\n",
            encoding="utf-8",
        )
        paths[f"{artifact_name}_md"] = md_path

    report_path = output_dir / "onda3_nested_validation_report_v1.md"
    report_path.write_text(
        render_onda3_nested_validation_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["onda3_nested_validation_report_md"] = report_path
    return paths
