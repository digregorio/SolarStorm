# Open-Meteo Causal Feature Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an experiment-only Open-Meteo feature pipeline and pilot model comparison without mutating the local-data baseline.

**Architecture:** Extend `solarstorm.open_meteo` with source eligibility, raw-response parsing, Previous Runs feature extraction, artifact writing, and a pilot comparison module. The first feature-generating source is `previous_runs_gfs_temperature`; Single Runs support remains represented in the decision layer but blocked until the endpoint contract succeeds. The Onda 3 pilot joins Open-Meteo features to local features on `(date_local, cp)` and compares local-only versus Open-Meteo-augmented candidates on identical narrowed folds.

**Tech Stack:** Python 3.12, Polars, NumPy ridge helpers already in `solarstorm.onda3`, Typer, pytest, Ruff.

---

## Guardrails

- All outputs must include `production_status = EXPERIMENT_ONLY`.
- Do not overwrite `data/features.parquet`.
- Do not train or promote a production model.
- Do not generate causal predictor rows from `historical_weather`, `historical_forecast`, or `forecast_api_best_match`.
- Do not unlock Single Runs feature generation until a decision row explicitly permits `single_runs_ecmwf_ifs_hres`.
- Unit tests must not hit the network.
- Live smoke commands are optional and must not be required for test success.

## File Structure

- Create `solarstorm/open_meteo/_features.py`
  - Source eligibility checks, Open-Meteo hourly payload parser, Previous Runs feature extraction, feature-table builder, feature artifacts, and report renderer.
- Create `solarstorm/open_meteo/_pilot.py`
  - Join local and Open-Meteo features, run same-row local-only versus augmented Onda 3F-style pooled ridge comparison, write pilot artifacts.
- Modify `solarstorm/open_meteo/__init__.py`
  - Export feature and pilot APIs.
- Modify `solarstorm/__main__.py`
  - Add `open-meteo-build-features` and `onda3-open-meteo-pilot` commands.
- Create `tests/test_open_meteo_features.py`
  - TDD coverage for eligibility, blockers, feature extraction, duplicate rejection, artifacts, and no local feature overwrite.
- Create `tests/test_open_meteo_pilot.py`
  - TDD coverage for covered-row joins and fair same-row model comparison.
- Create `tests/test_open_meteo_feature_cli.py`
  - CLI smoke tests using fixture payloads.
- Generate `reports/open-meteo-features/`
  - Experiment-only feature build artifacts.
- Generate `reports/onda3-open-meteo-pilot/`
  - Experiment-only pilot artifacts.
- Modify `ROADMAP.md` and `CHANGELOG.md`
  - Record the integration as experiment-only and explicitly non-production.

---

### Task 1: Source Eligibility Gate for Feature Generation

**Files:**
- Create: `tests/test_open_meteo_features.py`
- Create: `solarstorm/open_meteo/_features.py`
- Modify: `solarstorm/open_meteo/__init__.py`

- [ ] **Step 1: Write failing eligibility tests**

Create `tests/test_open_meteo_features.py`:

```python
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
import pytest

from solarstorm.open_meteo import (
    PRODUCTION_STATUS,
    build_decision_update,
    build_feature_source_eligibility,
    build_source_registry_frame,
    ensure_source_allowed_for_features,
)


def _decision_with_previous_runs_success() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "source_id": "previous_runs_gfs_temperature",
                "endpoint": "previous_runs",
                "model": "gfs_seamless",
                "causal_class": "fixed_lead_forecast",
                "n_probes": 1,
                "n_success": 1,
                "n_success_years": 1,
                "has_run_metadata": False,
                "has_lead_metadata": False,
                "success_pct": 100.0,
                "decision_status": "OPEN_METEO_PREVIOUS_RUNS_READY_FOR_LEAD_AUDIT",
                "pilot_scope_note": "fixed_lead_skill_audit_only",
                "production_status": PRODUCTION_STATUS,
            },
            {
                "source_id": "historical_weather_era5",
                "endpoint": "historical_weather",
                "model": "era5",
                "causal_class": "reanalysis_not_forecast",
                "n_probes": 1,
                "n_success": 1,
                "n_success_years": 1,
                "has_run_metadata": False,
                "has_lead_metadata": False,
                "success_pct": 100.0,
                "decision_status": "OPEN_METEO_BLOCKED_BY_CAUSALITY_METADATA",
                "pilot_scope_note": "diagnostic_only_reanalysis",
                "production_status": PRODUCTION_STATUS,
            },
            {
                "source_id": "historical_forecast_best_match",
                "endpoint": "historical_forecast",
                "model": "best_match",
                "causal_class": "seamless_historical_forecast",
                "n_probes": 1,
                "n_success": 1,
                "n_success_years": 1,
                "has_run_metadata": False,
                "has_lead_metadata": False,
                "success_pct": 100.0,
                "decision_status": "OPEN_METEO_HISTORICAL_FORECAST_AUDIT_ONLY",
                "pilot_scope_note": "requires_run_metadata_before_causal_use",
                "production_status": PRODUCTION_STATUS,
            },
            {
                "source_id": "single_runs_ecmwf_ifs_hres",
                "endpoint": "single_runs",
                "model": "ecmwf_ifs025",
                "causal_class": "forecast_snapshot",
                "n_probes": 1,
                "n_success": 0,
                "n_success_years": 0,
                "has_run_metadata": True,
                "has_lead_metadata": True,
                "success_pct": 0.0,
                "decision_status": "OPEN_METEO_BLOCKED_BY_AVAILABILITY",
                "pilot_scope_note": "no_successful_probe",
                "production_status": PRODUCTION_STATUS,
            },
        ]
    )


def test_feature_source_eligibility_allows_previous_runs_only_after_success():
    eligibility = build_feature_source_eligibility(_decision_with_previous_runs_success())

    by_id = {row["source_id"]: row for row in eligibility.iter_rows(named=True)}

    assert by_id["previous_runs_gfs_temperature"]["feature_generation_allowed"] is True
    assert by_id["previous_runs_gfs_temperature"]["feature_generation_reason"] == (
        "fixed_lead_forecast_pilot_allowed"
    )
    assert by_id["historical_weather_era5"]["feature_generation_allowed"] is False
    assert by_id["historical_weather_era5"]["feature_generation_reason"] == (
        "reanalysis_blocked_as_predictor"
    )
    assert by_id["historical_forecast_best_match"]["feature_generation_allowed"] is False
    assert by_id["historical_forecast_best_match"]["feature_generation_reason"] == (
        "seamless_historical_forecast_lacks_run_metadata"
    )
    assert by_id["single_runs_ecmwf_ifs_hres"]["feature_generation_allowed"] is False
    assert by_id["single_runs_ecmwf_ifs_hres"]["feature_generation_reason"] == (
        "forecast_snapshot_not_available"
    )
    assert set(eligibility["production_status"].to_list()) == {PRODUCTION_STATUS}


def test_feature_source_eligibility_blocks_previous_runs_without_success():
    availability = pl.DataFrame(
        [
            {
                "source_id": "previous_runs_gfs_temperature",
                "endpoint": "previous_runs",
                "model": "gfs_seamless",
                "causal_class": "fixed_lead_forecast",
                "n_probes": 1,
                "n_success": 0,
                "n_success_years": 0,
                "has_run_metadata": False,
                "has_lead_metadata": False,
                "success_pct": 0.0,
                "production_status": PRODUCTION_STATUS,
            }
        ]
    )
    decision = build_decision_update(availability)

    eligibility = build_feature_source_eligibility(decision)

    row = eligibility.row(0, named=True)
    assert row["source_id"] == "previous_runs_gfs_temperature"
    assert row["feature_generation_allowed"] is False
    assert row["feature_generation_reason"] == "fixed_lead_forecast_no_success"


def test_ensure_source_allowed_for_features_raises_for_blocked_source():
    eligibility = build_feature_source_eligibility(_decision_with_previous_runs_success())

    assert ensure_source_allowed_for_features(
        eligibility,
        "previous_runs_gfs_temperature",
    ) == "fixed_lead_forecast_pilot_allowed"

    with pytest.raises(ValueError, match="historical_weather_era5"):
        ensure_source_allowed_for_features(eligibility, "historical_weather_era5")

    with pytest.raises(ValueError, match="missing Open-Meteo source decision"):
        ensure_source_allowed_for_features(eligibility, "missing_source")
```

