from __future__ import annotations

import polars as pl


def build_onda3_slice_diagnostics(
    matrix: pl.DataFrame,
    *,
    slice_columns: list[str],
) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for column in slice_columns:
        if column not in matrix.columns:
            continue
        grouped = (
            matrix.group_by(column)
            .agg(
                pl.len().alias("rows"),
                pl.col("tmax_int").mean().alias("target_mean"),
            )
            .sort(column)
        )
        for row in grouped.iter_rows(named=True):
            rows.append(
                {
                    "slice_column": column,
                    "slice_value": str(row[column]),
                    "rows": row["rows"],
                    "target_mean": row["target_mean"],
                    "production_status": "EXPERIMENT_ONLY",
                }
            )
    return pl.DataFrame(rows, strict=False)
