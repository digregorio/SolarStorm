from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import numpy as np
import polars as pl

from solarstorm.onda3._baseline_model import _mae, _ridge_predict
from solarstorm.onda3._interactions import add_binary_macro_interaction_features
from solarstorm.onda3._model_attempt_review import (
    build_month_cp_bracket_summary,
    build_month_day_bracket_summary,
    build_overall_bracket_summary,
    build_regime_cp_performance_summary,
    build_regime_performance_summary,
    enrich_predictions_with_brackets,
)

PRODUCTION_STATUS = "EXPERIMENT_ONLY"
CP_ORDER = ("20:00", "21:00", "22:00", "23:00")
CP_INDEX = {cp: index for index, cp in enumerate(CP_ORDER)}
POOLED_ITERATION_ID = "onda3_f_pooled_temporal_regime"
POOLED_ITERATION_LABEL = "Onda 3F pooled temporal/regime"
TEMPORAL_FEATURE_COLUMNS = (
    "cp_sin",
    "cp_cos",
    "month_sin",
    "month_cos",
    "doy_sin",
    "doy_cos",
)
DECISION_READY_FOR_AUDIT = "READY_FOR_ONDA3_AUDIT_COMPARISON"
DECISION_KEEP_REVIEW = "KEEP_IN_ONDA3_EXPERIMENT_REVIEW"
POOLED_FILENAMES = {
    "onda3_pooled_feature_audit_v1": "onda3_pooled_feature_audit_v1.csv",
    "onda3_pooled_model_results_v1": "onda3_pooled_model_results_v1.csv",
    "onda3_pooled_predictions_v1": "onda3_pooled_predictions_v1.csv",
    "onda3_pooled_bracket_overall_v1": "onda3_pooled_bracket_overall_v1.csv",
    "onda3_pooled_bracket_by_month_day_v1": (
        "onda3_pooled_bracket_by_month_day_v1.csv"
    ),
    "onda3_pooled_bracket_by_month_cp_v1": (
        "onda3_pooled_bracket_by_month_cp_v1.csv"
    ),
    "onda3_pooled_regime_performance_v1": "onda3_pooled_regime_performance_v1.csv",
    "onda3_pooled_regime_by_cp_v1": "onda3_pooled_regime_by_cp_v1.csv",
    "onda3_pooled_slice_diagnostics_v1": "onda3_pooled_slice_diagnostics_v1.csv",
    "onda3_pooled_uncertainty_abstention_v1": (
        "onda3_pooled_uncertainty_abstention_v1.csv"
    ),
    "onda3_pooled_temporal_diagnostics_v1": (
        "onda3_pooled_temporal_diagnostics_v1.csv"
    ),
    "onda3_pooled_decision_update_v1": "onda3_pooled_decision_update_v1.csv",
}


def _canonical_cp_value(value: object) -> str:
    if isinstance(value, dt.time):
        return value.strftime("%H:%M")
    text = str(value).strip()
    if len(text) >= 5 and text[2] == ":":
        hour = text[:2]
        minute = text[3:5]
        if hour.isdigit() and minute.isdigit():
            return f"{hour}:{minute}"
    return text


def normalize_pooled_cp_column(frame: pl.DataFrame) -> pl.DataFrame:
    if "cp" not in frame.columns:
        return frame
    return frame.with_columns(
        pl.Series("cp", [_canonical_cp_value(cp) for cp in frame["cp"].to_list()])
    )


def _ensure_date(frame: pl.DataFrame) -> pl.DataFrame:
    dtype = frame.schema.get("date_local")
    if dtype == pl.Utf8:
        return frame.with_columns(pl.col("date_local").str.to_date())
    if isinstance(dtype, pl.Datetime):
        return frame.with_columns(pl.col("date_local").dt.date())
    return frame


def add_pooled_temporal_features(matrix: pl.DataFrame) -> pl.DataFrame:
    frame = normalize_pooled_cp_column(_ensure_date(matrix))
    cp_values = frame["cp"].to_list()
    cp_angles = [
        2.0 * math.pi * CP_INDEX.get(cp, 0) / float(len(CP_ORDER))
        for cp in cp_values
    ]
    dates = frame["date_local"].to_list()
    month_angles = [2.0 * math.pi * (date.month - 1) / 12.0 for date in dates]
    doy_angles = [
        2.0 * math.pi * (date.timetuple().tm_yday - 1) / 365.25 for date in dates
    ]
    return frame.with_columns(
        pl.Series("cp_sin", [math.sin(angle) for angle in cp_angles]),
        pl.Series("cp_cos", [math.cos(angle) for angle in cp_angles]),
        pl.Series("month_sin", [math.sin(angle) for angle in month_angles]),
        pl.Series("month_cos", [math.cos(angle) for angle in month_angles]),
        pl.Series("doy_sin", [math.sin(angle) for angle in doy_angles]),
        pl.Series("doy_cos", [math.cos(angle) for angle in doy_angles]),
    )


