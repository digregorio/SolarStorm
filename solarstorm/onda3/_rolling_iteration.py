from __future__ import annotations

import polars as pl

from solarstorm.onda3._next_iteration import build_onda3_next_iteration


def build_onda3_rolling_iteration(
    matrix: pl.DataFrame,
    *,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    target_column: str = "tmax_int",
) -> dict[str, pl.DataFrame]:
    result_frames: list[pl.DataFrame] = []
    prediction_frames: list[pl.DataFrame] = []
    diagnostic_frames: list[pl.DataFrame] = []
    uncertainty_frames: list[pl.DataFrame] = []

    dated = matrix.with_columns(pl.col("date_local").dt.year().alias("_year"))
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

        artifacts = build_onda3_next_iteration(
            split.drop("_year"),
            numeric_feature_columns=numeric_feature_columns,
            categorical_feature_columns=categorical_feature_columns,
            target_column=target_column,
        )
        for key, frames in [
            ("onda3_next_model_results_v1", result_frames),
            ("onda3_next_predictions_v1", prediction_frames),
            ("onda3_next_slice_diagnostics_v1", diagnostic_frames),
            ("onda3_next_uncertainty_abstention_v1", uncertainty_frames),
        ]:
            frames.append(artifacts[key].with_columns(pl.lit(test_year).alias("test_year")))

    results = pl.concat(result_frames) if result_frames else pl.DataFrame()
    predictions = pl.concat(prediction_frames) if prediction_frames else pl.DataFrame()
    diagnostics = pl.concat(diagnostic_frames) if diagnostic_frames else pl.DataFrame()
    uncertainty = pl.concat(uncertainty_frames) if uncertainty_frames else pl.DataFrame()

    challenger = results.filter(pl.col("model_name") == "ridge_challenger")
    all_beat = not challenger.is_empty() and bool(
        challenger.select(pl.col("beats_train_mean_null").all()).item()
    )
    temporal = pl.DataFrame(
        [
            {
                "diagnostic": "all_challengers_beat_null",
                "status": "PASS" if all_beat else "BLOCK",
                "test_years": ",".join(str(year) for year in test_years),
                "n_challenger_rows": challenger.height,
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )
    decision = pl.DataFrame(
        [
            {
                "decision_status": (
                    "READY_FOR_ONDA4_MODEL_RERUN"
                    if all_beat
                    else "KEEP_IN_ONDA3_EXPERIMENT_REVIEW"
                ),
                "decision_rationale": (
                    "Onda 3C rolling temporal model iteration completed."
                ),
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )
    return {
        "onda3_rolling_model_results_v1": results,
        "onda3_rolling_predictions_v1": predictions,
        "onda3_rolling_slice_diagnostics_v1": diagnostics,
        "onda3_rolling_uncertainty_abstention_v1": uncertainty,
        "onda3_rolling_temporal_diagnostics_v1": temporal,
        "onda3_rolling_decision_update_v1": decision,
    }