- [ ] **Step 2: Run the red tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_features.py::test_feature_source_eligibility_allows_previous_runs_only_after_success tests/test_open_meteo_features.py::test_feature_source_eligibility_blocks_previous_runs_without_success tests/test_open_meteo_features.py::test_ensure_source_allowed_for_features_raises_for_blocked_source -q
```

Expected: FAIL with import errors for the new functions.

- [ ] **Step 3: Implement eligibility in `_features.py`**

Create `solarstorm/open_meteo/_features.py`:

```python
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
from typing import Any

import polars as pl

from solarstorm.open_meteo._availability import PRODUCTION_STATUS

FEATURE_ELIGIBILITY_SCHEMA = {
    "source_id": pl.String,
    "endpoint": pl.String,
    "model": pl.String,
    "causal_class": pl.String,
    "decision_status": pl.String,
    "n_success": pl.Int64,
    "feature_generation_allowed": pl.Boolean,
    "feature_generation_reason": pl.String,
    "production_status": pl.String,
}


def _feature_decision(row: dict[str, object]) -> tuple[bool, str]:
    source_id = str(row["source_id"])
    causal_class = str(row["causal_class"])
    decision_status = str(row["decision_status"])
    n_success = int(row["n_success"] or 0)
    has_run_metadata = bool(row.get("has_run_metadata", False))
    has_lead_metadata = bool(row.get("has_lead_metadata", False))

    if causal_class == "fixed_lead_forecast":
        if (
            source_id == "previous_runs_gfs_temperature"
            and decision_status == "OPEN_METEO_PREVIOUS_RUNS_READY_FOR_LEAD_AUDIT"
            and n_success > 0
        ):
            return True, "fixed_lead_forecast_pilot_allowed"
        return False, "fixed_lead_forecast_no_success"
    if causal_class == "forecast_snapshot":
        if (
            decision_status == "OPEN_METEO_SINGLE_RUNS_READY_FOR_PILOT"
            and n_success > 0
            and has_run_metadata
            and has_lead_metadata
        ):
            return True, "forecast_snapshot_pilot_allowed"
        return False, "forecast_snapshot_not_available"
    if causal_class == "reanalysis_not_forecast":
        return False, "reanalysis_blocked_as_predictor"
    if causal_class == "seamless_historical_forecast":
        return False, "seamless_historical_forecast_lacks_run_metadata"
    if causal_class == "live_seamless_forecast":
        return False, "live_forecast_forward_collection_only"
    return False, f"unknown_causal_class:{causal_class}"