def _encode_features(
    train: pl.DataFrame,
    test: pl.DataFrame,
    *,
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
) -> tuple[np.ndarray, np.ndarray]:
    train_parts = (
        [train.select(numeric_feature_columns).to_numpy()]
        if numeric_feature_columns
        else []
    )
    test_parts = (
        [test.select(numeric_feature_columns).to_numpy()]
        if numeric_feature_columns
        else []
    )

    for column in categorical_feature_columns:
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
        raise ValueError("Onda 3F requires at least one numeric or categorical feature.")
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
        pl.lit(PRODUCTION_STATUS).alias("production_status"),
    )


def _prediction_assignments(matrix: pl.DataFrame) -> pl.DataFrame | None:
    if "binary_macro_regime_label" not in matrix.columns:
        return None
    return matrix.select(["date_local", "cp", "binary_macro_regime_label"]).unique()


def _slice_diagnostics(predictions: pl.DataFrame, matrix: pl.DataFrame) -> pl.DataFrame:
    if predictions.is_empty():
        return pl.DataFrame()
    columns = ["date_local", "cp"]
    if "binary_macro_regime_label" in matrix.columns:
        columns.append("binary_macro_regime_label")
    enriched = predictions.join(
        matrix.select(columns),
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
                    "iteration_id": POOLED_ITERATION_ID,
                    "iteration_label": POOLED_ITERATION_LABEL,
                    "slice_column": column,
                    "slice_value": str(row[column]),
                    "rows": row["rows"],
                    "mae": row["mae"],
                    "production_status": PRODUCTION_STATUS,
                }
            )
    return pl.DataFrame(rows, strict=False)


def _feature_audit(
    *,
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    interaction_columns: list[str],
) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for feature in TEMPORAL_FEATURE_COLUMNS:
        rows.append(
            {
                "feature": feature,
                "feature_role": "pooled_temporal_cyclic",
                "source_feature": "cp_or_date_local",
                "production_status": PRODUCTION_STATUS,
            }
        )
    for feature in interaction_columns:
        source_feature, macro_value = feature.split("_x_", maxsplit=1)
        rows.append(
            {
                "feature": feature,
                "feature_role": "continuous_x_binary_macro",
                "source_feature": source_feature,
                "macro_value": macro_value,
                "production_status": PRODUCTION_STATUS,
            }
        )
    for feature in categorical_feature_columns:
        rows.append(
            {
                "feature": feature,
                "feature_role": "pooled_categorical_input",
                "source_feature": feature,
                "production_status": PRODUCTION_STATUS,
            }
        )
    for feature in numeric_feature_columns:
        rows.append(
            {
                "feature": feature,
                "feature_role": "pooled_numeric_input",
                "source_feature": feature,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False).unique("feature", keep="first")


def _with_production_status(frame: pl.DataFrame) -> pl.DataFrame:
    if frame.is_empty():
        return frame
    return frame.with_columns(pl.lit(PRODUCTION_STATUS).alias("production_status"))


def _empty_model_results() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "test_year": pl.Int64,
            "model_name": pl.Utf8,
            "cp": pl.Utf8,
            "n_train": pl.Int64,
            "n_test": pl.Int64,
            "mae": pl.Float64,
            "beats_train_mean_null": pl.Boolean,
            "production_status": pl.Utf8,
        }
    )


def _empty_predictions() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "date_local": pl.Date,
            "cp": pl.Utf8,
            "actual": pl.Float64,
            "prediction": pl.Float64,
            "absolute_error": pl.Float64,
            "model_name": pl.Utf8,
            "production_status": pl.Utf8,
            "test_year": pl.Int64,
        }
    )


def _empty_uncertainty() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "test_year": pl.Int64,
            "model_name": pl.Utf8,
            "cp": pl.Utf8,
            "residual_abs_p50": pl.Float64,
            "residual_abs_p90": pl.Float64,
            "abstention_rule": pl.Utf8,
            "production_status": pl.Utf8,
        }
    )


