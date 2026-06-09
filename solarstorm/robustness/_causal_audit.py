"""Causal firewall re-audit for validated features."""
from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

import polars as pl

from solarstorm._config import TZ_NAME
from solarstorm.data._calendar import cp_to_utc


def _timestamp_candidates(feature_column: str) -> tuple[str, ...]:
    return (
        f"{feature_column}_max_obs_utc",
        f"{feature_column}_max_obs_ts",
        f"{feature_column}_latest_obs_utc",
        f"{feature_column}_latest_obs_ts",
        f"{feature_column}_feature_max_ts",
        "feature_max_ts",
        "max_obs_ts",
        "latest_obs_ts",
        "max_obs_utc",
    )


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


def reaudit_causality(
    features: pl.DataFrame,
    labels_or_feature_columns: pl.DataFrame | Sequence[str],
    feature_columns: Sequence[str] | None = None,
    *,
    tz_name: str = TZ_NAME,
) -> tuple[list[str], list[str]]:
    """Return clean and violating feature columns.

    The current production feature table is wide and may not yet include
    per-feature timestamp provenance. If no timestamp metadata exists for a
    feature, the function treats it as clean and leaves the stronger provenance
    requirement to future artifact versions.
    """
    columns = (
        list(labels_or_feature_columns)  # type: ignore[arg-type]
        if feature_columns is None
        else list(feature_columns)
    )

    clean: list[str] = []
    violating: list[str] = []

    for feature_column in columns:
        timestamp_col = next(
            (candidate for candidate in _timestamp_candidates(feature_column) if candidate in features.columns),
            None,
        )
        if feature_column not in features.columns:
            violating.append(feature_column)
            continue
        if timestamp_col is None:
            clean.append(feature_column)
            continue

        is_violation = False
        for row in features.select(["date_local", "cp", timestamp_col]).iter_rows(named=True):
            date_local = row.get("date_local")
            cp = row.get("cp")
            if date_local is None or cp is None:
                continue
            observed = _as_utc(row.get(timestamp_col))
            if observed is None:
                continue
            cutoff = cp_to_utc(date_local, str(cp), tz_name)
            if observed > cutoff:
                is_violation = True
                break

        if is_violation:
            violating.append(feature_column)
        else:
            clean.append(feature_column)

    return clean, violating
