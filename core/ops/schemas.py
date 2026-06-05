"""Shadow Ops schemas for forecast records (Phase 5.1).

Defines the required fields and validation for shadow forecast JSONL records.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any


# Required fields for a valid shadow forecast record.
# These must be present in every JSONL line emitted by the shadow runner.
REQUIRED_FORECAST_FIELDS: tuple[str, ...] = (
    "run_id",
    "date_local",
    "cp_utc",
    "prob_dist",
    "model_version",
    "routing",
)

# Minimum required routing fields for a record to be considered operationally valid.
MINIMUM_ROUTING_FIELDS: tuple[str, ...] = (
    "served_model",
)


@dataclass(frozen=True)
class ShadowForecastRecord:
    """Validated shadow forecast record.

    Attributes:
        run_id: Unique identifier for this forecast run.
        date_local: Local date string (YYYY-MM-DD).
        cp_utc: Checkpoint UTC timestamp (ISO format).
        prob_dist: Probability distribution dict {bracket_int: probability}.
        model_version: Version string of the model that produced the forecast.
        routing: Routing telemetry dict (model_route, served_model, fallback, etc.).
        p50_int: Median forecast value (integer bracket).
        ic80_low_int: Lower bound of 80% prediction interval.
        ic80_high_int: Upper bound of 80% prediction interval.
        support_k: Support K values used for prediction.
        feature_max_ts_utc: Latest observation timestamp used by CP features.
        feature_gap_to_cp_min: Minutes between the CP and latest feature timestamp.
        feature_staleness_min: Backward-compatible alias for feature_gap_to_cp_min.
        k_cp_available: Whether pre-CP temperature max was available.
    """

    run_id: str
    date_local: str
    cp_utc: str
    prob_dist: dict[str, float]
    model_version: str
    routing: dict[str, Any]
    p50_int: int | None = None
    ic80_low_int: int | None = None
    ic80_high_int: int | None = None
    support_k: list[int] | None = None
    feature_max_ts_utc: str | None = None
    feature_gap_to_cp_min: int | None = None
    feature_staleness_min: int | None = None
    k_cp_available: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ShadowForecastRecord:
        """Construct from a raw dict, extracting known fields."""
        return cls(
            run_id=str(data["run_id"]),
            date_local=str(data["date_local"]),
            cp_utc=str(data["cp_utc"]),
            prob_dist=data["prob_dist"],
            model_version=str(data["model_version"]),
            routing=data["routing"],
            p50_int=data.get("p50_int"),
            ic80_low_int=data.get("ic80_low_int"),
            ic80_high_int=data.get("ic80_high_int"),
            support_k=data.get("support_k"),
            feature_max_ts_utc=data.get("feature_max_ts_utc"),
            feature_gap_to_cp_min=data.get("feature_gap_to_cp_min"),
            feature_staleness_min=data.get("feature_staleness_min"),
            k_cp_available=data.get("k_cp_available"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dict."""
        return {
            "run_id": self.run_id,
            "date_local": self.date_local,
            "cp_utc": self.cp_utc,
            "prob_dist": self.prob_dist,
            "model_version": self.model_version,
            "routing": self.routing,
            "p50_int": self.p50_int,
            "ic80_low_int": self.ic80_low_int,
            "ic80_high_int": self.ic80_high_int,
            "support_k": self.support_k,
            "feature_max_ts_utc": self.feature_max_ts_utc,
            "feature_gap_to_cp_min": self.feature_gap_to_cp_min,
            "feature_staleness_min": self.feature_staleness_min,
            "k_cp_available": self.k_cp_available,
        }


class ShadowSchemaError(Exception):
    """Raised when a forecast record fails schema validation."""


def validate_record(record: dict[str, Any]) -> ShadowForecastRecord:
    """Validate a raw forecast dict against the schema.

    Args:
        record: Raw forecast dict (parsed from JSON).

    Returns:
        Validated ShadowForecastRecord.

    Raises:
        ShadowSchemaError: If required fields are missing or invalid.
    """
    missing = [f for f in REQUIRED_FORECAST_FIELDS if f not in record]
    if missing:
        raise ShadowSchemaError(f"Missing required fields: {missing}")

    # --- prob_dist validation ---
    prob_dist = record["prob_dist"]
    if not isinstance(prob_dist, dict):
        raise ShadowSchemaError("prob_dist must be a dict")
    if not prob_dist:
        raise ShadowSchemaError("prob_dist must not be empty")

    total = 0.0
    for k, v in prob_dist.items():
        # Keys must be integer-parseable.
        try:
            int(k)
        except (ValueError, TypeError):
            raise ShadowSchemaError(f"prob_dist key '{k}' is not an integer") from None
        # Values must be finite and non-negative.
        if not isinstance(v, (int, float)):
            raise ShadowSchemaError(f"prob_dist value for key '{k}' is not numeric")
        if not math.isfinite(v):
            raise ShadowSchemaError(f"prob_dist value for key '{k}' is not finite")
        if v < 0:
            raise ShadowSchemaError(f"prob_dist value for key '{k}' is negative")
        total += v

    # Sum should be approximately 1.0 (within 0.01 tolerance).
    if abs(total - 1.0) > 0.01:
        raise ShadowSchemaError(
            f"prob_dist sum is {total:.4f}, expected ~1.0 (tolerance 0.01)"
        )

    # --- routing validation ---
    routing = record["routing"]
    if not isinstance(routing, dict):
        raise ShadowSchemaError("routing must be a dict")
    for f in MINIMUM_ROUTING_FIELDS:
        if f not in routing:
            raise ShadowSchemaError(f"routing missing minimum field: '{f}'")

    # --- date_local validation (must be ISO date) ---
    date_local_str = str(record["date_local"])
    try:
        # Accept both date-only and datetime ISO formats.
        if "T" in date_local_str:
            datetime.fromisoformat(date_local_str)
        else:
            from datetime import date as date_type
            date_type.fromisoformat(date_local_str)
    except ValueError:
        raise ShadowSchemaError(
            f"date_local '{date_local_str}' is not a valid ISO date"
        ) from None

    # --- cp_utc validation (must be parseable ISO datetime) ---
    cp_utc_str = str(record["cp_utc"])
    try:
        datetime.fromisoformat(cp_utc_str)
    except ValueError:
        raise ShadowSchemaError(
            f"cp_utc '{cp_utc_str}' is not a valid ISO datetime"
        ) from None

    return ShadowForecastRecord.from_dict(record)


__all__ = [
    "REQUIRED_FORECAST_FIELDS",
    "ShadowForecastRecord",
    "ShadowSchemaError",
    "validate_record",
]