def _run_pooled_fold(
    split: pl.DataFrame,
    *,
    test_year: int,
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    target_column: str,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    train = split.filter(pl.col("fold") == "train")
    test = split.filter(pl.col("fold") == "test")
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
    predictions = _prediction_rows(
        test,
        predictions=challenger_prediction,
        target_column=target_column,
    ).with_columns(pl.lit(test_year).alias("test_year"))
    results = pl.DataFrame(
        [
            {
                "test_year": test_year,
                "model_name": "train_mean_null",
                "cp": "ALL",
                "n_train": train.height,
                "n_test": test.height,
                "mae": null_mae,
                "beats_train_mean_null": False,
                "production_status": PRODUCTION_STATUS,
            },
            {
                "test_year": test_year,
                "model_name": "ridge_challenger",
                "cp": "ALL",
                "n_train": train.height,
                "n_test": test.height,
                "mae": challenger_mae,
                "beats_train_mean_null": challenger_mae < null_mae,
                "production_status": PRODUCTION_STATUS,
            },
        ],
        strict=False,
    )
    uncertainty = pl.DataFrame(
        [
            {
                "test_year": test_year,
                "model_name": "ridge_challenger",
                "cp": "ALL",
                "residual_abs_p50": float(np.quantile(predictions["absolute_error"], 0.5)),
                "residual_abs_p90": float(np.quantile(predictions["absolute_error"], 0.9)),
                "abstention_rule": (
                    "abstain when pooled CP/regime slice support is weak"
                ),
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )
    return results, predictions, uncertainty


def build_onda3_pooled_iteration(
    matrix: pl.DataFrame,
    *,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    target_column: str = "tmax_int",
) -> dict[str, pl.DataFrame]:
    matrix = add_pooled_temporal_features(matrix)
    if "binary_macro_regime_label" in matrix.columns:
        matrix, interaction_columns = add_binary_macro_interaction_features(matrix)
    else:
        interaction_columns = []
    effective_numeric = [
        column
        for column in [
            *numeric_feature_columns,
            *TEMPORAL_FEATURE_COLUMNS,
            *interaction_columns,
        ]
        if column in matrix.columns and matrix.schema[column].is_numeric()
    ]
    effective_categorical = [
        column for column in categorical_feature_columns if column in matrix.columns
    ]
    dated = matrix.with_columns(pl.col("date_local").dt.year().alias("_year"))
    result_frames: list[pl.DataFrame] = []
    prediction_frames: list[pl.DataFrame] = []
    uncertainty_frames: list[pl.DataFrame] = []

    for test_year in test_years:
        split = dated.with_columns(
            pl.when(pl.col("_year") < test_year)
            .then(pl.lit("train"))
            .when(pl.col("_year") == test_year)
            .then(pl.lit("test"))
            .otherwise(pl.lit("holdout"))
            .alias("fold")
        ).filter(pl.col("fold") != "holdout")
        if split.filter(pl.col("fold") == "train").is_empty() or split.filter(
            pl.col("fold") == "test"
        ).is_empty():
            continue
        results, predictions, uncertainty = _run_pooled_fold(
            split.drop("_year"),
            test_year=test_year,
            numeric_feature_columns=effective_numeric,
            categorical_feature_columns=effective_categorical,
            target_column=target_column,
        )
        result_frames.append(results)
        prediction_frames.append(predictions)
        uncertainty_frames.append(uncertainty)

    results = (
        pl.concat(result_frames, how="diagonal_relaxed")
        if result_frames
        else _empty_model_results()
    )
    predictions = (
        pl.concat(prediction_frames, how="diagonal_relaxed")
        if prediction_frames
        else _empty_predictions()
    )
    uncertainty = (
        pl.concat(uncertainty_frames, how="diagonal_relaxed")
        if uncertainty_frames
        else _empty_uncertainty()
    )
    enriched_predictions = enrich_predictions_with_brackets(
        predictions,
        iteration_id=POOLED_ITERATION_ID,
        iteration_label=POOLED_ITERATION_LABEL,
        assignments=_prediction_assignments(matrix),
    )
    bracket_overall = _with_production_status(
        build_overall_bracket_summary(enriched_predictions)
    )
    challenger = results.filter(pl.col("model_name") == "ridge_challenger")
    all_beat = not challenger.is_empty() and bool(
        challenger.select(pl.col("beats_train_mean_null").all()).item()
    )
    decision_rationale = (
        "Onda 3F pooled temporal/regime model iteration completed."
        if not challenger.is_empty()
        else "No valid pooled folds were available for the requested test years."
    )
    temporal = pl.DataFrame(
        [
            {
                "diagnostic": "all_pooled_challengers_beat_null",
                "status": "PASS" if all_beat else "BLOCK",
                "test_years": ",".join(str(year) for year in test_years),
                "n_challenger_rows": challenger.height,
                "n_valid_folds": challenger.height,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )
    decision = pl.DataFrame(
        [
            {
                "decision_status": (
                    DECISION_READY_FOR_AUDIT if all_beat else DECISION_KEEP_REVIEW
                ),
                "decision_rationale": decision_rationale,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )
    return {
        "onda3_pooled_feature_audit_v1": _feature_audit(
            numeric_feature_columns=effective_numeric,
            categorical_feature_columns=effective_categorical,
            interaction_columns=interaction_columns,
        ),
        "onda3_pooled_model_results_v1": results,
        "onda3_pooled_predictions_v1": enriched_predictions,
        "onda3_pooled_bracket_overall_v1": bracket_overall,
        "onda3_pooled_bracket_by_month_day_v1": _with_production_status(
            build_month_day_bracket_summary(enriched_predictions)
        ),
        "onda3_pooled_bracket_by_month_cp_v1": _with_production_status(
            build_month_cp_bracket_summary(enriched_predictions)
        ),
        "onda3_pooled_regime_performance_v1": _with_production_status(
            build_regime_performance_summary(enriched_predictions)
        ),
        "onda3_pooled_regime_by_cp_v1": _with_production_status(
            build_regime_cp_performance_summary(enriched_predictions)
        ),
        "onda3_pooled_slice_diagnostics_v1": _slice_diagnostics(predictions, matrix),
        "onda3_pooled_uncertainty_abstention_v1": uncertainty,
        "onda3_pooled_temporal_diagnostics_v1": temporal,
        "onda3_pooled_decision_update_v1": decision,
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


def render_onda3_pooled_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    def frame(name: str) -> pl.DataFrame:
        return artifacts.get(name, pl.DataFrame())

    return "\n\n".join(
        [
            "# Onda 3F Pooled Temporal/Regime Model Report",
            f"Generated: {today.isoformat()}",
            "",
            (
                "Scope: pre-Open-Meteo local-data experiment. "
                "Open-Meteo forecast data is not integrated."
            ),
            "All outputs remain EXPERIMENT_ONLY.",
            "## Decision",
            _markdown_table(frame("onda3_pooled_decision_update_v1")),
            "## Temporal Diagnostics",
            _markdown_table(frame("onda3_pooled_temporal_diagnostics_v1")),
            "## Model Results",
            _markdown_table(frame("onda3_pooled_model_results_v1"), max_rows=30),
            "## Exact Bracket Overall",
            _markdown_table(frame("onda3_pooled_bracket_overall_v1")),
            "## Exact Bracket By Month",
            (
                "any_cp_exact_pct counts a day as correct if any checkpoint hit "
                "the exact integer bracket. cp23_exact_pct is the "
                "last-checkpoint-only rate."
            ),
            _markdown_table(frame("onda3_pooled_bracket_by_month_day_v1"), max_rows=80),
            "## Exact Bracket By Month And CP",
            _markdown_table(frame("onda3_pooled_bracket_by_month_cp_v1"), max_rows=80),
            "## Binary Macro Regime Performance",
            _markdown_table(frame("onda3_pooled_regime_performance_v1")),
            "## Slice Diagnostics",
            _markdown_table(frame("onda3_pooled_slice_diagnostics_v1"), max_rows=40),
            "## Feature Audit",
            _markdown_table(frame("onda3_pooled_feature_audit_v1"), max_rows=40),
            "## Uncertainty and Abstention",
            _markdown_table(frame("onda3_pooled_uncertainty_abstention_v1")),
        ]
    ) + "\n"


def write_onda3_pooled_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact_name, filename in POOLED_FILENAMES.items():
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

    report_path = output_dir / "onda3_pooled_model_report_v1.md"
    report_path.write_text(
        render_onda3_pooled_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["onda3_pooled_report_md"] = report_path
    return paths
