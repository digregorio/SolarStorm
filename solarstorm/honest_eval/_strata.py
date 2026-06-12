"""Remaining-warming lead strata and model-vs-null comparisons."""
from __future__ import annotations

import polars as pl

PRODUCTION_STATUS = "EXPERIMENT_ONLY"
STRATUM_ALREADY_SEEN = "already_seen"
STRATUM_SMALL = "small_1"
STRATUM_FORECAST = "forecast_2_plus"


def assign_remaining_warming_strata(frame: pl.DataFrame) -> pl.DataFrame:
    """Bucket rows by realized ``actual - k_cp`` remaining warming."""
    rw = pl.col("actual") - pl.col("k_cp")
    return frame.with_columns(
        rw.alias("remaining_warming_realized"),
        pl.when(rw <= 0)
        .then(pl.lit(STRATUM_ALREADY_SEEN))
        .when(rw <= 1)
        .then(pl.lit(STRATUM_SMALL))
        .otherwise(pl.lit(STRATUM_FORECAST))
        .alias("rw_stratum"),
    )


def _summary(frame: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
    return (
        frame.group_by(keys)
        .agg(
            pl.len().alias("n_rows"),
            (pl.col("prediction") - pl.col("actual")).abs().mean().alias("model_mae"),
            (pl.col("null_prediction") - pl.col("actual"))
            .abs()
            .mean()
            .alias("null_mae"),
            (pl.col("prediction").round(0) == pl.col("actual"))
            .mean()
            .alias("model_exact_rate"),
            (pl.col("null_prediction").round(0) == pl.col("actual"))
            .mean()
            .alias("null_exact_rate"),
        )
        .with_columns(
            (pl.col("model_mae") < pl.col("null_mae")).alias("model_beats_null"),
            pl.lit(PRODUCTION_STATUS).alias("production_status"),
        )
        .sort(keys)
    )


def build_honest_comparison(frame: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """Build honest-null comparison tables by CP and remaining-warming strata."""
    return {
        "by_cp": _summary(frame, ["cp"]),
        "by_stratum": _summary(frame, ["rw_stratum"]),
        "by_stratum_cp": _summary(frame, ["rw_stratum", "cp"]),
    }
