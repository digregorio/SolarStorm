"""Causal physical regime classifier for NZWN.

The classifier separates weather state from ex-post Tmax timing outcomes.
``late_warming``/late Tmax is deliberately not a regime here because it needs
future information. ``classify_regime()`` only uses the observations it is given,
which lets the feature builder pass a strictly pre-CP slice.
"""
from __future__ import annotations

import polars as pl

PHYSICAL_REGIMES: tuple[str, ...] = (
    "calm_radiative",
    "standard_nw",
    "strong_nw_foehn",
    "southerly_disrupted",
)


def _in_wrapped_sector(value: float | None, start: float, end: float) -> bool:
    if value is None:
        return False
    if start <= end:
        return start <= value <= end
    return value >= start or value <= end


def classify_regime(day_obs: pl.DataFrame) -> tuple[str, dict]:
    """Classify observations into a causal physical regime.

    Expects columns: ``ts_local``, ``tmp_c_int``, ``wind_dir_deg``, ``sknt``,
    ``dwp_c_int``, and ``p01i``. The caller controls causality by passing only
    observations that are visible at the relevant checkpoint.
    """
    if day_obs.height < 3:
        return "insufficient", {}

    obs = day_obs.sort("ts_local")
    obs = obs.with_columns(
        (
            pl.col("tmp_c_int").diff().cast(pl.Float64)
            / pl.col("ts_local").diff().dt.total_hours().cast(pl.Float64)
        ).alias("delta_t_per_h")
    )

    max_delta = obs["delta_t_per_h"].max() or 0.0
    min_delta = obs["delta_t_per_h"].min() or 0.0
    dwp_depression = (obs["tmp_c_int"] - obs["dwp_c_int"]).mean()
    mean_dir = obs["wind_dir_deg"].mean()

    in_nw = obs.filter(
        (pl.col("wind_dir_deg") >= 270) | (pl.col("wind_dir_deg") <= 45)
    )
    nw_flow_strength = (in_nw["sknt"].mean() or 0.0) if in_nw.height > 0 else 0.0
    nw_share = in_nw.height / obs.height if obs.height else 0.0

    in_southerly = obs.filter(
        (pl.col("wind_dir_deg") >= 135) & (pl.col("wind_dir_deg") <= 225)
    )
    southerly_share = in_southerly.height / obs.height if obs.height else 0.0
    southerly_speed = (
        (in_southerly["sknt"].mean() or 0.0) if in_southerly.height > 0 else 0.0
    )

    foehn_score = nw_flow_strength * (
        dwp_depression if dwp_depression is not None else 0.0
    )
    has_precip = (obs["p01i"].sum() or 0.0) > 0.01

    early_dir = obs.filter(pl.col("ts_local").dt.hour() <= 12)["wind_dir_deg"].mean()
    late_dir = obs.filter(pl.col("ts_local").dt.hour() >= 15)["wind_dir_deg"].mean()
    # Compatibility flag for H7. This is an observed day-state change signal,
    # not a new regime label or a validated A -> B regime transition.
    intraday_change = (
        abs(late_dir - early_dir) > 90
        if (early_dir is not None and late_dir is not None)
        else False
    )
    flags = {
        "intraday_regime_change": intraday_change,
        "foehn_score": float(foehn_score),
        "nw_share": float(nw_share),
        "southerly_share": float(southerly_share),
        "max_delta_t_per_h": float(max_delta),
        "min_delta_t_per_h": float(min_delta),
    }

    if has_precip or min_delta < -2.0 or (
        southerly_share >= 0.5 and southerly_speed >= 12.0
    ):
        regime = "southerly_disrupted"
    elif foehn_score > 60.0:
        regime = "strong_nw_foehn"
    elif nw_share >= 0.4 or _in_wrapped_sector(mean_dir, 270, 45):
        regime = "standard_nw"
    else:
        regime = "calm_radiative"

    return regime, flags
