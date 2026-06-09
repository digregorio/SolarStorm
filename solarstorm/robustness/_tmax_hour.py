"""Month/regime Tmax-hour stratification for Onda 4."""
from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

import polars as pl

from solarstorm._config import TZ_NAME
from solarstorm.data._calendar import cp_to_utc


def _empty_tmax_hour_table() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "hypothesis_id": pl.Utf8,
            "feature_column": pl.Utf8,
            "cp": pl.Utf8,
            "regime": pl.Utf8,
            "month": pl.Int64,
            "tmax_hour_bucket": pl.Utf8,
            "n_days": pl.Int64,
            "tmax_seen_share": pl.Float64,
            "late_tmax_baseline_name": pl.Utf8,
            "late_tmax_baseline_threshold": pl.Float64,
            "late_tmax_event_share": pl.Float64,
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


def _hour_bucket(hour: int | None) -> str:
    if hour is None:
        return "unknown"
    if hour < 12:
        return "morning_before_12"
    if hour <= 14:
        return "midday_12_14"
    if hour <= 18:
        return "afternoon_15_18"
    return "evening_after_18"


def _tmax_seen(row: dict, cp: str) -> bool:
    date_local = row.get("date_local")
    if date_local is None:
        return False
    if row.get("tmax_hour_utc") is not None:
        value = row["tmax_hour_utc"]
        if isinstance(value, dt.datetime):
            tmax_utc = value if value.tzinfo else value.replace(tzinfo=dt.UTC)
            return tmax_utc.astimezone(dt.UTC) <= cp_to_utc(date_local, cp, TZ_NAME)
    hour = row.get("tmax_hour")
    if hour is None:
        return False
    local = dt.datetime.combine(date_local, dt.time(int(hour)), tzinfo=dt.timezone(dt.timedelta(hours=13)))
    return local.astimezone(dt.UTC) <= cp_to_utc(date_local, cp, TZ_NAME)


def _q90_hour(hours: list[int]) -> float | None:
    if not hours:
        return None
    sorted_hours = sorted(hours)
    q90_index = min(len(sorted_hours) - 1, int(0.9 * (len(sorted_hours) - 1)))
    return float(sorted_hours[q90_index])


def tmax_hour_stratification(
    features: pl.DataFrame,
    labels: pl.DataFrame,
    validated_entries: Sequence[dict],
    *,
    min_days: int = 30,
) -> pl.DataFrame:
    """Aggregate validated features by regime, month, and observed Tmax hour."""
    label_cols = ["date_local", "tmax_hour"]
    if "tmax_hour_utc" in labels.columns:
        label_cols.append("tmax_hour_utc")
    label_view = labels.select([c for c in label_cols if c in labels.columns])

    rows: list[dict] = []
    for entry in _entries(validated_entries):
        feature_column = entry["feature_column"]
        cp = entry["cp"]
        if feature_column not in features.columns:
            continue
        feature_cols = ["date_local", "cp", "regime_label"]
        if feature_column not in feature_cols:
            feature_cols.append(feature_column)
        joined = (
            features.filter((pl.col("cp") == cp) & pl.col(feature_column).is_not_null())
            .select(feature_cols)
            .join(label_view, on="date_local", how="inner")
        )
        norm_hours: dict[tuple[str, int], list[int]] = {}
        groups: dict[tuple[str, int, str], list[tuple[bool, int | None]]] = {}
        for row in joined.iter_rows(named=True):
            date_local = row["date_local"]
            regime = row.get("regime_label") or "unknown"
            hour = row.get("tmax_hour")
            hour_int = int(hour) if hour is not None else None
            if hour_int is not None:
                norm_hours.setdefault((str(regime), int(date_local.month)), []).append(hour_int)
            key = (str(regime), int(date_local.month), _hour_bucket(hour_int))
            groups.setdefault(key, []).append((_tmax_seen(row, cp), hour_int))

        thresholds = {key: _q90_hour(hours) for key, hours in norm_hours.items()}
        for (regime, month, bucket), values in sorted(groups.items()):
            n_days = len(values)
            seen_share = sum(1 for seen, _hour in values if seen) / n_days if n_days else 0.0
            hours = sorted(hour for _seen, hour in values if hour is not None)
            threshold = thresholds.get((regime, month))
            if hours and threshold is not None:
                event_share = (
                    sum(1 for hour in hours if float(hour) > threshold) / len(hours)
                )
            else:
                event_share = None
            rows.append(
                {
                    **entry,
                    "regime": regime,
                    "month": month,
                    "tmax_hour_bucket": bucket,
                    "n_days": n_days,
                    "tmax_seen_share": seen_share,
                    "late_tmax_baseline_name": "month_regime_q90",
                    "late_tmax_baseline_threshold": threshold,
                    "late_tmax_event_share": event_share,
                    "passes": n_days >= min_days,
                }
            )

    return pl.DataFrame(rows) if rows else _empty_tmax_hour_table()


def detect_fixed_cp_artifact(tmax_hour_table: pl.DataFrame) -> bool:
    """True if all passing strata are already-known Tmax strata."""
    if tmax_hour_table.height == 0:
        return True
    passing = tmax_hour_table.filter(pl.col("passes").fill_null(False))
    if passing.height == 0:
        return True
    return passing.filter(pl.col("tmax_seen_share").fill_null(1.0) < 0.95).height == 0


def has_late_tmax_risk_baseline(tmax_hour_table: pl.DataFrame) -> bool:
    """Return True when R7 produced a non-empty late-Tmax timing baseline."""
    required = {"late_tmax_baseline_name", "late_tmax_baseline_threshold"}
    if tmax_hour_table.height == 0 or not required.issubset(set(tmax_hour_table.columns)):
        return False
    baseline_rows = tmax_hour_table.filter(
        pl.col("late_tmax_baseline_name").is_not_null()
        & pl.col("late_tmax_baseline_threshold").is_not_null()
    )
    return baseline_rows.height > 0
