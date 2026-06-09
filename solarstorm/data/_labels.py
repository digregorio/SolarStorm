"""Tmax labels: daily aggregation, CP-level k_cp, remaining_warming, settlement."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import polars as pl

from solarstorm._config import CP_SET_UTC, TZ_NAME
from solarstorm.data._calendar import cp_to_utc


@dataclass
class DayCompleteParams:
    min_obs: int = 40
    max_gap_minutes: int = 120
    min_quartile_coverage: int = 1


def risco_de_flip(tmax_dec: float) -> float:
    """Boundary distance: how far *tmax_dec* is from the nearest .5 degC rounding boundary.

    0.5 = at integer center (far from any boundary -- safe, wide margin).
    0.0 = exactly on a .5 boundary (a micro-variation flips the bracket).

    This is the *inverse* of flip risk: low boundary distance = high flip risk.
    """
    return round(0.5 - abs(tmax_dec - round(tmax_dec)), 10)


def remaining_warming(*, tmax: int, k_cp: int) -> int:
    """How much warming remains after the checkpoint. Core target from Onda 3."""
    return tmax - k_cp


def _quartile(hour: int) -> int:
    """Map a local hour to a quartile block (0-3)."""
    if hour < 6:
        return 0
    if hour < 12:
        return 1
    if hour < 18:
        return 2
    return 3


def build_tmax_labels(
    obs: pl.DataFrame,
    params: DayCompleteParams,
) -> pl.DataFrame:
    """Aggregate intraday observations into per-local-date Tmax labels.

    Expects obs with columns: valid (datetime[UTC]), tmp_c_int, dq_tmp_c_int,
    tmpf, metar.

    Returns one row per local date with tmax_int, tmax_dec, tmax_hour,
    day_complete, and per-CP k_cp columns.
    """
    obs = obs.with_columns(
        pl.col("valid").dt.convert_time_zone(TZ_NAME).alias("ts_local"),
    ).with_columns(
        pl.col("ts_local").dt.date().alias("date_local"),
        pl.col("ts_local").dt.hour().alias("hour_local"),
    )

    # Settlement target: only METAR-text temps (dq == "ok"), not imputed from tmpf
    valid = obs.filter(pl.col("dq_tmp_c_int") == "ok")

    # --- Daily aggregates (from canonical Tmax row) ---
    # Canonical row: max tmp_c_int, tiebreak by earliest ts_local
    canonical = (
        valid.sort(["tmp_c_int", "ts_local"], descending=[True, False])
        .head(1)
        .select(
            pl.col("date_local"),
            pl.col("tmp_c_int").alias("tmax_int"),
            pl.col("ts_local").alias("tmax_ts"),
            pl.col("hour_local").alias("tmax_hour_local"),
        )
    )
    # Tmax decimal from the canonical row's tmpf (P1: internal decimal)
    tmpf_canonical = (
        valid.sort(["tmp_c_int", "ts_local"], descending=[True, False])
        .head(1)
        .select(pl.col("date_local"), pl.col("tmpf").alias("tmpf_max_canonical"))
    )
    canonical = canonical.join(tmpf_canonical, on="date_local", how="left")

    # Daily stats
    daily = valid.group_by("date_local").agg([
        pl.col("tmp_c_int").min().alias("tmin_int"),
        pl.col("tmpf").min().alias("tmpf_min"),
        pl.col("ts_local").count().alias("n_obs"),
        pl.col("ts_local").sort().diff().dt.total_minutes().max().alias("max_gap_min"),
        pl.col("hour_local").min().alias("first_hour_local"),
        pl.col("hour_local").max().alias("last_hour_local"),
        # Count of imputed temps used in this day (for provenance)
        (pl.col("dq_tmp_c_int") == "imputed").sum().alias("n_imputed"),
    ])

    # Join canonical Tmax onto daily
    daily = daily.join(canonical, on="date_local", how="left")

    # Tmax decimal from canonical row's tmpf
    daily = daily.with_columns(
        ((pl.col("tmpf_max_canonical") - 32.0) * 5.0 / 9.0).alias("tmax_dec"),
        ((pl.col("tmpf_min") - 32.0) * 5.0 / 9.0).alias("tmin_dec"),
    )

    # tmax_source provenance
    daily = daily.with_columns(
        pl.lit("ok").alias("tmax_source"),
    )

    # --- day_complete gate with quartile coverage + edge gaps ---
    daily = daily.with_columns(
        # Edge gap start: minutes from local midnight to first obs
        (
            (pl.col("first_hour_local").cast(pl.Float64) * 60.0)
            .alias("edge_gap_start_min")
        ),
        # Edge gap end: minutes from last obs to local midnight (next day)
        (
            ((23.0 - pl.col("last_hour_local").cast(pl.Float64)) * 60.0 + 60.0)
            .alias("edge_gap_end_min")
        ),
    )

    # Quartile coverage (per-date) — compute from the valid obs
    quartile_coverage = (
        valid.with_columns(
            pl.col("hour_local").map_elements(_quartile, return_dtype=pl.Int32).alias("quartile")
        )
        .group_by("date_local")
        .agg(pl.col("quartile").n_unique().alias("quartile_count"))
    )
    daily = daily.join(quartile_coverage, on="date_local", how="left")

    daily = daily.with_columns(
        (
            (pl.col("n_obs") >= params.min_obs)
            & (pl.col("max_gap_min").fill_null(0) <= params.max_gap_minutes)
            & (pl.col("edge_gap_start_min") <= params.max_gap_minutes)
            & (pl.col("edge_gap_end_min") <= params.max_gap_minutes)
            & (pl.col("quartile_count").fill_null(0) >= params.min_quartile_coverage)
        ).alias("day_complete")
    )

    # --- Per-CP k_cp ---
    # Use only METAR-text temps (dq=="ok") for k_cp consistency
    obs_ok = obs.filter(pl.col("dq_tmp_c_int") == "ok")
    for cp_str in CP_SET_UTC:
        col_name = f"k_cp__cp_{cp_str.replace(':', '')}"
        kcp_rows = []
        for row in daily.iter_rows(named=True):
            d = row["date_local"]
            cp = cp_to_utc(d, cp_str, TZ_NAME).astimezone(dt.UTC)
            day_obs = obs_ok.filter(
                (pl.col("date_local") == d)
                & (pl.col("valid") < cp)
            )
            if day_obs.height > 0:
                kcp_rows.append({"date_local": d, col_name: int(day_obs["tmp_c_int"].max())})
            else:
                kcp_rows.append({"date_local": d, col_name: None})

        kcp_map = pl.DataFrame(
            kcp_rows,
            schema={"date_local": pl.Date, col_name: pl.Int64},
        )
        daily = daily.join(kcp_map, on="date_local", how="left")

    # --- tmax_hour: local hour-of-day integer of the canonical max ---
    daily = daily.with_columns(
        pl.col("tmax_hour_local").alias("tmax_hour")
    )

    # --- Tmax hour in UTC ---
    daily = daily.with_columns(
        pl.when(pl.col("tmax_hour_local").is_not_null())
          .then(
              pl.col("date_local").cast(pl.Utf8)
              + " " + pl.col("tmax_hour_local").cast(pl.Utf8).str.zfill(2)
              + ":00:00"
          )
          .otherwise(None)
          .alias("tmax_hour_str")
    )
    daily = daily.with_columns(
        pl.col("tmax_hour_str").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S")
        .dt.replace_time_zone(TZ_NAME)
        .dt.convert_time_zone("UTC")
        .alias("tmax_hour_utc")
    )

    # --- 24h scan: flag Tmax at atypical hours (P2, audit #9) ---
    daily = daily.with_columns(
        ((pl.col("tmax_hour_local") < 6) | (pl.col("tmax_hour_local") > 18))
        .alias("tmax_atypical_hour")
    )

    # --- risco_de_flip (P1+P4) ---
    daily = daily.with_columns(
        pl.col("tmax_dec").map_elements(risco_de_flip, return_dtype=pl.Float64).alias("risco_de_flip")
    )

    # Drop internal-only columns
    daily = daily.drop(["first_hour_local", "last_hour_local", "edge_gap_start_min",
                         "edge_gap_end_min", "quartile_count", "tmpf_max_canonical"],
                        strict=False)

    return daily
