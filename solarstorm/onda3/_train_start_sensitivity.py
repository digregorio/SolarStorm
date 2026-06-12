from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from solarstorm.onda3._interactions import build_onda3_interaction_iteration
from solarstorm.onda3._model_attempt_review import (
    build_month_cp_bracket_summary,
    build_month_day_bracket_summary,
    build_overall_bracket_summary,
    build_regime_cp_performance_summary,
    build_regime_performance_summary,
    enrich_predictions_with_brackets,
)

PRODUCTION_STATUS = "EXPERIMENT_ONLY"
LEGACY_VARIANT_ID = "legacy_2009_start"
CONTINUOUS_VARIANT_ID = "continuous_2012_start"
DECISION_CARRY_2012 = "CARRY_2012_START_TO_ONDA3F"
DECISION_KEEP_2009 = "KEEP_2009_START_FOR_ONDA3F"
DECISION_KEEP_BOTH = "KEEP_BOTH_STARTS_UNTIL_NESTED_VALIDATION"
MAE_DECISION_EPSILON = 0.01
BRACKET_GUARD_PERCENT_POINTS = 0.25
TRAIN_START_FILENAMES = {
    "onda3_train_start_scope_v1": "onda3_train_start_scope_v1.csv",
    "onda3_train_start_model_results_v1": "onda3_train_start_model_results_v1.csv",
    "onda3_train_start_predictions_v1": "onda3_train_start_predictions_v1.csv",
    "onda3_train_start_bracket_overall_v1": "onda3_train_start_bracket_overall_v1.csv",
    "onda3_train_start_bracket_by_month_day_v1": (
        "onda3_train_start_bracket_by_month_day_v1.csv"
    ),
    "onda3_train_start_bracket_by_month_cp_v1": (
        "onda3_train_start_bracket_by_month_cp_v1.csv"
    ),
    "onda3_train_start_regime_performance_v1": (
        "onda3_train_start_regime_performance_v1.csv"
    ),
    "onda3_train_start_regime_by_cp_v1": "onda3_train_start_regime_by_cp_v1.csv",
    "onda3_train_start_comparison_v1": "onda3_train_start_comparison_v1.csv",
    "onda3_train_start_decision_update_v1": (
        "onda3_train_start_decision_update_v1.csv"
    ),
}


@dataclass(frozen=True)
class TrainStartVariant:
    variant_id: str
    train_start: dt.date


DEFAULT_TRAIN_START_VARIANTS = (
    TrainStartVariant(LEGACY_VARIANT_ID, dt.date(2009, 4, 23)),
    TrainStartVariant(CONTINUOUS_VARIANT_ID, dt.date(2012, 1, 1)),
)


def _ensure_date(frame: pl.DataFrame) -> pl.DataFrame:
    dtype = frame.schema.get("date_local")
    if dtype == pl.Utf8:
        return frame.with_columns(pl.col("date_local").str.to_date())
    if isinstance(dtype, pl.Datetime):
        return frame.with_columns(pl.col("date_local").dt.date())
    return frame


def filter_matrix_for_train_start(
    matrix: pl.DataFrame,
    variant: TrainStartVariant,
) -> pl.DataFrame:
    matrix = _ensure_date(matrix)
    return matrix.filter(pl.col("date_local") >= variant.train_start)


def _period_text(frame: pl.DataFrame) -> str:
    if frame.is_empty():
        return "not_available"
    return (
        f"{frame['date_local'].min().isoformat()} "
        f"to {frame['date_local'].max().isoformat()}"
    )


def _logical_train_period(variant: TrainStartVariant, test_year: int) -> str:
    end = dt.date(test_year - 1, 12, 31)
    return f"{variant.train_start.isoformat()} to {end.isoformat()}"


