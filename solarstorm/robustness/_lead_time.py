"""Anti-nowcast lead-time analysis for Onda 4."""
from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

import polars as pl

from solarstorm._config import TZ_NAME
from solarstorm.data._calendar import cp_to_utc


def _empty_lead_time_table() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "hypothesis_id": pl.Utf8,
            "feature_column": pl.Utf8,
            "cp": pl.Utf8,
            "lead_time_bucket": pl.Utf8,
            "tmax_already_seen": pl.Boolean,
            "n_days": pl.Int64,
            "passes": pl.Boolean,
        }
    )


def _entries(validated_entries: Sequence[dict]) -> list[dict]:
    rows = []
    seen: set[tuple[str, str, str]] = set()
    for entry in validated_entries:
        if entry.get("regime", "all") != "all":
            continue
        feature_column = entry.get("feature_column")
        cp = entry.get("cp")
        if not feature_column or not cp:
            continue
        key = (str(entry.get("id") or feature_column), str(feature_column), str(cp))
        if key in seen:
            continue
        seen.add(key)
        rows.append({"hypothesis_id": key[0], "feature_column": key[1], "cp": key[2]})
    return rows


def _as_utc(value: object) -> dt.datetime | None:
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=dt.UTC)
        return value.astimezone(dt.UTC)
    if isinstance(value, str):
        try:
            parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.UTC)
        return parsed.astimezone(dt.UTC)
    return None


def _bucket(hours: float) -> str:
    if hours <= 0:
        return "already_seen"
    if hours <= 2:
        return "0_2h"
    if hours <= 4:
        return "2_4h"
    return "4h_plus"


def _tmax_time_utc(row: dict) -> dt.datetime | None:
    direct = _as_utc(row.get("tmax_hour_utc"))
    if direct is not None:
        return direct
    date_local = row.get("date_local")
    tmax_hour = row.get("tmax_hour")
    if date_local is None or tmax_hour is None:
        return None
    local = dt.datetime.combine(date_local, dt.time(int(tmax_hour)), tzinfo=dt.timezone(dt.timedelta(hours=13)))
    return local.astimezone(dt.UTC)


def lead_time_analysis(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    validated_entries: Sequence[dict],
    *,
    tz_name: str = TZ_NAME,
    min_days: int = 1,
) -> pl.DataFrame:
    """Summarize whether validated CPs are predictive before Tmax is known."""
    rows: list[dict] = []
    label_cols = ["date_local", "tmax_hour"]
    if "tmax_hour_utc" in labels.columns:
        label_cols.append("tmax_hour_utc")
    label_view = labels.select([c for c in label_cols if c in labels.columns])

    for entry in _entries(validated_entries):
        feature_column = entry["feature_column"]
        cp = entry["cp"]
        if feature_column not in features.columns:
            continue
        joined = (
            features.filter((pl.col("cp") == cp) & pl.col(feature_column).is_not_null())
            .select(["date_local", "cp", feature_column])
            .join(label_view, on="date_local", how="inner")
        )
        bucket_counts: dict[tuple[str, bool], int] = {}
        for row in joined.iter_rows(named=True):
            tmax_utc = _tmax_time_utc(row)
            if tmax_utc is None:
                continue
            cutoff = cp_to_utc(row["date_local"], cp, tz_name)
            lead_hours = (tmax_utc - cutoff).total_seconds() / 3600.0
            name = _bucket(lead_hours)
            already_seen = lead_hours <= 0
            bucket_counts[(name, already_seen)] = bucket_counts.get((name, already_seen), 0) + 1

        for (bucket_name, already_seen), n_days in sorted(bucket_counts.items()):
            rows.append(
                {
                    **entry,
                    "lead_time_bucket": bucket_name,
                    "tmax_already_seen": already_seen,
                    "n_days": n_days,
                    "passes": n_days >= min_days and not already_seen,
                }
            )

    return pl.DataFrame(rows) if rows else _empty_lead_time_table()


def detect_nowcast_only(lead_time_table: pl.DataFrame) -> bool:
    """True when no passing evidence exists before Tmax was effectively known."""
    if lead_time_table.height == 0:
        return True
    passing = lead_time_table.filter(pl.col("passes").fill_null(False))
    if passing.height == 0:
        return True
    return passing.filter(~pl.col("tmax_already_seen").fill_null(True)).height == 0
