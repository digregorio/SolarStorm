from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import NamedTuple

import polars as pl

CP_SET = ("20:00", "21:00", "22:00", "23:00")
FIXED_TRAIN_END = dt.date(2024, 12, 31)
FIXED_TEST_START = dt.date(2025, 1, 1)


class PredictionSpec(NamedTuple):
    iteration_id: str
    iteration_label: str
    path_parts: tuple[str, ...]


class Onda4ReviewSpec(NamedTuple):
    review_id: str
    review_label: str
    source_iteration_id: str
    path_parts: tuple[str, ...]


PREDICTION_SPECS = (
    PredictionSpec(
        "onda3_b_cp_specific_holdout",
        "Onda 3B CP-specific holdout 2025+",
        ("onda3-next", "onda3_next_predictions_v1.csv"),
    ),
    PredictionSpec(
        "onda3_c_rolling_temporal",
        "Onda 3C rolling temporal no-interaction",
        ("onda3-rolling", "onda3_rolling_predictions_v1.csv"),
    ),
    PredictionSpec(
        "onda3_d_binary_macro_interactions",
        "Onda 3D binary-macro interactions",
        ("onda3-interactions", "onda3_interaction_predictions_v1.csv"),
    ),
)

ONDA4_REVIEW_SPECS = (
    Onda4ReviewSpec(
        "onda4_review_onda3_a",
        "Onda 4M review on Onda 3A",
        "onda3_a_baseline_first",
        ("onda4-model",),
    ),
    Onda4ReviewSpec(
        "onda4_review_onda3_b",
        "Onda 4M review on Onda 3B",
        "onda3_b_cp_specific_holdout",
        ("onda4-model-next",),
    ),
    Onda4ReviewSpec(
        "onda4_review_onda3_c",
        "Onda 4M review on Onda 3C",
        "onda3_c_rolling_temporal",
        ("onda4-model-rolling",),
    ),
    Onda4ReviewSpec(
        "onda4_review_onda3_d",
        "Onda 4M review on Onda 3D",
        "onda3_d_binary_macro_interactions",
        ("onda4-model-interactions",),
    ),
)

REVIEW_FILENAMES = {
    "onda3_model_attempt_scope_v1": "onda3_model_attempt_scope_v1.csv",
    "onda3_model_iteration_summary_v1": "onda3_model_iteration_summary_v1.csv",
    "onda3_model_result_rows_v1": "onda3_model_result_rows_v1.csv",
    "onda3_bracket_overall_v1": "onda3_bracket_overall_v1.csv",
    "onda3_bracket_by_month_day_v1": "onda3_bracket_by_month_day_v1.csv",
    "onda3_bracket_by_month_cp_v1": "onda3_bracket_by_month_cp_v1.csv",
    "onda3_regime_performance_v1": "onda3_regime_performance_v1.csv",
    "onda3_regime_by_cp_v1": "onda3_regime_by_cp_v1.csv",
    "onda3_regime_comparison_v1": "onda3_regime_comparison_v1.csv",
    "onda3_interaction_feature_audit_v1": "onda3_interaction_feature_audit_v1.csv",
    "onda3_onda4_gate_review_v1": "onda3_onda4_gate_review_v1.csv",
}


def _ensure_date(df: pl.DataFrame) -> pl.DataFrame:
    dtype = df.schema.get("date_local")
    if dtype == pl.Utf8:
        return df.with_columns(pl.col("date_local").str.to_date())
    if isinstance(dtype, pl.Datetime):
        return df.with_columns(pl.col("date_local").dt.date())
    return df


def _path(reports_dir: Path, parts: tuple[str, ...]) -> Path:
    path = reports_dir
    for part in parts:
        path /= part
    return path


def _read_csv(path: Path) -> pl.DataFrame:
    return pl.read_csv(path) if path.exists() else pl.DataFrame()


def _percent_from_bool(column: str) -> pl.Expr:
    return (pl.col(column).cast(pl.Float64).mean() * 100.0)


def _format_period(start: dt.date | None, end: dt.date | None) -> str:
    if start is None or end is None:
        return "not_available"
    return f"{start.isoformat()} to {end.isoformat()}"


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