def build_train_start_scope(
    matrix: pl.DataFrame,
    *,
    variants: list[TrainStartVariant],
    test_years: list[int],
) -> pl.DataFrame:
    matrix = _ensure_date(matrix)
    dated = matrix.with_columns(pl.col("date_local").dt.year().alias("_year"))
    rows: list[dict[str, object]] = []
    for variant in variants:
        filtered = filter_matrix_for_train_start(dated, variant)
        for test_year in test_years:
            train = filtered.filter(pl.col("_year") < test_year)
            test = filtered.filter(pl.col("_year") == test_year)
            rows.append(
                {
                    "variant_id": variant.variant_id,
                    "train_start": variant.train_start.isoformat(),
                    "test_year": test_year,
                    "train_period": (
                        _logical_train_period(variant, test_year)
                        if not train.is_empty()
                        else "not_available"
                    ),
                    "test_period": _period_text(test),
                    "n_train_rows": train.height,
                    "n_test_rows": test.height,
                    "n_train_days": train.select("date_local").n_unique(),
                    "n_test_days": test.select("date_local").n_unique(),
                    "production_status": PRODUCTION_STATUS,
                }
            )
    return pl.DataFrame(rows, strict=False)


def _variant_label(variant: TrainStartVariant) -> str:
    if variant.variant_id == LEGACY_VARIANT_ID:
        return "Onda 3E legacy 2009-start binary-macro interactions"
    if variant.variant_id == CONTINUOUS_VARIANT_ID:
        return "Onda 3E continuous 2012-start binary-macro interactions"
    return f"Onda 3E {variant.variant_id} binary-macro interactions"


def _tag_variant(frame: pl.DataFrame, variant: TrainStartVariant) -> pl.DataFrame:
    if frame.is_empty():
        return frame
    return frame.with_columns(
        pl.lit(variant.variant_id).alias("variant_id"),
        pl.lit(variant.train_start.isoformat()).alias("train_start"),
    )


def _prediction_assignments(matrix: pl.DataFrame) -> pl.DataFrame | None:
    if "binary_macro_regime_label" not in matrix.columns:
        return None
    return matrix.select(
        ["date_local", "cp", "binary_macro_regime_label"]
    ).unique()


def _weighted_mae(result_rows: pl.DataFrame, variant_id: str) -> float | None:
    if result_rows.is_empty():
        return None
    rows = result_rows.filter(
        (pl.col("variant_id") == variant_id)
        & (pl.col("model_name") == "ridge_challenger")
    )
    if rows.is_empty():
        return None
    weight_sum = float(rows["n_test"].sum())
    if weight_sum == 0.0:
        return None
    return float((rows["mae"] * rows["n_test"]).sum() / weight_sum)


def _overall_metric(
    bracket_overall: pl.DataFrame,
    *,
    variant_id: str,
    column: str,
) -> float | None:
    if bracket_overall.is_empty() or column not in bracket_overall.columns:
        return None
    rows = bracket_overall.filter(pl.col("variant_id") == variant_id)
    if rows.is_empty():
        return None
    value = rows.row(0, named=True)[column]
    return None if value is None else float(value)


def _summary_with_variant_columns(
    summary: pl.DataFrame,
    variants: list[TrainStartVariant],
) -> pl.DataFrame:
    if summary.is_empty() or "iteration_id" not in summary.columns:
        return summary
    lookup = pl.DataFrame(
        [
            {
                "iteration_id": variant.variant_id,
                "variant_id": variant.variant_id,
                "train_start": variant.train_start.isoformat(),
            }
            for variant in variants
        ],
        strict=False,
    )
    return summary.join(lookup, on="iteration_id", how="left").with_columns(
        pl.lit(PRODUCTION_STATUS).alias("production_status")
    )


