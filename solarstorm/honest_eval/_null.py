"""Honest null: k_cp plus train-only climatological remaining warming."""
from __future__ import annotations

import polars as pl

from solarstorm.honest_eval._kcp import build_kcp_long

FALLBACK_MONTH = 0


def fit_honest_null(labels: pl.DataFrame, *, train_end_year: int) -> pl.DataFrame:
    """Fit monthly per-CP median remaining warming using train rows only."""
    long = build_kcp_long(labels).join(
        labels.select(["date_local", "tmax_int"]),
        on="date_local",
        how="inner",
    )
    train = long.filter(pl.col("date_local").dt.year() <= train_end_year).with_columns(
        (pl.col("tmax_int") - pl.col("k_cp")).alias("rw"),
        pl.col("date_local").dt.month().alias("month"),
    )
    if train.is_empty():
        raise ValueError("no train rows at or before train_end_year")
    monthly = train.group_by(["month", "cp"]).agg(
        pl.col("rw").median().alias("rw_median"),
        pl.len().alias("n_train_rows"),
    )
    fallback = (
        train.group_by("cp")
        .agg(
            pl.col("rw").median().alias("rw_median"),
            pl.len().alias("n_train_rows"),
        )
        .with_columns(pl.lit(FALLBACK_MONTH).cast(pl.Int8).alias("month"))
    )
    return (
        pl.concat(
            [monthly.with_columns(pl.col("month").cast(pl.Int8)), fallback],
            how="diagonal_relaxed",
        )
        .select(["month", "cp", "rw_median", "n_train_rows"])
        .sort(["cp", "month"])
    )


def predict_honest_null(rows: pl.DataFrame, null_table: pl.DataFrame) -> pl.DataFrame:
    """Add ``null_prediction = k_cp + round(train median remaining warming)``."""
    monthly = null_table.filter(pl.col("month") != FALLBACK_MONTH)
    fallback = null_table.filter(pl.col("month") == FALLBACK_MONTH).select(
        ["cp", pl.col("rw_median").alias("rw_median_fallback")]
    )
    out = (
        rows.with_columns(pl.col("date_local").dt.month().cast(pl.Int8).alias("month"))
        .join(
            monthly.select(["month", "cp", "rw_median"]),
            on=["month", "cp"],
            how="left",
        )
        .join(fallback, on="cp", how="left")
        .with_columns(
            pl.coalesce([pl.col("rw_median"), pl.col("rw_median_fallback")]).alias(
                "_rw"
            )
        )
    )
    if out["_rw"].null_count() > 0:
        raise ValueError("honest null has no fallback for at least one cp")
    return out.with_columns(
        (pl.col("k_cp") + pl.col("_rw").round(0)).alias("null_prediction")
    ).drop(["month", "rw_median", "rw_median_fallback", "_rw"])
