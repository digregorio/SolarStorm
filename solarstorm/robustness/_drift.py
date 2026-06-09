"""Calendar-time drift checks for Onda 4."""
from __future__ import annotations

import json
import math
from pathlib import Path

import polars as pl

from solarstorm.robustness._config import R4_TREND_ALPHA


def _normal_two_sided_p(z: float) -> float:
    return float(math.erfc(abs(z) / math.sqrt(2.0)))


def _mann_kendall(values: list[float]) -> tuple[float, float]:
    n = len(values)
    if n < 3:
        return 0.0, 1.0

    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            if values[j] > values[i]:
                s += 1
            elif values[j] < values[i]:
                s -= 1

    var_s = n * (n - 1) * (2 * n + 5) / 18.0
    if var_s <= 0:
        return float(s), 1.0

    if s > 0:
        z = (s - 1) / math.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / math.sqrt(var_s)
    else:
        z = 0.0
    return float(s), _normal_two_sided_p(z)


def _gap_expression(year_matrix: pl.DataFrame) -> pl.Expr:
    if {"best_null_mae", "challenger_mae"}.issubset(year_matrix.columns):
        return (pl.col("best_null_mae") - pl.col("challenger_mae")).alias("gap")
    if "effect_size" in year_matrix.columns:
        return pl.col("effect_size").alias("gap")
    raise ValueError("year_matrix must include effect_size or MAE columns")


def compute_drift_trend(year_matrix: pl.DataFrame) -> dict:
    """Compute Mann-Kendall trend over per-year feature-null gaps."""
    if year_matrix.height == 0:
        return {
            "trend_statistic": 0.0,
            "p_value": 1.0,
            "trend_direction": "flat",
            "warning": False,
            "per_year_gaps": {},
        }

    grouped = (
        year_matrix.with_columns(_gap_expression(year_matrix))
        .drop_nulls(["gap"])
        .group_by("year")
        .agg(pl.col("gap").mean().alias("gap"))
        .sort("year")
    )
    if grouped.height == 0:
        return {
            "trend_statistic": 0.0,
            "p_value": 1.0,
            "trend_direction": "flat",
            "warning": False,
            "per_year_gaps": {},
        }

    years = grouped["year"].to_list()
    values = [float(v) for v in grouped["gap"].to_list()]
    statistic, p_value = _mann_kendall(values)
    if statistic < 0:
        direction = "decreasing"
    elif statistic > 0:
        direction = "increasing"
    else:
        direction = "flat"

    return {
        "trend_statistic": statistic,
        "p_value": p_value,
        "trend_direction": direction,
        "warning": direction == "decreasing" and p_value < R4_TREND_ALPHA,
        "per_year_gaps": {int(year): float(gap) for year, gap in zip(years, values, strict=True)},
    }


def write_drift_snapshot(trend: dict, path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(trend, indent=2, sort_keys=True), encoding="utf-8")
