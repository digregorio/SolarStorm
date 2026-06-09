"""Climatology baselines: DOY-smoothed mean, CP x month, Tmax-hour distribution."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import numpy as np
import polars as pl


@dataclass
class Climatology:
    by_doy: dict[int, float]              # DOY → smoothed mean Tmax
    by_month: dict[int, dict[str, float]]  # month → {mean, p10, p50, p90}
    train_window: tuple[dt.date, dt.date]
    n_train_days: int

    def tmax_dec_for(self, d: dt.date) -> float:
        doy = d.timetuple().tm_yday
        return self.by_doy.get(doy, self.by_month[d.month]["mean"])

    def percentiles_for(self, d: dt.date, p_low: float = 0.1, p_high: float = 0.9) -> tuple[float, float]:
        m = self.by_month[d.month]
        return (m.get(f"p{int(p_low*100):.0f}", m["mean"]),
                m.get(f"p{int(p_high*100):.0f}", m["mean"]))


def fit_climatology(
    labels: pl.DataFrame,
    *,
    train_start: dt.date,
    train_end: dt.date,
    smoothing_window_days: int = 31,
) -> Climatology:
    """Fit DOY-smoothed and monthly climatology from daily Tmax labels.

    Requires ≥365 complete training days.
    """
    mask = (
        pl.col("date_local").is_between(train_start, train_end)
        & pl.col("day_complete")
        & pl.col("tmax_int").is_not_null()
    )
    train = labels.filter(mask)
    if train.height < 365:
        raise ValueError(f"Need ≥365 train days, got {train.height}")

    doy_raw = train.with_columns(
        pl.col("date_local").dt.ordinal_day().alias("doy")
    ).group_by("doy").agg(pl.col("tmax_int").mean().alias("mean")).sort("doy")

    raw_means = np.full(367, np.nan)
    for row in doy_raw.iter_rows(named=True):
        raw_means[row["doy"]] = row["mean"]

    # Linear interpolation through NaNs with circular wrap
    idx = np.arange(1, 367)
    valid = ~np.isnan(raw_means[1:367])
    if valid.sum() < 2:
        raise ValueError("Too few valid DOYs for interpolation")
    raw_means[1:367] = np.interp(idx, idx[valid], raw_means[1:367][valid])
    raw_means[0] = raw_means[366]

    # Circular smoothing
    half = smoothing_window_days // 2
    padded = np.concatenate([raw_means[-half:], raw_means, raw_means[:half]])
    kernel = np.ones(smoothing_window_days) / smoothing_window_days
    smoothed = np.convolve(padded, kernel, mode="valid")
    by_doy = {doy: float(smoothed[doy]) for doy in range(1, 367)}

    # Monthly stats
    monthly = train.with_columns(pl.col("date_local").dt.month().alias("month"))
    by_month = {}
    for m in range(1, 13):
        vals = monthly.filter(pl.col("month") == m)["tmax_int"].to_numpy()
        if len(vals) > 0:
            by_month[m] = {
                "mean": float(np.mean(vals)),
                "p10": float(np.percentile(vals, 10)),
                "p50": float(np.percentile(vals, 50)),
                "p90": float(np.percentile(vals, 90)),
            }
        else:
            by_month[m] = {"mean": 15.0, "p10": 10.0, "p50": 15.0, "p90": 20.0}

    return Climatology(
        by_doy=by_doy,
        by_month=by_month,
        train_window=(train_start, train_end),
        n_train_days=train.height,
    )