def _comparison(
    *,
    result_rows: pl.DataFrame,
    bracket_overall: pl.DataFrame,
    variants: list[TrainStartVariant],
) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for variant in variants:
        rows.append(
            {
                "variant_id": variant.variant_id,
                "train_start": variant.train_start.isoformat(),
                "weighted_challenger_mae": _weighted_mae(
                    result_rows,
                    variant.variant_id,
                ),
                "any_cp_exact_pct": _overall_metric(
                    bracket_overall,
                    variant_id=variant.variant_id,
                    column="any_cp_exact_pct",
                ),
                "cp23_exact_pct": _overall_metric(
                    bracket_overall,
                    variant_id=variant.variant_id,
                    column="cp23_exact_pct",
                ),
                "production_status": PRODUCTION_STATUS,
            }
        )
    comparison = pl.DataFrame(rows, strict=False)
    legacy = comparison.filter(pl.col("variant_id") == LEGACY_VARIANT_ID)
    continuous = comparison.filter(pl.col("variant_id") == CONTINUOUS_VARIANT_ID)
    if legacy.is_empty() or continuous.is_empty():
        return comparison
    legacy_row = legacy.row(0, named=True)
    continuous_row = continuous.row(0, named=True)
    legacy_mae = legacy_row["weighted_challenger_mae"]
    continuous_mae = continuous_row["weighted_challenger_mae"]
    legacy_exact = legacy_row["any_cp_exact_pct"]
    continuous_exact = continuous_row["any_cp_exact_pct"]
    mae_delta = (
        None
        if legacy_mae is None or continuous_mae is None
        else continuous_mae - legacy_mae
    )
    exact_delta = (
        None
        if legacy_exact is None or continuous_exact is None
        else continuous_exact - legacy_exact
    )
    return comparison.with_columns(
        pl.lit(mae_delta).alias("continuous_minus_legacy_weighted_mae"),
        pl.lit(exact_delta).alias("continuous_minus_legacy_any_cp_exact_pct"),
    )


