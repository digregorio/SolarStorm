from __future__ import annotations

import datetime as dt

import polars as pl


def _ensure_date(df: pl.DataFrame) -> pl.DataFrame:
    if "date_local" in df.columns and df.schema["date_local"] == pl.Utf8:
        return df.with_columns(pl.col("date_local").str.to_date())
    return df


def build_onda3_design_matrix(
    *,
    features: pl.DataFrame,
    labels: pl.DataFrame,
    binary_assignments: pl.DataFrame | None,
    train_end: dt.date,
    test_start: dt.date,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    features = _ensure_date(features)
    labels = _ensure_date(labels)
    matrix = features.join(
        labels.select(["date_local", "tmax_int"]),
        on="date_local",
        how="inner",
    )
    if binary_assignments is not None and not binary_assignments.is_empty():
        assignments = _ensure_date(binary_assignments).select(
            ["date_local", "cp", "binary_macro_regime_label"]
        )
        matrix = matrix.join(assignments, on=["date_local", "cp"], how="left")
    matrix = matrix.with_columns(
        pl.when(pl.col("date_local") <= train_end)
        .then(pl.lit("train"))
        .when(pl.col("date_local") >= test_start)
        .then(pl.lit("test"))
        .otherwise(pl.lit("gap"))
        .alias("fold")
    )
    audit = pl.DataFrame(
        [
            {
                "input_feature_rows": features.height,
                "input_label_rows": labels.height,
                "joined_rows": matrix.height,
                "train_rows": matrix.filter(pl.col("fold") == "train").height,
                "test_rows": matrix.filter(pl.col("fold") == "test").height,
                "production_status": "EXPERIMENT_ONLY",
            }
        ],
        strict=False,
    )
    return matrix, audit