def enrich_predictions_with_brackets(
    predictions: pl.DataFrame,
    *,
    iteration_id: str,
    iteration_label: str,
    assignments: pl.DataFrame | None = None,
) -> pl.DataFrame:
    if predictions.is_empty():
        return predictions

    frame = _ensure_date(predictions)
    if "test_year" not in frame.columns:
        frame = frame.with_columns(pl.lit(None).cast(pl.Int64).alias("test_year"))
    if "absolute_error" not in frame.columns:
        frame = frame.with_columns(
            (pl.col("actual") - pl.col("prediction")).abs().alias("absolute_error")
        )

    frame = frame.with_columns(
        (pl.col("prediction") + 0.5).floor().cast(pl.Int64).alias("pred_bracket"),
        (pl.col("actual") + 0.5).floor().cast(pl.Int64).alias("actual_bracket"),
        pl.col("date_local").dt.strftime("%Y-%m").alias("month"),
        pl.col("date_local").dt.year().alias("calendar_year"),
        pl.lit(iteration_id).alias("iteration_id"),
        pl.lit(iteration_label).alias("iteration_label"),
    ).with_columns(
        (pl.col("pred_bracket") == pl.col("actual_bracket")).alias("exact_bracket")
    )

    if assignments is not None and not assignments.is_empty():
        assignment_frame = _ensure_date(assignments).select(
            ["date_local", "cp", "binary_macro_regime_label"]
        )
        if "binary_macro_regime_label" not in frame.columns:
            frame = frame.join(assignment_frame, on=["date_local", "cp"], how="left")

    return frame.select(
        [
            "iteration_id",
            "iteration_label",
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


def build_month_cp_bracket_summary(enriched_predictions: pl.DataFrame) -> pl.DataFrame:
    if enriched_predictions.is_empty():
        return pl.DataFrame()
    return (
        enriched_predictions.group_by(["iteration_id", "iteration_label", "month", "cp"])
        .agg(
            pl.len().alias("n_cp_rows"),
            pl.col("exact_bracket").cast(pl.Int64).sum().alias("exact_bracket_rows"),
            _percent_from_bool("exact_bracket").alias("exact_bracket_pct"),
            pl.col("absolute_error").mean().alias("mae"),
        )
        .sort(["iteration_id", "month", "cp"])
    )


def build_month_day_bracket_summary(enriched_predictions: pl.DataFrame) -> pl.DataFrame:
    if enriched_predictions.is_empty():
        return pl.DataFrame()
    daily = enriched_predictions.group_by(
        ["iteration_id", "iteration_label", "date_local", "month"]
    ).agg(
        pl.col("exact_bracket").any().alias("any_cp_exact"),
        pl.col("exact_bracket").filter(pl.col("cp") == "23:00").first().alias("cp23_exact"),
    )
    return (
        daily.group_by(["iteration_id", "iteration_label", "month"])
        .agg(
            pl.len().alias("n_days"),
            pl.col("any_cp_exact").cast(pl.Int64).sum().alias("any_cp_exact_days"),
            _percent_from_bool("any_cp_exact").alias("any_cp_exact_pct"),
            pl.col("cp23_exact").is_not_null().sum().alias("n_days_with_cp23"),
            pl.col("cp23_exact").cast(pl.Int64).sum().alias("cp23_exact_days"),
            _percent_from_bool("cp23_exact").alias("cp23_exact_pct"),
        )
        .sort(["iteration_id", "month"])
    )


def _bool_pct(df: pl.DataFrame, column: str) -> float | None:
    if df.is_empty():
        return None
    values = df[column].drop_nulls()
    if values.is_empty():
        return None
    return float(values.cast(pl.Float64).mean() * 100.0)


def build_overall_bracket_summary(enriched_predictions: pl.DataFrame) -> pl.DataFrame:
    if enriched_predictions.is_empty():
        return pl.DataFrame()

    rows: list[dict[str, object]] = []
    iteration_pairs = (
        enriched_predictions.select(["iteration_id", "iteration_label"])
        .unique()
        .sort("iteration_id")
        .iter_rows(named=True)
    )
    for pair in iteration_pairs:
        subset = enriched_predictions.filter(
            pl.col("iteration_id") == pair["iteration_id"]
        )
        daily = subset.group_by(["date_local"]).agg(
            pl.col("exact_bracket").any().alias("any_cp_exact"),
            pl.col("exact_bracket").filter(pl.col("cp") == "23:00").first().alias("cp23_exact"),
        )
        row: dict[str, object] = {
            "iteration_id": pair["iteration_id"],
            "iteration_label": pair["iteration_label"],
            "n_days": daily.height,
            "n_cp_rows": subset.height,
            "mae": float(subset["absolute_error"].mean()),
            "any_cp_exact_pct": _bool_pct(daily, "any_cp_exact"),
            "cp23_exact_pct": _bool_pct(daily, "cp23_exact"),
        }
        for cp in CP_SET:
            cp_subset = subset.filter(pl.col("cp") == cp)
            row[f"cp_{cp.replace(':', '')}_exact_pct"] = _bool_pct(
                cp_subset, "exact_bracket"
            )
        rows.append(row)
    return pl.DataFrame(rows, strict=False)


def build_regime_performance_summary(enriched_predictions: pl.DataFrame) -> pl.DataFrame:
    if (
        enriched_predictions.is_empty()
        or "binary_macro_regime_label" not in enriched_predictions.columns
    ):
        return pl.DataFrame()
    return (
        enriched_predictions.drop_nulls("binary_macro_regime_label")
        .group_by(["iteration_id", "iteration_label", "binary_macro_regime_label"])
        .agg(
            pl.len().alias("n_cp_rows"),
            pl.col("date_local").n_unique().alias("n_unique_dates"),
            pl.col("absolute_error").mean().alias("mae"),
            pl.col("exact_bracket").cast(pl.Int64).sum().alias("exact_bracket_rows"),
            _percent_from_bool("exact_bracket").alias("exact_bracket_pct"),
        )
        .sort(["iteration_id", "binary_macro_regime_label"])
    )


def build_regime_cp_performance_summary(enriched_predictions: pl.DataFrame) -> pl.DataFrame:
    if (
        enriched_predictions.is_empty()
        or "binary_macro_regime_label" not in enriched_predictions.columns
    ):
        return pl.DataFrame()
    return (
        enriched_predictions.drop_nulls("binary_macro_regime_label")
        .group_by(["iteration_id", "iteration_label", "binary_macro_regime_label", "cp"])
        .agg(
            pl.len().alias("n_cp_rows"),
            pl.col("absolute_error").mean().alias("mae"),
            pl.col("exact_bracket").cast(pl.Int64).sum().alias("exact_bracket_rows"),
            _percent_from_bool("exact_bracket").alias("exact_bracket_pct"),
        )
        .sort(["iteration_id", "binary_macro_regime_label", "cp"])
    )


def build_regime_comparison_summary(regime_summary: pl.DataFrame) -> pl.DataFrame:
    if regime_summary.is_empty():
        return pl.DataFrame()

    rows: list[dict[str, object]] = []
    regimes = sorted(regime_summary["binary_macro_regime_label"].unique().to_list())
    for regime in regimes:
        c_rows = regime_summary.filter(
            (pl.col("iteration_id") == "onda3_c_rolling_temporal")
            & (pl.col("binary_macro_regime_label") == regime)
        )
        d_rows = regime_summary.filter(
            (pl.col("iteration_id") == "onda3_d_binary_macro_interactions")
            & (pl.col("binary_macro_regime_label") == regime)
        )
        if c_rows.is_empty() or d_rows.is_empty():
            continue
        c_row = c_rows.row(0, named=True)
        d_row = d_rows.row(0, named=True)
        rows.append(
            {
                "comparison": "onda3_d_minus_onda3_c",
                "binary_macro_regime_label": regime,
                "onda3_c_mae": c_row["mae"],
                "onda3_d_mae": d_row["mae"],
                "mae_delta": d_row["mae"] - c_row["mae"],
                "onda3_c_exact_bracket_pct": c_row["exact_bracket_pct"],
                "onda3_d_exact_bracket_pct": d_row["exact_bracket_pct"],
                "exact_bracket_pct_delta": (
                    d_row["exact_bracket_pct"] - c_row["exact_bracket_pct"]
                ),
                "n_cp_rows": d_row["n_cp_rows"],
                "production_status": "EXPERIMENT_ONLY",
            }
        )
    return pl.DataFrame(rows, strict=False)


def _standardize_results(
    df: pl.DataFrame,
    *,
    iteration_id: str,
    iteration_label: str,
) -> pl.DataFrame:
    if df.is_empty():
        return df
    frame = df
    if "test_year" not in frame.columns:
        frame = frame.with_columns(pl.lit(None).cast(pl.Int64).alias("test_year"))
    return frame.with_columns(
        pl.lit(iteration_id).alias("iteration_id"),
        pl.lit(iteration_label).alias("iteration_label"),
    ).select(
        [
            "iteration_id",
            "iteration_label",
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


def _load_model_result_rows(reports_dir: Path) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    baseline = _read_csv(reports_dir / "onda3" / "onda3_baseline_results_v1.csv")
    challenger = _read_csv(reports_dir / "onda3" / "onda3_challenger_results_v1.csv")
    if not baseline.is_empty() and not challenger.is_empty():
        frames.append(
            _standardize_results(
                pl.concat([baseline, challenger], how="diagonal_relaxed"),
                iteration_id="onda3_a_baseline_first",
                iteration_label="Onda 3A baseline-first aggregate ridge",
            )
        )

    for iteration_id, iteration_label, path in [
        (
            "onda3_b_cp_specific_holdout",
            "Onda 3B CP-specific holdout 2025+",
            reports_dir / "onda3-next" / "onda3_next_model_results_v1.csv",
        ),
        (
            "onda3_c_rolling_temporal",
            "Onda 3C rolling temporal no-interaction",
            reports_dir / "onda3-rolling" / "onda3_rolling_model_results_v1.csv",
        ),
        (
            "onda3_d_binary_macro_interactions",
            "Onda 3D binary-macro interactions",
            reports_dir / "onda3-interactions" / "onda3_interaction_model_results_v1.csv",
        ),
    ]:
        df = _read_csv(path)
        if not df.is_empty():
            frames.append(
                _standardize_results(
                    df,
                    iteration_id=iteration_id,
                    iteration_label=iteration_label,
                )
            )
    return pl.concat(frames, how="diagonal_relaxed") if frames else pl.DataFrame()


def _weighted_mae(df: pl.DataFrame) -> float | None:
    if df.is_empty():
        return None
    weight_sum = float(df["n_test"].sum())
    if weight_sum == 0.0:
        return None
    return float((df["mae"] * df["n_test"]).sum() / weight_sum)


def build_model_iteration_summary(
    result_rows: pl.DataFrame,
    *,
    prediction_iteration_ids: set[str],
) -> pl.DataFrame:
    if result_rows.is_empty():
        return pl.DataFrame()
    rows: list[dict[str, object]] = []
    for pair in (
        result_rows.select(["iteration_id", "iteration_label"])
        .unique()
        .sort("iteration_id")
        .iter_rows(named=True)
    ):
        subset = result_rows.filter(pl.col("iteration_id") == pair["iteration_id"])
        null_rows = subset.filter(pl.col("model_name") == "train_mean_null")
        challenger_rows = subset.filter(pl.col("model_name") == "ridge_challenger")
        null_mae = _weighted_mae(null_rows)
        challenger_mae = _weighted_mae(challenger_rows)
        all_beat = (
            not challenger_rows.is_empty()
            and bool(challenger_rows.select(pl.col("beats_train_mean_null").all()).item())
        )
        rows.append(
            {
                "iteration_id": pair["iteration_id"],
                "iteration_label": pair["iteration_label"],
                "n_result_rows": subset.height,
                "n_challenger_rows": challenger_rows.height,
                "weighted_null_mae": null_mae,
                "weighted_challenger_mae": challenger_mae,
                "weighted_mae_lift": (
                    None
                    if null_mae is None or challenger_mae is None
                    else null_mae - challenger_mae
                ),
                "all_challenger_rows_beat_null": all_beat,
                "has_line_level_predictions": pair["iteration_id"]
                in prediction_iteration_ids,
                "production_status": "EXPERIMENT_ONLY",
            }
        )
    return pl.DataFrame(rows, strict=False)


def _load_enriched_predictions(
    reports_dir: Path,
    *,
    assignments: pl.DataFrame | None,
) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    for spec in PREDICTION_SPECS:
        df = _read_csv(_path(reports_dir, spec.path_parts))
        if df.is_empty():
            continue
        frames.append(
            enrich_predictions_with_brackets(
                df,
                iteration_id=spec.iteration_id,
                iteration_label=spec.iteration_label,
                assignments=assignments,
            )
        )
    return pl.concat(frames, how="diagonal_relaxed") if frames else pl.DataFrame()


def _joined_feature_dates(features_path: Path, labels_path: Path) -> pl.DataFrame:
    if not features_path.exists() or not labels_path.exists():
        return pl.DataFrame()
    features = _ensure_date(pl.read_parquet(features_path)).select(["date_local"])
    labels = _ensure_date(pl.read_parquet(labels_path)).select(["date_local"])
    return features.join(labels, on="date_local", how="inner")


def _reported_counts(
    result_rows: pl.DataFrame,
    *,
    iteration_id: str,
    test_year: int | None = None,
) -> tuple[int | None, int | None]:
    rows = result_rows.filter(
        (pl.col("iteration_id") == iteration_id)
        & (pl.col("model_name") == "ridge_challenger")
    )
    if test_year is not None:
        rows = rows.filter(pl.col("test_year") == test_year)
    if rows.is_empty():
        return None, None
    first = rows.sort(["test_year", "cp"]).row(0, named=True)
    return first["n_train"], first["n_test"]


def build_scope_summary(
    *,
    result_rows: pl.DataFrame,
    enriched_predictions: pl.DataFrame,
    features_path: Path,
    labels_path: Path,
) -> pl.DataFrame:
    joined = _joined_feature_dates(features_path, labels_path)
    rows: list[dict[str, object]] = []

    if not joined.is_empty():
        fixed_train = joined.filter(pl.col("date_local") <= FIXED_TRAIN_END)
        fixed_test = joined.filter(pl.col("date_local") >= FIXED_TEST_START)
        fixed_train_period = _format_period(
            fixed_train["date_local"].min(),
            fixed_train["date_local"].max(),
        )
        fixed_test_period = _format_period(
            fixed_test["date_local"].min(),
            fixed_test["date_local"].max(),
        )
    else:
        fixed_train_period = f"not_available to {FIXED_TRAIN_END.isoformat()}"
        fixed_test_period = f"{FIXED_TEST_START.isoformat()} to not_available"

    for iteration_id, iteration_label, split_type, row_unit in [
        (
            "onda3_a_baseline_first",
            "Onda 3A baseline-first aggregate ridge",
            "fixed_holdout",
            "all_cp_rows",
        ),
        (
            "onda3_b_cp_specific_holdout",
            "Onda 3B CP-specific holdout 2025+",
            "fixed_holdout",
            "per_cp_model_rows",
        ),
    ]:
        n_train, n_test = _reported_counts(result_rows, iteration_id=iteration_id)
        if iteration_id == "onda3_a_baseline_first":
            a_rows = result_rows.filter(
                (pl.col("iteration_id") == iteration_id)
                & (pl.col("model_name") == "ridge_challenger")
            )
            if not a_rows.is_empty():
                row = a_rows.row(0, named=True)
                n_train, n_test = row["n_train"], row["n_test"]
        rows.append(
            {
                "iteration_id": iteration_id,
                "iteration_label": iteration_label,
                "split_type": split_type,
                "train_period": fixed_train_period,
                "validation_period": "none; no separate validation split persisted",
                "test_period": fixed_test_period,
                "row_unit": row_unit,
                "n_train_reported": n_train,
                "n_test_reported": n_test,
                "production_status": "EXPERIMENT_ONLY",
            }
        )

    rolling_ids = [
        (
            "onda3_c_rolling_temporal",
            "Onda 3C rolling temporal no-interaction",
        ),
        (
            "onda3_d_binary_macro_interactions",
            "Onda 3D binary-macro interactions",
        ),
    ]
    years = (
        result_rows.drop_nulls("test_year")["test_year"].unique().sort().to_list()
        if not result_rows.is_empty() and "test_year" in result_rows.columns
        else []
    )
    for iteration_id, iteration_label in rolling_ids:
        for year in years:
            year = int(year)
            train = (
                joined.filter(pl.col("date_local").dt.year() < year)
                if not joined.is_empty()
                else pl.DataFrame()
            )
            test_predictions = enriched_predictions.filter(
                (pl.col("iteration_id") == iteration_id) & (pl.col("test_year") == year)
            )
            n_train, n_test = _reported_counts(
                result_rows,
                iteration_id=iteration_id,
                test_year=year,
            )
            rows.append(
                {
                    "iteration_id": iteration_id,
                    "iteration_label": iteration_label,
                    "split_type": f"rolling_year_{year}",
                    "train_period": _format_period(
                        train["date_local"].min() if not train.is_empty() else None,
                        train["date_local"].max() if not train.is_empty() else None,
                    ),
                    "validation_period": "none; no separate validation split persisted",
                    "test_period": _format_period(
                        test_predictions["date_local"].min()
                        if not test_predictions.is_empty()
                        else None,
                        test_predictions["date_local"].max()
                        if not test_predictions.is_empty()
                        else None,
                    ),
                    "row_unit": "per_cp_model_rows",
                    "n_train_reported": n_train,
                    "n_test_reported": n_test,
                    "production_status": "EXPERIMENT_ONLY",
                }
            )
    return pl.DataFrame(rows, strict=False)


def _load_onda4_gate_review(reports_dir: Path) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for spec in ONDA4_REVIEW_SPECS:
        review_dir = _path(reports_dir, spec.path_parts)
        gates = _read_csv(review_dir / "onda4_model_gate_results_v1.csv")
        decision = _read_csv(review_dir / "onda4_model_decision_update_v1.csv")
        if gates.is_empty():
            continue
        blocked = gates.filter(pl.col("gate_status") != "PASS")
        m3 = gates.filter(pl.col("gate_id") == "M3")
        m4 = gates.filter(pl.col("gate_id") == "M4")
        decision_status = (
            decision.row(0, named=True)["decision_status"]
            if not decision.is_empty()
            else "not_available"
        )
        rows.append(
            {
                "review_id": spec.review_id,
                "review_label": spec.review_label,
                "source_iteration_id": spec.source_iteration_id,
                "n_gates": gates.height,
                "n_pass": gates.filter(pl.col("gate_status") == "PASS").height,
                "blocked_gates": ",".join(blocked["gate_id"].to_list()),
                "m3_detail": m3.row(0, named=True)["detail"]
                if not m3.is_empty()
                else "",
                "m4_detail": m4.row(0, named=True)["detail"]
                if not m4.is_empty()
                else "",
                "decision_status": decision_status,
                "production_status": "EXPERIMENT_ONLY",
            }
        )
    return pl.DataFrame(rows, strict=False)


def build_onda3_model_attempt_review(
    *,
    reports_dir: Path,
    features_path: Path,
    labels_path: Path,
) -> dict[str, pl.DataFrame]:
    result_rows = _load_model_result_rows(reports_dir)
    assignments_path = (
        reports_dir / "regime-design" / "regime_binary_macro_assignments_v1.csv"
    )
    assignments = _read_csv(assignments_path)
    enriched_predictions = _load_enriched_predictions(
        reports_dir,
        assignments=assignments,
    )
    prediction_iteration_ids = (
        set(enriched_predictions["iteration_id"].unique().to_list())
        if not enriched_predictions.is_empty()
        else set()
    )

    regime = build_regime_performance_summary(enriched_predictions)
    interaction_audit = _read_csv(
        reports_dir
        / "onda3-interactions"
        / "onda3_interaction_feature_audit_v1.csv"
    )
    return {
        "onda3_model_attempt_scope_v1": build_scope_summary(
            result_rows=result_rows,
            enriched_predictions=enriched_predictions,
            features_path=features_path,
            labels_path=labels_path,
        ),
        "onda3_model_iteration_summary_v1": build_model_iteration_summary(
            result_rows,
            prediction_iteration_ids=prediction_iteration_ids,
        ),
        "onda3_model_result_rows_v1": result_rows,
        "onda3_bracket_overall_v1": build_overall_bracket_summary(enriched_predictions),
        "onda3_bracket_by_month_day_v1": build_month_day_bracket_summary(
            enriched_predictions
        ),
        "onda3_bracket_by_month_cp_v1": build_month_cp_bracket_summary(
            enriched_predictions
        ),
        "onda3_regime_performance_v1": regime,
        "onda3_regime_by_cp_v1": build_regime_cp_performance_summary(
            enriched_predictions
        ),
        "onda3_regime_comparison_v1": build_regime_comparison_summary(regime),
        "onda3_interaction_feature_audit_v1": interaction_audit,
        "onda3_onda4_gate_review_v1": _load_onda4_gate_review(reports_dir),
    }


def _report_intro(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    summary = artifacts.get("onda3_model_iteration_summary_v1", pl.DataFrame())
    bracket = artifacts.get("onda3_bracket_overall_v1", pl.DataFrame())
    d_row = (
        summary.filter(pl.col("iteration_id") == "onda3_d_binary_macro_interactions")
        if not summary.is_empty()
        else pl.DataFrame()
    )
    d_bracket = (
        bracket.filter(pl.col("iteration_id") == "onda3_d_binary_macro_interactions")
        if not bracket.is_empty()
        else pl.DataFrame()
    )
    lines = [
        "# Onda 3 Model Attempt Review",
        f"Generated: {today.isoformat()}",
        "",
        "Scope: pre-Open-Meteo review. Open-Meteo forecast data is not integrated in these artifacts.",
        "All outputs remain EXPERIMENT_ONLY.",
    ]
    if not d_row.is_empty():
        row = d_row.row(0, named=True)
        lines.append(
            "Current best MAE surface: Onda 3D binary-macro interactions "
            f"with weighted challenger MAE {_format_value(row['weighted_challenger_mae'])}."
        )
    if not d_bracket.is_empty():
        row = d_bracket.row(0, named=True)
        lines.append(
            "Current daily exact-bracket surface: "
            f"any CP exact {_format_value(row['any_cp_exact_pct'])}% and "
            f"23:00 exact {_format_value(row['cp23_exact_pct'])}%."
        )
    lines.append(
        "Validation status: no distinct validation split is persisted; current artifacts use fixed holdout or rolling-year test folds."
    )
    return "\n".join(lines)


def render_onda3_model_attempt_review_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    def frame(name: str) -> pl.DataFrame:
        return artifacts.get(name, pl.DataFrame())

    return "\n\n".join(
        [
            _report_intro(artifacts, today=today),
            "## Train Validation Test Scope",
            _markdown_table(frame("onda3_model_attempt_scope_v1"), max_rows=12),
            "## Model Iteration Summary",
            _markdown_table(frame("onda3_model_iteration_summary_v1"), max_rows=20),
            "## Individual Challenger Result Rows",
            _markdown_table(
                frame("onda3_model_result_rows_v1").filter(
                    pl.col("model_name") == "ridge_challenger"
                ),
                max_rows=40,
            ),
            "## Exact Bracket Overall",
            _markdown_table(frame("onda3_bracket_overall_v1"), max_rows=20),
            "## Exact Bracket By Month Day",
            "any_cp_exact_pct counts a day as correct if any checkpoint hit the exact integer bracket. cp23_exact_pct is the last-checkpoint-only rate.",
            _markdown_table(frame("onda3_bracket_by_month_day_v1"), max_rows=120),
            "## Exact Bracket By Month And CP",
            _markdown_table(frame("onda3_bracket_by_month_cp_v1"), max_rows=80),
            "## Regime Performance",
            _markdown_table(frame("onda3_regime_performance_v1"), max_rows=20),
            "## Regime CP Performance",
            _markdown_table(frame("onda3_regime_by_cp_v1"), max_rows=40),
            "## Onda 3D vs Onda 3C Regime Delta",
            _markdown_table(frame("onda3_regime_comparison_v1"), max_rows=20),
            "## Binary Macro Interaction Structure",
            "Onda 3D keeps the binary macro regime as the structural switch and adds continuous-x-macro interactions for foehn_score and cloud_cover_suppression.",
            _markdown_table(frame("onda3_interaction_feature_audit_v1"), max_rows=20),
            "## Onda 4M Gate Review",
            _markdown_table(frame("onda3_onda4_gate_review_v1"), max_rows=20),
            "## Interpretation",
            "\n".join(
                [
                    "- The current baseline exists: Onda 3A train_mean_null vs ridge_challenger on the fixed 2025+ holdout.",
                    "- Onda 3A did not persist line-level predictions, so exact bracket rates cannot be reconstructed from its artifacts alone.",
                    "- Onda 3D improved MAE versus Onda 3C in both binary macro regimes; exact bracket improvement is smaller than MAE improvement.",
                    "- Southerly-flow rows often show slightly higher exact bracket rates, but the evidence is not strong enough to claim a dedicated regime-specialist model.",
                    "- The current path supports two macro regimes as a structural switch plus continuous foehn/cloud features inside the model, not as a complete meteorological taxonomy.",
                ]
            ),
        ]
    ) + "\n"


def write_onda3_model_attempt_review_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact_name, filename in REVIEW_FILENAMES.items():
        if artifact_name not in artifacts:
            continue
        path = output_dir / filename
        artifacts[artifact_name].write_csv(path)
        short = artifact_name.removesuffix("_v1")
        paths[f"{short}_csv"] = path
        paths[f"{artifact_name}_csv"] = path

    report_path = output_dir / "onda3_model_attempt_review_v1.md"
    report = render_onda3_model_attempt_review_report(artifacts, today=today)
    report_path.write_text(report, encoding="utf-8")
    paths["onda3_model_attempt_review_md"] = report_path
    return paths
