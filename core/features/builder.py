"""CP-aware feature builder (REQ-DAT-2, REQ-CON-5, REQ-AUD-4, design 4.5).

For each ``(date_local, cp_utc)`` we emit a single row whose ``feature_max_ts_utc``
is strictly less than ``cp_utc`` (closed='left'). The builder raises on any
violation - no silent leakage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import polars as pl

from core.io.timeutil import cp_to_utc, day_local_window
from core.labels.tmax import k_cp


@dataclass(frozen=True)
class CPFeatures:
    date_local: date
    cp_utc: datetime
    cp_local: datetime
    tz_name: str
    feature_max_ts_utc: datetime
    features: dict[str, Any]
    data_quality: dict[str, str]


def _filter_until(obs: pl.DataFrame, cp_utc: datetime) -> pl.DataFrame:
    """Return obs with ts_utc strictly less than cp_utc and tmp_c_int valid."""
    return obs.filter(
        (pl.col("ts_utc") < cp_utc) & (pl.col("dq_tmp_c_int") != "missing")
    ).sort("ts_utc")


def _slope(times_min: list[float], values: list[float | None]) -> float | None:
    """OLS slope per minute. Skips ``None`` values, returns ``None`` if < 2 points."""
    pairs = [(t, v) for t, v in zip(times_min, values, strict=True) if v is not None]
    if len(pairs) < 2:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    return num / den


def build_cp_features(
    observations: pl.DataFrame,
    *,
    date_local: date,
    cp_hhmm: str,
    tz_name: str,
    labels: pl.DataFrame | None = None,
) -> CPFeatures:
    """Build the per-CP feature row.

    ``observations`` covers at least ``[day_local - 1, day_local + 1]`` to support D-1 lookups.
    """
    cp_utc = cp_to_utc(date_local, cp_hhmm)
    day_start_utc, _ = day_local_window(date_local, tz_name=tz_name)

    # 1) until-CP slice
    sub = _filter_until(observations, cp_utc)
    sub_today = sub.filter(pl.col("ts_utc") >= day_start_utc)

    feats: dict[str, Any] = {}
    dq: dict[str, str] = {}

    # 2) t_so_far_max_c_int
    if sub_today.height > 0:
        max_idx = sub_today["tmp_c_int"].arg_max()
        t_so_far_max = int(sub_today["tmp_c_int"][max_idx])
        t_so_far_max_ts: datetime = sub_today["ts_utc"][max_idx]
        age_min = int((cp_utc - t_so_far_max_ts).total_seconds() // 60)
        feats["t_so_far_max_c_int"] = t_so_far_max
        feats["t_so_far_max_age_min"] = age_min
        feats["last_obs_tmp_c_int"] = int(sub_today["tmp_c_int"][-1])
        dq["t_so_far_max_c_int"] = "ok"
    else:
        feats["t_so_far_max_c_int"] = None
        feats["t_so_far_max_age_min"] = None
        feats["last_obs_tmp_c_int"] = None
        dq["t_so_far_max_c_int"] = "missing"

    # 3) k_cp (alias of t_so_far_max for predict-time consumers)
    kcp = k_cp(observations.filter(pl.col("ts_utc") >= day_start_utc), cp_utc)
    feats["k_cp"] = kcp
    dq["k_cp"] = "ok" if kcp is not None else "missing"

    # 4) Slopes 3h / 6h on tmp_c_dec
    cp_minus_3 = cp_utc - timedelta(hours=3)
    cp_minus_6 = cp_utc - timedelta(hours=6)
    feats["slope_3h_c_per_h"] = _compute_slope(sub, cp_utc, cp_minus_3)
    feats["slope_6h_c_per_h"] = _compute_slope(sub, cp_utc, cp_minus_6)

    # 5) Wind, qnh - latest
    if sub.height > 0:
        last_row = sub[-1]
        feats["wind_dir_deg"] = _opt_float(last_row.get_column("drct").item() if "drct" in sub.columns else None)
        feats["wind_speed_kt"] = _opt_float(last_row.get_column("sknt").item() if "sknt" in sub.columns else None)
        if "alti" in sub.columns:
            alti = last_row.get_column("alti").item()
            feats["qnh_hpa"] = _opt_float(alti * 33.8639 if alti is not None else None)
        else:
            feats["qnh_hpa"] = None
    else:
        feats["wind_dir_deg"] = None
        feats["wind_speed_kt"] = None
        feats["qnh_hpa"] = None

    # 6) Climatology placeholders (filled by caller using a fitted Climatology)
    feats["clim_tmax_c_dec"] = None
    feats["clim_tmax_int"] = None

    # 7) D-1 labels
    if labels is not None and "date_local" in labels.columns:
        d1 = date_local - timedelta(days=1)
        prev = labels.filter(pl.col("date_local") == d1)
        if prev.height == 1:
            feats["tmax_d_minus_1_int"] = _opt_int(prev["tmax_int"][0])
            feats["tmin_d_minus_1_int"] = _opt_int(prev["tmin_int"][0])
        else:
            feats["tmax_d_minus_1_int"] = None
            feats["tmin_d_minus_1_int"] = None
    else:
        feats["tmax_d_minus_1_int"] = None
        feats["tmin_d_minus_1_int"] = None

    # 8) Causality check
    feature_max_ts = sub["ts_utc"].max() if sub.height > 0 else day_start_utc - timedelta(seconds=1)
    if feature_max_ts is not None and feature_max_ts >= cp_utc:
        raise RuntimeError(
            f"Causality violation (REQ-CON-5): feature_max_ts={feature_max_ts.isoformat()} >= cp_utc={cp_utc.isoformat()}"
        )

    cp_local = cp_utc.astimezone(ZoneInfo(tz_name))
    return CPFeatures(
        date_local=date_local,
        cp_utc=cp_utc,
        cp_local=cp_local,
        tz_name=tz_name,
        feature_max_ts_utc=feature_max_ts,
        features=feats,
        data_quality=dq,
    )


def _compute_slope(
    sub: pl.DataFrame, cp_utc: datetime, cp_minus_h: datetime
) -> float | None:
    """OLS slope of ``T_obs_dec`` (decimal degC, derived from tmpf) over [cp - h, cp).

    Per design 4.1.1, ``T_obs_dec`` is the correct feature signal; ``T_obs_int`` is
    only used for labels and audits. Computing slopes on integer T would produce a
    step function with mostly-zero slopes between integer transitions (review #15).
    """
    if "tmpf" not in sub.columns:
        return None
    window = sub.filter(
        (pl.col("ts_utc") >= cp_minus_h) & (pl.col("ts_utc") < cp_utc)
    ).select(["ts_utc", "tmpf"])
    if window.height < 2:
        return None
    t0 = window["ts_utc"][0]
    times_min = [(t - t0).total_seconds() / 60.0 for t in window["ts_utc"].to_list()]
    tmpf = window["tmpf"].to_list()
    tmpc = [None if v is None else (v - 32.0) * 5.0 / 9.0 for v in tmpf]
    s = _slope(times_min, tmpc)  # _slope filters Nones; arrays must stay aligned
    return None if s is None else s * 60.0  # per hour


def _opt_float(x: object) -> float | None:
    if x is None:
        return None
    try:
        f = float(x)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if f != f:
        return None
    return f


def _opt_int(x: object) -> int | None:
    if x is None:
        return None
    try:
        return int(x)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def build_panel(
    observations: pl.DataFrame,
    labels: pl.DataFrame,
    *,
    tz_name: str,
    cp_set: Iterable[str],
    dates: Iterable[date] | None = None,
) -> pl.DataFrame:
    """Build the full ``(date_local, cp)`` panel as a Polars frame.

    Adds ``k_cp__cp_HH`` per CP from ``CPFeatures.features['k_cp']`` for downstream
    empirical conditional fitting.
    """
    cp_set = list(cp_set)
    if dates is None:
        dates = labels["date_local"].drop_nulls().unique().to_list()
    # Precompute label_map (review #6): single O(n) pass over labels avoids ~2 filters
    # per date. Stays O(n + len(dates) * len(cp_set)).
    label_map: dict[date, dict[str, Any]] = {}
    if labels.height:
        for row in labels.select(["date_local", "tmax_int", "day_complete"]).iter_rows(named=True):
            d_key = row["date_local"]
            if d_key is not None:
                label_map[d_key] = row
    rows: list[dict[str, Any]] = []
    for d in dates:
        if d is None:
            continue
        base: dict[str, Any] = {"date_local": d}
        # Lookup against the precomputed label_map (review #6 prep).
        label_row = label_map.get(d)
        tmax_int = label_row["tmax_int"] if label_row is not None else None
        day_complete = bool(label_row["day_complete"]) if label_row is not None else False
        base["tmax_int"] = tmax_int
        base["day_complete"] = day_complete
        base["month"] = d.month
        for cp in cp_set:
            try:
                f = build_cp_features(
                    observations, date_local=d, cp_hhmm=cp, tz_name=tz_name, labels=labels
                )
                base[f"k_cp__cp_{cp[:2]}"] = f.features["k_cp"]
            except RuntimeError as exc:
                # Causality violations (REQ-CON-5) and out-of-window CP (review #2) MUST
                # propagate. Swallowing them would hide leakage and silently shift dates.
                raise RuntimeError(
                    f"build_panel: build_cp_features failed for date={d} cp={cp}: {exc}"
                ) from exc
        rows.append(base)
    return pl.DataFrame(rows)


def build_empirical_panel_fast(
    observations: pl.DataFrame,
    labels: pl.DataFrame,
    *,
    tz_name: str,
    cp_set: Iterable[str],
    dates: Iterable[date] | None = None,
) -> pl.DataFrame:
    """Build the narrow empirical panel without per-date dataframe scans.

    The empirical baseline only needs ``date_local``, ``month``, ``tmax_int``,
    ``day_complete`` and one ``k_cp__cp_HH`` column per CP. The generic
    ``build_panel`` computes those values by calling ``build_cp_features`` for
    every date/CP, which is intentionally rich but too expensive for live
    forecasting. This narrow path keeps the same CP causality contract
    (``ts_utc < cp_utc`` and non-missing integer temperature) with a single
    pre-filtered observation scan per CP.
    """
    cp_set = list(cp_set)
    if dates is None:
        date_list = labels["date_local"].drop_nulls().unique().to_list()
    else:
        date_list = [d for d in dates if d is not None]
    date_set = set(date_list)
    label_rows: list[dict[str, Any]] = []
    if labels.height:
        for row in labels.select(["date_local", "tmax_int", "day_complete"]).iter_rows(named=True):
            d_key = row["date_local"]
            if d_key is not None and d_key in date_set:
                label_rows.append({
                    "date_local": d_key,
                    "tmax_int": row["tmax_int"],
                    "day_complete": bool(row["day_complete"]),
                    "month": d_key.month,
                })
    if not label_rows:
        return pl.DataFrame(
            schema={
                "date_local": pl.Date,
                "tmax_int": pl.Int32,
                "day_complete": pl.Boolean,
                "month": pl.Int32,
                **{f"k_cp__cp_{cp[:2]}": pl.Int32 for cp in cp_set},
            }
        )

    panel = pl.DataFrame(
        label_rows,
        schema_overrides={
            "date_local": pl.Date,
            "tmax_int": pl.Int32,
            "day_complete": pl.Boolean,
            "month": pl.Int32,
        },
    ).sort("date_local")
    obs_valid = (
        observations.filter(
            pl.col("tmp_c_int").is_not_null() & (pl.col("dq_tmp_c_int") != "missing")
        )
        .with_columns(
            pl.col("ts_utc").dt.convert_time_zone(tz_name).dt.date().alias("date_local")
        )
        .filter(pl.col("date_local").is_in(date_list))
        .select(["date_local", "ts_utc", "tmp_c_int"])
    )

    for cp in cp_set:
        cp_rows = [{"date_local": d, "cp_utc": cp_to_utc(d, cp)} for d in date_list]
        cp_frame = pl.DataFrame(
            cp_rows,
            schema_overrides={"date_local": pl.Date, "cp_utc": pl.Datetime("us", time_zone="UTC")},
        )
        if cp_frame.is_empty() or obs_valid.is_empty():
            kcp = pl.DataFrame(
                {"date_local": date_list, f"k_cp__cp_{cp[:2]}": [None] * len(date_list)},
                schema_overrides={"date_local": pl.Date, f"k_cp__cp_{cp[:2]}": pl.Int32},
            )
        else:
            kcp = (
                cp_frame.join(obs_valid, on="date_local", how="left")
                .filter(pl.col("ts_utc") < pl.col("cp_utc"))
                .group_by("date_local")
                .agg(pl.col("tmp_c_int").max().cast(pl.Int32).alias(f"k_cp__cp_{cp[:2]}"))
            )
        panel = panel.join(kcp, on="date_local", how="left")
    return panel


__all__ = ["CPFeatures", "build_cp_features", "build_panel", "build_empirical_panel_fast"]
