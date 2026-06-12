from __future__ import annotations

import polars as pl

from solarstorm.onda3._rolling_iteration import build_onda3_rolling_iteration

INTERACTION_CONTINUOUS_COLUMNS = ("foehn_score", "cloud_cover_suppression")
INTERACTION_MACROS = ("macro_non_southerly", "macro_southerly_flow")


def add_binary_macro_interaction_features(
    matrix: pl.DataFrame,
    *,
    macro_column: str = "binary_macro_regime_label",
    continuous_columns: tuple[str, ...] = INTERACTION_CONTINUOUS_COLUMNS,
    macro_values: tuple[str, ...] = INTERACTION_MACROS,
) -> tuple[pl.DataFrame, list[str]]:
    interaction_columns: list[str] = []
    expressions = []
    for source_column in continuous_columns:
        if source_column not in matrix.columns:
            continue
        for macro_value in macro_values:
            interaction_column = f"{source_column}_x_{macro_value}"
            interaction_columns.append(interaction_column)
            expressions.append(
                pl.when(pl.col(macro_column) == macro_value)
                .then(pl.col(source_column).cast(pl.Float64))
                .otherwise(0.0)
                .alias(interaction_column)
            )
    if not expressions:
        return matrix, interaction_columns
    return matrix.with_columns(expressions), interaction_columns


def _interaction_feature_audit(interaction_columns: list[str]) -> pl.DataFrame:
    rows = []
    for interaction_column in interaction_columns:
        source_feature, macro_value = interaction_column.split("_x_", maxsplit=1)
        rows.append(
            {
                "feature": interaction_column,
                "source_feature": source_feature,
                "macro_value": macro_value,
                "interaction_type": "continuous_x_binary_macro",
                "production_status": "EXPERIMENT_ONLY",
            }
        )
    return pl.DataFrame(rows, strict=False)


def build_interaction_feature_manifest(
    base_manifest: pl.DataFrame,
    interaction_audit: pl.DataFrame,
) -> pl.DataFrame:
    if interaction_audit.is_empty():
        return base_manifest
    interaction_rows = interaction_audit.select(
        [
            pl.col("feature"),
            pl.lit(True).alias("included_in_onda3"),
            pl.lit("causal_pre_cp_or_experiment_only").alias("leakage_class"),
            pl.lit("interaction_input").alias("feature_role"),
            pl.lit("EXPERIMENT_ONLY").alias("production_status"),
        ]
    )
    return pl.concat([base_manifest, interaction_rows], how="vertical")


def _comparison(base_results: pl.DataFrame, interaction_results: pl.DataFrame) -> pl.DataFrame:
    base_challenger = base_results.filter(pl.col("model_name") == "ridge_challenger")
    interaction_challenger = interaction_results.filter(
        pl.col("model_name") == "ridge_challenger"
    )
    joined = interaction_challenger.join(
        base_challenger.select(
            [
                "cp",
                "test_year",
                pl.col("mae").alias("no_interaction_mae"),
            ]
        ),
        on=["cp", "test_year"],
        how="left",
    )
    return joined.select(
        [
            "cp",
            "test_year",
            pl.col("mae").alias("interaction_mae"),
            "no_interaction_mae",
            (pl.col("mae") - pl.col("no_interaction_mae")).alias("mae_delta"),
            (pl.col("mae") < pl.col("no_interaction_mae")).alias(
                "beats_no_interaction"
            ),
            pl.lit("EXPERIMENT_ONLY").alias("production_status"),
        ]
    )


def build_onda3_interaction_iteration(
    matrix: pl.DataFrame,
    *,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    target_column: str = "tmax_int",
) -> dict[str, pl.DataFrame]:
    enriched, interaction_columns = add_binary_macro_interaction_features(matrix)
    interaction_audit = _interaction_feature_audit(interaction_columns)
    base_artifacts = build_onda3_rolling_iteration(
        matrix,
        test_years=test_years,
        numeric_feature_columns=numeric_feature_columns,
        categorical_feature_columns=categorical_feature_columns,
        target_column=target_column,
    )
    interaction_artifacts = build_onda3_rolling_iteration(
        enriched,
        test_years=test_years,
        numeric_feature_columns=[*numeric_feature_columns, *interaction_columns],
        categorical_feature_columns=categorical_feature_columns,
        target_column=target_column,
    )
    comparison = _comparison(
        base_artifacts["onda3_rolling_model_results_v1"],
        interaction_artifacts["onda3_rolling_model_results_v1"],
    )
    challenger = interaction_artifacts["onda3_rolling_model_results_v1"].filter(
        pl.col("model_name") == "ridge_challenger"
    )
    all_beat_null = not challenger.is_empty() and bool(
        challenger.select(pl.col("beats_train_mean_null").all()).item()
    )
    mean_delta = (
        float(comparison["mae_delta"].mean()) if not comparison.is_empty() else 0.0
    )
    beats_current_surface = mean_delta < 0.0
    decision = pl.DataFrame(
        [
            {
                "decision_status": (
                    "READY_FOR_ONDA4_MODEL_RERUN"
                    if all_beat_null and beats_current_surface
                    else "KEEP_IN_ONDA3_EXPERIMENT_REVIEW"
                ),
                "decision_rationale": (
                    "Onda 3D binary-macro interaction experiment completed."
                ),
                "mean_mae_delta_vs_no_interaction": mean_delta,
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )
    return {
        "onda3_interaction_feature_audit_v1": interaction_audit,
        "onda3_interaction_model_results_v1": interaction_artifacts[
            "onda3_rolling_model_results_v1"
        ],
        "onda3_interaction_predictions_v1": interaction_artifacts[
            "onda3_rolling_predictions_v1"
        ],
        "onda3_interaction_slice_diagnostics_v1": interaction_artifacts[
            "onda3_rolling_slice_diagnostics_v1"
        ],
        "onda3_interaction_uncertainty_abstention_v1": interaction_artifacts[
            "onda3_rolling_uncertainty_abstention_v1"
        ],
        "onda3_interaction_temporal_diagnostics_v1": interaction_artifacts[
            "onda3_rolling_temporal_diagnostics_v1"
        ],
        "onda3_interaction_challenger_comparison_v1": comparison,
        "onda3_interaction_decision_update_v1": decision,
    }