def build_feature_source_eligibility(decision_update: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for row in decision_update.iter_rows(named=True):
        allowed, reason = _feature_decision(row)
        rows.append(
            {
                "source_id": row["source_id"],
                "endpoint": row["endpoint"],
                "model": row["model"],
                "causal_class": row["causal_class"],
                "decision_status": row["decision_status"],
                "n_success": row["n_success"],
                "feature_generation_allowed": allowed,
                "feature_generation_reason": reason,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, schema=FEATURE_ELIGIBILITY_SCHEMA).sort("source_id")


def ensure_source_allowed_for_features(
    eligibility: pl.DataFrame,
    source_id: str,
) -> str:
    rows = eligibility.filter(pl.col("source_id") == source_id)
    if rows.is_empty():
        raise ValueError(f"missing Open-Meteo source decision for {source_id}")
    row = rows.row(0, named=True)
    if not bool(row["feature_generation_allowed"]):
        raise ValueError(
            f"Open-Meteo source {source_id} is blocked for feature generation: "
            f"{row['feature_generation_reason']}"
        )
    return str(row["feature_generation_reason"])
```

- [ ] **Step 4: Export the functions**

Update `solarstorm/open_meteo/__init__.py`:

```python
from solarstorm.open_meteo._features import (
    build_feature_source_eligibility,
    ensure_source_allowed_for_features,
)
```

Add both names to `__all__`.

- [ ] **Step 5: Verify Task 1**

Run:

```powershell
uv run pytest tests/test_open_meteo_features.py::test_feature_source_eligibility_allows_previous_runs_only_after_success tests/test_open_meteo_features.py::test_feature_source_eligibility_blocks_previous_runs_without_success tests/test_open_meteo_features.py::test_ensure_source_allowed_for_features_raises_for_blocked_source -q
uv run ruff check solarstorm/open_meteo tests/test_open_meteo_features.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 2: Previous Runs Payload Parser and Feature Extraction

**Files:**
- Modify: `tests/test_open_meteo_features.py`
- Modify: `solarstorm/open_meteo/_features.py`
- Modify: `solarstorm/open_meteo/__init__.py`

- [ ] **Step 1: Add fixture payload and failing parser tests**

Append to `tests/test_open_meteo_features.py`:

```python
from solarstorm.open_meteo import build_previous_runs_feature_rows


def _previous_runs_payload() -> dict[str, object]:
    return {
        "hourly": {
            "time": [
                "2024-07-15T00:00",
                "2024-07-15T10:00",
                "2024-07-15T11:00",
                "2024-07-15T23:00",
            ],
            "temperature_2m_previous_day1": [8.0, 11.0, 12.0, 16.0],
            "dew_point_2m_previous_day1": [5.0, 7.0, 7.0, 8.0],
            "cloud_cover_previous_day1": [70.0, 50.0, 40.0, 20.0],
            "cloud_cover_low_previous_day1": [80.0, 60.0, 30.0, 10.0],
            "pressure_msl_previous_day1": [1018.0, 1017.0, 1016.0, 1014.0],
            "wind_speed_10m_previous_day1": [8.0, 12.0, 14.0, 20.0],
            "wind_gusts_10m_previous_day1": [12.0, 18.0, 22.0, 30.0],
            "wind_direction_10m_previous_day1": [300.0, 315.0, 330.0, 340.0],
        }
    }


def test_build_previous_runs_feature_rows_extracts_day1_physical_features():
    rows = build_previous_runs_feature_rows(
        payload=_previous_runs_payload(),
        source_id="previous_runs_gfs_temperature",
        endpoint="previous_runs",
        model="gfs_seamless",
        date_local=dt.date(2024, 7, 15),
        cps=["23:00"],
        request_url_sha256="request-hash",
        response_sha256="response-hash",
    )

    assert rows.height == 1
    row = rows.row(0, named=True)
    assert row["date_local"] == dt.date(2024, 7, 15)
    assert row["cp"] == "23:00"
    assert row["om_source_id"] == "previous_runs_gfs_temperature"
    assert row["om_endpoint"] == "previous_runs"
    assert row["om_model"] == "gfs_seamless"
    assert row["om_causal_class"] == "fixed_lead_forecast"
    assert row["om_feature_status"] == "fixed_lead_forecast_pilot_allowed"
    assert row["om_fixed_lead_days"] == 1
    assert row["om_fixed_lead_hours"] == 24
    assert row["om_prev_d1_temp_23_local_c"] == 16.0
    assert row["om_prev_d1_temp_cp_c"] == 16.0
    assert row["om_prev_d1_remaining_warming_c"] == 0.0
    assert row["om_prev_d1_day_max_c"] == 16.0
    assert row["om_prev_d1_day_min_c"] == 8.0
    assert row["om_prev_d1_cloud_cover_mean_pct"] == 45.0
    assert row["om_prev_d1_cloud_cover_low_mean_pct"] == 45.0
    assert row["om_prev_d1_pressure_msl_mean_hpa"] == 1016.25
    assert row["om_prev_d1_wind_speed_10m_mean"] == 13.5
    assert row["om_prev_d1_wind_gusts_10m_max"] == 30.0
    assert 320.0 < row["om_prev_d1_wind_dir_10m_circular_mean"] < 325.0
    assert row["om_prev_d1_dewpoint_depression_23_local_c"] == 8.0
    assert row["om_prev_d1_foehn_support"] > 0
    assert row["om_prev_d1_stratus_support"] > 0
    assert row["om_request_url_sha256"] == "request-hash"
    assert row["om_response_sha256"] == "response-hash"
    assert row["production_status"] == PRODUCTION_STATUS


def test_build_previous_runs_feature_rows_uses_cp_local_hour():
    rows = build_previous_runs_feature_rows(
        payload=_previous_runs_payload(),
        source_id="previous_runs_gfs_temperature",
        endpoint="previous_runs",
        model="gfs_seamless",
        date_local=dt.date(2024, 7, 15),
        cps=["22:00", "23:00"],
        request_url_sha256="request-hash",
        response_sha256="response-hash",
    )

    by_cp = {row["cp"]: row for row in rows.iter_rows(named=True)}

    assert by_cp["22:00"]["om_prev_d1_temp_cp_c"] == 12.0
    assert by_cp["22:00"]["om_prev_d1_remaining_warming_c"] == 4.0
    assert by_cp["23:00"]["om_prev_d1_temp_cp_c"] == 16.0
    assert by_cp["23:00"]["om_prev_d1_remaining_warming_c"] == 0.0
```

- [ ] **Step 2: Run the red parser tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_features.py::test_build_previous_runs_feature_rows_extracts_day1_physical_features tests/test_open_meteo_features.py::test_build_previous_runs_feature_rows_uses_cp_local_hour -q
```

Expected: FAIL with import error for `build_previous_runs_feature_rows`.

- [ ] **Step 3: Implement parser helpers and feature extraction**

Append to `solarstorm/open_meteo/_features.py`:

```python
def _series(hourly: dict[str, object], name: str) -> list[float | None]:
    values = hourly.get(name, [])
    if not isinstance(values, list):
        return []
    result: list[float | None] = []
    for value in values:
        result.append(None if value is None else float(value))
    return result


def _mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return float(sum(clean) / len(clean)) if clean else None


def _max(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return max(clean) if clean else None


def _min(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return min(clean) if clean else None


def _circular_mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    if not clean:
        return None
    sin_sum = sum(math.sin(math.radians(value)) for value in clean)
    cos_sum = sum(math.cos(math.radians(value)) for value in clean)
    if abs(sin_sum) < 1e-12 and abs(cos_sum) < 1e-12:
        return None
    return math.degrees(math.atan2(sin_sum, cos_sum)) % 360.0


def _hour_index(hourly: dict[str, object]) -> dict[int, int]:
    times = hourly.get("time", [])
    if not isinstance(times, list):
        return {}
    result: dict[int, int] = {}
    for index, value in enumerate(times):
        if not isinstance(value, str):
            continue
        result[dt.datetime.fromisoformat(value).hour] = index
    return result


def _at(values: list[float | None], index: int | None) -> float | None:
    if index is None or index < 0 or index >= len(values):
        return None
    return values[index]


def _cp_local_hour(cp: str) -> int:
    return dt.time.fromisoformat(cp).hour


def _foehn_support(
    *,
    wind_speed_mean: float | None,
    wind_dir_mean: float | None,
    dewpoint_depression_23: float | None,
) -> float | None:
    if wind_speed_mean is None or wind_dir_mean is None or dewpoint_depression_23 is None:
        return None
    nw_component = 1.0 if wind_dir_mean >= 270.0 or wind_dir_mean <= 45.0 else 0.0
    return wind_speed_mean * dewpoint_depression_23 * nw_component


def _stratus_support(
    *,
    cloud_low_mean: float | None,
    dewpoint_depression_23: float | None,
) -> float | None:
    if cloud_low_mean is None or dewpoint_depression_23 is None:
        return None
    moist_factor = max(0.0, 10.0 - dewpoint_depression_23)
    return cloud_low_mean * moist_factor / 10.0


def build_previous_runs_feature_rows(
    *,
    payload: dict[str, object],
    source_id: str,
    endpoint: str,
    model: str,
    date_local: dt.date,
    cps: list[str] | tuple[str, ...],
    request_url_sha256: str,
    response_sha256: str,
) -> pl.DataFrame:
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        raise ValueError("Open-Meteo Previous Runs payload is missing hourly data")

    hour_to_index = _hour_index(hourly)
    temp = _series(hourly, "temperature_2m_previous_day1")
    dewpoint = _series(hourly, "dew_point_2m_previous_day1")
    cloud = _series(hourly, "cloud_cover_previous_day1")
    cloud_low = _series(hourly, "cloud_cover_low_previous_day1")
    pressure = _series(hourly, "pressure_msl_previous_day1")
    wind_speed = _series(hourly, "wind_speed_10m_previous_day1")
    wind_gusts = _series(hourly, "wind_gusts_10m_previous_day1")
    wind_dir = _series(hourly, "wind_direction_10m_previous_day1")

    idx23 = hour_to_index.get(23)
    temp23 = _at(temp, idx23)
    dew23 = _at(dewpoint, idx23)
    wind_dir_mean = _circular_mean(wind_dir)
    wind_speed_mean = _mean(wind_speed)
    cloud_low_mean = _mean(cloud_low)
    dewpoint_depression_23 = (
        temp23 - dew23 if temp23 is not None and dew23 is not None else None
    )
    rows: list[dict[str, object]] = []
    for cp in cps:
        cp_index = hour_to_index.get(_cp_local_hour(cp))
        temp_cp = _at(temp, cp_index)
        rows.append(
            {
                "date_local": date_local,
                "cp": cp,
                "om_source_id": source_id,
                "om_endpoint": endpoint,
                "om_model": model,
                "om_causal_class": "fixed_lead_forecast",
                "om_feature_status": "fixed_lead_forecast_pilot_allowed",
                "om_request_url_sha256": request_url_sha256,
                "om_response_sha256": response_sha256,
                "om_run_time_utc": None,
                "om_available_time_utc": None,
                "om_valid_time_utc": None,
                "om_lead_h": None,
                "om_fixed_lead_days": 1,
                "om_fixed_lead_hours": 24,
                "om_prev_d1_temp_23_local_c": temp23,
                "om_prev_d1_temp_cp_c": temp_cp,
                "om_prev_d1_remaining_warming_c": (
                    temp23 - temp_cp
                    if temp23 is not None and temp_cp is not None
                    else None
                ),
                "om_prev_d1_day_max_c": _max(temp),
                "om_prev_d1_day_min_c": _min(temp),
                "om_prev_d1_cloud_cover_mean_pct": _mean(cloud),
                "om_prev_d1_cloud_cover_low_mean_pct": cloud_low_mean,
                "om_prev_d1_pressure_msl_mean_hpa": _mean(pressure),
                "om_prev_d1_wind_speed_10m_mean": wind_speed_mean,
                "om_prev_d1_wind_gusts_10m_max": _max(wind_gusts),
                "om_prev_d1_wind_dir_10m_circular_mean": wind_dir_mean,
                "om_prev_d1_dewpoint_depression_23_local_c": dewpoint_depression_23,
                "om_prev_d1_foehn_support": _foehn_support(
                    wind_speed_mean=wind_speed_mean,
                    wind_dir_mean=wind_dir_mean,
                    dewpoint_depression_23=dewpoint_depression_23,
                ),
                "om_prev_d1_stratus_support": _stratus_support(
                    cloud_low_mean=cloud_low_mean,
                    dewpoint_depression_23=dewpoint_depression_23,
                ),
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False)
```

- [ ] **Step 4: Export the parser**

Update `solarstorm/open_meteo/__init__.py`:

```python
from solarstorm.open_meteo._features import build_previous_runs_feature_rows
```

Add the name to `__all__`.

- [ ] **Step 5: Verify Task 2**

Run:

```powershell
uv run pytest tests/test_open_meteo_features.py::test_build_previous_runs_feature_rows_extracts_day1_physical_features tests/test_open_meteo_features.py::test_build_previous_runs_feature_rows_uses_cp_local_hour -q
uv run ruff check solarstorm/open_meteo tests/test_open_meteo_features.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 3: Build and Write Open-Meteo Feature Artifacts

**Files:**
- Modify: `tests/test_open_meteo_features.py`
- Modify: `solarstorm/open_meteo/_features.py`
- Modify: `solarstorm/open_meteo/__init__.py`

- [ ] **Step 1: Write failing feature builder and artifact tests**

Append to `tests/test_open_meteo_features.py`:

```python
from solarstorm.open_meteo import (
    OPEN_METEO_FEATURE_FILENAMES,
    build_open_meteo_feature_artifacts,
    write_open_meteo_feature_artifacts,
)


def _raw_previous_runs_frame() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "source_id": "previous_runs_gfs_temperature",
                "endpoint": "previous_runs",
                "model": "gfs_seamless",
                "date_local": dt.date(2024, 7, 15),
                "request_url_sha256": "request-hash",
                "response_sha256": "response-hash",
                "response_text": json.dumps(_previous_runs_payload()),
                "production_status": PRODUCTION_STATUS,
            }
        ]
    )


def test_build_open_meteo_feature_artifacts_writes_only_allowed_sources():
    artifacts = build_open_meteo_feature_artifacts(
        raw_responses=_raw_previous_runs_frame(),
        decision_update=_decision_with_previous_runs_success(),
        cps=["22:00", "23:00"],
    )

    features = artifacts["open_meteo_features_v1"]
    manifest = artifacts["open_meteo_feature_manifest_v1"]
    coverage = artifacts["open_meteo_feature_coverage_v1"]

    assert features.height == 2
    assert set(features["cp"].to_list()) == {"22:00", "23:00"}
    assert features["date_local"].n_unique() == 1
    assert set(features["production_status"].to_list()) == {PRODUCTION_STATUS}
    assert all(
        column in {"date_local", "cp"} or column.startswith("om_") or column == "production_status"
        for column in features.columns
    )
    assert manifest.height > 0
    assert set(manifest["feature_source"].to_list()) == {"open_meteo_previous_runs"}
    assert coverage.row(0, named=True)["n_feature_rows"] == 2


def test_build_open_meteo_feature_artifacts_rejects_blocked_sources_even_with_payload():
    raw = _raw_previous_runs_frame().with_columns(
        pl.lit("historical_weather_era5").alias("source_id"),
        pl.lit("historical_weather").alias("endpoint"),
        pl.lit("era5").alias("model"),
    )

    artifacts = build_open_meteo_feature_artifacts(
        raw_responses=raw,
        decision_update=_decision_with_previous_runs_success(),
        cps=["23:00"],
    )

    assert artifacts["open_meteo_features_v1"].height == 0
    blocked = artifacts["open_meteo_feature_blocked_sources_v1"]
    assert blocked.height == 1
    assert blocked.row(0, named=True)["source_id"] == "historical_weather_era5"


def test_build_open_meteo_feature_artifacts_rejects_duplicate_keys():
    duplicated = pl.concat([_raw_previous_runs_frame(), _raw_previous_runs_frame()])

    with pytest.raises(ValueError, match="duplicate Open-Meteo feature keys"):
        build_open_meteo_feature_artifacts(
            raw_responses=duplicated,
            decision_update=_decision_with_previous_runs_success(),
            cps=["23:00"],
        )


def test_write_open_meteo_feature_artifacts_writes_parquet_and_report_without_overwriting_local_features(
    tmp_path: Path,
):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    local_features = data_dir / "features.parquet"
    local_features.write_text("do not touch", encoding="utf-8")

    artifacts = build_open_meteo_feature_artifacts(
        raw_responses=_raw_previous_runs_frame(),
        decision_update=_decision_with_previous_runs_success(),
        cps=["23:00"],
    )
    paths = write_open_meteo_feature_artifacts(
        artifacts,
        data_dir=data_dir,
        output_dir=tmp_path / "reports",
        today=dt.date(2026, 6, 10),
    )

    assert paths["open_meteo_features_parquet"] == data_dir / "open_meteo_features.parquet"
    assert paths["open_meteo_features_parquet"].exists()
    assert local_features.read_text(encoding="utf-8") == "do not touch"
    for key, filename in OPEN_METEO_FEATURE_FILENAMES.items():
        assert paths[key] == tmp_path / "reports" / filename
        assert paths[key].exists()
    report = paths["open_meteo_feature_report_md"].read_text(encoding="utf-8")
    assert "Historical Weather and Historical Forecast remain blocked" in report
    assert "EXPERIMENT_ONLY" in report
```

- [ ] **Step 2: Run the red feature artifact tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_features.py::test_build_open_meteo_feature_artifacts_writes_only_allowed_sources tests/test_open_meteo_features.py::test_build_open_meteo_feature_artifacts_rejects_blocked_sources_even_with_payload tests/test_open_meteo_features.py::test_build_open_meteo_feature_artifacts_rejects_duplicate_keys tests/test_open_meteo_features.py::test_write_open_meteo_feature_artifacts_writes_parquet_and_report_without_overwriting_local_features -q
```

Expected: FAIL with import errors for artifact helpers.

- [ ] **Step 3: Implement feature artifact builder and writer**

Append to `solarstorm/open_meteo/_features.py`:

```python
OPEN_METEO_FEATURE_FILENAMES = {
    "open_meteo_feature_manifest_v1": "open_meteo_feature_manifest_v1.csv",
    "open_meteo_feature_coverage_v1": "open_meteo_feature_coverage_v1.csv",
    "open_meteo_feature_source_eligibility_v1": (
        "open_meteo_feature_source_eligibility_v1.csv"
    ),
    "open_meteo_feature_blocked_sources_v1": (
        "open_meteo_feature_blocked_sources_v1.csv"
    ),
}


def _empty_features() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "date_local": pl.Date,
            "cp": pl.String,
            "production_status": pl.String,
        }
    )


def _parse_response_text(text: str) -> dict[str, object]:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Open-Meteo response payload must be a JSON object")
    return payload


def _feature_manifest(features: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for column in features.columns:
        if column in {"date_local", "cp", "production_status"}:
            continue
        rows.append(
            {
                "feature": column,
                "feature_source": "open_meteo_previous_runs",
                "non_null_rows": features.height - features[column].null_count(),
                "n_rows": features.height,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows, strict=False)


def _feature_coverage(features: pl.DataFrame) -> pl.DataFrame:
    if features.is_empty():
        return pl.DataFrame(
            [
                {
                    "n_feature_rows": 0,
                    "n_dates": 0,
                    "n_cps": 0,
                    "production_status": PRODUCTION_STATUS,
                }
            ],
            strict=False,
        )
    return pl.DataFrame(
        [
            {
                "n_feature_rows": features.height,
                "n_dates": features["date_local"].n_unique(),
                "n_cps": features["cp"].n_unique(),
                "min_date": features["date_local"].min(),
                "max_date": features["date_local"].max(),
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def _duplicate_key_count(features: pl.DataFrame) -> int:
    if features.is_empty():
        return 0
    return features.height - features.select(["date_local", "cp"]).unique().height


def build_open_meteo_feature_artifacts(
    *,
    raw_responses: pl.DataFrame,
    decision_update: pl.DataFrame,
    cps: list[str] | tuple[str, ...],
) -> dict[str, pl.DataFrame]:
    eligibility = build_feature_source_eligibility(decision_update)
    feature_frames: list[pl.DataFrame] = []
    blocked_rows: list[dict[str, object]] = []

    for row in raw_responses.iter_rows(named=True):
        source_id = str(row["source_id"])
        source_rows = eligibility.filter(pl.col("source_id") == source_id)
        if source_rows.is_empty() or not bool(source_rows.row(0, named=True)["feature_generation_allowed"]):
            reason = (
                "missing_source_decision"
                if source_rows.is_empty()
                else source_rows.row(0, named=True)["feature_generation_reason"]
            )
            blocked_rows.append(
                {
                    "source_id": source_id,
                    "endpoint": row["endpoint"],
                    "model": row["model"],
                    "blocked_reason": reason,
                    "production_status": PRODUCTION_STATUS,
                }
            )
            continue
        if source_id == "previous_runs_gfs_temperature":
            feature_frames.append(
                build_previous_runs_feature_rows(
                    payload=_parse_response_text(str(row["response_text"])),
                    source_id=source_id,
                    endpoint=str(row["endpoint"]),
                    model=str(row["model"]),
                    date_local=row["date_local"],
                    cps=cps,
                    request_url_sha256=str(row["request_url_sha256"]),
                    response_sha256=str(row["response_sha256"]),
                )
            )

    features = (
        pl.concat(feature_frames, how="diagonal_relaxed")
        if feature_frames
        else _empty_features()
    )
    if _duplicate_key_count(features):
        raise ValueError("duplicate Open-Meteo feature keys for date_local, cp")

    blocked = pl.DataFrame(blocked_rows, strict=False)
    return {
        "open_meteo_features_v1": features,
        "open_meteo_feature_manifest_v1": _feature_manifest(features),
        "open_meteo_feature_coverage_v1": _feature_coverage(features),
        "open_meteo_feature_source_eligibility_v1": eligibility,
        "open_meteo_feature_blocked_sources_v1": blocked,
    }


def _markdown_table(frame: pl.DataFrame, max_rows: int = 30) -> str:
    if frame.is_empty():
        return "_No rows._"
    header = "| " + " | ".join(frame.columns) + " |"
    divider = "| " + " | ".join("---" for _ in frame.columns) + " |"
    rows = [
        "| " + " | ".join("" if row[col] is None else str(row[col]) for col in frame.columns) + " |"
        for row in frame.head(max_rows).iter_rows(named=True)
    ]
    return "\n".join([header, divider, *rows])


def render_open_meteo_feature_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    return "\n\n".join(
        [
            "# Open-Meteo Feature Build Report",
            f"Generated: {today.isoformat()}",
            f"production_status: {PRODUCTION_STATUS}",
            "Historical Weather and Historical Forecast remain blocked as causal predictors.",
            "Previous Runs features are fixed-lead experiment-only predictors.",
            "## Coverage",
            _markdown_table(artifacts["open_meteo_feature_coverage_v1"]),
            "## Source Eligibility",
            _markdown_table(artifacts["open_meteo_feature_source_eligibility_v1"]),
            "## Feature Manifest",
            _markdown_table(artifacts["open_meteo_feature_manifest_v1"]),
            "## Blocked Sources",
            _markdown_table(artifacts["open_meteo_feature_blocked_sources_v1"]),
        ]
    ) + "\n"


def write_open_meteo_feature_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    data_dir: Path,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    features_path = data_dir / "open_meteo_features.parquet"
    artifacts["open_meteo_features_v1"].write_parquet(features_path)
    paths["open_meteo_features_parquet"] = features_path

    for key, filename in OPEN_METEO_FEATURE_FILENAMES.items():
        path = output_dir / filename
        artifacts[key].write_csv(path)
        paths[key] = path

    report_path = output_dir / "open_meteo_feature_report_v1.md"
    report_path.write_text(
        render_open_meteo_feature_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["open_meteo_feature_report_md"] = report_path
    return paths
```

- [ ] **Step 4: Export artifact APIs**

Update `solarstorm/open_meteo/__init__.py` exports:

```python
OPEN_METEO_FEATURE_FILENAMES
build_open_meteo_feature_artifacts
render_open_meteo_feature_report
write_open_meteo_feature_artifacts
```

- [ ] **Step 5: Verify Task 3**

Run:

```powershell
uv run pytest tests/test_open_meteo_features.py -q
uv run ruff check solarstorm/open_meteo tests/test_open_meteo_features.py
```

Expected: feature tests pass and Ruff reports `All checks passed!`.

---

### Task 4: Feature-Build CLI from Fixture/Raw CSV

**Files:**
- Create: `tests/test_open_meteo_feature_cli.py`
- Modify: `solarstorm/__main__.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_open_meteo_feature_cli.py`:

```python
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from solarstorm.open_meteo import PRODUCTION_STATUS
from tests.test_open_meteo_features import (
    _decision_with_previous_runs_success,
    _previous_runs_payload,
)

runner = CliRunner()


def test_open_meteo_build_features_cli_writes_feature_artifacts(tmp_path: Path):
    decision_path = tmp_path / "decision.csv"
    raw_path = tmp_path / "raw.csv"
    data_dir = tmp_path / "data"
    output_dir = tmp_path / "reports"
    _decision_with_previous_runs_success().write_csv(decision_path)
    pl.DataFrame(
        [
            {
                "source_id": "previous_runs_gfs_temperature",
                "endpoint": "previous_runs",
                "model": "gfs_seamless",
                "date_local": dt.date(2024, 7, 15),
                "request_url_sha256": "request-hash",
                "response_sha256": "response-hash",
                "response_text": json.dumps(_previous_runs_payload()),
                "production_status": PRODUCTION_STATUS,
            }
        ]
    ).write_csv(raw_path)
    (data_dir).mkdir()
    (data_dir / "features.parquet").write_text("local", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "open-meteo-build-features",
            "--raw-responses-path",
            str(raw_path),
            "--decision-path",
            str(decision_path),
            "--data-dir",
            str(data_dir),
            "--output-dir",
            str(output_dir),
            "--cps",
            "22:00,23:00",
        ],
    )

    assert result.exit_code == 0
    assert "Open-Meteo feature build complete." in result.stdout
    assert "EXPERIMENT_ONLY" in result.stdout
    features_path = data_dir / "open_meteo_features.parquet"
    assert features_path.exists()
    assert (data_dir / "features.parquet").read_text(encoding="utf-8") == "local"
    features = pl.read_parquet(features_path)
    assert features.height == 2
    assert set(features["cp"].to_list()) == {"22:00", "23:00"}
    assert (output_dir / "open_meteo_feature_report_v1.md").exists()


def test_open_meteo_build_features_cli_blocks_missing_inputs(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "open-meteo-build-features",
            "--raw-responses-path",
            str(tmp_path / "missing.csv"),
            "--decision-path",
            str(tmp_path / "missing-decision.csv"),
        ],
    )

    assert result.exit_code == 2
    assert "missing input paths" in result.stdout
```

- [ ] **Step 2: Run red CLI tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_feature_cli.py -q
```

Expected: FAIL because `open-meteo-build-features` command is missing.

- [ ] **Step 3: Add CLI imports**

Modify `solarstorm/__main__.py` Open-Meteo imports:

```python
from solarstorm.open_meteo import (
    build_open_meteo_feature_artifacts,
    write_open_meteo_feature_artifacts,
)
```

- [ ] **Step 4: Add command**

Append before `if __name__ == "__main__":` in `solarstorm/__main__.py`:

```python
@app.command("open-meteo-build-features")
def open_meteo_build_features(
    raw_responses_path: str = typer.Option(...),
    decision_path: str = typer.Option(
        "./reports/open-meteo-availability-live-smoke/open_meteo_decision_update_v1.csv"
    ),
    data_dir: str = typer.Option("./data"),
    output_dir: str = typer.Option("./reports/open-meteo-features"),
    cps: str = typer.Option("20:00,21:00,22:00,23:00"),
):
    """Build experiment-only Open-Meteo feature artifacts from raw responses."""
    raw_path = Path(raw_responses_path)
    decision_file = Path(decision_path)
    missing = [path for path in [raw_path, decision_file] if not path.exists()]
    if missing:
        print(f"ERROR: missing input paths: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)

    raw = pl.read_csv(raw_path, try_parse_dates=True)
    decision = pl.read_csv(decision_file)
    artifacts = build_open_meteo_feature_artifacts(
        raw_responses=raw,
        decision_update=decision,
        cps=_parse_open_meteo_csv_strings(cps),
    )
    paths = write_open_meteo_feature_artifacts(
        artifacts,
        data_dir=Path(data_dir),
        output_dir=Path(output_dir),
        today=dt.date.today(),
    )
    print("Open-Meteo feature build complete.")
    print("production_status: EXPERIMENT_ONLY")
    print(f"Features: {paths['open_meteo_features_parquet']}")
    print(f"Report: {paths['open_meteo_feature_report_md']}")
```

- [ ] **Step 5: Verify Task 4**

Run:

```powershell
uv run pytest tests/test_open_meteo_feature_cli.py tests/test_open_meteo_features.py -q
uv run ruff check solarstorm/__main__.py solarstorm/open_meteo tests/test_open_meteo_feature_cli.py tests/test_open_meteo_features.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 5: Open-Meteo Pilot Comparison Module

**Files:**
- Create: `tests/test_open_meteo_pilot.py`
- Create: `solarstorm/open_meteo/_pilot.py`
- Modify: `solarstorm/open_meteo/__init__.py`

- [ ] **Step 1: Write failing pilot tests**

Create `tests/test_open_meteo_pilot.py`:

```python
from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from solarstorm.open_meteo import (
    PRODUCTION_STATUS,
    build_open_meteo_pilot,
    join_open_meteo_features,
)


def _local_matrix() -> pl.DataFrame:
    rows = []
    for year in [2022, 2023, 2024]:
        for day in range(1, 7):
            date_local = dt.date(year, 7, day)
            for cp in ["22:00", "23:00"]:
                base = 12.0 + day + (year - 2022) * 0.2
                om_signal = 0.5 if cp == "23:00" else 0.0
                rows.append(
                    {
                        "date_local": date_local,
                        "cp": cp,
                        "tmax_int": int(round(base + om_signal)),
                        "k_cp": base - 1.0,
                        "slope_3h": 0.1 * day,
                        "dewpoint_depression": 3.0 + day,
                        "binary_macro_regime_label": (
                            "macro_non_southerly"
                            if day % 2
                            else "macro_southerly_flow"
                        ),
                    }
                )
    return pl.DataFrame(rows)


def _om_features() -> pl.DataFrame:
    rows = []
    for row in _local_matrix().iter_rows(named=True):
        if row["date_local"].year < 2023:
            continue
        rows.append(
            {
                "date_local": row["date_local"],
                "cp": row["cp"],
                "om_prev_d1_temp_23_local_c": float(row["tmax_int"]),
                "om_prev_d1_remaining_warming_c": (
                    0.5 if row["cp"] == "22:00" else 0.0
                ),
                "om_prev_d1_foehn_support": 2.0,
                "om_prev_d1_stratus_support": 1.0,
                "production_status": PRODUCTION_STATUS,
            }
        )
    return pl.DataFrame(rows)


def test_join_open_meteo_features_keeps_only_covered_rows():
    joined = join_open_meteo_features(_local_matrix(), _om_features())

    assert joined.height == _om_features().height
    assert set(joined["date_local"].dt.year().to_list()) == {2023, 2024}
    assert "om_prev_d1_temp_23_local_c" in joined.columns
    assert "k_cp" in joined.columns


def test_build_open_meteo_pilot_compares_local_and_augmented_on_same_rows():
    artifacts = build_open_meteo_pilot(
        local_features=_local_matrix(),
        open_meteo_features=_om_features(),
        test_years=[2024],
        numeric_feature_columns=["k_cp", "slope_3h", "dewpoint_depression"],
        categorical_feature_columns=["binary_macro_regime_label"],
        open_meteo_numeric_columns=[
            "om_prev_d1_temp_23_local_c",
            "om_prev_d1_remaining_warming_c",
        ],
    )

    results = artifacts["onda3_open_meteo_pilot_model_results_v1"]
    decision = artifacts["onda3_open_meteo_pilot_decision_update_v1"].row(0, named=True)
    predictions = artifacts["onda3_open_meteo_pilot_predictions_v1"]

    assert set(results["candidate_id"].to_list()) == {
        "local_only_reference",
        "open_meteo_augmented",
    }
    by_candidate = {row["candidate_id"]: row for row in results.iter_rows(named=True)}
    assert by_candidate["local_only_reference"]["n_train"] == (
        by_candidate["open_meteo_augmented"]["n_train"]
    )
    assert by_candidate["local_only_reference"]["n_test"] == (
        by_candidate["open_meteo_augmented"]["n_test"]
    )
    assert decision["decision_status"] in {
        "KEEP_LOCAL_ONLY_REFERENCE",
        "KEEP_OPEN_METEO_IN_EXPERIMENT_REVIEW",
        "PROMOTE_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION",
    }
    assert decision["production_status"] == PRODUCTION_STATUS
    assert set(predictions["production_status"].to_list()) == {PRODUCTION_STATUS}
```

- [ ] **Step 2: Run the red pilot tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_pilot.py -q
```

Expected: FAIL with import errors.

- [ ] **Step 3: Implement pilot module**

Create `solarstorm/open_meteo/_pilot.py`:

```python
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import polars as pl

from solarstorm.onda3._baseline_model import _mae, _ridge_predict
from solarstorm.onda3._pooled_iteration import (
    add_pooled_temporal_features,
    normalize_pooled_cp_column,
)
from solarstorm.open_meteo._availability import PRODUCTION_STATUS


def _ensure_date(frame: pl.DataFrame) -> pl.DataFrame:
    dtype = frame.schema.get("date_local")
    if dtype == pl.Utf8:
        return frame.with_columns(pl.col("date_local").str.to_date())
    if isinstance(dtype, pl.Datetime):
        return frame.with_columns(pl.col("date_local").dt.date())
    return frame


def join_open_meteo_features(
    local_features: pl.DataFrame,
    open_meteo_features: pl.DataFrame,
) -> pl.DataFrame:
    local = normalize_pooled_cp_column(_ensure_date(local_features))
    om = normalize_pooled_cp_column(_ensure_date(open_meteo_features))
    if om.height - om.select(["date_local", "cp"]).unique().height:
        raise ValueError("duplicate Open-Meteo feature keys for pilot join")
    return local.join(om, on=["date_local", "cp"], how="inner", suffix="_om_meta")


def _encode(
    train: pl.DataFrame,
    test: pl.DataFrame,
    *,
    numeric_columns: list[str],
    categorical_columns: list[str],
) -> tuple[np.ndarray, np.ndarray]:
    train_parts = [train.select(numeric_columns).to_numpy()] if numeric_columns else []
    test_parts = [test.select(numeric_columns).to_numpy()] if numeric_columns else []
    for column in categorical_columns:
        if column not in train.columns or column not in test.columns:
            continue
        categories = sorted(str(value) for value in train[column].drop_nulls().unique().to_list())
        for category in categories:
            train_parts.append(
                (train[column].cast(pl.Utf8) == category).cast(pl.Float64).to_numpy().reshape(-1, 1)
            )
            test_parts.append(
                (test[column].cast(pl.Utf8) == category).cast(pl.Float64).to_numpy().reshape(-1, 1)
            )
    if not train_parts:
        raise ValueError("Open-Meteo pilot requires at least one feature column")
    return np.column_stack(train_parts), np.column_stack(test_parts)


def _run_candidate(
    matrix: pl.DataFrame,
    *,
    test_year: int,
    candidate_id: str,
    numeric_columns: list[str],
    categorical_columns: list[str],
    target_column: str,
) -> tuple[dict[str, object], pl.DataFrame]:
    dated = matrix.with_columns(pl.col("date_local").dt.year().alias("_year"))
    train = dated.filter(pl.col("_year") < test_year).drop("_year")
    test = dated.filter(pl.col("_year") == test_year).drop("_year")
    train_y = train[target_column].to_numpy()
    test_y = test[target_column].to_numpy()
    train_x, test_x = _encode(
        train,
        test,
        numeric_columns=[column for column in numeric_columns if column in matrix.columns],
        categorical_columns=[
            column for column in categorical_columns if column in matrix.columns
        ],
    )
    prediction = _ridge_predict(train_x, train_y, test_x)
    mae = _mae(test_y, prediction)
    predictions = test.select(["date_local", "cp"]).with_columns(
        pl.lit(test_year).alias("test_year"),
        pl.lit(candidate_id).alias("candidate_id"),
        pl.Series("actual", test_y),
        pl.Series("prediction", prediction),
        pl.Series("absolute_error", np.abs(test_y - prediction)),
        (pl.Series("actual_bracket", test_y) + 0.5).floor().cast(pl.Int64),
        (pl.Series("pred_bracket", prediction) + 0.5).floor().cast(pl.Int64),
        pl.lit(PRODUCTION_STATUS).alias("production_status"),
    ).with_columns(
        (pl.col("actual_bracket") == pl.col("pred_bracket")).alias("exact_bracket")
    )
    return (
        {
            "test_year": test_year,
            "candidate_id": candidate_id,
            "n_train": train.height,
            "n_test": test.height,
            "mae": mae,
            "exact_bracket_pct": float(predictions["exact_bracket"].cast(pl.Float64).mean() * 100.0),
            "production_status": PRODUCTION_STATUS,
        },
        predictions,
    )


def _decision(results: pl.DataFrame) -> pl.DataFrame:
    if results.is_empty():
        status = "BLOCK_OPEN_METEO_BY_AVAILABILITY"
        rationale = "No covered Open-Meteo pilot rows were available."
        delta = None
    else:
        local = results.filter(pl.col("candidate_id") == "local_only_reference")
        augmented = results.filter(pl.col("candidate_id") == "open_meteo_augmented")
        local_mae = float(local["mae"].mean())
        augmented_mae = float(augmented["mae"].mean())
        delta = augmented_mae - local_mae
        if delta < -0.01:
            status = "PROMOTE_OPEN_METEO_TO_NEXT_EXPERIMENT_ONLY_ITERATION"
            rationale = "Open-Meteo augmented candidate improved same-row MAE."
        elif delta <= 0.05:
            status = "KEEP_OPEN_METEO_IN_EXPERIMENT_REVIEW"
            rationale = "Open-Meteo augmented candidate is close enough for further review."
        else:
            status = "KEEP_LOCAL_ONLY_REFERENCE"
            rationale = "Local-only reference outperformed Open-Meteo augmented candidate."
    return pl.DataFrame(
        [
            {
                "decision_status": status,
                "decision_rationale": rationale,
                "augmented_minus_local_mae": delta,
                "production_status": PRODUCTION_STATUS,
            }
        ],
        strict=False,
    )


def build_open_meteo_pilot(
    *,
    local_features: pl.DataFrame,
    open_meteo_features: pl.DataFrame,
    test_years: list[int],
    numeric_feature_columns: list[str],
    categorical_feature_columns: list[str],
    open_meteo_numeric_columns: list[str],
    target_column: str = "tmax_int",
) -> dict[str, pl.DataFrame]:
    joined = add_pooled_temporal_features(
        join_open_meteo_features(local_features, open_meteo_features)
    )
    local_numeric = [
        column
        for column in [*numeric_feature_columns, "cp_sin", "cp_cos", "month_sin", "month_cos", "doy_sin", "doy_cos"]
        if column in joined.columns and joined.schema[column].is_numeric()
    ]
    augmented_numeric = [
        column
        for column in [*local_numeric, *open_meteo_numeric_columns]
        if column in joined.columns and joined.schema[column].is_numeric()
    ]
    result_rows: list[dict[str, object]] = []
    prediction_frames: list[pl.DataFrame] = []
    for test_year in test_years:
        if joined.filter(pl.col("date_local").dt.year() < test_year).is_empty():
            continue
        if joined.filter(pl.col("date_local").dt.year() == test_year).is_empty():
            continue
        for candidate_id, columns in [
            ("local_only_reference", local_numeric),
            ("open_meteo_augmented", augmented_numeric),
        ]:
            result, predictions = _run_candidate(
                joined,
                test_year=test_year,
                candidate_id=candidate_id,
                numeric_columns=columns,
                categorical_columns=categorical_feature_columns,
                target_column=target_column,
            )
            result_rows.append(result)
            prediction_frames.append(predictions)

    results = pl.DataFrame(result_rows, strict=False)
    predictions = (
        pl.concat(prediction_frames, how="diagonal_relaxed")
        if prediction_frames
        else pl.DataFrame()
    )
    return {
        "onda3_open_meteo_pilot_join_scope_v1": pl.DataFrame(
            [
                {
                    "n_joined_rows": joined.height,
                    "n_joined_dates": joined["date_local"].n_unique() if joined.height else 0,
                    "production_status": PRODUCTION_STATUS,
                }
            ],
            strict=False,
        ),
        "onda3_open_meteo_pilot_model_results_v1": results,
        "onda3_open_meteo_pilot_predictions_v1": predictions,
        "onda3_open_meteo_pilot_decision_update_v1": _decision(results),
    }
```

- [ ] **Step 4: Export pilot functions**

Update `solarstorm/open_meteo/__init__.py`:

```python
from solarstorm.open_meteo._pilot import (
    build_open_meteo_pilot,
    join_open_meteo_features,
)
```

Add names to `__all__`.

- [ ] **Step 5: Verify Task 5**

Run:

```powershell
uv run pytest tests/test_open_meteo_pilot.py -q
uv run ruff check solarstorm/open_meteo tests/test_open_meteo_pilot.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 6: Pilot Artifact Writer and CLI

**Files:**
- Modify: `tests/test_open_meteo_pilot.py`
- Create: `tests/test_open_meteo_pilot_cli.py`
- Modify: `solarstorm/open_meteo/_pilot.py`
- Modify: `solarstorm/open_meteo/__init__.py`
- Modify: `solarstorm/__main__.py`

- [ ] **Step 1: Add failing writer tests**

Append to `tests/test_open_meteo_pilot.py`:

```python
from solarstorm.open_meteo import (
    ONDA3_OPEN_METEO_PILOT_FILENAMES,
    write_open_meteo_pilot_artifacts,
)


def test_write_open_meteo_pilot_artifacts_creates_csvs_and_report(tmp_path: Path):
    artifacts = build_open_meteo_pilot(
        local_features=_local_matrix(),
        open_meteo_features=_om_features(),
        test_years=[2024],
        numeric_feature_columns=["k_cp", "slope_3h", "dewpoint_depression"],
        categorical_feature_columns=["binary_macro_regime_label"],
        open_meteo_numeric_columns=["om_prev_d1_temp_23_local_c"],
    )

    paths = write_open_meteo_pilot_artifacts(
        artifacts,
        output_dir=tmp_path,
        today=dt.date(2026, 6, 10),
    )

    for key, filename in ONDA3_OPEN_METEO_PILOT_FILENAMES.items():
        assert paths[key] == tmp_path / filename
        assert paths[key].exists()
    report = paths["onda3_open_meteo_pilot_report_md"].read_text(encoding="utf-8")
    assert "Open-Meteo augmented candidate" in report
    assert "EXPERIMENT_ONLY" in report
```

- [ ] **Step 2: Run red writer test**

Run:

```powershell
uv run pytest tests/test_open_meteo_pilot.py::test_write_open_meteo_pilot_artifacts_creates_csvs_and_report -q
```

Expected: FAIL with import errors.

- [ ] **Step 3: Implement writer**

Append to `solarstorm/open_meteo/_pilot.py`:

```python
ONDA3_OPEN_METEO_PILOT_FILENAMES = {
    "onda3_open_meteo_pilot_join_scope_v1": (
        "onda3_open_meteo_pilot_join_scope_v1.csv"
    ),
    "onda3_open_meteo_pilot_model_results_v1": (
        "onda3_open_meteo_pilot_model_results_v1.csv"
    ),
    "onda3_open_meteo_pilot_predictions_v1": (
        "onda3_open_meteo_pilot_predictions_v1.csv"
    ),
    "onda3_open_meteo_pilot_decision_update_v1": (
        "onda3_open_meteo_pilot_decision_update_v1.csv"
    ),
}


def _markdown_table(frame: pl.DataFrame, max_rows: int = 30) -> str:
    if frame.is_empty():
        return "_No rows._"
    header = "| " + " | ".join(frame.columns) + " |"
    divider = "| " + " | ".join("---" for _ in frame.columns) + " |"
    rows = [
        "| " + " | ".join("" if row[col] is None else str(row[col]) for col in frame.columns) + " |"
        for row in frame.head(max_rows).iter_rows(named=True)
    ]
    return "\n".join([header, divider, *rows])


def render_open_meteo_pilot_report(
    artifacts: dict[str, pl.DataFrame],
    *,
    today: dt.date,
) -> str:
    return "\n\n".join(
        [
            "# Onda 3 Open-Meteo Pilot Report",
            f"Generated: {today.isoformat()}",
            f"production_status: {PRODUCTION_STATUS}",
            "Open-Meteo augmented candidate is compared against local-only reference on identical covered rows.",
            "## Decision",
            _markdown_table(artifacts["onda3_open_meteo_pilot_decision_update_v1"]),
            "## Join Scope",
            _markdown_table(artifacts["onda3_open_meteo_pilot_join_scope_v1"]),
            "## Model Results",
            _markdown_table(artifacts["onda3_open_meteo_pilot_model_results_v1"]),
        ]
    ) + "\n"


def write_open_meteo_pilot_artifacts(
    artifacts: dict[str, pl.DataFrame],
    *,
    output_dir: Path,
    today: dt.date,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for key, filename in ONDA3_OPEN_METEO_PILOT_FILENAMES.items():
        path = output_dir / filename
        artifacts[key].write_csv(path)
        paths[key] = path
    report_path = output_dir / "onda3_open_meteo_pilot_report_v1.md"
    report_path.write_text(
        render_open_meteo_pilot_report(artifacts, today=today),
        encoding="utf-8",
    )
    paths["onda3_open_meteo_pilot_report_md"] = report_path
    return paths
```

- [ ] **Step 4: Export writer APIs**

Update `solarstorm/open_meteo/__init__.py` exports:

```python
ONDA3_OPEN_METEO_PILOT_FILENAMES
render_open_meteo_pilot_report
write_open_meteo_pilot_artifacts
```

- [ ] **Step 5: Add CLI tests**

Create `tests/test_open_meteo_pilot_cli.py`:

```python
from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from solarstorm.__main__ import app
from tests.test_open_meteo_pilot import _local_matrix, _om_features

runner = CliRunner()


def test_onda3_open_meteo_pilot_cli_writes_artifacts(tmp_path: Path):
    local_path = tmp_path / "local.parquet"
    om_path = tmp_path / "om.parquet"
    output_dir = tmp_path / "pilot"
    _local_matrix().write_parquet(local_path)
    _om_features().write_parquet(om_path)

    result = runner.invoke(
        app,
        [
            "onda3-open-meteo-pilot",
            "--features-path",
            str(local_path),
            "--open-meteo-features-path",
            str(om_path),
            "--output-dir",
            str(output_dir),
            "--test-years",
            "2024",
        ],
    )

    assert result.exit_code == 0
    assert "Onda 3 Open-Meteo pilot complete." in result.stdout
    assert "EXPERIMENT_ONLY" in result.stdout
    assert (output_dir / "onda3_open_meteo_pilot_report_v1.md").exists()
    decision = pl.read_csv(output_dir / "onda3_open_meteo_pilot_decision_update_v1.csv")
    assert decision.row(0, named=True)["production_status"] == "EXPERIMENT_ONLY"


def test_onda3_open_meteo_pilot_cli_blocks_missing_inputs(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "onda3-open-meteo-pilot",
            "--features-path",
            str(tmp_path / "missing.parquet"),
            "--open-meteo-features-path",
            str(tmp_path / "missing-om.parquet"),
        ],
    )

    assert result.exit_code == 2
    assert "missing input paths" in result.stdout
```

- [ ] **Step 6: Run red CLI tests**

Run:

```powershell
uv run pytest tests/test_open_meteo_pilot_cli.py -q
```

Expected: FAIL because the command is missing.

- [ ] **Step 7: Add CLI imports**

Modify `solarstorm/__main__.py` Open-Meteo imports:

```python
from solarstorm.open_meteo import (
    build_open_meteo_pilot,
    write_open_meteo_pilot_artifacts,
)
```

- [ ] **Step 8: Add CLI command**

Append before `if __name__ == "__main__":`:

```python
@app.command("onda3-open-meteo-pilot")
def onda3_open_meteo_pilot(
    features_path: str = typer.Option("./data/features.parquet"),
    open_meteo_features_path: str = typer.Option("./data/open_meteo_features.parquet"),
    output_dir: str = typer.Option("./reports/onda3-open-meteo-pilot"),
    test_years: str = typer.Option("2024,2025"),
):
    """Run an experiment-only Open-Meteo augmented Onda 3 pilot."""
    local_path = Path(features_path)
    om_path = Path(open_meteo_features_path)
    missing = [path for path in [local_path, om_path] if not path.exists()]
    if missing:
        print(f"ERROR: missing input paths: {', '.join(str(path) for path in missing)}")
        raise typer.Exit(2)
    local = pl.read_parquet(local_path)
    om = pl.read_parquet(om_path)
    numeric_features, categorical_features = select_onda3h_feature_columns(local)
    om_numeric = [
        column
        for column in om.columns
        if column.startswith("om_prev_d1_") and om.schema[column].is_numeric()
    ]
    artifacts = build_open_meteo_pilot(
        local_features=local,
        open_meteo_features=om,
        test_years=_parse_open_meteo_csv_ints(test_years),
        numeric_feature_columns=numeric_features,
        categorical_feature_columns=categorical_features,
        open_meteo_numeric_columns=om_numeric,
    )
    paths = write_open_meteo_pilot_artifacts(
        artifacts,
        output_dir=Path(output_dir),
        today=dt.date.today(),
    )
    decision = artifacts["onda3_open_meteo_pilot_decision_update_v1"].row(0, named=True)
    print(f"Onda 3 Open-Meteo pilot complete: {decision['decision_status']}")
    print("production_status: EXPERIMENT_ONLY")
    print(f"Report: {paths['onda3_open_meteo_pilot_report_md']}")
```

- [ ] **Step 9: Verify Task 6**

Run:

```powershell
uv run pytest tests/test_open_meteo_pilot.py tests/test_open_meteo_pilot_cli.py -q
uv run ruff check solarstorm/open_meteo solarstorm/__main__.py tests/test_open_meteo_pilot.py tests/test_open_meteo_pilot_cli.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

---

### Task 7: Generate Experiment Artifacts and Update Docs

**Files:**
- Generate: `data/open_meteo_features.parquet` from fixture/raw cache if available
- Generate: `reports/open-meteo-features/`
- Generate: `reports/onda3-open-meteo-pilot/` when feature coverage overlaps local features
- Modify: `ROADMAP.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Run focused test suite**

Run:

```powershell
uv run pytest tests/test_open_meteo_availability.py tests/test_open_meteo_client.py tests/test_open_meteo_features.py tests/test_open_meteo_feature_cli.py tests/test_open_meteo_pilot.py tests/test_open_meteo_pilot_cli.py -q
uv run ruff check solarstorm/open_meteo solarstorm/__main__.py tests/test_open_meteo_availability.py tests/test_open_meteo_client.py tests/test_open_meteo_features.py tests/test_open_meteo_feature_cli.py tests/test_open_meteo_pilot.py tests/test_open_meteo_pilot_cli.py
```

Expected: tests pass and Ruff reports `All checks passed!`.

- [ ] **Step 2: Build feature artifacts from the live-smoke raw-equivalent only if raw response text is available**

If no response-text cache exists, create a fixture raw CSV under
`reports/open-meteo-features/fixture_previous_runs_raw_v1.csv` using the test
fixture and run:

```powershell
uv run tmax open-meteo-build-features --raw-responses-path reports/open-meteo-features/fixture_previous_runs_raw_v1.csv --decision-path reports/open-meteo-availability-live-smoke/open_meteo_decision_update_v1.csv --data-dir data --output-dir reports/open-meteo-features --cps 22:00,23:00
```

Expected:

- command exits 0;
- `data/open_meteo_features.parquet` exists;
- `data/features.parquet` still exists and is not overwritten;
- report says `EXPERIMENT_ONLY`.

- [ ] **Step 3: Run pilot only if generated features overlap local features and labels**

Run:

```powershell
uv run tmax onda3-open-meteo-pilot --features-path data/features.parquet --open-meteo-features-path data/open_meteo_features.parquet --output-dir reports/onda3-open-meteo-pilot --test-years 2024,2025
```

Expected:

- command exits 0 when there is overlap;
- otherwise exits cleanly or produces availability-blocked artifacts;
- all outputs remain `EXPERIMENT_ONLY`.

- [ ] **Step 4: Update `ROADMAP.md`**

Add under the Open-Meteo integration gate:

```markdown
- Open-Meteo causal feature integration is experiment-only. The first allowed
  feature source is Previous Runs day-1 fixed-lead data, gated by
  `open_meteo_decision_update_v1.csv`. Historical Weather and Historical
  Forecast remain blocked as predictors, and Single Runs remains blocked until
  its endpoint contract succeeds.
```

- [ ] **Step 5: Update `CHANGELOG.md`**

Add under Unreleased:

```markdown
- Added experiment-only Open-Meteo causal feature generation from eligible
  Previous Runs fixed-lead payloads and an Onda 3 Open-Meteo pilot comparison.
  The integration keeps Historical Weather/Historical Forecast blocked as
  causal predictors and leaves Single Runs disabled until its request contract
  succeeds.
```

- [ ] **Step 6: Final verification**

Run:

```powershell
uv run pytest tests/test_open_meteo_availability.py tests/test_open_meteo_client.py tests/test_open_meteo_features.py tests/test_open_meteo_feature_cli.py tests/test_open_meteo_pilot.py tests/test_open_meteo_pilot_cli.py -q
uv run ruff check solarstorm/open_meteo solarstorm/__main__.py tests/test_open_meteo_availability.py tests/test_open_meteo_client.py tests/test_open_meteo_features.py tests/test_open_meteo_feature_cli.py tests/test_open_meteo_pilot.py tests/test_open_meteo_pilot_cli.py
Test-Path data/features.parquet
Test-Path data/open_meteo_features.parquet
```

Expected:

- tests pass;
- Ruff passes;
- `data/features.parquet` exists;
- `data/open_meteo_features.parquet` exists only after the feature build step;
- no production readiness claim appears in generated reports.

