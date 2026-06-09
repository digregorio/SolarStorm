"""Segment evaluation results by CP, regime, window, natural gap."""
from __future__ import annotations

import polars as pl


def segment_results(df: pl.DataFrame, *, by: list[str]) -> dict[str, pl.DataFrame]:
    """Split a results DataFrame into segments by the given column(s).

    Each segment key is the string representation of the group value.
    """
    segments = {}
    for keys, group in df.group_by(by):
        # polars yields the group key as a tuple, even for a single column.
        key = str(keys[0]) if len(by) == 1 else "_".join(str(k) for k in keys)
        segments[key] = group
    return segments


def segment_by_regime(df: pl.DataFrame, regime_col: str = "regime") -> dict[str, pl.DataFrame]:
    return segment_results(df, by=[regime_col])


def segment_by_cp(df: pl.DataFrame, cp_col: str = "cp") -> dict[str, pl.DataFrame]:
    return segment_results(df, by=[cp_col])
