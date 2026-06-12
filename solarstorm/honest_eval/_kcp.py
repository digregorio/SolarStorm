"""k_cp wide-to-long view over the labels table."""
from __future__ import annotations

import polars as pl

KCP_PREFIX = "k_cp__cp_"


def build_kcp_long(labels: pl.DataFrame) -> pl.DataFrame:
    """Unpivot ``k_cp__cp_HHMM`` columns into ``date_local, cp, k_cp`` rows."""
    kcp_columns = [column for column in labels.columns if column.startswith(KCP_PREFIX)]
    if not kcp_columns:
        raise ValueError("labels frame has no k_cp__cp_* columns")
    long = labels.select(["date_local", *kcp_columns]).unpivot(
        index="date_local",
        on=kcp_columns,
        variable_name="kcol",
        value_name="k_cp",
    )
    return (
        long.drop_nulls("k_cp")
        .with_columns(
            (
                pl.col("kcol").str.slice(len(KCP_PREFIX), 2)
                + pl.lit(":")
                + pl.col("kcol").str.slice(len(KCP_PREFIX) + 2, 2)
            ).alias("cp")
        )
        .select(["date_local", "cp", "k_cp"])
    )