def _decision(comparison: pl.DataFrame) -> pl.DataFrame:
    if comparison.is_empty():
        status = DECISION_KEEP_BOTH
        rationale = "No comparison rows were available."
        mae_delta = None
        exact_delta = None
    else:
        legacy = comparison.filter(pl.col("variant_id") == LEGACY_VARIANT_ID)
        continuous = comparison.filter(pl.col("variant_id") == CONTINUOUS_VARIANT_ID)
        if legacy.is_empty() or continuous.is_empty():
            status = DECISION_KEEP_BOTH
            rationale = "Both canonical train-start variants were not available."
            mae_delta = None
            exact_delta = None
        else:
            row = comparison.row(0, named=True)
            mae_delta = row.get("continuous_minus_legacy_weighted_mae")
            exact_delta = row.get("continuous_minus_legacy_any_cp_exact_pct")
            if (
                mae_delta is not None
                and exact_delta is not None
                and mae_delta <= -MAE_DECISION_EPSILON
                and exact_delta >= -BRACKET_GUARD_PERCENT_POINTS
            ):
                status = DECISION_CARRY_2012
                rationale = (
                    "The 2012-start variant improves weighted MAE while staying "
                    "inside the exact-bracket guardrail."
                )
            elif (
                mae_delta is not None
                and exact_delta is not None
                and mae_delta >= MAE_DECISION_EPSILON
                and exact_delta <= BRACKET_GUARD_PERCENT_POINTS
            ):
                status = DECISION_KEEP_2009
                rationale = (
                    "The 2009-start variant improves weighted MAE while staying "
                    "inside the exact-bracket guardrail."
                )
            else:
                status = DECISION_KEEP_BOTH
                rationale = (
                    "The train-start variants are too close or trade MAE against "
                    "exact-bracket performance."
                )
    return pl.DataFrame(
        [
            {
                "decision_status": status,
                "decision_rationale": rationale,
                "continuous_minus_legacy_weighted_mae": mae_delta,
                "continuous_minus_legacy_any_cp_exact_pct": exact_delta,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def build_onda3_train_start_sensitivity(
    matrix: pl.DataFrame,
    *,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    variants: list[TrainStartVariant] | None = None,
    target_column: str = "tmax_int",
) -> dict[str, pl.DataFrame]:
    variants = variants or list(DEFAULT_TRAIN_START_VARIANTS)
    matrix = _ensure_date(matrix)
    scope = build_train_start_scope(matrix, variants=variants, test_years=test_years)

    result_frames: list[pl.DataFrame] = []
    enriched_frames: list[pl.DataFrame] = []
    for variant in variants:
        filtered = filter_matrix_for_train_start(matrix, variant)
        artifacts = build_onda3_interaction_iteration(
            filtered,
            test_years=test_years,
            numeric_feature_columns=numeric_feature_columns,
            categorical_feature_columns=categorical_feature_columns,
            target_column=target_column,
        )
        results = _tag_variant(
            artifacts["onda3_interaction_model_results_v1"],
            variant,
        )
        result_frames.append(results)
        enriched = enrich_predictions_with_brackets(
            artifacts["onda3_interaction_predictions_v1"],
            iteration_id=variant.variant_id,
            iteration_label=_variant_label(variant),
            assignments=_prediction_assignments(filtered),
        )
        enriched_frames.append(_tag_variant(enriched, variant))

    model_results = (
        pl.concat(result_frames, how="diagonal_relaxed")
        if result_frames
        else pl.DataFrame()
    )
    enriched_predictions = (
        pl.concat(enriched_frames, how="diagonal_relaxed")
        if enriched_frames
        else pl.DataFrame()
    )
    bracket_overall = _summary_with_variant_columns(
        build_overall_bracket_summary(enriched_predictions),
        variants,
    )
    comparison = _comparison(
        result_rows=model_results,
        bracket_overall=bracket_overall,
        variants=variants,
    )
    return {
        "onda3_train_start_scope_v1": scope,
        "onda3_train_start_model_results_v1": model_results,
        "onda3_train_start_predictions_v1": enriched_predictions,
        "onda3_train_start_bracket_overall_v1": bracket_overall,
        "onda3_train_start_bracket_by_month_day_v1": _summary_with_variant_columns(
            build_month_day_bracket_summary(enriched_predictions),
            variants,
        ),
        "onda3_train_start_bracket_by_month_cp_v1": _summary_with_variant_columns(
            build_month_cp_bracket_summary(enriched_predictions),
            variants,
        ),
        "onda3_train_start_regime_performance_v1": _summary_with_variant_columns(
            build_regime_performance_summary(enriched_predictions),
            variants,
        ),
        "onda3_train_start_regime_by_cp_v1": _summary_with_variant_columns(
            build_regime_cp_performance_summary(enriched_predictions),
            variants,
        ),
        "onda3_train_start_comparison_v1": comparison,
        "onda3_train_start_decision_update_v1": _decision(comparison),
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


def render_onda3_train_start_sensitivity_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    def frame(name: str) -> pl.DataFrame:
        return artifacts.get(name, pl.DataFrame())

    return "\n\n".join(
        [
            "# Onda 3E Train-Start Sensitivity Report",
            f"Generated: {today.isoformat()}",
            "",
            "Scope: pre-Open-Meteo local-data experiment. Open-Meteo forecast data is not integrated.",
            "All outputs remain EXPERIMENT_ONLY.",
            "## Decision",
            _markdown_table(frame("onda3_train_start_decision_update_v1")),
            "## Variant Comparison",
            _markdown_table(frame("onda3_train_start_comparison_v1")),
            "## Train/Test Scope",
            _markdown_table(frame("onda3_train_start_scope_v1"), max_rows=20),
            "## Exact Bracket Overall",
            _markdown_table(frame("onda3_train_start_bracket_overall_v1")),
            "## Exact Bracket By Month",
            "any_cp_exact_pct counts a day as correct if any checkpoint hit the exact integer bracket. cp23_exact_pct is the last-checkpoint-only rate.",
            _markdown_table(frame("onda3_train_start_bracket_by_month_day_v1"), max_rows=80),
            "## Exact Bracket By Month And CP",
            _markdown_table(frame("onda3_train_start_bracket_by_month_cp_v1"), max_rows=80),
            "## Binary Macro Regime Performance",
            _markdown_table(frame("onda3_train_start_regime_performance_v1")),
            "## Binary Macro Regime By CP",
            _markdown_table(frame("onda3_train_start_regime_by_cp_v1"), max_rows=40),
            "## Model Results",
            _markdown_table(
                frame("onda3_train_start_model_results_v1").filter(
                    pl.col("model_name") == "ridge_challenger"
                )
                if not frame("onda3_train_start_model_results_v1").is_empty()
                else pl.DataFrame(),
                max_rows=40,
            ),
        ]
    ) + "\n"


def write_onda3_train_start_sensitivity_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for artifact_name, filename in TRAIN_START_FILENAMES.items():
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

    report_path = output_dir / "onda3_train_start_sensitivity_report_v1.md"
    report_path.write_text(
        render_onda3_train_start_sensitivity_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["onda3_train_start_sensitivity_report_md"] = report_path
    return paths
