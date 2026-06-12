"""Physical-floor helpers for honest evaluation."""
from __future__ import annotations

import polars as pl

PRODUCTION_STATUS = "EXPERIMENT_ONLY"


def apply_physical_floor(
    frame: pl.DataFrame,
    *,
    prediction_col: str = "prediction",
    k_cp_col: str = "k_cp",
) -> pl.DataFrame:
    """Audit raw floor violations and add a clamped prediction column."""
    return frame.with_columns(
        pl.max_horizontal(pl.col(prediction_col), pl.col(k_cp_col).cast(pl.Float64))
        .alias("prediction_floored"),
        (pl.col(prediction_col) < pl.col(k_cp_col)).alias("floor_violation"),
    )


def build_floor_violation_audit(frame: pl.DataFrame) -> pl.DataFrame:
    """Report raw and clamped physical-floor violation rates overall and by CP."""
    audited = frame.with_columns(
        (pl.col("prediction_floored") < pl.col("k_cp")).alias("_clamped_violation")
    )
    per_cp = audited.group_by("cp").agg(
        pl.len().alias("n_rows"),
        pl.col("floor_violation").sum().alias("n_raw_violations"),
        pl.col("_clamped_violation").sum().alias("n_clamped_violations"),
    )
    overall = audited.select(
        pl.lit("ALL").alias("cp"),
        pl.len().alias("n_rows"),
        pl.col("floor_violation").sum().alias("n_raw_violations"),
        pl.col("_clamped_violation").sum().alias("n_clamped_violations"),
    )
    return (
        pl.concat([overall, per_cp.sort("cp")], how="diagonal_relaxed")
        .with_columns(
            (pl.col("n_raw_violations") * 100.0 / pl.col("n_rows")).alias(
                "raw_violation_pct"
            ),
            (pl.col("n_clamped_violations") * 100.0 / pl.col("n_rows")).alias(
                "clamped_violation_pct"
            ),
            pl.lit(PRODUCTION_STATUS).alias("production_status"),
        )
        .select(
            [
                "cp",
                "n_rows",
                "n_raw_violations",
                "raw_violation_pct",
                "n_clamped_violations",
                "clamped_violation_pct",
                "production_status",
            ]
        )
    )
