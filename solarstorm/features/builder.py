"""Causal feature builder: computes all H1-H23 feature columns from obs + labels."""
from __future__ import annotations

import datetime as dt
import json
import math
from typing import Any
from zoneinfo import ZoneInfo

import polars as pl

from solarstorm._config import TZ_NAME
from solarstorm._contracts import require_causal
from solarstorm.data._calendar import cp_to_utc
from solarstorm.eda._catalog import SEED_HYPOTHESES
from solarstorm.eda._regimes import classify_regime

ANCHOR_HOURS = (6, 9, 12, 15, 18)

_SKY_WEIGHTS: dict[str, float] = {
    "OVC": 1.0, "BKN": 0.75, "SCT": 0.4, "FEW": 0.2, "CLR": 0.0,
}

BLOCKED_FEATURES: dict[str, str] = {
    "sst_maritime_cap": "Requires Cook Strait SST — no METAR source available (H19)",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coverage_weight(code: str | None) -> float | None:
    """Return cloud coverage weight or None for unknown/missing codes (Fix 18)."""
    if code is None:
        return None
    return _SKY_WEIGHTS.get(code)


def _annotate_obs(obs: pl.DataFrame) -> pl.DataFrame:
    """Ensure ts_local, date_local, hour_local, wind_dir_deg columns exist."""
    if "ts_local" not in obs.columns:
        obs = obs.with_columns(
            pl.col("valid").dt.convert_time_zone(TZ_NAME).alias("ts_local"),
        )
    if "date_local" not in obs.columns:
        obs = obs.with_columns(
            pl.col("ts_local").dt.date().alias("date_local"),
        )
    if "hour_local" not in obs.columns:
        obs = obs.with_columns(
            pl.col("ts_local").dt.hour().alias("hour_local"),
        )
    if "wind_dir_deg" not in obs.columns and "drct" in obs.columns:
        obs = obs.with_columns(pl.col("drct").alias("wind_dir_deg"))
    return obs


def _nearest_anchor_value(
    slice_df: pl.DataFrame, anchor_hour: int, d: dt.date, col: str,
) -> Any:
    """Value of *col* in the obs nearest to *anchor_hour* within 30 min."""
    anchor_local = dt.datetime(
        d.year, d.month, d.day, anchor_hour, 0, tzinfo=ZoneInfo(TZ_NAME),
    )
    candidates = slice_df.filter(
        (pl.col("ts_local") - anchor_local).dt.total_minutes().abs() <= 30,
    )
    if candidates.height == 0:
        return None
    diffs = (candidates["ts_local"] - anchor_local).dt.total_minutes().abs()
    return candidates[col][diffs.arg_min()]


def _circular_mean_dir(slice_df: pl.DataFrame) -> float | None:
    """Circular mean of wind direction using vector sum (handles 0°/360° wrap)."""
    vals = slice_df["drct"].drop_nulls()
    if len(vals) == 0:
        return None
    sin_sum = sum(math.sin(math.radians(v)) for v in vals)
    cos_sum = sum(math.cos(math.radians(v)) for v in vals)
    if abs(sin_sum) < 1e-10 and abs(cos_sum) < 1e-10:
        return None
    return math.degrees(math.atan2(sin_sum, cos_sum)) % 360.0


def _mean_drct(slice_df: pl.DataFrame) -> float | None:
    vals = slice_df["drct"].drop_nulls()
    if len(vals) == 0:
        return None
    return vals.mean()


def _mean_wind_in_sector(slice_df: pl.DataFrame, start: float, end: float) -> float | None:
    """Mean wind direction of obs whose drct falls in [start, end] (handles 0°/360° wrap)."""
    if start <= end:
        mask = (pl.col("drct") >= start) & (pl.col("drct") <= end)
    else:
        mask = (pl.col("drct") >= start) | (pl.col("drct") <= end)
    in_sector = slice_df.filter(mask & pl.col("drct").is_not_null())
    if in_sector.height == 0:
        return None
    return in_sector["drct"].mean()


def _in_sector(val: float, start: float, end: float) -> bool:
    if start <= end:
        return start <= val <= end
    return val >= start or val <= end


def _max_cloud_cover(slice_df: pl.DataFrame) -> float | None:
    best: float | None = None
    for i in range(1, 5):
        col = f"skyc{i}"
        if col not in slice_df.columns:
            continue
        for val in slice_df[col].to_list():
            if val is not None:
                w = _coverage_weight(str(val))
                if w is not None and (best is None or w > best):
                    best = w
    return best


def _cloud_base_transparency(slice_df: pl.DataFrame) -> float | None:
    best: float | None = None
    for i in range(1, 5):
        ccol = f"skyc{i}"
        hcol = f"skyl{i}"
        if ccol not in slice_df.columns:
            continue
        codes = slice_df[ccol].to_list()
        heights = (
            slice_df[hcol].to_list()
            if hcol in slice_df.columns
            else [None] * len(codes)
        )
        for code, ht in zip(codes, heights, strict=True):
            if code is None:
                continue
            cw = _coverage_weight(str(code))
            if cw is None:
                continue
            ht_ok = ht if ht is not None else 0
            score = cw * min(1.0, ht_ok / 8000.0)
            if best is None or score > best:
                best = score
    return best


def _has_wxcode(slice_df: pl.DataFrame, code: str) -> bool:
    return any(val is not None and code in str(val) for val in slice_df["wxcodes"].to_list())


def _classify_regime_for_date(day_obs: pl.DataFrame) -> tuple[str, dict]:
    if day_obs.height < 3:
        return "insufficient", {}
    wd = "wind_dir_deg" if "wind_dir_deg" in day_obs.columns else "drct"
    return classify_regime(
        day_obs.with_columns(pl.col(wd).alias("wind_dir_deg")),
    )


def _obs_by_date(obs: pl.DataFrame) -> dict[dt.date, pl.DataFrame]:
    """Partition annotated observations by local date in chronological order."""
    obs = _annotate_obs(obs)
    groups: dict[dt.date, pl.DataFrame] = {}
    for day_obs in obs.partition_by("date_local", maintain_order=True):
        if day_obs.height == 0:
            continue
        groups[day_obs["date_local"][0]] = day_obs
    return groups


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------

def build_features(
    obs: pl.DataFrame,
    labels: pl.DataFrame,
    *,
    cp_set: tuple[str, ...] = ("20:00", "21:00", "22:00", "23:00"),
) -> pl.DataFrame:
    """Build a causal feature table, one row per (date_local, cp).

    Args:
        obs: Observation DataFrame with columns from _obs.py.
        labels: Daily labels DataFrame with date_local, tmax_int, tmin_int,
                tmax_hour, and k_cp__cp_* columns.
        cp_set: Checkpoint hour strings (default CP_SET_UTC).

    Returns:
        DataFrame with ``date_local``, ``cp``, ``regime_label``,
        ``regime_flags``, and all H1-H23 feature columns.
    """
    obs = _annotate_obs(obs).sort("valid")
    tz = ZoneInfo(TZ_NAME)

    obs_by_date = _obs_by_date(obs)
    dates = list(obs_by_date)

    # ---- Build label lookups (neighbour-day values only — no future leakage) ----
    # Pre-build dicts: date → tmax_int, tmin_int, tmax_hour for fast lookup
    label_by_date: dict[dt.date, dict[str, Any]] = {}
    for lr in labels.iter_rows(named=True):
        d_lab = lr["date_local"]
        label_by_date[d_lab] = lr

    rows: list[dict[str, Any]] = []

    for d in dates:
        day_obs = obs_by_date[d]

        # Labels for this date and neighbour days
        lr = label_by_date.get(d)
        if lr is None:
            continue
        lr_m1 = label_by_date.get(d - dt.timedelta(days=1))
        tmax_dminus1 = lr_m1.get("tmax_int") if lr_m1 else None

        lr_m2 = label_by_date.get(d - dt.timedelta(days=2))
        tmax_dminus2 = lr_m2.get("tmax_int") if lr_m2 else None

        lr_m3 = label_by_date.get(d - dt.timedelta(days=3))
        tmax_dminus3 = lr_m3.get("tmax_int") if lr_m3 else None

        # H9: day_sequence_pattern — uses only D-1, D-2, D-3 (causal, no target leakage)
        day_seq: str | None = None
        if tmax_dminus1 is not None and tmax_dminus2 is not None and tmax_dminus3 is not None:
            if abs(tmax_dminus1 - tmax_dminus2) <= 1 and abs(tmax_dminus2 - tmax_dminus3) <= 1:
                day_seq = "flat"
            elif tmax_dminus3 < tmax_dminus2 < tmax_dminus1:
                day_seq = "warming"
            elif tmax_dminus3 > tmax_dminus2 > tmax_dminus1:
                day_seq = "cooling"
            elif tmax_dminus3 < tmax_dminus2 > tmax_dminus1:
                day_seq = "peaked"
            elif tmax_dminus3 > tmax_dminus2 < tmax_dminus1:
                day_seq = "troughed"
            else:
                day_seq = "flat"

        for cp_str in cp_set:
            cp_utc_val = cp_to_utc(d, cp_str, TZ_NAME).astimezone(dt.UTC)
            cp_local_hour = cp_utc_val.astimezone(tz).hour

            # Causal slice: observations strictly before CP with valid temperature
            slice_df = day_obs.filter(
                (pl.col("valid") < cp_utc_val)
                & (pl.col("dq_tmp_c_int") != "missing"),
            )

            # Compute regime from CAUSAL slice only (not full-day — Fix 1)
            regime_label: str | None = None
            regime_flags: dict[str, Any] = {}
            if slice_df.height >= 3:
                wd_col_sl = "wind_dir_deg" if "wind_dir_deg" in slice_df.columns else "drct"
                regime_label, regime_flags = classify_regime(
                    slice_df.with_columns(pl.col(wd_col_sl).alias("wind_dir_deg")),
                )
            elif slice_df.height == 0:
                regime_label = "insufficient"
            else:
                regime_label = "insufficient"

            if slice_df.height == 0:
                row: dict[str, Any] = {
                    "date_local": d, "cp": cp_str,
                    "regime_label": regime_label,
                    "regime_flags": json.dumps(regime_flags),
                    "tmax_dminus1": tmax_dminus1,
                    "day_sequence_pattern": day_seq,
                    "intraday_regime_change": False,
                    "wind_dir_change_s_to_n": 0.0,
                    "precip_disruption": 0,
                    "nocturnal_plateau_flag": 0,
                    "prefrontal_warming_window": 0,
                    "nw_sector_not_foehn": 0,
                    "sst_maritime_cap": None,
                }
                for hyp in SEED_HYPOTHESES:
                    fc = hyp.feature_column
                    if fc in row or fc == "regime_label":
                        continue
                    row[fc] = None
                rows.append(row)
                continue

            feature_max_ts = slice_df["valid"].max()

            # ---- Anchor values ----
            # Use local CP hour for anchor filtering (Fix 8: UTC/local mixing)
            anchors: dict[int, dict[str, Any]] = {}
            for ah in ANCHOR_HOURS:
                if ah >= cp_local_hour:
                    anchors[ah] = {"tmp_c_int": None, "dwp_c_int": None,
                                   "sknt": None, "drct": None, "alti": None}
                else:
                    anchors[ah] = {
                        "tmp_c_int": _nearest_anchor_value(slice_df, ah, d, "tmp_c_int"),
                        "dwp_c_int": _nearest_anchor_value(slice_df, ah, d, "dwp_c_int"),
                        "sknt": _nearest_anchor_value(slice_df, ah, d, "sknt"),
                        "drct": _nearest_anchor_value(slice_df, ah, d, "drct"),
                        "alti": _nearest_anchor_value(slice_df, ah, d, "alti"),
                    }

            valid_anchors = [
                ah for ah in ANCHOR_HOURS
                if ah < cp_local_hour and anchors[ah]["tmp_c_int"] is not None
            ]
            dwp_anchors = [
                ah for ah in ANCHOR_HOURS
                if ah < cp_local_hour and anchors[ah]["dwp_c_int"] is not None
            ]
            alti_anchors = [
                ah for ah in ANCHOR_HOURS
                if ah < cp_local_hour and anchors[ah]["alti"] is not None
            ]

            # ---- Aggregate values ----
            p01i_sum = slice_df["p01i"].sum() if "p01i" in slice_df.columns else None
            mean_dw_dep = slice_df["dw_depression_c_int"].mean()

            # foehn_score from slice
            wd_col = "wind_dir_deg" if "wind_dir_deg" in slice_df.columns else "drct"
            in_nw = slice_df.filter(
                (pl.col(wd_col) >= 270) | (pl.col(wd_col) <= 45),
            )
            nw_flow_strength = in_nw["sknt"].mean() or 0.0 if in_nw.height > 0 else 0.0
            dwp_dep_slice = slice_df["dw_depression_c_int"].mean()
            foehn_score_val = (
                nw_flow_strength * dwp_dep_slice
                if dwp_dep_slice is not None else None
            )

            # ---- Feature computations ----

            # H1  slope_3h
            slope_3h: float | None = None
            if len(valid_anchors) >= 2:
                t0 = anchors[valid_anchors[0]]["tmp_c_int"]
                t1 = anchors[valid_anchors[-1]]["tmp_c_int"]
                dh = valid_anchors[-1] - valid_anchors[0]
                if t0 is not None and t1 is not None and dh > 0:
                    slope_3h = (t1 - t0) / dh

            # H2  hours_to_expected_peak — requires train-only stats; set None (recomputed in harness)
            hours_to_peak: float | None = None

            # H3  regime_label        (already available)
            # H4  dewpoint_depression
            dewpoint_depression: float | None = (
                float(mean_dw_dep) if mean_dw_dep is not None else None
            )

            # H5  tmax_dminus1        (already available)
            # H6  tmin_delta_tmax — use tmin_so_far from causal slice, not full-day tmin_d
            tmin_so_far = slice_df["tmp_c_int"].min() if slice_df.height > 0 else None
            tmin_delta_tmax: int | None = (
                tmin_so_far - tmax_dminus1
                if tmin_so_far is not None and tmax_dminus1 is not None
                else None
            )

            # H7  intraday_regime_change
            intraday_change: bool = regime_flags.get("intraday_regime_change", False)

            # H8  wind_dir_change_s_to_n
            wind_change: float = 0.0
            early_obs = slice_df.filter(pl.col("hour_local") <= 12)
            late_obs = slice_df.filter(pl.col("hour_local") >= 15)
            if early_obs.height > 0 and late_obs.height > 0:
                e_mean = _mean_drct(early_obs)
                l_mean = _mean_drct(late_obs)
                if e_mean is not None and l_mean is not None:
                    e_is_s = 135.0 <= e_mean <= 225.0
                    l_is_n = l_mean >= 315.0 or l_mean <= 45.0
                    if e_is_s and l_is_n:
                        raw = abs(l_mean - e_mean)
                        wind_change = raw if raw <= 180.0 else 360.0 - raw

            # H9  day_sequence_pattern  (already computed)
            # H10 precip_disruption
            precip_disruption: int = 0
            if p01i_sum is not None and p01i_sum > 0.01:
                precip_disruption = 1
            if _has_wxcode(slice_df, "RA"):
                precip_disruption = 1

            # H11 tmax_hour_by_regime_month — requires train-only stats; set None (recomputed in harness)
            tmax_hour_by_regime: float | None = None

            # H12 cloud_cover_suppression
            cloud_suppression: float | None = _max_cloud_cover(slice_df)

            # H13 pressure_trend_3h
            pressure_trend: float | None = None
            if len(alti_anchors) >= 2:
                a0 = anchors[alti_anchors[0]]["alti"]
                a1 = anchors[alti_anchors[-1]]["alti"]
                dh = alti_anchors[-1] - alti_anchors[0]
                if a0 is not None and a1 is not None and dh > 0:
                    # alti is in inHg; convert to hPa (1 inHg = 33.8639 hPa)
                    pressure_trend = ((a1 - a0) * 33.8639) / dh

            # H14 foehn_score
            # H15 late_warming_anomaly — requires train-only stats; set None (recomputed in harness)
            late_warming_anomaly: float | None = None

            # H16 regime_score_argmax
            regime_score_argmax: str = regime_label

            # H17 warming_rate_06_09
            warming_rate_06_09: float | None = None
            at_06 = anchors[6]["tmp_c_int"]
            at_09 = anchors[9]["tmp_c_int"]
            if at_06 is not None and at_09 is not None:
                warming_rate_06_09 = (at_09 - at_06) / 3.0

            # H18 nocturnal_plateau_flag
            nocturnal_flag: int = 0
            at_12 = anchors[12]["tmp_c_int"]
            if at_06 is not None and at_09 is not None and at_12 is not None:
                vals = [at_06, at_09, at_12]
                if max(vals) - min(vals) <= 0.5:
                    n_mean = _circular_mean_dir(slice_df)
                    if (
                        n_mean is not None
                        and (n_mean >= 315 or n_mean <= 45)
                        and cloud_suppression >= 0.75
                    ):
                        nocturnal_flag = 1

            # H19 sst_maritime_cap  — BLOCKED, always null
            # H20 dewpoint_collapse_rate_3h
            dwp_rate: float | None = None
            if len(dwp_anchors) >= 2:
                d0 = anchors[dwp_anchors[0]]["dwp_c_int"]
                d1 = anchors[dwp_anchors[-1]]["dwp_c_int"]
                dh = dwp_anchors[-1] - dwp_anchors[0]
                if d0 is not None and d1 is not None and dh > 0:
                    dwp_rate = (d1 - d0) / dh

            # H21 prefrontal_warming_window
            prefrontal: int = 0
            if len(alti_anchors) >= 2:
                a0 = anchors[alti_anchors[0]]["alti"]
                a1 = anchors[alti_anchors[-1]]["alti"]
                if (
                    a0 is not None
                    and a1 is not None
                    and a1 < a0
                    and (a0 - a1) * 33.8639 >= 0.5
                    and p01i_sum is not None
                    and p01i_sum == 0.0
                ):
                    n_mean = _circular_mean_dir(slice_df)
                    if n_mean is not None and (n_mean >= 315 or n_mean <= 45):
                        prefrontal = 1

            # H22 nw_sector_not_foehn
            nw_not_foehn: int = 0
            if regime_label == "strong_nw_foehn":
                n_mean = _circular_mean_dir(slice_df)
                if n_mean is not None and 280 <= n_mean <= 310:
                    nw_not_foehn = 1

            # H23 cloud_base_transparency
            cloud_transparency: float | None = _cloud_base_transparency(slice_df)

            # ---- Assemble row ----
            row = {
                "date_local": d,
                "cp": cp_str,
                "regime_label": regime_label,
                "regime_flags": json.dumps(regime_flags),
                "slope_3h": slope_3h,
                "hours_to_expected_peak": hours_to_peak,
                "dewpoint_depression": dewpoint_depression,
                "tmax_dminus1": tmax_dminus1,
                "tmin_delta_tmax": tmin_delta_tmax,
                "intraday_regime_change": intraday_change,
                "wind_dir_change_s_to_n": wind_change,
                "day_sequence_pattern": day_seq,
                "precip_disruption": precip_disruption,
                "tmax_hour_by_regime_month": tmax_hour_by_regime,
                "cloud_cover_suppression": cloud_suppression,
                "pressure_trend_3h": pressure_trend,
                "foehn_score": foehn_score_val,
                "late_warming_anomaly": late_warming_anomaly,
                "regime_score_argmax": regime_score_argmax,
                "warming_rate_06_09": warming_rate_06_09,
                "nocturnal_plateau_flag": nocturnal_flag,
                "sst_maritime_cap": None,
                "dewpoint_collapse_rate_3h": dwp_rate,
                "prefrontal_warming_window": prefrontal,
                "nw_sector_not_foehn": nw_not_foehn,
                "cloud_base_transparency": cloud_transparency,
            }

            require_causal(
                feature_max_ts=feature_max_ts,
                cp_utc=cp_utc_val,
                label=f"features for {d} {cp_str}",
            )

            rows.append(row)

    return pl.DataFrame(rows, strict=False)


# ---------------------------------------------------------------------------
# Coverage manifest
# ---------------------------------------------------------------------------

def build_coverage_manifest(
    features: pl.DataFrame,
    hypotheses: list | None = None,
) -> dict[str, Any]:
    """Build a JSON-serialisable coverage manifest for all feature columns.

    Args:
        features: Output of :func:`build_features`.
        hypotheses: List of :class:`~solarstorm.eda._hypotheses.Hypothesis`
            instances (defaults to ``SEED_HYPOTHESES``).

    Returns:
        Dict keyed by ``feature_column`` with status, reason (if BLOCKED),
        non_null_rate, n_total, n_non_null.
    """
    if hypotheses is None:
        hypotheses = SEED_HYPOTHESES  # type: ignore[assignment]

    manifest: dict[str, Any] = {}
    n_total = features.height

    for hyp in hypotheses:
        fc = hyp.feature_column
        if fc not in features.columns:
            manifest[fc] = {
                "status": "MISSING",
                "non_null_rate": 0.0,
                "n_total": n_total,
                "n_non_null": 0,
            }
            continue

        n_non_null = features[fc].null_count()
        n_non = n_total - n_non_null
        rate = round(n_non / n_total, 4) if n_total > 0 else 0.0

        if fc in BLOCKED_FEATURES:
            manifest[fc] = {
                "status": "BLOCKED",
                "reason": BLOCKED_FEATURES[fc],
                "non_null_rate": rate,
                "n_total": n_total,
                "n_non_null": n_non,
            }
        else:
            manifest[fc] = {
                "status": "computable",
                "non_null_rate": rate,
                "n_total": n_total,
                "n_non_null": n_non,
            }

    return manifest
